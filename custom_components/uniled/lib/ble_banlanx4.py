"""UniLED BLE Devices - SP LED (BanlanX v4)"""
from __future__ import annotations

from dataclasses import dataclass, replace
from collections import OrderedDict
from itertools import chain
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
from .ble_model import UNILEDBLEModel, BASE_UUID_FORMAT as BANLANX4_UUID_FORMAT

import logging

_LOGGER = logging.getLogger(__name__)

BANLANX4_MODEL_NUMBER_SP630E: Final = 0x630E
BANLANX4_MODEL_NAME_SP630E: Final = "SP630E"
BANLANX4_LOCAL_NAME_SP630E: Final = BANLANX4_MODEL_NAME_SP630E

BANLANX4_MODEL_NUMBER_SP642E: Final = 0x642E
BANLANX4_MODEL_NAME_SP642E: Final = "SP642E"
BANLANX4_LOCAL_NAME_SP642E: Final = BANLANX4_MODEL_NAME_SP642E

BANLANX4_MODEL_NUMBER_SP648E: Final = 0x648E
BANLANX4_MODEL_NAME_SP648E: Final = "SP648E"
BANLANX4_LOCAL_NAME_SP648E: Final = BANLANX4_MODEL_NAME_SP648E

BANLANX4_MANUFACTURER: Final = "SPLED (BanlanX)"
BANLANX4_MANUFACTURER_ID: Final = 20563
BANLANX4_UUID_SERVICE = [BANLANX4_UUID_FORMAT.format(part) for part in ["e0ff", "ffe0"]]
BANLANX4_UUID_WRITE = [BANLANX4_UUID_FORMAT.format(part) for part in ["ffe1"]]
BANLANX4_UUID_READ = []
   
DICTOF_ORDER_CW: Final = {
    0x78: "CW",
    0x79: "WC",
}

DICTOF_ORDER_CWO: Final = {
    0x00: "CWX",
    0x01: "CXW",
    0x02: "WCX",
    0x03: "WXC",
    0x04: "XCW",
    0x05: "XWC",
}

DICTOF_ORDER_123: Final = {
    0x00: "1,2,3",
    0x01: "1,3,2",
    0x02: "2,1,3",
    0x03: "2,3,1",
    0x04: "3,1,2",
    0x05: "3,2,1",
}

DICTOF_ORDER_RGB: Final = UNILED_CHIP_ORDER_3COLOR

DICTOF_ORDER_RGBW: Final = { # 24xCombos to do!
    0x01: "?",
}

DICTOF_ORDER_RGBCW: Final = { # 120xCombos to do!
    0x02: "GRBCW",
}

DICTOF_POWER_ONOFF_MODES: Final = {
    0x01: UNILEDEffects.FLOW_FORWARD,
    0x02: UNILEDEffects.FLOW_BACKWARD,
    0x03: UNILEDEffects.GRADIENT,
    0x04: UNILEDEffects.STARS,
}

DICTOF_POWER_ONOFF_SPEEDS: Final = {
    0x01: "Slow",
    0x02: "Medium",
    0x03: "Fast",
}

POWER_ONOFF_PIXELS_MIN: Final = 1
POWER_ONOFF_PIXELS_MAX: Final = 600

MODE_STATIC_COLOR: Final = 0x01
MODE_STATIC_WHITE: Final = 0x02
MODE_DYNAMIC_COLOR: Final = 0x03
MODE_DYNAMIC_WHITE: Final = 0x04
MODE_SOUND_COLOR: Final = 0x05
MODE_SOUND_WHITE: Final = 0x06
MODE_CUSTOM_COLOR: Final = 0x07

DICTOF_MODES: Final = {
    MODE_STATIC_COLOR: "Static Color",
    MODE_STATIC_WHITE: "Static White",
    MODE_DYNAMIC_COLOR: "Dynamic Color",
    MODE_DYNAMIC_WHITE: "Dynamic White",
    MODE_SOUND_COLOR: "Sound - Color",
    MODE_SOUND_WHITE: "Sound - White",
    MODE_CUSTOM_COLOR: "Custom",
}

LISTOF_STATIC_MODES: Final = [
    MODE_STATIC_COLOR,
    MODE_STATIC_WHITE,
]

LISTOF_SOUND_MODES: Final = [
    MODE_SOUND_COLOR,
    MODE_SOUND_WHITE,
]

LISTOF_COLOR_MODES: Final = [
    MODE_STATIC_COLOR,
    MODE_DYNAMIC_COLOR,
    MODE_SOUND_COLOR,
    MODE_CUSTOM_COLOR,
]

LISTOF_WHITE_MODES: Final = [
    MODE_STATIC_WHITE,
    MODE_DYNAMIC_WHITE,
    MODE_SOUND_WHITE,
]

EFFECT_TYPE_STATIC: Final = 0x00
EFFECT_TYPE_DYNAMIC: Final = 0x01
EFFECT_TYPE_SOUND: Final = 0x02

DICTOF_EFFECT_TYPES: dict(int, str) = {
    EFFECT_TYPE_STATIC: UNILEDEffectType.STATIC,
    EFFECT_TYPE_DYNAMIC: UNILEDEffectType.DYNAMIC,
    EFFECT_TYPE_SOUND: UNILEDEffectType.SOUND,
}


@dataclass(frozen=True)
class _FX_STATIC():
    """BanlanX v4 Effect and Attributes"""
    name: str
    colorable: bool = True
    sizeable: bool = False
    directional: bool = False
    pausable: bool = False
    speedable: bool = False

@dataclass(frozen=True)
class _FX_DYNAMIC():
    """BanlanX v4 Effect and Attributes"""
    name: str
    colorable: bool = False
    sizeable: bool = False
    directional: bool = False
    pausable: bool = False
    speedable: bool = True

@dataclass(frozen=True)
class _FX_SOUND():
    """BanlanX v4 Sound Effect and Attributes"""
    name: str
    colorable: bool = False
    sizeable: bool = False
    directional: bool = False
    pausable: bool = False
    speedable: bool = False

DICTOF_EFFECTS_STATIC_COLOR: Final = {
    0x01: _FX_STATIC(UNILEDEffects.SOLID),
}

DICTOF_EFFECTS_STATIC_WHITE: Final = {
    0x01: _FX_STATIC(UNILEDEffects.SOLID),
}

DICTOF_PWM_EFFECTS_DYNAMIC_WHITE: Final = {
    0x01: _FX_DYNAMIC("White Color Breath", True),
    0x02: _FX_DYNAMIC("White Color Strobe", True),
    0x03: _FX_DYNAMIC("White Color Heart Beat", True),
}

DICTOF_PWM_EFFECTS_SOUND_WHITE: Final = {
    0x01: _FX_SOUND("Sound - White Color Music Breath", True),
}

DICTOF_PWM_EFFECTS_DYNAMIC_COLOR: Final = {
    0x01: _FX_DYNAMIC(UNILEDEffects.JUMP_SEVEN_COLOR),
    0x02: _FX_DYNAMIC(UNILEDEffects.BREATH_SEVEN_COLOR),
    0x03: _FX_DYNAMIC(UNILEDEffects.STROBE_SEVEN_COLOR),
    0x04: _FX_DYNAMIC(UNILEDEffects.HEARTBEAT_SEVEN_COLOR),
    0x05: _FX_DYNAMIC(UNILEDEffects.GRADIENT_SEVEN_COLOR),
    0x06: _FX_DYNAMIC(UNILEDEffects.BREATH_RED),
    0x07: _FX_DYNAMIC(UNILEDEffects.BREATH_GREEN),
    0x08: _FX_DYNAMIC(UNILEDEffects.BREATH_BLUE),
    0x09: _FX_DYNAMIC(UNILEDEffects.BREATH_YELLOW),
    0x0A: _FX_DYNAMIC(UNILEDEffects.BREATH_CYAN),
    0x0B: _FX_DYNAMIC(UNILEDEffects.BREATH_PURPLE),
    0x0C: _FX_DYNAMIC(UNILEDEffects.BREATH_WHITE),
}

DICTOF_PWM_EFFECTS_SOUND_COLOR: Final = {
    0x00: _FX_SOUND(UNILEDEffects.SOUND_MUSIC_BREATH),
    0x01: _FX_SOUND(UNILEDEffects.SOUND_MUSIC_JUMP),
    0x02: _FX_SOUND(UNILEDEffects.SOUND_MUSIC_MONO_BREATH, True)
}

