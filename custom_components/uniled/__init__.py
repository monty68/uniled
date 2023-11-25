"""The UniLED integration."""
from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.match import ADDRESS, BluetoothCallbackMatcher
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_DEVICE,
    CONF_ADDRESS,
    CONF_MODEL,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)

from .lib.models_db import UNILED_MODELS

from .lib.ble.device import (
    close_stale_connections,
    get_device,
    UNILED_TRANSPORT_BLE,
    UniledBleDevice,
)

from .lib.net.device import (
    UNILED_TRANSPORT_NET,
    UniledNetDevice,
)

from .const import (
    DOMAIN,
    UNILED_DEVICE_RETRYS,
    UNILED_DEVICE_TIMEOUT,
    CONF_RETRY_COUNT,
)

from .coordinator import UniledUpdateCoordinator

import async_timeout
import gc
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UNILED from a config entry."""

    if not entry.options:
        hass.config_entries.async_update_entry(
            entry,
            options={CONF_RETRY_COUNT: UNILED_DEVICE_RETRYS},
        )

    address: str = str(entry.data[CONF_ADDRESS]).upper()
    model_name: str = entry.data.get(CONF_MODEL, None)
    device_class: str = entry.data[CONF_DEVICE_CLASS]
    device_retrys: int = entry.options[CONF_RETRY_COUNT]

    if device_class == UNILED_TRANSPORT_BLE:
        ble_device = bluetooth.async_ble_device_from_address(
            hass, address, True
        ) or await get_device(address)

        if not ble_device:
            # bluetooth.async_rediscover_address(hass, address)
            raise ConfigEntryNotReady(
                f"Could not find BLE device with address {address}"
            )

        await close_stale_connections(ble_device)

        service_info = bluetooth.async_last_service_info(
            hass, address, connectable=True
        )

        if not service_info:
            bluetooth.async_rediscover_address(hass, address)
            raise ConfigEntryNotReady(
                f"Could not find service info for BLE device with address {address}"
            )

        _LOGGER.debug(
            "*** Setup UniLED BLE Device: %s v%s - %s %s",
            ble_device,
            entry.version,
            entry.data,
            service_info.advertisement,
        )

        uniled = UniledBleDevice(
            ble_device, service_info.advertisement, model_name, device_retrys
        )

        if not uniled.model:
            model = await uniled.resolve_model(model_name is None, False)
            if model is None:
                return False

        if uniled.model_name != model_name:
            new = {**entry.data}
            new[CONF_MODEL] = uniled.model_name
            hass.config_entries.async_update_entry(entry, data=new)
            _LOGGER.debug("%s: Updated HASS configuration: %s.", uniled.name, new)

        @callback
        def _async_update_ble(
            service_info: bluetooth.BluetoothServiceInfoBleak,
            change: bluetooth.BluetoothChange,
        ) -> None:
            """Update from a ble callback."""
            uniled.set_device_and_advertisement(
                service_info.device, service_info.advertisement
            )

        entry.async_on_unload(
            bluetooth.async_register_callback(
                hass,
                _async_update_ble,
                BluetoothCallbackMatcher({ADDRESS: address}),
                bluetooth.BluetoothScanningMode.PASSIVE,
            )
        )

    elif device_class == UNILED_TRANSPORT_NET:
        raise ConfigEntryNotReady(
            f"Unable to communicate with network device {address} as currently not supported!"
        )
    else:
        raise ConfigEntryError(
            f"Unable to communicate with device {address} of unsupported class: {device_class}"
        )

    coordinator = UniledUpdateCoordinator(hass, uniled, entry)
    if not uniled.available:
        ## Device is not available, so attempt first connection
        startup_event = asyncio.Event()
        cancel_first_update = uniled.register_callback(lambda *_: startup_event.set())
        _LOGGER.debug("*** Awaiting UniLED Device: %s, first response...", uniled.name)

        try:
            await coordinator.async_config_entry_first_refresh()
        except ConfigEntryNotReady:
            cancel_first_update()
            await uniled.stop()
            if device_class == UNILED_TRANSPORT_BLE:
                bluetooth.async_rediscover_address(hass, address)
            raise
        try:
            async with async_timeout.timeout(UNILED_DEVICE_TIMEOUT):
                await startup_event.wait()
                _LOGGER.debug("*** Response from UniLED Device: %s", uniled.name)
        except asyncio.TimeoutError as ex:
            await uniled.stop()
            raise ConfigEntryNotReady("No response from device") from ex
        finally:
            cancel_first_update()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def _async_stop(event: Event) -> None:
        """Close the connection."""
        await uniled.stop()
        bluetooth.async_rediscover_address(hass, uniled.address)


    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )

    _LOGGER.debug(
        "*** Added UniLED device entry for: %s, ID: %s, Unique ID: %s",
        uniled.name,
        entry.entry_id,
        entry.unique_id,
    )

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: UniledUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    if entry.title != coordinator.title:
        await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    domain_data = hass.data[DOMAIN]
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: UniledUpdateCoordinator = domain_data.pop(entry.entry_id)
        await coordinator.device.stop()
        if coordinator.device.transport == UNILED_TRANSPORT_BLE:
            bluetooth.async_rediscover_address(hass, coordinator.device.address)
        del coordinator
        gc.collect()

    _LOGGER.debug("Unloaded OK: %s", unload_ok)
    return unload_ok
