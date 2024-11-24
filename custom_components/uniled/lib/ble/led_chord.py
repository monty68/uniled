"""UniLED BLE Devices - SP LED (LED Chord)"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Final

from ..const import *  # I know!
from ..channel import UniledChannel
from ..features import (
    UniledAttribute,
    LightStripFeature,
    LightModeFeature,
    EffectTypeFeature,
    EffectSpeedFeature,
    AudioSensitivityFeature,
    ChipTypeFeature,
    ChipOrderFeature,
    SegmentCountFeature,
    SegmentPixelsFeature,
)
from ..effects import (
    UNILEDEffectType,
    UNILEDEffects,
)
from ..chips import (
    UNILED_CHIP_ORDER_RGB as LEDCHORD_CHIP_ORDER_RGB,
    UNILED_CHIP_ORDER_RGBW as LEDCHORD_CHIP_ORDER_RGBW,
    UNILED_CHIP_TYPES as LEDCHORD_CHIP_TYPES,
    UNILED_CHIP_TYPES_4COLOR as LEDCHORD_CHIP_TYPES_4COLOR,
)
from .device import (
    UUID_BASE_FORMAT as LEDCHORD_UUID_FORMAT,
    ParseNotificationError,
    UniledBleDevice,
    UniledBleModel,
)

import functools
import operator
import logging

_LOGGER = logging.getLogger(__name__)

LEDCHORD_FX_DYNAMIC = 1
LEDCHORD_FX_STATIC = 0xB5
LEDCHORD_FX_STRIP = 0xBE
LEDCHORD_FX_MATRIX = 0xDC

LEDCHORD_LIGHT_MODE_SINGULAR = 0x00
LEDCHORD_LIGHT_MODE_AUTO_DYNAMIC = 0x01
LEDCHORD_LIGHT_MODE_AUTO_STRIP = 0x02
LEDCHORD_LIGHT_MODE_AUTO_MATRIX = 0x03

LEDCHORD_LIGHT_MODES: Final = {
    LEDCHORD_LIGHT_MODE_SINGULAR: "Single FX",
    LEDCHORD_LIGHT_MODE_AUTO_DYNAMIC: "Cycle Dynamic FX's",
    LEDCHORD_LIGHT_MODE_AUTO_STRIP: "Cycle Strip FX's",
    LEDCHORD_LIGHT_MODE_AUTO_MATRIX: "Cycle Matrix FX's",
}

LEDCHORD_MAX_SEGMENT_COUNT = 64
LEDCHORD_MAX_SEGMENT_PIXELS = 150
LEDCHORD_MAX_TOTAL_PIXELS = 960
LEDCHORD_MAX_SENSITIVITY = 165
LEDCHORD_MAX_EFFECT_SPEED = 186

LEDCHORD_EFFECT_TYPE_DYNAMIC = str(UNILEDEffectType.DYNAMIC)
LEDCHORD_EFFECT_TYPE_STATIC = str(UNILEDEffectType.STATIC)
LEDCHORD_EFFECT_TYPE_STRIP = "Sound - Strip FX"
LEDCHORD_EFFECT_TYPE_MATRIX = "Sound - Matrix FX"

LEDCHORD_EFFECT_GROUPS: Final = [
    {LEDCHORD_FX_STATIC: UNILEDEffects.SOLID},
    {
        (LEDCHORD_FX_DYNAMIC + k): f"{LEDCHORD_EFFECT_TYPE_DYNAMIC} FX {k+1}"
        for k in range(180)
    },
    {(LEDCHORD_FX_STRIP + k): f"{LEDCHORD_EFFECT_TYPE_STRIP} {k+1}" for k in range(18)},
    {
        (LEDCHORD_FX_MATRIX + k): f"{LEDCHORD_EFFECT_TYPE_MATRIX} {k+1}"
        for k in range(30)
    },
]

LEDCHORD_EFFECTS: Final = dict(functools.reduce(operator.or_, LEDCHORD_EFFECT_GROUPS))


##
## LED Chord Protocol Implementation
##
@dataclass(frozen=True)
class _LEDCHORD(UniledBleModel):
    """LED Hue Protocol Implementation"""

    @dataclass(frozen=True)
    class cmd(IntEnum):
        TURN_ON = 0xAA
        TURN_OFF = 0xBB
        CHECK_DEVICE = 1
        STATUS_QUERY = 2
        RENAME_DEVICE = 3
        SET_CHIP_ORDER = 4
        SET_CHIP_TYPE = 5
        SET_SEGMENTS = 6
        SET_EFFECT = 8
        SET_EFFECT_SPEED = 9
        SET_BRIGHTNESS = 10
        SET_WHITE_BRIGHTNESS = 11
        SET_COLOR = 12
        SET_DYNAMIC_AUTO_MODE = 13
        SET_STRIP_COLOR = 14
        SET_STRIP_AUTO_MODE = 15
        SET_MATRIX_COL_COLOR = 16
        SET_MATRIX_DOT_COLOR = 17
        SET_MATRIX_AUTO_MODE = 18
        SET_SENSITIVITY = 19

    def __init__(self, id: int, name: str, info: str, data: bytes, channels: int = 1):
        super().__init__(
            model_num=id,
            model_name=name,
            description=info,
            manufacturer="SPLED (LED Chord)",
            channels=channels,
            ble_manufacturer_id=[0, 21301], # Fix Issue #65
            ble_service_uuids=[LEDCHORD_UUID_FORMAT.format(part) for part in ["ffe0"]],
            ble_write_uuids=[LEDCHORD_UUID_FORMAT.format(part) for part in ["ffe1"]],
            ble_read_uuids=[],
            ble_notify_uuids=[],
            ble_manufacturer_data=data,
        )

    def parse_notifications(
        self,
        device: UniledBleDevice,
        sender: int,
        data: bytearray,
    ) -> bool:
        """Parse notification message(s)"""

        # 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14
        # --------------------------------------------
        # 00 01 00 02 18 02 32 b5 00 00 00 6a 24 00 01
        # 00 02 8f 12 fc ff 00 00 00 00 00 ff 00 ff ff

        if len(data) == 15 and data[0] == 0x00 and data[1] == 0x01:
            #
            # Save first status packet, minus the first 2 header bytes
            #
            device.save_notification_data(data[2:])
        elif len(data) == 15 and data[0] == 0x00 and data[1] == 0x02:
            #
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
            power = True if data[0] != 0 else False
            chip_order = data[1]
            chip_type = data[2]
            effect = data[5]

            device.master.status.replace(
                {
                    ATTR_UL_DEVICE_FORCE_REFRESH: True,
                    ATTR_UL_CHIP_TYPE: self.str_if_key_in(
                        chip_type, LEDCHORD_CHIP_TYPES
                    ),
                    ATTR_UL_CHIP_ORDER: chip_order,
                    ATTR_UL_SEGMENT_COUNT: data[3],
                    ATTR_UL_SEGMENT_PIXELS: data[4],
                    ATTR_UL_TOTAL_PIXELS: (data[4] * data[3]),
                    ATTR_UL_POWER: data[0] == 1,
                    ATTR_UL_EFFECT_NUMBER: effect,
                    ATTR_HA_EFFECT: self.str_if_key_in(
                        effect, LEDCHORD_EFFECTS, UNILED_UNKNOWN
                    ),
                }
            )

            mode = -1
            type = UNILED_UNKNOWN
            rgb = (data[13], data[14], data[15])
            white = data[11] if chip_type in LEDCHORD_CHIP_TYPES_4COLOR else None

            if effect == LEDCHORD_FX_STATIC:
                type = LEDCHORD_EFFECT_TYPE_STATIC
                mode = LEDCHORD_LIGHT_MODE_SINGULAR
            elif effect < LEDCHORD_FX_STATIC:
                device.master.status.set(ATTR_UL_EFFECT_SPEED, data[9])
                type = LEDCHORD_EFFECT_TYPE_DYNAMIC
                mode = (
                    LEDCHORD_LIGHT_MODE_AUTO_DYNAMIC
                    if data[6]
                    else LEDCHORD_LIGHT_MODE_SINGULAR
                )
            else:
                device.master.status.set(ATTR_UL_SENSITIVITY, data[25])
                if effect >= LEDCHORD_FX_STRIP and effect < LEDCHORD_FX_MATRIX:
                    rgb = (data[16], data[17], data[18])
                    type = LEDCHORD_EFFECT_TYPE_STRIP
                    mode = (
                        LEDCHORD_LIGHT_MODE_AUTO_STRIP
                        if data[7]
                        else LEDCHORD_LIGHT_MODE_SINGULAR
                    )
                elif effect >= LEDCHORD_FX_MATRIX:
                    rgb = (data[22], data[23], data[24])  # Dot Color
                    device.master.status.set(  # Column Color
                        ATTR_UL_RGB2_COLOR, (data[19], data[20], data[21])
                    )
                    type = LEDCHORD_EFFECT_TYPE_MATRIX
                    mode = (
                        LEDCHORD_LIGHT_MODE_AUTO_MATRIX
                        if data[8]
                        else LEDCHORD_LIGHT_MODE_SINGULAR
                    )

            device.master.status.set(ATTR_HA_BRIGHTNESS, data[10])

            if white is not None:
                device.master.status.set(ATTR_HA_RGBW_COLOR, rgb + (white,))
                device.master.status.set(
                    ATTR_UL_CHIP_ORDER,
                    self.chip_order_name(LEDCHORD_CHIP_ORDER_RGBW, chip_order),
                )
            else:
                device.master.status.set(ATTR_HA_RGB_COLOR, rgb)
                device.master.status.set(
                    ATTR_UL_CHIP_ORDER,
                    self.chip_order_name(LEDCHORD_CHIP_ORDER_RGB, chip_order),
                )
            device.master.status.set(ATTR_UL_EFFECT_TYPE, type)
            device.master.status.set(ATTR_UL_LIGHT_MODE_NUMBER, mode)
            device.master.status.set(
                ATTR_UL_LIGHT_MODE,
                self.str_if_key_in(mode, LEDCHORD_LIGHT_MODES, UNILED_UNKNOWN),
            )

            if not device.master.features:
                device.master.features = [
                    LightStripFeature(extra=UNILED_CONTROL_ATTRIBUTES),
                    LightModeFeature(),
                    EffectTypeFeature(),
                    EffectSpeedFeature(LEDCHORD_MAX_EFFECT_SPEED),
                    ChipTypeFeature(),
                    ChipOrderFeature(),
                    AudioSensitivityFeature(LEDCHORD_MAX_SENSITIVITY),
                    SegmentCountFeature(LEDCHORD_MAX_SEGMENT_COUNT),
                    SegmentPixelsFeature(LEDCHORD_MAX_SEGMENT_PIXELS),
                ]

            return True
        else:
            raise ParseNotificationError("Invalid packet!")
        return False

    def build_on_connect(self, device: UniledBleDevice) -> list[bytearray] | None:
        """Build on connect message(s)"""
        return None

    def build_state_query(self, device: UniledBleDevice) -> bytearray | None:
        """Build a state query message"""
        return bytearray([0x00, 0x00, 0x00, self.cmd.STATUS_QUERY])

    def build_onoff_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """Build power on/off state message(s)"""
        return bytearray(
            [0x00, 0x00, 0x00, self.cmd.TURN_ON if state else self.cmd.TURN_OFF]
        )

    def build_light_mode_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str
    ) -> list[bytearray] | None:
        """The bytes to send for a light mode change."""
        if isinstance(value, str):
            mode = self.int_if_str_in(
                value, LEDCHORD_LIGHT_MODES, LEDCHORD_LIGHT_MODE_SINGULAR
            )
        elif (mode := int(value)) not in LEDCHORD_LIGHT_MODES:
            return None
        if mode == LEDCHORD_LIGHT_MODE_AUTO_DYNAMIC:
            cmd = self.cmd.SET_DYNAMIC_AUTO_MODE
        elif mode == LEDCHORD_LIGHT_MODE_AUTO_STRIP:
            cmd = self.cmd.SET_STRIP_AUTO_MODE
        elif mode == LEDCHORD_LIGHT_MODE_AUTO_MATRIX:
            cmd = self.cmd.SET_MATRIX_AUTO_MODE
        else:
            return self.build_effect_command(
                device, channel, channel.status.effect_number
            )
        return bytearray([0x01, 0x00, 0x00, cmd])

    def fetch_light_mode_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light modes"""
        return list(LEDCHORD_LIGHT_MODES.values())

    def build_brightness_command(
        self, device: UniledBleDevice, channel: UniledChannel, level: int
    ) -> bytearray | None:
        """The bytes to send for a brightness level change"""
        return bytearray([level & 0xFF, 0x00, 0x00, self.cmd.SET_BRIGHTNESS])

    def build_white_command(
        self, device: UniledBleDevice, channel: UniledChannel, white: int
    ) -> bytearray | None:
        """The bytes to send for a white level change"""
        return bytearray([white & 0xFF, 0x00, 0x00, self.cmd.SET_WHITE_BRIGHTNESS])

    def build_rgb_color_command(
        self, device: UniledBleDevice, channel: UniledChannel, rgb: tuple[int, int, int]
    ) -> bytearray | None:
        """The bytes to send for a color level change"""
        cmd = self.cmd.SET_COLOR
        effect = channel.get(ATTR_UL_EFFECT_NUMBER)
        if effect >= LEDCHORD_FX_STRIP and effect < LEDCHORD_FX_MATRIX:
            cmd = self.cmd.SET_STRIP_COLOR
        elif effect >= LEDCHORD_FX_MATRIX:
            cmd = self.cmd.SET_MATRIX_DOT_COLOR
        elif effect != LEDCHORD_FX_STATIC:
            effect = LEDCHORD_FX_STATIC
            mode = LEDCHORD_LIGHT_MODE_SINGULAR
            channel.status.update(
                {
                    ATTR_UL_LIGHT_MODE_NUMBER: mode,
                    ATTR_UL_LIGHT_MODE: self.str_if_key_in(
                        mode, LEDCHORD_LIGHT_MODES, UNILED_UNKNOWN
                    ),
                    ATTR_UL_EFFECT_NUMBER: effect,
                    ATTR_HA_EFFECT: self.str_if_key_in(
                        effect, LEDCHORD_EFFECTS, UNILED_UNKNOWN
                    ),
                    ATTR_HA_RGB_COLOR: rgb,
                }
            )
            channel.status.set(ATTR_HA_RGBW_COLOR, None)

        red, green, blue = rgb
        return bytearray([red, green, blue, self.cmd.SET_COLOR])

    def build_rgb2_color_command(
        self, device: UniledBleDevice, channel: UniledChannel, rgb: tuple[int, int, int]
    ) -> bytearray | None:
        """The bytes to send for a color level change"""
        red, green, blue = rgb
        return bytearray([red, green, blue, self.cmd.SET_MATRIX_COL_COLOR])

    def build_rgbw_color_command(
        self,
        device: UniledBleDevice,
        channel: UniledChannel,
        rgbw: tuple[int, int, int, int],
    ) -> list[bytearray] | None:
        """The bytes to send for a color level change"""
        red, green, blue, white = rgbw
        commands = [self.build_rgb_color_command(device, channel, (red, green, blue))]
        if channel.status.get(ATTR_HA_RGBW_COLOR, None) is not None:
            commands.append(self.build_white_command(device, channel, white))
        return commands

    def build_effect_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str | int
    ) -> bytearray | None:
        """The bytes to send for an effect change"""
        if isinstance(value, str):
            effect = self.int_if_str_in(value, LEDCHORD_EFFECTS, LEDCHORD_FX_STATIC)
        elif (effect := int(value)) not in LEDCHORD_EFFECTS:
            return None
        return bytearray([effect, 0x00, 0x00, self.cmd.SET_EFFECT])

    def fetch_effect_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of effect names"""
        return list(LEDCHORD_EFFECTS.values())

    def build_effect_speed_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect speed change."""
        speed = int(value) & 0xFF
        if not 1 <= speed <= LEDCHORD_MAX_EFFECT_SPEED:
            return None
        return bytearray([speed, 0x00, 0x00, self.cmd.SET_EFFECT_SPEED])

    def build_sensitivity_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for a gain/sensitivity change"""
        if not 1 <= int(value) <= LEDCHORD_MAX_SENSITIVITY:
            return None
        return self.construct_message(
            bytearray([value, 0x00, 0x00, self.cmd.SET_SENSITIVITY])
        )

    def build_chip_type_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str | None = None
    ) -> bytearray | None:
        """Build chip type message(s)"""
        if (type := self.int_if_str_in(value, LEDCHORD_CHIP_TYPES)) is not None:
            return bytearray([type & 0xFF, 0x00, 0x00, self.cmd.SET_CHIP_TYPE])
        return None

    def fetch_chip_type_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of chip types"""
        return list(LEDCHORD_CHIP_TYPES.values())

    def build_chip_order_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str | None = None
    ) -> bytearray | None:
        """Build chip order message(s)"""
        sequence = (
            LEDCHORD_CHIP_ORDER_RGBW
            if channel.has(ATTR_HA_RGBW_COLOR)
            else LEDCHORD_CHIP_ORDER_RGB
        )
        if (order := self.chip_order_index(sequence, value)) is not None:
            return bytearray([order & 0xFF, 0x00, 0x00, self.cmd.SET_CHIP_ORDER])
        return None

    def fetch_chip_order_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of chip orders"""
        if channel.has(ATTR_HA_RGBW_COLOR):
            return self.chip_order_list(LEDCHORD_CHIP_ORDER_RGBW)
        return self.chip_order_list(LEDCHORD_CHIP_ORDER_RGB)

    def build_segment_count_command(
        self,
        device: UniledBleDevice,
        channel: UniledChannel,
        segments: int,
        pixels: int | None = None,
    ) -> bytearray | None:
        """Build segment length message(s)"""
        if not 1 <= int(segments) <= LEDCHORD_MAX_SEGMENT_PIXELS:
            return None
        if pixels is None:
            pixels = channel.status.segment_pixels
        if not 1 <= int(pixels) <= LEDCHORD_MAX_SEGMENT_PIXELS:
            return None
        if (pixels * segments) > LEDCHORD_MAX_TOTAL_PIXELS:
            return None
        return bytearray([segments, pixels, 0x00, self.cmd.SET_SEGMENTS])

    def build_segment_pixels_command(
        self, device: UniledBleDevice, channel: UniledChannel, pixels: int | None
    ) -> bytearray | None:
        """Build segment length message(s)"""
        segments = channel.status.segment_count
        return self.build_segment_count_command(device, channel, segments, pixels)


##
## SP107E
##
SP107E = _LEDCHORD(
    id=0x107E,
    name="SP107E",
    info="RGB(W) SPI (Music) Controller",
    data=b"\x00\x00",
)
