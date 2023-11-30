"""UniLED Chip Types"""
from __future__ import annotations
from typing import Final

UNILED_CHIP_ORDER_CW: Final = "CW"
UNILED_CHIP_ORDER_123: Final = "123"
UNILED_CHIP_ORDER_CWX: Final = "CWX"
UNILED_CHIP_ORDER_RGB: Final = "RGB"
UNILED_CHIP_ORDER_RGBW: Final = "RGBW"
UNILED_CHIP_ORDER_RGBCW: Final = "RGBCW"

UNILED_CHIP_TYPES: Final = {
    # 3 Color - RGB
    0x00: "SM16703",
    0x01: "TM1804",
    0x02: "UCS1903",
    0x03: "WS2811",
    0x04: "WS2801",
    0x05: "SK6812",
    0x06: "LPD6803",
    0x07: "LPD8806",
    0x08: "APA102",
    0x09: "APA105",
    0x0A: "DMX512",
    0x0B: "TM1914",
    0x0C: "TM1913",
    0x0D: "P9813",
    0x0E: "INK1003",
    0x0F: "P943S",
    0x10: "P9411",
    0x11: "P9413",
    0x12: "TX1812",
    0x13: "TX1813",
    0x14: "GS8206",
    0x15: "GS8208",
    0x16: "SK9822",
    # 4 Color - RGBW
    0x17: "TM1814",
    0x18: "SK6812_RGBW",
    0x19: "P9414",
    0x1A: "P9412",
}

UNILED_CHIP_TYPES_4COLOR: Final = [
    0x17,  # TM1814
    0x18,  # SK6812_RGBW
    0x19,  # P9414
    0x1A,  # P9412
]
