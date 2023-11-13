"""UniLED BLE Devices - SP LED (BanlanX v3)"""
from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import chain
from typing import Final
from enum import IntEnum

from .artifacts import (
    UNKNOWN,
    UNILED_CHIP_ORDER_3COLOR,
    UNILED_CHIP_ORDER_4COLOR,
    UNILEDMode,
    UNILEDModelType,
    UNILEDInput,
    UNILEDEffectType,
    UNILEDEffects,
)
from .states import UNILEDStatus
from .classes import UNILEDDevice, UNILEDChannel
from .ble_model import UNILEDBLEModel, BASE_UUID_FORMAT as BANLANX3_UUID_FORMAT

import logging

_LOGGER = logging.getLogger(__name__)

BANLANX3_MODEL_NUMBER_SP613E: Final = 0x613E
BANLANX3_MODEL_NAME_SP613E: Final = "SP613E"
BANLANX3_LOCAL_NAME_SP613E: Final = BANLANX3_MODEL_NAME_SP613E

BANLANX3_MODEL_NUMBER_SP614E: Final = 0x614E
BANLANX3_MODEL_NAME_SP614E: Final = "SP614E"
BANLANX3_LOCAL_NAME_SP614E: Final = BANLANX3_MODEL_NAME_SP614E

BANLANX3_MANUFACTURER: Final = "SPLED (BanlanX)"
BANLANX3_MANUFACTURER_ID: Final = 20563
BANLANX3_UUID_SERVICE = [BANLANX3_UUID_FORMAT.format(part) for part in ["e0ff", "ffe0"]]
BANLANX3_UUID_WRITE = [BANLANX3_UUID_FORMAT.format(part) for part in ["ffe1"]]
BANLANX3_UUID_READ = []

BANLANX3_EFFECT_PATTERN: Final = 0x01
BANLANX3_EFFECT_SOLID: Final = 0x63
BANLANX3_EFFECT_CUSTOM: Final = 0x64
BANLANX3_EFFECT_SOUND: Final = 0x65
BANLANX3_EFFECT_WHITE: Final = 0xCC

BANLANX3_INPUTS: Final = {
    0x00: UNILEDInput.INTMIC,
    0x01: UNILEDInput.PLAYER,
    0x02: UNILEDInput.EXTMIC,
}

@dataclass(frozen=True)
class _FXMode(IntEnum):
    OFF = 0x00
    AUTO = 0x01
    AUTO_SOUND = 0x02

BANLANX3_MODES: Final = {
    _FXMode.OFF.value: UNILEDMode.MANUAL,
    _FXMode.AUTO.value: UNILEDMode.AUTO,
    _FXMode.AUTO_SOUND.value: UNILEDMode.AUTO_SOUND,
}

@dataclass(frozen=True)
class _FXType(IntEnum):
    STATIC = 0x00
    PATTERN = 0x01
    SOUND = 0x02


BANLANX3_EFFECT_TYPES: dict(int, str) = {
    _FXType.STATIC.value: UNILEDEffectType.STATIC,
    _FXType.PATTERN.value: UNILEDEffectType.PATTERN,
    _FXType.SOUND.value: UNILEDEffectType.SOUND,
}

