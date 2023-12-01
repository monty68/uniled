"""UniLED BLE Devices - SP LED (BanlanX v3)"""
from __future__ import annotations
from dataclasses import dataclass, replace
from itertools import chain
from typing import Final
from enum import IntEnum

from ..const import *  # I know!
from ..channel import UniledChannel
from ..features import (
    UniledAttribute,
    UniledGroup,
    UniledButton,
    UniledLedStrip,
    UniledSceneLoop,
    UniledEffectType,
    UniledEffectSpeed,
    UniledEffectLength,
    UniledEffectDirection,
    UniledSensitivity,
    UniledAudioInput,
    UniledChipOrder,
)
from ..effects import (
    UNILED_EFFECT_TYPE_DYNAMIC,
    UNILED_EFFECT_TYPE_STATIC,
    UNILED_EFFECT_TYPE_SOUND,
    UNILEDEffects,
)
from .device import (
    BASE_UUID_FORMAT as BANLANX_UUID_FORMAT,
    BANLANX_MANUFACTURER,
    BANLANX_MANUFACTURER_ID,
    ParseNotificationError,
    UniledBleDevice,
    UniledBleModel,
)

from ..chips import UNILED_CHIP_ORDER_RGB

import logging

_LOGGER = logging.getLogger(__name__)

BANLANX3_SP613E: Final = 0x613E
BANLANX3_SP614E: Final = 0x614E

BANLANX3_EFFECT_DYNAMIC: Final = 0x01
BANLANX3_EFFECT_SOLID: Final = 0x63
BANLANX3_EFFECT_CUSTOM: Final = 0x64
BANLANX3_EFFECT_SOUND: Final = 0x65
BANLANX3_EFFECT_WHITE: Final = 0xCC

BANLANX3_EFFECTS_613: Final = {
    BANLANX3_EFFECT_SOLID: UNILEDEffects.SOLID_COLOR,
    BANLANX3_EFFECT_DYNAMIC + 0: UNILEDEffects.GRADIENT_SEVEN_COLOR,
    BANLANX3_EFFECT_DYNAMIC + 1: UNILEDEffects.JUMP_SEVEN_COLOR,
    BANLANX3_EFFECT_DYNAMIC + 2: UNILEDEffects.BREATH_SEVEN_COLOR,
    BANLANX3_EFFECT_DYNAMIC + 3: UNILEDEffects.STROBE_SEVEN_COLOR,
    BANLANX3_EFFECT_DYNAMIC + 4: UNILEDEffects.BREATH_RED,
    BANLANX3_EFFECT_DYNAMIC + 5: UNILEDEffects.BREATH_GREEN,
    BANLANX3_EFFECT_DYNAMIC + 6: UNILEDEffects.BREATH_BLUE,
    BANLANX3_EFFECT_DYNAMIC + 7: UNILEDEffects.BREATH_YELLOW,
    BANLANX3_EFFECT_DYNAMIC + 8: UNILEDEffects.BREATH_CYAN,
    BANLANX3_EFFECT_DYNAMIC + 9: UNILEDEffects.BREATH_PURPLE,
    BANLANX3_EFFECT_DYNAMIC + 10: UNILEDEffects.BREATH_WHITE,
    BANLANX3_EFFECT_DYNAMIC + 11: UNILEDEffects.STROBE_RED,
    BANLANX3_EFFECT_DYNAMIC + 12: UNILEDEffects.STROBE_GREEN,
    BANLANX3_EFFECT_DYNAMIC + 13: UNILEDEffects.STROBE_BLUE,
    BANLANX3_EFFECT_DYNAMIC + 14: UNILEDEffects.STROBE_YELLOW,
    BANLANX3_EFFECT_DYNAMIC + 15: UNILEDEffects.STROBE_CYAN,
    BANLANX3_EFFECT_DYNAMIC + 16: UNILEDEffects.STROBE_PURPLE,
    BANLANX3_EFFECT_DYNAMIC + 17: UNILEDEffects.STROBE_WHITE,
    BANLANX3_EFFECT_DYNAMIC + 18: "Adjustable Color Breath", # Colorable
    BANLANX3_EFFECT_DYNAMIC + 19: "Adjustable Color Strobe", # Colorable
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

BANLANX3_INPUTS: Final = {
    0x00: UNILED_AUDIO_INPUT_INTMIC,
    0x01: UNILED_AUDIO_INPUT_PLAYER,
    0x02: UNILED_AUDIO_INPUT_EXTMIC,
}

@dataclass(frozen=True)
class BanlanX3(UniledBleModel):
    """BanlanX v3 Protocol Implementation"""

    def __init__(self, id: int, name: str, info: str, data: bytes, channels: int = 1):
        super().__init__(
            model_num = id,
            model_name = name,
            description = info,
            manufacturer = BANLANX_MANUFACTURER,
            channels = channels,
            ble_manufacturer_id = BANLANX_MANUFACTURER_ID,
            ble_manufacturer_data = data,
            ble_service_uuids = [BANLANX_UUID_FORMAT.format(part) for part in ["ffe0"]],
            ble_write_uuids = [BANLANX_UUID_FORMAT.format(part) for part in ["ffe1"]],
            ble_read_uuids = [],
        )

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

    def parse_notifications(
        self,
        device: UniledBleDevice,
        sender: int,
        data: bytearray,
    ) -> bool:
        """Parse notification message(s)"""

        _PACKET_NUMBER = 0
        _MESSAGE_LENGTH = 1
        _PAYLOAD_LENGTH = 2
        _HEADER_LENGTH = 3

        # 01 19 11 00 ff 05 00 64 00 ff 00 ff 10 04 03 ff 00 00 00 00
        # 02 08 00 00 00 ff 00 00 00 00
        #
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
                raise ParseNotificationError("Skip out of sequence Packet!")

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
                raise ParseNotificationError("Bad Packet!")
            data = last[_HEADER_LENGTH:] + data[2:]

        if len(data) != message_length:
            raise ParseNotificationError("Unknown/Invalid Packet!")

        _LOGGER.debug("%s: Good Status Message: %s", device.name, data.hex())           
        return True

##
## SP613E
##
SP613E = BanlanX3(
    id = BANLANX3_SP613E,
    name = "SP613E",
    info = "BLE RGB (Music) Strip Controller",
    data = b"\x09\x00",
)

##
## SP614E
##
SP614E = BanlanX3(
    id = BANLANX3_SP614E,
    name = "SP614E",
    info = "BLE RGB&W (Music) Strip Controller",
    data = b"\x0a\x21",
)
