"""UniLED BLE Devices - SP LED (BanlanX v2)"""
from __future__ import annotations
from itertools import chain
from typing import Final

from ..const import *  # I know!
from ..channel import UniledChannel
from ..features import (
    UniledAttribute,
    LightStripFeature,
    LightModeFeature,
    EffectLoopFeature,
    EffectTypeFeature,
    EffectSpeedFeature,
    EffectLengthFeature,
    AudioSensitivityFeature,
    AudioInputFeature,
    ChipOrderFeature,
)
from ..effects import (
    UNILED_EFFECT_TYPE_DYNAMIC,
    UNILED_EFFECT_TYPE_STATIC,
    UNILED_EFFECT_TYPE_SOUND,
    UNILEDEffects,
)
from .device import (
    UUID_BASE_FORMAT as BANLANX_UUID_FORMAT,
    BANLANX_MANUFACTURER,
    BANLANX_MANUFACTURER_ID,
    ParseNotificationError,
    UniledBleDevice,
    UniledBleModel,
)

from ..chips import UNILED_CHIP_ORDER_RGB, UNILED_CHIP_ORDER_RGBW

import logging

_LOGGER = logging.getLogger(__name__)

BANLANX2_AUDIO_INPUTS: Final = {
    0x00: UNILED_AUDIO_INPUT_INTMIC,
    0x01: UNILED_AUDIO_INPUT_PLAYER,
    0x02: UNILED_AUDIO_INPUT_EXTMIC,
}

BANLANX2_LIGHT_MODE_SINGULAR: Final = 0x00
BANLANX2_LIGHT_MODE_AUTO_DYNAMIC: Final = 0x01
BANLANX2_LIGHT_MODE_AUTO_SOUND: Final = 0x02

BANLANX2_LIGHT_MODES: Final = {
    BANLANX2_LIGHT_MODE_SINGULAR: "Single FX",
    BANLANX2_LIGHT_MODE_AUTO_DYNAMIC: "Cycle Dynamic FX's",
    BANLANX2_LIGHT_MODE_AUTO_SOUND: "Cycle Sound FX's",
}

BANLANX2_MAX_SENSITIVITY: Final = 16
BANLANX2_MAX_EFFECT_SPEED: Final = 10
BANLANX2_MAX_EFFECT_LENGTH: Final = 150

BANLANX2_EFFECT_SOLID: Final = 0xBE
BANLANX2_EFFECT_WHITE: Final = 0xBF
BANLANX2_EFFECT_SOUND: Final = 0xC9

