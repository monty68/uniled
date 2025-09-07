"""UniLED NET Devices - SP LED (BanlanX SP530E)"""

from __future__ import annotations

from itertools import chain
import logging
from typing import Final

from ..discovery import UniledProxy
from ..effects import UNILEDEffects
from ..sptech_conf import (
    CFG_8A as SP5XXE_8A,
    CFG_8B as SP5XXE_8B,
    CFG_8C as SP5XXE_8C,
    CFG_8D as SP5XXE_8D,
    CFG_8E as SP5XXE_8E,
    CFG_81 as SP5XXE_81,
    CFG_82 as SP5XXE_82,
    CFG_83 as SP5XXE_83,
    CFG_84 as SP5XXE_84,
    CFG_85 as SP5XXE_85,
    # CFG_86 as SP5XXE_86,
    CFG_87 as SP5XXE_87,
    # CFG_88 as SP5XXE_88,
    CFG_89 as SP5XXE_89,
    SPTechChips,
    SPTechConf,
    SPTechSig,
)
from ..sptech_effects import _FX_DYNAMIC, _FX_SOUND, _FX_STATIC, SPTechFX
from ..sptech_model import SPTechModel
from .device import UniledNetDevice
from .model import UniledNetModel

_LOGGER = logging.getLogger(__name__)


##
## BanlanX - SP53xE and SP54xE Network Protocol Implementation
##
class SPTechNetModel(SPTechModel, UniledNetModel):
    """BanlanX - SP53xE/SP54xE Network Protocol Implementation."""

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
    ) -> None:
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
## SP5xxE Configuration(s)
##
class SP5XXE_86(SPTechConf):
    def __init__(self) -> None:
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


class SP5XXE_88(SPTechConf):
    def __init__(self) -> None:
        super().__init__()
        self.name = "SPI - RGBW"
        self.spi = True
        self.hue = True
        self.white = True
        self.coexistence = True
        self.order = SPTechChips.CHIP_ORDER_RGBW
        self.effects = {
            SPTechFX.MODE_STATIC_COLOR: SPTechFX.DICTOF_EFFECTS_STATIC_COLOR,
            SPTechFX.MODE_STATIC_WHITE: SPTechFX.DICTOF_EFFECTS_STATIC_WHITE,
            SPTechFX.MODE_DYNAMIC_COLOR: SPTechFX.DICTOF_SPI_EFFECTS_DYNAMIC_COLOR,
            SPTechFX.MODE_DYNAMIC_WHITE: SPTechFX.DICTOF_SPI_EFFECTS_DYNAMIC_WHITE,
            SPTechFX.MODE_SOUND_COLOR: SPTechNetModel.DICTOF_SPI_EFFECTS_SOUND_COLOR,
            SPTechFX.MODE_SOUND_WHITE: SPTechFX.DICTOF_SPI_EFFECTS_SOUND_WHITE,
            SPTechFX.MODE_CUSTOM_SOLID: SPTechNetModel.DICTOF_SPI_EFFECTS_CUSTOM_SOLID,
            SPTechFX.MODE_CUSTOM_GRADIENT: SPTechFX.DICTOF_SPI_EFFECTS_CUSTOM_GRADIENT,
        }


##
## BanlanX - SP5xxE Device Proxy
##
class SP5XXE(UniledProxy):
    """BanlanX - SP5xxE Device Proxy."""

    class SP530E(SPTechSig):
        """SP530E."""

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

    class SP538E_SP548E(SPTechSig):
        """SP538E & SP548E."""

        info = "SPI RGB (Music) Controller"
        code = {0x56: "SP538E", 0x63: "SP548E", 0x69: "SP548E"}
        conf = {0x06: SP5XXE_86()}

    class SP537E(SPTechSig):
        """SP537E."""

        info = "SPI CCT (Music) Controller"
        code = {0x55: "SP537E"}
        conf = {0x04: SP5XXE_84(), 0x0D: SP5XXE_8D()}

    class SP539E_SP549E(SPTechSig):
        """SP539E & SP549E."""

        info = "SPI RGBW (Music) Controller"
        code = {0x57: "SP539E", 0x64: "SP549E"}
        conf = {0x08: SP5XXE_88()}

    MODEL_SIGNATURE_LIST: Final = [
        SP530E,
        SP537E,
        SP538E_SP548E,
        SP539E_SP549E,
    ]

    def _make_model(self, model: SPTechSig, code: int) -> SPTechNetModel:
        """Instantiate model class."""
        assert code in model.code
        return SPTechNetModel(
            code=code, name=model.code[code], info=model.info, configs=model.conf
        )

    def match_model_name(self, name: str) -> UniledNetModel | None:
        """Match a device model name."""
        for signature in self.MODEL_SIGNATURE_LIST:
            for model_code, model_name in signature.code.items():
                if name != model_name:
                    continue
                return self._make_model(signature, model_code)
        return None

    def match_model_code(self, code: int) -> UniledNetModel | None:
        """Match a device model name."""
        for signature in self.MODEL_SIGNATURE_LIST:
            for model_code, model in signature.code.items():
                if code != model_code:
                    continue
                return self._make_model(signature, model_code)
        return None
