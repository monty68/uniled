"""UniLED NET Devices - SP LED (BanlanX SP630E)"""

from __future__ import annotations
from typing import Final

from ..discovery import UniledProxy
from ..sptech_model import SPTechModel
from ..sptech_conf import (
    SPTechSig,
    SPTechConf,
    CFG_81 as SP6XXE_81,
    CFG_82 as SP6XXE_82,
    CFG_83 as SP6XXE_83,
    CFG_84 as SP6XXE_84,
    CFG_85 as SP6XXE_85,
    CFG_86 as SP6XXE_86,
    CFG_87 as SP6XXE_87,
    CFG_88 as SP6XXE_88,
    CFG_89 as SP6XXE_89,
    CFG_8A as SP6XXE_8A,
    CFG_8B as SP6XXE_8B,
    CFG_8C as SP6XXE_8C,
    CFG_8D as SP6XXE_8D,
    CFG_8E as SP6XXE_8E,
)
from .device import (
    UUID_BASE_FORMAT as UUID_FORMAT,
    ParseNotificationError,
    UniledBleDevice,
    UniledBleModel,
    BLEDevice,
    AdvertisementData,
)
import logging

_LOGGER = logging.getLogger(__name__)


##
## BanlanX - SP63xE and SP64xE BLE Protocol Implementation
##
class SPTechBleModel(SPTechModel, UniledBleModel):
    """BanlanX - SP56xE/SP64xE BLE Protocol Implementation"""

    MANUFACTURER_ID: Final = 20563
    UUID_SERVICE: Final = [UUID_FORMAT.format(part) for part in ["e0ff", "ffe0"]]
    UUID_WRITE: Final = [UUID_FORMAT.format(part) for part in ["ffe1"]]

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
            ble_manufacturer_id=self.MANUFACTURER_ID,
            ble_service_uuids=self.UUID_SERVICE,
            ble_write_uuids=self.UUID_WRITE,
            ble_read_uuids=[],
            ble_notify_uuids=[],
            ble_manufacturer_data=bytearray([code & 0xFF, 0x10]),
        )

    def parse_notifications(
        self,
        device: UniledBleDevice,
        sender: int,
        data: bytearray,
    ) -> bool:
        """Parse notification message(s)"""
        _HEADER_LENGTH = 6
        _HEADER_BYTE = 0x53
        _MESSAGE_TYPE = 1
        _MESSAGE_KEY = 2
        _MESSAGE_LENGTH = 5

        packet_length = len(data)
        if packet_length < _HEADER_LENGTH:
            raise ParseNotificationError("Packet is undersized")
        if data[0] != _HEADER_BYTE or data[_MESSAGE_TYPE] != self.cmd.STATUS_QUERY:
            raise ParseNotificationError("Packet is invalid")
        message_length = data[_MESSAGE_LENGTH]
        expected_length = message_length + _HEADER_LENGTH
        if packet_length != expected_length:
            raise ParseNotificationError(
                f"Packet payload size mismatch: {packet_length} vs {expected_length}"
            )
        if message_key := data[_MESSAGE_KEY]:
            raise ParseNotificationError("Encoded packet - currently unsupported")
        return self.decode_response_payload(
            device, (), data[:_HEADER_LENGTH], data[_HEADER_LENGTH:]
        )


