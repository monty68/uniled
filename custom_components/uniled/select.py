"""Platform for UniLED select integration."""
from __future__ import annotations

from functools import partial
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.select import SelectEntity

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
    """Set up the UniLED button platform."""
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
        if channel.mode is not None:
            new_entities.append(UNILEDModeSelect(coordinator, channel_id))
        if channel.input is not None:
            new_entities.append(UNILEDInputSelect(coordinator, channel_id))
        if channel.chip_type is not None:
            new_entities.append(UNILEDChipTypeSelect(coordinator, channel_id))
        if channel.chip_order is not None:
            new_entities.append(UNILEDChipOrderSelect(coordinator, channel_id))

    async_add_entities(new_entities)


class UNILEDModeSelect(
    UNILEDEntity, CoordinatorEntity[UNILEDUpdateCoordinator], SelectEntity
):
    """Defines a UniLED mode select control."""

    _attr_entity_registry_enabled_default = True
    _attr_entity_category = None

    def __init__(self, coordinator: UNILEDUpdateCoordinator, channel_id: int) -> None:
        """Initialize a UniLED mode control."""
        super().__init__(coordinator, channel_id, "Mode", "mode")
        self._attr_icon = "mdi:refresh-auto"
        self._attr_options = self.channel.mode_list
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        self._attr_current_option = self.channel.mode

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.channel.async_set_mode(option)


class UNILEDInputSelect(
    UNILEDEntity, CoordinatorEntity[UNILEDUpdateCoordinator], SelectEntity
):
    """Defines a UniLED input select control."""

    _attr_entity_registry_enabled_default = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: UNILEDUpdateCoordinator, channel_id: int) -> None:
        """Initialize a UniLED input control."""
        super().__init__(coordinator, channel_id, "Audio Input", "input")
        self._attr_icon = "mdi:microphone"
        self._attr_options = self.channel.input_list
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        self._attr_current_option = self.channel.input

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.channel.async_set_input(option)


class UNILEDChipTypeSelect(
    UNILEDEntity, CoordinatorEntity[UNILEDUpdateCoordinator], SelectEntity
):
    """Defines a UniLED chip type select control."""

    _attr_entity_registry_enabled_default = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: UNILEDUpdateCoordinator, channel_id: int) -> None:
        """Initialize a UniLED chip type control."""
        super().__init__(coordinator, channel_id, "Chip Type", "chip_type")
        self._attr_icon = "mdi:chip"
        self._attr_options = self.channel.chip_type_list
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        self._attr_current_option = self.channel.chip_type

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.channel.async_set_chip_type(option)


class UNILEDChipOrderSelect(
    UNILEDEntity, CoordinatorEntity[UNILEDUpdateCoordinator], SelectEntity
):
    """Defines a UniLED chip color order select control."""

    _attr_entity_registry_enabled_default = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: UNILEDUpdateCoordinator, channel_id: int) -> None:
        """Initialize a UniLED chip color order control."""
        super().__init__(coordinator, channel_id, "Chip Color Order", "chip_order")
        self._attr_icon = "mdi:palette"
        self._attr_options = self.channel.chip_order_list
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        self._attr_current_option = self.channel.chip_order

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.channel.async_set_chip_order(option)
