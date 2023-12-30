"""Support for UniLED lights."""
from __future__ import annotations
from abc import abstractmethod
from typing import Any, Protocol
from functools import partial

from homeassistant.const import (
    ATTR_CONNECTIONS,
    ATTR_HW_VERSION,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    ATTR_SW_VERSION,
    ATTR_SUGGESTED_AREA,
    Platform,
)
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ATTR_HA_TRANSITION,
    ATTR_UL_INFO_FIRMWARE,
    ATTR_UL_INFO_HARDWARE,
    ATTR_UL_INFO_MODEL_NAME,
    ATTR_UL_INFO_MANUFACTURER,
    ATTR_UL_DEVICE_FORCE_REFRESH,
    ATTR_UL_EFFECT,
    ATTR_UL_EFFECT_NUMBER,
    ATTR_UL_EFFECT_LOOP,
    ATTR_UL_EFFECT_PLAY,
    ATTR_UL_EFFECT_SPEED,
    ATTR_UL_EFFECT_LENGTH,
    ATTR_UL_EFFECT_DIRECTION,
    ATTR_UL_LIGHT_MODE,
    ATTR_UL_LIGHT_MODE_NUMBER,
    ATTR_UL_MAC_ADDRESS,
    ATTR_UL_NODE_ID,
    ATTR_UL_POWER,
    ATTR_UL_SEGMENT_COUNT,
    ATTR_UL_SEGMENT_PIXELS,
    ATTR_UL_STATUS,
    ATTR_UL_SUGGESTED_AREA,
    ATTR_UL_TOTAL_PIXELS,
    UNILED_STATE_CHANGE_LATENCY,
)

from .coordinator import UniledUpdateCoordinator
from .lib.device import UniledDevice, UniledChannel
from .lib.attributes import (
    UniledGroup,
    UniledAttribute,
)
from .lib.net.device import UNILED_TRANSPORT_NET
from .lib.ble.device import UNILED_TRANSPORT_BLE

import asyncio
import logging

_LOGGER = logging.getLogger(__name__)


class UniledEntityInstance(Protocol):
    """Protocol type for adding Uniled entities."""

    def __call__(
        self,
        coordinator: UniledUpdateCoordinator,
        channel: UniledChannel,
        feature: UniledAttribute | None,
    ) -> UniledEntity | None:
        """Define add_entity type."""


async def async_uniled_entity_setup(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    async_add_entity: UniledEntityInstance,
    platform: Platform,
) -> None:
    """Set up the UniLED number platform."""
    coordinator: UniledUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    update_entity = partial(
        async_uniled_entity_update,
        coordinator,
        async_add_entities,
        async_add_entity,
        platform,
        set(),
    )

    entry.async_on_unload(coordinator.async_add_listener(update_entity))
    update_entity()


@callback
def async_uniled_entity_update(
    coordinator: UniledUpdateCoordinator,
    async_add_entities: AddEntitiesCallback,
    async_add_entity: UniledEntityInstance,
    platform: Platform,
    current_ids: set[int],
) -> None:
    """Update channels."""
    new_entities: list[UniledEntity] = []

    # Process new channels, add them to Home Assistant
    for channel in coordinator.device.channel_list:
        if channel.number in current_ids:
            continue
        current_ids.add(channel.number)

        if entity := async_add_entity(coordinator, channel, None):
            if isinstance(entity, list):
                new_entities.extend(entity)
            else:
                new_entities.append(entity)

        if not channel.features:
            continue

        for feature in channel.features:
            if not feature.platform.startswith(platform):
                continue
            if entity := async_add_entity(coordinator, channel, feature):
                new_entities.append(entity)

    if len(new_entities):
        async_add_entities(new_entities)


