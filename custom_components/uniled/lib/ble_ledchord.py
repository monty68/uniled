"""UniLED BLE Devices - SP107E from SPLED (LedChord)"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final
from enum import IntEnum

from .artifacts import (
    UNKNOWN,
    UNILEDModelType,
    UNILEDColorOrder,
    UNILEDChipset,
    UNILEDEffectType,
    UNILEDEffects,
)
from .states import (
    UNILED_STATE_SETUP,
    UNILED_STATE_COLUMN_COLOR,
    UNILEDSetup,
    UNILEDStatus,
)
from .classes import UNILEDDevice, UNILEDChannel
from .ble_model import UNILEDBLEModel, BASE_UUID_FORMAT as LEDCHORD_UUID_FORMAT

import logging

_LOGGER = logging.getLogger(__name__)

LEDCHORD_MANUFACTURER_ID: Final = 0
LEDCHORD_MANUFACTURER: Final = "SPLED (LedChord)"
LEDCHORD_LOCAL_NAME_SP107E: Final = "SP107E"


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
class _FXGroup(IntEnum):
    PATTERN = 1
    SOLID = 0xB5
    SOUND_STRIP = 0xBE
    SOUND_MATRIX = 0xDC
    CYCLE_PATTERN = SOLID + 1
    CYCLE_STRIP = CYCLE_PATTERN + 1
    CYCLE_MATRIX = CYCLE_STRIP + 1


@dataclass(frozen=True)
class _FXType(IntEnum):
    STATIC = 0x00
    PATTERN = 0x01
    CYCLE_PATTERN = 0x02
    SOUND_STRIP = 0x03
    CYCLE_STRIP = 0x04
    SOUND_MATRIX = 0x05
    CYCLE_MATRIX = 0x06

LEDCHORD_CHIP_TYPES: Final  = {
    # 3 Color - RGB
    0x00: UNILEDChipset.SM16703,
    0x01: UNILEDChipset.TM1804,
    0x02: UNILEDChipset.UCS1903,
    0x03: UNILEDChipset.WS2811,
    0x04: UNILEDChipset.WS2801,
    0x05: UNILEDChipset.SK6812,
    0x06: UNILEDChipset.LPD6803,
    0x07: UNILEDChipset.LPD8806,
    0x08: UNILEDChipset.APA102,
    0x09: UNILEDChipset.APA105,
    0x0A: UNILEDChipset.DMX512,
    0x0B: UNILEDChipset.TM1914,
    0x0C: UNILEDChipset.TM1913,
    0x0D: UNILEDChipset.P9813,
    0x0E: UNILEDChipset.INK1003,
    0x0F: UNILEDChipset.P943S,
    0x10: UNILEDChipset.P9411,
    0x11: UNILEDChipset.P9413,
    0x12: UNILEDChipset.TX1812,
    0x13: UNILEDChipset.TX1813,
    0x14: UNILEDChipset.GS8206,
    0x15: UNILEDChipset.GS8208,
    0x16: UNILEDChipset.SK9822,
    # 4 Color - RGBW
    0x17: UNILEDChipset.TM1814,
    0x18: UNILEDChipset.SK6812_RGBW,
    0x19: UNILEDChipset.P9414,
    0x1A: UNILEDChipset.P9412,
}

LEDCHORD_IC_4COLOR: Final = [
    0x17, # TM1814
    0x18, # SK6812_RGBW
    0x19, # P9414
    0x1A, # P9412
]

LEDCHORD_LED_ORDERS: Final  = {
    0x00: UNILEDColorOrder.RGB,
    0x01: UNILEDColorOrder.RBG,
    0x02: UNILEDColorOrder.GRB,
    0x03: UNILEDColorOrder.GBR,
    0x04: UNILEDColorOrder.BRG,
    0x05: UNILEDColorOrder.BGR,
}

LEDCHORD_EFFECT_TYPES: dict(int, str) = {
    _FXType.STATIC.value: UNILEDEffectType.STATIC,
    _FXType.PATTERN.value: UNILEDEffectType.PATTERN,
    _FXType.CYCLE_PATTERN.value: "Cycle - Pattern FX's",
    _FXType.SOUND_STRIP.value: "Sound - Strip FX",
    _FXType.CYCLE_STRIP.value: "Cycle - Strip FX's",
    _FXType.SOUND_MATRIX.value: "Sound - Matrix FX",
    _FXType.CYCLE_MATRIX.value: "Cycle - Matrix FX's",
}

LEDCHORD_EFFECTS: dict(int, str) = {
    _FXGroup.SOLID.value: UNILEDEffects.SOLID,
    _FXGroup.CYCLE_STRIP.value: LEDCHORD_EFFECT_TYPES[_FXType.CYCLE_STRIP.value],
    _FXGroup.SOUND_STRIP.value + 0: "Sound - Strip FX 1",
    _FXGroup.SOUND_STRIP.value + 1: "Sound - Strip FX 2",
    _FXGroup.SOUND_STRIP.value + 2: "Sound - Strip FX 3",
    _FXGroup.SOUND_STRIP.value + 3: "Sound - Strip FX 4",
    _FXGroup.SOUND_STRIP.value + 4: "Sound - Strip FX 5",
    _FXGroup.SOUND_STRIP.value + 5: "Sound - Strip FX 6",
    _FXGroup.SOUND_STRIP.value + 6: "Sound - Strip FX 7",
    _FXGroup.SOUND_STRIP.value + 7: "Sound - Strip FX 8",
    _FXGroup.SOUND_STRIP.value + 8: "Sound - Strip FX 9",
    _FXGroup.SOUND_STRIP.value + 9: "Sound - Strip FX 10",
    _FXGroup.SOUND_STRIP.value + 10: "Sound - Strip FX 11",
    _FXGroup.SOUND_STRIP.value + 11: "Sound - Strip FX 12",
    _FXGroup.SOUND_STRIP.value + 12: "Sound - Strip FX 13",
    _FXGroup.SOUND_STRIP.value + 13: "Sound - Strip FX 14",
    _FXGroup.SOUND_STRIP.value + 14: "Sound - Strip FX 15",
    _FXGroup.SOUND_STRIP.value + 15: "Sound - Strip FX 16",
    _FXGroup.SOUND_STRIP.value + 16: "Sound - Strip FX 17",
    _FXGroup.SOUND_STRIP.value + 17: "Sound - Strip FX 18",
    _FXGroup.CYCLE_MATRIX.value: LEDCHORD_EFFECT_TYPES[_FXType.CYCLE_MATRIX.value],
    _FXGroup.SOUND_MATRIX.value + 0: "Sound - Matrix FX 1",
    _FXGroup.SOUND_MATRIX.value + 1: "Sound - Matrix FX 2",
    _FXGroup.SOUND_MATRIX.value + 2: "Sound - Matrix FX 3",
    _FXGroup.SOUND_MATRIX.value + 3: "Sound - Matrix FX 4",
    _FXGroup.SOUND_MATRIX.value + 4: "Sound - Matrix FX 5",
    _FXGroup.SOUND_MATRIX.value + 5: "Sound - Matrix FX 6",
    _FXGroup.SOUND_MATRIX.value + 6: "Sound - Matrix FX 7",
    _FXGroup.SOUND_MATRIX.value + 7: "Sound - Matrix FX 8",
    _FXGroup.SOUND_MATRIX.value + 8: "Sound - Matrix FX 9",
    _FXGroup.SOUND_MATRIX.value + 9: "Sound - Matrix FX 10",
    _FXGroup.SOUND_MATRIX.value + 10: "Sound - Matrix FX 11",
    _FXGroup.SOUND_MATRIX.value + 11: "Sound - Matrix FX 12",
    _FXGroup.SOUND_MATRIX.value + 12: "Sound - Matrix FX 13",
    _FXGroup.SOUND_MATRIX.value + 13: "Sound - Matrix FX 14",
    _FXGroup.SOUND_MATRIX.value + 14: "Sound - Matrix FX 15",
    _FXGroup.SOUND_MATRIX.value + 15: "Sound - Matrix FX 16",
    _FXGroup.SOUND_MATRIX.value + 16: "Sound - Matrix FX 17",
    _FXGroup.SOUND_MATRIX.value + 17: "Sound - Matrix FX 18",
    _FXGroup.SOUND_MATRIX.value + 18: "Sound - Matrix FX 19",
    _FXGroup.SOUND_MATRIX.value + 19: "Sound - Matrix FX 20",
    _FXGroup.SOUND_MATRIX.value + 20: "Sound - Matrix FX 21",
    _FXGroup.SOUND_MATRIX.value + 21: "Sound - Matrix FX 22",
    _FXGroup.SOUND_MATRIX.value + 22: "Sound - Matrix FX 23",
    _FXGroup.SOUND_MATRIX.value + 23: "Sound - Matrix FX 24",
    _FXGroup.SOUND_MATRIX.value + 24: "Sound - Matrix FX 25",
    _FXGroup.SOUND_MATRIX.value + 25: "Sound - Matrix FX 26",
    _FXGroup.SOUND_MATRIX.value + 26: "Sound - Matrix FX 27",
    _FXGroup.SOUND_MATRIX.value + 27: "Sound - Matrix FX 28",
    _FXGroup.SOUND_MATRIX.value + 28: "Sound - Matrix FX 29",
    _FXGroup.SOUND_MATRIX.value + 29: "Sound - Matrix FX 30",
    _FXGroup.CYCLE_PATTERN.value: LEDCHORD_EFFECT_TYPES[_FXType.CYCLE_PATTERN.value],
    0x01: UNILEDEffects.RAINBOW,
    0x02: "Pattern FX 2",
    0x03: "Pattern FX 3",
    0x04: "Pattern FX 4",
    0x0E: "Pattern FX 14",
}


@dataclass(frozen=True)
class _LEDCHORD(UNILEDBLEModel):
    """LedChord Protocol Implementation"""

    ##
    ## Device Control
    ##
    def construct_connect_message(self) -> bytearray | None:
        """The bytes to send when first connecting."""
        #return self.construct_message(bytearray([0x00, 0x00, 0x00, _Msg.CMD_CHECK_DEVICE]))
        return None

    def construct_status_query(self, device: UNILEDDevice) -> bytearray:
        """The bytes to send for a state query."""
        return self.construct_message(bytearray([0x00, 0x00, 0x00, _Msg.CMD_GET_INFO]))

    async def async_decode_notifications(
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
            # 7  = Auto Strip Music
            # 8  = Auto Matrix Music
            # 9  = Speed
            # 10 = Brightness Level
            # 11 = White Level
            # 12 = ?? Unknown
            # 13 = Static Red
            # 14 = Static Green
            # 15 = Static Blue
            # 16 = Music Red
            # 17 = Music Green
            # 18 = Music Blue
            # 19 = Matrix Column Red
            # 20 = Matrix Column Green
            # 21 = Matrix Column Blue
            # 22 = Matrix Dot Red
            # 23 = Matrix Dot Green
            # 24 = Matrix Dot Blue
            # 25 = Input Gain
            #

            rgb = (data[13], data[14], data[15])
            fxtype = _FXType.STATIC
            effect = data[5]
            white = data[11]
            chipset = data[2]

            if chipset not in LEDCHORD_IC_4COLOR:
                white = None

            if effect < _FXGroup.SOLID:
                fxtype = _FXType.CYCLE_PATTERN if data[6] else _FXType.PATTERN
                if fxtype == _FXType.CYCLE_PATTERN.value:
                    effect = _FXGroup.CYCLE_PATTERN.value
            elif effect >= _FXGroup.SOUND_STRIP and effect < _FXGroup.SOUND_MATRIX:
                fxtype = _FXType.CYCLE_STRIP if data[7] else _FXType.SOUND_STRIP
                if fxtype == _FXType.CYCLE_STRIP.value:
                    effect = _FXGroup.CYCLE_STRIP.value
                rgb = (data[16], data[17], data[18])
            elif effect >= _FXGroup.SOUND_MATRIX:
                fxtype = _FXType.CYCLE_MATRIX if data[8] else _FXType.SOUND_MATRIX
                if fxtype == _FXType.CYCLE_MATRIX.value:
                    effect = _FXGroup.CYCLE_MATRIX.value
                rgb = (data[19], data[20], data[21])

            return UNILEDStatus(
                power=data[0],
                fxtype=fxtype.value,
                effect=effect,
                speed=data[9],
                white=white,
                level=data[10],
                rgb=rgb,
                gain=data[25],
                extra={
                    UNILED_STATE_SETUP: UNILEDSetup(
                        order=data[1], chipset=chipset, segments=data[3], leds=data[4]
                    ),
                    UNILED_STATE_COLUMN_COLOR: (data[19], data[20], data[21]),
                },
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

    def construct_effect_change(
        self, channel: UNILEDChannel, effect: int
    ) -> list[bytearray] | None:
        """The bytes to send for an effect change."""
        commands: list[bytearray] = []

        if effect == _FXGroup.CYCLE_PATTERN:
            return self.construct_message(
                bytearray([True, 0x50, 0x4D, _Msg.CMD_SET_NO_MUSIC_AUTO_MODE])
            )
        elif effect == _FXGroup.CYCLE_STRIP:
            return self.construct_message(
                bytearray([True, 0x50, 0x4D, _Msg.CMD_SET_STRIP_MUSIC_AUTO_MODE])
            )
        elif effect == _FXGroup.CYCLE_MATRIX:
            return self.construct_message(
                bytearray([True, 0x50, 0x4D, _Msg.CMD_SET_SCREEN_MUSIC_AUTO_MODE])
            )
        elif (
            effect >= _FXGroup.SOUND_MATRIX
            and channel.effect_type == _FXType.CYCLE_MATRIX
        ):
            commands.append(
                self.construct_message(
                    bytearray([False, 0x50, 0x4D, _Msg.CMD_SET_SCREEN_MUSIC_AUTO_MODE])
                )
            )
        elif (
            effect >= _FXGroup.SOUND_STRIP
            and effect < _FXGroup.SOUND_MATRIX
            and channel.effect_type == _FXType.CYCLE_STRIP
        ):
            commands.append(
                self.construct_message(
                    bytearray([False, 0x50, 0x4D, _Msg.CMD_SET_STRIP_MUSIC_AUTO_MODE])
                )
            )
        elif effect < _FXGroup.SOLID and channel.effect_type == _FXType.CYCLE_PATTERN:
            commands.append(
                self.construct_message(
                    bytearray([False, 0x50, 0x4D, _Msg.CMD_SET_NO_MUSIC_AUTO_MODE])
                )
            )

        commands.append(
            self.construct_message(bytearray([effect, 0x50, 0x4D, _Msg.CMD_SET_MODE]))
        )

        return commands

    def construct_effect_speed_change(
        self, channel: UNILEDChannel, speed: int
    ) -> list[bytearray] | None:
        """The bytes to send for an effect speed change."""
        return self.construct_message(
            bytearray([speed, 0x00, 0x00, _Msg.CMD_SET_NO_MUSIC_SPEED])
        )

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
        """The bytes to send for a color level change."""
        return self.construct_message(
            bytearray([level, 0x00, 0x00, _Msg.CMD_SET_NO_MUSIC_WHITE_BRIGHTNESS])
        )

    def construct_color_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a color change."""
        effect = channel.status.effect
        cmd = _Msg.CMD_SET_NO_MUSIC_STATIC_COLOR

        if effect >= _FXGroup.SOUND_STRIP and effect < _FXGroup.SOUND_MATRIX:
            cmd = _Msg.CMD_SET_STRIP_MUSIC_COLOR
        elif effect >= _FXGroup.SOUND_MATRIX:
            cmd = _Msg.CMD_SET_SCREEN_MUSIC_DOT_COLOR
        elif effect != _FXGroup.SOLID:
            channel.set_status(replace(channel.status, effect=_FXGroup.SOLID.value))

        return self.construct_message(bytearray([red, green, blue, cmd]))

    def construct_input_gain_change(
        self, device: UNILEDDevice, gain: int
    ) -> list[bytearray] | None:
        """The bytes to send for a gain/sensitivity change"""
        return self.construct_message(
            bytearray([gain, 0x00, 0x00, _Msg.CMD_SET_MUSIC_GAIN])
        )

    ##
    ## Channel Informational
    ##
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
        self, device: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return (1, 165, 1)

##
## SP107E
##
SP107E = _LEDCHORD(
    model_num=0x107E,
    model_name="SP107E",
    model_type=UNILEDModelType.STRIP,
    description="BLE RGB(W) (Music) Controller",
    manufacturer=LEDCHORD_MANUFACTURER,
    manufacturer_id=LEDCHORD_MANUFACTURER_ID,
    manufacturer_data=b"\x00\x00",
    resolve_protocol=False,
    channels=1,
    extra_data={},
    service_uuids=[LEDCHORD_UUID_FORMAT.format(part) for part in ["ffe0", "ffb0"]],
    write_uuids=[LEDCHORD_UUID_FORMAT.format(part) for part in ["ffe1"]],
    read_uuids=[],
)
