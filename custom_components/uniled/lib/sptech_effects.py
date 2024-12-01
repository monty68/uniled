"""UniLED SPTech Common Components"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Final

from .effects import (
    UNILEDEffectType,
    UNILEDEffects,
)

@dataclass(frozen=True)
class _FX_STATIC:
    """Static Effect and Attributes"""

    name: str
    colorable: bool = True
    sizeable: bool = False
    directional: bool = False
    pausable: bool = False
    speedable: bool = False


@dataclass(frozen=True)
class _FX_DYNAMIC:
    """Dynamic Effect and Attributes"""

    name: str
    colorable: bool = False
    sizeable: bool = False
    directional: bool = False
    pausable: bool = False
    speedable: bool = True


@dataclass(frozen=True)
class _FX_SOUND:
    """Sound Effect and Attributes"""

    name: str
    colorable: bool = False
    sizeable: bool = False
    directional: bool = False
    pausable: bool = False
    speedable: bool = False

##
## BanlanX - SPTech Common Effects
##
class SPTechFX:
    """BanlanX - SPTech Common Effects"""

    MODE_STATIC_COLOR: Final = 0x01
    MODE_STATIC_WHITE: Final = 0x02
    MODE_DYNAMIC_COLOR: Final = 0x03
    MODE_DYNAMIC_WHITE: Final = 0x04
    MODE_SOUND_COLOR: Final = 0x05
    MODE_SOUND_WHITE: Final = 0x06
    MODE_CUSTOM_SOLID: Final = 0x07
    MODE_CUSTOM_GRADIENT: Final = 0x08

    DICTOF_MODES: Final = {
        MODE_STATIC_COLOR: "Static Color",
        MODE_STATIC_WHITE: "Static White",
        MODE_DYNAMIC_COLOR: "Dynamic Color",
        MODE_DYNAMIC_WHITE: "Dynamic White",
        MODE_SOUND_COLOR: "Sound - Color",
        MODE_SOUND_WHITE: "Sound - White",
        MODE_CUSTOM_SOLID: "Custom Solid",
        MODE_CUSTOM_GRADIENT: "Custom Gradient"
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
        MODE_CUSTOM_SOLID,
        MODE_CUSTOM_GRADIENT,
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

    LISTOF_CUSTOM_MODES: Final = [
        MODE_CUSTOM_SOLID,
        MODE_CUSTOM_GRADIENT
    ]

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

    DICTOF_SPI_EFFECTS_CUSTOM_SOLID: Final = {
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

    DICTOF_SPI_EFFECTS_CUSTOM_GRADIENT: Final = {
        0x01: _FX_STATIC(UNILEDEffects.STATIC, False),
        0x02: _FX_DYNAMIC("Chase Forward"),
        0x03: _FX_DYNAMIC("Chase Backward"),
        0x04: _FX_DYNAMIC("Spin"),
        0x05: _FX_DYNAMIC("Sine Chase Forward"),
        0x06: _FX_DYNAMIC("Sine Chase Backward"),
        0x07: _FX_DYNAMIC("Fire Forward"),
        0x08: _FX_DYNAMIC("Fire Backward"),
        0x09: _FX_DYNAMIC("Juggle"),
        0x0A: _FX_DYNAMIC("Meteor Forward"),
        0x0B: _FX_DYNAMIC("Meteor Backward"),
    }
