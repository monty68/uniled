"""Platform for UniLED light integration."""
from __future__ import annotations
from typing import Any
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, callback, CALLBACK_TYPE
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_platform
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.util.color import (
    color_temperature_to_rgbww,
    rgbww_to_color_temperature,
    color_temperature_kelvin_to_mired,
    color_temperature_mired_to_kelvin,
)

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    ATTR_SUPPORTED_COLOR_MODES,
    ATTR_TRANSITION,
    ATTR_WHITE,
    LIGHT_TURN_ON_SCHEMA,
    LightEntity,
    LightEntityFeature,
    ColorMode,
    color_supported,
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
    ATTR_HA_MIN_COLOR_TEMP_KELVIN,
    ATTR_HA_MAX_COLOR_TEMP_KELVIN,
    ATTR_HA_MIN_MIREDS,
    ATTR_HA_MAX_MIREDS,
    ATTR_UL_CCT_COLOR,
    ATTR_UL_DEVICE_FORCE_REFRESH,
    ATTR_UL_DEVICE_NEEDS_ON,
    ATTR_UL_EFFECT_LOOP,
    ATTR_UL_EFFECT_PLAY,
    ATTR_UL_EFFECT_SPEED,
    ATTR_UL_EFFECT_LENGTH,
    ATTR_UL_EFFECT_DIRECTION,
    ATTR_UL_LIGHT_MODE,
    ATTR_UL_SENSITIVITY,
    ATTR_UL_RGB2_COLOR,
    UNILED_DEFAULT_MAX_KELVIN,
    UNILED_DEFAULT_MIN_KELVIN,
    UNILED_DEFAULT_MAX_MIREDS,
    UNILED_DEFAULT_MIN_MIREDS,
)

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