BANLANX2_EFFECTS_RGB: Final = {
    BANLANX2_EFFECT_SOLID: UNILEDEffects.SOLID_COLOR,
    0x01: UNILEDEffects.RAINBOW,
    0x02: UNILEDEffects.RAINBOW_METEOR,
    0x03: UNILEDEffects.RAINBOW_STARS,
    0x04: UNILEDEffects.RAINBOW_SPIN,
    0x05: UNILEDEffects.FIRE_RED_YELLOW,
    0x06: UNILEDEffects.FIRE_RED_PURPLE,
    0x07: UNILEDEffects.FIRE_GREEN_YELLOW,
    0x08: UNILEDEffects.FIRE_GREEN_CYAN,
    0x09: UNILEDEffects.FIRE_BLUE_PURPLE,
    0x0A: UNILEDEffects.FIRE_BLUE_CYAN,
    0x0B: UNILEDEffects.COMET_RED,
    0x0C: UNILEDEffects.COMET_GREEN,
    0x0D: UNILEDEffects.COMET_BLUE,
    0x0E: UNILEDEffects.COMET_YELLOW,
    0x0F: UNILEDEffects.COMET_CYAN,
    0x10: UNILEDEffects.COMET_PURPLE,
    0x11: UNILEDEffects.COMET_WHITE,
    0x12: UNILEDEffects.METEOR_RED,
    0x13: UNILEDEffects.METEOR_GREEN,
    0x14: UNILEDEffects.METEOR_BLUE,
    0x15: UNILEDEffects.METEOR_YELLOW,
    0x16: UNILEDEffects.METEOR_CYAN,
    0x17: UNILEDEffects.METEOR_PURPLE,
    0x18: UNILEDEffects.METEOR_WHITE,
    0x19: UNILEDEffects.GRADUAL_SNAKE_RED_GREEN,
    0x1A: UNILEDEffects.GRADUAL_SNAKE_RED_BLUE,
    0x1B: UNILEDEffects.GRADUAL_SNAKE_RED_YELLOW,
    0x1C: UNILEDEffects.GRADUAL_SNAKE_RED_CYAN,
    0x1D: UNILEDEffects.GRADUAL_SNAKE_RED_PURPLE,
    0x1E: UNILEDEffects.GRADUAL_SNAKE_RED_WHITE,
    0x1F: UNILEDEffects.GRADUAL_SNAKE_GREEN_BLUE,
    0x20: UNILEDEffects.GRADUAL_SNAKE_GREEN_YELLOW,
    0x21: UNILEDEffects.GRADUAL_SNAKE_GREEN_CYAN,
    0x22: UNILEDEffects.GRADUAL_SNAKE_GREEN_PURPLE,
    0x23: UNILEDEffects.GRADUAL_SNAKE_GREEN_WHITE,
    0x24: UNILEDEffects.GRADUAL_SNAKE_BLUE_YELLOW,
    0x25: UNILEDEffects.GRADUAL_SNAKE_BLUE_CYAN,
    0x26: UNILEDEffects.GRADUAL_SNAKE_BLUE_PURPLE,
    0x27: UNILEDEffects.GRADUAL_SNAKE_BLUE_WHITE,
    0x28: UNILEDEffects.GRADUAL_SNAKE_YELLOW_CYAN,
    0x29: UNILEDEffects.GRADUAL_SNAKE_YELLOW_PURPLE,
    0x2A: UNILEDEffects.GRADUAL_SNAKE_YELLOW_WHITE,
    0x2B: UNILEDEffects.GRADUAL_SNAKE_CYAN_PURPLE,
    0x2C: UNILEDEffects.GRADUAL_SNAKE_CYAN_WHITE,
    0x2D: UNILEDEffects.GRADUAL_SNAKE_PURPLE_WHITE,
    0x2E: UNILEDEffects.WAVE_RED,
    0x2F: UNILEDEffects.WAVE_GREEN,
    0x30: UNILEDEffects.WAVE_BLUE,
    0x31: UNILEDEffects.WAVE_YELLOW,
    0x32: UNILEDEffects.WAVE_CYAN,
    0x33: UNILEDEffects.WAVE_PURPLE,
    0x34: UNILEDEffects.WAVE_WHITE,
    0x35: UNILEDEffects.WAVE_RED_GREEN,
    0x36: UNILEDEffects.WAVE_RED_BLUE,
    0x37: UNILEDEffects.WAVE_RED_YELLOW,
    0x38: UNILEDEffects.WAVE_RED_CYAN,
    0x39: UNILEDEffects.WAVE_RED_PURPLE,
    0x3A: UNILEDEffects.WAVE_RED_WHITE,
    0x3B: UNILEDEffects.WAVE_GREEN_BLUE,
    0x3C: UNILEDEffects.WAVE_GREEN_YELLOW,
    0x3D: UNILEDEffects.WAVE_GREEN_CYAN,
    0x3E: UNILEDEffects.WAVE_GREEN_PURPLE,
    0x3F: UNILEDEffects.WAVE_GREEN_WHITE,
    0x40: UNILEDEffects.WAVE_BLUE_YELLOW,
    0x41: UNILEDEffects.WAVE_BLUE_CYAN,
    0x42: UNILEDEffects.WAVE_BLUE_PURPLE,
    0x43: UNILEDEffects.WAVE_BLUE_WHITE,
    0x44: UNILEDEffects.WAVE_YELLOW_CYAN,
    0x45: UNILEDEffects.WAVE_YELLOW_PURPLE,
    0x46: UNILEDEffects.WAVE_YELLOW_WHITE,
    0x47: UNILEDEffects.WAVE_CYAN_PURPLE,
    0x48: UNILEDEffects.WAVE_CYAN_WHITE,
    0x49: UNILEDEffects.WAVE_PURPLE_WHITE,
    0x4A: UNILEDEffects.STARS_RED,
    0x4B: UNILEDEffects.STARS_GREEN,
    0x4C: UNILEDEffects.STARS_BLUE,
    0x4D: UNILEDEffects.STARS_YELLOW,
    0x4E: UNILEDEffects.STARS_CYAN,
    0x4F: UNILEDEffects.STARS_PURPLE,
    0x50: UNILEDEffects.STARS_WHITE,
    0x51: UNILEDEffects.BACKGROUND_STARS_RED,
    0x52: UNILEDEffects.BACKGROUND_STARS_GREEN,
    0x53: UNILEDEffects.BACKGROUND_STARS_BLUE,
    0x54: UNILEDEffects.BACKGROUND_STARS_YELLOW,
    0x55: UNILEDEffects.BACKGROUND_STARS_CYAN,
    0x56: UNILEDEffects.BACKGROUND_STARS_PURPLE,
    0x57: UNILEDEffects.BACKGROUND_STARS_RED_WHITE,
    0x58: UNILEDEffects.BACKGROUND_STARS_GREEN_WHITE,
    0x59: UNILEDEffects.BACKGROUND_STARS_BLUE_WHITE,
    0x5A: UNILEDEffects.BACKGROUND_STARS_YELLOW_WHITE,
    0x5B: UNILEDEffects.BACKGROUND_STARS_CYAN_WHITE,
    0x5C: UNILEDEffects.BACKGROUND_STARS_PURPLE_WHITE,
    0x5D: UNILEDEffects.BACKGROUND_STARS_WHITE_WHITE,
    0x5E: UNILEDEffects.BREATH_RED,
    0x5F: UNILEDEffects.BREATH_GREEN,
    0x60: UNILEDEffects.BREATH_BLUE,
    0x61: UNILEDEffects.BREATH_YELLOW,
    0x62: UNILEDEffects.BREATH_CYAN,
    0x63: UNILEDEffects.BREATH_PURPLE,
    0x64: UNILEDEffects.BREATH_WHITE,
    0x65: UNILEDEffects.STACKING_RED,
    0x66: UNILEDEffects.STACKING_GREEN,
    0x67: UNILEDEffects.STACKING_BLUE,
    0x68: UNILEDEffects.STACKING_YELLOW,
    0x69: UNILEDEffects.STACKING_CYAN,
    0x6A: UNILEDEffects.STACKING_PRUPLE,
    0x6B: UNILEDEffects.STACKING_WHITE,
    0x6C: UNILEDEffects.STACK_FULL_COLOR,
    0x6D: UNILEDEffects.STACK_RED_GREEN,
    0x6E: UNILEDEffects.STACK_GREEN_BLUE,
    0x6F: UNILEDEffects.STACK_BLUE_YELLOW,
    0x70: UNILEDEffects.STACK_YELLOW_CYAN,
    0x71: UNILEDEffects.STACK_CYAN_PURPLE,
    0x72: UNILEDEffects.STACK_PURPLE_WHITE,
    0x73: UNILEDEffects.SNAKE_RED_BLUE_WHITE,
    0x74: UNILEDEffects.SNAKE_GREEN_YELLOW_WHITE,
    0x75: UNILEDEffects.SNAKE_RED_GREEN_WHITE,
    0x76: UNILEDEffects.SNAKE_RED_YELLOW,
    0x77: UNILEDEffects.SNAKE_RED_WHITE,
    0x78: UNILEDEffects.SNAKE_GREEN_WHITE,
    0x79: UNILEDEffects.COMET_SPIN_RED,
    0x7A: UNILEDEffects.COMET_SPIN_GREEN,
    0x7B: UNILEDEffects.COMET_SPIN_BLUE,
    0x7C: UNILEDEffects.COMET_SPIN_YELLOW,
    0x7D: UNILEDEffects.COMET_SPIN_CYAN,
    0x7E: UNILEDEffects.COMET_SPIN_PURPLE,
    0x7F: UNILEDEffects.COMET_SPIN_WHITE,
    0x80: UNILEDEffects.DOT_SPIN_RED,
    0x81: UNILEDEffects.DOT_SPIN_GREEN,
    0x82: UNILEDEffects.DOT_SPIN_BLUE,
    0x83: UNILEDEffects.DOT_SPIN_YELLOW,
    0x84: UNILEDEffects.DOT_SPIN_CYAN,
    0x85: UNILEDEffects.DOT_SPIN_PURPLE,
    0x86: UNILEDEffects.DOT_SPIN_WHITE,
    0x87: UNILEDEffects.SEGMENT_SPIN_RED,
    0x88: UNILEDEffects.SEGMENT_SPIN_GREEN,
    0x89: UNILEDEffects.SEGMENT_SPIN_BLUE,
    0x8A: UNILEDEffects.SEGMENT_SPIN_YELLOW,
    0x8B: UNILEDEffects.SEGMENT_SPIN_CYAN,
    0x8C: UNILEDEffects.SEGMENT_SPIN_PURPLE,
    0x8D: UNILEDEffects.SEGMENT_SPIN_WHITE,
    0x8E: UNILEDEffects.GRADIENT,
}

