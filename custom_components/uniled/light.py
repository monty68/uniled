"""Platform for UniLED light integration."""
from __future__ import annotations

from functools import partial
from typing import Any

from homeassistant.components.light import (
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

from .coordinator import UNILEDUpdateCoordinator
from .entity import UNILEDEntity
from .const import DOMAIN
from .lib.artifacts import UNILEDModelType

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform for UniLED."""
    coordinator: UNILEDUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    _LOGGER.debug("Setup light entities for %s", coordinator.device.name)

    update_channels = partial(
        async_update_channels,
        coordinator,
        set(),
        async_add_entities,
    )

    coordinator.async_add_listener(update_channels)
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

        if self.channel.effect_number is not None:
            extra["effect_number"] = self.channel.effect_number

            if self.channel.effect_type is not None:
                extra["effect_type"] = self.channel.effect_type

            if not self.channel.effect_type_is_static:
                if (rangeof := self.channel.effect_speed_range) is not None:
                    extra[
                        f"effect_speed ({rangeof[0]}-{rangeof[1]})"
                    ] = self.channel.effect_speed
                if (rangeof := self.channel.effect_length_range) is not None:
                    extra[
                        f"effect_length ({rangeof[0]}-{rangeof[1]})"
                    ] = self.channel.effect_length
                if self.channel.effect_direction is not None:
                    extra["effect_direction"] = self.channel.effect_direction
                if (
                    self.channel.effect_type_is_sound
                    and (rangeof := self.channel.input_gain_range) is not None
                ):
                    extra[
                        f"sensitivity ({rangeof[0]}-{rangeof[1]})"
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
        if self.channel.needs_on or not kwargs:
            if not self.is_on:
                await self.channel.async_turn_on()
            if not kwargs:
                return

        if ATTR_RGB_COLOR in kwargs:
            await self.channel.async_set_rgb(kwargs[ATTR_RGB_COLOR])
            return
        if ATTR_RGBW_COLOR in kwargs:
            await self.channel.async_set_rgbw(kwargs[ATTR_RGBW_COLOR])
            return
        if ATTR_BRIGHTNESS in kwargs:
            await self.channel.async_set_level(kwargs[ATTR_BRIGHTNESS])
            return
        if ATTR_WHITE in kwargs:
            await self.channel.async_set_white(kwargs[ATTR_WHITE])
            return
        if ATTR_EFFECT in kwargs:
            if effect := kwargs.get(ATTR_EFFECT, self.effect):
                await self.channel.async_set_effect(effect)
            return

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        await self.channel.async_turn_off()
