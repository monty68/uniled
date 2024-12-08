"""Platform for UniLED number integration."""

from __future__ import annotations

import logging
from typing import cast

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .entity import (
    AddEntitiesCallback,
    Platform,
    UniledChannel,
    UniledEntity,
    UniledUpdateCoordinator,
    async_uniled_entity_setup,
)
from .lib.attributes import NumberAttribute, UniledAttribute

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the UniLED number platform."""
    await async_uniled_entity_setup(
        hass, entry, async_add_entities, _add_number_entity, Platform.NUMBER
    )


def _add_number_entity(
    coordinator: UniledUpdateCoordinator,
    channel: UniledChannel,
    feature: UniledAttribute | None,
) -> UniledEntity | None:
    """Create UniLED number entity."""
    return None if not feature else UniledNumberEntity(coordinator, channel, feature)


class UniledNumberEntity(
    UniledEntity, CoordinatorEntity[UniledUpdateCoordinator], NumberEntity
):
    """Defines a UniLED number control."""

    def __init__(
        self,
        coordinator: UniledUpdateCoordinator,
        channel: UniledChannel,
        feature: NumberAttribute,
    ) -> None:
        """Initialize a UniLED number control."""
        self._attr_mode = NumberMode.AUTO
        self._attr_native_min_value = feature.min_value
        self._attr_native_max_value = feature.max_value
        self._attr_native_step = feature.step
        super().__init__(coordinator, channel, feature)

    @property
    def native_value(self) -> float:
        """Return the number value."""
        return cast(float, self.device.get_state(self.channel, self.feature.attr))

    async def async_set_native_value(self, value: float) -> None:
        """Set the features value value."""
        await self._async_state_change(value)
