"""UniLED BLE Base Model"""
from __future__ import annotations
from dataclasses import dataclass
from abc import abstractmethod

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .classes import UNILEDModel

import logging

_LOGGER = logging.getLogger(__name__)

BASE_UUID_FORMAT = "0000{}-0000-1000-8000-00805f9b34fb"

CONF_UNILEDBLE_SERVICE_UUID = "service_uuid"
CONF_UNILEDBLE_READ_UUIDS = "read_uuids"
CONF_UNILEDBLE_WRITE_UUIDS = "write_uuids"


@dataclass(frozen=True)
class UNILEDBLEModel(UNILEDModel):
    """UniLED BLE Model Class"""

    local_names: list[str] | None
    manufacturer_id: int
    manufacturer_data: bytearray | None
    service_uuids: list[str]
    write_uuids: list[str]
    read_uuids: list[str]
    resolve_protocol: bool

    @abstractmethod
    def is_device_valid(
        self, device: BLEDevice, advertisement: AdvertisementData | None = None
    ) -> bool:
        """Is a device supported by UniLED BLE."""
        for mid, data in advertisement.manufacturer_data.items():
            if self.manufacturer_id != mid:
                continue
            for uuid in self.service_uuids:
                if uuid in advertisement.service_uuids:
                    if self.manufacturer_data is not None:
                        _LOGGER.debug(
                            "%s : %s in %s",
                            mid,
                            self.manufacturer_data.hex(),
                            data.hex(),
                        )
                        if not data.count(self.manufacturer_data):
                            return False
                    return True
        return False
