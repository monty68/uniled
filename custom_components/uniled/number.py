"""Platform for UniLED number integration."""
from __future__ import annotations

from functools import partial
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.number import NumberEntity, NumberMode

from .const import DOMAIN
from .entity import UNILEDEntity
from .coordinator import UNILEDUpdateCoordinator

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the UniLED number platform."""
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
    rangeof: tuple(int, int, int)

    # Process new channels, add them to Home Assistant
    for channel_id in channel_ids - current_ids:
        current_ids.add(channel_id)
        try:
            channel = coordinator.device.channels[channel_id]
        except IndexError:
            continue
        if channel.effect is not None:
            if (rangeof := channel.effect_speed_range) is not None:
                new_entities.append(
                    UNILEDEffectSpeedNumber(coordinator, channel_id, rangeof)
                )
            if (rangeof := channel.effect_length_range) is not None:
                new_entities.append(
                    UNILEDEffectLengthNumber(coordinator, channel_id, rangeof)
                )
            if (rangeof := channel.input_gain_range) is not None:
                new_entities.append(
                    UNILEDSensitivityNumber(coordinator, channel_id, rangeof)
                )

        if (rangeof := channel.segment_count_range) is not None:
            new_entities.append(
                UNILEDSegmentCountNumber(coordinator, channel_id, rangeof)
            )
        if (rangeof := channel.segment_length_range) is not None:
            new_entities.append(
                UNILEDSegmentLengthNumber(coordinator, channel_id, rangeof)
            )

    async_add_entities(new_entities)


class UNILEDEffectSpeedNumber(
    UNILEDEntity, CoordinatorEntity[UNILEDUpdateCoordinator], NumberEntity
):
    """Defines a UniLED effect speed number control."""

    _attr_entity_registry_enabled_default = True
    _attr_entity_category = None
    _attr_mode = NumberMode.AUTO
    _attr_icon = "mdi:speedometer"

    def __init__(
        self,
        coordinator: UNILEDUpdateCoordinator,
        channel_id: int,
        rangeof: tuple(int, int, int),
    ) -> None:
        """Initialize a UniLED effect speed control."""
        super().__init__(coordinator, channel_id, "Effect Speed", "speed")
        self._attr_native_min_value = rangeof[0]
        self._attr_native_max_value = rangeof[1]
        self._attr_native_step = rangeof[2]

    @property
    def available(self) -> bool:
        if not self.channel.is_on or self.channel.effect_type_is_static:
            return False
        return super().available

    @property
    def native_value(self) -> float:
        """Return the UniLED effect speed."""
        return cast(float, self.channel.effect_speed)

    async def async_set_native_value(self, value: float) -> None:
        """Set the UniLED effect speed value."""
        new_speed = int(value)
        if not self.channel.is_on:
            raise HomeAssistantError("Speed can only be adjusted when the light is on")
        if self.channel.effect_type_is_static:
            raise HomeAssistantError(
                "Effect Speed can only be adjusted when an effect is active"
            )
        await self.channel.async_set_effect_speed(new_speed)


class UNILEDEffectLengthNumber(
    UNILEDEntity, CoordinatorEntity[UNILEDUpdateCoordinator], NumberEntity
):
    """Defines a UniLED effect length number control."""

    _attr_entity_registry_enabled_default = True
    _attr_entity_category = None
    _attr_mode = NumberMode.AUTO
    _attr_icon = "mdi:ruler"

    def __init__(
        self,
        coordinator: UNILEDUpdateCoordinator,
        channel_id: int,
        rangeof: tuple(int, int, int),
    ) -> None:
        """Initialize a UniLED effect length control."""
        super().__init__(coordinator, channel_id, "Effect Length", "length")
        self._attr_native_min_value = rangeof[0]
        self._attr_native_max_value = rangeof[1]
        self._attr_native_step = rangeof[2]

    @property
    def available(self) -> bool:
        if not self.channel.is_on or self.channel.effect_type_is_static:
            return False
        return super().available

    @property
    def native_value(self) -> float:
        """Return the UniLED effect length."""
        return cast(float, self.channel.effect_length)

    async def async_set_native_value(self, value: float) -> None:
        """Set the UniLED effect length value."""
        new_length = int(value)
        if not self.channel.is_on:
            raise HomeAssistantError(
                "Effect length can only be adjusted when the light is on"
            )
        if self.channel.effect_type_is_static:
            raise HomeAssistantError(
                "Effect length can only be adjusted when an effect is active"
            )
        await self.channel.async_set_effect_length(new_length)


class UNILEDSensitivityNumber(
    UNILEDEntity, CoordinatorEntity[UNILEDUpdateCoordinator], NumberEntity
):
    """Defines a UniLED sensitivity number control."""

    _attr_entity_registry_enabled_default = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.AUTO
    _attr_icon = "mdi:knob"

    def __init__(
        self,
        coordinator: UNILEDUpdateCoordinator,
        channel_id: int,
        rangeof: tuple(int, int, int),
    ) -> None:
        """Initialize a UniLED sensitivity control."""
        super().__init__(coordinator, channel_id, "Effect Sensitivity", "sensitivity")
        self._attr_native_min_value = rangeof[0]
        self._attr_native_max_value = rangeof[1]
        self._attr_native_step = rangeof[2]

    @property
    def available(self) -> bool:
        if not self.channel.is_on or not self.channel.effect_type_is_sound:
            return False
        return super().available

    @property
    def native_value(self) -> float:
        """Return the UniLED sensitivity."""
        return cast(float, self.channel.input_gain)

    async def async_set_native_value(self, value: float) -> None:
        """Set the UniLED sensitivity value."""
        new_gain = int(value)
        if not self.channel.is_on:
            raise HomeAssistantError(
                "Sensitivity can only be adjusted when the light is on"
            )
        if not self.channel.effect_type_is_sound:
            raise HomeAssistantError(
                "Sensitivity can only be adjusted when a sound activated effect is active"
            )
        await self.channel.async_set_input_gain(new_gain)


class UNILEDSegmentCountNumber(
    UNILEDEntity, CoordinatorEntity[UNILEDUpdateCoordinator], NumberEntity
):
    """Defines a UniLED segment count number control."""

    _attr_entity_registry_enabled_default = False
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:numeric"

    def __init__(
        self,
        coordinator: UNILEDUpdateCoordinator,
        channel_id: int,
        rangeof: tuple(int, int, int),
    ) -> None:
        """Initialize a UniLED segment count control."""
        super().__init__(coordinator, channel_id, "Segments", "segment_count")
        self._attr_native_min_value = rangeof[0]
        self._attr_native_max_value = rangeof[1]
        self._attr_native_step = rangeof[2]

    @property
    def native_value(self) -> float:
        """Return the UniLED sensitivity."""
        return cast(float, self.channel.segment_count)

    async def async_set_native_value(self, value: float) -> None:
        """Set the UniLED sensitivity value."""
        await self.channel.async_set_segment_count(int(value))


class UNILEDSegmentLengthNumber(
    UNILEDEntity, CoordinatorEntity[UNILEDUpdateCoordinator], NumberEntity
):
    """Defines a UniLED segment length number control."""

    _attr_entity_registry_enabled_default = False
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:numeric"

    def __init__(
        self,
        coordinator: UNILEDUpdateCoordinator,
        channel_id: int,
        rangeof: tuple(int, int, int),
    ) -> None:
        """Initialize a UniLED segment length control."""
        super().__init__(coordinator, channel_id, "Segment Length", "segment_length")
        self._attr_native_min_value = rangeof[0]
        self._attr_native_max_value = rangeof[1]
        self._attr_native_step = rangeof[2]

    @property
    def native_value(self) -> float:
        """Return the UniLED sensitivity."""
        return cast(float, self.channel.segment_length)

    async def async_set_native_value(self, value: float) -> None:
        """Set the UniLED sensitivity value."""
        await self.channel.async_set_segment_length(int(value))
