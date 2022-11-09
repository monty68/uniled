"""UniLED BLE Devices - SP107E - SPLED (LedChord)"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from enum import IntEnum

from .artifacts import (
    UNKNOWN,
    UNILEDModelType,
    # UNILEDColorOrder,
    # UNILEDInputs,
    UNILEDModes,
    UNILEDEffects,
)
from .states import (
    UNILED_STATE_SETUP,
    # UNILED_STATE_INPUT,
    UNILED_STATE_MUSIC_COLOR,
    UNILED_STATE_COLUMN_COLOR,
    UNILED_STATE_DOT_COLOR,
    UNILEDSetup,
    UNILEDStatus,
)
from .helpers import StrEnum
from .classes import UNILEDDevice, UNILEDChannel
from .ble_banlanx1 import BANLANX1_LED_ORDERS as LEDCHORD_LED_ORDERS
from .ble_model import UNILEDBLEModel, BASE_UUID_FORMAT as LEDCHORD_UUID_FORMAT

import logging

_LOGGER = logging.getLogger(__name__)

LEDCHORD_MANUFACTURER_ID: Final = 0
LEDCHORD_MANUFACTURER: Final = "SPLED (LedChord)"
LEDCHORD_LOCAL_NAME: Final = "SP107E"


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
    DYNAMIC = 1
    SOLID = 0xB5
    SOUND_STRIP = 0xBE
    SOUND_MATRIX = 0xDC
    CYCLE_DYNAMIC = SOLID + 1
    CYCLE_STRIP = CYCLE_DYNAMIC + 1
    CYCLE_MATRIX = CYCLE_STRIP + 1


@dataclass(frozen=True)
class _FXType(IntEnum):
    STATIC = 0x00
    DYNAMIC = 0x01
    CYCLE_DYNAMIC = 0x02
    SOUND_STRIP = 0x03
    CYCLE_STRIP = 0x04
    SOUND_MATRIX = 0x05
    CYCLE_MATRIX = 0x06


LEDCHORD_EFFECT_TYPES: dict(int, str) = {
    _FXType.STATIC.value: UNILEDModes.STATIC,
    _FXType.DYNAMIC.value: UNILEDModes.DYNAMIC,
    _FXType.CYCLE_DYNAMIC.value: "Cycle all Dynamic FX's",
    _FXType.SOUND_STRIP.value: "Strip Sound FX",
    _FXType.CYCLE_STRIP.value: "Cycle all Strip FX's",
    _FXType.SOUND_MATRIX.value: "Matrix Sound FX",
    _FXType.CYCLE_MATRIX.value: "Cycle all Matrix FX's",
}

LEDCHORD_EFFECTS: dict(int, str) = {
    _FXGroup.SOLID.value: UNILEDEffects.SOLID,
    _FXGroup.CYCLE_DYNAMIC.value: LEDCHORD_EFFECT_TYPES[_FXType.CYCLE_DYNAMIC.value],
    0x01: "Dynamic FX 1",
    0x02: "Dynamic FX 2",
    0x03: "Dynamic FX 3",
    0x04: "Dynamic FX 4",
    0x0E: "Dynamic FX 14",
    _FXGroup.CYCLE_STRIP.value: LEDCHORD_EFFECT_TYPES[_FXType.CYCLE_STRIP.value],
    _FXGroup.SOUND_STRIP.value + 0: "Strip FX 1",
    _FXGroup.SOUND_STRIP.value + 2: "Strip FX 2",
    _FXGroup.SOUND_STRIP.value + 3: "Strip FX 3",
    _FXGroup.SOUND_STRIP.value + 4: "Strip FX 4",
    _FXGroup.CYCLE_MATRIX.value: LEDCHORD_EFFECT_TYPES[_FXType.CYCLE_MATRIX.value],
    _FXGroup.SOUND_MATRIX.value + 0: "Matrix FX 1",
    _FXGroup.SOUND_MATRIX.value + 1: "Matrix FX 2",
    _FXGroup.SOUND_MATRIX.value + 2: "Matrix FX 3",
    _FXGroup.SOUND_MATRIX.value + 3: "Matrix FX 4",
}


@dataclass(frozen=True)
class LEDCHORD(UNILEDBLEModel):
    """LedChord Protocol Implementation"""

    ##
    ## Device Control
    ##
    def construct_connect_message(self) -> bytearray | None:
        """The bytes to send when first connecting."""
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
            # 19 = Music Column Red
            # 20 = Music Column Green
            # 21 = Music Column Blue
            # 22 = Music Dot Red
            # 23 = Music Dot Green
            # 24 = Music Dot Blue
            # 25 = Music Gain
            #

            rgb = (data[13], data[14], data[15])
            fxtype = _FXType.STATIC
            effect = data[5]

            if effect < _FXGroup.SOLID:
                fxtype = _FXType.CYCLE_DYNAMIC if data[6] else _FXType.DYNAMIC
                if fxtype == _FXType.CYCLE_DYNAMIC.value:
                    effect = _FXGroup.CYCLE_DYNAMIC.value
                    rgb = None
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

            _LOGGER.debug(
                "Effect: %s (AM=%s), type: %s",
                hex(data[5]),
                data[8],
                self.nameof_channel_effect_type(device.master, fxtype.value),
            )

            return UNILEDStatus(
                power=data[0],
                fxtype=fxtype.value,
                effect=effect,
                speed=data[9],
                level=data[10],
                rgb=rgb,
                gain=data[25],
                extra={
                    UNILED_STATE_SETUP: UNILEDSetup(
                        order=data[1], chipset=data[2], segments=data[3], leds=data[4]
                    ),
                    # UNILED_STATE_MUSIC_COLOR: (data[16], data[17], data[18]),
                    UNILED_STATE_COLUMN_COLOR: (data[19], data[20], data[21]),
                    # UNILED_STATE_DOT_COLOR: (data[22], data[23], data[24]),
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
                [0x00, 0x50, 0x4D, _Msg.CMD_LED_ON if turn_on else _Msg.CMD_LED_OFF]
            )
        )

    def construct_effect_change(
        self, channel: UNILEDChannel, effect: int
    ) -> list[bytearray] | None:
        """The bytes to send for an effect change."""
        commands: list[bytearray] = []

        if effect == _FXGroup.CYCLE_DYNAMIC:
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
        elif effect < _FXGroup.SOLID and channel.effect_type == _FXType.CYCLE_DYNAMIC:
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
            bytearray([speed, 0x50, 0x4D, _Msg.CMD_SET_NO_MUSIC_SPEED])
        )

    def construct_level_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a color level change."""
        return self.construct_message(
            bytearray([level, 0x50, 0x4D, _Msg.CMD_SET_NO_MUSIC_BRIGHTNESS])
        )

    def construct_white_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a color level change."""
        return self.construct_message(
            bytearray([level, 0x50, 0x4D, _Msg.CMD_SET_NO_MUSIC_WHITE_BRIGHTNESS])
        )

    def construct_color_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a color change."""
        effect = channel.status.effect

        if effect == _FXGroup.SOLID:
            cmd = _Msg.CMD_SET_NO_MUSIC_STATIC_COLOR
        elif effect >= _FXGroup.SOUND_STRIP and effect < _FXGroup.SOUND_MATRIX:
            cmd = _Msg.CMD_SET_STRIP_MUSIC_COLOR
        elif effect >= _FXGroup.SOUND_MATRIX:
            cmd = _Msg.CMD_SET_SCREEN_MUSIC_DOT_COLOR
        else:
            return None
        return self.construct_message(bytearray([red, green, blue, cmd]))

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
        return (1, 10, 1)

    def rangeof_channel_effect_length(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect length (min,max,step)."""
        return (1, 150, 1)


##
## SP107E
##
SP107E = LEDCHORD(
    model_num=0x107E,
    model_name="SP107E",
    model_type=UNILEDModelType.STRIP,
    description="BLE RGB (Music) Controller",
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
