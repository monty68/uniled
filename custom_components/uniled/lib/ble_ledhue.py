"""UniLED BLE Devices - SP110E from SPLED (LedHue)"""
from __future__ import annotations

import functools
import operator

from dataclasses import dataclass, replace
from typing import Final
from enum import IntEnum

from .artifacts import (
    UNKNOWN,
    UNILED_CHIP_4COLOR,
    UNILEDModelType,
    UNILEDEffectType,
    UNILEDEffects,
)
from .states import UNILEDStatus
from .classes import UNILEDDevice, UNILEDChannel
from .ble_model import UNILEDBLEModel, BASE_UUID_FORMAT as LEDHUE_UUID_FORMAT

import logging

_LOGGER = logging.getLogger(__name__)

LEDHUE_MANUFACTURER_ID: Final = 0
LEDHUE_MANUFACTURER: Final = "SPLED (LedHue)"
LEDHUE_MODEL_NUMBER_SP110E: Final = 0x110E
LEDHUE_MODEL_NAME_SP110E: Final = "SP110E"
LEDHUE_LOCAL_NAME_SP110E: Final = LEDHUE_MODEL_NAME_SP110E


@dataclass(frozen=True)
class _Msg(IntEnum):
    CMD_LED_ON = 0xAA
    CMD_LED_OFF = 0xAB
    CMD_CHECK_DEVICE = 0xD5
    CMD_GET_INFO = 0x10
    CMD_RENAME = 0xBB
    CMD_SET_RGB = 0x3C
    CMD_SET_IC = 0x1C
    CMD_SET_LED_PIXELS_COUNT = 0x2D
    CMD_SET_STATIC = 0x06
    CMD_SET_MODE = 0x2C  # 0x06??
    CMD_SET_SPEED = 0x03
    CMD_SET_BRIGHTNESS = 0x2A
    CMD_SET_WHITE_BRIGHTNESS = 0x69
    CMD_SET_STATIC_COLOR = 0x1E
    CMD_SET_AUTO_MODE = 0xFF


@dataclass(frozen=True)
class _FXType(IntEnum):
    STATIC = 0x00
    PATTERN = 0x01


@dataclass(frozen=True)
class _FXGroup(IntEnum):
    PATTERN = 1
    SOLID = 0x79


LEDHUE_EFFECT_TYPES: dict(int, str) = {
    _FXType.STATIC.value: UNILEDEffectType.STATIC,
    _FXType.PATTERN.value: UNILEDEffectType.PATTERN,
}

LEDHUE_EFFECT_GROUPS: Final = [
    {_FXGroup.SOLID.value: UNILEDEffects.SOLID.value},
    {
        (_FXGroup.PATTERN + k): f"{UNILEDEffectType.PATTERN} {k+1}"
        for k in range(_FXGroup.SOLID.value - 1)
    },
]

LEDHUE_EFFECTS: Final = dict(functools.reduce(operator.or_, LEDHUE_EFFECT_GROUPS))


