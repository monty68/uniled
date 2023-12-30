"""Platform for UniLED scene integration."""
from __future__ import annotations
from typing import cast

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.scene import Scene

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
    SceneAttribute,
)

import logging

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the UniLED switch platform."""
    await async_uniled_entity_setup(
        hass, entry, async_add_entities, _add_scene_entity, Platform.SCENE
    )


def _add_scene_entity(
    coordinator: UniledUpdateCoordinator,
    channel: UniledChannel,
    feature: UniledAttribute | None,
) -> UniledEntity | None:
    """Create UniLED switch entity."""
    return None if not feature else UniledSceneEntity(coordinator, channel, feature)


class UniledSceneEntity(
    UniledEntity, CoordinatorEntity[UniledUpdateCoordinator], Scene
):
    """Defines a UniLED scene control."""

    def __init__(
        self,
        coordinator: UniledUpdateCoordinator,
        channel: UniledChannel,
        feature: SceneAttribute,
    ) -> None:
        """Initialize a UniLED scene control."""
        super().__init__(coordinator, channel, feature)
    
    async def async_activate(self, **kwargs) -> None:
        """Turn the entity off."""
        await self._async_state_change(value=self.feature.scene_id)
