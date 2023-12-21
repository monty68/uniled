"""Zengge (Mesh) Node"""
from __future__ import annotations
from typing import Final
from ..channel import UniledChannel
from ..ble.device import (
    UNILED_BLE_BAD_RSSI,
    AdvertisementData,
    BLEDevice,
)
from ..attributes import (
    UniledAttribute,
    UniledGroup,
)
from ..const import (
    ATTR_UL_LIGHT_MODE_NUMBER,
    ATTR_UL_MAC_ADDRESS,
    ATTR_UL_NODE_ID,
    ATTR_UL_POWER,
    ATTR_UL_RSSI,
)
from .telink import TELINK_MANUFACTURER_ID, TELINK_MESH_ADDRESS_NONE

ZENGGE_DEVICE_TYPE_LIGHT_STRIP: Final = 2
ZENGGE_DEVICE_TYPE_LIGHT_BULB: Final = 5
ZENGGE_DEVICE_TYPE_PANEL_RGBCCT: Final = 35  # Powered RGB/CCT 4 Group Panel!

import logging

_LOGGER = logging.getLogger(__name__)


##
## Zengge (Node) Feature
##
class ZenggeFeature(UniledAttribute):
    """UniLED Light Feature Class"""

    def __init__(self, node: ZenggeNode) -> None:
        self._extra = (
            ATTR_UL_LIGHT_MODE_NUMBER,
            ATTR_UL_MAC_ADDRESS,
            ATTR_UL_NODE_ID,
            ATTR_UL_RSSI,
        )
        self._attr = ATTR_UL_POWER
        self._type = "light"
        self._node = node

    @property
    def name(self) -> str:
        if self.node.node_type == ZENGGE_DEVICE_TYPE_PANEL_RGBCCT:
            return "Panel"
        if self.node.node_type == ZENGGE_DEVICE_TYPE_LIGHT_STRIP:
            return "Strip"
        return "Light"

    @property
    def icon(self) -> str:
        if self.node.node_type == ZENGGE_DEVICE_TYPE_PANEL_RGBCCT:
            return "mdi:remote"
        if self.node.node_type == ZENGGE_DEVICE_TYPE_LIGHT_STRIP:
            return "mdi:led-strip-variant"
        return "mdi:lightbulb"

    @property
    def node(self) -> ZenggeNode:
        """Return features node"""
        return self._node

    @property
    def key(self) -> str:
        return None


##
## Zengge (Mesh) Node
##
class ZenggeNode(UniledChannel):
    """Zengge Mesh Node"""

    # _device: BLEDevice | None = None
    # _advert: AdvertisementData | None
    # _mesh_id: int

    def __init__(
        self,
        mesh_id: int,
        node_id: int,
        node_type: int = 0,
        node_wiring: int = 0,
        node_mac: str | None = None,
        node_name: str | None = None,
    ):
        """Initialise Zengge Mesh Node"""
        self._device = None
        self._advert = None
        self._mesh_id = mesh_id
        if node_id != 0:
            self._features = [ZenggeFeature(self)]
        self.update(node_type, node_wiring, node_mac, node_name)
        super().__init__(node_id)

    @staticmethod
    def device_mesh_node_id(device: BLEDevice, advert: AdvertisementData):
        if advert is not None and TELINK_MANUFACTURER_ID in advert.manufacturer_data:
            data = advert.manufacturer_data[TELINK_MANUFACTURER_ID]
            # data[6] = ?
            # data[7] = controlType or deviceType
            # data[8] = ?
            # _LOGGER.debug(repr(list(data)))
            return (int.from_bytes(data[:2], byteorder="little"), data[9], data[7])
        return (0, 0, 0)

    def update_device(self, device: BLEDevice | None, advert: AdvertisementData | None):
        """Update BLE device details"""
        self._device = device
        self._advert = advert
        self._mesh_id, self._number, self._type = ZenggeNode.device_mesh_node_id(
            device, advert
        )

    def update(
        self,
        node_type: int = 0,
        node_wiring: int = 0,
        node_mac: str | None = None,
        node_name: str | None = None,
    ) -> None:
        """Update Zengge Mesh Node"""
        self._type = node_type
        self._wiring = node_wiring
        self._address = node_mac
        self._name = node_name

    @property
    def name(self) -> str:
        """Returns the nodes (display) name."""
        if self._name is not None:
            return self._name
        return self.title

    @property
    def title(self) -> str:
        """Returns the nodes title."""
        return f"Node {self.number}"

    @property
    def device(self) -> BLEDevice:
        """Returns attached BLE device"""
        return self._device

    @property
    def address(self) -> BLEDevice:
        """Return attached BLE device address"""
        if isinstance(self.device, BLEDevice):
            return self.device.address
        if not self._address:
            return "??:??:??:??:??:??"
        return self._address

    @property
    def advert(self) -> AdvertisementData:
        """Return attached BLE devices last advert"""
        return self._advert

    @property
    def rssi(self) -> int:
        """Return attached BLE devices last advert"""
        if isinstance(self._advert, AdvertisementData):
            return self._advert.rssi
        return UNILED_BLE_BAD_RSSI

    @property
    def mesh_id(self) -> int:
        """Return nodes mesh ID"""
        return self._mesh_id

    @property
    def node_id(self) -> int:
        """Return nodes ID"""
        return self._number

    @property
    def node_type(self) -> int:
        """Return nodes type"""
        return self._type

    @property
    def node_wiring(self) -> int:
        """Return nodes wiring"""
        return self._wiring
