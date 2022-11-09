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
    def available(self) -> bool:
        """Return True if entity is available."""
        try:
            self.device.channels[self.id]
        except IndexError:
            return False

        return super().available

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
        return self.channel.nameof_effect

    @property
    def effect_list(self) -> list[str]:
        """Return the list of supported effects."""
        return self.channel.listof_effects

    @callback
    def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        _LOGGER.debug("%s: Updating attributes", self.name)

        if self.channel.rgb is not None:
            self._attr_supported_color_modes = {ColorMode.RGB}
            self._attr_color_mode = ColorMode.RGB
            self._attr_rgb_color = self.channel.rgb  # rgb_unscaled
            if self.channel.white is not None:
                self._attr_supported_color_modes = {ColorMode.RGBW}
                self._attr_color_mode = ColorMode.RGBW
                self._attr_rgbw_color = self.channel.rgbw
        if self.channel.effect is not None:
            self._attr_supported_features = LightEntityFeature.EFFECT

        self._attr_brightness = self.channel.level
        self._attr_is_on = self.channel.is_on
        self._attr_effect = self.channel.nameof_effect
        self._attr_effect_list = self.channel.listof_effects

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""

        if self.channel.needs_on or not kwargs:
            if not self.is_on:
                await self.channel.async_turn_on()
            if not kwargs:
                return

        level = kwargs.get(ATTR_BRIGHTNESS, self.brightness)

        if ATTR_RGB_COLOR in kwargs:
            await self.channel.async_set_rgb(kwargs[ATTR_RGB_COLOR], level)
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
                _LOGGER.debug(
                    "%s: Effect, from: %s to: %s",
                    self.device.name,
                    self._attr_effect,
                    effect,
                )
                await self.channel.async_set_effect_byname(effect)
            return

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        await self.channel.async_turn_off()
