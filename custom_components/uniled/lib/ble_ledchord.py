"""UniLED BLE Devices - SP107E from SPLED (LEDChord)"""
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
    UNILEDMode,
    UNILEDEffectType,
    UNILEDEffects,
)
from .states import UNILEDStatus
from .classes import UNILEDDevice, UNILEDChannel
from .ble_model import UNILEDBLEModel, BASE_UUID_FORMAT as LEDCHORD_UUID_FORMAT

import logging

_LOGGER = logging.getLogger(__name__)

LEDCHORD_MANUFACTURER_ID: Final = 0
LEDCHORD_MANUFACTURER: Final = "SPLED (LEDChord)"
LEDCHORD_MODEL_NUMBER_SP107E: Final = 0x107E
LEDCHORD_MODEL_NAME_SP107E: Final = "SP107E"
LEDCHORD_LOCAL_NAME_SP107E: Final = LEDCHORD_MODEL_NAME_SP107E


@dataclass(frozen=True)
class _Msg(IntEnum):
    CMD_LED_ON = 0xAA
    CMD_LED_OFF = 0xBB
    CMD_CHECK_DEVICE = 1
    CMD_GET_INFO = 2
    CMD_RENAME = 3
    CMD_SET_RGB = 4
    CMD_SET_IC = 5
    CMD_SET_LED_PIXELS_COUNT = 6
    CMD_SET_MODE = 8
    CMD_SET_NO_MUSIC_SPEED = 9
    CMD_SET_NO_MUSIC_BRIGHTNESS = 10
    CMD_SET_NO_MUSIC_WHITE_BRIGHTNESS = 11
    CMD_SET_NO_MUSIC_STATIC_COLOR = 12
    CMD_SET_NO_MUSIC_AUTO_MODE = 13
    CMD_SET_STRIP_MUSIC_COLOR = 14
    CMD_SET_STRIP_MUSIC_AUTO_MODE = 15
    CMD_SET_SCREEN_MUSIC_COL_COLOR = 16
    CMD_SET_SCREEN_MUSIC_DOT_COLOR = 17
    CMD_SET_SCREEN_MUSIC_AUTO_MODE = 18
    CMD_SET_MUSIC_GAIN = 19


@dataclass(frozen=True)
class _FXMode(IntEnum):
    SINGULAR = 0x00
    AUTO_PATTERN = 0x01
    AUTO_STRIP = 0x02
    AUTO_MATRIX = 0x03


@dataclass(frozen=True)
class _FXType(IntEnum):
    STATIC = 0x00
    PATTERN = 0x01
    SOUND_STRIP = 0x02
    SOUND_MATRIX = 0x03


@dataclass(frozen=True)
class _FXGroup(IntEnum):
    PATTERN = 1
    SOLID = 0xB5
    SOUND_STRIP = 0xBE
    SOUND_MATRIX = 0xDC


LEDCHORD_MODES: Final = {
    _FXMode.SINGULAR.value: UNILEDMode.SINGULAR,
    _FXMode.AUTO_PATTERN.value: UNILEDMode.AUTO_PATTERN,
    _FXMode.AUTO_STRIP.value: "Cycle Strip FX's",
    _FXMode.AUTO_MATRIX.value: "Cycle Matrix FX's",
}

LEDCHORD_EFFECT_TYPES: dict(int, str) = {
    _FXType.STATIC.value: UNILEDEffectType.STATIC,
    _FXType.PATTERN.value: UNILEDEffectType.PATTERN,
    _FXType.SOUND_STRIP.value: "Sound - Strip FX",
    _FXType.SOUND_MATRIX.value: "Sound - Matrix FX",
}

LEDCHORD_EFFECT_GROUPS: Final = [
    {_FXGroup.SOLID.value: UNILEDEffects.SOLID},
    {(_FXGroup.PATTERN + k): f"Pattern FX {k+1}" for k in range(180)},
    {(_FXGroup.SOUND_STRIP + k): f"Sound - Strip FX {k+1}" for k in range(18)},
    {(_FXGroup.SOUND_MATRIX + k): f"Sound - Matrix FX {k+1}" for k in range(30)},
]

LEDCHORD_EFFECTS: Final = dict(functools.reduce(operator.or_, LEDCHORD_EFFECT_GROUPS))


