"""UniLED SPTech Light Type Configurations"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Final
from .const import UNILED_UNKNOWN
from .sptech_effects import (
    UNILEDEffectType,
    UNILEDEffects,
    SPTechFX,
)
from .chips import (
    UNILED_CHIP_ORDER_CW,
    UNILED_CHIP_ORDER_123,
    UNILED_CHIP_ORDER_CWX,
    UNILED_CHIP_ORDER_RGB,
    UNILED_CHIP_ORDER_RGBW,
    UNILED_CHIP_ORDER_RGBCW,
)

##
## Chip Information
##
dataclass(frozen=True)
class SPTechChips:
    """BanlanX SPTech Chip Information"""
    CHIP_ORDER_CW: Final = UNILED_CHIP_ORDER_CW
    CHIP_ORDER_123: Final = UNILED_CHIP_ORDER_123
    CHIP_ORDER_CWX: Final = UNILED_CHIP_ORDER_CWX
    CHIP_ORDER_RGB: Final = UNILED_CHIP_ORDER_RGB
    CHIP_ORDER_RGBW: Final = UNILED_CHIP_ORDER_RGBW
    CHIP_ORDER_RGBCW: Final = UNILED_CHIP_ORDER_RGBCW

##
## Device Signatures
##
dataclass(frozen=True)
class SPTechSig:
    """BanlanX SPTech Device Signature"""

    info: str
    code: dict[int, str]
    conf: dict[int, Any]


##
## BanlanX SPTech Base Configuration
##
@dataclass
class SPTechConf:
    """BanlanX SPTech Light Type Base Configuration"""

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
class CFG_81(SPTechConf):
    def __init__(self):
        super().__init__()
        self.name = "1 CH PWM - Single Color"
        self.pwm = True
        self.white = True
        self.effects = {
            SPTechFX.MODE_STATIC_WHITE: SPTechFX.DICTOF_EFFECTS_STATIC_WHITE,
            SPTechFX.MODE_DYNAMIC_WHITE: SPTechFX.DICTOF_PWM_EFFECTS_DYNAMIC_WHITE,
            SPTechFX.MODE_SOUND_WHITE: SPTechFX.DICTOF_PWM_EFFECTS_SOUND_WHITE,
        }


class CFG_83(CFG_81):
    def __init__(self):
        super().__init__()
        self.name = "2 CH PWM - CCT"
        self.cct = True
        self.order = UNILED_CHIP_ORDER_CW


class CFG_85(SPTechConf):
    def __init__(self):
        super().__init__()
        self.name = "3 CH PWM - RGB"
        self.pwm = True
        self.hue = True
        self.order = UNILED_CHIP_ORDER_RGB
        self.effects = {
            SPTechFX.MODE_STATIC_COLOR: SPTechFX.DICTOF_EFFECTS_STATIC_COLOR,
            SPTechFX.MODE_DYNAMIC_COLOR: SPTechFX.DICTOF_PWM_EFFECTS_DYNAMIC_COLOR,
            SPTechFX.MODE_SOUND_COLOR: SPTechFX.DICTOF_PWM_EFFECTS_SOUND_COLOR,
            SPTechFX.MODE_CUSTOM_SOLID: SPTechFX.DICTOF_PWM_EFFECTS_CUSTOM_COLOR,
        }


class CFG_87(SPTechConf):
    def __init__(self):
        super().__init__()
        self.name = "4 CH PWM - RGBW"
        self.pwm = True
        self.hue = True
        self.white = True
        self.coexistence = True
        self.order = UNILED_CHIP_ORDER_RGBW
        self.effects = {
            SPTechFX.MODE_STATIC_COLOR: SPTechFX.DICTOF_EFFECTS_STATIC_COLOR,
            SPTechFX.MODE_STATIC_WHITE: SPTechFX.DICTOF_EFFECTS_STATIC_WHITE,
            SPTechFX.MODE_DYNAMIC_COLOR: SPTechFX.DICTOF_PWM_EFFECTS_DYNAMIC_COLOR,
            SPTechFX.MODE_DYNAMIC_WHITE: SPTechFX.DICTOF_PWM_EFFECTS_DYNAMIC_WHITE,
            SPTechFX.MODE_SOUND_COLOR: SPTechFX.DICTOF_PWM_EFFECTS_SOUND_COLOR,
            SPTechFX.MODE_SOUND_WHITE: SPTechFX.DICTOF_PWM_EFFECTS_SOUND_WHITE,
            SPTechFX.MODE_CUSTOM_SOLID: SPTechFX.DICTOF_PWM_EFFECTS_CUSTOM_COLOR,
        }


class CFG_8A(CFG_87):
    def __init__(self):
        super().__init__()
        self.name = "5 CH PWM - RGBCCT"
        self.cct = True
        self.order = UNILED_CHIP_ORDER_RGBCW


class CFG_82(SPTechConf):
    def __init__(self):
        super().__init__()
        self.name = "SPI - Single Color"
        self.spi = True
        self.white = True
        self.order = UNILED_CHIP_ORDER_123
        self.effects = {
            SPTechFX.MODE_STATIC_WHITE: SPTechFX.DICTOF_EFFECTS_STATIC_WHITE,
            SPTechFX.MODE_DYNAMIC_WHITE: SPTechFX.DICTOF_SPI_EFFECTS_DYNAMIC_WHITE,
            SPTechFX.MODE_SOUND_WHITE: SPTechFX.DICTOF_SPI_EFFECTS_SOUND_WHITE,
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


class CFG_86(SPTechConf):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGB"
        self.spi = True
        self.hue = True
        self.order = UNILED_CHIP_ORDER_RGB
        self.effects = {
            SPTechFX.MODE_STATIC_COLOR: SPTechFX.DICTOF_EFFECTS_STATIC_COLOR,
            SPTechFX.MODE_DYNAMIC_COLOR: SPTechFX.DICTOF_SPI_EFFECTS_DYNAMIC_COLOR,
            SPTechFX.MODE_SOUND_COLOR: SPTechFX.DICTOF_SPI_EFFECTS_SOUND_COLOR,
            SPTechFX.MODE_CUSTOM_SOLID: SPTechFX.DICTOF_SPI_EFFECTS_CUSTOM_SOLID,
        }


class CFG_88(SPTechConf):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGBW"
        self.spi = True
        self.hue = True
        self.white = True
        self.coexistence = True
        self.order = UNILED_CHIP_ORDER_RGBW
        self.effects = {
            SPTechFX.MODE_STATIC_COLOR: SPTechFX.DICTOF_EFFECTS_STATIC_COLOR,
            SPTechFX.MODE_STATIC_WHITE: SPTechFX.DICTOF_EFFECTS_STATIC_WHITE,
            SPTechFX.MODE_DYNAMIC_COLOR: SPTechFX.DICTOF_SPI_EFFECTS_DYNAMIC_COLOR,
            SPTechFX.MODE_DYNAMIC_WHITE: SPTechFX.DICTOF_SPI_EFFECTS_DYNAMIC_WHITE,
            SPTechFX.MODE_SOUND_COLOR: SPTechFX.DICTOF_SPI_EFFECTS_SOUND_COLOR,
            SPTechFX.MODE_SOUND_WHITE: SPTechFX.DICTOF_SPI_EFFECTS_SOUND_WHITE,
            SPTechFX.MODE_CUSTOM_SOLID: SPTechFX.DICTOF_SPI_EFFECTS_CUSTOM_SOLID,
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


class CFG_89(SPTechConf):
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
            SPTechFX.MODE_STATIC_COLOR: SPTechFX.DICTOF_EFFECTS_STATIC_COLOR,
            SPTechFX.MODE_STATIC_WHITE: SPTechFX.DICTOF_EFFECTS_STATIC_WHITE,
            SPTechFX.MODE_DYNAMIC_COLOR: SPTechFX.DICTOF_SPI_EFFECTS_DYNAMIC_COLOR,
            SPTechFX.MODE_DYNAMIC_WHITE: SPTechFX.DICTOF_PWM_EFFECTS_DYNAMIC_WHITE,
            SPTechFX.MODE_SOUND_COLOR: SPTechFX.DICTOF_SPI_EFFECTS_SOUND_COLOR,
            SPTechFX.MODE_SOUND_WHITE: SPTechFX.DICTOF_PWM_EFFECTS_SOUND_WHITE,
            SPTechFX.MODE_CUSTOM_SOLID: SPTechFX.DICTOF_SPI_EFFECTS_CUSTOM_SOLID,
        }


class CFG_8C(CFG_89):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGB + 2 CH PWM"
        self.cct = True
        self.order = UNILED_CHIP_ORDER_RGBCW