DICTOF_SPI_EFFECTS_DYNAMIC_WHITE: Final = {
    0x01: _FX_DYNAMIC("White Color Breath", True, False, True),
    0x02: _FX_DYNAMIC("White Color Stars", True, False, True),
    0x03: _FX_DYNAMIC("White Color Meteor", True, True, True),
    0x04: _FX_DYNAMIC("White Color Comet Spin", True, True, True),
    0x05: _FX_DYNAMIC("White Color Dot Spin", True, True, True, True),
    0x06: _FX_DYNAMIC("White Color Segment Spin", True, True, True, True),
    0x07: _FX_DYNAMIC("White Color Chasing Dots", True, True, True, True),
    0x08: _FX_DYNAMIC("White Color Comet", True, True, True, True),
    0x09: _FX_DYNAMIC("White Color Wave", True, True, True, True),
    0x0A: _FX_DYNAMIC("White Color Stacking", True, True, True),
}

DICTOF_SPI_EFFECTS_DYNAMIC_COLOR: Final = {
    0x01: _FX_DYNAMIC(UNILEDEffects.RAINBOW, False, True, True, True),
    0x02: _FX_DYNAMIC(UNILEDEffects.RAINBOW_METEOR, False, True, True),
    0x03: _FX_DYNAMIC(UNILEDEffects.RAINBOW_COMET, False, True, True),
    0x04: _FX_DYNAMIC(UNILEDEffects.RAINBOW_SEGMENT, False, True, True),
    0x05: _FX_DYNAMIC(UNILEDEffects.RAINBOW_WAVE, False, True, True),
    0x06: _FX_DYNAMIC(UNILEDEffects.RAINBOW_JUMP),
    0x07: _FX_DYNAMIC(UNILEDEffects.RAINBOW_STARS),
    0x08: _FX_DYNAMIC(UNILEDEffects.RAINBOW_SPIN, False, True),
    0x09: _FX_DYNAMIC(UNILEDEffects.FIRE_RED_YELLOW, False, True, True),
    0x0A: _FX_DYNAMIC(UNILEDEffects.FIRE_RED_PURPLE, False, True, True),
    0x0B: _FX_DYNAMIC(UNILEDEffects.FIRE_GREEN_YELLOW, False, True, True),
    0x0C: _FX_DYNAMIC(UNILEDEffects.FIRE_GREEN_CYAN, False, True, True),
    0x0D: _FX_DYNAMIC(UNILEDEffects.FIRE_BLUE_PURPLE, False, True, True),
    0x0E: _FX_DYNAMIC(UNILEDEffects.FIRE_BLUE_CYAN, False, True, True),
    0x0F: _FX_DYNAMIC(UNILEDEffects.COMET_RED, False, True, True, True),
    0x10: _FX_DYNAMIC(UNILEDEffects.COMET_GREEN, False, True, True, True),
    0x11: _FX_DYNAMIC(UNILEDEffects.COMET_BLUE, False, True, True, True),
    0x12: _FX_DYNAMIC(UNILEDEffects.COMET_YELLOW, False, True, True, True),
    0x13: _FX_DYNAMIC(UNILEDEffects.COMET_CYAN, False, True, True, True),
    0x14: _FX_DYNAMIC(UNILEDEffects.COMET_PURPLE, False, True, True, True),
    0x15: _FX_DYNAMIC(UNILEDEffects.COMET_WHITE, False, True, True, True),
    0x16: _FX_DYNAMIC(UNILEDEffects.METEOR_RED, False, True, True),
    0x17: _FX_DYNAMIC(UNILEDEffects.METEOR_GREEN, False, True, True),
    0x18: _FX_DYNAMIC(UNILEDEffects.METEOR_BLUE, False, True, True),
    0x19: _FX_DYNAMIC(UNILEDEffects.METEOR_YELLOW, False, True, True),
    0x1A: _FX_DYNAMIC(UNILEDEffects.METEOR_CYAN, False, True, True),
    0x1B: _FX_DYNAMIC(UNILEDEffects.METEOR_PURPLE, False, True, True),
    0x1C: _FX_DYNAMIC(UNILEDEffects.METEOR_WHITE, False, True, True),
    0x1D: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_RED_GREEN, False, True, True, True),
    0x1E: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_RED_BLUE, False, True, True, True),
    0x1F: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_RED_YELLOW, False, True, True, True),
    0x20: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_RED_CYAN, False, True, True, True),
    0x21: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_RED_PURPLE, False, True, True, True),
    0x22: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_RED_WHITE, False, True, True, True),
    0x23: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_GREEN_BLUE, False, True, True, True),
    0x24: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_GREEN_YELLOW, False, True, True, True),
    0x25: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_GREEN_CYAN, False, True, True, True),
    0x26: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_GREEN_PURPLE, False, True, True, True),
    0x27: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_GREEN_WHITE, False, True, True, True),
    0x28: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_BLUE_YELLOW, False, True, True, True),
    0x29: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_BLUE_CYAN, False, True, True, True),
    0x2A: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_BLUE_PURPLE, False, True, True, True),
    0x2B: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_BLUE_WHITE, False, True, True, True),
    0x2C: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_YELLOW_CYAN, False, True, True, True),
    0x2D: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_YELLOW_PURPLE, False, True, True, True),
    0x2E: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_YELLOW_WHITE, False, True, True, True),
    0x2F: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_CYAN_PURPLE, False, True, True, True),
    0x30: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_CYAN_WHITE, False, True, True, True),
    0x31: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_PURPLE_WHITE, False, True, True, True),
    0x32: _FX_DYNAMIC(UNILEDEffects.WAVE_RED, False, True, True, True),
    0x33: _FX_DYNAMIC(UNILEDEffects.WAVE_GREEN, False, True, True, True),
    0x34: _FX_DYNAMIC(UNILEDEffects.WAVE_BLUE, False, True, True, True),
    0x35: _FX_DYNAMIC(UNILEDEffects.WAVE_YELLOW, False, True, True, True),
    0x36: _FX_DYNAMIC(UNILEDEffects.WAVE_CYAN, False, True, True, True),
    0x37: _FX_DYNAMIC(UNILEDEffects.WAVE_PURPLE, False, True, True, True),
    0x38: _FX_DYNAMIC(UNILEDEffects.WAVE_WHITE, False, True, True, True),
    0x39: _FX_DYNAMIC(UNILEDEffects.WAVE_RED_GREEN, False, True, True, True),
    0x3A: _FX_DYNAMIC(UNILEDEffects.WAVE_RED_BLUE, False, True, True, True),
    0x3B: _FX_DYNAMIC(UNILEDEffects.WAVE_RED_YELLOW, False, True, True, True),
    0x3C: _FX_DYNAMIC(UNILEDEffects.WAVE_RED_CYAN, False, True, True, True),
    0x3D: _FX_DYNAMIC(UNILEDEffects.WAVE_RED_PURPLE, False, True, True, True),
    0x3E: _FX_DYNAMIC(UNILEDEffects.WAVE_RED_WHITE, False, True, True, True),
    0x3F: _FX_DYNAMIC(UNILEDEffects.WAVE_GREEN_BLUE, False, True, True, True),
    0x40: _FX_DYNAMIC(UNILEDEffects.WAVE_GREEN_YELLOW, False, True, True, True),
    0x41: _FX_DYNAMIC(UNILEDEffects.WAVE_GREEN_CYAN, False, True, True, True),
    0x42: _FX_DYNAMIC(UNILEDEffects.WAVE_GREEN_PURPLE, False, True, True, True),
    0x43: _FX_DYNAMIC(UNILEDEffects.WAVE_GREEN_WHITE, False, True, True, True),
    0x44: _FX_DYNAMIC(UNILEDEffects.WAVE_BLUE_YELLOW, False, True, True, True),
    0x45: _FX_DYNAMIC(UNILEDEffects.WAVE_BLUE_CYAN, False, True, True, True),
    0x46: _FX_DYNAMIC(UNILEDEffects.WAVE_BLUE_PURPLE, False, True, True, True),
    0x47: _FX_DYNAMIC(UNILEDEffects.WAVE_BLUE_WHITE, False, True, True, True),
    0x48: _FX_DYNAMIC(UNILEDEffects.WAVE_YELLOW_CYAN, False, True, True, True),
    0x49: _FX_DYNAMIC(UNILEDEffects.WAVE_YELLOW_PURPLE, False, True, True, True),
    0x4A: _FX_DYNAMIC(UNILEDEffects.WAVE_YELLOW_WHITE, False, True, True, True),
    0x4B: _FX_DYNAMIC(UNILEDEffects.WAVE_CYAN_PURPLE, False, True, True, True),
    0x4C: _FX_DYNAMIC(UNILEDEffects.WAVE_CYAN_WHITE, False, True, True, True),
    0x4D: _FX_DYNAMIC(UNILEDEffects.WAVE_PURPLE_WHITE, False, True, True, True),
    0x4E: _FX_DYNAMIC(UNILEDEffects.STARS_RED),
    0x4F: _FX_DYNAMIC(UNILEDEffects.STARS_GREEN),
    0x50: _FX_DYNAMIC(UNILEDEffects.STARS_BLUE),
    0x51: _FX_DYNAMIC(UNILEDEffects.STARS_YELLOW),
    0x52: _FX_DYNAMIC(UNILEDEffects.STARS_CYAN),
    0x53: _FX_DYNAMIC(UNILEDEffects.STARS_PURPLE),
    0x54: _FX_DYNAMIC(UNILEDEffects.STARS_WHITE),
    0x55: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_RED),
    0x56: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_GREEN),
    0x57: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_BLUE),
    0x58: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_YELLOW),
    0x59: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_CYAN),
    0x5A: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_PURPLE),
    0x5B: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_RED_WHITE),
    0x5C: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_GREEN_WHITE),
    0x5D: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_BLUE_WHITE),
    0x5E: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_YELLOW_WHITE),
    0x5F: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_CYAN_WHITE),
    0x60: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_PURPLE_WHITE),
    0x61: _FX_DYNAMIC(UNILEDEffects.BACKGROUND_STARS_WHITE_WHITE),
    0x62: _FX_DYNAMIC(UNILEDEffects.BREATH_RED),
    0x63: _FX_DYNAMIC(UNILEDEffects.BREATH_GREEN),
    0x64: _FX_DYNAMIC(UNILEDEffects.BREATH_BLUE),
    0x65: _FX_DYNAMIC(UNILEDEffects.BREATH_YELLOW),
    0x66: _FX_DYNAMIC(UNILEDEffects.BREATH_CYAN),
    0x67: _FX_DYNAMIC(UNILEDEffects.BREATH_PURPLE),
    0x68: _FX_DYNAMIC(UNILEDEffects.BREATH_WHITE),
    0x69: _FX_DYNAMIC(UNILEDEffects.STACKING_RED, False, True, True, True),
    0x6A: _FX_DYNAMIC(UNILEDEffects.STACKING_GREEN, False, True, True, True),
    0x6B: _FX_DYNAMIC(UNILEDEffects.STACKING_BLUE, False, True, True, True),
    0x6C: _FX_DYNAMIC(UNILEDEffects.STACKING_YELLOW, False, True, True, True),
    0x6D: _FX_DYNAMIC(UNILEDEffects.STACKING_CYAN, False, True, True, True),
    0x6E: _FX_DYNAMIC(UNILEDEffects.STACKING_PRUPLE, False, True, True, True),
    0x6F: _FX_DYNAMIC(UNILEDEffects.STACKING_WHITE, False, True, True, True),
    0x70: _FX_DYNAMIC(UNILEDEffects.STACK_FULL_COLOR, False, True, True, True),
    0x71: _FX_DYNAMIC(UNILEDEffects.STACK_RED_GREEN, False, True, True, True),
    0x72: _FX_DYNAMIC(UNILEDEffects.STACK_GREEN_BLUE, False, True, True, True),
    0x73: _FX_DYNAMIC(UNILEDEffects.STACK_BLUE_YELLOW, False, True, True, True),
    0x74: _FX_DYNAMIC(UNILEDEffects.STACK_YELLOW_CYAN, False, True, True, True),
    0x75: _FX_DYNAMIC(UNILEDEffects.STACK_CYAN_PURPLE, False, True, True, True),
    0x76: _FX_DYNAMIC(UNILEDEffects.STACK_PURPLE_WHITE, False, True, True, True),
    0x77: _FX_DYNAMIC(UNILEDEffects.SNAKE_RED_BLUE_WHITE, False, True, True, True),
    0x78: _FX_DYNAMIC(UNILEDEffects.SNAKE_GREEN_YELLOW_WHITE, False, True, True, True),
    0x79: _FX_DYNAMIC(UNILEDEffects.SNAKE_RED_GREEN_WHITE, False, True, True, True),
    0x7A: _FX_DYNAMIC(UNILEDEffects.SNAKE_RED_YELLOW, False, True, True, True),
    0x7B: _FX_DYNAMIC(UNILEDEffects.SNAKE_RED_WHITE, False, True, True, True),
    0x7C: _FX_DYNAMIC(UNILEDEffects.SNAKE_GREEN_WHITE, False, True, True, True),
    0x7D: _FX_DYNAMIC(UNILEDEffects.COMET_SPIN_RED, False, True),
    0x7E: _FX_DYNAMIC(UNILEDEffects.COMET_SPIN_GREEN, False, True),
    0x7F: _FX_DYNAMIC(UNILEDEffects.COMET_SPIN_BLUE, False, True),
    0x80: _FX_DYNAMIC(UNILEDEffects.COMET_SPIN_YELLOW, False, True),
    0x81: _FX_DYNAMIC(UNILEDEffects.COMET_SPIN_CYAN, False, True),
    0x82: _FX_DYNAMIC(UNILEDEffects.COMET_SPIN_PURPLE, False, True),
    0x83: _FX_DYNAMIC(UNILEDEffects.COMET_SPIN_WHITE, False, True),
    0x84: _FX_DYNAMIC(UNILEDEffects.DOT_SPIN_RED, False, True),
    0x85: _FX_DYNAMIC(UNILEDEffects.DOT_SPIN_GREEN, False, True),
    0x86: _FX_DYNAMIC(UNILEDEffects.DOT_SPIN_BLUE, False, True),
    0x87: _FX_DYNAMIC(UNILEDEffects.DOT_SPIN_YELLOW, False, True),
    0x88: _FX_DYNAMIC(UNILEDEffects.DOT_SPIN_CYAN, False, True),
    0x89: _FX_DYNAMIC(UNILEDEffects.DOT_SPIN_PURPLE, False, True),
    0x8A: _FX_DYNAMIC(UNILEDEffects.DOT_SPIN_WHITE, False, True),
    0x8B: _FX_DYNAMIC(UNILEDEffects.SEGMENT_SPIN_RED, False, True, False, True),
    0x8C: _FX_DYNAMIC(UNILEDEffects.SEGMENT_SPIN_GREEN, False, True, False, True),
    0x8D: _FX_DYNAMIC(UNILEDEffects.SEGMENT_SPIN_BLUE, False, True, False, True),
    0x8E: _FX_DYNAMIC(UNILEDEffects.SEGMENT_SPIN_YELLOW, False, True, False, True),
    0x8F: _FX_DYNAMIC(UNILEDEffects.SEGMENT_SPIN_CYAN, False, True, False, True),
    0x90: _FX_DYNAMIC(UNILEDEffects.SEGMENT_SPIN_PURPLE, False, True, False, True),
    0x91: _FX_DYNAMIC(UNILEDEffects.SEGMENT_SPIN_WHITE, False, True, False, True),
    0x92: _FX_DYNAMIC(UNILEDEffects.GRADIENT),
}

