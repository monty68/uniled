"""Platform for UniLED scene integration."""
from __future__ import annotations
from typing import Any
from dataclasses import dataclass
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import ExtraStoredData
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
from .lib.const import UNILED_CONTROL_ATTRIBUTES, UNILED_ENTITY_ATTRIBUTES

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


@dataclass
class UniledSceneData(ExtraStoredData):
    """Object to hold extra channel scene data"""

    def __init__(self, channel: UniledChannel):
        self.channel = channel

    def as_dict(self) -> dict[str, Any]:
        """Return a dict representation of the extra data."""
        data = dict()
        for attr in UNILED_CONTROL_ATTRIBUTES:
            if not self.channel.status.has(attr):
                continue
            data[attr] = self.channel.status.get(attr)
        for attr in UNILED_ENTITY_ATTRIBUTES:
            if not self.channel.status.has(attr):
                continue
            data[attr] = self.channel.status.get(attr)
        # _LOGGER.warn(
        #    "%s: %s Scene Data: %s", self.channel.name, self.channel.status.dump(), data
        # )
        return data


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

    @property
    def extra_restore_state_data(self) -> ExtraStoredData | None:
        """Return entity specific state data to be restored."""
        return UniledSceneData(self.channel)

    async def async_activate(self, **kwargs) -> None:
        """Turn the entity off."""
        data = await self.async_get_last_extra_data()
        # _LOGGER.warn(
        #    "Scene %s - %s - %s", self.feature.scene_id, kwargs, data.as_dict()
        # )
        await self._async_state_change(value=self.feature.scene_id)
