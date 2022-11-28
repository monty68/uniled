"""The uniled integration."""
from __future__ import annotations

import gc
import asyncio
import async_timeout
from datetime import timedelta

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import (
    CONF_ADDRESS,
    CONF_DEVICE_CLASS,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from .lib.models_db import (
    UNILED_TRANSPORT_BLE,
    UNILED_TRANSPORT_NET,
)
from bleak_retry_connector import get_device
from .lib.ble_device import UNILEDBLE

# from .lib.net_device import UNILEDNET
from .coordinator import UNILEDUpdateCoordinator
from .const import DOMAIN, DEVICE_TIMEOUT

import logging

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SELECT,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.LIGHT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UNILED from a config entry."""

    device_class: str = entry.data[CONF_DEVICE_CLASS]
    address: str = entry.data[CONF_ADDRESS]

    if device_class == UNILED_TRANSPORT_BLE:
        ble_device = bluetooth.async_ble_device_from_address(
            hass, address.upper(), True
        ) or await get_device(address)
        if not ble_device:
            raise ConfigEntryNotReady(
                f"Could not find BLE device with address {address}"
            )

        _LOGGER.debug("*** Setup UniLED BLE Device: %s (%s)", ble_device, entry.data)

        service_info = bluetooth.async_last_service_info(
            hass, address, connectable=True
        )
        if not service_info:
            return False

        uniled = UNILEDBLE(ble_device, service_info.advertisement)

    elif device_class == UNILED_TRANSPORT_NET:
        raise ConfigEntryNotReady(
            f"Unable to communicate with network device {address} as currently not supported!"
        )
    else:
        raise ConfigEntryNotReady(
            f"Unable to communicate with unknown device class: {device_class}"
        )

    startup_event = asyncio.Event()
    cancel_first_update = uniled.register_callback(lambda *_: startup_event.set())
    coordinator = UNILEDUpdateCoordinator(hass, uniled, entry)

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        cancel_first_update()
        await uniled.stop()
        if device_class == UNILED_TRANSPORT_BLE:
            bluetooth.async_rediscover_address(hass, address)
        raise

    _LOGGER.debug("*** Awaiting UniLED Device: %s, response", uniled.name)

    try:
        async with async_timeout.timeout(DEVICE_TIMEOUT):
            await startup_event.wait()
            _LOGGER.debug("*** Response from UniLED Device: %s", uniled.name)
    except asyncio.TimeoutError as ex:
        await uniled.stop()
        raise ConfigEntryNotReady("No response from device") from ex
    finally:
        cancel_first_update()

    # await uniled.stop()
    # _LOGGER.debug("Refs: %s", gc.get_referrers(uniled))
    # return True

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def _async_stop(event: Event) -> None:
        """Close the connection."""
        await uniled.stop()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )

    _LOGGER.debug(
        "***Added device entry for UniLED Device: %s, ID: %s, Unique ID: %s",
        uniled.name,
        entry.entry_id,
        entry.unique_id,
    )

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: UNILEDUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    if entry.title != coordinator.title:
        await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    domain_data = hass.data[DOMAIN]
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: UNILEDUpdateCoordinator = domain_data.pop(entry.entry_id)
        await coordinator.device.stop()
        del coordinator

        # _LOGGER.debug("Refs: %s", gc.get_referrers(device))
        # del coordinator
        gc.collect()

    _LOGGER.debug("Unloaded OK: %s", unload_ok)
    return unload_ok