@dataclass(frozen=True)
class _LEDCHORD(UNILEDBLEModel):
    """LED Chord Protocol Implementation"""

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

        if data[0] == 0 and data[1] == 1:
            # Save first status packet, minus the first 2 header bytes
            device.save_notification_data(data[2:])
        elif data[0] == 0 and data[1] == 2:  #
            # Combine this data (minus first 2 bytes) with the previous
            # notification data (also minus its first 2 bytes).
            #
            data = device.save_notification_data(
                device.last_notification_data + data[2:]
            )
            # This leaves a 26 byte array with the following layout:
            #
            # 01 02 18 06 3c 03 01 01 01 60 c9 00 01
            # -----------------------------------------------------------------------------
            # 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25
            # -----------------------------------------------------------------------------
            # PW OR IC SG QY FX AE AS AM SP BL WW ?? SR SG SB MR MG MB CR CG CB DR DG DB IG
            # -----------------------------------------------------------------------------
            #
            # 0  = Power State
            # 1  = RGB Ordering
            # 2  = Chipset
            # 3  = Segments
            # 4  = LEDs
            # 5  = Effect
            # 6  = Auto Effects
            # 7  = Strip Music Auto
            # 8  = Screen/Matrix Music Auto
            # 9  = Speed
            # 10 = Brightness Level
            # 11 = White Level
            # 12 = ?? Unknown
            # 13 = Static Red
            # 14 = Static Green
            # 15 = Static Blue
            # 16 = Strip Music Red
            # 17 = Strip Music Green
            # 18 = Strip Music Blue
            # 19 = Screen/Matrix Column Red
            # 20 = Screen/Matrix Column Green
            # 21 = Screen/Matrix Column Blue
            # 22 = Screen/Matrix Dot Red
            # 23 = Screen/Matrix Dot Green
            # 24 = Screen/Matrix Dot Blue
            # 25 = Input Gain
            #
            chip = data[2]
            white = data[11]
            if chip not in UNILED_CHIP_4COLOR:
                white = None

            rgb = (data[13], data[14], data[15])
            rgb2 = None
            fxtype = _FXType.STATIC.value
            mode = _FXMode.SINGULAR.value
            effect = data[5]
            power = data[0]

            if effect < _FXGroup.SOLID:
                fxtype = _FXType.PATTERN.value
                mode = _FXMode.AUTO_PATTERN.value if data[6] else mode
            elif effect >= _FXGroup.SOUND_STRIP and effect < _FXGroup.SOUND_MATRIX:
                fxtype = _FXType.SOUND_STRIP.value
                mode = _FXMode.AUTO_STRIP.value if data[7] else mode
                rgb = (data[16], data[17], data[18])
            elif effect >= _FXGroup.SOUND_MATRIX:
                mode = _FXMode.AUTO_MATRIX.value if data[8] else mode
                fxtype = _FXType.SOUND_MATRIX.value
                rgb = (data[22], data[23], data[24])
                rgb2 = (data[19], data[20], data[21])

            return UNILEDStatus(
                power=power,
                mode=mode,
                fxtype=fxtype,
                effect=effect,
                speed=data[9],
                white=white,
                level=data[10],
                rgb=rgb,
                gain=data[25],
                rgb2=rgb2,  # Matrix Column Color - TODO, how to set in the HA UI?
                chip_order=data[1],
                chip_type=chip,
                segment_count=data[3],
                segment_length=data[4],
                extra={"unknown": data[12]},
            )

        # Getting here means a notification has not changed the state
        #
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

    def construct_mode_change(
        self, channel: UNILEDChannel, mode: int
    ) -> list[bytearray] | None:
        """The bytes to send for a mode change."""
        if mode == _FXMode.SINGULAR:
            return self.construct_effect_change(channel, channel.status.effect)

        if mode == _FXMode.AUTO_STRIP:
            msg = _Msg.CMD_SET_STRIP_MUSIC_AUTO_MODE
        elif mode == _FXMode.AUTO_MATRIX:
            msg = _Msg.CMD_SET_SCREEN_MUSIC_AUTO_MODE
        else:
            msg = _Msg.CMD_SET_NO_MUSIC_AUTO_MODE

        return [
            self.construct_message(bytearray([True, 0x00, 0x00, msg])),
            # self.construct_status_query(channel.device),
        ]

    def construct_level_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a color level change."""
        return self.construct_message(
            bytearray([level, 0x00, 0x00, _Msg.CMD_SET_NO_MUSIC_BRIGHTNESS])
        )

    def construct_white_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a white level change."""
        return self.construct_message(
            bytearray([level, 0x00, 0x00, _Msg.CMD_SET_NO_MUSIC_WHITE_BRIGHTNESS])
        )

    def construct_color_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int, white: int | None
    ) -> list[bytearray] | None:
        """The bytes to send for a color change."""
        effect = channel.status.effect
        msg = _Msg.CMD_SET_NO_MUSIC_STATIC_COLOR
        commands = []

        if effect >= _FXGroup.SOUND_STRIP and effect < _FXGroup.SOUND_MATRIX:
            msg = _Msg.CMD_SET_STRIP_MUSIC_COLOR
        elif effect >= _FXGroup.SOUND_MATRIX:
            msg = _Msg.CMD_SET_SCREEN_MUSIC_DOT_COLOR
        elif effect != _FXGroup.SOLID:
            channel.set_status(
                replace(
                    channel.status,
                    effect=_FXGroup.SOLID.value,
                    mode=_FXMode.SINGULAR.value,
                )
            )

        if channel.status.rgb != (red, green, blue):
            commands.append(self.construct_message(bytearray([red, green, blue, msg])))

        if (
            white is not None and channel.status.white is not None
        ) and channel.status.white != white:
            commands.append(
                self.construct_message(
                    bytearray(
                        [white, 0x00, 0x00, _Msg.CMD_SET_NO_MUSIC_WHITE_BRIGHTNESS]
                    )
                )
            )
        return commands

    def construct_color_two_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int
    ) -> list[bytearray] | None:
        """The bytes to send for a second color change."""
        if channel.status.rgb2 != (red, green, blue):
            return self.construct_message(
                bytearray([red, green, blue, _Msg.CMD_SET_SCREEN_MUSIC_COL_COLOR])
            )
        return None

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
            bytearray([speed, 0x00, 0x00, _Msg.CMD_SET_NO_MUSIC_SPEED])
        )

    ##
    ## Channel Configuration
    ##
    def construct_input_gain_change(
        self, channel: UNILEDChannel, gain: int
    ) -> list[bytearray] | None:
        """The bytes to send for a gain/sensitivity change"""
        return self.construct_message(
            bytearray([gain, 0x00, 0x00, _Msg.CMD_SET_MUSIC_GAIN])
        )

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

    def construct_segment_count_change(
        self, channel: UNILEDChannel, count: int
    ) -> list[bytearray] | None:
        """The bytes to send for a segment count change"""
        return self.construct_message(
            bytearray(
                [
                    count,
                    channel.status.segment_length,
                    0x00,
                    _Msg.CMD_SET_LED_PIXELS_COUNT,
                ]
            )
        )

    def construct_segment_length_change(
        self, channel: UNILEDChannel, length: int
    ) -> list[bytearray] | None:
        """The bytes to send for a segment length change"""
        return self.construct_message(
            bytearray(
                [
                    channel.status.segment_count,
                    length,
                    0x00,
                    _Msg.CMD_SET_LED_PIXELS_COUNT,
                ]
            )
        )

    ##
    ## Channel Informational
    ##
    def listof_channel_modes(self, channel: UNILEDChannel) -> list | None:
        """List of available channel modes"""
        return list(LEDCHORD_MODES.values())

    def codeof_channel_mode(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named mode"""
        if name is None:
            return channel.status.mode
        return [k for k in LEDCHORD_MODES.items() if k[1] == name][0][0]

    def nameof_channel_mode(
        self, channel: UNILEDChannel, mode: int | None = None
    ) -> str | None:
        """Name a mode."""
        if mode is None:
            mode = channel.status.mode
        if mode in LEDCHORD_MODES:
            return LEDCHORD_MODES[mode]
        return None

    def listof_channel_effects(self, channel: UNILEDChannel) -> list | None:
        """List of available channel effects"""
        return list(LEDCHORD_EFFECTS.values())

    def codeof_channel_effect(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named channel effect"""
        if name is None:
            return channel.status.effect
        return [k for k in LEDCHORD_EFFECTS.items() if k[1] == name][0][0]

    def nameof_channel_effect(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> str | None:
        """Name an effect."""
        if effect is None:
            effect = channel.status.effect
        if effect in LEDCHORD_EFFECTS:
            return LEDCHORD_EFFECTS[effect]
        return None

    def codeof_channel_effect_type(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> int | None:
        """Code of channel effect type from effect code"""
        if effect is None:
            effect = channel.status.effect

        if effect == _FXGroup.SOLID:
            return _FXType.STATIC.value
        elif effect >= _FXGroup.SOUND_STRIP and effect < _FXGroup.SOUND_MATRIX:
            return _FXType.SOUND_STRIP.value
        elif effect >= _FXGroup.SOUND_MATRIX:
            return _FXType.SOUND_MATRIX.value
        return _FXType.PATTERN.value

    def nameof_channel_effect_type(
        self, channel: UNILEDChannel, fxtype: int | None = None
    ) -> str | None:
        """Name an effects type."""
        if fxtype is None:
            fxtype = channel.status.fxtype
        if fxtype in LEDCHORD_EFFECT_TYPES:
            return LEDCHORD_EFFECT_TYPES[fxtype]
        return f"{UNKNOWN} ({fxtype})"

    def rangeof_channel_effect_speed(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        return (1, 186, 1)

    def rangeof_channel_input_gain(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return (1, 165, 1)

    def rangeof_channel_segment_count(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return (1, 64, 1)

    def rangeof_channel_segment_length(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return (1, 150, 1)

    def rangeof_channel_led_total(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return (1, 960, 0)


##
## SP107E
##
SP107E = _LEDCHORD(
    model_num=LEDCHORD_MODEL_NUMBER_SP107E,
    model_name=LEDCHORD_MODEL_NAME_SP107E,
    model_type=UNILEDModelType.STRIP,
    description="BLE RGB(W) (Music) Controller",
    manufacturer=LEDCHORD_MANUFACTURER,
    manufacturer_id=LEDCHORD_MANUFACTURER_ID,
    manufacturer_data=b"\x00\x00",
    resolve_protocol=True,
    channels=1,
    needs_on=True,
    sends_status_on_commands=False,
    local_names=[LEDCHORD_LOCAL_NAME_SP107E],
    service_uuids=[LEDCHORD_UUID_FORMAT.format(part) for part in ["ffe0", "ffb0"]],
    write_uuids=[LEDCHORD_UUID_FORMAT.format(part) for part in ["ffe1"]],
    read_uuids=[],
)