##
## BanlanX - SP6xxE Device Proxy
##
class SP6XXE(UniledProxy):
    """BanlanX - SP6xxE Device Proxy"""

    class SP630E(SPTechSig):
        info = "RGB(CW) SPI/PWM (Music) Controller"
        code = {0x1F: "SP630E"}
        conf = {
            0x81: SP6XXE_81(),  # PWM Mono
            0x83: SP6XXE_83(),  # PWM CCT
            0x85: SP6XXE_85(),  # PWM RGB
            0x87: SP6XXE_87(),  # PWM RGBW
            0x8A: SP6XXE_8A(),  # PWM RGBCCT
            0x82: SP6XXE_82(),  # SPI - Mono
            0x84: SP6XXE_84(),  # SPI - CCT (1)
            0x8D: SP6XXE_8D(),  # SPI - CCT (2)
            0x86: SP6XXE_86(),  # SPI - RGB
            0x88: SP6XXE_88(),  # SPI - RGBW
            0x8B: SP6XXE_8B(),  # SPI - RGBCCT (1)
            0x8E: SP6XXE_8E(),  # SPI - RGBCCT (2)
            0x89: SP6XXE_89(),  # SPI - RGB + 1 CH PWM
            0x8C: SP6XXE_8C(),  # SPI - RGB + 2 CH PWM
        }

    class SP631E_SP641E(SPTechSig):
        info = "PWM Single Color (Music) Controller"
        code = {0x20: "SP631E", 0x2C: "SP641E"}
        conf = {0x01: SP6XXE_81()}

    class SP632E_SP642E(SPTechSig):
        info = "PWM CCT (Music) Controller"
        code = {0x21: "SP632E", 0x2D: "SP642E", 0x4A: "SP642E"}
        conf = {0x03: SP6XXE_83()}

    class SP633E_SP643E(SPTechSig):
        info = "PWM RGB (Music) Controller"
        code = {0x22: "SP633E", 0x2E: "SP643E"}
        conf = {0x05: SP6XXE_85()}

    class SP634E_SP644E(SPTechSig):
        info = "PWM RGBW (Music) Controller"
        code = {0x23: "SP634E", 0x2F: "SP644E"}
        conf = {0x07: SP6XXE_87()}

    class SP635E_SP645E(SPTechSig):
        info = "PWM RGBCCT (Music) Controller"
        code = {0x24: "SP635E", 0x30: "SP645E"}
        conf = {0x0A: SP6XXE_8A()}

    class SP636E_SP646E(SPTechSig):
        info = "SPI Single Color (Music) Controller"
        code = {0x25: "SP636E", 0x31: "SP646E"}
        conf = {0x02: SP6XXE_82()}

    class SP637E_SP647E(SPTechSig):
        info = "SPI CCT (Music) Controller"
        code = {0x26: "SP637E", 0x32: "SP647E"}
        conf = {0x04: SP6XXE_84(), 0x0D: SP6XXE_8D()}

    class SP638E_SP648E(SPTechSig):
        info = "SPI RGB (Music) Controller"
        code = {0x27: "SP638E", 0x33: "SP648E", 0x45: "SP648E", 0x4C: "SP648E"}
        conf = {0x06: SP6XXE_86()}

    class SP639E_SP649E(SPTechSig):
        info = "SPI RGBW (Music) Controller"
        code = {0x28: "SP639E", 0x34: "SP649E"}
        conf = {0x08: SP6XXE_88()}

    class SP63AE_SP64AE(SPTechSig):
        info = "SPI RGBCCT (Music) Controller"
        code = {0x29: "SP63AE", 0x35: "SP64AE"}
        conf = {0x0B: SP6XXE_8B(), 0x0E: SP6XXE_8E()}

    class SP63BE_SP64BE(SPTechSig):
        info = "SPI RGB+1CH PWM (Music) Controller"
        code = {0x2A: "SP63BE", 0x36: "SP64BE"}
        conf = {0x09: SP6XXE_89()}

    class SP63CE_SP64CE(SPTechSig):
        info = "SPI RGB+2CH PWM (Music) Controller"
        code = {0x2B: "SP63CE", 0x37: "SP64CE"}
        conf = {0x0C: SP6XXE_8C()}

    MODEL_SIGNATURE_LIST: Final = [
        SP630E,
        SP631E_SP641E,
        SP632E_SP642E,
        SP633E_SP643E,
        SP634E_SP644E,
        SP635E_SP645E,
        SP636E_SP646E,
        SP637E_SP647E,
        SP638E_SP648E,
        SP639E_SP649E,
        SP63AE_SP64AE,
        SP63BE_SP64BE,
        SP63CE_SP64CE,
    ]

    def _make_model(self, model: SPTechSig, code: int) -> SPTechBleModel:
        """Instantiate model class"""
        assert code in model.code
        return SPTechBleModel(
            code=code, name=model.code[code], info=model.info, configs=model.conf
        )

    def match_model_name(self, name: str) -> UniledBleModel | None:
        """Match a device model name"""
        for signature in self.MODEL_SIGNATURE_LIST:
            for model_code, model_name in signature.code.items():
                if name != model_name:
                    continue
                return self._make_model(signature, model_code)
        return None

    def match_model_code(self, code: int) -> UniledBleModel | None:
        """Match a device model code"""
        for signature in self.MODEL_SIGNATURE_LIST:
            for model_code, model in signature.code.items():
                if code != model_code:
                    continue
                return self._make_model(signature, model_code)
        return None

    def match_ble_model(self, model: str) -> UniledBleModel | None:
        """Match a device model name"""
        return self.match_model_name(name=model)

    def match_ble_device(
        self, device: BLEDevice, advertisement: AdvertisementData | None = None
    ) -> UniledBleModel | None:
        """Match to one of the SP6xxE devices"""
        if not hasattr(advertisement, "manufacturer_data"):
            return None
        for mid, data in advertisement.manufacturer_data.items():
            # if mid != SPTechBleModel.MANUFACTURER_ID or data[1] != 0x10:
            if mid != SPTechBleModel.MANUFACTURER_ID:
                continue
            if (model := self.match_model_code(code=data[0])) is not None:
                return model
        return None
