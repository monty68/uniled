"""UniLED BLE Devices - SP LED (LED Chord)"""
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
    BASE_UUID_FORMAT as LEDCHORD_UUID_FORMAT,
    ParseNotificationError,
    UniledBleDevice,
    UniledBleModel,
)

import logging

_LOGGER = logging.getLogger(__name__)

LEDCHORD_MANUFACTURER_ID: Final = 0
LEDCHORD_MANUFACTURER: Final = "SPLED (LED Chord)"
LEDCHORD_MODEL_NUMBER_SP107E: Final = 0x107E
LEDCHORD_UUID_SERVICE = [LEDCHORD_UUID_FORMAT.format(part) for part in ["ffe0"]]
LEDCHORD_UUID_WRITE = [LEDCHORD_UUID_FORMAT.format(part) for part in ["ffe1"]]
LEDCHORD_UUID_READ = []

##
## LED Chord Protocol Implementation
##
@dataclass(frozen=True)
class _LEDCHORD(UniledBleModel):
    """LED Hue Protocol Implementation"""

##
## SP107E
##
SP107E = _LEDCHORD(
    model_num=LEDCHORD_MODEL_NUMBER_SP107E,
    model_name="SP107E",
    description="RGB(W) SPI (Music) Controller",
    manufacturer=LEDCHORD_MANUFACTURER,
    channels=1,
    ble_manufacturer_id=LEDCHORD_MANUFACTURER_ID,
    ble_manufacturer_data=b"\x00\x00",
    ble_service_uuids=LEDCHORD_UUID_SERVICE,
    ble_write_uuids=LEDCHORD_UUID_WRITE,
    ble_read_uuids=LEDCHORD_UUID_READ,
)