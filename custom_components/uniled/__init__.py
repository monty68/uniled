"""The uniled integration."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

import async_timeout

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.match import ADDRESS, BluetoothCallbackMatcher
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from bleak_retry_connector import get_device
from .lib.ble_device import UNILEDBLE, BLEAK_EXCEPTIONS
from .lib.classes import UNILEDDevice
from .coordinator import UNILEDUpdateCoordinator
from .const import DOMAIN, DEVICE_TIMEOUT

PLATFORMS: list[Platform] = [
    Platform.SELECT,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.LIGHT,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UNILED from a config entry."""

    address: str = entry.data[CONF_ADDRESS]
    ble_device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), True
    ) or await get_device(address)
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find BTF BLE device with address {address}"
        )

    _LOGGER.debug("*** Setup Device Entry for BLE Device: %s (%s)", ble_device, entry.data)

    service_info = bluetooth.async_last_service_info(hass, address, connectable=True)
    if not service_info:
        return False

    uniled = UNILEDBLE(ble_device, service_info.advertisement)

    startup_event = asyncio.Event()
    cancel_first_update = uniled.register_callback(lambda *_: startup_event.set())
    coordinator = UNILEDUpdateCoordinator(hass, uniled, entry)

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        cancel_first_update()
        bluetooth.async_rediscover_address(hass, address)
        raise

    try:
        async with async_timeout.timeout(DEVICE_TIMEOUT):
            await startup_event.wait()
            _LOGGER.debug("*** BLE Device: %s, Responded", ble_device)
    except asyncio.TimeoutError as ex:
        raise ConfigEntryNotReady(
            "Unable to communicate with the device; "
            f"Try moving the Bluetooth adapter closer to {uniled.name}"
        ) from ex
    finally:
        cancel_first_update()

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

    _LOGGER.debug("***Add entry for BLE Device: %s, ID: %s, Unique ID: %s", ble_device, entry.entry_id, entry.unique_id)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def _async_stop(event: Event) -> None:
        """Close the connection."""
        await uniled.stop()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: UNILEDUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    if entry.title != coordinator.title:
        await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    device: UNILEDDevice = hass.data[DOMAIN][entry.entry_id].device
    _LOGGER.debug("%s: Unloading!", device.name)
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Make sure we probe the device again in case something has changed externally
        # async_clear_discovery_cache(hass, entry.data[CONF_ADDRESS])
        bluetooth.async_rediscover_address(hass, entry.data[CONF_ADDRESS])
        del hass.data[DOMAIN][entry.entry_id]
        await device.stop()
    return unload_ok
