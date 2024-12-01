"""UniLED NET Devices - SP LED (BanlanX SP530E)"""

from __future__ import annotations
from typing import Final
from itertools import chain
from .model import UniledNetModel
from .device import UniledNetDevice
from ..discovery import UniledProxy
from ..effects import UNILEDEffects
from ..sptech_model import SPTechModel
from ..sptech_effects import _FX_STATIC, _FX_DYNAMIC, _FX_SOUND, SPTechFX
from ..sptech_conf import (
    SPTechChips,
    SPTechSig,
    SPTechConf,
    CFG_81 as SP5XXE_81,
    CFG_82 as SP5XXE_82,
    CFG_83 as SP5XXE_83,
    CFG_84 as SP5XXE_84,
    CFG_85 as SP5XXE_85,
    # CFG_86 as SP5XXE_86,
    CFG_87 as SP5XXE_87,
    CFG_88 as SP5XXE_88,
    CFG_89 as SP5XXE_89,
    CFG_8A as SP5XXE_8A,
    CFG_8B as SP5XXE_8B,
    CFG_8C as SP5XXE_8C,
    CFG_8D as SP5XXE_8D,
    CFG_8E as SP5XXE_8E,
)

import logging

_LOGGER = logging.getLogger(__name__)


##
## BanlanX - SP53xE and SP54xE Network Protocol Implementation
##
class SPTechNetModel(SPTechModel, UniledNetModel):
    """BanlanX - SP53xE/SP54xE Network Protocol Implementation"""

    DICTOF_SPI_EFFECTS_SOUND_COLOR: Final = {
        0x01: _FX_SOUND("Sound - Music Mode 1"),
        0x02: _FX_SOUND("Sound - Music Mode 2", True),
        0x03: _FX_SOUND("Sound - Music Mode 3"),
        0x04: _FX_SOUND("Sound - Music Mode 4", True),
        0x05: _FX_SOUND("Sound - Music Mode 5", False, True),
    }

    DICTOF_SPI_EFFECTS_CUSTOM_SOLID: Final = dict(
        chain.from_iterable(
            d.items()
            for d in (
                SPTechFX.DICTOF_SPI_EFFECTS_CUSTOM_SOLID,
                {0x13: _FX_DYNAMIC("Firework")},
            )
        )
    )

    def __init__(
        self,
        code: int,
        name: str,
        info: str,
        configs: dict[int, SPTechConf],
    ):
        self.configs = configs
        super().__init__(
            model_code=code,
            model_name=name,
            model_info=info,
            manufacturer=self.MANUFACTURER_NAME,
            channels=1,
            net_port=8587,
            net_close=False,
        )


##
## SP530E Specific Configuration(s)
##
class SP5XXE_86(SPTechConf):
    def __init__(self):
        super().__init__()
        self.name = "SPI - RGB"
        self.spi = True
        self.hue = True
        self.order = SPTechChips.CHIP_ORDER_RGB
        self.effects = {
            SPTechFX.MODE_STATIC_COLOR: SPTechFX.DICTOF_EFFECTS_STATIC_COLOR,
            SPTechFX.MODE_DYNAMIC_COLOR: SPTechFX.DICTOF_SPI_EFFECTS_DYNAMIC_COLOR,
            SPTechFX.MODE_SOUND_COLOR: SPTechNetModel.DICTOF_SPI_EFFECTS_SOUND_COLOR,
            SPTechFX.MODE_CUSTOM_SOLID: SPTechNetModel.DICTOF_SPI_EFFECTS_CUSTOM_SOLID,
            SPTechFX.MODE_CUSTOM_GRADIENT: SPTechFX.DICTOF_SPI_EFFECTS_CUSTOM_GRADIENT,
        }


##
## BanlanX - SP5xxE Device Proxy
##
class SP5XXE(UniledProxy):
    """BanlanX - SP5xxE Device Proxy"""

    class SP530E(SPTechSig):
        info = "RGB(CW) SPI/PWM (Music) Controller"
        code = {0x4E: "SP530E"}
        conf = {
            0x81: SP5XXE_81(),  # PWM Mono
            0x83: SP5XXE_83(),  # PWM CCT
            0x85: SP5XXE_85(),  # PWM RGB
            0x87: SP5XXE_87(),  # PWM RGBW
            0x8A: SP5XXE_8A(),  # PWM RGBCCT
            0x82: SP5XXE_82(),  # SPI - Mono
            0x84: SP5XXE_84(),  # SPI - CCT (1)
            0x8D: SP5XXE_8D(),  # SPI - CCT (2)
            0x86: SP5XXE_86(),  # SPI - RGB
            0x88: SP5XXE_88(),  # SPI - RGBW
            0x8B: SP5XXE_8B(),  # SPI - RGBCCT (1)
            0x8E: SP5XXE_8E(),  # SPI - RGBCCT (2)
            0x89: SP5XXE_89(),  # SPI - RGB + 1 CH PWM
            0x8C: SP5XXE_8C(),  # SPI - RGB + 2 CH PWM
        }

    MODEL_SIGNATURE_LIST: Final = [
        SP530E,
    ]

    def _make_model(self, model: SPTechSig, code: int) -> SPTechNetModel:
        """Instantiate model class"""
        assert code in model.code
        return SPTechNetModel(
            code=code, name=model.code[code], info=model.info, configs=model.conf
        )

    def match_model_name(self, name: str) -> UniledNetModel | None:
        """Match a device model name"""
        for signature in self.MODEL_SIGNATURE_LIST:
            for model_code, model_name in signature.code.items():
                if name != model_name:
                    continue
                return self._make_model(signature, model_code)
        return None

    def match_model_code(self, code: int) -> UniledNetModel | None:
        """Match a device model name"""
        for signature in self.MODEL_SIGNATURE_LIST:
            for model_code, model in signature.code.items():
                if code != model_code:
                    continue
                return self._make_model(signature, model_code)
        return None
