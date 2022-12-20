"""UniLED Artifacts"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from enum import IntEnum
from .helpers import StrEnum

UNKNOWN: Final = "Uknown"


@dataclass(frozen=True)
class UNILEDModelType(IntEnum):
    """Model Type"""

    BULB = 0
    STRIP = 1


class UNILEDChipType(StrEnum):
    """LED Chipset Names"""

    SM16703 = "SM16703"
    TM1804 = "TM1804"
    UCS1903 = "UCS1903"
    WS2811 = "WS2811"
    WS2801 = "WS2801"
    SK6812 = "SK6812"
    LPD6803 = "LPD6803"
    LPD8806 = "LPD8806"
    APA102 = "APA102"
    APA105 = "APA105"
    DMX512 = "DMX512"
    TM1914 = "TM1914"
    TM1913 = "TM1913"
    P9813 = "P9813"
    INK1003 = "INK1003"
    P943S = "P943S"
    P9411 = "P9411"
    P9413 = "P9413"
    TX1812 = "TX1812"
    TX1813 = "TX1813"
    GS8206 = "GS8206"
    GS8208 = "GS8208"
    SK9822 = "SK9822"
    TM1814 = "TM1814"
    SK6812_RGBW = "SK6812_RGBW"
    P9414 = "P9414"
    P9412 = "P9412"


UNILED_CHIP_TYPES: Final = {
    # 3 Color - RGB
    0x00: UNILEDChipType.SM16703,
    0x01: UNILEDChipType.TM1804,
    0x02: UNILEDChipType.UCS1903,
    0x03: UNILEDChipType.WS2811,
    0x04: UNILEDChipType.WS2801,
    0x05: UNILEDChipType.SK6812,
    0x06: UNILEDChipType.LPD6803,
    0x07: UNILEDChipType.LPD8806,
    0x08: UNILEDChipType.APA102,
    0x09: UNILEDChipType.APA105,
    0x0A: UNILEDChipType.DMX512,
    0x0B: UNILEDChipType.TM1914,
    0x0C: UNILEDChipType.TM1913,
    0x0D: UNILEDChipType.P9813,
    0x0E: UNILEDChipType.INK1003,
    0x0F: UNILEDChipType.P943S,
    0x10: UNILEDChipType.P9411,
    0x11: UNILEDChipType.P9413,
    0x12: UNILEDChipType.TX1812,
    0x13: UNILEDChipType.TX1813,
    0x14: UNILEDChipType.GS8206,
    0x15: UNILEDChipType.GS8208,
    0x16: UNILEDChipType.SK9822,
    # 4 Color - RGBW
    0x17: UNILEDChipType.TM1814,
    0x18: UNILEDChipType.SK6812_RGBW,
    0x19: UNILEDChipType.P9414,
    0x1A: UNILEDChipType.P9412,
}

UNILED_CHIP_4COLOR: Final = [
    0x17,  # TM1814
    0x18,  # SK6812_RGBW
    0x19,  # P9414
    0x1A,  # P9412
]


class UNILEDChipOrder(StrEnum):
    """LED Ordering Names"""

    RGB = "RGB"
    RBG = "RBG"
    GRB = "GRB"
    GBR = "GBR"
    BRG = "BRG"
    BGR = "BGR"


UNILED_CHIP_ORDER_3COLOR: Final = {
    0x00: UNILEDChipOrder.RGB,
    0x01: UNILEDChipOrder.RBG,
    0x02: UNILEDChipOrder.GRB,
    0x03: UNILEDChipOrder.GBR,
    0x04: UNILEDChipOrder.BRG,
    0x05: UNILEDChipOrder.BGR,
}

UNILED_CHIP_ORDER_4COLOR: Final = {
    0x00: "RGBW",
    0x01: "RBGW",
    0x02: "GRBW",
    0x03: "GBRW",
    0x04: "BRGW",
    0x05: "BGRW",
    0x06: "RGWB",
    0x07: "RBWG",
    0x08: "RWGB",
    0x09: "RWBG",
    0x0A: "GRWB",
    0x0B: "GBWR",
    0x0C: "GWRB",
    0x0D: "GWBR",
    0x0E: "BRWG",
    0x0F: "BGWR",
    0x10: "BWRG",
    # 0x11: "",
}


class UNILEDMode(StrEnum):
    """Mode Names"""

    OFF = "Off"
    MANUAL = "Manual"
    SINGULAR = "Single FX"
    AUTO = "Cycle Effects"
    AUTO_PATTERN = "Cycle Pattern Effects"
    AUTO_SCENE = "Cycle Scenes"
    AUTO_SOUND = "Cycle Sound Effects"


class UNILEDInput(StrEnum):
    """Audio Input Names"""

    AUXIN = "Aux In"
    INTMIC = "Int. Mic"
    EXTMIC = "Ext. Mic"
    PLAYER = "Player"


class UNILEDEffectType(StrEnum):
    """Effect Mode/Type Names"""

    PATTERN = "Pattern"
    STATIC = "Static"
    SOUND = "Sound"


class UNILEDEffectDirection(StrEnum):
    """Effect Direction Names"""

    BACKWARDS = "Backwards"
    FORWARDS = "Forwards"


class UNILEDEffects(StrEnum):
    """Effect/Pattern Names"""

    SOLID = "Solid"

    RAINBOW = "Rainbow"
    RAINBOW_METEOR = "Rainbow Metor"
    RAINBOW_STARS = "Rainbow Stars"
    RAINBOW_SPIN = "Rainbow Spin"

    FIRE = "Fire"
    FIRE_RED_YELLOW = "Red/Yellow Fire"
    FIRE_RED_PURPLE = "Red/Purple Fire"
    FIRE_GREEN_YELLOW = "Green/Yellow Fire"
    FIRE_GREEN_CYAN = "Green/Cyan Fire"
    FIRE_BLUE_PURPLE = "Blue/Purple Fire"
    FIRE_BLUE_CYAN = "Blue/Cyan Fire"

    COMET = "Comet"
    COMET_RED = "Red Comet"
    COMET_GREEN = "Green Comet"
    COMET_BLUE = "Blue Comet"
    COMET_YELLOW = "Yellow Comet"
    COMET_CYAN = "Cyan Comet"
    COMET_PURPLE = "Purple Comet"
    COMET_WHITE = "White Comet"

    METEOR = "Meteor"
    METEOR_RED = "Red Meteor"
    METEOR_GREEN = "Green Meteor"
    METEOR_BLUE = "Blue Meteor"
    METEOR_YELLOW = "Yellow Meteor"
    METEOR_CYAN = "Cyan Meteor"
    METEOR_PURPLE = "Purple Meteor"
    METEOR_WHITE = "White Meteor"

    GRADUAL_SNAKE = "Gradual Snake"
    GRADUAL_SNAKE_RED_GREEN = "Red/Green Gradual Snake"
    GRADUAL_SNAKE_RED_BLUE = "Red/Blue Gradual Snake"
    GRADUAL_SNAKE_RED_YELLOW = "Red/Yellow Gradual Snake"
    GRADUAL_SNAKE_RED_CYAN = "Red/Cyan Gradual Snake"
    GRADUAL_SNAKE_RED_PURPLE = "Red/Purple Gradual Snake"
    GRADUAL_SNAKE_RED_WHITE = "Red/White Gradual Snake"
    GRADUAL_SNAKE_GREEN_BLUE = "Green/Blue Gradual Snake"
    GRADUAL_SNAKE_GREEN_YELLOW = "Green/Yellow Gradual Snake"
    GRADUAL_SNAKE_GREEN_CYAN = "Green/Cyan Gradual Snake"
    GRADUAL_SNAKE_GREEN_PURPLE = "Green/Purple Gradual Snake"
    GRADUAL_SNAKE_GREEN_WHITE = "Green/White Gradual Snake"
    GRADUAL_SNAKE_BLUE_YELLOW = "Blue/Yellow Gradual Snake"
    GRADUAL_SNAKE_BLUE_CYAN = "Blue/Cyan Gradual Snake"
    GRADUAL_SNAKE_BLUE_PURPLE = "Blue/Purple Gradual Snake"
    GRADUAL_SNAKE_BLUE_WHITE = "Blue/White Gradual Snake"
    GRADUAL_SNAKE_YELLOW_CYAN = "Yellow/Cyan Gradual Snake"
    GRADUAL_SNAKE_YELLOW_PURPLE = "Yellow/Purple Gradual Snake"
    GRADUAL_SNAKE_YELLOW_WHITE = "Yellow/White Gradual Snake"
    GRADUAL_SNAKE_CYAN_PURPLE = "Cyan/Purple Gradual Snake"
    GRADUAL_SNAKE_CYAN_WHITE = "Cyan/White Gradual Snake"
    GRADUAL_SNAKE_PURPLE_WHITE = "Purple/White Gradual Snake"

    WAVE = "Wave"
    WAVE_RED = "Red Wave"
    WAVE_GREEN = "Green Wave"
    WAVE_BLUE = "Blue Wave"
    WAVE_YELLOW = "Yellow Wave"
    WAVE_CYAN = "Cyan Wave"
    WAVE_PURPLE = "Purple Wave"
    WAVE_WHITE = "White Wave"
    WAVE_RED_GREEN = "Red/Green Wave"
    WAVE_RED_BLUE = "Red/Blue Wave"
    WAVE_RED_YELLOW = "Red/Yellow Wave"
    WAVE_RED_CYAN = "Red/Cyan Wave"
    WAVE_RED_PURPLE = "Red/Purple Wave"
    WAVE_RED_WHITE = "Red/White Wave"
    WAVE_GREEN_BLUE = "Green/Blue Wave"
    WAVE_GREEN_YELLOW = "Green/Yellow Wave"
    WAVE_GREEN_CYAN = "Green/Cyan Wave"
    WAVE_GREEN_PURPLE = "Green/Purple Wave"
    WAVE_GREEN_WHITE = "Green/White Wave"
    WAVE_BLUE_YELLOW = "Blue/Yellow Wave"
    WAVE_BLUE_CYAN = "Blue/Cyan Wave"
    WAVE_BLUE_PURPLE = "Blue/Purple Wave"
    WAVE_BLUE_WHITE = "Blue/White Wave"
    WAVE_YELLOW_CYAN = "Yellow/Cyan Wave"
    WAVE_YELLOW_PURPLE = "Yellow/Purple Wave"
    WAVE_YELLOW_WHITE = "Yellow/White Wave"
    WAVE_CYAN_PURPLE = "Cyan/Purple Wave"
    WAVE_CYAN_WHITE = "Cyan/White Wave"
    WAVE_PURPLE_WHITE = "Purple/White Wave"

    STARS = "Stars"
    STARS_TWINKLE = "Twinkle Stars"
    STARS_RED = "Red Stars"
    STARS_GREEN = "Green Stars"
    STARS_BLUE = "Blue Stars"
    STARS_YELLOW = "Yellow Stars"
    STARS_CYAN = "Cyan Stars"
    STARS_PURPLE = "Purple Stars"
    STARS_WHITE = "White Stars"

    BACKGROUND_STARS = "Background Stars"
    BACKGROUND_STARS_RED = "Red Background Stars"
    BACKGROUND_STARS_GREEN = "Green Background Stars"
    BACKGROUND_STARS_BLUE = "Blue Background Stars"
    BACKGROUND_STARS_YELLOW = "Yellow Background Stars"
    BACKGROUND_STARS_CYAN = "Cyan Background Stars"
    BACKGROUND_STARS_PURPLE = "Purple Background Stars"
    BACKGROUND_STARS_RED_WHITE = "Red/White Background Stars"
    BACKGROUND_STARS_GREEN_WHITE = "Green/White Background Stars"
    BACKGROUND_STARS_BLUE_WHITE = "Blue/White Background Stars"
    BACKGROUND_STARS_YELLOW_WHITE = "Yellow/White Background Stars"
    BACKGROUND_STARS_CYAN_WHITE = "Cyan/White Background Stars"
    BACKGROUND_STARS_PURPLE_WHITE = "Purple/White Background Stars"
    BACKGROUND_STARS_WHITE_WHITE = "White/White Background Stars"

    BREATH = "Breath"
    BREATH_RED = "Red Breath"
    BREATH_GREEN = "Green Breath"
    BREATH_BLUE = "Blue Breath"
    BREATH_YELLOW = "Yellow Breath"
    BREATH_CYAN = "Cyan Breath"
    BREATH_PRUPLE = "Purple Breath"
    BREATH_WHITE = "White Breath"

    STACKING = "Stacking"
    STACKING_RED = "Red Stacking"
    STACKING_GREEN = "Green Stacking"
    STACKING_BLUE = "Blue Stacking"
    STACKING_YELLOW = "Yellow Stacking"
    STACKING_CYAN = "Cyan Stacking"
    STACKING_PRUPLE = "Purple Stacking"
    STACKING_WHITE = "White Stacking"

    STACK = "Stack"
    STACK_FULL_COLOR = "Full Color Stack"
    STACK_RED_GREEN = "Red to Green Stack"
    STACK_GREEN_BLUE = "Green to Blue Stack"
    STACK_BLUE_YELLOW = "Blue to Yellow Stack"
    STACK_YELLOW_CYAN = "Yellow to Cyan Stack"
    STACK_CYAN_PURPLE = "Cyan to Purple Stack"
    STACK_PURPLE_WHITE = "Purple to White Stack"

    SNAKE = "Snake"
    SNAKE_RED_BLUE_WHITE = "Red/Blue/White Snake"
    SNAKE_GREEN_YELLOW_WHITE = "Green/Yellow/White Snake"
    SNAKE_RED_GREEN_WHITE = "Red/Green/White Snake"
    SNAKE_RED_YELLOW = "Red/Yellow Snake"
    SNAKE_RED_WHITE = "Red/White Snake"
    SNAKE_GREEN_WHITE = "Green/White Snake"

    COMET_SPIN = "Comet Spin"
    COMET_SPIN_RED = "Red Comet Spin"
    COMET_SPIN_GREEN = "Green Comet Spin"
    COMET_SPIN_BLUE = "Blue Comet Spin"
    COMET_SPIN_YELLOW = "Yellow Comet Spin"
    COMET_SPIN_CYAN = "Cyan Comet Spin"
    COMET_SPIN_PURPLE = "Purple Comet Spin"
    COMET_SPIN_WHITE = "White Comet Spin"

    DOT_SPIN = "Dot Spin"
    DOT_SPIN_RED = "Red Dot Spin"
    DOT_SPIN_GREEN = "Green Dot Spin"
    DOT_SPIN_BLUE = "Blue Dot Spin"
    DOT_SPIN_YELLOW = "Yellow Dot Spin"
    DOT_SPIN_CYAN = "Cyan Dot Spin"
    DOT_SPIN_PURPLE = "Purple Dot Spin"
    DOT_SPIN_WHITE = "White Dot Spin"

    SEGMENT_SPIN = "Segment Spin"
    SEGMENT_SPIN_RED = "Red Segment Spin"
    SEGMENT_SPIN_GREEN = "Green Segment Spin"
    SEGMENT_SPIN_BLUE = "Blue Segment Spin"
    SEGMENT_SPIN_YELLOW = "Yellow Segment Spin"
    SEGMENT_SPIN_CYAN = "Cyan Segment Spin"
    SEGMENT_SPIN_PURPLE = "Purple Segment Spin"
    SEGMENT_SPIN_WHITE = "White Segment Spin"

    GRADIENT = "Gradient"

    # Sound Activated
    SOUND_RHYTHM_SPECTRUM_FULL = "Sound - Full Color Rhythm Spectrum"
    SOUND_RHYTHM_SPECTRUM_SINGLE = "Sound - Single Color Rhythm Spectrum"
    SOUND_RHYTHM_STARS_FULL = "Sound - Full Color Rhythm Stars"
    SOUND_RHYTHM_STARS_SINGLE = "Sound - Single Color Rhythm Stars"
    SOUND_ENERGY_GRADIENT = "Sound - Gradient Energy"
    SOUND_ENERGY_SINGLE = "Sound - Single Color Energy"
    SOUND_PULSE_GRADIENT = "Sound - Gradient Pulse"
    SOUND_PULSE_SINGLE = "Sound - Single Color Pulse"
    SOUND_EJECTION_FORWARD_FULL = "Sound - Full Color Ejection Forward"
    SOUND_EJECTION_FORWARD_SINGLE = "Sound - Single Color Ejection Forward"
    SOUND_EJECTION_BACKWARD_FULL = "Sound - Full Color Ejection Backward"
    SOUND_EJECTION_BACKWARD_SINGLE = "Sound - Single Color Ejection Backward"
    SOUND_VU_METER_FULL = "Sound - Full Color VuMeter"
    SOUND_VU_METER_SINGLE = "Sound - Single Color VuMeter"
    SOUND_LOVE_AND_PEACE = "Sound - Love & Peace"
    SOUND_CHRISTMAS = "Sound - Christmas"
    SOUND_HEARTBEAT = "Sound - Heartbeat"
    SOUND_PARTY = "Sound - Party"
