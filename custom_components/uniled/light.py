"""Platform for UniLED light integration."""
from __future__ import annotations
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_platform
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.util.color import (
    color_temperature_to_rgbww,
    rgbww_to_color_temperature,
    color_temperature_kelvin_to_mired,
    color_temperature_mired_to_kelvin,
)

from homeassistant.components.light import (
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_COLOR_TEMP,
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    ATTR_WHITE,
    LIGHT_TURN_ON_SCHEMA,
    LightEntity,
    LightEntityFeature,
    ColorMode,
)

from .entity import (
    UniledUpdateCoordinator,
    UniledChannel,
    UniledEntity,
    Platform,
    async_uniled_entity_setup,
    AddEntitiesCallback,
    DOMAIN,
)

from .lib.attributes import UniledAttribute

from .lib.const import (
    UNILED_COMMAND_SETTLE_DELAY,
    UNILED_EXTRA_ATTRIBUTE_TYPE,
    UNILED_DEFAULT_MIN_KELVIN,
    UNILED_DEFAULT_MAX_KELVIN,
    ATTR_HA_MIN_COLOR_TEMP_KELVIN,
    ATTR_HA_MAX_COLOR_TEMP_KELVIN,
    ATTR_UL_CCT_COLOR,
    ATTR_UL_DEVICE_FORCE_REFRESH,
    ATTR_UL_DEVICE_NEEDS_ON,
    ATTR_UL_EFFECT,
    ATTR_UL_EFFECT_NUMBER,
    ATTR_UL_EFFECT_LOOP,
    ATTR_UL_EFFECT_PLAY,
    ATTR_UL_EFFECT_SPEED,
    ATTR_UL_EFFECT_LENGTH,
    ATTR_UL_EFFECT_DIRECTION,
    ATTR_UL_LIGHT_MODE,
    ATTR_UL_LIGHT_MODE_NUMBER,
    ATTR_UL_SEGMENT_COUNT,
    ATTR_UL_SEGMENT_PIXELS,
    ATTR_UL_TOTAL_PIXELS,
    ATTR_UL_SENSITIVITY,
    ATTR_UL_RGB2_COLOR,
)

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the UniLED number platform."""
    coordinator: UniledUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    platform = entity_platform.async_get_current_platform()

    ## @todo Build service more dynamically!
    ##
    schema = {
        **LIGHT_TURN_ON_SCHEMA,
    }

    schema[ATTR_UL_LIGHT_MODE] = vol.All(vol.Coerce(int), vol.Clamp(min=1, max=255))
    schema[ATTR_UL_RGB2_COLOR] = vol.All(
        vol.Coerce(tuple), vol.ExactSequence((cv.byte,) * 3)
    )
    schema[ATTR_UL_EFFECT_LOOP] = cv.boolean
    schema[ATTR_UL_EFFECT_PLAY] = cv.boolean
    schema[ATTR_UL_EFFECT_SPEED] = vol.All(vol.Coerce(int), vol.Clamp(min=1, max=255))
    schema[ATTR_UL_EFFECT_LENGTH] = vol.All(vol.Coerce(int), vol.Clamp(min=1, max=255))
    schema[ATTR_UL_EFFECT_DIRECTION] = cv.boolean
    schema[ATTR_UL_SENSITIVITY] = vol.All(vol.Coerce(int), vol.Clamp(min=1, max=255))

    platform.async_register_entity_service("set_state", schema, "async_set_state")

    await async_uniled_entity_setup(
        hass, entry, async_add_entities, _add_light_entity, Platform.LIGHT
    )


def _add_light_entity(
    coordinator: UniledUpdateCoordinator,
    channel: UniledChannel,
    feature: UniledAttribute | None,
) -> UniledEntity | None:
    """Create UniLED number entity."""
    return None if not feature else UniledLightEntity(coordinator, channel, feature)


class UniledLightEntity(
    UniledEntity, CoordinatorEntity[UniledUpdateCoordinator], LightEntity
):
    """Defines a UniLED light control."""

    _unrecorded_attributes = frozenset(
        {
            ATTR_UL_LIGHT_MODE,
            ATTR_UL_LIGHT_MODE_NUMBER,
            ATTR_UL_EFFECT,
            ATTR_UL_EFFECT_NUMBER,
            ATTR_UL_EFFECT_LOOP,
            ATTR_UL_EFFECT_PLAY,
            ATTR_UL_EFFECT_SPEED,
            ATTR_UL_EFFECT_LENGTH,
            ATTR_UL_EFFECT_DIRECTION,
            ATTR_UL_SEGMENT_COUNT,
            ATTR_UL_SEGMENT_PIXELS,
            ATTR_UL_TOTAL_PIXELS,
        }
    )

    def __init__(
        self,
        coordinator: UniledUpdateCoordinator,
        channel: UniledChannel,
        feature: UniledAttribute,
    ) -> None:
        """Initialize a UniLED light control."""
        super().__init__(coordinator, channel, feature)

    @callback
    def _async_update_attrs(self, first: bool = False) -> None:
        """Handle updating _attr values."""
        super()._async_update_attrs()

        if self.channel.has(ATTR_RGBWW_COLOR):
            self._attr_supported_color_modes = {ColorMode.RGBWW}
            self._attr_color_mode = ColorMode.RGBWW
        elif self.channel.has(ATTR_RGBW_COLOR):
            self._attr_supported_color_modes = {ColorMode.RGBW}
            self._attr_color_mode = ColorMode.RGBW
        elif self.channel.has(ATTR_RGB_COLOR):
            self._attr_supported_color_modes = {ColorMode.RGB}
            self._attr_color_mode = ColorMode.RGB
        elif self.channel.has(ATTR_UL_CCT_COLOR) or self.channel.has(
            ATTR_COLOR_TEMP_KELVIN
        ):
            self._attr_supported_color_modes = {ColorMode.COLOR_TEMP}
            self._attr_color_mode = ColorMode.COLOR_TEMP
        elif self.channel.has(ATTR_WHITE):
            self._attr_supported_color_modes = {ColorMode.WHITE}
            self._attr_color_mode = ColorMode.WHITE
        elif self.channel.has(ATTR_BRIGHTNESS):
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            self._attr_color_mode = ColorMode.ONOFF

        if self.channel.has(ATTR_EFFECT):
            self._attr_supported_features = LightEntityFeature.EFFECT

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        extra = {}
        for feature in self.channel.features:
            if feature.type != UNILED_EXTRA_ATTRIBUTE_TYPE:
                continue
            if (value := self.device.get_state(self.channel, feature.attr)) is not None:
                key = feature.attr if feature.key is None else feature.key
                extra[key] = value
        return extra

    @property
    def is_on(self) -> bool:
        """Is the switch currently on or not."""
        return self.device.get_state(self.channel, self.feature.attr)

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 1..255."""
        return self.device.get_state(self.channel, ATTR_BRIGHTNESS)

    @property
    def white(self) -> int | None:
        """Return the white level of this light between 1..255."""
        return self.device.get_state(self.channel, ATTR_WHITE)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the color value."""
        return self.device.get_state(self.channel, ATTR_RGB_COLOR)

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        """Return the color value."""
        return self.device.get_state(self.channel, ATTR_RGBW_COLOR)

    @property
    def rgbww_color(self) -> tuple[int, int, int, int, int] | None:
        """Return the rgbww aka rgbcw color value."""
        return self.device.get_state(self.channel, ATTR_RGBWW_COLOR)

    @property
    def color_temp(self) -> int | None:
        """Return the mired value of this light."""
        return color_temperature_kelvin_to_mired(self.color_temp_kelvin)

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the kelvin value of this light."""
        if self.channel.has(ATTR_COLOR_TEMP_KELVIN):
            return self.device.get_state(self.channel, ATTR_COLOR_TEMP_KELVIN)
        elif self.channel.has(ATTR_UL_CCT_COLOR):
            cold, warm, level, kelvin = self.device.get_state(
                self.channel, ATTR_UL_CCT_COLOR
            )
            if not kelvin:
                kelvin, level = rgbww_to_color_temperature(
                    (0, 0, 0, cold, warm),
                    self.min_color_temp_kelvin,
                    self.max_color_temp_kelvin,
                )
            return kelvin
        return self._attrcolor_temp_kelvin

    @property
    def min_color_temp_kelvin(self) -> int:
        """Max Color Temp in Kelvins"""
        return self.channel.status.get(
            ATTR_HA_MIN_COLOR_TEMP_KELVIN, UNILED_DEFAULT_MIN_KELVIN
        )

    @property
    def max_color_temp_kelvin(self) -> int:
        """Max Color Temp in Kelvins"""
        return self.channel.status.get(
            ATTR_HA_MAX_COLOR_TEMP_KELVIN, UNILED_DEFAULT_MAX_KELVIN
        )

    @property
    def effect(self) -> str | None:
        """Effect Name"""
        return self.device.get_state(self.channel, ATTR_EFFECT)

    @property
    def effect_list(self) -> list | None:
        """Effect List"""
        return self.device.get_list(self.channel, ATTR_EFFECT)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on (forwards)."""
        await self.async_set_state(**{**kwargs, self.feature.attr: True})

    async def async_turn_off(self, **kwargs):
        """Turn the entity off (backwards)."""
        await self.async_set_state(**{**kwargs, self.feature.attr: False})

    async def async_set_state(self, **kwargs: Any) -> None:
        """Control a light"""
        self.coordinator.async_set_updated_data(None)
        async with self.coordinator.lock:
            # Process power state first, in case device needs on before
            # processing any other commands.
            #
            if self.feature.attr in kwargs:
                power = kwargs.pop(self.feature.attr, not self.is_on)
                if not power:
                    await self.device.async_set_state(
                        self.channel, self.feature.attr, False
                    )
                    kwargs.clear()
                    # return
                if not self.is_on:
                    if power or (kwargs and self.channel.status.device_needs_on):
                        await self.device.async_set_state(
                            self.channel, self.feature.attr, True
                        )

            # Set the light mode before we set any effects as some devices use
            # the same effect numbering for different effects etc.
            #
            if (value := kwargs.pop(ATTR_UL_LIGHT_MODE, None)) is not None:
                await self.device.async_set_state(
                    self.channel, ATTR_UL_LIGHT_MODE, value
                )

            # Set effect before we set any colors as some devices use
            # different commands depending on what effect is in use.
            #
            if (value := kwargs.pop(ATTR_EFFECT, None)) is not None:
                await self.device.async_set_state(self.channel, ATTR_EFFECT, value)

            # Process any color temperature changes here to do a kelvin
            # to cold, warm and brightness conversion first
            #
            if (mired := kwargs.pop(ATTR_COLOR_TEMP, None)) is not None:
                pass

            if (kelvin := kwargs.pop(ATTR_COLOR_TEMP_KELVIN, None)) is not None:
                if self.channel.has(ATTR_COLOR_TEMP_KELVIN):
                    await self.device.async_set_state(
                        self.channel, ATTR_COLOR_TEMP_KELVIN, kelvin
                    )
                elif self.channel.has(ATTR_UL_CCT_COLOR):
                    level = self.white
                    _, _, _, cold, warm = color_temperature_to_rgbww(
                        kelvin,
                        level,
                        self.min_color_temp_kelvin,
                        self.max_color_temp_kelvin,
                    )
                    await self.device.async_set_state(
                        self.channel, ATTR_UL_CCT_COLOR, (cold, warm, level, kelvin)
                    )

            # Process any other commands
            #
            if len(kwargs):
                await self.device.async_set_multi_state(self.channel, **kwargs)

        if self.channel.status.get(ATTR_UL_DEVICE_FORCE_REFRESH, False):
            await self.coordinator.async_request_refresh()

    ## May not be needed now?
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
