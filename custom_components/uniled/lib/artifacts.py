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

class UNILEDColorOrder(StrEnum):
    """LED Ordering Names"""

    RGB = "RGB"
    RBG = "RBG"
    GRB = "GRB"
    GBR = "GBR"
    BRG = "BRG"
    BGR = "BGR"

class UNILEDChipsets(StrEnum):
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


class UNILEDModes(StrEnum):
    """Effect Mode/Type Names"""

    STATIC = "Static"
    DYNAMIC = "Dynamic"
    SOUND = "Sound"


class UNILEDInputs(StrEnum):
    """Audio Input Names"""

    AUXIN = "Aux In"
    INTMIC = "Int. Mic"
    EXTMIC = "Ext. Mic"
    PLAYER = "Player"


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

    # Music Modes (SP611E)
    MUSIC_RHYTHM_SPECTRUM_FULL = "Full Color Rhythm Spectrum"
    MUSIC_RHYTHM_SPECTRUM_SINGLE = "Single Color Rhythm Spectrum"
    MUSIC_RHYTHM_STARS_FULL = "Full Color Rhythm Stars"
    MUSIC_RHYTHM_STARS_SINGLE = "Single Color Rhythm Stars"
    MUSIC_ENERGY_GRADIENT = "Gradient Energy"
    MUSIC_ENERGY_SINGLE = "Single Color Energy"
    MUSIC_PULSE_GRADIENT = "Gradient Pulse"
    MUSIC_PULSE_SINGLE = "Single Color Pulse"
    MUSIC_EJECTION_FORWARD_FULL = "Full Color Ejection Forward"
    MUSIC_EJECTION_FORWARD_SINGLE = "Single Color Ejection Forward"
    MUSIC_EJECTION_BACKWARD_FULL = "Full Color Ejection Backward"
    MUSIC_EJECTION_BACKWARD_SINGLE = "Single Color Ejection Backward"
    MUSIC_VU_METER_FULL = "Full Color VuMeter"
    MUSIC_VU_METER_SINGLE = "Single Color VuMeter"
    MUSIC_LOVE_AND_PEACE = "Love & Peace"
    MUSIC_CHRISTMAS = "Christmas"
    MUSIC_HEARTBEAT = "Heartbeat"
    MUSIC_PARTY = "Party"
