"""UniLED BLE Devices - SP LED (BanlanX v2)"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final
from enum import IntEnum

from .artifacts import (
    UNKNOWN,
    UNILED_CHIP_ORDER_3COLOR,
    UNILED_CHIP_ORDER_4COLOR,
    UNILEDModelType,
    UNILEDInput,
    UNILEDEffectType,
    UNILEDEffects,
)
from .states import UNILEDStatus
from .classes import UNILEDDevice, UNILEDChannel
from .ble_model import UNILEDBLEModel, BASE_UUID_FORMAT as BANLANX2_UUID_FORMAT

import logging

_LOGGER = logging.getLogger(__name__)

BANLANX2_MODEL_NUMBER_SP611E: Final = 0x611E
BANLANX2_MODEL_NAME_SP611E: Final = "SP611E"
BANLANX2_LOCAL_NAME_SP611E: Final = BANLANX2_MODEL_NAME_SP611E

BANLANX2_MODEL_NUMBER_SP617E: Final = 0x617E
BANLANX2_MODEL_NAME_SP617E: Final = "SP617E"
BANLANX2_LOCAL_NAME_SP617E: Final = BANLANX2_MODEL_NAME_SP617E

BANLANX2_MANUFACTURER: Final = "SPLED (BanlanX)"
BANLANX2_MANUFACTURER_ID: Final = 20563
BANLANX2_UUID_SERVICE = [BANLANX2_UUID_FORMAT.format(part) for part in ["e0ff", "ffe0"]]
BANLANX2_UUID_WRITE = [BANLANX2_UUID_FORMAT.format(part) for part in ["ffe1"]]
BANLANX2_UUID_READ = []

BANLANX2_TYPE_SOLID: Final = 0xBE
BANLANX2_TYPE_SOUND: Final = 0xC9

BANLANX2_INPUTS: Final = {
    0x00: UNILEDInput.INTMIC,
    0x01: UNILEDInput.PLAYER,
    0x02: UNILEDInput.EXTMIC,
}


@dataclass(frozen=True)
class _FXType(IntEnum):
    STATIC = 0x00
    PATTERN = 0x01
    SOUND = 0x02


BANLANX2_EFFECT_TYPES: dict(int, str) = {
    _FXType.STATIC.value: UNILEDEffectType.STATIC,
    _FXType.PATTERN.value: UNILEDEffectType.PATTERN,
    _FXType.SOUND.value: UNILEDEffectType.SOUND,
}

BANLANX2_EFFECTS: Final = {
    0xBE: UNILEDEffects.SOLID,
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
    0x63: UNILEDEffects.BREATH_PRUPLE,
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
    0x87: UNILEDEffects.SEGMENT_SPIN,
    0x88: UNILEDEffects.SEGMENT_SPIN_RED,
    0x89: UNILEDEffects.SEGMENT_SPIN_GREEN,
    0x8A: UNILEDEffects.SEGMENT_SPIN_BLUE,
    0x8B: UNILEDEffects.SEGMENT_SPIN_YELLOW,
    0x8C: UNILEDEffects.SEGMENT_SPIN_CYAN,
    0x8D: UNILEDEffects.SEGMENT_SPIN_PURPLE,
    0x8E: UNILEDEffects.SEGMENT_SPIN_WHITE,
    0x8F: UNILEDEffects.GRADIENT,
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

_STATUS_FLAG_1 = 0x53
_STATUS_FLAG_2 = 0x43
_HEADER_LENGTH = 5
_PACKET_NUMBER = 2
_MESSAGE_LENGTH = 3
_PAYLOAD_LENGTH = 4


@dataclass(frozen=True)
class _BANLANX2(UNILEDBLEModel):
    """BanlanX v2 Protocol Implementation"""

    ##
    ## Device State
    ##
    def construct_connect_message(self, device: UNILEDDevice) -> list[bytearray]:
        """The bytes to send when first connecting."""
        # return [
        #    self.construct_message(bytearray([0xA0, 0x64, 0x01, 0x11])),
        #    self.construct_message(bytearray([0xA0, 0x64, 0x01, 0x11])),
        # ]
        return None

    def construct_status_query(self, device: UNILEDDevice) -> bytearray:
        """The bytes to send for a state query."""
        return self.construct_message(bytearray([0xA0, 0x70, 0x00]))

    def async_decode_notifications(
        self, device: UNILEDDevice, sender: int, data: bytearray
    ) -> UNILEDStatus | None:
        """Handle notification responses."""

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
                    _LOGGER.debug(
                        "%s: Packet 1 - payload size: %s, message length: %s",
                        device.name,
                        payload_length,
                        message_length,
                    )
                    return None
                data = data[_HEADER_LENGTH:]
            else:

                if (
                    len((last := device.last_notification_data)) == 0
                    or last[_PACKET_NUMBER] != packet_number - 1
                ):
                    _LOGGER.debug("%s: Skip out of sequence Packet!", device.name)
                    device.save_notification_data(())
                    return None

                payload_so_far = last[_PAYLOAD_LENGTH] + data[_PAYLOAD_LENGTH]

                _LOGGER.debug(
                    "%s: Packet %s - payload size: %s, payload so far: %s, message length: %s (%s)",
                    device.name,
                    packet_number,
                    payload_length,
                    payload_so_far,
                    message_length,
                    last[_MESSAGE_LENGTH],
                )

                if payload_so_far < last[_MESSAGE_LENGTH]:
                    last[_PACKET_NUMBER] = packet_number
                    last[_PAYLOAD_LENGTH] = payload_so_far
                    device.save_notification_data(last + data[_HEADER_LENGTH:])
                    return None

                if (
                    payload_so_far > message_length
                    or message_length != last[_MESSAGE_LENGTH]
                ):
                    _LOGGER.debug("%s: Bad Packet!", device.name)
                    last[_MESSAGE_LENGTH] = 0
                    return None

                data = last[_HEADER_LENGTH:] + data[_HEADER_LENGTH:]

            if len(data) == message_length:
                #
                # 01 00 01 12 99 05 4a 00 00 ff 00 10 09 04 0b 14 1a 32 37 50 53 73 03 00 01 7f 00 93 a8 01 01 00 7f 00 93 e4 01 02 01 80 00 94 20 01 1a 1a
                # 00 00 01 12 99 05 4a 00 00 ff 00 10 09 04 0b 14 1a 32 37 50 53 73 01 00 01 6a 00 93 a8 00 1a 1a
                # 01 00 01 12 99 05 4a 00 00 ff 00 10 09 04 0b 14 1a 32 37 50 53 73 02 00 01 6a 00 93 a8 01 01 00 15 01 3c 68 01 1a 1a
                # 01 00 d9 12 99 05 4a 00 00 ff 00 10 09 04 0b 14 1a 32 37 50 53 73 02 00 01 6a 00 93 a8 01 01 00 15 01 3c 68 01 1a 1a
                # 01 00 d9 12 99 05 4a 00 00 ff 00 10 09 04 0b 14 1a 32 37 50 53 73 02 00 01 6a 00 93 a8 01 01 00 15 01 3c 68 01 1a 1a
                # 00 00 c9 12 0f 05 4a ff ff ff 00 10 09 04 0b 14 1a 32 37 50 53 73 02 00 01 6a 00 93 a8 01 01 00 15 01 3c 68 01 ff ff
                # 01 66 53 22 0f 05 4a 00 00 ff 00 10 09 04 0b 14 1a 32 37 50 53 73 01 00 00 00 00 00 00 00                      40 40
                # 01 00 be 08 ff 05 4a ff 00 00 00 10 09 04 0b 14 1a 32 37 50 53 73 00 40 40
                # 01 00 05 02 32 01 17 ff ff ff 00 10 09 04 0b 14 1a 32 37 50 53 73 00 ff ff
                # 00 00 5e 02 38 06 48 ff 00 00 00 10 09 04 0b 14 1a 32 37 50 53 73 00 -> more can follow
                # 01 00 be 02 ff 0a 48 00 00 ff 00 10 09 04 0b 14 1a 32 37 50 53 73 00 - SP611E
                # 00 00 c9 12 0c 0a 4a 00 00 ff 00 10 09 04 0b 14 1a 32 37 50 53 73 00 1a 1a
                # ---------------------------------------------------------------------------------------
                # 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 -> more can follow
                #
                # 0  = Power: (0x00=Off, 0x01=On)
                # 1  = ??
                # 2  = Effect/Mode
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

                white = None
                if self.model_num == BANLANX2_MODEL_NUMBER_SP617E:
                    cool = data[message_length - 2]
                    _warm = data[message_length - 1]
                    white = cool

                return UNILEDStatus(
                    power=data[0] == 0x01,
                    level=data[4],
                    white=white,
                    rgb=(data[7], data[8], data[9]),
                    fxtype=self.codeof_channel_effect_type(device.master, data[2]),
                    effect=data[2],
                    speed=data[5],
                    length=data[6],
                    input=data[10],
                    gain=data[11],
                    chip_order=data[3],
                )

        _LOGGER.debug("%s: Unknown/Invalid Packet!", device.name)
        device.save_notification_data(())
        return None

    ##
    ## Channel Configuration
    ##
    def construct_input_change(
        self, channel: UNILEDChannel, input_type: int
    ) -> bytearray | None:
        """The bytes to send for an input change"""
        return self.construct_message(bytearray([0xA0, 0x6C, 0x01, input_type]))

    def construct_input_gain_change(
        self, channel: UNILEDChannel, gain: int
    ) -> list[bytearray] | None:
        """The bytes to send for a gain/sensitivity change"""
        return self.construct_message(bytearray([0xA0, 0x6B, 0x01, gain]))

    def construct_chip_order_change(
        self, channel: UNILEDChannel, chip_order: str
    ) -> list[bytearray] | None:
        """The bytes to send for a chip order change"""
        return self.construct_message(bytearray([0xA0, 0x64, 0x01, chip_order]))

    ##
    ## Channel Control
    ##
    def construct_power_change(
        self, channel: UNILEDChannel, turn_on: int
    ) -> bytearray | None:
        """The bytes to send for a state change"""
        return self.construct_message(
            bytearray([0xA0, 0x62, 0x01, 0x01 if turn_on else 0x00])
        )

    def construct_level_change(
        self, channel: UNILEDChannel, level: int
    ) -> bytearray | None:
        """The bytes to send for a brightness level change"""
        return self.construct_message(bytearray([0xA0, 0x66, 0x01, level]))

    def construct_white_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a white level change."""
        # Two level bytes are sent, assuming first is cool white, second is warm, although not supported by SP6117E?
        cool = level
        warm = 0x00
        return self.construct_message(bytearray([0xA0, 0x76, 0x02, cool, warm]))

    def construct_color_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int, white: int | None
    ) -> bytearray | None:
        """The bytes to send for a color level change"""
        commands = []

        if channel.status.effect < BANLANX2_TYPE_SOLID:
            commands.append(self.construct_effect_change(channel, BANLANX2_TYPE_SOLID))
            channel.set_status(
                replace(
                    channel.status,
                    effect=BANLANX2_TYPE_SOLID,
                    fxtype=_FXType.STATIC.value,
                )
            )

        level = channel.status.level

        commands.append(
            self.construct_message(
                bytearray([0xA0, 0x69, 0x04, red, green, blue, level])
            )
        )

        if self.model_num == BANLANX2_MODEL_NUMBER_SP617E and white is not None:
            commands.append(self.construct_white_change(channel, white))

        return commands

    def construct_effect_change(
        self, channel: UNILEDChannel, effect: int
    ) -> bytearray | None:
        """The bytes to send for an effect change"""
        return self.construct_message(bytearray([0xA0, 0x63, 0x01, effect]))

    def construct_effect_speed_change(
        self, channel: UNILEDChannel, speed: int
    ) -> bytearray | None:
        """The bytes to send for an effect speed change"""
        return self.construct_message(bytearray([0xA0, 0x67, 0x01, speed]))

    def construct_effect_length_change(
        self, channel: UNILEDChannel, length: int
    ) -> bytearray | None:
        """The bytes to send for an efect length change"""
        return self.construct_message(bytearray([0xA0, 0x68, 0x01, length]))

    ##
    ## Channel Informational
    ##
    def listof_channel_effects(self, channel: UNILEDChannel) -> list | None:
        """List of available channel effects"""
        return list(BANLANX2_EFFECTS.values())

    def codeof_channel_effect(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named channel effect"""
        if name is None:
            return channel.status.effect
        return [k for k in BANLANX2_EFFECTS.items() if k[1] == name][0][0]

    def nameof_channel_effect(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> str | None:
        """Name an effect."""
        if effect is None:
            effect = channel.status.effect
        if effect in BANLANX2_EFFECTS:
            return BANLANX2_EFFECTS[effect]
        return None

    def codeof_channel_effect_type(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> int | None:
        """Code of channel effect type from effect code"""
        if effect is None:
            effect = channel.status.effect
        if effect < BANLANX2_TYPE_SOLID:
            return _FXType.PATTERN.value
        elif effect >= BANLANX2_TYPE_SOUND:
            return _FXType.SOUND.value
        return _FXType.STATIC.value

    def nameof_channel_effect_type(
        self, channel: UNILEDChannel, fxtype: int | None = None
    ) -> str | None:
        """Name an effects type."""
        if fxtype is None:
            fxtype = channel.status.fxtype
        if fxtype in BANLANX2_EFFECT_TYPES:
            return BANLANX2_EFFECT_TYPES[fxtype]
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

    def nameof_channel_input_type(
        self, channel: UNILEDChannel, audio_input: int | None = None
    ) -> str | None:
        """Name a channel input type."""
        if audio_input is None:
            audio_input = channel.status.input
        if audio_input in BANLANX2_INPUTS:
            return BANLANX2_INPUTS[audio_input]
        return None

    def codeof_channel_input_type(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named input type"""
        if name is None:
            return None
        return [k for k in BANLANX2_INPUTS.items() if k[1] == name][0][0]

    def listof_channel_inputs(self, channel: UNILEDChannel) -> list | None:
        """List of available channel inputs."""
        return list(BANLANX2_INPUTS.values())

    def rangeof_channel_input_gain(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return (1, 16, 1)

    def codeof_channel_chip_order(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named chip order"""
        if name is None:
            return None
        if self.model_num == BANLANX2_MODEL_NUMBER_SP611E:
            return super().codeof_channel_chip_order(channel, name)
        return [k for k in UNILED_CHIP_ORDER_4COLOR.items() if k[1] == name][0][0]

    def nameof_channel_chip_order(
        self, channel: UNILEDChannel, order: int | None = None
    ) -> str | None:
        """Name a chip order."""
        if channel.status.chip_order is not None:
            if order is None:
                order = channel.status.chip_order
            if self.model_num == BANLANX2_MODEL_NUMBER_SP611E:
                return super().nameof_channel_chip_order(channel, order)
            if order in UNILED_CHIP_ORDER_4COLOR:
                return UNILED_CHIP_ORDER_4COLOR[order]
        return None

    def listof_channel_chip_orders(self, channel: UNILEDChannel) -> list | None:
        """List of available chip orders"""
        if channel.status.chip_order is not None:
            if self.model_num == BANLANX2_MODEL_NUMBER_SP611E:
                return list(UNILED_CHIP_ORDER_3COLOR.values())
            return list(UNILED_CHIP_ORDER_4COLOR.values())
        return None


##
## SP611E
##
SP611E = _BANLANX2(
    model_type=UNILEDModelType.STRIP,
    model_name=BANLANX2_MODEL_NAME_SP611E,
    model_num=BANLANX2_MODEL_NUMBER_SP611E,
    description="BLE Controller (Music) RGB",
    manufacturer=BANLANX2_MANUFACTURER,
    manufacturer_id=BANLANX2_MANUFACTURER_ID,
    manufacturer_data=b"\x04\x10",
    resolve_protocol=False,
    channels=1,
    needs_on=True,
    sends_status_on_commands=False,
    local_names=[BANLANX2_LOCAL_NAME_SP611E],
    service_uuids=BANLANX2_UUID_SERVICE,
    write_uuids=BANLANX2_UUID_WRITE,
    read_uuids=BANLANX2_UUID_READ,
)

##
## SP617E
##
SP617E = _BANLANX2(
    model_type=UNILEDModelType.STRIP,
    model_name=BANLANX2_MODEL_NAME_SP617E,
    model_num=BANLANX2_MODEL_NUMBER_SP617E,
    description="BLE Controller (Music) RGB&W",
    manufacturer=BANLANX2_MANUFACTURER,
    manufacturer_id=BANLANX2_MANUFACTURER_ID,
    manufacturer_data=b"\x17\x10",
    resolve_protocol=False,
    channels=1,
    needs_on=True,
    sends_status_on_commands=False,
    local_names=[BANLANX2_LOCAL_NAME_SP617E],
    service_uuids=BANLANX2_UUID_SERVICE,
    write_uuids=BANLANX2_UUID_WRITE,
    read_uuids=BANLANX2_UUID_READ,
)
