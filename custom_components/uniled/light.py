"""Platform for UniLED light integration."""
from __future__ import annotations

from functools import partial
from typing import Any

from homeassistant.components.light import (
    LIGHT_TURN_ON_SCHEMA,
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_WHITE,
    LightEntity,
    LightEntityFeature,
    ColorMode,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import entity_platform
import homeassistant.helpers.config_validation as cv

from .coordinator import UNILEDUpdateCoordinator
from .entity import UNILEDEntity
from .lib.artifacts import UNILEDModelType, UNILEDEffectDirection
from .const import (
    DOMAIN,
    COMMAND_SETTLE_DELAY,
    ATTR_POWER,
    ATTR_MODE,
    ATTR_RGB2_COLOR,
    ATTR_EFFECT_NUMBER,
    ATTR_EFFECT_TYPE,
    ATTR_EFFECT_SPEED,
    ATTR_EFFECT_LENGTH,
    ATTR_EFFECT_DIRECTION,
    ATTR_SENSITIVITY,
)

import voluptuous as vol
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

UNILED_EFFECT_BACKWARDS = UNILEDEffectDirection.BACKWARDS.lower()
UNILED_EFFECT_FORWARDS = UNILEDEffectDirection.FORWARDS.lower()

UNILED_EFFECT_DIRECTIONS = {UNILED_EFFECT_BACKWARDS, UNILED_EFFECT_FORWARDS}

UNILED_SERVICE_SET_STATE = "set_state"
UNILED_SET_STATE_SCHEMA = {
    **LIGHT_TURN_ON_SCHEMA,
    ATTR_RGB2_COLOR: vol.All(vol.Coerce(tuple), vol.ExactSequence((cv.byte,) * 3)),
    ATTR_EFFECT_SPEED: vol.All(vol.Coerce(int), vol.Clamp(min=1, max=255)),
    ATTR_EFFECT_LENGTH: vol.All(vol.Coerce(int), vol.Clamp(min=1, max=255)),
    ATTR_EFFECT_DIRECTION: vol.All(vol.Coerce(str), vol.In(UNILED_EFFECT_DIRECTIONS)),
    ATTR_SENSITIVITY: vol.All(vol.Coerce(int), vol.Clamp(min=1, max=255)),
    ATTR_POWER: cv.boolean,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform for UniLED."""
    coordinator: UNILEDUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        UNILED_SERVICE_SET_STATE, UNILED_SET_STATE_SCHEMA, "async_set_state"
    )

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
    """Update channelss."""
    channel_ids = {channel.number for channel in coordinator.device.channels}
    new_entities: list[UNILEDLight] = []

    # Process new channels, add them to Home Assistant
    for channel_id in channel_ids - current_ids:
        current_ids.add(channel_id)
        new_entities.append(UNILEDLight(coordinator, channel_id))

    async_add_entities(new_entities)


class UNILEDLight(
    UNILEDEntity, CoordinatorEntity[UNILEDUpdateCoordinator], LightEntity
):
    """Representation of UniLED device."""

    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, coordinator: UNILEDUpdateCoordinator, channel_id: int) -> None:
        """Initialize a UniLED light."""
        super().__init__(coordinator, channel_id, "Light", "strip")
        self._attr_icon = self.icon
        self._async_update_attrs()

    @property
    def icon(self) -> str:
        if self.device.model_type == UNILEDModelType.STRIP:
            return "mdi:led-strip-variant"
        return "mdi:lightbulb"

    @property
    def is_on(self) -> bool:
        """Return the state of the light."""
        return self.channel.is_on

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 1..255."""
        return self.channel.level

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the color value."""
        return self.channel.rgb

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        """Return the color value."""
        return self.channel.rgbw

    @property
    def effect(self) -> str | None:
        """Return the current effect of the light."""
        return self.channel.effect

    @property
    def effect_list(self) -> list[str]:
        """Return the list of supported effects."""
        return self.channel.effect_list

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        extra = {}

        if self.channel.mode is not None:
            extra[ATTR_MODE] = self.channel.mode

        if self.channel.effect_number is not None:
            extra[ATTR_EFFECT_NUMBER] = self.channel.effect_number

            if self.channel.effect_type is not None:
                extra[ATTR_EFFECT_TYPE] = self.channel.effect_type

            if not self.channel.effect_type_is_static:
                if (rangeof := self.channel.effect_speed_range) is not None:
                    extra[
                        f"{ATTR_EFFECT_SPEED} ({rangeof[0]}-{rangeof[1]})"
                    ] = self.channel.effect_speed
                if (rangeof := self.channel.effect_length_range) is not None:
                    extra[
                        f"{ATTR_EFFECT_LENGTH} ({rangeof[0]}-{rangeof[1]})"
                    ] = self.channel.effect_length
                if self.channel.effect_direction is not None:
                    extra[ATTR_EFFECT_DIRECTION] = self.channel.effect_direction
                if (
                    self.channel.effect_type_is_sound
                    and (rangeof := self.channel.input_gain_range) is not None
                ):
                    extra[
                        f"{ATTR_SENSITIVITY} ({rangeof[0]}-{rangeof[1]})"
                    ] = self.channel.input_gain
        return extra

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        if self.channel.rgb is not None:
            self._attr_supported_color_modes = {ColorMode.RGB}
            self._attr_color_mode = ColorMode.RGB
            self._attr_rgb_color = self.channel.rgb  # rgb_unscaled
            if self.channel.white is not None:
                self._attr_supported_color_modes = {ColorMode.RGBW}
                self._attr_color_mode = ColorMode.RGBW
                self._attr_rgbw_color = self.channel.rgbw
        elif self.channel.level is not None:
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_supported_color_modes = {ColorMode.ONOFF}

        if self.channel.effect is not None:
            self._attr_supported_features = LightEntityFeature.EFFECT

        self._attr_brightness = self.channel.level
        self._attr_is_on = self.channel.is_on
        self._attr_effect = self.channel.effect
        self._attr_effect_list = self.channel.effect_list
        self._attr_extra_state_attributes = self.extra_state_attributes

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        await self.async_set_state(**{**kwargs, ATTR_POWER: True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        await self.async_set_state(**{**kwargs, ATTR_POWER: False})

    async def async_set_state(self, **kwargs: Any) -> None:
        """Control a light"""
        self.coordinator.async_set_updated_data(None)
        async with self.coordinator.lock:
            _LOGGER.debug("%s: set_state: %s", self.name, kwargs)

            if ATTR_POWER in kwargs:
                power = kwargs.pop(ATTR_POWER, not self.is_on)
                if not power:
                    await self.channel.async_turn_off()
                    return
                if not self.is_on:
                    if power or (kwargs and self.channel.needs_on):
                        await self.channel.async_turn_on()

            # Must set effect before we set any colors as some devices use
            # different commands depending on what effect is in use!
            #
            if ATTR_EFFECT in kwargs:
                if effect := kwargs.get(ATTR_EFFECT, self.effect):
                    await self.channel.async_set_effect(effect)

            if ATTR_RGB_COLOR in kwargs:
                await self.channel.async_set_rgb(kwargs[ATTR_RGB_COLOR])
            if ATTR_RGBW_COLOR in kwargs:
                await self.channel.async_set_rgbw(kwargs[ATTR_RGBW_COLOR])
            if ATTR_BRIGHTNESS in kwargs:
                await self.channel.async_set_level(kwargs[ATTR_BRIGHTNESS])
            if ATTR_WHITE in kwargs:
                await self.channel.async_set_white(kwargs[ATTR_WHITE])

            # Some extra settings available through service calls
            #
            if ATTR_RGB2_COLOR in kwargs:
                await self.channel.async_set_rgb2(kwargs[ATTR_RGB2_COLOR])

            if ATTR_EFFECT_SPEED in kwargs:
                value = self._clamp_to_rangeof(
                    kwargs.get(ATTR_EFFECT_SPEED, -1), self.channel.effect_speed_range
                )
                await self.channel.async_set_effect_speed(value)

            if ATTR_EFFECT_LENGTH in kwargs:
                value = self._clamp_to_rangeof(
                    kwargs.get(ATTR_EFFECT_LENGTH, -1), self.channel.effect_length_range
                )
                await self.channel.async_set_effect_length(value)

            if ATTR_EFFECT_DIRECTION in kwargs:
                direction = (
                    True
                    if kwargs[ATTR_EFFECT_DIRECTION] == UNILED_EFFECT_FORWARDS
                    else False
                )
                await self.channel.async_set_effect_direction(direction)

            if ATTR_SENSITIVITY in kwargs:
                value = self._clamp_to_rangeof(
                    kwargs.get(ATTR_SENSITIVITY, -1), self.channel.input_gain_range
                )
                await self.channel.async_set_input_gain(value)

        if not self.channel.sends_status_on_commands:
            await asyncio.sleep(COMMAND_SETTLE_DELAY)
            await self.coordinator.async_refresh()

    def _clamp_to_rangeof(
        self, value: int, rangeof: tuple(int, int, int) | None
    ) -> int | None:
        """Clamp a value to a specified range"""
        try:
            if value < rangeof[0]:
                return rangeof[0]
            if value > rangeof[1]:
                return rangeof[1]
            return value
        except TypeError:
            pass
        return None
