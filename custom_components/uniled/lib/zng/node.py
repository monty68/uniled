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
    ATTR_HA_TRANSITION,
    ATTR_UL_LIGHT_MODE_NUMBER,
    ATTR_UL_MAC_ADDRESS,
    ATTR_UL_NODE_ID,
    ATTR_UL_POWER,
    ATTR_UL_RSSI,
    ATTR_UL_STATUS,
)
from .zengge import *

import logging

_LOGGER = logging.getLogger(__name__)


##
## Zengge (Node) Feature
##
class ZenggeFeature(UniledAttribute):
    """UniLED Light Feature Class"""

    def __init__(self, node: ZenggeNode) -> None:
        self._node = node
        super().__init__(
            "light",
            ATTR_UL_POWER,
            None,
            None,
            None,
            extra=(
                ATTR_UL_NODE_ID,
                ATTR_UL_MAC_ADDRESS,
                ATTR_UL_RSSI,
                ATTR_UL_LIGHT_MODE_NUMBER,
                ATTR_HA_TRANSITION,
            ),
        )

    @property
    def attr(self) -> str:
        if self.node.node_type == ZENGGE_DEVICE_TYPE_PANEL_RGBCCT:
            return ATTR_UL_STATUS
        return self._attr

    @property
    def platform(self) -> str:
        if self.node.node_type == ZENGGE_DEVICE_TYPE_PANEL_RGBCCT:
            return "sensor"
        return "light"

    @property
    def name(self) -> str:
        if self.node.node_type == ZENGGE_DEVICE_TYPE_PANEL_RGBCCT:
            return "Panel"
        if self.node.node_type == ZENGGE_DEVICE_TYPE_LIGHT_STRIP:
            return "Strip"
        if self.node.node_type == ZENGGE_DEVICE_TYPE_LIGHT_BULB:
            return "Bulb"
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

    def __init__(self, mesh_uuid: int, node_id: int, data: dict = {}):
        """Initialise Zengge Mesh Node"""
        self._device = None
        self._advert = None
        self._data: dict = {
            "meshAddress": node_id,
            "meshUUID": mesh_uuid,
        }
        super().__init__(node_id)
        self.update_data(data)

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
        mesh_id, self._number, type = ZenggeNode.device_mesh_node_id(device, advert)
        self._data["deviceType"] = type

    def update_data(self, data: dict) -> None:
        """Update Zengge Mesh Node"""
        if not data:
            return
        self._data = {**data, **self._data}
        if self.number != 0:
            self._features = [ZenggeFeature(self)]
        _LOGGER.debug("Node %s data: %s", self.node_id, self._data)

    @property
    def mesh_uuid(self) -> int:
        """Return nodes mesh ID"""
        return self._data.get("meshUUID", ZENGGE_DEFAULT_MESH_UUID)

    @property
    def mesh_key(self) -> str:
        """Mesh Key"""
        return self._data.get("meshKey", ZENGGE_DEFAULT_MESH_KEY)

    @property
    def mesh_pass(self) -> str:
        """Mesh Password"""
        return self._data.get("meshPassword", ZENGGE_DEFAULT_MESH_PASS)

    @property
    def mesh_token(self) -> str:
        """Mesh Long Term Token"""
        return self._data.get("meshLTK", ZENGGE_DEFAULT_MESH_TOKEN)

    @property
    def node_id(self) -> int:
        """Return nodes ID"""
        return self._data.get("meshAddress", 0)

    @property
    def node_area(self) -> int:
        """Return nodes area (location)"""
        return self._data.get("deviceArea", None)

    @property
    def node_type(self) -> int:
        """Return nodes type"""
        return self._data.get("deviceType", 0)

    @property
    def node_wiring(self) -> int:
        """Return nodes wiring"""
        return self._data.get("wiringType", 0)

    @property
    def name(self) -> str:
        """Returns the nodes (display) name."""
        return self._data.get("displayName", f"Node {self.number}")

    @property
    def identity(self) -> str:
        """Returns the nodes identity string."""
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
        return self._data.get("macAddress", "??:??:??:??:??:??")

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
