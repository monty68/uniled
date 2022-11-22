"""UniLED State and Status"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .helpers import StrEnum


@dataclass(frozen=True)
class UNILEDState(StrEnum):
    """UniLED Channel States Class"""

    POWER = "power"
    MODE = "mode"
    EFFECT = "effect"
    TYPE = "fxtype"
    SPEED = "speed"
    LENGTH = "length"
    DIRECTION = "direction"
    LEVEL = "level"
    WHITE = "white"
    RGB = "rgb"
    RGB2 = "rgb2"
    # RGBW = "rgbw"
    GAIN = "gain"
    INPUT = "input"
    CHIPTYPE = "chip_type"
    CHIPORDER = "chip_order"
    SEGMENT_COUNT = "segment_count"
    SEGMENT_LENGTH = "segment_length"


@dataclass(frozen=True)
class UNILEDStatus:
    """UniLED Channel Status Class"""

    power: bool | None = None
    mode: int | None = None
    level: int | None = None
    white: int | None = None
    rgb: tuple[int, int, int] | None = None
    rgb2: tuple[int, int, int] | None = None
    effect: int | None = None
    fxtype: int | None = None
    speed: int | None = None
    length: int | None = None
    direction: int | None = None
    input: int | None = None
    gain: int | None = None
    chip_type: int | None = None
    chip_order: int | None = None
    segment_count: int | None = None
    segment_length: int | None = None
    extra: dict(str, Any) = field(default_factory=dict)
