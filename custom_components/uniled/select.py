"""Platform for UniLED number integration."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .entity import (
    AddEntitiesCallback,
    Platform,
    UniledChannel,
    UniledEntity,
    UniledUpdateCoordinator,
    async_uniled_entity_setup,
)
from .lib.attributes import SelectAttribute, UniledAttribute

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the UniLED select platform."""
    await async_uniled_entity_setup(
        hass, entry, async_add_entities, _add_number_entity, Platform.SELECT
    )


def _add_number_entity(
    coordinator: UniledUpdateCoordinator,
    channel: UniledChannel,
    feature: UniledAttribute | None,
) -> UniledEntity | None:
    """Create UniLED select entity."""
    return None if not feature else UniledSelectEntity(coordinator, channel, feature)


class UniledSelectEntity(
    UniledEntity, CoordinatorEntity[UniledUpdateCoordinator], SelectEntity
):
    """Defines a UniLED select control."""

    def __init__(
        self,
        coordinator: UniledUpdateCoordinator,
        channel: UniledChannel,
        feature: SelectAttribute,
    ) -> None:
        """Initialize a UniLED select control."""
        super().__init__(coordinator, channel, feature)

    @callback
    def _async_update_attrs(self, first: bool = False) -> None:
        """Handle updating _attr values."""
        super()._async_update_attrs()
        options = self.device.get_list(self.channel, self.feature.attr)
        self._attr_options = [] if options is None else options
        self._attr_current_option = self.device.get_state(
            self.channel, self.feature.attr
        )

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._async_state_change(value=option)