DICTOF_SPI_EFFECTS_SOUND_WHITE: Final = {
    0x01: _FX_SOUND("Sound - White Color Music Blink", True),
    0x02: _FX_SOUND("Sound - White Color Music Force", True, True),
    0x03: _FX_SOUND("Sound - White Color Music Hits", True),
    0x04: _FX_SOUND("Sound - White Color Music Eject Forward", True, False, True),
    0x05: _FX_SOUND("Sound - White Color Music Eject Backward", True, False, True),
}

DICTOF_SPI_EFFECTS_SOUND_COLOR: Final = {
    0x01: _FX_SOUND(UNILEDEffects.SOUND_RHYTHM_SPECTRUM_FULL),
    0x02: _FX_SOUND(UNILEDEffects.SOUND_RHYTHM_SPECTRUM_SINGLE, True),
    0x03: _FX_SOUND(UNILEDEffects.SOUND_RHYTHM_STARS_FULL),
    0x04: _FX_SOUND(UNILEDEffects.SOUND_RHYTHM_STARS_SINGLE, True),
    0x05: _FX_SOUND(UNILEDEffects.SOUND_ENERGY_GRADIENT, False, True),
    0x06: _FX_SOUND(UNILEDEffects.SOUND_ENERGY_SINGLE, True, True),
    0x07: _FX_SOUND(UNILEDEffects.SOUND_PULSE_GRADIENT),
    0x08: _FX_SOUND(UNILEDEffects.SOUND_PULSE_SINGLE, True),
    0x09: _FX_SOUND(UNILEDEffects.SOUND_EJECTION_FORWARD_FULL, False, True),
    0x0A: _FX_SOUND(UNILEDEffects.SOUND_EJECTION_FORWARD_SINGLE, True, True),
    0x0B: _FX_SOUND(UNILEDEffects.SOUND_EJECTION_BACKWARD_FULL, False, True),
    0x0C: _FX_SOUND(UNILEDEffects.SOUND_EJECTION_BACKWARD_SINGLE, True, True),
    0x0D: _FX_SOUND(UNILEDEffects.SOUND_VU_METER_FULL, False, True),
    0x0E: _FX_SOUND(UNILEDEffects.SOUND_VU_METER_SINGLE, True, True),
    0x0F: _FX_SOUND(UNILEDEffects.SOUND_LOVE_AND_PEACE),
    0x10: _FX_SOUND(UNILEDEffects.SOUND_CHRISTMAS),
    0x11: _FX_SOUND(UNILEDEffects.SOUND_HEARTBEAT),
    0x12: _FX_SOUND(UNILEDEffects.SOUND_PARTY),
}

