"""UniLED Chip Types"""
from __future__ import annotations
from typing import Final
import itertools

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

class UniledChips:
    """UniLED Chip Utilities Class"""

    def chip_order_list(self, sequence: str, suffix: str = "") -> list:
        """Generate list of chip order combinations"""
        combos = list()
        letters = len(sequence)
        if sequence and letters <= 3:
            for combo in itertools.permutations(sequence, len(sequence)):
                combos.append("".join(combo) + suffix)
        elif letters <= 5:
            combos = self.chip_order_list(sequence[:3], sequence[3:])
            for combo in itertools.permutations(sequence, len(sequence)):
                order = "".join(combo) + suffix
                if order not in combos:
                    combos.append(order)
        return combos

    def chip_order_name(self, sequence: str, value: int) -> str:
        """Generate list of chip order combinations"""
        order = None
        if orders := self.chip_order_list(sequence):
            try:
                order = orders[value]
            except IndexError:
                pass
        return order

    def chip_order_index(self, sequence: str, value: str) -> int:
        """Generate list of chip order combinations"""
        if orders := self.chip_order_list(sequence):
            if value in orders:
                return orders.index(value)
        return None

    def str_if_key_in(self, key, dikt: dict, default: str | None = None) -> str | None:
        """Return dictionary string value from key"""
        if not dikt or not isinstance(dikt, dict):
            return default
        return default if key not in dikt else str(dikt[key])

    def int_if_str_in(
        self, string: str, dikt: dict, default: int | None = None
    ) -> int | None:
        """Return dictionary key value from string lookup"""
        if not dikt or not isinstance(dikt, dict):
            return default
        for key, value in dikt.items():
            if value == string:
                return key
        return default
