"""Support for UniLED lights."""
from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.const import (
    ATTR_CONNECTIONS,
    ATTR_HW_VERSION,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    ATTR_SW_VERSION,
    CONF_MODEL,
    CONF_NAME,
)
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import UNILEDUpdateCoordinator
from .lib.classes import UNILEDChannel, UNILEDDevice
from .lib.models_db import UNILED_TRANSPORT_BLE, UNILED_TRANSPORT_NET

import logging

_LOGGER = logging.getLogger(__name__)


class UNILEDEntity(CoordinatorEntity[UNILEDUpdateCoordinator]):
    """Representation of a UniLED entity with a coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UNILEDUpdateCoordinator,
        channel_id: int,
        name: str,
        key: str | None = None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._responding = True
        self._device: UNILEDDevice = coordinator.device
        self._channel: UNILEDChannel = self._device.channels[channel_id]
        self._channel_id = channel_id
        self._attr_name = f"{self._channel.name} {name}"
        mangled_name = self._channel.name.replace(" ", "_").lower()
        base_unique_id = coordinator.entry.unique_id or coordinator.entry.entry_id
        self._attr_unique_id = f"_{base_unique_id}_{mangled_name}"
        if key is not None:
            self._attr_unique_id = f"_{self._attr_unique_id}_{key}"
        self._attr_device_info = _async_device_info(self._device, coordinator.entry)

    @property
    def available(self) -> bool:
        if not self.channel.is_available:
            return False
        return super().available

    @property
    def id(self) -> int:
        """Return channel id"""
        return self._channel_id

    @property
    def channel(self) -> UNILEDChannel:
        """Return UniLED channel object"""
        return self._channel

    @property
    def device(self) -> UNILEDDevice:
        """Return UniLED device object"""
        return self._device

    async def _async_ensure_device_on(self) -> None:
        """Turn the device on if it needs to be turned on before a command."""
        if self.channel.needs_on and not self.channel.is_on:
            await self.channel.async_turn_on()

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        self.async_on_remove(
            self._channel.register_callback(self._handle_coordinator_update)
        )
        await super().async_added_to_hass()

    @callback
    def _handle_coordinator_update(self, *args: Any) -> None:
        """Handle updated data from the coordinator."""
        self._async_update_attrs()
        self.async_write_ha_state()

    # @abstractmethod
    @callback
    def _async_update_attrs(self) -> None:
        """Update entity attributes"""


def _async_device_info(
    device: UNILEDDevice, entry: config_entries.ConfigEntry
) -> DeviceInfo:

    device_info: DeviceInfo = {
        ATTR_IDENTIFIERS: {(DOMAIN, entry.entry_id)},
        ATTR_MANUFACTURER: device.manufacturer,
        ATTR_MODEL: device.model_name,
        ATTR_NAME: device.name,  # entry.data.get(CONF_NAME, entry.title),
        ATTR_HW_VERSION: device.description,
        # ATTR_SW_VERSION: hex(device.version),
    }

    if device.transport == UNILED_TRANSPORT_BLE:
        device_info[ATTR_CONNECTIONS] = {(dr.CONNECTION_BLUETOOTH, device.address)}
    elif device.transport == UNILED_TRANSPORT_NET:
        if entry.unique_id:
            device_info[ATTR_CONNECTIONS] = {
                (dr.CONNECTION_NETWORK_MAC, entry.unique_id)
            }

    return device_info
