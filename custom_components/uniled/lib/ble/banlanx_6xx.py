"""UniLED BLE Devices - SP LED (BanlanX SP630E)"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Final

from ..const import *  # I know!
from ..channel import UniledChannel
from ..features import (
    UniledAttribute,
    LightStripFeature,
    EffectTypeFeature,
    EffectLoopFeature,
    EffectPlayFeature,
    EffectSpeedFeature,
    EffectLengthFeature,
    EffectDirectionFeature,
    AudioInputFeature,
    AudioSensitivityFeature,
    LightModeFeature,
    LightTypeFeature,
    ChipOrderFeature,
    OnOffEffectFeature,
    OnOffSpeedFeature,
    OnOffPixelsFeature,
    CoexistenceFeature,
    OnPowerFeature,
)
from ..effects import (
    UNILEDEffectType,
    UNILEDEffects,
)
from ..chips import (
    UNILED_CHIP_ORDER_CW,
    UNILED_CHIP_ORDER_123,
    UNILED_CHIP_ORDER_CWX,
    UNILED_CHIP_ORDER_RGB,
    UNILED_CHIP_ORDER_RGBW,
    UNILED_CHIP_ORDER_RGBCW,
)
from .device import (
    UUID_BASE_FORMAT as BANLANX6XX_UUID_FORMAT,
    ParseNotificationError,
    UniledBleDevice,
    UniledBleModel,
    BLEDevice,
    AdvertisementData,
)
import logging

_LOGGER = logging.getLogger(__name__)

BANLANX6XX_MANUFACTURER: Final = "SPLED (BanlanX)"
BANLANX6XX_MANUFACTURER_ID: Final = 20563
BANLANX6XX_UUID_SERVICE = [
    BANLANX6XX_UUID_FORMAT.format(part) for part in ["e0ff", "ffe0"]
]
BANLANX6XX_UUID_WRITE = [BANLANX6XX_UUID_FORMAT.format(part) for part in ["ffe1"]]
BANLANX6XX_UUID_READ = []

DICTOF_ONOFF_EFFECTS: Final = {
    0x01: UNILEDEffects.FLOW_FORWARD,
    0x02: UNILEDEffects.FLOW_BACKWARD,
    0x03: UNILEDEffects.GRADIENT,
    0x04: UNILEDEffects.STARS,
}

DICTOF_ONOFF_SPEEDS: Final = {
    0x01: "Slow",
    0x02: "Medium",
    0x03: "Fast",
}

MIN_ONOFF_PIXELS: Final = 1
MAX_ONOFF_PIXELS: Final = 600

DICTOF_ON_POWER_STATES: Final = {
    0x00: "Light Off",
    0x01: "Light On",
    0x02: "Last state",
}

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

LISTOF_DYNAMIC_MODES: Final = [
    MODE_DYNAMIC_COLOR,
    MODE_DYNAMIC_WHITE,
]

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

LISTOF_LOOPABLE_MODES: Final = [
    MODE_DYNAMIC_COLOR,
    MODE_DYNAMIC_WHITE,
    MODE_SOUND_COLOR,
    MODE_SOUND_WHITE,
]


@dataclass(frozen=True)
class _FX_STATIC:
    """BanlanX Effect and Attributes"""

    name: str
    colorable: bool = True
    sizeable: bool = False
    directional: bool = False
    pausable: bool = False
    speedable: bool = False


@dataclass(frozen=True)
class _FX_DYNAMIC:
    """BanlanX Effect and Attributes"""

    name: str
    colorable: bool = False
    sizeable: bool = False
    directional: bool = False
    pausable: bool = False
    speedable: bool = True


@dataclass(frozen=True)
class _FX_SOUND:
    """BanlanX Sound Effect and Attributes"""

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
    0x02: _FX_SOUND(UNILEDEffects.SOUND_MUSIC_MONO_BREATH, True),
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
    0x24: _FX_DYNAMIC(
        UNILEDEffects.GRADUAL_SNAKE_GREEN_YELLOW, False, True, True, True
    ),
    0x25: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_GREEN_CYAN, False, True, True, True),
    0x26: _FX_DYNAMIC(
        UNILEDEffects.GRADUAL_SNAKE_GREEN_PURPLE, False, True, True, True
    ),
    0x27: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_GREEN_WHITE, False, True, True, True),
    0x28: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_BLUE_YELLOW, False, True, True, True),
    0x29: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_BLUE_CYAN, False, True, True, True),
    0x2A: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_BLUE_PURPLE, False, True, True, True),
    0x2B: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_BLUE_WHITE, False, True, True, True),
    0x2C: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_YELLOW_CYAN, False, True, True, True),
    0x2D: _FX_DYNAMIC(
        UNILEDEffects.GRADUAL_SNAKE_YELLOW_PURPLE, False, True, True, True
    ),
    0x2E: _FX_DYNAMIC(
        UNILEDEffects.GRADUAL_SNAKE_YELLOW_WHITE, False, True, True, True
    ),
    0x2F: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_CYAN_PURPLE, False, True, True, True),
    0x30: _FX_DYNAMIC(UNILEDEffects.GRADUAL_SNAKE_CYAN_WHITE, False, True, True, True),
    0x31: _FX_DYNAMIC(
        UNILEDEffects.GRADUAL_SNAKE_PURPLE_WHITE, False, True, True, True
    ),
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

MIN_CUSTOM_SLOT_PIXELS: Final = 0
MAX_CUSTOM_SLOT_PIXELS: Final = 150

MAX_EFFECT_SPEED: Final = 10
MAX_EFFECT_LENGTH: Final = 150
MAX_SENSITIVITY: Final = 16

DICTOF_AUDIO_INPUTS: Final = {
    0x00: UNILED_AUDIO_INPUT_INTMIC,
    0x01: UNILED_AUDIO_INPUT_PLAYER,
    0x02: UNILED_AUDIO_INPUT_EXTMIC,
}


##
## BanlanX Configurations
##
class _CONFIG:
    """BanlanX Light Type Configuration"""

    def __init__(self):
        self.name = str(UNILED_UNKNOWN)
        self.pwm = bool(False)
        self.spi = bool(False)
        self.hue = bool(False)
        self.cct = bool(False)
        self.white = bool(False)
        self.order = None
        self.effects = None
        self.coexistence = bool(False)

    def dictof_mode_effects(self, mode: int | None) -> dict | None:
        """Mode effects dictionary"""
        if mode is not None and self.effects is not None:
            if mode in self.effects:
                return self.effects[mode]
        return None

    def dictof_channel_effects(self, mode) -> dict | None:
        """Channel effects dictionary"""
        if (fxlist := self.dictof_mode_effects(mode)) is not None:
            effects = dict()
            for fx in fxlist:
                effects[fx] = fxlist[fx].name
            return effects


##
## Light Type Configurations
##
class CFG_81(_CONFIG):
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


class CFG_83(CFG_81):
    def __init__(self):
        super().__init__()
        self.name = "2 CH PWM - CCT"
        self.cct = True
        self.order = UNILED_CHIP_ORDER_CW


class CFG_85(_CONFIG):
    def __init__(self):
        super().__init__()
        self.name = "3 CH PWM - RGB"
        self.pwm = True
        self.hue = True
        self.order = UNILED_CHIP_ORDER_RGB
        self.effects = {
            MODE_STATIC_COLOR: DICTOF_EFFECTS_STATIC_COLOR,
            MODE_DYNAMIC_COLOR: DICTOF_PWM_EFFECTS_DYNAMIC_COLOR,
            MODE_SOUND_COLOR: DICTOF_PWM_EFFECTS_SOUND_COLOR,
            MODE_CUSTOM_COLOR: DICTOF_PWM_EFFECTS_CUSTOM_COLOR,
        }


class CFG_87(_CONFIG):
    def __init__(self):
        super().__init__()
        self.name = "4 CH PWM - RGBW"
        self.pwm = True
        self.hue = True
        self.white = True
        self.coexistence = True
        self.order = UNILED_CHIP_ORDER_RGBW
        self.effects = {
            MODE_STATIC_COLOR: DICTOF_EFFECTS_STATIC_COLOR,
            MODE_STATIC_WHITE: DICTOF_EFFECTS_STATIC_WHITE,
            MODE_DYNAMIC_COLOR: DICTOF_PWM_EFFECTS_DYNAMIC_COLOR,
            MODE_DYNAMIC_WHITE: DICTOF_PWM_EFFECTS_DYNAMIC_WHITE,
            MODE_SOUND_COLOR: DICTOF_PWM_EFFECTS_SOUND_COLOR,
            MODE_SOUND_WHITE: DICTOF_PWM_EFFECTS_SOUND_WHITE,
            MODE_CUSTOM_COLOR: DICTOF_PWM_EFFECTS_CUSTOM_COLOR,
        }


class CFG_8A(CFG_87):
    def __init__(self):
        super().__init__()
        self.name = "5 CH PWM - RGBCCT"
        self.cct = True
        self.order = UNILED_CHIP_ORDER_RGBCW


class CFG_82(_CONFIG):
    def __init__(self):
        super().__init__()
        self.name = "SPI - Single Color"
        self.spi = True
        self.white = True
        self.order = UNILED_CHIP_ORDER_123
        self.effects = {
            MODE_STATIC_WHITE: DICTOF_EFFECTS_STATIC_WHITE,
            MODE_DYNAMIC_WHITE: DICTOF_SPI_EFFECTS_DYNAMIC_WHITE,
            MODE_SOUND_WHITE: DICTOF_SPI_EFFECTS_SOUND_WHITE,
        }


class CFG_84(CFG_82):
    def __init__(self):
        super().__init__()
        self.name = "SPI - CCT1"
        self.cct = True
        self.order = UNILED_CHIP_ORDER_CWX


class CFG_8D(CFG_84):
    def __init__(self):
        super().__init__()
        self.name = "SPI - CCT2"
        self.order = UNILED_CHIP_ORDER_CWX


class CFG_86(_CONFIG):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGB"
        self.spi = True
        self.hue = True
        self.order = UNILED_CHIP_ORDER_RGB
        self.effects = {
            MODE_STATIC_COLOR: DICTOF_EFFECTS_STATIC_COLOR,
            MODE_DYNAMIC_COLOR: DICTOF_SPI_EFFECTS_DYNAMIC_COLOR,
            MODE_SOUND_COLOR: DICTOF_SPI_EFFECTS_SOUND_COLOR,
            MODE_CUSTOM_COLOR: DICTOF_SPI_EFFECTS_CUSTOM_COLOR,
        }


class CFG_88(_CONFIG):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGBW"
        self.spi = True
        self.hue = True
        self.white = True
        self.coexistence = True
        self.order = UNILED_CHIP_ORDER_RGBW
        self.effects = {
            MODE_STATIC_COLOR: DICTOF_EFFECTS_STATIC_COLOR,
            MODE_STATIC_WHITE: DICTOF_EFFECTS_STATIC_WHITE,
            MODE_DYNAMIC_COLOR: DICTOF_SPI_EFFECTS_DYNAMIC_COLOR,
            MODE_DYNAMIC_WHITE: DICTOF_SPI_EFFECTS_DYNAMIC_WHITE,
            MODE_SOUND_COLOR: DICTOF_SPI_EFFECTS_SOUND_COLOR,
            MODE_SOUND_WHITE: DICTOF_SPI_EFFECTS_SOUND_WHITE,
            MODE_CUSTOM_COLOR: DICTOF_SPI_EFFECTS_CUSTOM_COLOR,
        }


class CFG_8B(CFG_88):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGBCCT (1)"
        self.cct = True
        self.coexistence = True
        self.order = UNILED_CHIP_ORDER_RGBCW


class CFG_8E(CFG_8B):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGBCCT (2)"


class CFG_89(_CONFIG):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGB + 1 CH PWM"
        self.pwm = True
        self.spi = True
        self.hue = True
        self.white = True
        self.coexistence = True
        self.order = UNILED_CHIP_ORDER_RGB
        self.effects = {
            MODE_STATIC_COLOR: DICTOF_EFFECTS_STATIC_COLOR,
            MODE_STATIC_WHITE: DICTOF_EFFECTS_STATIC_WHITE,
            MODE_DYNAMIC_COLOR: DICTOF_SPI_EFFECTS_DYNAMIC_COLOR,
            MODE_DYNAMIC_WHITE: DICTOF_PWM_EFFECTS_DYNAMIC_WHITE,
            MODE_SOUND_COLOR: DICTOF_SPI_EFFECTS_SOUND_COLOR,
            MODE_SOUND_WHITE: DICTOF_PWM_EFFECTS_SOUND_WHITE,
            MODE_CUSTOM_COLOR: DICTOF_SPI_EFFECTS_CUSTOM_COLOR,
        }


class CFG_8C(CFG_89):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGB + 2 CH PWM"
        self.cct = True
        self.order = UNILED_CHIP_ORDER_RGBCW


##
## Device Signatures
##
dataclass(frozen=True)


class Signature:
    info: str
    conf: Any  # dict(int, Any)
    ids: dict(int, str)


dataclass(frozen=True)


class SP630E(Signature):
    info = "RGB(CW) SPI/PWM (Music) Controller"
    conf = {
        0x81: CFG_81(),  # PWM Mono
        0x83: CFG_83(),  # PWM CCT
        0x85: CFG_85(),  # PWM RGB
        0x87: CFG_87(),  # PWM RGBW
        0x8A: CFG_8A(),  # PWM RGBCCT
        0x82: CFG_82(),  # SPI - Mono
        0x84: CFG_84(),  # SPI - CCT (1)
        0x8D: CFG_8D(),  # SPI - CCT (2)
        0x86: CFG_86(),  # SPI - RGB
        0x88: CFG_88(),  # SPI - RGBW
        0x8B: CFG_8B(),  # SPI - RGBCCT (1)
        0x8E: CFG_8E(),  # SPI - RGBCCT (2)
        0x89: CFG_89(),  # SPI - RGB + 1 CH PWM
        0x8C: CFG_8C(),  # SPI - RGB + 2 CH PWM
    }
    ids = {
        0x1F: "SP630E",
    }


dataclass(frozen=True)


class SP631E_SP641E_SP651E(Signature):
    info = "PWM Single Color (Music) Controller"
    conf = {
        0x01: CFG_81(),
    }
    ids = {
        0x20: "SP631E",
        0x2C: "SP641E",
        0x38: "SP651E",
    }


dataclass(frozen=True)


class SP632E_SP642E_SP652E(Signature):
    info = "PWM CCT (Music) Controller"
    conf = {
        0x03: CFG_83(),
    }
    ids = {0x21: "SP632E", 0x2D: "SP642E", 0x39: "SP652E"}


dataclass(frozen=True)


class SP633E_SP643E_SP653E(Signature):
    info = "PWM RGB (Music) Controller"
    conf = {
        0x05: CFG_85(),
    }
    ids = {0x22: "SP633E", 0x2E: "SP643E", 0x3A: "SP653E"}


dataclass(frozen=True)


class SP634E_SP644E_SP654E(Signature):
    info = "PWM RGBW (Music) Controller"
    conf = {
        0x07: CFG_87(),
    }
    ids = {0x23: "SP634E", 0x2F: "SP644E", 0x3B: "SP654E"}


dataclass(frozen=True)


class SP635E_SP645E_SP655E(Signature):
    info = "PWM RGBCCT (Music) Controller"
    conf = {
        0x0A: CFG_8A(),
    }
    ids = {0x24: "SP635E", 0x30: "SP645E", 0x3C: "SP655E"}


dataclass(frozen=True)


class SP636E_SP646E_SP656E(Signature):
    info = "SPI Single Color (Music) Controller"
    conf = {
        0x02: CFG_82(),
    }
    ids = {0x25: "SP636E", 0x31: "SP646E", 0x3D: "SP656E"}


dataclass(frozen=True)


class SP637E_SP647E_SP657E(Signature):
    info = "SPI CCT (Music) Controller"
    conf = {0x04: CFG_84(), 0x0D: CFG_8D()}
    ids = {0x26: "SP637E", 0x32: "SP647E", 0x3E: "SP657E"}


dataclass(frozen=True)


class SP638E_SP648E_SP658E(Signature):
    info = "SPI RGB (Music) Controller"
    conf = {
        0x06: CFG_86(),
    }
    ids = {0x27: "SP638E", 0x33: "SP648E", 0x3F: "SP658E"}


dataclass(frozen=True)


class SP639E_SP649E_SP659E(Signature):
    info = "SPI RGBW (Music) Controller"
    conf = {
        0x08: CFG_88(),
    }
    ids = {0x28: "SP639E", 0x34: "SP649E", 0x40: "SP659E"}


dataclass(frozen=True)


class SP63AE_SP64AE_SP65AE(Signature):
    info = "SPI RGBCCT (Music) Controller"
    conf = {
        0x0B: CFG_8B(),
        0x0E: CFG_8E(),
    }
    ids = {0x29: "SP63AE", 0x35: "SP64AE", 0x41: "SP65AE"}


MODEL_SIGNATURE_LIST: Final = [
    SP630E,
    SP631E_SP641E_SP651E,
    SP632E_SP642E_SP652E,
    SP633E_SP643E_SP653E,
    SP634E_SP644E_SP654E,
    SP635E_SP645E_SP655E,
    SP636E_SP646E_SP656E,
    SP637E_SP647E_SP657E,
    SP638E_SP648E_SP658E,
    SP639E_SP649E_SP659E,
    SP63AE_SP64AE_SP65AE,
]


##
## BanlanX SP63XE Proxy Model
##
class SP6xxEProxy(UniledBleModel):
    """BanlanX SP6xxE Proxy Model"""

    def match_ble_model(self, model: str) -> UniledBleModel | None:
        for signature in MODEL_SIGNATURE_LIST:
            for id, name in signature.ids.items():
                if model != name:
                    continue
                return BanlanX6xx(
                    id=id, name=name, info=signature.info, conf=signature.conf
                )
        return None

    def match_ble_device(
        self, device: BLEDevice, advertisement: AdvertisementData | None = None
    ) -> UniledBleModel | None:
        """Match to one of the SP6xxE devices"""
        if not hasattr(advertisement, "manufacturer_data"):
            return None
        for mid, data in advertisement.manufacturer_data.items():
            if mid != self.ble_manufacturer_id or data[1] != 0x10:
                continue
            for signature in MODEL_SIGNATURE_LIST:
                for id, name in signature.ids.items():
                    if id != data[0]:
                        continue
                    return BanlanX6xx(
                        id=id, name=name, info=signature.info, conf=signature.conf
                    )
        return None

    def __init__(self, id: int, name: str, info: str):
        """Initialise class"""
        super().__init__(
            model_num=id,
            model_name=name,
            description=info,
            manufacturer=BANLANX6XX_MANUFACTURER,
            channels=1,
            ble_manufacturer_id=BANLANX6XX_MANUFACTURER_ID,
            ble_service_uuids=BANLANX6XX_UUID_SERVICE,
            ble_write_uuids=BANLANX6XX_UUID_WRITE,
            ble_read_uuids=BANLANX6XX_UUID_READ,
            ble_notify_uuids=[],
            ble_manufacturer_data=bytearray([id & 0xFF, 0x10]),
        )


##
## BanlanX SP6xxE Protocol Implementation
##
class BanlanX6xx(SP6xxEProxy):
    """BanlanX SP630E Protocol Implementation"""

    _HEADER_LENGTH = 6
    _HEADER_BYTE = 0x53
    _MESSAGE_TYPE = 1
    _MESSAGE_KEY = 2
    _MESSAGE_LENGTH = 5
    _DEVICE_STATUS = 0x02

    configs: dict(int, _CONFIG) | None

    def __init__(self, id: int, name: str, info: str, conf: dict(int, _CONFIG)):
        """Initialise class"""
        super().__init__(id, name, info)
        self.configs = conf

    def __decoder(self, encoded: bytearray) -> bytearray | None:
        """Decode BanlanX Message."""

        packet_length = len(encoded)
        if packet_length < self._HEADER_LENGTH:
            raise ParseNotificationError("Packet is undersized")

        if encoded[0] != self._HEADER_BYTE:
            raise ParseNotificationError("Packet is invalid")

        message_length = encoded[self._MESSAGE_LENGTH]
        expected_length = message_length + self._HEADER_LENGTH

        if packet_length != expected_length:
            raise ParseNotificationError(
                f"Packet payload size mismatch: {packet_length} vs {expected_length}"
            )

        message_key = encoded[self._MESSAGE_KEY]
        if not message_key:
            return encoded

        raise ParseNotificationError("Encoded packet - currently unsupported")

    def __encoder(self, cmd: int, data: bytearray) -> bytearray:
        """Encode BanlanX Message."""
        key = 0x00
        bytes = len(data) & 0xFF
        encoded = bytearray([self._HEADER_BYTE, cmd & 0xFF, key, 0x01, 0x00, bytes])
        for b in range(bytes):
            c = data[b]
            encoded.append(c)
        encoded[self._MESSAGE_KEY] = key & 0xFF
        return encoded

    def parse_notifications(
        self,
        device: UniledBleDevice,
        sender: int,
        data: bytearray,
    ) -> bool:
        """Parse notification message(s)"""
        data = self.__decoder(data)

        if data[self._MESSAGE_TYPE] != self._DEVICE_STATUS:
            # raise ParseNotificationError("Invalid Packet!")
            _LOGGER.warning("Invalid Packet!")
            return False

        cfg: _CONFIG = self.match_light_type_config(data[19])
        device.master.context = cfg
        if not cfg:
            raise ParseNotificationError("Missing light type config!")

        firmware = data[11:18].decode("utf-8")
        onoff_effect = self.str_if_key_in(data[20], DICTOF_ONOFF_EFFECTS)
        onoff_speed = self.str_if_key_in(data[21], DICTOF_ONOFF_SPEEDS)
        onoff_pixels = int.from_bytes(data[22:24], byteorder="big")
        on_power = self.str_if_key_in(data[25], DICTOF_ON_POWER_STATES)
        coexistence = data[24] if cfg.coexistence else None
        power = True if data[29] > 0x00 else False
        mode = data[32]
        effect = data[33]
        play = data[34]
        color_level = data[35]
        white_level = data[36]
        speed = data[42]
        length = data[43]
        direction = data[44]
        gain = data[45]
        input = data[46]

        device.master.status.replace(
            {
                "chip_order_number": data[31],
                "diy_mode": data[52],
                "debug_extra": bytearray([data[8], data[10], data[26], data[28]]),
                ATTR_UL_DEVICE_FORCE_REFRESH: True,
                ATTR_UL_INFO_FIRMWARE: firmware,
                ATTR_UL_ONOFF_EFFECT: onoff_effect,
                ATTR_UL_ONOFF_SPEED: onoff_speed,
                ATTR_UL_ONOFF_PIXELS: onoff_pixels,
                ATTR_UL_ON_POWER: on_power,
                ATTR_UL_POWER: power,
                ATTR_UL_LIGHT_MODE_NUMBER: mode,
                ATTR_UL_LIGHT_MODE: UNILED_UNKNOWN
                if mode not in DICTOF_MODES
                else DICTOF_MODES[mode],
                ATTR_UL_EFFECT_NUMBER: effect,
                ATTR_UL_EFFECT: UNILED_UNKNOWN,
                ATTR_UL_EFFECT_TYPE: UNILED_UNKNOWN,
            }
        )

        if (fxlist := cfg.dictof_mode_effects(mode)) is not None:
            if fxattr := None if effect not in fxlist else fxlist[effect]:
                # _LOGGER.warn("%s: FXATTR: (%s) %s", device.name, cfg.name, fxattr)
                device.master.set(ATTR_HA_EFFECT, str(fxattr.name))

                device.master.set(
                    ATTR_UL_EFFECT_TYPE,
                    str(self.match_channel_effect_type(device.master, effect, mode)),
                )
                device.master.set(
                    ATTR_UL_EFFECT_LOOP,
                    bool(data[30]) if self.is_loop_mode(mode) else None,
                )
                device.master.set(
                    ATTR_UL_EFFECT_PLAY, bool(play) if fxattr.pausable else None
                )
                device.master.set(
                    ATTR_UL_EFFECT_SPEED, speed if fxattr.speedable else None
                )
                device.master.set(
                    ATTR_UL_EFFECT_LENGTH, length if fxattr.sizeable else None
                )
                device.master.set(
                    ATTR_UL_EFFECT_DIRECTION,
                    bool(direction) if fxattr.directional else None,
                )

                audio_input = (
                    self.str_if_key_in(input, DICTOF_AUDIO_INPUTS)
                    if power and self.is_sound_mode(mode)
                    else None
                )
                device.master.set(ATTR_UL_AUDIO_INPUT, audio_input)
                device.master.set(
                    ATTR_UL_SENSITIVITY, gain if audio_input is not None else None
                )

                if self.is_sound_mode(mode):
                    # In sound modes, irrespective of coexistence setting
                    # the color and white(s) are separatly controlled when
                    # supported by the effect, but brightness changes are
                    # not supported.
                    #
                    if self.is_white_mode(mode) and fxattr.colorable and cfg.cct:
                        device.master.set(ATTR_HA_BRIGHTNESS, 255)
                        device.master.set(ATTR_HA_WHITE, 255)
                        device.master.set(
                            ATTR_UL_CCT_COLOR, (data[50], data[51], 255, None)
                        )
                    elif self.is_color_mode(mode) and fxattr.colorable and cfg.hue:
                        device.master.set(ATTR_HA_BRIGHTNESS, 255)
                        device.master.set(
                            ATTR_HA_RGB_COLOR, (data[47], data[48], data[49])
                        )
                elif self.is_dynamic_mode(mode):
                    # In dynamic modes, irrespective of coexistence setting
                    # the color and white(s) are separatly controlled when
                    # supported by the effect, brightness changes are also
                    # supported.
                    #
                    if self.is_white_mode(mode) and fxattr.colorable and cfg.cct:
                        device.master.set(
                            ATTR_UL_CCT_COLOR, (data[50], data[51], white_level, None)
                        )
                    elif self.is_color_mode(mode) and fxattr.colorable and cfg.hue:
                        device.master.set(
                            ATTR_HA_RGB_COLOR, (data[47], data[48], data[49])
                        )
                    device.master.set(
                        ATTR_HA_BRIGHTNESS,
                        white_level if self.is_white_mode(mode) else color_level
                    )
                elif self.is_static_mode(mode):
                    if cfg.hue and cfg.cct and coexistence:
                        device.master.set(ATTR_HA_RGBWW_COLOR, (data[37], data[38], data[39], data[40], data[41]))
                    elif cfg.hue and cfg.white and coexistence:
                        device.master.set(ATTR_HA_RGBW_COLOR, (data[37], data[38], data[39], white_level))
                    elif cfg.hue or cfg.cct or cfg.white:
                        white_mode = COLOR_MODE_BRIGHTNESS
                        supported_color_modes = set()

                        if cfg.hue:
                            device.master.set(ATTR_HA_RGB_COLOR, (data[37], data[38], data[39]))
                            supported_color_modes.add(COLOR_MODE_RGB)
                        if cfg.cct:
                            device.master.set(ATTR_UL_CCT_COLOR, (data[40], data[41], white_level, None))
                            white_mode = COLOR_MODE_COLOR_TEMP
                            supported_color_modes.add(white_mode)
                        elif cfg.white and cfg.hue:
                            device.master.set(ATTR_HA_WHITE, white_level)
                            white_mode = COLOR_MODE_WHITE
                            supported_color_modes.add(white_mode)
                        else:
                            # Fix Issue #73, #77
                            # supported_color_modes = set(white_mode)
                            supported_color_modes.add(white_mode)

                        device.master.set(ATTR_HA_SUPPORTED_COLOR_MODES, supported_color_modes)
                        device.master.set(ATTR_HA_COLOR_MODE, 
                            COLOR_MODE_RGB 
                            if self.is_color_mode(mode) 
                            else white_mode
                        )
                    device.master.set(ATTR_HA_BRIGHTNESS, white_level if self.is_white_mode(mode) else color_level)
                elif mode == MODE_CUSTOM_COLOR:
                    device.master.set(ATTR_HA_BRIGHTNESS, color_level)

        if cfg:
            features = [
                LightStripFeature(extra=UNILED_CONTROL_ATTRIBUTES),
                LightModeFeature(),
                EffectTypeFeature(),
                EffectLoopFeature(),
                EffectPlayFeature(),
                EffectSpeedFeature(MAX_EFFECT_SPEED),
                EffectLengthFeature(MAX_EFFECT_LENGTH),
                EffectDirectionFeature(),
                AudioInputFeature(),
                AudioSensitivityFeature(MAX_SENSITIVITY),
                OnOffEffectFeature(),
                OnOffSpeedFeature(),
                OnOffPixelsFeature(MAX_ONOFF_PIXELS),
                OnPowerFeature(),
            ]

            if self.configs and len(self.configs) > 1:
                features.append(LightTypeFeature())
                device.master.status.set(ATTR_UL_LIGHT_TYPE, cfg.name)

            if cfg.order and len(cfg.order) > 1:
                features.append(ChipOrderFeature())
                order = self.chip_order_name(cfg.order, data[31])
                device.master.status.set(ATTR_UL_CHIP_ORDER, order)

            if cfg.coexistence:
                features.append(CoexistenceFeature())
                device.master.status.set(
                    ATTR_UL_COEXISTENCE, True if coexistence != 0x00 else False
                )

            if not device.master.features or len(device.master.features) != len(
                features
            ):
                device.master.features = features

        return True

    def build_on_connect(self, device: UniledBleDevice) -> list[bytearray] | None:
        """Build on connect message(s)"""
        return None

    def build_state_query(self, device: UniledBleDevice) -> bytearray | None:
        """Build a state query message"""
        return self.__encoder(0x02, bytearray([0x01]))

    def build_onoff_effect_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str
    ) -> bytearray | None:
        """Build On/Off effect message(s)"""
        effect = self.fetch_onoff_effect_code(channel, value)
        speed = self.fetch_onoff_speed_code(channel)
        pixels = channel.status.onoff_pixels
        return self.__encoder(
            0x08,
            bytearray([0x01, effect, speed]) + bytearray(pixels.to_bytes(2, "big")),
        )

    def fetch_onoff_effect_code(
        self, channel: UniledChannel, value: str | None = None
    ) -> int:
        """Return key for On/Off effect string"""
        value = channel.status.onoff_effect if value is None else value
        return self.int_if_str_in(value, DICTOF_ONOFF_EFFECTS, 0x01)

    def fetch_onoff_effect_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of On/Off modes"""
        return list(DICTOF_ONOFF_EFFECTS.values())

    def build_onoff_speed_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str
    ) -> bytearray | None:
        """Build On/Off speed message(s)"""
        effect = self.fetch_onoff_effect_code(channel)
        speed = self.fetch_onoff_speed_code(channel, value)
        pixels = channel.status.onoff_pixels
        return self.__encoder(
            0x08,
            bytearray([0x01, effect, speed]) + bytearray(pixels.to_bytes(2, "big")),
        )

    def fetch_onoff_speed_code(
        self, channel: UniledChannel, value: str | None = None
    ) -> int:
        """Return key for On/Off speed string"""
        value = channel.status.onoff_speed if value is None else value
        return self.int_if_str_in(value, DICTOF_ONOFF_SPEEDS, 0x02)

    def fetch_onoff_speed_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of On/Off speeds"""
        return list(DICTOF_ONOFF_SPEEDS.values())

    def build_onoff_pixels_command(
        self, device: UniledBleDevice, channel: UniledChannel, pixels: int
    ) -> bytearray | None:
        """Build On/Off speed message(s)"""
        if not MIN_ONOFF_PIXELS <= pixels <= MAX_ONOFF_PIXELS:
            return None
        effect = self.fetch_onoff_effect_code(channel)
        speed = self.fetch_onoff_speed_code(channel)
        return self.__encoder(
            0x08,
            bytearray([0x01, effect, speed])
            + bytearray(int(pixels).to_bytes(2, "big")),
        )

    def build_coexistence_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """Build color/white coexistence message(s)"""
        return self.__encoder(0x0A, bytearray([0x01 if state else 0x00]))

    def build_on_power_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: Any
    ) -> bytearray | None:
        """Build on power restore message(s)"""
        if isinstance(value, str):
            mode = self.int_if_str_in(
                value, DICTOF_ON_POWER_STATES, channel.status.on_power
            )
        elif (mode := int(value)) not in DICTOF_ON_POWER_STATES:
            return None
        return self.__encoder(0x0B, bytearray([mode]))

    def fetch_on_power_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light modes"""
        return list(DICTOF_ON_POWER_STATES.values())

    def build_onoff_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """Build power on/off state message(s)"""
        return self.__encoder(0x50, bytearray([0x01 if state else 0x00]))

    def build_white_command(
        self, device: UniledBleDevice, channel: UniledChannel, level: int
    ) -> bytearray | None:
        """The bytes to send for a change to white mode"""
        if self.is_white_mode(channel.status.light_mode_number):
            _LOGGER.warn("Skip white mode change as already white")
            return None
        if self.is_sound_mode(channel.status.light_mode_number):
            mode = MODE_SOUND_WHITE
        elif self.is_dynamic_mode(channel.status.light_mode_number):
            mode = MODE_DYNAMIC_WHITE
        else:
            mode = MODE_STATIC_WHITE
        channel.status.set(ATTR_HA_COLOR_MODE, COLOR_MODE_WHITE)
        return self.build_light_mode_command(device, channel, mode)

    def build_brightness_command(
        self, device: UniledBleDevice, channel: UniledChannel, level: int
    ) -> bytearray | None:
        """The bytes to send for a brightness level change"""
        if self.is_sound_mode(channel.status.light_mode_number):
            _LOGGER.info("Ignore brightness change in sound mode")
            channel.status.set(ATTR_HA_BRIGHTNESS, 255)
            return None
        which = 0x00 if self.is_color_mode(channel.status.light_mode_number) else 0x01
        return self.__encoder(0x51, bytearray([which, level]))

    def build_rgb_color_command(
        self, device: UniledBleDevice, channel: UniledChannel, rgb: tuple[int, int, int]
    ) -> bytearray | None:
        """The bytes to send for a color level change"""
        red, green, blue = rgb
        if self.is_static_mode(channel.status.light_mode_number):
            level = channel.status.brightness
            if level is None:
                level = 0xFF
            return self.__encoder(0x52, bytearray([red, green, blue, level]))
        return self.__encoder(0x57, bytearray([red, green, blue]))

    def build_rgbw_color_command(
        self,
        device: UniledBleDevice,
        channel: UniledChannel,
        rgbw: tuple[int, int, int, int],
    ) -> bytearray | None:
        """The bytes to send for a color level change"""
        red, green, blue, white = rgbw
        return [
            self.build_rgb_color_command(device, channel, (red, green, blue)),
            self.__encoder(0x51, bytearray([0x01, white])),
        ]

    def build_rgbww_color_command(
        self,
        device: UniledBleDevice,
        channel: UniledChannel,
        rgbww: tuple[int, int, int, int, int],
    ) -> list[bytearray] | None:
        """The bytes to send for a color level change"""
        red, green, blue, cold, warm = rgbww
        level = channel.status.brightness
        if level is None:
            level = 0xFF
        return [
            self.build_rgb_color_command(device, channel, (red, green, blue)),
            self.build_cct_color_command(device, channel, (cold, warm, level, None)),
        ]

    def build_cct_color_command(
        self,
        device: UniledBleDevice,
        channel: UniledChannel,
        cct: tuple[int, int, int, int],
    ) -> bytearray | None:
        """The bytes to send for a temperature color change."""
        cold, warm, level, kelvin = cct
        if self.is_static_mode(channel.status.light_mode_number):
            return self.__encoder(0x61, bytearray([cold, warm]))
        return self.__encoder(0x60, bytearray([cold, warm]))

    def build_light_mode_command(
        self,
        device: UniledBleDevice,
        channel: UniledChannel,
        value: Any,
        effect: int | None = None,
    ) -> list[bytearray] | None:
        """The bytes to send for a light mode change."""
        cfg: _CONFIG = channel.context
        if isinstance(value, str):
            mode = self.int_if_str_in(
                value, DICTOF_MODES, channel.status.light_mode_number
            )
        elif (mode := int(value)) not in DICTOF_MODES:
            return None
        if not cfg or (fxlist := cfg.dictof_mode_effects(mode)) is None:
            return None
        if effect is None:
            effect = channel.status.effect_number
        force_refresh = False
        if mode != channel.status.light_mode_number:
            if effect not in fxlist:
                effect = next(iter(fxlist))
            force_refresh = True
        commands = [self.__encoder(0x53, bytearray([mode, effect]))]
        if force_refresh or not channel.status.get(ATTR_UL_DEVICE_FORCE_REFRESH):
            commands.append(self.build_state_query(device))
        return commands

    def fetch_light_mode_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light modes"""
        return list(self.fetch_light_mode_dict(channel).values())

    def fetch_light_mode_dict(self, channel: UniledChannel) -> dict:
        """Channel mode dictionary"""
        modes = dict()
        cfg: _CONFIG = channel.context
        if cfg is not None and cfg.effects:
            for m in cfg.effects:
                modes[m] = str(DICTOF_MODES[m])
        return modes

    def build_effect_command(
        self,
        device: UniledBleDevice,
        channel: UniledChannel,
        effect: Any,
        mode: int | None = None,
    ) -> [bytearray] | None:
        """The bytes to send for an effect change"""
        if mode is None:
            mode = channel.status.light_mode_number
        if isinstance(effect, str):
            cfg: _CONFIG = channel.context
            if not cfg:
                return None
            effect = self.int_if_str_in(
                effect, cfg.dictof_channel_effects(mode), channel.status.effect_number
            )
        return self.build_light_mode_command(device, channel, mode, effect)

    def fetch_effect_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of effect names"""
        cfg: _CONFIG = channel.context
        mode = channel.status.light_mode_number
        if cfg and mode is not None:
            if (fxlist := cfg.dictof_mode_effects(mode)) is not None:
                effects = list()
                for fx in fxlist:
                    effects.append(str(fxlist[fx].name))
                return effects
        return None

    def build_effect_speed_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect speed change."""
        speed = int(value) & 0xFF
        if not 1 <= speed <= MAX_EFFECT_SPEED:
            return None
        return self.__encoder(0x54, bytearray([speed]))

    def build_effect_length_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect length change."""
        length = int(value) & 0xFF
        if not 1 <= length <= MAX_EFFECT_LENGTH:
            return None
        return self.__encoder(0x55, bytearray([length]))

    def build_effect_direction_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """The bytes to send for an effect direction change."""
        return self.__encoder(0x56, bytearray([0x01 if state else 0x00]))

    def build_effect_loop_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """The bytes to send to enable/disable looping effects."""
        return self.__encoder(0x58, bytearray([0x01 if state else 0x00]))

    def build_audio_input_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str
    ) -> bytearray | None:
        """The bytes to send for an input change"""
        input = self.int_if_str_in(str(value), DICTOF_AUDIO_INPUTS, 0x00)
        return self.__encoder(0x59, bytearray([input]))

    def fetch_audio_input_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light modes"""
        return list(DICTOF_AUDIO_INPUTS.values())

    def build_sensitivity_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for a gain/sensitivity change"""
        gain = int(value) & 0xFF
        if not 1 <= gain <= MAX_SENSITIVITY:
            return None
        return self.__encoder(0x5A, bytearray([gain]))

    def build_effect_play_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """The bytes to send to play/pause effects."""
        return self.__encoder(0x5D, bytearray([0x01 if state else 0x00]))

    def build_light_type_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str
    ) -> list[bytearray]:
        """Build light type message(s)"""
        if (
            light := self.int_if_str_in(str(value), self.fetch_light_type_dict())
        ) is None:
            return None
        cfg: _CONFIG = self.match_light_type_config(light)
        if cfg is None:
            return None
        channel.context = cfg
        order = None if cfg.order is None else self.chip_order_index(cfg.order, channel.status.chip_order)
        if order is None:
            order = 0x00
        mode = channel.status.light_mode_number
        effect = channel.status.effect_number

        if mode not in cfg.effects:
            mode = next(iter(cfg.effects))

        commands = []
        if power := channel.status.onoff:
            commands.append(self.build_onoff_command(device, channel, False))
        commands.append(self.__encoder(0x6A, bytearray([0x01, light & 0x7F])))
        commands.append(self.__encoder(0x6B, bytearray([order])))
        commands.extend(self.build_light_mode_command(device, channel, mode))
        return commands

    def fetch_light_type_dict(self) -> dict | None:
        """Mode effects dictionary"""
        types = dict()
        if self.configs is not None:
            for key, cfg in self.configs.items():
                types[key] = cfg.name
        return types

    def fetch_light_type_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light types"""
        listing = list()
        if self.configs is not None:
            for _, cfg in self.configs.items():
                listing.append(str(cfg.name))
        return listing

    def build_chip_order_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str | None = None
    ) -> list[bytearray]:
        """Build chip order message(s)"""
        cfg: _CONFIG = channel.context
        if cfg is not None and cfg.order:
            order = self.chip_order_index(cfg.order, value)
            return self.__encoder(0x6B, bytearray([order]))
        return None

    def fetch_chip_order_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of chip orders"""
        cfg: _CONFIG = channel.context
        if cfg is not None and cfg.order:
            return self.chip_order_list(cfg.order)
        return None

    ##
    ## Helpers
    ##
    def match_light_type_config(self, light_type: int) -> _CONFIG | None:
        """Light type dictionary"""
        if self.configs is not None:
            if light_type in self.configs:
                return self.configs[light_type]
            if len(self.configs) > 1:
                return next(iter(self.configs))
        return None

    def match_channel_effect_type(
        self, channel: UniledChannel, effect: int | None = None, mode: int | None = None
    ) -> str:
        """Code of channel effect type from effect code"""
        if effect is None:
            effect = channel.status.effect
        if mode is None:
            mode = channel.status.mode
        if mode == MODE_CUSTOM_COLOR:
            cfg: _CONFIG = channel.context
            if cfg and cfg.spi and effect == 0x01:
                return UNILEDEffectType.STATIC
        if self.is_static_mode(mode):
            return UNILEDEffectType.STATIC
        if self.is_sound_mode(mode):
            return UNILEDEffectType.SOUND
        return UNILEDEffectType.DYNAMIC

    def is_dynamic_mode(self, mode: int | None) -> bool:
        """Is a dynamic mode"""
        if (mode is not None) and mode in LISTOF_DYNAMIC_MODES:
            return True
        return False

    def is_static_mode(self, mode: int | None) -> bool:
        """Is a static mode"""
        if (mode is not None) and mode in LISTOF_STATIC_MODES:
            return True
        return False

    def is_sound_mode(self, mode: int | None) -> bool:
        """Is a sound mode"""
        if (mode is not None) and mode in LISTOF_SOUND_MODES:
            return True
        return False

    def is_color_mode(self, mode: int | None) -> bool:
        """Is a color mode"""
        if (mode is not None) and mode in LISTOF_COLOR_MODES:
            return True
        return False

    def is_white_mode(self, mode: int | None) -> bool:
        """Is a white mode"""
        if (mode is not None) and mode in LISTOF_WHITE_MODES:
            return True
        return False

    def is_loop_mode(self, mode: int | None) -> bool:
        """Is a loopable mode"""
        if (mode is not None) and mode in LISTOF_LOOPABLE_MODES:
            return True
        return False


##
## SP6xxE
##
SP6XXE = SP6xxEProxy(
    id=0xFF, name="SP6xxE", info="SP63xE and SP64xE PWM/SPI Controllers"
)
