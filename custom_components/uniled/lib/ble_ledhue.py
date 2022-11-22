"""UniLED BLE Devices - SP110E from SPLED (LedHue)"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final
from enum import IntEnum

from .artifacts import (
    UNKNOWN,
    UNILEDModelType,
    UNILEDEffectType,
    UNILEDEffects,
)
from .states import UNILEDStatus
from .helpers import StrEnum
from .classes import UNILEDDevice, UNILEDChannel
from .ble_model import UNILEDBLEModel, BASE_UUID_FORMAT as LEDHUE_UUID_FORMAT

import logging

_LOGGER = logging.getLogger(__name__)

LEDHUE_MANUFACTURER_ID: Final = 0
LEDHUE_MANUFACTURER: Final = "SPLED (LedHue)"
LEDHUE_MODEL_NUMBER_SP110E: Final = 0x110E
LEDHUE_MODEL_NAME_SP110E: Final = "SP107E"
LEDHUE_LOCAL_NAME_SP110E: Final = LEDHUE_MODEL_NAME_SP110E


@dataclass(frozen=True)
class _LEDHUE(UNILEDBLEModel):
    """LedHue Protocol Implementation"""


##
## SP110E
##
SP110E = _LEDHUE(
    model_num=LEDHUE_MODEL_NUMBER_SP110E,
    model_name=LEDHUE_MODEL_NAME_SP110E,
    model_type=UNILEDModelType.STRIP,
    description="BLE RGB(W) Controller",
    manufacturer=LEDHUE_MANUFACTURER,
    manufacturer_id=LEDHUE_MANUFACTURER_ID,
    manufacturer_data=b"\x00\x00",
    resolve_protocol=False,
    channels=1,
    needs_on=True,
    service_uuids=[LEDHUE_UUID_FORMAT.format(part) for part in ["ffe0", "ffb0"]],
    write_uuids=[LEDHUE_UUID_FORMAT.format(part) for part in ["ffe1"]],
    read_uuids=[],
)
