"""UniLED BLE Devices - SP110E from SPLED (LedHue)"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final
from enum import IntEnum

from .artifacts import (
    UNKNOWN,
    UNILEDModelType,
    # UNILEDColorOrder,
    UNILEDEffectType,
    UNILEDEffects,
)
from .states import (
    UNILED_STATE_SETUP,
    UNILED_STATE_MUSIC_COLOR,
    UNILED_STATE_COLUMN_COLOR,
    UNILED_STATE_DOT_COLOR,
    UNILEDSetup,
    UNILEDStatus,
)
from .helpers import StrEnum
from .classes import UNILEDDevice, UNILEDChannel
from .ble_banlanx1 import BANLANX1_LED_ORDERS as LEDHUE_LED_ORDERS
from .ble_model import UNILEDBLEModel, BASE_UUID_FORMAT as LEDHUE_UUID_FORMAT

import logging

_LOGGER = logging.getLogger(__name__)

LEDHUE_MANUFACTURER_ID: Final = 0
LEDHUE_MANUFACTURER: Final = "SPLED (LedHue)"
LEDHUE_LOCAL_NAME_SP110E: Final = "SP110E"

@dataclass(frozen=True)
class _LEDHUE(UNILEDBLEModel):
    """LedHue Protocol Implementation"""

##
## SP110E
##
SP110E = _LEDHUE(
    model_num=0x107E,
    model_name="SP107E",
    model_type=UNILEDModelType.STRIP,
    description="BLE RGB(W) Controller",
    manufacturer=LEDHUE_MANUFACTURER,
    manufacturer_id=LEDHUE_MANUFACTURER_ID,
    manufacturer_data=b"\x00\x00",
    resolve_protocol=False,
    channels=1,
    extra_data={},
    service_uuids=[LEDHUE_UUID_FORMAT.format(part) for part in ["ffe0", "ffb0"]],
    write_uuids=[LEDHUE_UUID_FORMAT.format(part) for part in ["ffe1"]],
    read_uuids=[],
)