class UniledEntity(CoordinatorEntity[UniledUpdateCoordinator]):
    """Representation of a UniLED entity with a coordinator."""

    _unrecorded_attributes = frozenset(
        {
            ATTR_HA_TRANSITION,
            ATTR_UL_INFO_FIRMWARE,
            ATTR_UL_INFO_HARDWARE,
            ATTR_UL_INFO_MODEL_NAME,
            ATTR_UL_INFO_MANUFACTURER,
            ATTR_UL_EFFECT,
            ATTR_UL_EFFECT_NUMBER,
            ATTR_UL_EFFECT_LOOP,
            ATTR_UL_EFFECT_PLAY,
            ATTR_UL_EFFECT_SPEED,
            ATTR_UL_EFFECT_LENGTH,
            ATTR_UL_EFFECT_DIRECTION,
            ATTR_UL_LIGHT_MODE,
            ATTR_UL_LIGHT_MODE_NUMBER,
            ATTR_UL_MAC_ADDRESS,
            ATTR_UL_NODE_ID,
            ATTR_UL_SEGMENT_COUNT,
            ATTR_UL_SEGMENT_PIXELS,
            ATTR_UL_STATUS,
            ATTR_UL_SUGGESTED_AREA,
            ATTR_UL_TOTAL_PIXELS,
        }
    )

    def __init__(
        self,
        coordinator: UniledUpdateCoordinator,
        channel: UniledChannel,
        feature: UniledAttribute,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device: UniledDevice = coordinator.device
        self._channel: UniledChannel = channel
        self._feature: UniledAttribute = feature
        self._attr_has_entity_name = True

        if channel.name:
            if feature.name.lower() not in channel.name.lower():
                self._attr_name = f"{channel.name} {feature.name}"
            else:
                self._attr_name = f"{channel.name}"
        else:
            self._attr_name = f"{feature.name}"

        if self._attr_name.lower() == feature.platform:
            self._attr_name = None

        base_unique_id = coordinator.entry.unique_id or coordinator.entry.entry_id
        self._attr_unique_id = f"_{base_unique_id}"

        if channel.identity is not None:
            if mangled_name := channel.identity.replace(" ", "_").lower():
                self._attr_unique_id = f"{self._attr_unique_id}_{mangled_name}"

        if (key := getattr(feature, "key", None)) is not None:
            self._attr_unique_id = f"{self._attr_unique_id}_{key}"

        # _LOGGER.debug("%s: %s (%s)", self._attr_unique_id, self._attr_name, channel.name)

        self._attr_entity_registry_enabled_default = feature.enabled
        self._attr_entity_category = None
        self._attr_icon = feature.icon

        if feature.group == UniledGroup.CONFIGURATION:
            self._attr_entity_category = EntityCategory.CONFIG
        elif feature.group == UniledGroup.DIAGNOSTIC:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._async_update_attrs(first=True)

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        self.async_on_remove(
            self._channel.register_callback(self._handle_coordinator_update)
        )
        await super().async_added_to_hass()

    def _async_device_info(
        self, device: UniledDevice, entry: config_entries.ConfigEntry
    ) -> DeviceInfo:
        device_info: DeviceInfo = {
            ATTR_IDENTIFIERS: {(DOMAIN, entry.entry_id)},
            ATTR_NAME: device.name,
            ATTR_MODEL: device.master.get(
                ATTR_UL_INFO_HARDWARE, device.description
            ),
            ATTR_MANUFACTURER: device.master.get(
                ATTR_UL_INFO_MANUFACTURER, device.manufacturer
            ),
            ATTR_HW_VERSION: device.master.get(ATTR_UL_INFO_MODEL_NAME, device.model_name),
            ATTR_SW_VERSION: device.master.get(ATTR_UL_INFO_FIRMWARE, None),
            ATTR_SUGGESTED_AREA: device.master.get(ATTR_UL_SUGGESTED_AREA, None),
        }

        if device.transport == UNILED_TRANSPORT_NET:
            if entry.unique_id:
                device_info[ATTR_CONNECTIONS] = {
                    (dr.CONNECTION_NETWORK_MAC, entry.unique_id)
                }
        elif device.transport == UNILED_TRANSPORT_BLE:
            device_info[ATTR_CONNECTIONS] = {(dr.CONNECTION_BLUETOOTH, device.address)}

        return device_info

    async def _async_delayed_reload(
        self, hass: HomeAssistant, entry: config_entries.ConfigEntry
    ) -> None:
        """Reload after making a change that will effect the operation of the device."""
        await asyncio.sleep(UNILED_STATE_CHANGE_LATENCY)
        _LOGGER.warning("Reloading...")
        hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))

    @callback
    def _handle_coordinator_update(self, *args: Any) -> None:
        """Handle updated data from the coordinator."""
        self._async_update_attrs()
        self.async_write_ha_state()

    @callback
    def _async_update_attrs(self, first: bool = False) -> None:
        """Update entity attributes"""
        self._attr_device_info = self._async_device_info(
            self._device, self.coordinator.entry
        )

    async def _async_state_change(self, value: Any) -> None:
        """Update device with new entity value/state"""
        success = await self.device.async_set_state(
            self.channel, self.feature.attr, value
        )
        if self.channel.status.get(ATTR_UL_DEVICE_FORCE_REFRESH, False):
            # await self.coordinator.async_request_refresh()
            await self.coordinator.async_refresh()
        else:
            self._async_update_attrs()
        if self.feature.reload and success:
            ## TODO Can we warn the user there will be a reload??
            await self._async_delayed_reload(self.hass, self.coordinator.entry)

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        extra = {}
        if self.feature and self.feature.extra:
            for x in self.feature.extra:
                if (value := self.device.get_state(self.channel, x)) is not None:
                    extra[x] = value
        return extra

    @property
    def available(self) -> bool:
        """Return if entity is available"""
        if self.feature.attr and not self.channel.has(self.feature.attr):
            return False
        if self.feature.group == UniledGroup.NEEDS_ON and not self.channel.is_on:
            return False
        # Needs checking with other transport models!
        if (
            self.feature.attr == ATTR_UL_POWER
            and self.channel.get(self.feature.attr, None) is None
        ):
            return False
        return super().available

    @property
    def id(self) -> int:
        """Return channel id"""
        return self._channel.number

    @property
    def channel(self) -> UniledChannel:
        """Return UniLED channel object"""
        return self._channel

    @property
    def feature(self) -> UniledAttribute:
        """Return UniLED channel object"""
        return self._feature

    @property
    def device(self) -> UniledDevice:
        """Return UniLED device object"""
        return self._device