BANLANX3_EFFECTS_613: Final = {
    BANLANX3_EFFECT_SOLID: UNILEDEffects.SOLID_COLOR,
    BANLANX3_EFFECT_PATTERN + 0: UNILEDEffects.GRADIENT_SEVEN_COLOR,
    BANLANX3_EFFECT_PATTERN + 1: UNILEDEffects.JUMP_SEVEN_COLOR,
    BANLANX3_EFFECT_PATTERN + 2: UNILEDEffects.BREATH_SEVEN_COLOR,
    BANLANX3_EFFECT_PATTERN + 3: UNILEDEffects.STROBE_SEVEN_COLOR,
    BANLANX3_EFFECT_PATTERN + 4: UNILEDEffects.BREATH_RED,
    BANLANX3_EFFECT_PATTERN + 5: UNILEDEffects.BREATH_GREEN,
    BANLANX3_EFFECT_PATTERN + 6: UNILEDEffects.BREATH_BLUE,
    BANLANX3_EFFECT_PATTERN + 7: UNILEDEffects.BREATH_YELLOW,
    BANLANX3_EFFECT_PATTERN + 8: UNILEDEffects.BREATH_CYAN,
    BANLANX3_EFFECT_PATTERN + 9: UNILEDEffects.BREATH_PURPLE,
    BANLANX3_EFFECT_PATTERN + 10: UNILEDEffects.BREATH_WHITE,
    BANLANX3_EFFECT_PATTERN + 11: UNILEDEffects.STROBE_RED,
    BANLANX3_EFFECT_PATTERN + 12: UNILEDEffects.STROBE_GREEN,
    BANLANX3_EFFECT_PATTERN + 13: UNILEDEffects.STROBE_BLUE,
    BANLANX3_EFFECT_PATTERN + 14: UNILEDEffects.STROBE_YELLOW,
    BANLANX3_EFFECT_PATTERN + 15: UNILEDEffects.STROBE_CYAN,
    BANLANX3_EFFECT_PATTERN + 16: UNILEDEffects.STROBE_PURPLE,
    BANLANX3_EFFECT_PATTERN + 17: UNILEDEffects.STROBE_WHITE,
    BANLANX3_EFFECT_PATTERN + 18: "Adjustable Color Breath", # Colorable
    BANLANX3_EFFECT_PATTERN + 19: "Adjustable Color Strobe", # Colorable
    BANLANX3_EFFECT_CUSTOM: UNILEDEffects.CUSTOM,
    BANLANX3_EFFECT_SOUND + 0: UNILEDEffects.SOUND_MUSIC_BREATH, # 65
    BANLANX3_EFFECT_SOUND + 1: UNILEDEffects.SOUND_MUSIC_JUMP, # 66
    BANLANX3_EFFECT_SOUND + 2: UNILEDEffects.SOUND_MUSIC_MONO_BREATH, # 67 - Colorable
}

BANLANX3_EFFECTS_614: Final = dict(
    chain.from_iterable(d.items() for d in (
        {BANLANX3_EFFECT_WHITE: UNILEDEffects.SOLID_WHITE}, BANLANX3_EFFECTS_613)))

BANLANX3_COLORABLE_EFFECTS: Final = (
    BANLANX3_EFFECT_SOLID,
    BANLANX3_EFFECT_CUSTOM,
    0x13,   #  19 - Adjustable Color Breath
    0x14,   #  20 - Adjustable Color Strobe
    0x67,   # 103 - Monochrome Music Breath
)

_PACKET_NUMBER = 0
_MESSAGE_LENGTH = 1
_PAYLOAD_LENGTH = 2
_HEADER_LENGTH = 3


