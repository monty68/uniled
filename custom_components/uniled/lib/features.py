"""UniLED Features."""
from __future__ import annotations
from typing import Final

from .attributes import (
    UniledAttribute,
    UniledGroup,
    UniledNumber,
    UniledSelect,
    # UniledBinary,
    UniledSensor,
    UniledButton,
    UniledSwitch,
    ATTR_UL_POWER,
    ATTR_UL_LIGHT_TYPE,
    ATTR_UL_LIGHT_MODE,
    ATTR_UL_EFFECT_TYPE,
    ATTR_UL_EFFECT_LOOP,
    ATTR_UL_EFFECT_PLAY,
    ATTR_UL_EFFECT_SPEED,
    ATTR_UL_EFFECT_LENGTH,
    ATTR_UL_EFFECT_DIRECTION,
    ATTR_UL_AUDIO_INPUT,
    ATTR_UL_SENSITIVITY,
    ATTR_UL_CHIP_TYPE,
    ATTR_UL_CHIP_ORDER,
    ATTR_UL_ONOFF_EFFECT,
    ATTR_UL_ONOFF_SPEED,
    ATTR_UL_ONOFF_PIXELS,
    ATTR_UL_ON_POWER,
    ATTR_UL_COEXISTENCE,
    ATTR_UL_SEGMENT_COUNT,
    ATTR_UL_SEGMENT_PIXELS,
    ATTR_UL_SCENE_LOOP,
    ATTR_HA_COLOR_TEMP_KELVIN,
)


class UniledLight(UniledAttribute):
    """UniLED Light Feature Class"""

    def __init__(
        self,
    ) -> None:
        self._attr = ATTR_UL_POWER
        self._type = "light"
        self._name = "Light"
        self._icon = "mdi:lightbulb"
        self._key = "light"

class UniledBulb(UniledLight):
    """UniLED Light Feature Class"""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._name = "Bulb"
        self._key = "bulb"

class UniledLamp(UniledLight):
    """UniLED Light Feature Class"""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._name = "Lamp"
        self._icon = "mdi:lamp"
        self._key = "lamp"

class UniledLedStrip(UniledAttribute):
    """UniLED Light Feature Class"""

    def __init__(
        self,
    ) -> None:
        self._attr = ATTR_UL_POWER
        self._type = "light"
        self._name = "Light" # Backwards compat
        self._icon = "mdi:led-strip-variant"
        self._key = "strip"


class UniledEffectType(UniledSensor):
    """UniLED Effect Type Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.STANDARD,
            False,
            ATTR_UL_EFFECT_TYPE,
            "Effect Type",
            "mdi:magic-staff",
            None,
        )


class UniledEffectSpeed(UniledNumber):
    """UniLED Effect Speed Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(
            UniledGroup.NEEDS_ON,
            True,
            ATTR_UL_EFFECT_SPEED,
            "Effect Speed",
            "mdi:play-speed",
            "speed",
            max,
            min,
            inc,
        )


class UniledEffectLength(UniledNumber):
    """UniLED Effect Length Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(
            UniledGroup.NEEDS_ON,
            True,
            ATTR_UL_EFFECT_LENGTH,
            "Effect Length",
            "mdi:ruler",
            "length",
            max,
            min,
            inc,
        )


class UniledEffectDirection(UniledSwitch):
    """UniLED Effect Length Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.NEEDS_ON,
            True,
            ATTR_UL_EFFECT_DIRECTION,
            "Effect Direction",
            "mdi:arrow-right",
            "mdi:arrow-left",
            "direction", # Backwards compat
        )


class UniledEffectLoop(UniledSwitch):
    """UniLED Effect Loop Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.NEEDS_ON,
            False,
            ATTR_UL_EFFECT_LOOP,
            "Loop Effects",
            "mdi:lightbulb-auto",
            "mdi:refresh-auto",
        )

class UniledSceneLoop(UniledSwitch):
    """UniLED Scene Loop Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.STANDARD,
            True,
            ATTR_UL_SCENE_LOOP,
            "Loop Scenes",
            "mdi:progress-star",
            "mdi:refresh-auto",
        )

