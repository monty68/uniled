"""UniLED Telink"""
from __future__ import annotations
from typing import Final

TELINK_UUID_SERVICE: Final = "00010203-0405-0607-0809-0a0b0c0d1910"
TELINK_UUID_STATUS_CHAR: Final = "00010203-0405-0607-0809-0a0b0c0d1911"
TELINK_UUID_COMMAND_CHAR: Final = "00010203-0405-0607-0809-0a0b0c0d1912"
TELINK_UUID_OTA_CHAR: Final = "00010203-0405-0607-0809-0a0b0c0d1913"
TELINK_UUID_PAIR_CHAR: Final = "00010203-0405-0607-0809-0a0b0c0d1914"
TELINK_MANUFACTURER_ID: Final = 529
TELINK_MESH_ADDRESS_NONE: Final = 0x00

#: Data : one byte
C_LIGHT_MODE = 0x33

#: Data : one byte 0 to 6
C_PRESET = 0xC8

#: On/Off command. Data : one byte 0, 1
C_POWER = 0xD0

#: ?
C_FLASH = 0xD2

#: Set mesh groups.
#: Data : 3 bytes
C_MESH_GROUP = 0xD7

#: Request current light/device status
C_GET_STATUS_SENT = 0xDA

#: Response of light/device status request
C_GET_STATUS_RECEIVED = 0xDB

#: State notification
C_NOTIFICATION_RECEIVED = 0xDC

#: Set the mesh id. The light will still answer to the 0 mesh id. Calling the
#: command again replaces the previous mesh id.
#: Data : the new mesh id, 2 bytes in little endian order
C_MESH_ADDRESS = 0xE0

#: 4 bytes : 0x4 red green blue
C_COLOR = 0xE2 # -30

#: Data : None
C_MESH_RESET = 0xE3

#: 7 bytes
C_TIME = 0xE4

#: 10 bytes
C_ALARMS = 0xE5

#: White temperature. one byte 0 to 0x7f
C_WHITE_TEMPERATURE = 0xF0

#: one byte 1 to 0x7f
C_WHITE_BRIGHTNESS = 0xF1

#: one byte : 0xa to 0x64 ....
C_COLOR_BRIGHTNESS = 0xF2

#: Data 4 bytes : How long a color is displayed in a sequence in milliseconds as
#:   an integer in little endian order
C_SEQUENCE_COLOR_DURATION = 0xF5

#: Data 4 bytes : Duration of the fading between colors in a sequence, in
#:   milliseconds, as an integer in little endian order
C_SEQUENCE_FADE_DURATION = 0xF6


