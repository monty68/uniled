"""UniLED Features."""
from __future__ import annotations
from typing import Final

from .attributes import (
    UniledAttribute,
    UniledGroup,
    # BinaryAttribute,
    ButtonAttribute,
    NumberAttribute,
    SceneAttribute,
    SelectAttribute,
    SensorAttribute,
    SwitchAttribute,
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


class LightFeature(UniledAttribute):
    """UniLED Light Feature Class"""

    def __init__(self, extra: list | None = None) -> None:
        super().__init__(
           "light",
           ATTR_UL_POWER,
           "Light",
           "mdi:lightbulb",
           "light",
           True,
           UniledGroup.STANDARD,
           extra 
        )


class LampFeature(LightFeature):
    """UniLED Lamp Feature Class"""

    def __init__(self, extra: list | None = None) -> None:
        super().__init__(extra)
        self._name = "Lamp"
        self._icon = "mdi:lamp"
        self._key = "lamp"


class LightBulbFeature(LightFeature):
    """UniLED Light Bulb Feature Class"""

    def __init__(self, extra: list | None = None) -> None:
        super().__init__(extra)
        self._name = "Bulb"
        self._icon = "mdi:lightbulb"
        self._key = "bulb"


class LightStripFeature(LightFeature):
    """UniLED Light Strip Feature Class"""

    def __init__(self, extra: list | None = None) -> None:
        super().__init__(extra)
        self._name = "Light"  # Backwards compat
        self._icon = "mdi:led-strip-variant"
        self._key = "strip"

class EffectTypeFeature(SensorAttribute):
    """UniLED Effect Type Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_EFFECT_TYPE,
            "Effect Type",
            "mdi:magic-staff",
            enabled=False
        )


class EffectSpeedFeature(NumberAttribute):
    """UniLED Effect Speed Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(
            ATTR_UL_EFFECT_SPEED,
            "Effect Speed",
            "mdi:play-speed",
            max,
            min,
            inc,
            group=UniledGroup.NEEDS_ON,
        )


class EffectLengthFeature(NumberAttribute):
    """UniLED Effect Length Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(
            ATTR_UL_EFFECT_LENGTH,
            "Effect Length",
            "mdi:ruler",
            max,
            min,
            inc,
            group=UniledGroup.NEEDS_ON,
        )


class EffectDirectionFeature(SwitchAttribute):
    """UniLED Effect Length Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_EFFECT_DIRECTION,
            "Effect Direction",
            "mdi:arrow-right",
            "mdi:arrow-left",
            group=UniledGroup.NEEDS_ON,
        )


class EffectLoopFeature(SwitchAttribute):
    """UniLED Effect Loop Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_EFFECT_LOOP,
            "Loop Effects",
            "mdi:lightbulb-auto",
            "mdi:refresh-auto",
            group=UniledGroup.NEEDS_ON,
            enabled=False,
        )


class EffectPlayFeature(SwitchAttribute):
    """UniLED Effect Play Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_EFFECT_PLAY,
            "Effect Play/Pause",
            "mdi:play",
            "mdi:pause",
            group=UniledGroup.NEEDS_ON,
            enabled=False,
        )


class SceneLoopFeature(SwitchAttribute):
    """UniLED Scene Loop Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_SCENE_LOOP,
            "Loop Scenes",
            "mdi:progress-star",
            "mdi:refresh-auto",
        )


class AudioInputFeature(SelectAttribute):
    """UniLED Sound Input Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_AUDIO_INPUT,
            "Audio Input",
            "mdi:microphone",
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )


class AudioSensitivityFeature(NumberAttribute):
    """UniLED Sensitivity Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(
            ATTR_UL_SENSITIVITY,
            "Audio Input Sensitivity",
            "mdi:knob",
            max,
            min,
            inc,
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )


class LightModeFeature(SelectAttribute):
    """UniLED Light Mode Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_LIGHT_MODE,
            "Light Mode",
            "mdi:palette",
            group=UniledGroup.NEEDS_ON,
        )


class LightTypeFeature(SelectAttribute):
    """UniLED Light Type Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_LIGHT_TYPE,
            "Light Type",
            "mdi:lightbulb-question",
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )
        self._reload = True


class ChipTypeFeature(SelectAttribute):
    """UniLED Chip Type Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_CHIP_TYPE,
            "Chip Type",
            "mdi:chip",
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )


class ChipOrderFeature(SelectAttribute):
    """UniLED Chip Order Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_CHIP_ORDER,
            "Chip Order",
            "mdi:palette",
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )


class OnOffEffectFeature(SelectAttribute):
    """UniLED On/Off Effect Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_ONOFF_EFFECT,
            "On/Off Effect",
            "mdi:creation-outline",
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )


class OnOffSpeedFeature(SelectAttribute):
    """UniLED On/Off Mode Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_ONOFF_SPEED,
            "On/Off Speed",
            "mdi:speedometer",
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )


class OnOffPixelsFeature(NumberAttribute):
    """UniLED On/Off Pixels Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(
            ATTR_UL_ONOFF_PIXELS,
            "On/Off Pixels",
            "mdi:pencil-ruler",
            max,
            min,
            inc,
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )


class OnPowerFeature(SelectAttribute):
    """UniLED Light Type Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_ON_POWER,
            "On Power Restore",
            "mdi:lightning-bolt",
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )


class CoexistenceFeature(SwitchAttribute):
    """UniLED Effect Length Feature Class"""

    def __init__(self) -> None:
        super().__init__(
            ATTR_UL_COEXISTENCE,
            "Color/White Coexistence",
            "mdi:lightbulb-multiple",
            "mdi:lightbulb",
            group=UniledGroup.CONFIGURATION,
        )


class SegmentCountFeature(NumberAttribute):
    """UniLED Segment Count Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(
            ATTR_UL_SEGMENT_COUNT,
            "Segments",
            "mdi:numeric",
            max,
            min,
            inc,
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )


class SegmentPixelsFeature(OnOffPixelsFeature):
    """UniLED Segment Pixels Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(max, min, inc)
        self._attr = ATTR_UL_SEGMENT_PIXELS
        self._name = "Segment Pixels"


class ColorTemperatureFeature(NumberAttribute):
    """UniLED Temperature Feature Class"""

    def __init__(self, max: int, min: int = 1, inc: int = 1) -> None:
        super().__init__(
            ATTR_HA_COLOR_TEMP_KELVIN,
            "Color Temperature",
            "mdi:temperature-kelvin",
            "temperature",
            max,
            min,
            inc,
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )
