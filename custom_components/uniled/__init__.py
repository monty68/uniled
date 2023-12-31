"""The UniLED integration."""
from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.match import (
    BluetoothCallbackMatcher,
    MANUFACTURER_ID,
    ADDRESS,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback, CoreState
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.entity_registry import async_migrate_entries
from homeassistant.const import (
    CONF_ADDRESS,
    CONF_COUNTRY,
    CONF_MODEL,
    CONF_PASSWORD,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from .lib.zng.manager import (
    CONF_ZNG_ACTIVE_SCAN as CONF_ACTIVE_SCAN,
    CONF_ZNG_MESH_ID as CONF_MESH_ID,
    CONF_ZNG_MESH_UUID as CONF_MESH_UUID,
    UNILED_TRANSPORT_ZNG,
    ZENGGE_MANUFACTURER_ID,
    ZenggeManager,
)
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
    CONF_UL_RETRY_COUNT as CONF_RETRY_COUNT,
    CONF_UL_TRANSPORT as CONF_TRANSPORT,
    CONF_UL_UPDATE_INTERVAL as CONF_UPDATE_INTERVAL,
    UNILED_COMMAND_SETTLE_DELAY,
    UNILED_DEVICE_RETRYS as DEFAULT_RETRY_COUNT,
    UNILED_UPDATE_SECONDS as DEFAULT_UPDATE_INTERVAL,
    UNILED_DEVICE_TIMEOUT,
)

from .coordinator import UniledUpdateCoordinator

import async_timeout
import gc
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SCENE,
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UNILED from a config entry."""

    transport: str = entry.data.get(CONF_TRANSPORT)

    if transport == UNILED_TRANSPORT_ZNG:
        mesh_id: str = entry.data.get(CONF_MESH_ID)
        mesh_uuid: str = entry.data.get(CONF_MESH_UUID, 0)
        mesh_user: str = entry.data.get(CONF_USERNAME, "")
        mesh_pass: str = entry.data.get(CONF_PASSWORD, "")
        mesh_area: str = entry.data.get(CONF_COUNTRY, "")
        scan_mode = (
            bluetooth.BluetoothScanningMode.ACTIVE
            if entry.options.get(CONF_ACTIVE_SCAN, True)
            else bluetooth.BluetoothScanningMode.PASSIVE
        )

        uniled = ZenggeManager(
            mesh_id, mesh_uuid, mesh_user, mesh_pass, mesh_area, entry.options
        )

        coordinator = UniledUpdateCoordinator(hass, uniled, entry)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

        _LOGGER.debug(
            "*** Added UniLED entry for: %s - %s (%s) %s HASS: %s",
            coordinator.device.name,
            entry.unique_id,
            entry.entry_id,
            scan_mode,
            hass.state,
        )

        @callback
        async def _async_startup(event=None) -> None:
            """Startup"""
            await coordinator.device.startup()
            try:
                await coordinator.async_config_entry_first_refresh()
                await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
            except ConfigEntryNotReady:
                _LOGGER.debug(
                    "%s: First update attempt failed!", coordinator.device.name
                )
                await _async_shutdown_coordinator(hass, coordinator)
                if hass.state != CoreState.running:
                    raise

        @callback
        def _async_ble_sniffer(
            service_info: bluetooth.BluetoothServiceInfoBleak,
            change: bluetooth.BluetoothChange,
        ) -> None:
            """Update from a ble callback."""
            coordinator.device.set_device_and_advertisement(
                service_info.device, service_info.advertisement
            )

        entry.async_on_unload(
            bluetooth.async_register_callback(
                hass,
                _async_ble_sniffer,
                BluetoothCallbackMatcher({MANUFACTURER_ID: ZENGGE_MANUFACTURER_ID}),
                scan_mode,
            )
        )

        entry.async_on_unload(
            hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STOP, coordinator.device.shutdown
            )
        )

        entry.async_on_unload(entry.add_update_listener(_async_update_listener))

        if hass.state == CoreState.running:
            await _async_startup()
        else:
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _async_startup)

        return True
    elif transport == UNILED_TRANSPORT_BLE:
        address: str = str(entry.data[CONF_ADDRESS]).upper()
        model_name: str = entry.data.get(CONF_MODEL, None)

        ble_device = bluetooth.async_ble_device_from_address(
            hass, address, True
        ) or await get_device(address)

        if not ble_device:
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
            entry.options, ble_device, service_info.advertisement, model_name
        )

        if not uniled.model:
            model = await uniled.resolve_model(model_name is None, False)
            if model is None:
                raise ConfigEntryError(
                    f"Could not resolve model for BLE device with address {address}"
                )

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

    elif transport == UNILED_TRANSPORT_NET:
        raise ConfigEntryError(
            f"Unable to communicate with network device {address} as currently not supported!"
        )
    else:
        raise ConfigEntryError(
            f"Unable to communicate with device {address} of unsupported class: {transport}"
        )

    coordinator = UniledUpdateCoordinator(hass, uniled, entry)
    if not await coordinator.device.startup():
        raise ConfigEntryNotReady("Failed to startup")

    if not coordinator.device.available:
        ## Device is not available, so attempt first connection
        startup_event = asyncio.Event()
        cancel_first_update = coordinator.device.register_callback(
            lambda *_: startup_event.set()
        )
        _LOGGER.debug(
            "*** Awaiting UniLED Device: %s, first response...", coordinator.device.name
        )

        try:
            await coordinator.async_config_entry_first_refresh()
        except ConfigEntryNotReady:
            _LOGGER.warning("%s: First update attempt failed!", coordinator.device.name)
            cancel_first_update()
            await _async_shutdown_coordinator(hass, coordinator)
            del coordinator
            gc.collect()
            raise

        try:
            async with async_timeout.timeout(UNILED_DEVICE_TIMEOUT):
                await startup_event.wait()
                cancel_first_update()
                _LOGGER.debug(
                    "*** Response from UniLED Device: %s", coordinator.device.name
                )

        except asyncio.TimeoutError as ex:
            cancel_first_update()
            await _async_shutdown_coordinator(hass, coordinator)
            del coordinator
            gc.collect()
            raise ConfigEntryNotReady("No response from device") from ex
            return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def _async_stop(event: Event) -> None:
        """Close the connection."""
        await _async_shutdown_coordinator(hass, coordinator)

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


async def _async_shutdown_coordinator(
    hass: HomeAssistant, coordinator: UniledUpdateCoordinator, rediscover: bool = True
) -> None:
    """Shutdown coordinator device"""
    await coordinator.device.shutdown()
    if (
        coordinator.device.transport != UNILED_TRANSPORT_NET
        and coordinator.device.address
        and rediscover
    ):
        bluetooth.async_rediscover_address(hass, coordinator.device.address)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: UniledUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.info(
        "%s: Reloading due to config/options update...", coordinator.device.name
    )
    await asyncio.sleep(UNILED_COMMAND_SETTLE_DELAY)
    await _async_shutdown_coordinator(hass, coordinator, rediscover=False)
    await asyncio.sleep(UNILED_COMMAND_SETTLE_DELAY * 3)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry) -> bool:
    """Unload a config entry."""
    coordinator = None
    if entry.entry_id in hass.data[DOMAIN]:
        coordinator: UniledUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        _LOGGER.info("%s: Unloading...", coordinator.device.name)
        await coordinator.device.shutdown()

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if coordinator:
            if coordinator.device.transport != UNILED_TRANSPORT_NET:
                bluetooth.async_rediscover_address(hass, coordinator.device.address)
            del coordinator
        gc.collect()

    return unload_ok


async def async_migrate_entry(hass, entry):
    """Migrate old entry."""
    if entry.version == 1:
        # Miserable, but needed :-(
        _LOGGER.error(
            "UniLED is unable to migrate this entities configuration, remove and re-install."
        )
        return False
    return True