DICTOF_PWM_EFFECTS_CUSTOM_COLOR: Final = {
    0x01: _FX_DYNAMIC(UNILEDEffects.JUMP),
    0x02: _FX_DYNAMIC(UNILEDEffects.BREATH),
    0x03: _FX_DYNAMIC(UNILEDEffects.STROBE),
}

DICTOF_SPI_EFFECTS_CUSTOM_COLOR: Final = {       
    0x01: _FX_STATIC(UNILEDEffects.STATIC, False),
    0x02: _FX_DYNAMIC("Chase Forward"),
    0x03: _FX_DYNAMIC("Chase Backward"),
    0x04: _FX_DYNAMIC("Chase Middle to Out"),
    0x05: _FX_DYNAMIC("Chase Out to Middle"),
    0x06: _FX_DYNAMIC("Twinkle"),
    0x07: _FX_DYNAMIC(UNILEDEffects.FADE),
    0x08: _FX_DYNAMIC("Comet Forward"),
    0x09: _FX_DYNAMIC("Comet Backward"),
    0x0A: _FX_DYNAMIC("Comet Middle to Out"),
    0x0B: _FX_DYNAMIC("Comet Out to Middle"),
    0x0C: _FX_DYNAMIC("Wave Forward"),
    0x0D: _FX_DYNAMIC("Wave Backward"),
    0x0E: _FX_DYNAMIC("Wave Middle to Out"),
    0x0F: _FX_DYNAMIC("Wave Out to Middle"),
    0x10: _FX_DYNAMIC(UNILEDEffects.STROBE),
    0x11: _FX_DYNAMIC("Solid Fade"),
    0x12: _FX_DYNAMIC("Full Strobe"),
}

CUSTOM_SLOT_PIXELS_MIN: Final = 0
CUSTOM_SLOT_PIXELS_MAX: Final = 150

RANGEOF_EFFECT_SPEED: Final = (1, 10, 1)
RANGEOF_EFFECT_LENGTH: Final = (1, 150, 1)
RANGEOF_INPUT_GAIN: Final = (1, 16, 1)

DICTOF_INPUTS: Final = {
    0x00: UNILEDInput.INTMIC,
    0x01: UNILEDInput.PLAYER,
    0x02: UNILEDInput.EXTMIC,
}

class _ATTRIBUTES():
    """BanlanX v4 Chip Type Attributes"""
    def __init__(self):
        self.name = str(UNKNOWN)
        self.pwm = bool(False)
        self.spi = bool(False)
        self.hue = bool(False)
        self.cct = bool(False)
        self.white = bool(False)
        self.order = {0x80: "Mono"}
        self.effects = None
        self.coexistence = bool(False)

    def dictof_mode_effects(self, mode: int | None) -> dict | None:
        """Mode effects dictionary"""
        if mode is not None and self.effects is not None:
            if mode in self.effects:
                return self.effects[mode]
        return None

