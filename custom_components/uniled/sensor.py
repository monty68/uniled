"""Platform for UniLED sensor integration."""
from __future__ import annotations

from functools import partial
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)

from .const import DOMAIN
from .entity import UNILEDEntity
from .coordinator import UNILEDUpdateCoordinator

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform for UniLED."""
    coordinator: UNILEDUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    update_channels = partial(
        async_update_channels,
        coordinator,
        set(),
        async_add_entities,
    )

    entry.async_on_unload(coordinator.async_add_listener(update_channels))
    update_channels()


@callback
def async_update_channels(
    coordinator: UNILEDUpdateCoordinator,
    current_ids: set[int],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Update segments."""
    channel_ids = {channel.number for channel in coordinator.device.channels}
    new_entities: list[UNILEDEntity] = []

    # Process new channels, add them to Home Assistant
    for channel_id in channel_ids - current_ids:
        current_ids.add(channel_id)
        if channel_id == 0:
            new_entities.append(UNILEDConnectivitySensor(coordinator, channel_id))

    async_add_entities(new_entities)


class UNILEDConnectivitySensor(
    UNILEDEntity, CoordinatorEntity[UNILEDUpdateCoordinator], SensorEntity
):
    """Representation of a UniLED connectivity sensor."""

    _attr_entity_registry_enabled_default = False
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_icon = "mdi:signal"

    def __init__(self, coordinator: UNILEDUpdateCoordinator, channel_id: int) -> None:
        """Initialize a UniLED light."""
        super().__init__(coordinator, channel_id, "RSSI", "rssi")

    @property
    def native_value(self) -> str:
        """Return the value reported by the sensor."""
        return self.device.rssi

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes."""
        return {"mac_address": self.device.address}
