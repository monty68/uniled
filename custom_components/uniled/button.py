"""Platform for UniLED button integration."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
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
from .lib.attributes import ButtonAttribute, UniledAttribute

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the UniLED button platform."""
    await async_uniled_entity_setup(
        hass, entry, async_add_entities, _add_button_entity, Platform.BUTTON
    )


def _add_button_entity(
    coordinator: UniledUpdateCoordinator,
    channel: UniledChannel,
    feature: UniledAttribute | None,
) -> UniledEntity | None:
    """Create UniLED button entity."""
    return None if not feature else UniledButtonEntity(coordinator, channel, feature)


class UniledButtonEntity(
    UniledEntity, CoordinatorEntity[UniledUpdateCoordinator], ButtonEntity
):
    """Defines a UniLED button control."""

    def __init__(
        self,
        coordinator: UniledUpdateCoordinator,
        channel: UniledChannel,
        feature: ButtonAttribute,
    ) -> None:
        """Initialize a UniLED button control."""
        super().__init__(coordinator, channel, feature)

        if feature.attr.startswith(ButtonDeviceClass.IDENTIFY):
            self._attr_device_class = ButtonDeviceClass.IDENTIFY
        if feature.attr.startswith(ButtonDeviceClass.RESTART):
            self._attr_device_class = ButtonDeviceClass.RESTART
        if feature.attr.startswith(ButtonDeviceClass.UPDATE):
            self._attr_device_class = ButtonDeviceClass.UPDATE

    async def async_press(self) -> None:
        """Button Pressed."""
        value = self.device.get_state(self.channel, self.feature.attr)
        value = (
            not value if isinstance(self.feature.value, bool) else self.feature.value
        )
        await self._async_state_change(value)
