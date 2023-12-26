"""Platform for UniLED switch integration."""
from __future__ import annotations
from typing import cast

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.switch import SwitchEntity

from .entity import (
    AddEntitiesCallback,
    UniledUpdateCoordinator,
    UniledChannel,
    UniledEntity,
    Platform,
    async_uniled_entity_setup,
)

from .lib.attributes import (
    UniledAttribute,
    SwitchAttribute,
)

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the UniLED switch platform."""
    await async_uniled_entity_setup(
        hass, entry, async_add_entities, _add_switch_entity, Platform.SWITCH
    )


def _add_switch_entity(
    coordinator: UniledUpdateCoordinator,
    channel: UniledChannel,
    feature: UniledAttribute | None,
) -> UniledEntity | None:
    """Create UniLED switch entity."""
    return None if not feature else UniledSwitchEntity(coordinator, channel, feature)


class UniledSwitchEntity(
    UniledEntity, CoordinatorEntity[UniledUpdateCoordinator], SwitchEntity
):
    """Defines a UniLED switch control."""
    _unrecorded_attributes = frozenset(
        {
            "state",
        }
    )

    def __init__(
        self,
        coordinator: UniledUpdateCoordinator,
        channel: UniledChannel,
        feature: SwitchAttribute,
    ) -> None:
        """Initialize a UniLED switch control."""
        super().__init__(coordinator, channel, feature)
    
    @property
    def icon(self):
        """Return Icon based on switch state"""
        return self.feature.state_icon(self.is_on) if self.available else "mdi:help"

    @property
    def is_on(self) -> bool:
        """Is the switch currently on or not."""
        return self.device.get_state(self.channel, self.feature.attr)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self._async_state_change(value=True)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self._async_state_change(value=False)
