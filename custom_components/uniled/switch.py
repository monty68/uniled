"""Platform for UniLED switch integration."""
from __future__ import annotations

from functools import partial
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass

from .const import DOMAIN
from .entity import UNILEDEntity
from .coordinator import UNILEDUpdateCoordinator

import logging

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the UniLED switch platform."""
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
    """Update channels."""
    channel_ids = {channel.number for channel in coordinator.device.channels}
    new_entities: list[UNILEDEntity] = []

    # Process new channels, add them to Home Assistant
    for channel_id in channel_ids - current_ids:
        current_ids.add(channel_id)
        try:
            channel = coordinator.device.channels[channel_id]
        except IndexError:
            continue

        if channel.effect is not None:
            if channel.effect_direction is not None:
                new_entities.append(UNILEDEffectDirection(coordinator, channel_id))

    async_add_entities(new_entities)


class UNILEDEffectDirection(
    UNILEDEntity, CoordinatorEntity[UNILEDUpdateCoordinator], SwitchEntity
):
    """Defines a UniLED effect direction switch control."""

    _attr_entity_registry_enabled_default = True
    _attr_entity_category = None
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self,
        coordinator: UNILEDUpdateCoordinator,
        channel_id: int,
    ) -> None:
        """Initialize a UniLED direction control."""
        super().__init__(coordinator, channel_id, "Effect Direction", "direction")
        self._async_update_attrs()

    @property
    def available(self) -> bool:
        if not self.channel.is_on or self.channel.effect_type_is_static:
            return False
        return super().available

    @property
    def is_on(self) -> bool:
        """Is the switch currently on (forwards) or off (backwards)."""
        return self.channel.effect_direction

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        self._attr_icon = "mdi:arrow-right" if self.is_on else "mdi:arrow-left"

    async def async_turn_on(self, **kwargs):
        """Turn the entity on (forwards)."""
        await self.channel.async_set_effect_direction(True)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off (backwards)."""
        await self.channel.async_set_effect_direction(False)

    async def async_toggle(self, **kwargs):
        """Toggle the switch"""
        await self.channel.async_set_effect_direction(not self.is_on)
