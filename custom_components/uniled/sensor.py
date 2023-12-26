"""Platform for UniLED number integration."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntity,
)
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from .lib.attributes import (
    UniledAttribute,
    UniledGroup,
    SensorAttribute,
)
from .entity import (
    UniledUpdateCoordinator,
    UniledChannel,
    UniledEntity,
    Platform,
    AddEntitiesCallback,
    async_uniled_entity_setup,
)
from .const import ATTR_UL_RSSI

from .lib.net.device import UNILED_TRANSPORT_NET

EXTRA_ATTRIBUTE_MAC_ADDRESS = "mac_address"

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the UniLED sensor platform."""
    await async_uniled_entity_setup(
        hass, entry, async_add_entities, _add_sensor_entity, Platform.SENSOR
    )


def _add_sensor_entity(
    coordinator: UniledUpdateCoordinator,
    channel: UniledChannel,
    feature: UniledAttribute | None,
) -> UniledEntity | None:
    """Create UniLED sensor entity."""
    if feature:
        return UniledSensorEntity(coordinator, channel, feature)
    if channel.number == 0 and coordinator.device.transport != UNILED_TRANSPORT_NET:
        return UniledSignalSensor(coordinator, channel)
    return None

class UniledSensorEntity(
    UniledEntity, CoordinatorEntity[UniledUpdateCoordinator], SensorEntity
):
    """Defines a UniLED sensor."""

    def __init__(
        self,
        coordinator: UniledUpdateCoordinator,
        channel: UniledChannel,
        feature: SensorAttribute,
    ) -> None:
        """Initialize a UniLED sensor."""
        super().__init__(coordinator, channel, feature)

    @property
    def native_value(self) -> str:
        """Return the value reported by the sensor."""
        return self.device.get_state(self.channel, self.feature.attr)

@dataclass
class RSSIFeature(SensorAttribute):
    """UniLED RSSI Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            None,
            "RSSI",
            "mdi:signal",
            key="rssi",
            group=UniledGroup.DIAGNOSTIC,
            enabled=False,
        )


class UniledSignalSensor(
    UniledEntity, CoordinatorEntity[UniledUpdateCoordinator], SensorEntity
):
    """Defines a UniLED Signal Sensor control."""

    _unrecorded_attributes = frozenset(
        {
            EXTRA_ATTRIBUTE_MAC_ADDRESS,
        }
    )

    def __init__(
        self,
        coordinator: UniledUpdateCoordinator,
        channel: UniledChannel,
    ) -> None:
        """Initialize a UniLED effect speed control."""
        super().__init__(coordinator, channel, RSSIFeature())

    @callback
    def _async_update_attrs(self, first: bool = False) -> None:
        """Handle updating _attr values."""
        super()._async_update_attrs()
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT

    @property
    def native_value(self) -> str:
        """Return the value reported by the sensor."""
        return self.device.rssi

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes."""
        return {EXTRA_ATTRIBUTE_MAC_ADDRESS: self.device.address}
