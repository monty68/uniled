"""UniLED Telink"""
from __future__ import annotations
from typing import Final
from .telink import *

ZENGGE_DEFAULT_MESH_UUID: Final = 0x0211
ZENGGE_DEFAULT_MESH_KEY: Final = "ZenggeMesh"
ZENGGE_DEFAULT_MESH_PASS: Final = "ZenggeTechnology"
ZENGGE_DEFAULT_MESH_TOKEN: Final = None

ZENGGE_DEVICE_TYPE_LIGHT_STRIP: Final = 2
ZENGGE_DEVICE_TYPE_LIGHT_BULB: Final = 5
ZENGGE_DEVICE_TYPE_PANEL_RGBCCT: Final = 35  # Powered RGB/CCT 4 Group Panel

ZENGGE_LIGHT_TYPES: Final = (
    ZENGGE_DEVICE_TYPE_LIGHT_STRIP,
    ZENGGE_DEVICE_TYPE_LIGHT_BULB,
)

ZENGGE_MANUFACTURER_ID: Final = 63517
ZENGGE_MANUFACTURER: Final = "Zengge Technology"
ZENGGE_DESCRIPTION: Final = "Zengge Mesh"
ZENGGE_MODEL_NAME: Final = "HaoDeng"
ZENGGE_UUID_SERVICE: Final = TELINK_UUID_SERVICE
ZENGGE_UUID_PAIR_CHAR: Final = TELINK_UUID_PAIR_CHAR
ZENGGE_UUID_STATUS_CHAR: Final = TELINK_UUID_STATUS_CHAR
ZENGGE_UUID_COMMAND_CHAR: Final = TELINK_UUID_COMMAND_CHAR
ZENGGE_UUID_READ_CHAR: Final = ZENGGE_UUID_COMMAND_CHAR
ZENGGE_UUID_WRITE_CHAR: Final = ZENGGE_UUID_COMMAND_CHAR

ZENGGE_MASTER_IDENTITY: Final = "Mesh"
ZENGGE_MESH_ADDRESS_BRIDGE: Final = 255
ZENGGE_MESH_ADDRESS_NONE: Final = TELINK_MESH_ADDRESS_NONE

ZENGGE_STATUS_ONLINE: Final = "Online"
ZENGGE_STATUS_OFFLINE: Final = "Offline"

ZENGGE_STATE_MODE_RGB: Final = 0
ZENGGE_STATE_MODE_CCT: Final = 1
ZENGGE_STATE_MODE_DYNAMIC: Final = 2
ZENGGE_STATE_MODE_OTHER: Final = 3

ZENGGE_WIRING_CONNECTION_NONE: Final = 0
ZENGGE_WIRING_CONNECTION_RGB: Final = 1
ZENGGE_WIRING_CONNECTION_RGB_W: Final = 2
ZENGGE_WIRING_CONNECTION_RGBW: Final = 3
ZENGGE_WIRING_CONNECTION_RGB_CCT: Final = 4
ZENGGE_WIRING_CONNECTION_RGBCCT: Final = 5
ZENGGE_WIRING_CONNECTION_DIM: Final = 6
ZENGGE_WIRING_CONNECTION_CCT: Final = 7

ZENGGE_WIRING_CONTROL_NONE: Final = 0
ZENGGE_WIRING_CONTROL_RGB: Final = 1
ZENGGE_WIRING_CONTROL_RGB_W: Final = 2  # RGB / W
ZENGGE_WIRING_CONTROL_RGBW: Final = 3  # RGB & W
ZENGGE_WIRING_CONTROL_RGB_CCT: Final = 4
ZENGGE_WIRING_CONTROL_RGBCCT: Final = 5
ZENGGE_WIRING_CONTROL_WARM: Final = 6
ZENGGE_WIRING_CONTROL_COLD: Final = 7
ZENGGE_WIRING_CONTROL_CCT: Final = 8

# STATEACTION_POWER = 0x01
# STATEACTION_BRIGHTNESS = 0x02
# STATEACTION_INCREASEBRIGHTNESS = 0x03
# STATEACTION_DECREASEBRIGHTNESS = 0x04

ZENGGE_COLOR_MODE_RGB: Final = 0x60  # 96
ZENGGE_COLOR_MODE_WARMWHITE: Final = 0x61  # 97
ZENGGE_COLOR_MODE_CCT: Final = 0x62  # 98
ZENGGE_COLOR_MODE_AUX: Final = 0x63  # 99
ZENGGE_COLOR_MODE_CCTAUX: Final = 0x64  # 100

ZENGGE_DIMMING_TARGET_RGBKWC: Final = 0x01  # Set RGB, Keep WC
ZENGGE_DIMMING_TARGET_WCKRGB: Final = 0x02  # Set WC, Keep RGB
ZENGGE_DIMMING_TARGET_RGBWC: Final = 0x03  # Set RGB & WC
ZENGGE_DIMMING_TARGET_RGBOWC: Final = 0x04  # Set RGB, WC Off
ZENGGE_DIMMING_TARGET_WCORGB: Final = 0x05  # Set WC, RGB Off
ZENGGE_DIMMING_TARGET_AUTO: Final = 0x06  # Set lights according to situation

ZENGGE_MIN_KELVIN: Final = 2800
ZENGGE_MAX_KELVIN: Final = 6500

ZENGGE_EFFECT_SOLID: Final = "Solid"
ZENGGE_EFFECT_UNKNOWN: Final = "?FX?"

ZENGGE_EFFECT_LIST: Final = {
    0x01: "Seven Color Cross Fade",
    0x02: "Red Gradual Change",
    0x03: "Green Gradual Change",
    0x04: "Blue Gradual Change",
    0x05: "Yellow Gradual Change",
    0x06: "Cyan Gradual Change",
    0x07: "Purple Gradual Change",
    0x08: "White Gradual Change",
    0x09: "Red/Green Cross Fade",
    0x0A: "Red/Blue Cross Fade",
    0x0B: "Green/Blue Cross Fade",
    0x0C: "Seven Color Strobe",
    0x0D: "Red Strobe Flash",
    0x0E: "Green Strobe Flash",
    0x0F: "Blue Strobe Flash",
    0x10: "Yellow Strobe Flash",
    0x11: "Cyan Strobe Flash",
    0x12: "Purple Strobe Flash",
    0x13: "White Strobe Flash",
    0x14: "Seven Color Jumping Change",
}