BANLANX2_EFFECTS_SOUND: Final = {
    0xC9: UNILEDEffects.SOUND_RHYTHM_SPECTRUM_FULL,
    0xCA: UNILEDEffects.SOUND_RHYTHM_SPECTRUM_SINGLE,
    0xCB: UNILEDEffects.SOUND_RHYTHM_STARS_FULL,
    0xCC: UNILEDEffects.SOUND_RHYTHM_STARS_SINGLE,
    0xCD: UNILEDEffects.SOUND_ENERGY_GRADIENT,
    0xCE: UNILEDEffects.SOUND_ENERGY_SINGLE,
    0xCF: UNILEDEffects.SOUND_PULSE_GRADIENT,
    0xD0: UNILEDEffects.SOUND_PULSE_SINGLE,
    0xD1: UNILEDEffects.SOUND_EJECTION_FORWARD_FULL,
    0xD2: UNILEDEffects.SOUND_EJECTION_FORWARD_SINGLE,
    0xD3: UNILEDEffects.SOUND_EJECTION_BACKWARD_FULL,
    0xD4: UNILEDEffects.SOUND_EJECTION_BACKWARD_SINGLE,
    0xD5: UNILEDEffects.SOUND_VU_METER_FULL,
    0xD6: UNILEDEffects.SOUND_VU_METER_SINGLE,
    0xD7: UNILEDEffects.SOUND_LOVE_AND_PEACE,
    0xD8: UNILEDEffects.SOUND_CHRISTMAS,
    0xD9: UNILEDEffects.SOUND_HEARTBEAT,
    0xDA: UNILEDEffects.SOUND_PARTY,
}