@dataclass(frozen=True)
class _MODEL(UNILEDBLEModel):
    """BanlanX v4 Protocol Implementation"""
    attr_dict: dict(int, _ATTRIBUTES) | None
    attr: _ATTRIBUTES | None = None
    
    ##
    ## Unknown Command:   53 01 00 01 00 0a 96 62 9c 17 0a 06 00 00 84 e3
    ## Unknown Response:  53 01 00 01 00 01 a5
    ##
    ## 0000   53 6c 08 01 00 05 17 e8 17 17 17  - ??
    ## 0000   53 08 38 01 00 05 27 25 26 27 2d  - On/Off Mode?
    ## 0000   53 0a a7 01 00 01 b8 - coexistence on/off
    ## 0000   53 0b 35 01 00 01 2b              - Power On State?
    ## 0000   53 03 44 01 00 07 08 0b 6d 68 6b 1e 69    - Rename
    ## 0000   53 58 24 01 00 01 3a              - Loop
    ## 0000   53 5d e2 01 00 01 fd              - Play/Pause
    ##
    ## Host Packet to control sound FX
    ## 0000   53 5b 28 01 00 10 33 32 31 3f 3e 3c 3b 3b 3b 3b 3c 3e 3f 31 32 33
    ##
    ## Custom Mode Settings
    ## 0000   53 63 fa 01 00 1d e4 e3 1a 1a e5 e3 e5 1a e5 e3 e5 e5 1a e5 e5 e5 e5 e5 e5 e5 e5 e5 e5 e5 e5 e5 e5 e5 e5

    _HEADER_LENGTH = 6
    _HEADER_BYTE = 0x53
    _MESSAGE_TYPE = 1
    _MESSAGE_KEY = 2
    _MESSAGE_LENGTH = 5
    _DEVICE_STATUS = 0x02

    def __decoder(self, device: UNILEDDevice, encoded: bytearray) -> bytearray | None:
        """Decode BanlanX v4 Message."""

        packet_length = len(encoded) 
        if packet_length < self._HEADER_LENGTH:
            _LOGGER.error("%s: Packet is undersized", device.name)
            return None

        if encoded[0] != self._HEADER_BYTE:
            _LOGGER.error("%s: Packet is invalid", device.name)
            return None

        message_length = encoded[self._MESSAGE_LENGTH]
        if packet_length != message_length + self._HEADER_LENGTH:
            _LOGGER.error("%s: Packet payload size mismatch: %s vs %s", 
                          device.name, 
                          packet_length,
                          message_length + self._HEADER_LENGTH)
            return None

        message_key = encoded[self._MESSAGE_KEY]
        if not message_key:
            return encoded

        _LOGGER.warning("%s: Encoded packet - currently unsupported", device.name)
        return None
    
    def __encoder(self, cmd: int, data: bytearray) -> list[bytearray]:
        """Encode BanlanX v4 Message."""
        key = 0x00
        bytes = len(data) & 0xFF
        encoded = bytearray([self._HEADER_BYTE, cmd & 0xFF, key, 0x01, 0x00, bytes])
        for b in range(bytes):
            c = data[b]
            encoded.append(c)
        
        encoded[self._MESSAGE_KEY] = key & 0xFF

        return self.construct_message(encoded)
    
    ##
    ## Device State
    ##   
    def construct_connect_message(self, device: UNILEDDevice) -> list[bytearray]:
        """The bytes to send when first connecting."""
        ## 0000   53 08 38 01 00 05 27 25 26 27 2d  - On/Off Mode?
        #b = 42
        #return self.__encoder(0x08, bytearray([0x01, 0x02, 0x01]) + bytearray(b.to_bytes(2, 'big')))
        #return self.__encoder(0x53, bytearray([0x01, 0x04]))
        return None

    def construct_status_query(self, device: UNILEDDevice) -> bytearray:
        """The bytes to send for a state query."""
        # 53 02 9A 01 00 01 3C
        return self.__encoder(0x02, bytearray([0x01]))

    def async_decode_notifications(
        self, device: UNILEDDevice, sender: int, data: bytearray
    ) -> UNILEDStatus | None:
        """Handle notification responses."""

        data = self.__decoder(device, data)
        if data is None:
            return None       
        
        if data[self._MESSAGE_TYPE] != self._DEVICE_STATUS:
            _LOGGER.warning("%s: Invalid Packet!", device.name)
            return None

        #                          1 1 1 1 1 1 1 1 1 1 2 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 5 5 5 5 5 5 5 5 5 5 6 6 6 6 6 6 6 6 6 6 7 7 7 7 7 7 7 7 7 7 8 8 8 8 8 8 8 8 8 8 9 9 9 9 9 9 9 9 9 9 0 0 0
        #      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2
        #      H1H2      ML        MTV1V2V3V4V5V6V7V8CTOMOSPXLSWCPS      PWLMO2MDFXRNHLWLRRGGBBCWWWSPFLFDGSINR2G2B2CWWWFXCSP1RRGGBBP2RRGGBBP3RRGGBBP4RRGGBBP5RRGGBBP6RRGGBBP7RRGGBB 
        #      530200010061000111003356332e302e3039208c010013000101024b00010002050801ff471e2dffffff0a660010001921ffffbb010706ff00000600ff00060000ff000000000000000000000000000000000a03010302030503070309031e0345035403770392
        #      530200010061000111003356332e302e3039208c030100130101024b00010002050801ff471e2dffffff0a660010001921ffffbb010706ff00000600ff00060000ff000000000000000000000000000000000a03010302030503070309031e0345035403770392
        #      530200010061000111003356332e302e3039208c0103002a0101024b00010002732601ff99ff0c457b1e0a660010001921ffb34c010706ff00000600ff00060000ff000000000000000000000000000000000a03010302030503070309031e0345035403770392
        #      530200010061000111003356332e302e3039208c0401002a0002024b00010002010101ffff68ff4923230a66000900ff6e5400f50d0706ff00000600ff00060000ff000000000000000000000000000000000a03010302030503070309031e0345035403770392

        # SP636E
        #      530200010061000111001e56322e302e333020020103003c0001024b00010078060101ffffff0000ff000a1e011000ff0000ff00010706ff00000600ff00060000ff000000000000000000000000000000000a040104020403040404050406040704080409040a
       
        # SP637E
        #      530200010061000111001e56322e302e33302004040100150001024b00010000060101ffffff0000ff000a1e011000ff0000ff00010706ff00000600ff00060000ff000000000000000000000000000000000a040104020403040404050406040704080409040a
       
        # SP642E
        #      53020001004f000111003056332e302e303620030303003c00010239000000780201010103ff0000ff000a1e011000ff0000ff00010706ff00000600ff00060000ff00000000000000000000000000000000010401
        #      530100010001b4
       
        # SP648E
        #      530200010061000111003156332e302e303720060203000d0002024b00010002010101ffff00ff00ff000a1e011000ff0000ff000f0770ff00000600ff00060000ff5c00ffff0000000000000000000000000a03010302030503070309031e0345035403770392
        
        # 00  = Always 0x53
        # 01  = Always 0x02
        # 02  = ?? - 0x00
        # 03  = ?? - 0x01
        # 04  = ?? - 0x00
        # 05  = Message Length
        # 06  = ?? - 0x00
        # 07  = ?? - 0x01
        # 08  = ?? - 0x11 #17
        # 09  = ?? - 0x00
        # 10  = ?? - SP630E=0x33, SP648E=0x31, SP642E=0x30
        # 11  = Version Char #1
        # 12  = Version Char #2
        # 13  = Version Char #3
        # 14  = Version Char #4
        # 15  = Version Char #5
        # 16  = Version Char #6
        # 17  = Version Char #7
        # 18  = Version Char #8
        # 19  = Chip Type (0x86=IC RGB, 0x89=IC RGB + PWM CW etc.)
        # 20  = On/Off Mode FX Mode (0x00=??, 0x01=Flow Forward, 0x02=Flow Backward, 0x03=Gradient, 0x04=Stars)
        # 21  = On/Off Mode FX Speed (0x00=??, 0x01=Slow, 0x02=Medium, 0x03=Fast)
        # 22  = On/Off Mode FX Pixel Count MSB (min=1, max=600)
        # 23  = On/Off Mode FX Pixel Count LSB (min=1, max=600)
        # 24  = Coexistence of colored and white (0x00=Off, 0x01=On) - Only available if white channel(s)
        # 25  = Power On State (0x00=Off, 0x01=On, 0x02=Last)
        # 26  = ?? - 0x02
        # 27  = Sub Message Length (bytes from poistion 28 to the end of packet)
        # 28  = ?? - 0x00 (# of Timers)
        # 29  = Power (0x00=Off, 0x01=On)
        # 30  = Loop Mode (0x00 = Off, 0x01 = Cycle FX, 0x02 = Cycle Sound)
        # 31  = Chip Order
        # 32  = FX Mode (0x01=Static Color, 0x02=Static White, 0x03=Dynamic Color, 0x04=Dynamic White, 0x05=Sound Color, 0x06=Sound White, 0x07=Custom)
        # 33  = FX Number
        # 34  = FX Play (0x00=Paused, 0x01=Run)
        # 35  = Hue Brightness Level
        # 36  = White Brightness Level
        # 37  = Static Red Level (0x00 - 0xFF)
        # 38  = Static Green Level (0x00 - 0xFF)
        # 39  = Static Blue Level (0x00 - 0xFF)
        # 40  = Static Cool White
        # 41  = Static Warm White
        # 42  = Effect Speed (0x01 - 0x0A)
        # 43  = Effect Length (0x01 - 0x96)
        # 44  = Effect Direction (0x00=Backward, 0x01=Forward)
        # 45  = Gain/Sesnsitivity (0x01 - 0x10)
        # 46  = Input (0x00=Internal Mic, 0x01=Player, 0x02=External Mic)
        # 47  = Music Red Level (0x00 - 0xFF)
        # 48  = Music Green Level (0x00 - 0xFF)
        # 49  = Music Blue Level (0x00 - 0xFF)
        # 50  = Music Cool White
        # 51  = Music Warm White
        # 52  = Custom FX Type
        # 53  = Custom Slots (0x07)
        # 54  = Custom 1 Pixels
        # 55  = Custom 1 Red Level
        # 56  = Custom 1 Green Level
        # 57  = Custom 1 Blue Level
        # 58  = Custom 2 Pixels
        # 59  = Custom 2 Red Level
        # 60  = Custom 2 Green Level
        # 61  = Custom 2 Blue Level
        # 62  = Custom 3 Pixels
        # 63  = Custom 3 Red Level
        # 64  = Custom 3 Green Level
        # 65  = Custom 3 Blue Level
        # 66  = Custom 4 Pixels
        # 67  = Custom 4 Red Level
        # 68  = Custom 4 Green Level
        # 69  = Custom 4 Blue Level
        # 70  = Custom 5 Pixels
        # 71  = Custom 5 Red Level
        # 72  = Custom 5 Green Level
        # 73  = Custom 5 Blue Level
        # 74  = Custom 6 Pixels
        # 75  = Custom 6 Red Level
        # 76  = Custom 6 Green Level
        # 77  = Custom 6 Blue Level
        # 78  = Custom 7 Pixels
        # 79  = Custom 7 Red Level
        # 80  = Custom 7 Green Level
        # 81  = Custom 7 Blue Level
        # 82  = Favourite Slots (max=10)
        # 83  = Favourite 1 Mode
        # 84  = Favourite 1 Effect
        # 85  = Favourite 2 Mode
        # 86  = Favourite 2 Effect
        # 87  = Favourite 3 Mode
        # 88  = Favourite 3 Effect
        # 89  = Favourite 4 Mode
        # 90  = Favourite 4 Effect
        # 91  = Favourite 5 Mode
        # 92  = Favourite 5 Effect
        # 93  = Favourite 6 Mode
        # 94  = Favourite 6 Effect
        # 95  = Favourite 7 Mode
        # 96  = Favourite 7 Effect
        # 97  = Favourite 8 Mode
        # 98  = Favourite 8 Effect
        # 99  = Favourite 9 Mode
        # 100  = Favourite 9 Effect
        # 101  = Favourite 10 Mode
        # 102  = Favourite 10 Effect
        #
        chip_type = data[19]
        object.__setattr__(self, 'attr', self.dictof_chip_type_attributes(chip_type))

        if self.attr is None:
            _LOGGER.warning("%s: Missing attributes object!", device.name)
            return None
        
        power = 0x01 if data[29] > 0x00 else 0x00
        mode = data[32]
        coexistence = data[24] if self.attr.coexistence else None

        direction = length = speed = effect = fxtype = fxplay = fxloop = None
        level = white = cool = warm = rgb = None
        rgb1 = (data[37], data[38], data[39])
        rgb2 = (data[47], data[48], data[49])

        if (fxlist := self.attr.dictof_mode_effects(mode)) is not None:
            if (fxattr := None if data[33] not in fxlist else fxlist[data[33]]):
                _LOGGER.debug("%s: FXATTR: (%s - %s) %s", device.name, self.attr.name, self.attr.coexistence, fxattr)
                effect = data[33]
                fxtype = self.codeof_channel_effect_type(device.master, effect, mode)
                fxloop = data[30] # Hmmm!
                fxplay = data[34] if fxattr.pausable else None 
                speed = data[42] if fxattr.speedable else None
                length = data[43] if fxattr.sizeable else None
                direction = data[44] if fxattr.directional else None

                if self.is_sound_mode(mode):
                    if self.is_color_mode(mode) and fxattr.colorable:
                        rgb = rgb2
                    if  self.is_white_mode(mode) and fxattr.colorable:
                        white = data[36] if self.attr.white else None
                        cool = data[50] if self.attr.cct else None
                        warm = data[51] if self.attr.cct else None
                elif self.is_static_mode(mode) and coexistence:
                    white = data[36] if self.attr.white else None
                    cool = data[40] if self.attr.cct else None
                    warm = data[41] if self.attr.cct else None
                    rgb = rgb1
                    level = white if self.is_white_mode(mode) and white else data[35]
                elif self.is_white_mode(mode) and fxattr.colorable:
                    cool = data[40 if self.is_static_mode(mode) else 50] if self.attr.cct else None
                    warm = data[41 if self.is_static_mode(mode) else 51] if self.attr.cct else None
                    level = white = data[36] if self.attr.white else None
                elif self.is_color_mode(mode) and fxattr.colorable:
                    rgb = rgb1 if self.is_static_mode(mode) else rgb2
                    level = data[35]

        return UNILEDStatus(
            power=power,
            mode=mode,
            level=level,
            white=white,
            cool=cool,
            warm=warm,
            rgb=rgb,
            rgb2=rgb2,
            effect=effect,
            fxtype=fxtype,
            fxloop=fxloop,
            fxplay=fxplay,
            speed=speed,
            length=length,
            direction=direction,
            input=data[46],
            gain=data[45],
            chip_type=chip_type,
            chip_order=data[31],
            coexistence=coexistence,
            extra={
                "firmware": data[11:18].decode("utf-8"),
                "onoff_mode": data[20],
                "onoff_speed": data[21],
                "onoff_pixels": int.from_bytes(data[22:24], byteorder="big"), #data[22] + data[23],
                "power_on_state": data[25],
                "diy_mode": data[52],
            },
        )
    
    ##
    ## Channel Control
    ##
    def construct_power_change(
        self, channel: UNILEDChannel, turn_on: int
    ) -> bytearray | None:
        """The bytes to send for a state change"""
        return self.__encoder(0x50, bytearray([0x01 if turn_on else 0x00]))

    def construct_level_change(
        self, channel: UNILEDChannel, level: int
    ) -> bytearray | None:
        """The bytes to send for a brightness level change"""
        which = 0x00 if self.is_color_mode(channel.status.mode) else 0x01
        return self.__encoder(0x51, bytearray([which, level]))

    def construct_color_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int, white: int | None
    ) -> bytearray | None:
        """The bytes to send for a color level change"""
        if self.is_static_mode(channel.status.mode):
            level = channel.status.level
            if level is None:
                level = 0xFF
            return self.__encoder(0x52, bytearray([red, green, blue, level]))
        return self.__encoder(0x57, bytearray([red, green, blue]))

    def construct_mode_change(
        self, channel: UNILEDChannel, mode: int, effect: int | None = None
    ) -> list[bytearray] | None:
        """The bytes to send for a mode change."""
        if (fxlist := self.attr.dictof_mode_effects(mode)) is None:
            return None
        if effect is None:
            effect = channel.status.effect
        if mode != channel.status.mode:
            if effect not in fxlist:
                effect = next(iter(fxlist))
        return [ 
            self.__encoder(0x53, bytearray([mode, effect])),
            self.construct_status_query(channel.device),
        ]

    def construct_effect_change(
        self, channel: UNILEDChannel, effect: int, mode: int | None = None
    ) -> bytearray | None:
        """The bytes to send for an effect change"""
        if mode is None:
            mode = channel.status.mode
        return self.construct_mode_change(channel, mode, effect)

    def construct_effect_speed_change(
        self, channel: UNILEDChannel, speed: int
    ) -> bytearray | None:
        """The bytes to send for an effect speed change."""
        # 53 54 1b 01 00 01 0e
        return self.__encoder(0x54, bytearray([speed]))

    def construct_effect_length_change(
        self, channel: UNILEDChannel, length: int
    ) -> bytearray | None:
        """The bytes to send for an effect length change."""
        # 53 55 01 01 00 01 8a
        return self.__encoder(0x55, bytearray([length]))

    def construct_effect_direction_change(
        self, channel: UNILEDChannel, direction: int
    ) -> bytearray | None:
        """The bytes to send for an effect direction change."""
        # 53 56 ef 01 00 01 f0
        return self.__encoder(0x56, bytearray([direction]))

    def construct_effect_loop_change(
        self, channel: UNILEDChannel, loop: int
    ) -> bytearray | None:
        """The bytes to send to enable/disable looping effects."""
        # 53 58 f6 01 00 01 e9
        return self.__encoder(0x58, bytearray([loop]))

    def construct_effect_play_change(
        self, channel: UNILEDChannel, play: int
    ) -> bytearray | None:
        """The bytes to send to play/pause effects."""
        # 53 5d e2 01 00 01 fd
        return self.__encoder(0x5D, bytearray([play]))

    def construct_cct_change(
        self, channel: UNILEDChannel, kelvin: int, cool: int, warm: int, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a temperature color change."""
        if self.is_static_mode(channel.status.mode):
            return self.__encoder(0x61, bytearray([cool, warm]))
        return self.__encoder(0x60, bytearray([cool, warm]))

    ##
    ## Device Configuration
    ##   
    def construct_coexistence_change(
        self, channel: UNILEDChannel, coexist: int
    ) -> list[bytearray] | None:
        """The bytes to send for a coexistence change."""
        ## 53 0a a7 01 00 01 b8
        return self.__encoder(0x0A, bytearray([coexist]))

    def construct_chip_type_change(
        self, channel: UNILEDChannel, chip_type: int
    ) -> list[bytearray] | None:
        """The bytes to send for a chip type change"""
        # 53 6a 27 01 00 02 38 39    - Set Chip Type
        # 53 6b 01 01 00 01 1e       - Set Chip Order
        # 53 53 7c 01 00 02 67 62    - Resetting FX & Mode
        attr = self.dictof_chip_type_attributes(chip_type)
        if attr is not None:
            object.__setattr__(self, 'attr', attr)
            chip_order = channel.status.chip_order
            effect = channel.status.effect
            mode = channel.status.mode

            if channel.status.chip_order not in attr.order: 
                chip_order = next(iter(attr.order))               
            if attr.effects is not None:
                if channel.status.mode not in attr.effects: 
                    mode = next(iter(attr.effects))
                if (fxlist := self.attr.dictof_mode_effects(mode)) is not None:
                    if channel.status.effect not in fxlist:
                        effect = next(iter(fxlist))
            
            commands = []
            if (power := channel.status.power):
                commands.append(self.construct_power_change(channel, 0x00))
            commands.append(self.__encoder(0x6A, bytearray([0x01, chip_type & 0x7F])))
            commands.append(self.__encoder(0x6B, bytearray([chip_order])))
            commands.extend(self.construct_mode_change(channel, mode, effect))

        return commands

    def construct_chip_order_change(
        self, channel: UNILEDChannel, chip_order: int
    ) -> list[bytearray] | None:
        """The bytes to send for a chip order change"""
        return self.__encoder(0x6B, bytearray([chip_order]))

    def construct_input_change(
        self, channel: UNILEDChannel, input_type: int
    ) -> bytearray | None:
        """The bytes to send for an input change"""
        ## 53 59 c6 01 00 01 db
        return self.__encoder(0x59, bytearray([input_type]))

    def construct_input_gain_change(
        self, channel: UNILEDChannel, gain: int
    ) -> list[bytearray] | None:
        """The bytes to send for a gain/sensitivity change"""
        ## 53 5a 2d 01 00 01 30
        return self.__encoder(0x5A, bytearray([gain]))
    
    ##
    ## Helpers
    ##
    def dictof_chip_type_attributes(self, chip_type: int) -> dict | None:
        """Get chip type attributes"""
        if self.attr_dict is not None:
            if chip_type in self.attr_dict:
                return self.attr_dict[chip_type]
            if len(self.attr_dict) == 1:
                return next(iter(self.attr_dict))
        return _ATTRIBUTES()
    
    def is_static_mode(self, mode: int | None) -> bool:
        """Is a static mode """
        if (mode is not None) and mode in LISTOF_STATIC_MODES:
            return True
        return False

    def is_sound_mode(self, mode: int | None) -> bool:
        """Is a sound mode """
        if (mode is not None) and mode in LISTOF_SOUND_MODES:
            return True
        return False

    def is_color_mode(self, mode: int | None) -> bool:
        """Is a color mode """
        if (mode is not None) and mode in LISTOF_COLOR_MODES:
            return True
        return False

    def is_white_mode(self, mode: int | None) -> bool:
        """Is a white mode """
        if (mode is not None) and mode in LISTOF_WHITE_MODES:
            return True
        return False

    ##
    ## Device Configuration Informational
    ##   
    def dictof_channel_chip_types(self, channel: UNILEDChannel) -> dict | None:
        """Chip type dictionary"""
        chip_type = channel.status.chip_type
        if self.attr_dict is not None:
            return {
                chip_type: f"{self.attr_dict[chip_type].name}"
                for chip_type in self.attr_dict
            }
        return {chip_type: UNKNOWN}

    def dictof_channel_chip_orders(self, channel: UNILEDChannel) -> dict | None:
        """Chip order dictionary"""
        chip_order = channel.status.chip_order
        if self.attr is not None:
            if self.attr.order is not None:
                if chip_order in self.attr.order:
                    return self.attr.order
        return {chip_order: UNKNOWN}

    def dictof_channel_inputs(self, channel: UNILEDChannel) -> dict | None:
        """Inputs type dictionary"""
        input = channel.status.input
        if input in DICTOF_INPUTS:
            return DICTOF_INPUTS
        return {input: UNKNOWN}

    def rangeof_channel_input_gain(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        return RANGEOF_INPUT_GAIN

    def firmware(self, master: UNILEDChannel) -> str:
        """Returns the firmware version."""
        return master.status.extra.get("firmware", None)

    ##
    ## Effect Informational
    ##
    def dictof_channel_modes(self, channel: UNILEDChannel) -> dict | None:
        """Channel mode dictionary"""
        if self.attr is not None:
            if self.attr.effects is not None:
                modes = dict()
                for m in self.attr.effects:
                    modes[m] = DICTOF_MODES[m]
                return modes
        return None
    
    def dictof_channel_effects(self, channel: UNILEDChannel) -> dict | None:
        """Channel effects dictionary"""
        if self.attr is not None:
            mode = channel.status.mode
            if (fxlist := self.attr.dictof_mode_effects(mode)) is not None:
                effects = dict()
                for fx in fxlist:
                    effects[fx] = fxlist[fx].name
                return effects
        return None

    def codeof_channel_effect_type(
        self, channel: UNILEDChannel, effect: int | None = None, mode: int | None = None
    ) -> int | None:
        """Code of channel effect type from effect code"""
        if effect is None:
            effect = channel.status.effect
        if mode is None:
            mode = channel.status.mode
        if mode == MODE_CUSTOM_COLOR and self.attr.spi and effect == 0x01:
            return EFFECT_TYPE_STATIC
        if self.is_static_mode(mode):
            return EFFECT_TYPE_STATIC
        if self.is_sound_mode(mode):
            return EFFECT_TYPE_SOUND               
        return EFFECT_TYPE_DYNAMIC

    def nameof_channel_effect_type(
        self, channel: UNILEDChannel, fxtype: int | None = None
    ) -> str | None:
        """Name an effects type."""
        if fxtype is None:
            fxtype = channel.status.fxtype
        if channel.status.mode is None or fxtype is None:
            return None
        if fxtype in DICTOF_EFFECT_TYPES:
            return DICTOF_EFFECT_TYPES[fxtype]
        return f"{UNKNOWN} ({fxtype})"

    def rangeof_channel_effect_speed(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        return RANGEOF_EFFECT_SPEED

    def rangeof_channel_effect_length(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect length (min,max,step)."""
        return RANGEOF_EFFECT_LENGTH

##
## Chip Type Attributes
##
class _81_ATTRIBUTES(_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "1 CH PWM - Single Color"
        self.pwm = True
        self.white = True
        self.effects = {
            MODE_STATIC_WHITE: DICTOF_EFFECTS_STATIC_WHITE,
            MODE_DYNAMIC_WHITE: DICTOF_PWM_EFFECTS_DYNAMIC_WHITE,
            MODE_SOUND_WHITE: DICTOF_PWM_EFFECTS_SOUND_WHITE,
        }

class _83_ATTRIBUTES(_81_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "2 CH PWM - CCT"
        self.cct = True
        self.order = DICTOF_ORDER_CW

class _85_ATTRIBUTES(_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "3 CH PWM - RGB"
        self.pwm = True
        self.hue = True
        self.order = DICTOF_ORDER_RGB
        self.effects = {
            MODE_STATIC_COLOR: DICTOF_EFFECTS_STATIC_COLOR,
            MODE_DYNAMIC_COLOR: DICTOF_PWM_EFFECTS_DYNAMIC_COLOR,
            MODE_SOUND_COLOR: DICTOF_PWM_EFFECTS_SOUND_COLOR,
            MODE_CUSTOM_COLOR: DICTOF_PWM_EFFECTS_CUSTOM_COLOR,
        }

class _87_ATTRIBUTES(_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "4 CH PWM - RGBW"
        self.pwm = True
        self.hue = True
        self.white = True
        self.coexistence = True
        self.order = DICTOF_ORDER_RGBW
        self.effects = {
            MODE_STATIC_COLOR: DICTOF_EFFECTS_STATIC_COLOR,
            MODE_STATIC_WHITE: DICTOF_EFFECTS_STATIC_WHITE,
            MODE_DYNAMIC_COLOR: DICTOF_PWM_EFFECTS_DYNAMIC_COLOR,
            MODE_DYNAMIC_WHITE: DICTOF_PWM_EFFECTS_DYNAMIC_WHITE,
            MODE_SOUND_COLOR: DICTOF_PWM_EFFECTS_SOUND_COLOR,
            MODE_SOUND_WHITE: DICTOF_PWM_EFFECTS_SOUND_WHITE,
            MODE_CUSTOM_COLOR: DICTOF_PWM_EFFECTS_CUSTOM_COLOR,
        }

class _8A_ATTRIBUTES(_87_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "5 CH PWM - RGBCCT"
        self.cct = True
        self.order = DICTOF_ORDER_RGBCW

class _82_ATTRIBUTES(_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "SPI - Single Color"
        self.spi = True
        self.white = True
        self.order = DICTOF_ORDER_123
        self.effects = {
            MODE_STATIC_WHITE: DICTOF_EFFECTS_STATIC_WHITE,
            MODE_DYNAMIC_WHITE: DICTOF_SPI_EFFECTS_DYNAMIC_WHITE,
            MODE_SOUND_WHITE: DICTOF_SPI_EFFECTS_SOUND_WHITE,
        }

class _84_ATTRIBUTES(_82_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "SPI - CCT1"
        self.cct = True
        self.order = DICTOF_ORDER_CWO

class _8D_ATTRIBUTES(_84_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "SPI - CCT2"
        self.order = DICTOF_ORDER_CW

class _86_ATTRIBUTES(_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGB"
        self.spi = True
        self.hue = True
        self.order = DICTOF_ORDER_RGB
        self.effects = {
            MODE_STATIC_COLOR: DICTOF_EFFECTS_STATIC_COLOR,
            MODE_DYNAMIC_COLOR: DICTOF_SPI_EFFECTS_DYNAMIC_COLOR,
            MODE_SOUND_COLOR: DICTOF_SPI_EFFECTS_SOUND_COLOR,
            MODE_CUSTOM_COLOR: DICTOF_SPI_EFFECTS_CUSTOM_COLOR,
        }

class _88_ATTRIBUTES(_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGBW"
        self.spi = True
        self.hue = True
        self.white = True
        self.coexistence = True
        self.order = DICTOF_ORDER_RGBW
        self.effects = {
            MODE_STATIC_COLOR: DICTOF_EFFECTS_STATIC_COLOR,
            MODE_STATIC_WHITE: DICTOF_EFFECTS_STATIC_WHITE,
            MODE_DYNAMIC_COLOR: DICTOF_SPI_EFFECTS_DYNAMIC_COLOR,
            MODE_DYNAMIC_WHITE: DICTOF_SPI_EFFECTS_DYNAMIC_WHITE,
            MODE_SOUND_COLOR: DICTOF_SPI_EFFECTS_SOUND_COLOR,
            MODE_SOUND_WHITE: DICTOF_SPI_EFFECTS_SOUND_WHITE,
            MODE_CUSTOM_COLOR: DICTOF_SPI_EFFECTS_CUSTOM_COLOR,
        }

class _8B_ATTRIBUTES(_88_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGBCCT (1)"
        self.cct = True
        self.coexistence = True
        self.order = DICTOF_ORDER_RGBCW

class _8E_ATTRIBUTES(_8B_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGBCCT (2)"

class _89_ATTRIBUTES(_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGB + 1 CH PWM"
        self.pwm = True
        self.spi = True
        self.hue = True
        self.white = True
        self.coexistence = True
        self.order = DICTOF_ORDER_RGB
        self.effects = {
            MODE_STATIC_COLOR: DICTOF_EFFECTS_STATIC_COLOR,
            MODE_STATIC_WHITE: DICTOF_EFFECTS_STATIC_WHITE,
            MODE_DYNAMIC_COLOR: DICTOF_SPI_EFFECTS_DYNAMIC_COLOR,
            MODE_DYNAMIC_WHITE: DICTOF_PWM_EFFECTS_DYNAMIC_WHITE,
            MODE_SOUND_COLOR: DICTOF_SPI_EFFECTS_SOUND_COLOR,
            MODE_SOUND_WHITE: DICTOF_PWM_EFFECTS_SOUND_WHITE,
            MODE_CUSTOM_COLOR: DICTOF_SPI_EFFECTS_CUSTOM_COLOR,
        }

class _8C_ATTRIBUTES(_89_ATTRIBUTES):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGB + 2 CH PWM"
        self.cct = True
        self.order = DICTOF_ORDER_RGBCW

##
## SP630E
##
SP630E = _MODEL(
    model_type=UNILEDModelType.STRIP,
    model_name=BANLANX4_MODEL_NAME_SP630E,
    model_num=BANLANX4_MODEL_NUMBER_SP630E,
    description="BLE RGB(CW) (Music) Pixel/PWM Controller",
    manufacturer=BANLANX4_MANUFACTURER,
    manufacturer_id=BANLANX4_MANUFACTURER_ID,
    manufacturer_data=b"\x1f\x10",
    resolve_protocol=False,
    channels=1,
    needs_on=True,
    needs_type_reload=True,
    effects_directional=True,
    effects_pausable=True,
    effects_loopable=True,
    sends_status_on_commands=False,
    local_names=[BANLANX4_LOCAL_NAME_SP630E],
    service_uuids=BANLANX4_UUID_SERVICE,
    write_uuids=BANLANX4_UUID_WRITE,
    read_uuids=BANLANX4_UUID_READ,
    attr_dict = {
        0x81: _81_ATTRIBUTES(), # 1 CH PWM Single Color
        0x83: _83_ATTRIBUTES(), # 2 CH PWM CCT
        0x85: _85_ATTRIBUTES(), # 3 CH PWM RGB
        0x87: _87_ATTRIBUTES(), # 4 CH PWM RGBW - Coexist
        0x8A: _8A_ATTRIBUTES(), # 5 CH PWM RGBCCT - Coexist
        0x82: _82_ATTRIBUTES(), # SPI - Single Color
        0x84: _84_ATTRIBUTES(), # SPI - CCT (1)
        0x8D: _8D_ATTRIBUTES(), # SPI - CCT (2)
        0x86: _86_ATTRIBUTES(), # SPI - RGB
        0x88: _88_ATTRIBUTES(), # SPI - RGBW - Coexist
        0x8B: _8B_ATTRIBUTES(), # SPI - RGBCCT (1) - Coexist
        0x8E: _8E_ATTRIBUTES(), # SPI - RGBCCT (2) - Coexist
        0x89: _89_ATTRIBUTES(), # SPI - RGB + 1 CH PWM - Coexist
        0x8C: _8C_ATTRIBUTES(), # SPI - RGB + 2 CH PWM - Coexist
    }
)

##
## SP642E
##
SP642E = _MODEL(
    model_type=UNILEDModelType.STRIP,
    model_name=BANLANX4_MODEL_NAME_SP642E,
    model_num=BANLANX4_MODEL_NUMBER_SP642E,
    description="BLE CCT (Music) PWM Controller",
    manufacturer=BANLANX4_MANUFACTURER,
    manufacturer_id=BANLANX4_MANUFACTURER_ID,
    manufacturer_data=b"\x4a\x10",
    resolve_protocol=False,
    channels=1,
    needs_on=True,
    needs_type_reload=False,
    effects_directional=True,
    effects_pausable=True,
    effects_loopable=True,
    sends_status_on_commands=False,
    local_names=[BANLANX4_LOCAL_NAME_SP648E],
    service_uuids=BANLANX4_UUID_SERVICE,
    write_uuids=BANLANX4_UUID_WRITE,
    read_uuids=BANLANX4_UUID_READ,
    attr_dict = {
        0x03: _83_ATTRIBUTES(), # 2 CH PWM CCT
    },
)

##
## SP648E
##
SP648E = _MODEL(
    model_type=UNILEDModelType.STRIP,
    model_name=BANLANX4_MODEL_NAME_SP648E,
    model_num=BANLANX4_MODEL_NUMBER_SP648E,
    description="BLE RGB (Music) Pixel Controller",
    manufacturer=BANLANX4_MANUFACTURER,
    manufacturer_id=BANLANX4_MANUFACTURER_ID,
    manufacturer_data=b"\x33\x10",
    resolve_protocol=False,
    channels=1,
    needs_on=True,
    needs_type_reload=True,
    effects_directional=True,
    effects_pausable=True,
    effects_loopable=True,
    sends_status_on_commands=False,
    local_names=[BANLANX4_LOCAL_NAME_SP648E],
    service_uuids=BANLANX4_UUID_SERVICE,
    write_uuids=BANLANX4_UUID_WRITE,
    read_uuids=BANLANX4_UUID_READ,
    attr_dict = {
        0x06: _86_ATTRIBUTES(), # SPI RGB
    },
)
