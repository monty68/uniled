"""UniLed Base Classes"""
from __future__ import annotations

from dataclasses import dataclass, replace
from collections.abc import Callable
from abc import abstractmethod
from typing import Any

from .artifacts import UNILEDModelType
from .states import UNILEDStatus

import colorsys
import logging

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class UNILEDModel:
    """UniLED Base Model Class"""

    model_num: int  # The model number
    model_name: str  # The model name
    model_type: UNILEDModelType # Type of device model
    description: str  # Description of the model ({type} {color_mode})
    manufacturer: str  # The manufacturers name
    manufacturer_id: int
    channels: int
    extra_data: dict(str, Any)

    ##
    ## Protocol Wrapper
    ##
    @abstractmethod
    def construct_message(self, raw_bytes: bytearray) -> bytearray:
        """Base protocol uses no checksum."""
        return raw_bytes

    ##
    ## Device Control
    ##
    @abstractmethod
    def construct_on_connect(self) -> list[bytearray]:
        """The bytes to send when first connecting."""

    @abstractmethod
    def construct_status_query(self, device: UNILEDDevice) -> list[bytearray]:
        """The bytes to send for a status query."""
        return None

    @abstractmethod
    def construct_gain_change(
        self, device: UNILEDDevice, gain: int
    ) -> list[bytearray] | None:
        """The bytes to send for a gain/sensitivity change"""
        return None

    @abstractmethod
    def construct_input_change(
        self, device: UNILEDDevice, audio_input: int
    ) -> bytearray | None:
        """The bytes to send for an input change."""
        return None

    @abstractmethod
    async def async_decode_notifications(
        self, device: UNILEDDevice, sender: int, data: bytearray
    ) -> UNILEDStatus | None:
        """Handle notification responses."""
        return device.master.status

    ##
    ## Channel Control
    ##
    @abstractmethod
    def construct_power_change(
        self, channel: UNILEDChannel, turn_on: int
    ) -> list[bytearray]:
        """The bytes to send for a power state change."""

    @abstractmethod
    def construct_white_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a white level change."""
        return None

    @abstractmethod
    def construct_level_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a color level change."""
        return None

    @abstractmethod
    def construct_color_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a color change."""
        return None

    @abstractmethod
    def construct_effect_change(
        self, channel: UNILEDChannel, effect: int
    ) -> list[bytearray] | None:
        """The bytes to send for an effect change."""
        return None

    @abstractmethod
    def construct_effect_speed_change(
        self, channel: UNILEDChannel, speed: int
    ) -> list[bytearray] | None:
        """The bytes to send for an effect speed change."""
        return None

    @abstractmethod
    def construct_effect_length_change(
        self, channel: UNILEDChannel, length: int
    ) -> list[bytearray] | None:
        """The bytes to send for an efect length change."""
        return None

    ##
    ## Device Informational
    ##
    @abstractmethod
    def nameof_device_input_type(
        self, device: UNILEDDevice, audio_input: int | None = None
    ) -> str | None:
        """Name a device input type."""
        return None

    @abstractmethod
    def listof_device_inputs(self, device: UNILEDDevice) -> list | None:
        """List of available device inputs."""
        return None

    ##
    ## Channel Informational
    ##
    @abstractmethod
    def rangeof_channel_input_gain(
        self, device: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return None

    @abstractmethod
    def listof_channel_effects(self, channel: UNILEDChannel) -> list | None:
        """List of available channel effects"""
        return None

    @abstractmethod
    def codeof_channel_effects(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named channel effect"""
        return None

    @abstractmethod
    def nameof_channel_effect(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> str | None:
        """Name an effect."""
        return None

    @abstractmethod
    def nameof_channel_effect_type(
        self, channel: UNILEDChannel, fxtype: int | None = None
    ) -> str | None:
        """Name an effects type."""
        return None

    @abstractmethod
    def rangeof_channel_effect_speed(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        return None

    @abstractmethod
    def rangeof_channel_effect_length(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect length (min,max,step)."""
        return None


class UNILEDChannel:
    """UniLED Channel Class"""

    def __init__(self, device: UNILEDDevice, number: int) -> None:
        self._callbacks: list[Callable[[UNILEDChannel], None]] = []
        self._number: int = number
        self._device: UNILEDDevice = device
        self._status: UNILEDStatus = UNILEDStatus()

        _LOGGER.debug("%s: Init %s", self.device.name, self.name)

    @property
    def name(self) -> str:
        """Returns the channel name."""
        if self.number == 0:
            return "Master" # if len(self.device.model.channels) > 1 else ""
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
    def effect(self) -> int:
        """Returns effect number"""
        return self._status.effect

    @property
    def nameof_effect(self) -> str:
        """Returns effect name"""
        assert self.device.model is not None  # nosec
        name =  self.device.model.nameof_channel_effect(self, self._status.effect)
        if name is not None:
            return name
        return f"FX ({self._status.effect})"

    @property
    def effect_type(self) -> int:
        """Returns effect number"""
        return self._status.fxtype

    @property
    def nameof_effect_type(self) -> str | None:
        """Range of effect speed (min,max,step)."""
        assert self.device.model is not None  # nosec
        return self.device.model.nameof_channel_effect_type(self, self._status.fxtype)

    @property
    def listof_effects(self) -> list | None:
        """List of effects"""
        assert self.device.model is not None  # nosec
        return self.device.model.listof_channel_effects(self)

    @property
    def effect_speed(self) -> int:
        """Current effect speed."""
        return self._status.speed

    @property
    def rangeof_effect_speed(self) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        assert self.device.model is not None  # nosec
        return self.device.model.rangeof_channel_effect_speed(self)

    @property
    def effect_length(self) -> int:
        """Current effect length."""
        return self._status.length

    @property
    def rangeof_effect_length(self) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        assert self.device.model is not None  # nosec
        return self.device.model.rangeof_channel_effect_length(self)

    @property
    def input_gain(self) -> int:
        """Returns the current input gain."""
        return self._status.gain

    @property
    def rangeof_input_gain(self) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        assert self.device.model is not None  # nosec
        return self.device.model.rangeof_channel_input_gain(self)

    @property
    def needs_on(self) -> bool:
        """Returns if On state needed to change settings"""
        return True  # TODO: Get from model data!

    @property
    def is_on(self) -> bool | None:
        """Returns current power status"""
        return self._status.power

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

            # If the master, update all the other channels
            if self.number == 0:
                for channel in self.device.channels:
                    if channel.number == self.number:
                        continue
                    await channel.set_status(replace(channel.status, power=state))
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

    async def async_set_rgb(
        self, rgb: tuple[int, int, int], level: int | None = None
    ) -> None:
        """Set channel RGB levels."""
        _LOGGER.debug("%s: Set RGB: %s Level: %s", self.name, rgb, level)
        if self.rgb is None:
            return
        if level is None:
            level = self.level
        elif not 0 <= level <= 255:
            raise ValueError("Value {} is outside the valid range of 0-255")
        for value in rgb:
            if not 0 <= value <= 255:
                raise ValueError("Value {} is outside the valid range of 0-255")
        command = self.device.model.construct_color_change(self, *rgb, level)
        if await self.device.send_command(command):
            self._status = replace(self._status, rgb=rgb, level=level)
            self._fire_callbacks()

    async def async_set_rgbw(self, rgbw: tuple[int, int, int, int]) -> None:
        """Set channel RGBW levels."""
        if self.rgbw is None:
            return
        for value in rgbw:
            if not 0 <= value <= 255:
                raise ValueError("Value {} is outside the valid range of 0-255")
        # TODO: Needs coding!

    async def async_set_effect_byname(self, name: str) -> None:
        """Set effect by name."""
        _LOGGER.debug("%s: Set Effect: %s", self.name, name)
        try:
            code = self.device.model.codeof_channel_effect(self, name)
            if code is not None:
                await self.async_set_effect_bycode(code)
        except IndexError as exc:
            raise ValueError(f"Effect name: {name} is not valid") from exc
        return

    async def async_set_effect_bycode(self, code: int) -> None:
        """Set effect by id code."""
        if self.device.model.nameof_channel_effect(self, code) is not None:
            if code != self.effect:
                await self.device.send_command(
                    self.device.model.construct_effect_change(self, code)
                )
                self._status = replace(self._status, effect=code)
                self._fire_callbacks()
            return
        raise ValueError(f"Effect code: {code} is not valid")

    async def set_status(self, status: UNILEDStatus) -> None:
        """Set status of channel"""
        _LOGGER.debug("%s: Set Status: %s", self.name, status)
        self._status = status
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

    @property
    def input(self) -> str:
        """Returns the current input."""

    @property
    def input_list(self) -> list[str] | None:
        """Returns a list of available inputs."""


class UNILEDDevice:
    """UniLED Base Device Class"""

    def __init__(self) -> None:
        """Init the UniLED Base Driver"""
        self._channels: list[UNILEDChannel] = [UNILEDMaster(self, 0)]
        self._model: UNILEDModel | None = None
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
    def model(self) -> int:
        """Return the device model num."""
        assert self._model is not None  # nosec
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
        """Return the device model num."""
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
    def master(self) -> UNILEDChannel | None:
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
    def id(self) -> str:
        """Return the ID of the device."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the device."""

    @property
    @abstractmethod
    def address(self) -> str:
        """Return the address of the device."""

    @abstractmethod
    async def send_command(
        self, commands: list[bytes] | bytes, retry: int | None = None
    ) -> None:
        """Send command to a UniLED device."""
        return None

    @abstractmethod
    async def update(self, force: bool = False) -> None:
        """Update the UniLED device."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the UniLED device"""