BANLANX2_EFFECTS_RGBW: Final = dict(
    chain.from_iterable(
        d.items()
        for d in (
            {BANLANX2_EFFECT_WHITE: UNILEDEffects.SOLID_WHITE},
            BANLANX2_EFFECTS_RGB,
        )
    )
)

BANLANX2_EFFECTS_RGB_SOUND: Final = dict(
    chain.from_iterable(
        d.items()
        for d in (
            BANLANX2_EFFECTS_RGB,
            BANLANX2_EFFECTS_SOUND,
        )
    )
)

BANLANX2_EFFECTS_RGBW_SOUND: Final = dict(
    chain.from_iterable(
        d.items()
        for d in (
            BANLANX2_EFFECTS_RGBW,
            BANLANX2_EFFECTS_SOUND,
        )
    )
)

BANLANX2_COLORABLE_EFFECTS: Final = (
    BANLANX2_EFFECT_SOLID,
    0xCA,
    0xCC,
    0xCE,
    0xD0,
    0xD2,
    0xD4,
    0xD6,
)


class BanlanX2(UniledBleModel):
    """BanlanX v2 Protocol Implementation"""

    colors: int
    intmic: bool

    def __init__(
        self, id: int, name: str, info: str, data: bytes, colors: int, intmic: bool
    ):
        super().__init__(
            model_num=id,
            model_name=name,
            description=info,
            manufacturer=BANLANX_MANUFACTURER,
            channels=1,
            ble_manufacturer_id=[BANLANX_MANUFACTURER_ID, 5053],
            ble_manufacturer_data=data,
            ble_service_uuids=[BANLANX_UUID_FORMAT.format(part) for part in ["ffe0"]],
            ble_write_uuids=[BANLANX_UUID_FORMAT.format(part) for part in ["ffe1"]],
            ble_read_uuids=[],
            ble_notify_uuids=[],
        )
        self.colors = colors
        self.intmic = intmic

    def parse_notifications(
        self,
        device: UniledBleDevice,
        sender: int,
        data: bytearray,
    ) -> bool:
        """Parse notification message(s)"""
        _STATUS_FLAG_1 = 0x53
        _STATUS_FLAG_2 = 0x43
        _HEADER_LENGTH = 5
        _PACKET_NUMBER = 2
        _MESSAGE_LENGTH = 3
        _PAYLOAD_LENGTH = 4

        if (
            (len(data) > _HEADER_LENGTH)
            and data[0] == _STATUS_FLAG_1
            and data[1] == _STATUS_FLAG_2
        ):
            packet_number = data[_PACKET_NUMBER]
            message_length = data[_MESSAGE_LENGTH]
            payload_length = data[_PAYLOAD_LENGTH]

            if packet_number == 1:
                data = device.save_notification_data(data)
                if message_length > payload_length:
                    return None
                data = data[_HEADER_LENGTH:]
            else:
                if (
                    len((last := device.last_notification_data)) == 0
                    or last[_PACKET_NUMBER] != packet_number - 1
                ):
                    raise ParseNotificationError("Skip out of sequence Packet!")

                payload_so_far = last[_PAYLOAD_LENGTH] + data[_PAYLOAD_LENGTH]

                if payload_so_far < last[_MESSAGE_LENGTH]:
                    last[_PACKET_NUMBER] = packet_number
                    last[_PAYLOAD_LENGTH] = payload_so_far
                    device.save_notification_data(last + data[_HEADER_LENGTH:])
                    return False

                if (
                    payload_so_far > message_length
                    or message_length != last[_MESSAGE_LENGTH]
                ):
                    raise ParseNotificationError("Bad Packet!")

                data = last[_HEADER_LENGTH:] + data[_HEADER_LENGTH:]

            if len(data) != message_length:
                raise ParseNotificationError("Unknown/Invalid Packet!")

        #
        # 01 00 be 08 ff 05 4a ff 00 00 00 10 09 04 0b 14 1a 32 37 50 53 73 00 40 40
        # 01 00 05 02 32 01 17 ff ff ff 00 10 09 04 0b 14 1a 32 37 50 53 73 00 ff ff
        # 00 00 5e 02 38 06 48 ff 00 00 00 10 09 04 0b 14 1a 32 37 50 53 73 00 -> more can follow
        # 01 00 be 02 ff 0a 48 00 00 ff 00 10 09 04 0b 14 1a 32 37 50 53 73 00 - SP611E
        # 00 00 c9 12 0c 0a 4a 00 00 ff 00 10 09 04 0b 14 1a 32 37 50 53 73 00 1a 1a
        # 01 00 0e 02 61 0a 1e ff 00 00 01 10 09 04 0b 14 1a 32 37 50 53 73 00 - SP621E

        # ---------------------------------------------------------------------------------------
        # 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 -> more can follow
        #
        # 0  = Power: (0x00=Off, 0x01=On)
        # 1  = Loop Effects??
        # 2  = Effect
        # 3  = RGB Ordering
        # 4  = Brightness (0x00 - 0xFF)
        # 5  = Speed (0x01 - 0x0A)
        # 6  = Effect Length (0x01 - 0x96)
        # 7  = Red Level (0x00 - 0xFF)
        # 8  = Green Level (0x00 - 0xFF)
        # 9  = Blue Level (0x00 - 0xFF)
        # 10 = Input (0x00=Internal Mic, 0x01=Player, 0x02=External Mic)
        # 11 = Sesnsitivity (0x01 - 0x10)
        # 12 = ?? - 0x09 - Bytes to follow??
        # 13 = ?? - 0x04 - 4
        # 14 = ?? - 0x0b - 11 ( 0x08 on a SP611E?)
        # 15 = ?? - 0x14 - 20
        # 16 = ?? - 0x1a - 26
        # 17 = ?? - 0x32 - 50  - '2'
        # 18 = ?? - 0x37 - 55  - '7'
        # 19 = ?? - 0x50 - 80  - 'P'
        # 20 = ?? - 0x53 - 83  - 'S'
        # 21 = ?? - 0x73 - 115 - 's'
        # 22 = The number of timers set
        #
        # For each timer set, there are 7 bytes that follow
        #
        # 00 01 6a 00 93 a8 00 - On  @ 10:30 AM - Sun, Tue, Thu, Sat & Disabled
        # 00 01 6a 00 93 a8 01 - On  @ 10:30 AM - Sun, Tue, Thu, Sat & Enabled
        # 01 00 15 01 3c 68 01 - Off @ 10:30 PM - Mon, Wed, Fri & Enabled
        #
        # 00 01 7f 00 93 a8 01 - On  @ 10:30 AM - Everyday & Enabled
        # 01 00 7f 00 93 e4 01 - Off @ 10:31 AM - Everyday & Enabled
        # 02 01 80 00 94 20 01 - On  @ 10:32 AM - Once & Enabled
        #
        # SP617E Only - Last two bytes in message are cool and warm white levels.
        #
        # xx = Cool White Level
        # xx = Warm White Level (Not used on SP617E)
        #
        _LOGGER.debug("%s: Good Status Message: %s", device.name, data.hex())

        if not device.master.features:
            features = [
                LightStripFeature(extra=UNILED_CONTROL_ATTRIBUTES),
                EffectTypeFeature(),
                EffectSpeedFeature(BANLANX2_MAX_EFFECT_SPEED),
                EffectLengthFeature(BANLANX2_MAX_EFFECT_LENGTH),
                ChipOrderFeature(),
            ]

            if self.intmic:
                features.append(LightModeFeature()),
                features.append(AudioInputFeature())
                features.append(AudioSensitivityFeature(BANLANX2_MAX_SENSITIVITY))
            else:
                features.append(EffectLoopFeature())
            device.master.features = features

        mode = data[1]
        effect = data[2]
        chip_order = data[3]
        level = data[4]
        speed = data[5]
        length = data[6]
        rgb = (data[7], data[8], data[9])
        gain = data[11]
        input = data[10]
        cold = data[message_length - 2]
        # warm = data[message_length - 1]

        device.master.status.replace(
            {
                ATTR_UL_DEVICE_FORCE_REFRESH: True,
                ATTR_UL_POWER: data[0] == 1,
                ATTR_HA_SUPPORTED_COLOR_MODES: [COLOR_MODE_BRIGHTNESS],
                ATTR_HA_COLOR_MODE: COLOR_MODE_BRIGHTNESS,
                ATTR_UL_CHIP_ORDER: self.chip_order_name(
                    UNILED_CHIP_ORDER_RGBW
                    if self.colors == 4
                    else UNILED_CHIP_ORDER_RGB,
                    chip_order,
                ),
                ATTR_UL_LIGHT_MODE_NUMBER: mode,
                ATTR_UL_LIGHT_MODE: self.str_if_key_in(
                    mode, BANLANX2_LIGHT_MODES, UNILED_UNKNOWN
                ),
                ATTR_UL_EFFECT_NUMBER: 0,
                ATTR_HA_EFFECT: UNILED_UNKNOWN,
                ATTR_UL_EFFECT_TYPE: UNILED_UNKNOWN,
                ATTR_UL_EFFECT_LOOP: True if mode != 0 else False,
                ATTR_HA_BRIGHTNESS: level,
                ATTR_HA_RGB_COLOR: rgb,
            }
        )

        if mode == BANLANX2_LIGHT_MODE_SINGULAR:
            device.master.set(ATTR_UL_EFFECT_NUMBER, effect)
            device.master.set(
                ATTR_HA_EFFECT,
                self.str_if_key_in(effect, BANLANX2_EFFECTS_RGBW_SOUND, UNILED_UNKNOWN),
            )
            if self.colors == 4:
                device.master.set(ATTR_HA_WHITE, cold)
                device.master.set(
                    ATTR_HA_SUPPORTED_COLOR_MODES, [COLOR_MODE_RGB, COLOR_MODE_WHITE]
                )
            else:
                device.master.set(ATTR_HA_SUPPORTED_COLOR_MODES, [COLOR_MODE_RGB])

            if effect in BANLANX2_EFFECTS_SOUND:
                device.master.set(ATTR_UL_EFFECT_TYPE, UNILED_EFFECT_TYPE_SOUND)
                device.master.set(ATTR_UL_SENSITIVITY, gain)
                device.master.set(
                    ATTR_UL_AUDIO_INPUT,
                    self.str_if_key_in(input, BANLANX2_AUDIO_INPUTS, UNILED_UNKNOWN),
                )
                device.master.set(ATTR_HA_SUPPORTED_COLOR_MODES, [COLOR_MODE_ONOFF])
                device.master.set(ATTR_HA_COLOR_MODE, COLOR_MODE_ONOFF)
                device.master.set(ATTR_UL_COLOR_LEVEL, level)
                device.master.set(ATTR_HA_BRIGHTNESS, None)
            elif effect == BANLANX2_EFFECT_SOLID or effect == BANLANX2_EFFECT_WHITE:
                device.master.set(ATTR_UL_EFFECT_TYPE, UNILED_EFFECT_TYPE_STATIC)
                if effect == BANLANX2_EFFECT_WHITE:
                    device.master.set(
                        ATTR_HA_SUPPORTED_COLOR_MODES,
                        [COLOR_MODE_RGB, COLOR_MODE_WHITE],
                    )
                    device.master.set(ATTR_HA_COLOR_MODE, COLOR_MODE_WHITE)
                    device.master.set(ATTR_HA_BRIGHTNESS, cold)
                    device.master.set(ATTR_UL_COLOR_LEVEL, level)
                    return True
            else:
                device.master.set(ATTR_UL_EFFECT_SPEED, speed)
                device.master.set(ATTR_UL_EFFECT_LENGTH, length)
                device.master.set(ATTR_UL_EFFECT_TYPE, UNILED_EFFECT_TYPE_DYNAMIC)

            if effect in BANLANX2_COLORABLE_EFFECTS:
                device.master.set(ATTR_HA_COLOR_MODE, COLOR_MODE_RGB)

        elif mode == BANLANX2_LIGHT_MODE_AUTO_DYNAMIC:
            device.master.set(ATTR_UL_EFFECT_SPEED, speed)
            device.master.set(ATTR_UL_EFFECT_LENGTH, length)
            device.master.set(ATTR_UL_EFFECT_TYPE, UNILED_EFFECT_TYPE_DYNAMIC)
        elif mode == BANLANX2_LIGHT_MODE_AUTO_SOUND:
            device.master.set(ATTR_HA_SUPPORTED_COLOR_MODES, [COLOR_MODE_ONOFF])
            device.master.set(ATTR_HA_COLOR_MODE, COLOR_MODE_ONOFF)
            device.master.set(ATTR_UL_COLOR_LEVEL, level)
            device.master.set(ATTR_HA_BRIGHTNESS, None)
            device.master.set(ATTR_UL_SENSITIVITY, gain)
            device.master.set(ATTR_UL_EFFECT_TYPE, UNILED_EFFECT_TYPE_SOUND)
        return True

    def build_on_connect(self, device: UniledBleDevice) -> list[bytearray] | None:
        """Build on connect message(s)"""
        return None

    def build_state_query(self, device: UniledBleDevice) -> bytearray:
        """Build a state query message"""
        return bytearray([0xA0, 0x70, 0x00])

    def build_light_mode_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str
    ) -> list[bytearray] | None:
        """The bytes to send for a light mode change."""
        if isinstance(value, str):
            mode = self.int_if_str_in(
                value, BANLANX2_LIGHT_MODES, BANLANX2_LIGHT_MODE_SINGULAR
            )
        elif (mode := int(value)) not in BANLANX2_LIGHT_MODES:
            return None
        return bytearray([0xA0, 0x6A, 0x01, mode])

    def fetch_light_mode_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light modes"""
        return list(BANLANX2_LIGHT_MODES.values())

    def build_onoff_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray:
        """Build power on/off state message(s)"""
        return bytearray([0xA0, 0x62, 0x01, 0x01 if state else 0x00])

    def build_white_command(
        self, device: UniledBleDevice, channel: UniledChannel, level: int
    ) -> bytearray | None:
        """The bytes to send for a white level change."""
        if channel.status.effect_number != BANLANX2_EFFECT_WHITE:
            return self.build_effect_command(device, channel, BANLANX2_EFFECT_WHITE)
        return None

    def build_brightness_command(
        self, device: UniledBleDevice, channel: UniledChannel, level: int
    ) -> bytearray:
        """The bytes to send for a brightness level change"""
        if channel.status.effect_number == BANLANX2_EFFECT_WHITE:
            return bytearray([0xA0, 0x76, 0x02, level & 0xFF, 0x00])
        return bytearray([0xA0, 0x66, 0x01, level & 0xFF])

    def build_rgb_color_command(
        self, device: UniledBleDevice, channel: UniledChannel, rgb: tuple[int, int, int]
    ) -> bytearray | None:
        """The bytes to send for an RGB color change"""
        channel.set(ATTR_HA_RGB_COLOR, rgb)
        commands = []

        if channel.status.effect_number not in BANLANX2_COLORABLE_EFFECTS:
            commands.append(
                self.build_effect_command(device, channel, BANLANX2_EFFECT_SOLID)
            )

        red, green, blue = rgb
        level = channel.get(ATTR_UL_COLOR_LEVEL, channel.get(ATTR_HA_BRIGHTNESS, 0xFF))
        commands.append(bytearray([0xA0, 0x69, 0x04, red, green, blue, level]))
        return commands

    def build_rgbw_color_command(
        self,
        device: UniledBleDevice,
        channel: UniledChannel,
        rgbw: tuple[int, int, int, int],
    ) -> list[bytearray]:
        """The bytes to send for an RGBW color change"""
        red, green, blue, white = rgbw
        return [
            self.build_rgb_command(device, channel, (red, green, blue)),
            bytearray([0xA0, 0x76, 0x02, white & 0xFF, 0x00])
        ]

    def build_effect_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str | int
    ) -> bytearray:
        """The bytes to send for an effect change"""
        if isinstance(value, str):
            effect = self.int_if_str_in(
                value, BANLANX2_EFFECTS_RGBW_SOUND, BANLANX2_EFFECT_SOLID
            )
        elif (effect := int(value)) not in BANLANX2_EFFECTS_RGBW_SOUND:
            return None
        if effect == BANLANX2_EFFECT_WHITE:
            channel.set(ATTR_HA_COLOR_MODE, COLOR_MODE_WHITE)
            channel.set(ATTR_HA_BRIGHTNESS, channel.get(ATTR_HA_WHITE, 0xFF))
        elif effect == BANLANX2_EFFECT_SOLID:
            channel.set(ATTR_HA_COLOR_MODE, COLOR_MODE_RGB)
        return bytearray([0xA0, 0x63, 0x01, effect])

    def fetch_effect_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list:
        """Return list of effect names"""
        if not self.intmic:
            if self.colors == 4:
                return list(BANLANX2_EFFECTS_RGBW.values())
            else:
                return list(BANLANX2_EFFECTS_RGB.values())
        if self.colors == 4:
            return list(BANLANX2_EFFECTS_RGBW_SOUND.values())
        return list(BANLANX2_EFFECTS_RGB_SOUND.values())

    def build_effect_speed_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect speed change."""
        speed = int(value) & 0xFF
        if not 1 <= speed <= BANLANX2_MAX_EFFECT_SPEED:
            return None
        return bytearray([0xA0, 0x67, 0x01, speed])

    def build_effect_length_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect length change."""
        length = int(value) & 0xFF
        if not 1 <= length <= BANLANX2_MAX_EFFECT_LENGTH:
            return None
        return bytearray([0xA0, 0x68, 0x01, length])

    def build_effect_loop_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """The bytes to send for an effect loop change."""
        return self.build_light_mode_command(device, channel, 0x01 if state else 0x00)

    def build_sensitivity_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for a gain/sensitivity change"""
        gain = int(value) & 0xFF
        if not 1 <= gain <= BANLANX2_MAX_SENSITIVITY:
            return None
        return bytearray([0xA0, 0x6B, 0x01, gain])

    def build_audio_input_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str
    ) -> bytearray | None:
        """The bytes to send for an input change"""
        if (
            input := self.int_if_str_in(
                str(value), BANLANX2_AUDIO_INPUTS, channel.status.audio_input
            )
        ) is None:
            return None
        return bytearray([0xA0, 0x6C, 0x01, input])

    def fetch_audio_input_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light modes"""
        return list(BANLANX2_AUDIO_INPUTS.values())

    def build_chip_order_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str | None = None
    ) -> bytearray | None:
        """Build chip order message(s)"""
        sequence = UNILED_CHIP_ORDER_RGBW if self.colors == 4 else UNILED_CHIP_ORDER_RGB
        if (order := self.chip_order_index(sequence, str(value))) is not None:
            return bytearray([0xA0, 0x64, 0x01, order])
        return None

    def fetch_chip_order_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of chip orders"""
        if self.colors == 4:
            return self.chip_order_list(UNILED_CHIP_ORDER_RGBW)
        return self.chip_order_list(UNILED_CHIP_ORDER_RGB)


##
## Device Signatures
##
SP611E = BanlanX2(
    id=0x611E,
    name="SP611E",
    info="SPI RGB (Music) Controller",
    data=b"\x04\x10",
    colors=3,
    intmic=True,
)

SP617E = BanlanX2(
    id=0x617E,
    name="SP617E",
    info="SPI RGB(W) (Music) Controller",
    data=b"\x17\x10",
    colors=4,
    intmic=True,
)

SP620E = BanlanX2(
    id=0x620E,
    name="SP620E",
    info="USB SPI RGB (Music) Controller",
    data=b"\x1b\x10",
    colors=3,
    intmic=True,
)

SP621E = BanlanX2(
    id=0x621E,
    name="SP621E",
    info="Mini SPI RGB Controller",
    data=b"\x0d\x00",
    colors=3,
    intmic=False,
)
