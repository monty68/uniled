"""UniLed Base Classes"""
from __future__ import annotations

from dataclasses import dataclass, replace
from collections.abc import Callable
from abc import abstractmethod

from .artifacts import (
    UNILED_CHIP_ORDER_3COLOR,
    UNILED_CHIP_TYPES,
    UNILEDModelType,
    UNILEDEffectType,
)
from .states import UNILEDStatus

import weakref
import colorsys
import logging

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class UNILEDModel:
    """UniLED Base Model Class"""

    model_num: int  # The model number
    model_name: str  # The model name
    model_type: UNILEDModelType  # Type of device model
    description: str  # Description of the model ({type} {color_mode})
    manufacturer: str  # The manufacturers name
    manufacturer_id: int
    channels: int
    needs_on: bool
    sends_status_on_commands: bool

    ##
    ## Protocol Wrapper
    ##
    def construct_message(self, raw_bytes: bytearray) -> bytearray:
        """Base protocol uses no checksum."""
        return raw_bytes

    ##
    ## Device Control
    ##
    def construct_connect_message(self, device: UNILEDDevice) -> list[bytearray] | None:
        """The bytes to send when first connecting."""
        return None

    @abstractmethod
    def construct_status_query(self, device: UNILEDDevice) -> list[bytearray] | None:
        """The bytes to send for a status query."""

    @abstractmethod
    def async_decode_notifications(
        self, device: UNILEDDevice, sender: int, data: bytearray
    ) -> UNILEDStatus | None:
        """Handle notification responses."""

    ##
    ## Channel Control
    ##
    @abstractmethod
    def construct_power_change(
        self, channel: UNILEDChannel, turn_on: int
    ) -> list[bytearray] | None:
        """The bytes to send for a power state change."""

    def construct_mode_change(
        self, channel: UNILEDChannel, mode: str
    ) -> list[bytearray] | None:
        """The bytes to send for a mode change."""
        return None

    def construct_level_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a color level change."""
        return None

    def construct_white_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a white level change."""
        return None

    def construct_color_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int, white: int | None
    ) -> list[bytearray] | None:
        """The bytes to send for a color change."""
        return None

    def construct_color_two_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int
    ) -> list[bytearray] | None:
        """The bytes to send for a second color change."""
        return None

    def construct_effect_change(
        self, channel: UNILEDChannel, effect: int
    ) -> list[bytearray] | None:
        """The bytes to send for an effect change."""
        return None

    def construct_effect_speed_change(
        self, channel: UNILEDChannel, speed: int
    ) -> list[bytearray] | None:
        """The bytes to send for an effect speed change."""
        return None

    def construct_effect_length_change(
        self, channel: UNILEDChannel, length: int
    ) -> list[bytearray] | None:
        """The bytes to send for an efect length change."""
        return None

    def construct_effect_direction_change(
        self, channel: UNILEDChannel, direction: int
    ) -> list[bytearray] | None:
        """The bytes to send for an efect direction change."""
        return None

    ##
    ## Channel Configuration
    ##
    def construct_input_change(
        self, channel: UNILEDChannel, input_type: int
    ) -> list[bytearray] | None:
        """The bytes to send for an input change."""
        return None

    def construct_input_gain_change(
        self, channel: UNILEDChannel, gain: int
    ) -> list[bytearray] | None:
        """The bytes to send for a gain/sensitivity change"""
        return None

    def construct_chip_type_change(
        self, channel: UNILEDChannel, chip_type: int
    ) -> list[bytearray] | None:
        """The bytes to send for a chip type change"""
        return None

    def construct_chip_order_change(
        self, channel: UNILEDChannel, chip_order: int
    ) -> list[bytearray] | None:
        """The bytes to send for a chip order change"""
        return None

    def construct_segment_count_change(
        self, channel: UNILEDChannel, count: int
    ) -> list[bytearray] | None:
        """The bytes to send for a segment count change"""
        return None

    def construct_segment_length_change(
        self, channel: UNILEDChannel, length: int
    ) -> list[bytearray] | None:
        """The bytes to send for a segment length change"""
        return None

    ##
    ## Channel Informational
    ##
    def listof_channel_modes(self, channel: UNILEDChannel) -> list | None:
        """List of available channel modes"""
        return None

    def codeof_channel_mode(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named mode"""
        return None

    def nameof_channel_mode(
        self, channel: UNILEDChannel, mode: int | None = None
    ) -> str | None:
        """Name a mode."""
        return None

    def listof_channel_effects(self, channel: UNILEDChannel) -> list | None:
        """List of available channel effects"""
        return None

    def codeof_channel_effect(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named channel effect"""
        return None

    def nameof_channel_effect(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> str | None:
        """Name an effect."""
        return None

    def codeof_channel_effect_type(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> int | None:
        """Code of channel effect type from effect code"""
        return None

    def nameof_channel_effect_type(
        self, channel: UNILEDChannel, fxtype: int | None = None
    ) -> str | None:
        """Name an effects type."""
        return None

    def rangeof_channel_effect_speed(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        return None

    def rangeof_channel_effect_length(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect length (min,max,step)."""
        return None

    def nameof_channel_input_type(
        self, channel: UNILEDChannel, audio_input: int | None = None
    ) -> str | None:
        """Name a channel input type."""
        return None

    def codeof_channel_input_type(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named input type"""
        return None

    def listof_channel_inputs(self, channel: UNILEDChannel) -> list | None:
        """List of available channel inputs."""
        return None

    def rangeof_channel_input_gain(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return None

    def rangeof_channel_segment_count(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of channel segments (min,max,step)."""
        return None

    def rangeof_channel_segment_length(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of segment LEDs (min,max,step)."""
        return None

    def rangeof_channel_led_total(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of total LEDs (min,max,step)."""
        return None

    def nameof_channel_chip_order(
        self, channel: UNILEDChannel, order: int | None = None
    ) -> str | None:
        """Name a chip order."""
        if channel.status.chip_order is not None:
            if order is None:
                order = channel.status.chip_order
            if order in UNILED_CHIP_ORDER_3COLOR:
                return UNILED_CHIP_ORDER_3COLOR[order]
        return None

    def codeof_channel_chip_order(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named chip order"""
        if name is None:
            return None
        return [k for k in UNILED_CHIP_ORDER_3COLOR.items() if k[1] == name][0][0]

    def listof_channel_chip_orders(self, channel: UNILEDChannel) -> list | None:
        """List of available chip orders"""
        if channel.status.chip_order is not None:
            return list(UNILED_CHIP_ORDER_3COLOR.values())
        return None

    def nameof_channel_chip_type(
        self, channel: UNILEDChannel, chip: int | None = None
    ) -> str | None:
        """Name a chip type."""
        if channel.status.chip_type is not None:
            if chip is None:
                chip = channel.status.chip_type
            if chip in UNILED_CHIP_TYPES:
                return UNILED_CHIP_TYPES[chip]
        return None

    def codeof_channel_chip_type(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named chip type"""
        if name is None:
            return None
        return [k for k in UNILED_CHIP_TYPES.items() if k[1] == name][0][0]

    def listof_channel_chip_types(self, channel: UNILEDChannel) -> list | None:
        """List of available chip types"""
        if channel.status.chip_type is not None:
            return list(UNILED_CHIP_TYPES.values())
        return None


class UNILEDChannel:
    """UniLED Channel Class"""

    def __init__(self, device: UNILEDDevice, number: int) -> None:
        self._callbacks: list[Callable[[UNILEDChannel], None]] = []
        self._number: int = number
        self._device: weakref.ProxyType(UNILEDDevice) = weakref.proxy(device)
        self._status: UNILEDStatus = UNILEDStatus()
        _LOGGER.debug("%s: Init Channel %s", self.device.name, self._number)

    def __del__(self):
        """Destroy the class"""
        _LOGGER.debug("Channel %s Destroyed", self.number)

    @property
    def name(self) -> str:
        """Returns the channel name."""
        if self.number == 0:
            return "Master" if len(self.device.channels) > 1 else ""
        return f"Channel {self.number}"

    @property
    def number(self) -> int:
        """Returns the channel name."""
        return self._number

    @property
    def device(self) -> UNILEDDevice:
        """Returns the device."""
        return self._device

    @property
    def status(self) -> UNILEDStatus:
        """Returns the status."""
        return self._status

    @property
    def is_available(self) -> bool:
        """Returns if the channel is available"""
        return self.device.available

    @property
    def sends_status_on_commands(self) -> bool:
        """Returns if device sends status report after a command"""
        assert self.device.model is not None  # nosec
        return self.device.model.sends_status_on_commands

    @property
    def needs_on(self) -> bool:
        """Returns if On state needed to change settings"""
        assert self.device.model is not None  # nosec
        return self.device.model.needs_on

    @property
    def is_on(self) -> bool | None:
        """Returns current power status"""
        return self._status.power

    @property
    def mode(self) -> str | None:
        """Name of the current effect type."""
        assert self.device.model is not None  # nosec
        return self.device.model.nameof_channel_mode(self, self._status.mode)

    @property
    def mode_list(self) -> list | None:
        """List of modes"""
        assert self.device.model is not None  # nosec
        return self.device.model.listof_channel_modes(self)

    @property
    def white(self) -> int | None:
        """Returns current white level 0-255."""
        return self._status.white

    @property
    def level(self) -> int | None:
        """Returns current (brightness) level 0-255."""
        return self._status.level

    @property
    def rgb(self) -> tuple[int, int, int] | None:
        """Returns current RGB state"""
        return self._status.rgb

    @property
    def rgb_unscaled(self) -> tuple[int, int, int] | None:
        """Return the unscaled RGB."""
        if self.rgb is None:
            return None
        red, green, blue = self.rgb
        hsv = colorsys.rgb_to_hsv(red / 255.0, green / 255.0, blue / 255.0)
        r_p, g_p, b_p = colorsys.hsv_to_rgb(hsv[0], hsv[1], 1)
        return round(r_p * 255), round(g_p * 255), round(b_p * 255)

    @property
    def rgbw(self) -> tuple[int, int, int, int] | None:
        """Return the unscaled RGB."""
        red, green, blue = (0, 0, 0)
        if self.rgb is not None:
            red, green, blue = self.rgb
        return (red, green, blue, 0xFF if self.white is None else self.white)

    @property
    def rgb2(self) -> tuple[int, int, int] | None:
        """Returns current RGB2 state"""
        return self._status.rgb2

    @property
    def effect(self) -> str | None:
        """Returns effect name."""
        if self.effect_number is None:
            return None
        assert self.device.model is not None  # nosec
        name = self.device.model.nameof_channel_effect(self, self._status.effect)
        if name is not None:
            return name
        return f"FX ({self._status.effect})"

    @property
    def effect_list(self) -> list | None:
        """List of effects"""
        assert self.device.model is not None  # nosec
        return self.device.model.listof_channel_effects(self)

    @property
    def effect_number(self) -> int | None:
        """Returns effect number."""
        return self._status.effect

    @property
    def effect_type(self) -> str | None:
        """Name of the current effect type."""
        if self._status.fxtype is None:
            return None
        assert self.device.model is not None  # nosec
        return self.device.model.nameof_channel_effect_type(self, self._status.fxtype)

    @property
    def effect_type_is_static(self) -> bool:
        """Test if effec type is sound activated"""
        if self._status.fxtype is None:
            return False
        return self._status.fxtype == UNILEDEffectType.STATIC

    @property
    def effect_type_is_pattern(self) -> bool:
        """Test if effec type is sound activated"""
        if self._status.fxtype is None:
            return False
        return self._status.fxtype == UNILEDEffectType.PATTERN

    @property
    def effect_type_is_sound(self) -> bool:
        """Test if effec type is sound activated"""
        if self._status.fxtype is None:
            return False
        return self.effect_type.startswith(UNILEDEffectType.SOUND)

    @property
    def effect_speed(self) -> int | None:
        """Current effect speed."""
        return self._status.speed

    @property
    def effect_speed_range(self) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        if self.effect_speed is None:
            return None
        assert self.device.model is not None  # nosec
        return self.device.model.rangeof_channel_effect_speed(self)

    @property
    def effect_length(self) -> int | None:
        """Current effect length."""
        return self._status.length

    @property
    def effect_length_range(self) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        if self.effect_length is None:
            return None
        assert self.device.model is not None  # nosec
        return self.device.model.rangeof_channel_effect_length(self)

    @property
    def effect_direction(self) -> bool | None:
        """Name of current effect direction."""
        return self._status.direction

    @property
    def input(self) -> str:
        """Returns the current input."""
        assert self.device.model is not None  # nosec
        return self.device.model.nameof_channel_input_type(self)

    @property
    def input_list(self) -> list[str] | None:
        """Returns a list of available inputs."""
        assert self.device.model is not None  # nosec
        return self.device.model.listof_channel_inputs(self)

    @property
    def input_gain(self) -> int | None:
        """Returns the current input gain."""
        return self._status.gain

    @property
    def input_gain_range(self) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        if self.input_gain is None:
            return None
        assert self.device.model is not None  # nosec
        return self.device.model.rangeof_channel_input_gain(self)

    @property
    def segment_count(self) -> int | None:
        """Returns the current number of segments"""
        return self._status.segment_count

    @property
    def segment_count_range(self) -> tuple(int, int, int) | None:
        """Range of channel segments (min,max,step)."""
        assert self.device.model is not None  # nosec
        return self.device.model.rangeof_channel_segment_count(self)

    @property
    def segment_length(self) -> int | None:
        """Returns the current number of segments"""
        return self._status.segment_length

    @property
    def segment_length_range(self) -> tuple(int, int, int) | None:
        """Range of segment LEDs (min,max,step)."""
        assert self.device.model is not None  # nosec
        return self.device.model.rangeof_channel_segment_length(self)

    @property
    def total_led_range(self) -> tuple(int, int, int) | None:
        """Range of total LEDs (min,max,step)."""
        assert self.device.model is not None  # nosec
        return self.device.model.rangeof_channel_led_total(self)

    @property
    def chip_order(self) -> str | None:
        """Name of current chip order"""
        assert self.device.model is not None  # nosec
        return self.device.model.nameof_channel_chip_order(self)

    @property
    def chip_order_list(self) -> list | None:
        """List of available chip orders"""
        assert self.device.model is not None  # nosec
        return self.device.model.listof_channel_chip_orders(self)

    @property
    def chip_type(self) -> str | None:
        """Name of current chip type"""
        assert self.device.model is not None  # nosec
        return self.device.model.nameof_channel_chip_type(self)

    @property
    def chip_type_list(self) -> list | None:
        """List of available chip types"""
        assert self.device.model is not None  # nosec
        return self.device.model.listof_channel_chip_types(self)

    async def async_turn_on(self) -> None:
        """Turn channel on."""
        await self.async_set_power(True)

    async def async_turn_off(self) -> None:
        """Turn channel off."""
        await self.async_set_power(False)

    async def async_set_power(self, state: bool) -> None:
        """Set channel power state."""
        _LOGGER.debug("%s: Set Power State: %s (%s)", self.name, state, self.is_on)
        if self.is_on is None or self.is_on == state:
            return
        command = self.device.model.construct_power_change(self, state)
        if await self.device.send_command(command):
            self._status = replace(self._status, power=state)
            self._fire_callbacks()

    async def async_set_mode(self, name: str) -> None:
        """Set mode by name."""
        _LOGGER.debug("%s: Set Mode: %s", self.name, name)
        if self._status.mode is None:
            return
        try:
            mode = self.device.model.codeof_channel_mode(self, name)
            if mode is not None and mode != self._status.mode:
                await self.device.send_command(
                    self.device.model.construct_mode_change(self, mode)
                )
                self._status = replace(self._status, mode=mode)
        except IndexError as exc:
            raise ValueError(f"Effect name: {name} is not valid") from exc
        self._fire_callbacks()

    async def async_set_white(self, level: int) -> None:
        """Set channel white level."""
        _LOGGER.debug("%s: Set White Level: %s", self.name, level)
        if self.white is None:
            return
        if not 0 <= level <= 255:
            raise ValueError("Value {} is outside the valid range of 0-255")
        command = self.device.model.construct_white_change(self, level)
        if await self.device.send_command(command):
            self._status = replace(self._status, level=level)
            self._fire_callbacks()

    async def async_set_level(self, level: int) -> None:
        """Set channel brightness level."""
        _LOGGER.debug("%s: Set Brightness Level: %s", self.name, level)
        if self.level is None:
            return
        if not 0 <= level <= 255:
            raise ValueError("Value {} is outside the valid range of 0-255")
        command = self.device.model.construct_level_change(self, level)
        if await self.device.send_command(command):
            self._status = replace(self._status, level=level)
            self._fire_callbacks()

    async def async_set_rgb(self, rgb: tuple[int, int, int]) -> None:
        """Set channel RGB levels."""
        _LOGGER.debug("%s: Set RGB: %s, Current: %s", self.name, rgb, self.rgb)
        if self.rgb is None:
            return
        for value in rgb:
            if not 0 <= value <= 255:
                raise ValueError("Value {} is outside the valid range of 0-255")
        command = self.device.model.construct_color_change(self, *rgb, None)
        if await self.device.send_command(command):
            self._status = replace(self._status, rgb=rgb)
            self._fire_callbacks()

    async def async_set_rgbw(self, rgbw: tuple[int, int, int, int]) -> None:
        """Set channel RGBW levels."""
        _LOGGER.debug("%s: Set RGBW: %s, Current: %s", self.name, rgbw, self.rgbw)
        if self.rgbw is None:
            return
        for value in rgbw:
            if not 0 <= value <= 255:
                raise ValueError("Value {} is outside the valid range of 0-255")

        red, green, blue, white = rgbw
        command = self.device.model.construct_color_change(
            self, red, green, blue, white
        )

        if await self.device.send_command(command):
            self._status = replace(self._status, rgb=(red, green, blue), white=white)
            self._fire_callbacks()

    async def async_set_rgb2(self, rgb: tuple[int, int, int]) -> None:
        """Set channel second RGB levels."""
        _LOGGER.debug("%s: Set RGB2: %s, Current: %s", self.name, rgb, self.rgb2)
        if self.rgb2 is None:
            return
        for value in rgb:
            if not 0 <= value <= 255:
                raise ValueError("Value {} is outside the valid range of 0-255")
        command = self.device.model.construct_color_two_change(self, *rgb, None)
        if await self.device.send_command(command):
            self._status = replace(self._status, rgb2=rgb)
            self._fire_callbacks()

    async def async_set_effect(self, name: str) -> None:
        """Set effect by name."""
        _LOGGER.debug("%s: Set Effect: %s", self.name, name)
        if self._status.effect is not None:
            try:
                code = self.device.model.codeof_channel_effect(self, name)
                if code is not None:
                    await self._async_set_effect_bycode(code)
            except IndexError as exc:
                raise ValueError(f"Effect name: {name} is not valid") from exc

    async def _async_set_effect_bycode(self, code: int) -> None:
        """Set effect by id code."""
        if self.device.model.nameof_channel_effect(self, code) is not None:
            if code != self.effect:
                await self.device.send_command(
                    self.device.model.construct_effect_change(self, code)
                )
                self._status = replace(
                    self._status,
                    effect=code,
                    fxtype=self.device.model.codeof_channel_effect_type(self, code),
                )
                self._fire_callbacks()
            return
        raise ValueError(f"Effect code: {code} is not valid")

    async def async_set_effect_speed(self, value: int) -> None:
        """Set effect speed."""
        _LOGGER.debug("%s: Set Effect Speed: %s", self.name, value)
        if self._status.speed is not None:
            if (rangeof := self.effect_speed_range) is None:
                return
            if not rangeof[0] <= value <= rangeof[1]:
                raise ValueError(
                    "Value {} is outside the valid range of {rangeof[0]}-{rangeof[1]}"
                )

            if not await self.device.send_command(
                self.device.model.construct_effect_speed_change(self, value)
            ):
                value = self._status.speed
            self._status = replace(self._status, speed=value)
            self._fire_callbacks()

    async def async_set_effect_length(self, value: int) -> None:
        """Set effect length."""
        _LOGGER.debug("%s: Set Effect Length: %s", self.name, value)
        if self._status.length is not None:
            if (rangeof := self.effect_length_range) is None:
                return
            if not rangeof[0] <= value <= rangeof[1]:
                raise ValueError(
                    "Value {} is outside the valid range of {rangeof[0]}-{rangeof[1]}"
                )

            if not await self.device.send_command(
                self.device.model.construct_effect_length_change(self, value)
            ):
                value = self._status.length
            self._status = replace(self._status, length=value)
            self._fire_callbacks()

    async def async_set_effect_direction(self, value: bool) -> None:
        """Set effect direction."""
        _LOGGER.debug("%s: Set Effect Direction: %s", self.name, value)
        if self._status.direction is not None:
            if not await self.device.send_command(
                self.device.model.construct_effect_direction_change(self, value)
            ):
                value = self._status.direction
            self._status = replace(self._status, direction=value)
            self._fire_callbacks()

    async def async_set_input(self, name: str) -> None:
        """Set audio input."""
        _LOGGER.debug("%s: Set Audio Input: %s", self.name, name)
        if self._status.input is not None:
            try:
                code = self.device.model.codeof_channel_input_type(self, name)
                if code is not None and code != self._status.input:
                    if not await self.device.send_command(
                        self.device.model.construct_input_change(self, code)
                    ):
                        code = self._status.input
                    self._status = replace(self._status, input=code)
                self._fire_callbacks()
            except IndexError as exc:
                raise ValueError(f"Input type: {name} is not valid") from exc

    async def async_set_input_gain(self, value: int) -> None:
        """Set input gain."""
        _LOGGER.debug("%s: Set Input Gain: %s", self.name, value)
        if (rangeof := self.input_gain_range) is None:
            return
        if not rangeof[0] <= value <= rangeof[1]:
            raise ValueError(
                "Value {} is outside the valid range of {rangeof[0]}-{rangeof[1]}"
            )

        if not await self.device.send_command(
            self.device.model.construct_input_gain_change(self, value)
        ):
            value = self._status.length
        self._status = replace(self._status, gain=value)
        self._fire_callbacks()

    async def async_set_chip_type(self, name: str) -> None:
        """Set chip type."""
        _LOGGER.debug("%s: Set Chip Type: %s", self.name, name)
        if self._status.chip_type is not None:
            try:
                code = self.device.model.codeof_channel_chip_type(self, name)
                if code is not None and code != self._status.chip_type:
                    if not await self.device.send_command(
                        self.device.model.construct_chip_type_change(self, code)
                    ):
                        code = self._status.chip_type
                    self._status = replace(self._status, chip_type=code)
                self._fire_callbacks()
            except IndexError as exc:
                raise ValueError(f"Chip type: {name} is not valid") from exc

    async def async_set_chip_order(self, name: str) -> None:
        """Set chip order."""
        _LOGGER.debug("%s: Set Chip Order: %s", self.name, name)
        if self._status.chip_order is not None:
            try:
                code = self.device.model.codeof_channel_chip_order(self, name)
                if code is not None and code != self._status.chip_order:
                    if not await self.device.send_command(
                        self.device.model.construct_chip_order_change(self, code)
                    ):
                        code = self._status.chip_order
                    self._status = replace(self._status, chip_order=code)
                self._fire_callbacks()
            except IndexError as exc:
                raise ValueError(f"Chip order: {name} is not valid") from exc

    async def async_set_segment_count(self, value: int) -> None:
        """Set segment count."""
        _LOGGER.debug("%s: Set Segment Count: %s", self.name, value)
        if self._status.segment_count is not None:
            if (rangeof := self.segment_count_range) is None:
                return
            if not rangeof[0] <= value <= rangeof[1]:
                raise ValueError(
                    "Value {} is outside the valid range of {rangeof[0]}-{rangeof[1]}"
                )

            if not await self.device.send_command(
                self.device.model.construct_segment_count_change(self, value)
            ):
                value = self._status.segment_count
            self._status = replace(self._status, segment_count=value)
        self._fire_callbacks()

    async def async_set_segment_length(self, value: int) -> None:
        """Set segment length."""
        _LOGGER.debug("%s: Set Segment Length: %s", self.name, value)
        if self._status.segment_length is not None:
            if (rangeof := self.segment_length_range) is None:
                return
            if not rangeof[0] <= value <= rangeof[1]:
                raise ValueError(
                    "Value {} is outside the valid range of {rangeof[0]}-{rangeof[1]}"
                )

            if not await self.device.send_command(
                self.device.model.construct_segment_length_change(self, value)
            ):
                value = self._status.segment_length
            self._status = replace(self._status, segment_length=value)
        self._fire_callbacks()

    def set_status(self, status: UNILEDStatus, force_update: bool = True) -> None:
        """Set status of channel"""
        _LOGGER.debug("%s: Set Status: %s", self.name, status)
        self._status = status
        if force_update:
            self._fire_callbacks()

    def register_callback(
        self, callback: Callable[[UNILEDChannel], None]
    ) -> Callable[[], None]:
        """Register a callback to be called when the state changes."""

        def unregister_callback() -> None:
            self._callbacks.remove(callback)

        self._callbacks.append(callback)
        return unregister_callback

    def _fire_callbacks(self) -> None:
        """Fire the callbacks."""
        for callback in self._callbacks:
            callback(self)


class UNILEDMaster(UNILEDChannel):
    """UniLED Master Channel Class"""


class UNILEDDevice:
    """UniLED Base Device Class"""

    def __init__(self) -> None:
        """Init the UniLED Base Driver"""
        self._channels: list[UNILEDChannel] = [UNILEDMaster(self, 0)]
        self._model: weakref.ProxyType(UNILEDModel) | None = None
        self._last_notification_data: bytearray = ()

    def _create_channels(self) -> None:
        """Create device channels."""
        assert self._model is not None  # nosec
        count = self._model.channels or 1
        if len(self._channels) < count:
            for index in range(count):
                self._channels.append(UNILEDChannel(self, index + 1))

    def register_callback(
        self, callback: Callable[[UNILEDChannel], None]
    ) -> Callable[[], None]:
        """Register a callback to be called when the state changes."""
        return self.master.register_callback(callback)

    @property
    def model(self) -> UNILEDModel:
        """Return the device model."""
        return self._model

    @property
    def model_name(self) -> int:
        """Return the device model name."""
        assert self._model is not None  # nosec
        return self._model.model_name

    @property
    def model_type(self) -> UNILEDModelType:
        """Return the device model type"""
        assert self._model is not None  # nosec
        return self._model.model_type

    @property
    def model_number(self) -> int:
        """Return the device model number."""
        assert self._model is not None  # nosec
        return self._model.model_num

    @property
    def manufacturer(self) -> str:
        """Return the device manufacturer."""
        assert self._model is not None  # nosec
        return self._model.manufacturer

    @property
    def description(self) -> str:
        """Return the device description."""
        assert self._model is not None  # nosec
        return self._model.description

    @property
    def outputs(self) -> int:
        """Return the device description."""
        assert self._model is not None  # nosec
        return self._model.channels or 1

    @property
    def master(self) -> UNILEDMaster | None:
        """Return the master channel"""
        return self._channels[0]

    @property
    def channels(self) -> list[UNILEDChannel]:
        """Return the device channels"""
        return self._channels

    @property
    def last_notification_data(self) -> bytearray:
        """Last notification data"""
        return self._last_notification_data

    def save_notification_data(self, save: bytearray) -> bytearray:
        """Save some notification data"""
        self._last_notification_data = save
        return save

    @property
    @abstractmethod
    def transport(self) -> str:
        """Return the device transport."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the device."""

    @property
    @abstractmethod
    def address(self) -> str:
        """Return the address of the device."""

    @property
    @abstractmethod
    def available(self) -> bool:
        """Return if the UniLED device available."""

    @abstractmethod
    async def send_command(
        self, commands: list[bytes] | bytes, retry: int | None = None
    ) -> None:
        """Send command to a UniLED device."""
        return None

    @abstractmethod
    async def update(self) -> None:
        """Update the UniLED device."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the UniLED device"""
