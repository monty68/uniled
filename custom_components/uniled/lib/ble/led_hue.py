"""UniLED BLE Devices - SP LED (LED Hue)"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from ..const import *  # I know!
from ..channel import UniledChannel
from ..features import (
    UniledAttribute,
    UniledLedStrip,
    UniledEffectType,
    UniledEffectLoop,
    UniledEffectSpeed,
    UniledChipType,
    UniledChipOrder,
    UniledSegmentPixels,
)
from ..artifacts import (
    UNILED_CHIP_TYPES as LEDHUE_CHIP_TYPES,
    UNILED_CHIP_4COLOR as LEDHUE_CHIP_TYPES_4COLOR,
    UNILED_CHIP_ORDER_3COLOR as LEDHUE_CHIP_ORDER_RGB,
    UNILED_CHIP_ORDER_4COLOR as LEDHUE_CHIP_ORDER_RGBW,
    UNILEDEffectType,
    UNILEDEffects,
    UNILEDMode,
)
from .device import (
    BASE_UUID_FORMAT as LEDHUE_UUID_FORMAT,
    ParseNotificationError,
    UniledBleDevice,
    UniledBleModel,
)

import functools
import operator
import logging

_LOGGER = logging.getLogger(__name__)

LEDHUE_MANUFACTURER_ID: Final = 0
LEDHUE_MANUFACTURER: Final = "SPLED (LED Hue)"
LEDHUE_MODEL_NUMBER_SP110E: Final = 0x110E
LEDHUE_UUID_SERVICE = [LEDHUE_UUID_FORMAT.format(part) for part in ["ffe0"]]
LEDHUE_UUID_WRITE = [LEDHUE_UUID_FORMAT.format(part) for part in ["ffe1"]]
LEDHUE_UUID_READ = []

LEDHUE_MAX_SEGMENT_PIXELS = 1024
LEDHUE_EFFECT_MAX_SPEED = 255
LEDHUE_EFFECT_TYPE_AUTO = 0x00
LEDHUE_EFFECT_TYPE_DYNAMIC = 0x01
LEDHUE_EFFECT_TYPE_STATIC = 0x79

LEDHUE_EFFECT_GROUPS: Final = [
    {LEDHUE_EFFECT_TYPE_STATIC: UNILEDEffects.SOLID.value},
    {
        (LEDHUE_EFFECT_TYPE_DYNAMIC + k): f"{UNILEDEffectType.PATTERN} {k+1}"
        for k in range(LEDHUE_EFFECT_TYPE_STATIC - 1)
    },
]

LEDHUE_EFFECTS: Final = dict(functools.reduce(operator.or_, LEDHUE_EFFECT_GROUPS))


##
## LED Hue Protocol Implementation
##
@dataclass(frozen=True)
class _LEDHUE(UniledBleModel):
    """LED Hue Protocol Implementation"""

    @dataclass(frozen=True)
    class cmd(IntEnum):
        SET_EFFECT_SPEED = 0x03
        SET_AUTO_LOOP = 0x06
        STATUS_QUERY = 0x10
        SET_CHIP_TYPE = 0x1C
        SET_STATIC_COLOR = 0x1E
        SET_BRIGHTNESS = 0x2A
        SET_EFFECT = 0x2C  # 0x06??
        SET_SEGMENT_PIXELS = 0x2D
        SET_CHIP_ORDER = 0x3C
        SET_WHITE_BRIGHTNESS = 0x69
        TURN_ON = 0xAA
        TURN_OFF = 0xAB
        CHECK_DEVICE = 0xD5
        RENAME_DEVICE = 0xBB

    def parse_notifications(
        self,
        device: UniledBleDevice,
        sender: int,
        data: bytearray,
    ) -> bool:
        """Parse notification message(s)"""

        if sender == 12 and len(data) == 13 and data[0] == 0x00:
            data = data[1:]
        elif sender != 12 or len(data) != 12:
            raise ParseNotificationError("Packet is invalid")

        features = [
            UniledLedStrip(),
            UniledEffectType(),
            UniledEffectLoop(),
            UniledEffectSpeed(LEDHUE_EFFECT_MAX_SPEED),
            UniledChipType(),
            UniledChipOrder(),
            UniledSegmentPixels(LEDHUE_MAX_SEGMENT_PIXELS),
            UniledAttribute(ATTR_UL_EFFECT_NUMBER),
            UniledAttribute(ATTR_UL_EFFECT_LOOP),
            UniledAttribute(ATTR_UL_EFFECT_SPEED),
        ]

        effect = data[1]  # If 0, then in Auto Mode
        chip_type = data[4]

        device.master.status.replace(
            {
                ATTR_UL_DEVICE_FORCE_REFRESH: True,
                ATTR_UL_CHIP_TYPE: self.str_if_key_in(chip_type, LEDHUE_CHIP_TYPES),
                ATTR_UL_CHIP_ORDER: data[5],
                ATTR_UL_SEGMENT_PIXELS: int.from_bytes(data[6:8], byteorder="big"),
                ATTR_UL_POWER: data[0] == 1,
                ATTR_UL_EFFECT_LOOP: not effect,
                ATTR_UL_EFFECT_NUMBER: effect,
                ATTR_HA_EFFECT: self.str_if_key_in(
                    effect, LEDHUE_EFFECTS, str(UNILEDMode.AUTO)
                ),
            }
        )

        if effect == LEDHUE_EFFECT_TYPE_AUTO or effect != LEDHUE_EFFECT_TYPE_STATIC:
            device.master.status.set(ATTR_UL_EFFECT_TYPE, str(UNILEDEffectType.DYNAMIC))
            device.master.status.set(ATTR_UL_EFFECT_SPEED, data[2])
        else:
            device.master.status.set(ATTR_UL_EFFECT_TYPE, str(UNILEDEffectType.STATIC))

        if chip_type not in LEDHUE_CHIP_TYPES_4COLOR:
            device.master.status.set(
                ATTR_UL_CHIP_ORDER, self.str_if_key_in(data[5], LEDHUE_CHIP_ORDER_RGB)
            )
            if effect == LEDHUE_EFFECT_TYPE_STATIC:
                device.master.status.set(
                    ATTR_HA_RGB_COLOR, (data[8], data[9], data[10])
                )
        else:
            device.master.status.set(
                ATTR_UL_CHIP_ORDER, self.str_if_key_in(data[5], LEDHUE_CHIP_ORDER_RGBW)
            )
            if effect == LEDHUE_EFFECT_TYPE_STATIC:
                device.master.status.set(
                    ATTR_HA_RGBW_COLOR, (data[8], data[9], data[10], data[11])
                )
        device.master.status.set(ATTR_HA_BRIGHTNESS, data[3])

        if not device.master.features:
            device.master.features = features

        return True

    def build_on_connect(self, device: UniledBleDevice) -> list[bytearray] | None:
        """Build on connect message(s)"""
        return bytearray([0x00, 0x00, 0x00, self.cmd.CHECK_DEVICE])

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
        red, green, blue = rgb
        return bytearray([red, green, blue, self.cmd.SET_STATIC_COLOR])

    def build_rgbw_color_command(
        self,
        device: UniledBleDevice,
        channel: UniledChannel,
        rgbw: tuple[int, int, int, int],
    ) -> list[bytearray] | None:
        """The bytes to send for a color level change"""
        red, green, blue, white = rgbw
        return [
            self.build_rgb_color_command(device, channel, rgb=(red, green, blue)),
            self.build_white_command(device, channel, white),
        ]

    def build_effect_command(
        self,
        device: UniledBleDevice,
        channel: UniledChannel,
        value: str | int,
    ) -> bytearray | None:
        """The bytes to send for an effect change"""
        if isinstance(value, str):
            effect = self.int_if_str_in(
                value, LEDHUE_EFFECTS, LEDHUE_EFFECT_TYPE_STATIC
            )
        else:
            effect = int(value)
        return bytearray([effect, 0x00, 0x00, self.cmd.SET_EFFECT])

    def fetch_effect_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of effect names"""
        return list(LEDHUE_EFFECTS.values())

    def build_effect_loop_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """The bytes to send for an auto effect loop change."""
        if state and not channel.status.effect_loop:
            channel.context = channel.status.effect_number
            return bytearray([0x00, 0x00, 0x00, self.cmd.SET_AUTO_LOOP])
        last = LEDHUE_EFFECT_TYPE_STATIC if not channel.context else channel.context
        return self.build_effect_command(device, channel, last)

    def build_effect_speed_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect speed change."""
        speed = int(value) & 0xFF
        if not 1 <= speed <= LEDHUE_EFFECT_MAX_SPEED:
            return None
        return bytearray([speed, 0x00, 0x00, self.cmd.SET_EFFECT_SPEED])

    def build_chip_type_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str | None = None
    ) -> bytearray | None:
        """Build chip type message(s)"""
        if (type := self.int_if_str_in(value, LEDHUE_CHIP_TYPES)) is not None:
            return bytearray([type & 0xFF, 0x00, 0x00, self.cmd.SET_CHIP_TYPE])

    def fetch_chip_type_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of chip types"""
        return list(LEDHUE_CHIP_TYPES.values())

    def build_chip_order_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str | None = None
    ) -> bytearray | None:
        """Build chip order message(s)"""
        order_dict = (
            LEDHUE_CHIP_ORDER_RGBW
            if device.master.has(ATTR_HA_RGBW_COLOR)
            else LEDHUE_CHIP_ORDER_RGB
        )
        if (order := self.int_if_str_in(value, order_dict)) is not None:
            return bytearray([order & 0xFF, 0x00, 0x00, self.cmd.SET_CHIP_ORDER])
        return None

    def fetch_chip_order_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of chip orders"""
        if device.master.has(ATTR_HA_RGBW_COLOR):
            return list(LEDHUE_CHIP_ORDER_RGBW.values())
        return list(LEDHUE_CHIP_ORDER_RGB.values())

    def build_segment_pixels_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int | None = None
    ) -> bytearray | None:
        """Build segment length message(s)"""
        if not 1 <= int(value) <= LEDHUE_MAX_SEGMENT_PIXELS:
            return None
        pixels = int(value).to_bytes(2, byteorder="big")
        return bytearray([pixels[0], pixels[1], 0x00, self.cmd.SET_SEGMENT_PIXELS])


##
## SP110E
##
SP110E = _LEDHUE(
    model_num=LEDHUE_MODEL_NUMBER_SP110E,
    model_name="SP110E",
    description="RGB(W) SPI Controller",
    manufacturer=LEDHUE_MANUFACTURER,
    channels=1,
    ble_manufacturer_id=LEDHUE_MANUFACTURER_ID,
    ble_manufacturer_data=b"\x00\x00",
    ble_service_uuids=LEDHUE_UUID_SERVICE,
    ble_write_uuids=LEDHUE_UUID_WRITE,
    ble_read_uuids=LEDHUE_UUID_READ,
)