@dataclass(frozen=True)
class _LEDHUE(UNILEDBLEModel):
    """LedHue Protocol Implementation"""

    ##
    ## Device State
    ##
    def construct_status_query(self, device: UNILEDDevice) -> bytearray:
        """The bytes to send for a state query."""
        return self.construct_message(bytearray([0x00, 0x00, 0x00, _Msg.CMD_GET_INFO]))

    def async_decode_notifications(
        self, device: UNILEDDevice, sender: int, data: bytearray
    ) -> UNILEDStatus | None:
        """Handle notification responses."""

        if sender == 12 and len(data) == 12:
            # 00 79 e8 db 03 02 00 15 00 ff ff 66
            # 00 01 79 ba 2b 03 02 00 15 ff ff 00 66
            # ff 01 2b bf ff 03 02 02 58 00 00 00 d6

            effect = data[1]
            chip = data[4]
            white = data[11]
            if chip not in UNILED_CHIP_4COLOR:
                white = None

            return UNILEDStatus(
                power=data[0] == 1,
                effect=effect,
                fxtype=_FXType.PATTERN.value
                if effect < _FXGroup.SOLID
                else _FXType.STATIC.value,
                speed=data[2],
                white=white,
                level=data[3],
                rgb=(data[8], data[9], data[10]),
                chip_order=data[5],
                chip_type=chip,
                segment_count=1,
                segment_length=int.from_bytes(data[6:8], byteorder="big"),
            )

        return None

    ##
    ## Channel Control
    ##
    def construct_power_change(
        self, channel: UNILEDChannel, turn_on: int
    ) -> list[bytearray] | None:
        """The bytes to send for a power state change"""
        return self.construct_message(
            bytearray(
                [0x00, 0x00, 0x00, _Msg.CMD_LED_ON if turn_on else _Msg.CMD_LED_OFF]
            )
        )

    def construct_level_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a color level change."""
        return self.construct_message(
            bytearray([level, 0x00, 0x00, _Msg.CMD_SET_BRIGHTNESS])
        )

    def construct_white_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a white level change."""
        return self.construct_message(
            bytearray([level, 0x00, 0x00, _Msg.CMD_SET_WHITE_BRIGHTNESS])
        )

    def construct_color_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int, white: int | None
    ) -> list[bytearray] | None:
        """The bytes to send for a color change."""
        effect = channel.status.effect
        msg = _Msg.CMD_SET_STATIC_COLOR
        commands = []

        if effect != _FXGroup.SOLID:
            channel.set_status(
                replace(
                    channel.status,
                    effect=_FXGroup.SOLID.value,
                )
            )

        if channel.status.rgb != (red, green, blue):
            commands.append(self.construct_message(bytearray([red, green, blue, msg])))

        if (
            white is not None and channel.status.white is not None
        ) and channel.status.white != white:
            commands.append(
                self.construct_message(
                    bytearray([white, 0x00, 0x00, _Msg.CMD_SET_WHITE_BRIGHTNESS])
                )
            )
        return commands

    def construct_effect_change(
        self, channel: UNILEDChannel, effect: int
    ) -> list[bytearray] | None:
        """The bytes to send for an effect change."""
        return self.construct_message(
            bytearray([effect, 0x00, 0x00, _Msg.CMD_SET_MODE])
        )

    def construct_effect_speed_change(
        self, channel: UNILEDChannel, speed: int
    ) -> list[bytearray] | None:
        """The bytes to send for an effect speed change."""
        return self.construct_message(
            bytearray([speed, 0x00, 0x00, _Msg.CMD_SET_SPEED])
        )

    ##
    ## Channel Configuration
    ##
    def construct_chip_type_change(
        self, channel: UNILEDChannel, chip_type: int
    ) -> list[bytearray] | None:
        """The bytes to send for a chip type change"""
        return self.construct_message(
            bytearray([chip_type, 0x00, 0x00, _Msg.CMD_SET_IC])
        )

    def construct_chip_order_change(
        self, channel: UNILEDChannel, chip_order: int
    ) -> list[bytearray] | None:
        """The bytes to send for a chip order change"""
        return self.construct_message(
            bytearray([chip_order, 0x00, 0x00, _Msg.CMD_SET_RGB])
        )

    def construct_segment_length_change(
        self, channel: UNILEDChannel, length: int
    ) -> list[bytearray] | None:
        """The bytes to send for a segment length change"""
        pixels = length.to_bytes(2, byteorder="big")
        return self.construct_message(
            bytearray(
                [
                    pixels[0],
                    pixels[1],
                    0x00,
                    _Msg.CMD_SET_LED_PIXELS_COUNT,
                ]
            )
        )

    ##
    ## Channel Informational
    ##
    def listof_channel_effects(self, channel: UNILEDChannel) -> list | None:
        """List of available channel effects"""
        return list(LEDHUE_EFFECTS.values())

    def codeof_channel_effect(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named channel effect"""
        if name is None:
            return channel.status.effect
        return [k for k in LEDHUE_EFFECTS.items() if k[1] == name][0][0]

    def nameof_channel_effect(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> str | None:
        """Name an effect."""
        if effect is None:
            effect = channel.status.effect
        if effect in LEDHUE_EFFECTS:
            return LEDHUE_EFFECTS[effect]
        return None

    def codeof_channel_effect_type(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> int | None:
        """Code of channel effect type from effect code"""
        if effect is None:
            effect = channel.status.effect
        if effect == _FXGroup.SOLID:
            return _FXType.STATIC.value
        return _FXType.PATTERN.value

    def nameof_channel_effect_type(
        self, channel: UNILEDChannel, fxtype: int | None = None
    ) -> str | None:
        """Name an effects type."""
        if fxtype is None:
            fxtype = channel.status.fxtype
        if fxtype in LEDHUE_EFFECT_TYPES:
            return LEDHUE_EFFECT_TYPES[fxtype]
        return f"{UNKNOWN} ({fxtype})"

    def rangeof_channel_effect_speed(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        return (1, 255, 1)

    def rangeof_channel_segment_length(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return (1, 1024, 1)

    def rangeof_channel_led_total(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return (1, 1024, 0)


##
## SP110E
##
SP110E = _LEDHUE(
    model_num=LEDHUE_MODEL_NUMBER_SP110E,
    model_name=LEDHUE_MODEL_NAME_SP110E,
    model_type=UNILEDModelType.STRIP,
    description="BLE RGB(W) Controller",
    manufacturer=LEDHUE_MANUFACTURER,
    manufacturer_id=LEDHUE_MANUFACTURER_ID,
    manufacturer_data=b"\x00\x00",
    resolve_protocol=True,
    channels=1,
    needs_on=True,
    sends_status_on_commands=False,
    local_names=[LEDHUE_LOCAL_NAME_SP110E],
    service_uuids=[LEDHUE_UUID_FORMAT.format(part) for part in ["ffe0"]],
    write_uuids=[LEDHUE_UUID_FORMAT.format(part) for part in ["ffe1"]],
    read_uuids=[],
)
