"""UniLED State"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

UNILED_STATE_AUTO = "auto"
UNILED_STATE_AUTO_MATRIX_FX = "auto_matrix_fx"
UNILED_STATE_AUTO_STRIP_FX = "auto_strip_fx"
UNILED_STATE_INPUT = "input"
UNILED_STATE_SETUP = "setup"

UNILED_STATE_GAIN = "gain"  # TODO: Remove when updated: banlax2.py!

UNILED_STATE_MUSIC_COLOR = "music_color"
UNILED_STATE_COLUMN_COLOR = "column_color"
UNILED_STATE_DOT_COLOR = "dot_color"


@dataclass(frozen=True)
class UNILEDSetup:
    """UniLED Strip Setup Class"""

    order: int | None = None
    chipset: int | None = None
    segments: int | None = None
    leds: int | None = None


@dataclass(frozen=True)
class UNILEDStatus:
    """UniLED Channel State Class"""

    power: bool = False
    effect: int | None = None
    fxtype: int | None = None
    speed: int | None = None
    length: int | None = None
    direction: int | None = None
    gain: int | None = None
    white: int | None = None
    level: int | None = None
    rgb: tuple[int, int, int] | None = None
    extra: dict(str, Any) = field(default_factory=dict)