class UniledEffectPlay(UniledSwitch):
    """UniLED Effect Play Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.NEEDS_ON,
            False,
            ATTR_UL_EFFECT_PLAY,
            "Effect Play/Pause",
            "mdi:play",
            "mdi:pause",
        )


class UniledAudioInput(UniledSelect):
    """UniLED Sound Input Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.CONFIGURATION,
            False,
            ATTR_UL_AUDIO_INPUT,
            "Audio Input",
            "mdi:microphone",
            "input", # Backwards compat
        )


class UniledSensitivity(UniledNumber):
    """UniLED Sensitivity Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(
            UniledGroup.CONFIGURATION,
            False,
            ATTR_UL_SENSITIVITY,
            "Audio Input Sensitivity",
            "mdi:knob",
            "sensitivity", # Backwards compat
            max,
            min,
            inc,
        )


class UniledLightMode(UniledSelect):
    """UniLED Light Mode Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.NEEDS_ON,
            True,
            ATTR_UL_LIGHT_MODE,
            "Light Mode",
            "mdi:palette",
            "mode", # Backwards compat
        )


class UniledLightType(UniledSelect):
    """UniLED Light Type Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.CONFIGURATION,
            False,
            ATTR_UL_LIGHT_TYPE,
            "Light Type",
            "mdi:lightbulb-question",
            None,
        )
        self._reload = True


class UniledChipType(UniledSelect):
    """UniLED Chip Type Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.CONFIGURATION,
            False,
            ATTR_UL_CHIP_TYPE,
            "Chip Type",
            "mdi:chip",
            None,
        )


class UniledChipOrder(UniledSelect):
    """UniLED Chip Order Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.CONFIGURATION,
            False,
            ATTR_UL_CHIP_ORDER,
            "Chip Order",
            "mdi:palette",
            None,
        )

class UniledOnOffEffect(UniledSelect):
    """UniLED On/Off Effect Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.CONFIGURATION,
            False,
            ATTR_UL_ONOFF_EFFECT,
            "On/Off Effect",
            "mdi:magic-staff",
            None,
        )

class UniledOnOffSpeed(UniledSelect):
    """UniLED On/Off Mode Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.CONFIGURATION,
            False,
            ATTR_UL_ONOFF_SPEED,
            "On/Off Speed",
            "mdi:speedometer",
            None,
        )

class UniledOnOffPixels(UniledNumber):
    """UniLED On/Off Pixels Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(
            UniledGroup.CONFIGURATION,
            False,
            ATTR_UL_ONOFF_PIXELS,
            "On/Off Pixels",
            "mdi:pencil-ruler",
            None,
            max,
            min,
            inc,
        )

class UniledOnPower(UniledSelect):
    """UniLED Light Type Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.CONFIGURATION,
            False,
            ATTR_UL_ON_POWER,
            "On Power Restore",
            "mdi:lightning-bolt",
            None,
        )


class UniledCoexistence(UniledSwitch):
    """UniLED Effect Length Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            UniledGroup.CONFIGURATION,
            True,
            ATTR_UL_COEXISTENCE,
            "Color/White Coexistence",
            "mdi:lightbulb-multiple",
            "mdi:lightbulb",
        )


class UniledSegmentCount(UniledNumber):
    """UniLED Segment Count Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(
            UniledGroup.CONFIGURATION,
            False,
            ATTR_UL_SEGMENT_COUNT,
            "Segments",
            "mdi:numeric",
            None,
            max,
            min,
            inc,
        )

class UniledSegmentPixels(UniledOnOffPixels):
    """UniLED Segment Pixels Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(max, min, inc)
        self._attr = ATTR_UL_SEGMENT_PIXELS
        self._name = "Segment Pixels"
        self._key = "segment_length" # Backwards compat

class UniledTemperature(UniledNumber):
    """UniLED Sensitivity Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(
            UniledGroup.CONFIGURATION,
            False,
            ATTR_HA_COLOR_TEMP_KELVIN,
            "Color Temperature",
            "mdi:temperature-kelvin",
            "temperature",
            max,
            min,
            inc,
        )


# "mdi:tape-measure"
# "mdi-pencil-ruler"
# "mdi:cog"
# "mdi:knob",
# "mdi:AutoMode"
# "mdi:chip"
# "mdi:microphone"
# "mdi:magic-staff"
# "mdi:refresh-auto"
# "mdi:numeric"
# "mdi:star"
# "mdi:star-cog"
# "mdi:star-shooting"
# "mdi:lightbulb-multiple-outline"
# "mdi:lightbulb-group-outline"
# "mdi:lightbulb-auto"
# "mdi:lightbulb-question"
