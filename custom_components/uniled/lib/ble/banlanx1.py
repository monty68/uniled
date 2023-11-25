"""UniLED BLE Devices - SP LED (BanlanX v1)"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Final

from ..const import *  # I know!
from ..channel import UniledChannel
from ..features import (
    UniledAttribute,
)
from ..artifacts import (
    UNKNOWN,
    UNILED_CHIP_ORDER_3COLOR,
    UNILED_CHIP_ORDER_4COLOR,
    UNILEDInput,
    UNILEDEffectType,
    UNILEDEffects,
)
from .device import (
    BASE_UUID_FORMAT as BANLANX1_UUID_FORMAT,
    ParseNotificationError,
    UniledBleDevice,
    UniledBleModel,
)

import logging

_LOGGER = logging.getLogger(__name__)

BANLANX1_MODEL_NUMBER_SP601E: Final = 0x601E
BANLANX1_MODEL_NUMBER_SP602E: Final = 0x602E
BANLANX1_MODEL_NUMBER_SP608E: Final = 0x608E
BANLANX1_MANUFACTURER: Final = "SPLED (BanlanX)"
BANLANX1_MANUFACTURER_ID: Final = 20563
BANLANX1_UUID_SERVICE = [BANLANX1_UUID_FORMAT.format(part) for part in ["ffe0"]]
BANLANX1_UUID_WRITE = [BANLANX1_UUID_FORMAT.format(part) for part in ["ffe1"]]
BANLANX1_UUID_READ = []

##
## BanlanX type 4 Protocol Implementation
##
@dataclass(frozen=True)
class BanlanX1(UniledBleModel):
    """BanlanX type 1 Protocol Implementation"""


##
## SP601E
##
SP601E = BanlanX1(
    model_num=BANLANX1_MODEL_NUMBER_SP601E,
    model_name="SP601E",
    description="2x RGB SPI (Music) Controller",
    manufacturer=BANLANX1_MANUFACTURER,
    channels=2,
    ble_manufacturer_id=BANLANX1_MANUFACTURER_ID,
    ble_manufacturer_data=b"\x01\x02",
    ble_service_uuids=BANLANX1_UUID_SERVICE,
    ble_write_uuids=BANLANX1_UUID_WRITE,
    ble_read_uuids=BANLANX1_UUID_READ,
)

##
## SP602E
##
SP602E = BanlanX1(
    model_num=BANLANX1_MODEL_NUMBER_SP602E,
    model_name="SP602E",
    description="4x RGB SPI (Music) Controller",
    manufacturer=BANLANX1_MANUFACTURER,
    channels=4,
    ble_manufacturer_id=BANLANX1_MANUFACTURER_ID,
    ble_manufacturer_data=[b"\x02\x02"],
    ble_service_uuids=BANLANX1_UUID_SERVICE,
    ble_write_uuids=BANLANX1_UUID_WRITE,
    ble_read_uuids=BANLANX1_UUID_READ,
)

##
## SP608E
##
SP608E = BanlanX1(
    model_num=BANLANX1_MODEL_NUMBER_SP608E,
    model_name="SP608E",
    description="8x RGB SPI (Music) Controller",
    manufacturer=BANLANX1_MANUFACTURER,
    channels=8,
    ble_manufacturer_id=BANLANX1_MANUFACTURER_ID,
    ble_manufacturer_data=[b"\x08\x02"],
    ble_service_uuids=BANLANX1_UUID_SERVICE,
    ble_write_uuids=BANLANX1_UUID_WRITE,
    ble_read_uuids=BANLANX1_UUID_READ,
)