@dataclass(frozen=True)
class _BANLANX3(UNILEDBLEModel):
    """BanlanX v3 Protocol Implementation"""

    ## 02 07 10 a7 a6 00 e0 f1 04
    ## 01 02 03 04 05 b3 00 02
    ## 1e 01 01
    ## 1e 01 02
    ## 1a 01 0a 01 64 00 00 00 ff 00 00 00 ff (set DIY colors, 3rd byte number of data bytes)
    ## 1a 01 0a 01 64 00 00 00 65 00 00 00 ff
    ## 1f 03 00 ff 00

    ## 11 01 03             - Calibration
    ## 12 01 ff             - Level
    ## 13 04 b3 00 ff ff    - Color & Level
    ## 14 01 09             - Speed
    ## 15 01 01             - Effect 0x63 = Solid, 0x65 = Music, 0x01+ = Pattern
    ## 16 01 00             - Auto Mode 0x00 = Off, 0x01 Auto Pattern, 0x02 Auto Music
    ## 17 01 0f             - Gain/Sensitivity (0x01 - 0x0F)
    ## 19 01 01             - Input

    ##
    ## Device State
    ##
    def construct_connect_message(self, device: UNILEDDevice) -> list[bytearray]:
        """The bytes to send when first connecting."""
        return None

    def construct_status_query(self, device: UNILEDDevice) -> bytearray:
        """The bytes to send for a state query."""
        return self.construct_message(bytearray([0x1D, 0x00]))

    def async_decode_notifications(
        self, device: UNILEDDevice, sender: int, data: bytearray
    ) -> UNILEDStatus | None:
        """Handle notification responses."""

        # 01 19 11 00 ff 05 00 64 00 ff 00 ff 10 04 03 ff 00 00 00 00
        # 02 08 00 00 00 ff 00 00 00 00

        packet_number = data[_PACKET_NUMBER]

        if packet_number == 1:
            message_length = data[_MESSAGE_LENGTH]
            payload_length = data[_PAYLOAD_LENGTH]

            data = device.save_notification_data(data)
            if message_length > payload_length:
                #_LOGGER.debug(
                #    "%s: Packet 1 - payload size: %s, message length: %s",
                #    device.name,
                #    payload_length,
                #    message_length,
                #)
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

            message_length = last[_MESSAGE_LENGTH]
            payload_length = data[_MESSAGE_LENGTH]
            payload_so_far = last[_PAYLOAD_LENGTH] + payload_length

            #_LOGGER.debug(
            #    "%s: Packet %s - payload size: %s, payload so far: %s, message length: %s",
            #    device.name,
            #    packet_number,
            #    payload_length,
            #    payload_so_far,
            #    message_length,
            #)

            if payload_so_far < message_length:
                last[_PACKET_NUMBER] = packet_number
                last[_PAYLOAD_LENGTH] = payload_so_far
                device.save_notification_data(last + data[2:])
                return None

            if (
                payload_so_far > message_length
                or message_length != last[_MESSAGE_LENGTH]
            ):
                _LOGGER.debug("%s: Bad Packet!", device.name)
                last[_MESSAGE_LENGTH] = 0
                return None

            data = last[_HEADER_LENGTH:] + data[2:]

        if len(data) == message_length:
            _LOGGER.debug("%s: Good Status Message: %s", device.name, data.hex())

            #
            # 0  = Power State
            # 1  = level
            # 2  = Speed
            # 3  = Chip Order (Calibration)
            # 4  = Effect
            # 5  = Auto Mode (0x00 = Off, 0x01 = Cycle FX, 0x02 = Cycle Sound)
            # 6  = Red Level (0x00 - 0xFF)
            # 7  = Green Level (0x00 - 0xFF)
            # 8  = Blue Level (x00 - 0xFF)
            # 9  = Gain/Sensitivity (0x01 - 0x0F)
            # 10 = DIY Effect Type
            # 11 = DIY # Colors
            # 12 = DIY FX - Color 1 - Red Level
            # 13 = DIY FX - Color 1 - Green Level
            # 14 = DIY FX - Color 1 - Blue Level
            #
            # SP613E & SP614E - 3rd from last byte in message is the sound input type
            #
            # SP614E Only - Last two bytes in message are cool and warm white levels.
            #
            # xx = Cool White Level
            # xx = Warm White Level (Not used on SP614E)

            level=data[1]
            effect = data[4]
            rgb = (data[6], data[7], data[8])
            input = data[message_length - 3]

            white = None
            if self.model_num == BANLANX3_MODEL_NUMBER_SP614E and effect == BANLANX3_EFFECT_WHITE:
                cool = data[message_length - 2]
                _warm = data[message_length - 1]
                #white = cool
                rgb = None
                rgb = (255, 255, 255)
                level = cool

            mode = data[5] if data[5] in BANLANX3_MODES else _FXMode.OFF.value

            if mode == _FXMode.AUTO.value:
                fxtype = _FXType.PATTERN.value
            elif mode == _FXMode.AUTO_SOUND.value:
                fxtype = _FXType.SOUND.value
            else:
                fxtype = self.codeof_channel_effect_type(device.master, effect)

            return UNILEDStatus(
                power=data[0] == 0x01,
                level=level,
                white=white,
                rgb=rgb,
                fxtype=fxtype,
                effect=effect,
                speed=data[2],
                mode=mode,
                input=input,                
                gain=data[9],
                chip_order=data[3],
            )

        _LOGGER.debug("%s: Unknown/Invalid Packet!", device.name)
        device.save_notification_data(())
        return None

    ##
    ## Channel Control
    ##
    def construct_power_change(
        self, channel: UNILEDChannel, turn_on: int
    ) -> bytearray | None:
        """The bytes to send for a state change"""
        return self.construct_message(
            bytearray([0x0F, 0x01, 0x01 if turn_on else 0x00])
        )

    def construct_level_change(
        self, channel: UNILEDChannel, level: int
    ) -> bytearray | None:
        """The bytes to send for a brightness level change"""
        if channel.status.effect == BANLANX3_EFFECT_WHITE:
            return self.construct_white_change(channel, level)
        return self.construct_message(bytearray([0x12, 0x01, level]))
    
    def construct_color_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int, white: int | None
    ) -> bytearray | None:
        """The bytes to send for a color level change"""
        commands = []

        if channel.status.effect == BANLANX3_EFFECT_WHITE:
            commands.append(
                self.construct_effect_change(channel, BANLANX3_EFFECT_SOLID)
            )
        elif channel.status.effect not in BANLANX3_COLORABLE_EFFECTS:
            return None

        level = channel.status.level
        commands.append(
            self.construct_message(
                bytearray([0x13, 0x04, red, green, blue, level])
            )
        )

        return commands
    
    def construct_effect_speed_change(
        self, channel: UNILEDChannel, speed: int
    ) -> bytearray | None:
        """The bytes to send for an effect speed change"""
        return self.construct_message(bytearray([0x14, 0x01, speed]))

    def construct_effect_change(
        self, channel: UNILEDChannel, effect: int
    ) -> bytearray | None:
        """The bytes to send for an effect change"""
        _LOGGER.debug("Effect Change: %s from %s", effect, channel.status.fxlast)
        return self.construct_message(bytearray([0x15, 0x01, effect]))

    def construct_mode_change(
        self, channel: UNILEDChannel, mode: int
    ) -> list[bytearray] | None:
        """The bytes to send for a mode change."""
        return self.construct_message(bytearray([0x16, 0x01, mode]))

    def construct_white_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a white level change."""
        cool = level
        warm = 0x00
        channel.set_status(
            replace(
                channel.status,
                effect=BANLANX3_EFFECT_WHITE,
                fxtype=_FXType.STATIC.value,
                white=level,
                level=0,
                rgb=(0, 0, 0),
            )
        )
        return self.construct_message(bytearray([0x21, 0x02, cool, warm]))

    ##
    ## Device Configuration
    ##
    def construct_input_change(
        self, channel: UNILEDChannel, input_type: int
    ) -> bytearray | None:
        """The bytes to send for an input change"""
        return self.construct_message(bytearray([0x19, 0x01, input_type]))

    def construct_input_gain_change(
        self, channel: UNILEDChannel, gain: int
    ) -> list[bytearray] | None:
        """The bytes to send for a gain/sensitivity change"""
        return self.construct_message(bytearray([0x17, 0x01, gain]))

    def construct_chip_order_change(
        self, channel: UNILEDChannel, chip_order: str
    ) -> list[bytearray] | None:
        """The bytes to send for a chip order change"""
        return self.construct_message(bytearray([0x11, 0x01, chip_order]))
    
    ##
    ## Channel Informational
    ##
    def dictof_channel_modes(self, channel: UNILEDChannel) -> dict | None:
        """Channel mode dictionary"""
        return BANLANX3_MODES

    def dictof_channel_effects(self, channel: UNILEDChannel) -> dict | None:
        """Channel effects dictionary"""
        if self.model_num == BANLANX3_MODEL_NUMBER_SP614E:
            return BANLANX3_EFFECTS_614
        return BANLANX3_EFFECTS_613

    def codeof_channel_effect_type(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> int | None:
        """Code of channel effect type from effect code"""
        if effect is None:
            effect = channel.status.effect
        if effect < BANLANX3_EFFECT_SOLID:
            return _FXType.PATTERN.value
        elif effect >= BANLANX3_EFFECT_SOUND and effect < BANLANX3_EFFECT_WHITE:
            return _FXType.SOUND.value
        return _FXType.STATIC.value

    def nameof_channel_effect_type(
        self, channel: UNILEDChannel, fxtype: int | None = None
    ) -> str | None:
        """Name an effects type."""
        if fxtype is None:
            fxtype = channel.status.fxtype
        if fxtype in BANLANX3_EFFECT_TYPES:
            return BANLANX3_EFFECT_TYPES[fxtype]
        return f"{UNKNOWN} ({fxtype})"

    def rangeof_channel_effect_speed(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        return (1, 10, 1)

    def rangeof_channel_input_gain(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return (1, 16, 1)

    def dictof_channel_inputs(self, channel: UNILEDChannel) -> dict | None:
        """Inputs type dictionary"""
        return BANLANX3_INPUTS

    ##
    ## Device Informational
    ##
    def rangeof_channel_input_gain(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return (1, 16, 1)

    def dictof_channel_inputs(self, channel: UNILEDChannel) -> dict | None:
        """Inputs type dictionary"""
        return BANLANX3_INPUTS

    def dictof_channel_chip_orders(self, channel: UNILEDChannel) -> dict | None:
        """Chip order dictionary"""
        if self.model_num == BANLANX3_MODEL_NUMBER_SP614E:
            return UNILED_CHIP_ORDER_4COLOR
        return UNILED_CHIP_ORDER_3COLOR

##
## SP613E
##
SP613E = _BANLANX3(
    model_type=UNILEDModelType.STRIP,
    model_name=BANLANX3_MODEL_NAME_SP613E,
    model_num=BANLANX3_MODEL_NUMBER_SP613E,
    description="BLE RGB (Music) Strip Controller",
    manufacturer=BANLANX3_MANUFACTURER,
    manufacturer_id=BANLANX3_MANUFACTURER_ID,
    manufacturer_data=b"\x09\x00",
    resolve_protocol=False,
    channels=1,
    needs_on=True,
    needs_type_reload=False,
    effects_directional=False,
    effects_pausable=False,
    effects_loopable=False,
    sends_status_on_commands=False,
    local_names=[BANLANX3_LOCAL_NAME_SP613E],
    service_uuids=BANLANX3_UUID_SERVICE,
    write_uuids=BANLANX3_UUID_WRITE,
    read_uuids=BANLANX3_UUID_READ,
)

##
## SP614E
##
SP614E = _BANLANX3(
    model_type=UNILEDModelType.STRIP,
    model_name=BANLANX3_MODEL_NAME_SP614E,
    model_num=BANLANX3_MODEL_NUMBER_SP614E,
    description="BLE RGB&W (Music) Strip Controller",
    manufacturer=BANLANX3_MANUFACTURER,
    manufacturer_id=BANLANX3_MANUFACTURER_ID,
    manufacturer_data=b"\x0a\x21",
    resolve_protocol=False,
    channels=1,
    needs_on=True,
    needs_type_reload=False,
    effects_directional=True,
    effects_pausable=False,
    effects_loopable=False,
    sends_status_on_commands=False,
    local_names=[BANLANX3_LOCAL_NAME_SP614E],
    service_uuids=BANLANX3_UUID_SERVICE,
    write_uuids=BANLANX3_UUID_WRITE,
    read_uuids=BANLANX3_UUID_READ,
)