# PARALLEL_UPDATES = 1


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

    def __init__(
        self,
        coordinator: UniledUpdateCoordinator,
        channel: UniledChannel,
        feature: UniledAttribute,
    ) -> None:
        """Initialize a UniLED light control."""
        super().__init__(coordinator, channel, feature)
        self.postponed_update: CALLBACK_TYPE | None = None
        self._attr_max_color_temp_kelvin = UNILED_DEFAULT_MAX_KELVIN
        self._attr_min_color_temp_kelvin = UNILED_DEFAULT_MIN_KELVIN

    @callback
    def _async_update_attrs(self, first: bool = False) -> None:
        """Handle updating _attr values."""
        super()._async_update_attrs()

    @property
    def color_mode(self) -> ColorMode | str | None:
        """Return the color mode of the light."""
        if self.channel.has(ATTR_COLOR_MODE):
            return self.channel.get(ATTR_COLOR_MODE, ColorMode.ONOFF)
        return self._attr_color_mode

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        """Flag supported color modes."""
        if self.channel.has(ATTR_SUPPORTED_COLOR_MODES):
            return self.channel.get(ATTR_SUPPORTED_COLOR_MODES, {ColorMode.ONOFF})
        elif self.channel.has(ATTR_RGBWW_COLOR):
            self._attr_supported_color_modes = {ColorMode.RGBWW}
            self._attr_color_mode = ColorMode.RGBWW
        elif self.channel.has(ATTR_RGBW_COLOR):
            self._attr_supported_color_modes = {ColorMode.RGBW}
            self._attr_color_mode = ColorMode.RGBW
        elif self.channel.has(ATTR_RGB_COLOR):
            self._attr_supported_color_modes = {ColorMode.RGB}
            self._attr_color_mode = ColorMode.RGB
        elif (
            self.channel.has(ATTR_COLOR_TEMP)
            or self.channel.has(ATTR_COLOR_TEMP_KELVIN)
            or self.channel.has(ATTR_UL_CCT_COLOR)
        ):
            self._attr_supported_color_modes = {ColorMode.COLOR_TEMP}
            self._attr_color_mode = ColorMode.COLOR_TEMP
        elif self.channel.has(ATTR_BRIGHTNESS):
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            self._attr_color_mode = ColorMode.ONOFF
        return self._attr_supported_color_modes

    @property
    def supported_features(self) -> LightEntityFeature:
        """Flag supported features."""
        self._attr_supported_features = 0
        if self.channel.has(ATTR_EFFECT):
            self._attr_supported_features |= LightEntityFeature.EFFECT
        if self.channel.has(ATTR_TRANSITION):
            self._attr_supported_features |= LightEntityFeature.TRANSITION
        return self._attr_supported_features

    @property
    def is_on(self) -> bool:
        """Is the switch currently on or not."""
        return self.device.get_state(self.channel, self.feature.attr, False)

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
        if self.channel.has(ATTR_COLOR_TEMP):
            return self.channel.get(ATTR_COLOR_TEMP)
        return color_temperature_kelvin_to_mired(self.color_temp_kelvin)

    @property
    def max_mireds(self) -> int:
        """Return the warmest color_temp that this light supports."""
        return self.channel.get(ATTR_HA_MAX_MIREDS, UNILED_DEFAULT_MAX_MIREDS)

    @property
    def min_mireds(self) -> int:
        """Return the coldest color_temp that this light supports."""
        return self.channel.get(ATTR_HA_MIN_MIREDS, UNILED_DEFAULT_MIN_MIREDS)

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the kelvin value of this light."""
        if self.channel.has(ATTR_COLOR_TEMP_KELVIN):
            return self.channel.get(ATTR_COLOR_TEMP_KELVIN)
        elif self.channel.has(ATTR_UL_CCT_COLOR):
            cold, warm, level, kelvin = self.channel.get(ATTR_UL_CCT_COLOR)
            if not kelvin:
                kelvin, level = rgbww_to_color_temperature(
                    (0, 0, 0, cold, warm),
                    self.min_color_temp_kelvin,
                    self.max_color_temp_kelvin,
                )
            return kelvin
        elif self.channel.has(ATTR_COLOR_TEMP):
            kelvin = color_temperature_mired_to_kelvin(
                self.channel.get(ATTR_COLOR_TEMP)
            )
            return kelvin
        return self._attr_color_temp_kelvin

    @property
    def max_color_temp_kelvin(self) -> int:
        """Max Color Temp in Kelvin"""
        if self.channel.has(ATTR_HA_MAX_COLOR_TEMP_KELVIN):
            return self.channel.get(
                ATTR_HA_MAX_COLOR_TEMP_KELVIN, UNILED_DEFAULT_MAX_KELVIN
            )
        if self.channel.has(ATTR_HA_MIN_MIREDS):
            return color_temperature_mired_to_kelvin(
                self.channel.get(ATTR_HA_MIN_MIREDS)
            )
        return self._attr_max_color_temp_kelvin

    @property
    def min_color_temp_kelvin(self) -> int:
        """Max Color Temp in Kelvin"""
        if self.channel.has(ATTR_HA_MIN_COLOR_TEMP_KELVIN):
            return self.channel.get(
                ATTR_HA_MIN_COLOR_TEMP_KELVIN, UNILED_DEFAULT_MIN_KELVIN
            )
        if self.channel.has(ATTR_HA_MAX_MIREDS):
            return color_temperature_mired_to_kelvin(
                self.channel.get(ATTR_HA_MAX_MIREDS)
            )
        return self._attr_min_color_temp_kelvin

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
        success = False
        async with self.coordinator.lock:
            # Any transition time
            #
            if gradual := kwargs.pop(ATTR_TRANSITION, 0):
                gradual = gradual * 1000

            # Process power state first, in case device needs on before
            # processing any other commands.
            #
            if self.feature.attr in kwargs:
                power = kwargs.pop(self.feature.attr, not self.is_on)
                if not power:
                    success = await self.device.async_set_state(
                        self.channel, self.feature.attr, False
                    )
                    kwargs.clear()
                    # return
                if not self.is_on:
                    if power or (kwargs and self.channel.status.device_needs_on):
                        success = await self.device.async_set_state(
                            self.channel, self.feature.attr, True
                        )

            # If we only have a brightness change to do and the command
            # fails (likely due to unsupported mode), then don't force
            # a device update, as nothing changed.
            #
            if ATTR_BRIGHTNESS in kwargs and len(kwargs) == 1:
                level = kwargs.pop(ATTR_BRIGHTNESS)
                success = await self.device.async_set_state(
                    self.channel, ATTR_BRIGHTNESS, level
                )
                if not success:
                    self.channel.refresh()

            # Set the light mode before we set any effects as some devices use
            # the same effect numbering for different effects etc.
            #
            if (value := kwargs.pop(ATTR_UL_LIGHT_MODE, None)) is not None:
                success = await self.device.async_set_state(
                    self.channel, ATTR_UL_LIGHT_MODE, value
                )

            # Set effect before we set any colors as some devices use
            # different commands depending on what effect is in use.
            #
            if (value := kwargs.pop(ATTR_EFFECT, None)) is not None:
                success = await self.device.async_set_state(self.channel, ATTR_EFFECT, value)

            # Process any color temperature changes here to do a kelvin
            # to cold, warm and brightness conversion first etc.
            #
            mireds = kwargs.pop(ATTR_COLOR_TEMP, None)
            if (kelvin := kwargs.pop(ATTR_COLOR_TEMP_KELVIN, None)) is not None:
                if self.channel.has(ATTR_COLOR_TEMP_KELVIN):
                    success = await self.device.async_set_state(
                        self.channel, ATTR_COLOR_TEMP_KELVIN, kelvin
                    )
                elif self.channel.has(ATTR_UL_CCT_COLOR):
                    level = self.white or self.brightness or 255
                    _, _, _, cold, warm = color_temperature_to_rgbww(
                        kelvin,
                        level,
                        self.min_color_temp_kelvin,
                        self.max_color_temp_kelvin,
                    )
                    success = await self.device.async_set_state(
                        self.channel, ATTR_UL_CCT_COLOR, (cold, warm, level, kelvin)
                    )
                elif self.channel.has(ATTR_COLOR_TEMP):
                    if mireds is not None:
                        await self.device.async_set_state(
                            self.channel, ATTR_COLOR_TEMP, mireds
                        )

            # Process any other commands
            #
            if len(kwargs):
                if await self.device.async_set_multi_state(self.channel, **kwargs) and not success:
                    success = True
                
            if success:
                await self.update_during_transition(gradual)
            # self.coordinator.async_set_updated_data(None)

        if self.channel.status.get(ATTR_UL_DEVICE_FORCE_REFRESH, False) and success and not gradual:
            await self.coordinator.async_request_refresh()

    async def update_during_transition(self, when: int) -> None:
        """Update state at the start and end of a transition."""
        self._cancel_postponed_update()

        # Transition has started
        self.async_write_ha_state()

        # Transition has ended
        if when > 0:
            _LOGGER.debug("Schedule refresh: %s", when)
            await self.coordinator.async_request_refresh()

            async def _async_refresh(now: datetime) -> None:
                """Refresh the state."""
                _LOGGER.debug("%s: Firing postponed update", self.channel.name)
                await self.coordinator.async_refresh()

            self.postponed_update = async_call_later(
                self.hass,
                timedelta(milliseconds=when),
                _async_refresh,
            )

    def _cancel_postponed_update(self) -> None:
        """Cancel postponed update, if applicable."""
        if self.postponed_update:
            self.postponed_update()
            self.postponed_update = None

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self._cancel_postponed_update()
        return await super().async_will_remove_from_hass()
