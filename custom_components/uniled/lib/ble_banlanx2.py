"""UniLED BLE Devices - SP LED (BanlanX)"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .artifacts import (
    UNILEDModelType,
    UNILEDInput,
    UNILEDEffectType,
    UNILEDEffects
)
from .states import UNILEDStatus
from .classes import UNILEDDevice, UNILEDChannel
from .ble_model import UNILEDBLEModel
from .ble_banlanx1 import (
    BANLANX1_MANUFACTURER_ID as BANLANX2_MANUFACTURER_ID,
    BANLANX1_MANUFACTURER as BANLANX2_MANUFACTURER,
    BANLANX1_UUID_FORMAT as BANLANX2_UUID_FORMAT,
)

import logging

_LOGGER = logging.getLogger(__name__)

BANLANX2_TYPE_SOLID: Final = 0xBE
BANLANX2_TYPE_SOUND: Final = 0xC9

BANLANX2_INPUTS: Final = {
    0x00: UNILEDInput.INTMIC,
    0x01: UNILEDInput.PLAYER,
    0x02: UNILEDInput.EXTMIC,
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


@dataclass(frozen=True)
class _BANLANX2(UNILEDBLEModel):
    """BanlanX v2 Protocol Implementation"""

    ##
    ## Device Control
    ##
    def construct_connect_message(self) -> bytearray | None:
        """The bytes to send when first connecting."""
        return self.construct_message(
            bytearray([0xA0, 0x60, 0x07, 0x92, 0x9F, 0x00, 0x62, 0xA5, 0x04, 0x00])
        )

    def construct_status_query(self, device: UNILEDDevice) -> bytearray:
        """The bytes to send for a state query."""
        return self.construct_message(bytearray([0xA0, 0x70, 0x00]))

    async def async_decode_notifications(
        self, device: UNILEDDevice, sender: int, data: bytearray
    ) -> UNILEDStatus | None:
        """Handle notification responses."""

        if data[0] == 0x53 and data[1] == 0x43:
            #
            # Status Response #1 (SP617E)
            #
            # 53 43 01 19 0f 00 00 03 02 ff 01 0e 00 00 ff 00 10 09 04 0b

            #
            # Status Response #1 (SP611E)
            #
            # 53 43 01 1e 0f 00 00 be 02 45 09 96 ff 00 00 00 10 09 04 0b # Solid Color (0xbe)
            # 53 43 01 17 0f 00 00 04 02 45 07 96 ff 00 00 00 10 09 04 0b
            # 53 43 01 17 0f 01 00 05 02 ff 07 96 40 ff 00 00 10 09 04 0b
            # 53 43 01 17 0f 01 00 c9 02 ff 0a 96 00 00 ff 00 10 09 04 0b # First Music FX (0xc9) Internal Mic
            # 53 43 01 17 0f 01 00 be 02 ff 0a 96 ff ff ff 00 10 09 04 0b # White Mode
            # 53 43 01 17 0f 01 00 be 02 03 0a 96 ff ff ff 00 10 09 04 0b # White, Brightness Lowered
            # 53 43 01 17 0f 01 00 be 02 03 0a 96 ff 00 00 00 10 09 04 0b # Red, Brightness Lowered
            # 53 43 01 17 0f 01 00 be 02 03 0a 96 40 ff ff 00 10 09 04 0b
            # 53 43 01 17 0f 01 00 be 02 38 0a 10 ff ff ff 00 06 09 04 0b
            # 53 43 01 19 0f 00 00 c9 02 ff 0a 96 ff ff ff 02 10 09 04 0b # SP617E - External Mic
            # 53 43 01 19 0f 01 00 c9 02 ff 0a 96 ff ff ff 01 10 09 04 0b # Player
            # -----------------------------------------------------------
            # 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19
            # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
            # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Unknown
            # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Unknown
            # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Unknown
            # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Sesnsitivity (0x00 - 0x0F)
            # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Input 0x00 = Internal Mic, 0x01 = Player, 0x02 = External Mic
            # |  |  |  |  |  |  |  |  |  |  |  |  |  |  Blue Level (0x00 - 0xFF)
            # |  |  |  |  |  |  |  |  |  |  |  |  |  Green Level (0x00 - 0xFF)
            # |  |  |  |  |  |  |  |  |  |  |  |  Red Level (0x00 - 0xFF)
            # |  |  |  |  |  |  |  |  |  |  |  Effect Length (0x00 - 0x96)
            # |  |  |  |  |  |  |  |  |  |  Speed (0x00 - 0x0A)
            # |  |  |  |  |  |  |  |  |  Brightness (0x00 - 0xFF)
            # |  |  |  |  |  |  |  |  Unknown
            # |  |  |  |  |  |  |  Effect/Mode
            # |  |  |  |  |  |  Unknown
            # |  |  |  |  |  Power: 0x00=Off, 0x01=On
            # |  |  |  |  Unknown
            # |  |  |  Unknown
            # |  |  Response Type, always 0x01
            # |  Header Byte 2, always 0x43
            # Header Byte 1, always 0x53
            #
            if data[2] == 0x01:
                return UNILEDStatus(
                    power=data[5] == 0x01,
                    fxtype=data[7],
                    effect=data[7],
                    speed=data[10],
                    length=data[11],
                    white=None,
                    level=data[9],
                    rgb=(data[12], data[13], data[14]),
                    gain=data[16],
                    input=data[15]
                )

            # Status Response #2
            #
            # 53 43 02 19 0a 14 1a 32 37 50 53 73 00 ff ff
            # 53 43 02 1e 0f 14 1a 32 37 50 53 73 01 00 01 4d 00 7b 0c 01
            # 53 43 02 17 08 14 1a 32 37 50 53 73 00
            #
            # elif data[2] == 0x02:

            # Status Response #3
            #
            #
            #
            # elif data[2] == 0x03:

        # Getting here means a notification has not changed the state
        # so return None to indicate no changes to the frontend and
        # save unneeded updates.
        #
        return None

    def construct_gain_change(
        self, device: UNILEDDevice, gain: int
    ) -> bytearray | None:
        """The bytes to send for a gain/sensitivity change"""
        return self.construct_message(bytearray([0xA0, 0x6B, 0x01, gain]))

    def construct_input_change(
        self, device: UNILEDDevice, audio_input: int
    ) -> bytearray | None:
        """The bytes to send for an input change"""
        return None

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

    def construct_white_change(
        self, channel: UNILEDChannel, level: int
    ) -> bytearray | None:
        """The bytes to send for a white level change"""
        return None

    def construct_level_change(
        self, channel: UNILEDChannel, level: int
    ) -> bytearray | None:
        """The bytes to send for a color level change"""
        return self.construct_message(bytearray([0xA0, 0x66, 0x01, level]))

    def construct_color_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int, white: int | None
    ) -> bytearray | None:
        """The bytes to send for a level change"""
        if channel.status.effect < BANLANX2_TYPE_SOLID:
            return None

        if self.model_num != 0x6117E:
            white = 0xFF
        elif white is None:
            white = channel.status.white

        return self.construct_message(
            bytearray([0xA0, 0x69, 0x04, red, green, blue, white])
        )

    ##
    ## Device Informational
    ##
    def nameof_device_input_type(
        self, device: UNILEDDevice, audio_input: int | None = None
    ) -> str | None:
        """Name a device input type."""
        if audio_input is None:
            audio_input = device.input
        if audio_input in BANLANX2_INPUTS:
            return BANLANX2_INPUTS[audio_input]
        return None

    def listof_device_inputs(self, device: UNILEDDevice) -> list | None:
        """List of available device inputs."""
        return list(BANLANX2_INPUTS.values())

    def rangeof_device_input_gain(
        self, device: UNILEDDevice
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return (1, 16, 1)

    ##
    ## Channel Informational
    ##
    def listof_channel_effects(self, channel: UNILEDChannel) -> list | None:
        """List of available channel effects"""
        return list(BANLANX2_EFFECTS.values())

    def nameof_channel_effect(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> str | None:
        """Name an effect."""
        if effect is None:
            effect = channel.status.effect
        if effect in BANLANX2_EFFECTS:
            return BANLANX2_EFFECTS[effect]
        return None

    def nameof_channel_effect_type(
        self, channel: UNILEDChannel, fxtype: int | None = None
    ) -> str | None:
        """Name an effects type."""
        if fxtype is None:
            fxtype = channel.status.fxtype
        if fxtype == BANLANX2_TYPE_SOLID:
            return UNILEDEffectType.STATIC
        if fxtype >= BANLANX2_TYPE_SOUND:
            return UNILEDEffectType.SOUND
        return UNILEDEffectType.PATTERN

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
## SP611E
##
SP611E = _BANLANX2(
    model_num=0x611E,
    model_name="SP611E",
    model_type=UNILEDModelType.STRIP,
    description="BLE Controller (Music) RGB",
    manufacturer=BANLANX2_MANUFACTURER,
    manufacturer_id=BANLANX2_MANUFACTURER_ID,
    manufacturer_data=b"\x04\x10\xff\x10",
    resolve_protocol=False,
    channels=1,
    needs_on=True,
    # service_uuid=BASE_UUID_FORMAT.format("ffe0"),
    service_uuids=["5833ff01-9b8b-5191-6142-22a4536ef123"],
    write_uuids=[BANLANX2_UUID_FORMAT.format(part) for part in ["ffe1"]],
    read_uuids=[],
)

##
## SP617E
##
SP617E = _BANLANX2(
    model_num=0x617E,
    model_name="SP617E",
    model_type=UNILEDModelType.STRIP,
    description="BLE Controller (Music) RGB&W",
    manufacturer=BANLANX2_MANUFACTURER,
    manufacturer_id=BANLANX2_MANUFACTURER_ID,
    manufacturer_data=b"\x17\x10!\x06",
    resolve_protocol=False,
    channels=1,
    needs_on=True,
    service_uuids=[BANLANX2_UUID_FORMAT.format(part) for part in ["e0ff", "ffe0"]],
    write_uuids=[BANLANX2_UUID_FORMAT.format(part) for part in ["e0ff", "ffe1"]],
    read_uuids=[],
)
