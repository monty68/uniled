"""UniLED ZNG (Zengge Mesh) Device Handler."""
##
## With huge thanks to SleepyNinja0o for the great work deciphering and developing code for Zengge mesh devices
##
## https://github.com/SleepyNinja0o
##
from __future__ import annotations
from datetime import timedelta
from typing import Any, Final
from os import urandom

from . import packetutils as pckt
from .telink import *
from .cloud import MagicHue
from .node import (
    ZENGGE_DEVICE_TYPE_LIGHT_BULB,
    ZENGGE_DEVICE_TYPE_LIGHT_STRIP,
    ZENGGE_DEVICE_TYPE_PANEL_RGBCCT,
    ZenggeNode,
)
from .color import (
    ZENGGE_MIN_MIREDS,
    ZENGGE_MAX_MIREDS,
    ZenggeColor,
)
from ..ble.device import (
    UNILED_BLE_NOTFICATION_TIMEOUT,
    UNILED_BLE_BAD_RSSI,
    UUID_MANUFACTURER,
    UUID_HARDWARE_REV,
    UUID_FIRMWARE_REV,
    UUID_MODEL_NBR,
    AdvertisementData,
    BLEDevice,
    BleakGATTCharacteristic,
    ParseNotificationError,
    UniledBleDevice,
    UniledBleModel,
)
from ..const import (
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_RGB,
    COLOR_MODE_WHITE,
    ATTR_HA_BRIGHTNESS,
    ATTR_HA_COLOR_MODE,
    ATTR_HA_COLOR_TEMP,
    ATTR_HA_EFFECT,
    ATTR_HA_MAX_MIREDS,
    ATTR_HA_MIN_MIREDS,
    ATTR_HA_RGB_COLOR,
    ATTR_HA_RGBW_COLOR,
    ATTR_HA_RGBWW_COLOR,
    ATTR_HA_SUPPORTED_COLOR_MODES,
    ATTR_HA_WHITE,
    ATTR_UL_DEVICE_FORCE_REFRESH,
    ATTR_UL_LIGHT_MODE_NUMBER,
    ATTR_UL_MAC_ADDRESS,
    ATTR_UL_NODE_ID,
    ATTR_UL_NODE_TYPE,
    ATTR_UL_NODE_WIRING,
    ATTR_UL_POWER,
    ATTR_UL_RSSI,
    ATTR_UL_STATUS,
)

import time
import struct
import asyncio
import async_timeout
import logging

_LOGGER = logging.getLogger(__name__)

# Device 'bd2c53ed2e7c15ff' (F8:1D:78:68:28:43)
#   11 02 43 28 68 78
#   11 02 43 28 68 78 02 02 01 02 00 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
#
# Device 'bd2c53ed2e7c15ff' (F8:1D:78:68:44:C1)
#   11 02 c1 44 68 78
#   11 02 c1 44 68 78 02 02 01 03 00 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
#
UNILED_TRANSPORT_ZNG: Final = "zng"

CONF_ZNG_ACTIVE_SCAN: Final = "active_scan"
CONF_ZNG_COUNTRY: Final = "country"
CONF_ZNG_MESH_ID: Final = "mesh_id"
CONF_ZNG_MESH_UUID: Final = "mesh_uuid"
CONF_ZNG_PASSWORD: Final = "password"
CONF_ZNG_USERNAME: Final = "username"

ZENGGE_UPDATE_SECONDS: Final = 40

ZENGGE_MANUFACTURER_ID: Final = 63517
ZENGGE_MANUFACTURER: Final = "Hao Deng"
ZENGGE_DESCRIPTION: Final = "Zengge Mesh"
ZENGGE_MODEL_NAME: Final = "ZENGGE"
ZENGGE_MASTER_NAME: Final = "Mesh"
ZENGGE_MESH_ADDRESS_BRIDGE: Final = 255
ZENGGE_MESH_ADDRESS_NONE: Final = TELINK_MESH_ADDRESS_NONE

ZENGGE_DEFAULT_MESH_UUID: Final = 0x0211
ZENGGE_DEFAULT_MESH_KEY: Final = "ZenggeMesh"
ZENGGE_DEFAULT_MESH_PASS: Final = "ZenggeTechnology"
ZENGGE_DEFAULT_MESH_TOKEN: Final = None

ZENGGE_STATUS_ONLINE: Final = "Online"
ZENGGE_STATUS_OFFLINE: Final = "Offline"

ZENGGE_WIRING_CONNECTION_NONE: Final = 0
ZENGGE_WIRING_CONNECTION_RGB: Final = 1
ZENGGE_WIRING_CONNECTION_RGB_W: Final = 2
ZENGGE_WIRING_CONNECTION_RGBW: Final = 3
ZENGGE_WIRING_CONNECTION_RGB_CCT: Final = 4
ZENGGE_WIRING_CONNECTION_RGBCCT: Final = 5
ZENGGE_WIRING_CONNECTION_DIM: Final = 6
ZENGGE_WIRING_CONNECTION_CCT: Final = 7

ZENGGE_WIRING_CONTROL_NONE: Final = 0
ZENGGE_WIRING_CONTROL_RGB: Final = 1
ZENGGE_WIRING_CONTROL_RGB_W: Final = 2  # RGB / W
ZENGGE_WIRING_CONTROL_RGBW: Final = 3  # RGB & W
ZENGGE_WIRING_CONTROL_RGB_CCT: Final = 4
ZENGGE_WIRING_CONTROL_RGBCCT: Final = 5
ZENGGE_WIRING_CONTROL_WARM: Final = 6
ZENGGE_WIRING_CONTROL_COLD: Final = 7
ZENGGE_WIRING_CONTROL_CCT: Final = 8

# STATEACTION_POWER = 0x01
# STATEACTION_BRIGHTNESS = 0x02
# STATEACTION_INCREASEBRIGHTNESS = 0x03
# STATEACTION_DECREASEBRIGHTNESS = 0x04

ZENGGE_COLOR_MODE_RGB: Final = 0x60
ZENGGE_COLOR_MODE_WARMWHITE: Final = 0x61
ZENGGE_COLOR_MODE_CCT: Final = 0x62
ZENGGE_COLOR_MODE_AUX: Final = 0x63
ZENGGE_COLOR_MODE_CCTAUX: Final = 0x64

ZENGGE_DIMMING_TARGET_RGBKWC: Final = 0x01  # Set RGB, Keep WC
ZENGGE_DIMMING_TARGET_WCKRGB: Final = 0x02  # Set WC, Keep RGB
ZENGGE_DIMMING_TARGET_RGBWC: Final = 0x03  # Set RGB & WC
ZENGGE_DIMMING_TARGET_RGBOWC: Final = 0x04  # Set RGB, WC Off
ZENGGE_DIMMING_TARGET_WCORGB: Final = 0x05  # Set WC, RGB Off
ZENGGE_DIMMING_TARGET_AUTO: Final = 0x06  # Set lights according to situation

ZENGGE_EFFECT_SOLID: Final = "Solid"
ZENGGE_EFFECT_UNKNOWN: Final = "?FX?"

ZENGGE_EFFECT_LIST: Final = {
    0x01:   "Seven Color Cross Fade",
    0x02:   "Red Gradual Change",
    0x03:   "Green Gradual Change",
    0x04:   "Blue Gradual Change",
    0x05:   "Yellow Gradual Change",
    0x06:   "Cyan Gradual Change",
    0x07:   "Purple Gradual Change",
    0x08:   "White Gradual Change",
    0x09:   "Red/Green Cross Fade",
    0x0A:   "Red/Blue Cross Fade",
    0x0B:   "Green/Blue Cross Fade",
    0x0C:   "Seven Color Strobe",
    0x0D:   "Red Strobe Flash",
    0x0E:   "Green Strobe Flash",
    0x0F:   "Blue Strobe Flash",
    0x10:   "Yellow Strobe Flash",
    0x11:   "Cyan Strobe Flash",
    0x12:   "Purple Strobe Flash",
    0x13:   "White Strobe Flash",
    0x14:   "Seven Color Jumping Change",
 }

##
## Zengge Master
##
class ZenggeMaster(ZenggeNode):
    """Zengge Mesh - Master Channel"""

    _manager: ZenggeManager

    def __init__(self, manager: ZenggeManager) -> None:
        super().__init__(manager.mesh_uuid, 0)
        self._manager = manager

    @property
    def name(self) -> str:
        """Returns the channel name."""
        return ZENGGE_MASTER_NAME

    @property
    def title(self) -> str:
        """Returns the channel title."""
        return ZENGGE_DESCRIPTION

    @property
    def manager(self) -> ZenggeManager:
        """Returns the device."""
        return self._manager


##
## Zengee Model
##
class ZenggeModel(UniledBleModel):
    """UniLED ZNG (Zengge Mesh) Model Class"""

    ##
    ## Model is a singleton class!
    ##
    __instance: ZenggeModel = None

    def __new__(cls):
        """Singleton Class"""
        if cls.__instance is None:
            cls.__instance = super(UniledBleModel, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        super().__init__(
            model_num=0x5A4D,  # 'ZM'
            model_name=ZENGGE_MODEL_NAME,
            description=ZENGGE_DESCRIPTION,
            manufacturer=ZENGGE_MANUFACTURER,
            channels=0,
            ble_manufacturer_data=None,
            ble_manufacturer_id=ZENGGE_MANUFACTURER_ID,
            ble_service_uuids=[TELINK_UUID_SERVICE],
            ble_notify_uuids=[TELINK_UUID_STATUS_CHAR],
            ble_write_uuids=[TELINK_UUID_COMMAND_CHAR],
            ble_read_uuids=[TELINK_UUID_COMMAND_CHAR],
        )

    def color_modes(self, node: ZenggeNode) -> list:
        """Base node feature set"""
        if node.node_type == ZENGGE_DEVICE_TYPE_PANEL_RGBCCT:
            return {}       
        if node.node_wiring == ZENGGE_WIRING_CONTROL_RGB_CCT:
            return {
                COLOR_MODE_RGB,
                COLOR_MODE_COLOR_TEMP,
            }
        if node.node_wiring == ZENGGE_WIRING_CONTROL_RGB_W:
            return {
                COLOR_MODE_RGB,
                COLOR_MODE_WHITE,
            }
        return {COLOR_MODE_BRIGHTNESS}

    def percentage(self, part, whole):
        per = 100 * float(part) / float(whole)
        return int(round(per))

    def byte_percentage(self, percent: int) -> int:
        """Convert integer percentage of 255"""
        return int(round((percent * 255) / 100.0)) & 0xFF

    def cct_percentage(self, percent: int) -> int:
        """Convert cct percentage to mireds, note % inversion"""
        percent = 100 - percent
        return (
            ZENGGE_MIN_MIREDS
            + int(round((percent * (ZENGGE_MAX_MIREDS - ZENGGE_MIN_MIREDS)) / 100.0))
            & 0xFFFF
        )

    def percentage_cct(self, mireds) -> int:
        """Convert mireds to cct percentage, note % inversion"""
        whole = ZENGGE_MAX_MIREDS - ZENGGE_MIN_MIREDS
        part = mireds - ZENGGE_MIN_MIREDS
        return 100 - int(self.percentage(part, whole)) & 0xFF

    def parse_notifications(
        self,
        manager: ZenggeManager,
        sender: int,
        data: bytearray,
    ) -> bool:
        """Parse notification message(s)"""
        if (node_id := data[0]) == ZENGGE_MESH_ADDRESS_NONE:
            return False
        status = dict()
        for nid, node in manager.nodes.items():
            if node.number != node_id:
                continue

            if node_id == ZENGGE_MESH_ADDRESS_BRIDGE:
                _LOGGER.warning(f"{node_id}: Bridge status: {repr(list(data))}")
                return False
            elif node.node_type == ZENGGE_DEVICE_TYPE_PANEL_RGBCCT:
                _LOGGER.warning(f"{node_id}: Panel status: {repr(list(data))}")
                connected = data[1] & 0xFF
                status = {
                    ATTR_UL_RSSI: node.rssi,
                    ATTR_UL_NODE_ID: node_id,
                    ATTR_UL_MAC_ADDRESS: node.address,
                    ATTR_UL_STATUS: ZENGGE_STATUS_ONLINE if connected else ZENGGE_STATUS_OFFLINE,
                }
                node.status.replace(status, refresh=True)
                return True

            connected = data[1] & 0xFF
            level = data[2] & 0xFF
            power = level != 0 if connected != 0 else None
            mode = data[3] >> 6 & 0xFF
            value1 = data[4]
            value2 = data[3] & 0x3F
            brightness = self.byte_percentage(level)

            status = {
                "type": node.node_type,
                "wiring": node.node_wiring,
                "mode": mode,
                "val1": value1,
                "val2": value2,
                "360?": value1+value2,
                ATTR_UL_DEVICE_FORCE_REFRESH: True,
                ATTR_UL_RSSI: node.rssi,
                ATTR_UL_NODE_ID: node_id,
                ATTR_UL_MAC_ADDRESS: node.address,
                ATTR_UL_STATUS: ZENGGE_STATUS_ONLINE if connected else ZENGGE_STATUS_OFFLINE,
                ATTR_UL_POWER: power,
                ATTR_HA_SUPPORTED_COLOR_MODES: self.color_modes(node),
                ATTR_HA_EFFECT: ZENGGE_EFFECT_SOLID,
                ATTR_HA_BRIGHTNESS: (
                    brightness if power else node.status.get(ATTR_HA_BRIGHTNESS, 255)
                ),
            }

            if COLOR_MODE_RGB in status[ATTR_HA_SUPPORTED_COLOR_MODES]:
                status[ATTR_HA_RGB_COLOR] = node.status.get(
                    ATTR_HA_RGB_COLOR, (0xFF, 0xFF, 0xFF)
                )
            if COLOR_MODE_WHITE in status[ATTR_HA_SUPPORTED_COLOR_MODES]:
                status[ATTR_HA_WHITE] = node.status.get(ATTR_HA_WHITE, True)
            if COLOR_MODE_COLOR_TEMP in status[ATTR_HA_SUPPORTED_COLOR_MODES]:
                status[COLOR_MODE_COLOR_TEMP] = node.status.get(
                    COLOR_MODE_COLOR_TEMP, ZENGGE_MAX_MIREDS
                )
                status[ATTR_HA_MAX_MIREDS] = ZENGGE_MAX_MIREDS
                status[ATTR_HA_MIN_MIREDS] = ZENGGE_MIN_MIREDS
            status[ATTR_HA_COLOR_MODE] = COLOR_MODE_BRIGHTNESS

            if power:
                if mode == 0:
                    status[ATTR_HA_COLOR_MODE] = COLOR_MODE_RGB
                    rgb = ZenggeColor.decode_rgb(value1)
                    status[ATTR_HA_RGB_COLOR] = (rgb[0], rgb[1], rgb[2])

                    h = ZenggeColor.h255_to_h360(value1)
                    s = value2
                    l = level
                    rgb = ZenggeColor.hsv_to_rgb(h, s, l)
                    status["rgb2"] = (rgb[0], rgb[1], rgb[2])

                elif mode == 1:
                    if (
                        node.node_wiring == ZENGGE_WIRING_CONNECTION_CCT
                        or node.node_wiring == ZENGGE_WIRING_CONNECTION_RGB_CCT
                    ):
                        status[ATTR_HA_COLOR_MODE] = COLOR_MODE_COLOR_TEMP
                        status[ATTR_HA_COLOR_TEMP] = self.cct_percentage(value1)
                    else:
                        status[
                            ATTR_HA_COLOR_MODE
                        ] = COLOR_MODE_BRIGHTNESS  # COLOR_MODE_WHITE
                        status[ATTR_HA_WHITE] = status[ATTR_HA_BRIGHTNESS]
                elif mode == 2:
                    status[ATTR_HA_EFFECT] = ZENGGE_EFFECT_UNKNOWN

            node.status.replace(status, refresh=True)
            return True

        if (node := manager.notified_new_node(node_id)) is not None:
            node.status.replace(status, refresh=True)
        return True

    def _command(
        self,
        manager: ZenggeManager,
        command: int,
        opcode: int,
        value1: int,
        value2: int = 0,
        value3: int = 0,
        gradualSecond: float = 0.0,
        delaySecond: float = 0.0,
        deviceType: int = 0xFF,
        dest: int | None = None,
    ):
        """Make command payload and packet"""
        delaySecond = int(round(delaySecond * 10.0)) & 0xFFFF
        gradualSecond = int(round(gradualSecond * 10.0)) & 0xFFFF

        data = struct.pack(
            "<BBBBBHH",
            deviceType & 0xFF,
            opcode & 0xFF,
            value1 & 0xFF,
            value2 & 0xFF,
            value3 & 0xFF,
            delaySecond,
            gradualSecond,
        )
        return self._command_packet(manager, command & 0xFF, data, dest)

    def _command_packet(
        self, manager: ZenggeManager, command: int, data: bytes = b"", dest=None
    ):
        """Make command packet"""
        if dest is None:
            dest = manager.mesh_uuid
        packet = pckt.make_command_packet(
            manager.mesh_session, manager.address, dest, command, data
        )
        return packet

    def build_on_connect(self, manager: ZenggeManager) -> bytearray | None:
        """Build on connect message(s)"""
        return None

    def build_state_query(self, manager: ZenggeManager) -> bytearray | None:
        """Build a state query message"""
        # This does not work, see the update() method in the manager class
        return self._command_packet(manager, C_GET_STATUS_SENT)

    def build_onoff_command(
        self, manager: ZenggeManager, node: ZenggeNode, state: bool
    ) -> bytearray | None:
        """Build power on/off state message(s)"""
        return self._command(
            manager, C_POWER, 0x01, 0xFF if state else 0x00, dest=node.node_id
        )

    def build_brightness_command(
        self, manager: ZenggeManager, node: ZenggeNode, level: int
    ) -> bytearray | None:
        """The bytes to send for a brightness level change"""
        level = self.percentage(level, 255)
        target = ZENGGE_DIMMING_TARGET_AUTO
        return self._command(manager, C_POWER, 0x02, level, target, dest=node.node_id)

    def build_rgb_color_command(
        self, manager: ZenggeManager, node: ZenggeNode, rgb: tuple[int, int, int]
    ) -> bytearray | None:
        """The bytes to send for a color level change"""
        node.status.set(ATTR_HA_COLOR_MODE, COLOR_MODE_RGB)
        node.status.set(ATTR_HA_RGB_COLOR, rgb)
        red, green, blue = rgb
        return self._command(
            manager,
            C_COLOR,
            ZENGGE_COLOR_MODE_RGB,
            red,
            green,
            blue,
            dest=node.node_id,
        )

    def build_color_temp_command(
        self, manager: ZenggeManager, node: ZenggeNode, temp: int
    ) -> bytearray | None:
        cct = self.percentage_cct(temp)
        level = self.percentage(node.status.get(ATTR_HA_BRIGHTNESS, 255), 255)
        node.status.set(ATTR_HA_COLOR_MODE, COLOR_MODE_COLOR_TEMP)
        return self._command(
            manager,
            C_COLOR,
            ZENGGE_COLOR_MODE_CCT,
            cct,
            level,
            dest=node.node_id,
        )

    def build_white_command(
        self, manager: ZenggeManager, node: ZenggeNode, white: int
    ) -> bytearray | None:
        if (level := node.status.get(ATTR_HA_WHITE, white)) is True:
            level = white
        node.status.set(ATTR_HA_COLOR_MODE, COLOR_MODE_BRIGHTNESS)
        return self._command(
            manager, C_COLOR, ZENGGE_COLOR_MODE_WARMWHITE, level, dest=node.node_id
        )

    def build_effect_command(
        self, manager: ZenggeManager, node: ZenggeNode, value: str | int
    ) -> bytearray:
        """The bytes to send for an effect change"""
        if isinstance(value, str):
            effect = self.int_if_str_in(
                value, ZENGGE_EFFECT_LIST, 0
            )
        elif (effect := int(value)) not in ZENGGE_EFFECT_LIST:
            return None
        return self._command(
            manager, C_COLOR, 0x80, 5, 20, dest=node.node_id
        )


        return self._command(
            manager,
            C_PRESET,
            1,
            1,
            2,
            dest=node.node_id,
        )

    def fetch_effect_list(
        self, manager: ZenggeManager, node: ZenggeNode
    ) -> list:
        """Return list of effect names"""
        return list(ZENGGE_EFFECT_LIST.values())

##
## UniLed Zengge Device Manager
##
class ZenggeManager(UniledBleDevice):
    """Zengge Mesh Manager Class"""

    @staticmethod
    def device_mesh_uuid(
        device: BLEDevice, advertisement: AdvertisementData | None = None
    ) -> int | None:
        if ZENGGE_MANUFACTURER_ID not in advertisement.manufacturer_data:
            return None
        if TELINK_MANUFACTURER_ID in advertisement.manufacturer_data:
            data = advertisement.manufacturer_data[TELINK_MANUFACTURER_ID]
            return int.from_bytes(data[:2], byteorder="little")
        return None

    @staticmethod
    def mesh_uuid_unique(
        device: BLEDevice, advertisement: AdvertisementData | None = None
    ) -> str | None:
        if (mesh_uuid := ZenggeManager.device_mesh_uuid(device, advertisement)) is None:
            return (None, None)
        return (mesh_uuid, f"{UNILED_TRANSPORT_ZNG}_mesh_{hex(mesh_uuid)}")

    ##
    ## Initialize device instance
    ##
    _nodes: dict(str, ZenggeNode) = dict()
    _starting: bool = False
    _mesh_id = None
    _mesh_uuid = None
    _mesh_user = None
    _mesh_pass = None
    _mesh_area = None
    _mesh_key = None
    _mesh_pass = None
    _mesh_token = None
    _mesh_session = None

    def __init__(
        self,
        mesh_id: str,
        mesh_uuid: int,
        cloud_user: str,
        cloud_pass: str,
        cloud_area: str,
        config: Any,
    ) -> None:
        """Init the UniLED ZNG Model"""
        self._model = ZenggeModel()
        super().__init__(config, None, None, self.model_name)
        self._started = False
        self._mesh_key = None
        self._mesh_pass = None
        self._mesh_token = None
        self._mesh_id = mesh_id
        self._mesh_uuid = mesh_uuid
        self._cloud_user = cloud_user
        self._cloud_pass = cloud_pass
        self._cloud_area = cloud_area
        self._nodes[mesh_uuid] = ZenggeMaster(self) # uuid or bridge ID or mesh_id ?????

    @property
    def transport(self) -> str:
        """Return the device transport."""
        return UNILED_TRANSPORT_ZNG

    @property
    def name(self) -> str:
        """Return the name of the mesh."""
        return f"{self.transport}{hex(int(self.mesh_uuid))}".upper()

    @property
    def connected(self) -> bool:
        """Return if the mesh is connected."""
        return self.available and self.mesh_session is not None

    @property
    def channel_list(self) -> list[ZenggeNode]:
        """Return the number of channels"""
        return list(self._nodes.values())

    @property
    def mesh_session(self) -> int:
        """Mesh (Session) Key"""
        return self._mesh_session

    @property
    def mesh_uuid(self) -> int:
        """Mesh ID"""
        return self._mesh_uuid if self._mesh_uuid is not None else ZENGGE_DEFAULT_MESH_UUID

    @property
    def mesh_key(self) -> str:
        """Mesh Key"""
        return self._mesh_key if self._mesh_key is not None else ZENGGE_DEFAULT_MESH_KEY

    @property
    def mesh_pass(self) -> str:
        """Mesh Password"""
        return (
            self._mesh_pass if self._mesh_pass is not None else ZENGGE_DEFAULT_MESH_PASS
        )

    @property
    def mesh_token(self) -> str:
        """Mesh Long Term Token"""
        return (
            self._mesh_token
            if self._mesh_token is not None
            else ZENGGE_DEFAULT_MESH_TOKEN
        )

    @property
    def nodes(self) -> dict:
        """Node dictionary"""
        return self._nodes

    async def cloud_refresh(self) -> bool:
        """Cloud Connect"""
        _LOGGER.info("%s: Connecting to cloud...", self.name)
        cloud = MagicHue(self._cloud_user, self._cloud_pass, self._cloud_area)
        if await cloud.login() is not True:
            return False
        if await cloud.get_meshes() is not True:
            return False
        if await cloud.get_devices() is not True:
            return False
        for location in cloud.meshes:
            if len(location["deviceList"]):
                self._mesh_key = location["meshKey"]
                self._mesh_pass = location["meshPassword"]
                self._mesh_token = location["meshLTK"]
                self.update_nodes(location["deviceList"])
        return True

    def update_nodes(self, devicelist) -> None:
        """Extract node information from selected cloud location results"""
        if devicelist is not None:
            for n in devicelist:
                node_mesh = n.get("meshUUID", 0)
                if node_mesh != self.mesh_uuid:
                    continue
                node_id = n.get("meshAddress", TELINK_MESH_ADDRESS_NONE)
                if node_id == TELINK_MESH_ADDRESS_NONE:
                    continue
                node_mac = n.get("macAddress", None)
                node_name = n.get("displayName", None)
                node_type = n.get("deviceType", None)
                node_wiring = n.get("wiringType", None)

                if node_id not in self._nodes:
                    node = ZenggeNode(
                        self.mesh_uuid,
                        node_id,
                        node_type,
                        node_wiring,
                        node_mac,
                        node_name,
                    )
                    self._nodes[node_id] = node
                    _LOGGER.debug("CREATED NODE: %s", n)
                else:
                    node = self._nodes[node_id]
                    node.update(node_type, node_wiring, node_mac, node_name)
                    _LOGGER.debug("UPDATED NODE: %s", n)

        if len(self._nodes) <= 1:
            _LOGGER.warning("%s: No mesh node configuration details found.", self.name)

    async def startup(self, event=None) -> bool:
        """Startup the mesh."""
        if self.started or self._starting:
            return
        _LOGGER.info("%s: Starting mesh...", self.name)
        self._starting = True
        async with self._operation_lock:
            await self.cloud_refresh() # Exception on failure??
            try:
                success = await self._async_ensure_connected(force=True)
            except Exception as ex:
                _LOGGER.warning(
                    "%s: Startup - Failed, exception: %s", self.name, str(ex)
                )
                success = False
        _LOGGER.debug("Mesh startup state: %s", success)
        self._started = True
        if success:
            await self.update()
        self._starting = False
        return self._started

    async def shutdown(self, event=None) -> None:
        """Shutdown the mesh."""
        if not self.started:
            return
        _LOGGER.info("%s: Shutdown mesh...", self.name)
        self._started = False
        await self.stop()

    # Zengge can't use Status request to receive device details, need notification requests
    async def update(self, retry: int | None = None) -> bool:
        """Update the device."""
        if not self._started:
            return True

        _LOGGER.debug("%s: Update - Send State Query...", self.name)
        self._notification_event.clear()
        if self._operation_lock.locked():
            _LOGGER.debug(
                "%s: Operation already in progress, waiting for it to complete...",
                self.name,
            )
        async with self._operation_lock:
            try:
                if not await self._async_ensure_connected():
                    return False
                reply = await self._client.write_gatt_char(
                    self._notify_char, b"\x01", True
                )
            except Exception as ex:
                _LOGGER.warning(
                    "%s: Update - Failed, exception: %s", self.name, str(ex)
                )
                return False

        if not self.connected:
            _LOGGER.warning("%s: Update - Failed, mesh not connected.", self.name)
            return False

        if not self._notification_event.is_set():
            # Wait for actual response!
            async with self._operation_lock:
                _LOGGER.debug(
                    "%s: Update - Awaiting %s seconds for status notification...",
                    self.name,
                    UNILED_BLE_NOTFICATION_TIMEOUT,
                )
                try:
                    async with async_timeout.timeout(UNILED_BLE_NOTFICATION_TIMEOUT):
                        await self._notification_event.wait()
                except asyncio.TimeoutError:
                    _LOGGER.warning(
                        "%s: Update - Failed, notification timeout.", self.name
                    )
                    return False

        for channel in self.channel_list:
            if channel.number != 0 or not channel.status.dump():
                continue
            _LOGGER.debug(
                "%s: %s, Status: %s",
                self.name,
                channel.title,
                channel.status.dump(),
            )
        return True

    ##
    ## Utilities
    ##
    def notified_new_node(self, node_id: int) -> ZenggeNode | None:
        """Notified of a new node"""
        if node_id == ZENGGE_MESH_ADDRESS_NONE:
            return None
        if node_id not in self._nodes:
            self._nodes[node_id] = ZenggeNode(self.mesh_uuid, node_id)
            _LOGGER.info("%s: Notified of new node: %s", self.name, node_id)
        return self._nodes[node_id]

    def set_device_and_advertisement(
        self, device: BLEDevice, advert: AdvertisementData
    ) -> None:
        """Update the BLE device/advertisement."""
        mesh_uuid, node_id, node_type = ZenggeNode.device_mesh_node_id(device, advert)
        if mesh_uuid != self.mesh_uuid:
            _LOGGER.debug(
                "%s: Ignored '%s' advertisement update, as wrong mesh UUID: %s; RSSI: %s",
                self.name,
                device.name,
                hex(mesh_uuid),
                advert.rssi,
            )
            return

        if node_id not in self._nodes:
            node = ZenggeNode(mesh_uuid, node_id)
            self._nodes[node_id] = node
            _LOGGER.info(
                "%s: Discovered node '%s' (%s), type=%d; RSSI: %s",
                self.name,
                node_id,
                device.address,
                node_type,
                advert.rssi,
            )

        if isinstance(self._nodes[node_id], ZenggeNode):
            self._nodes[node_id].update_device(device, advert)
        if self.address == device.address:
            super().set_device_and_advertisement(device, advert)

    def _nodes_by_sorted_rssi(self) -> list:
        """Sort nodes by rssi and only return devices with a RSSI that could be in range"""
        nodes = sorted(self._nodes.items(), key=lambda node: node[1].rssi, reverse=True)
        return list(filter(lambda node: node[1].rssi > UNILED_BLE_BAD_RSSI, nodes))

    ##
    ## Connect to mesh
    ##
    async def _async_ensure_connected(self, force: bool = False) -> bool:
        """Login/Pair device"""
        if self.connected and not force:
            return True

        if self.available:
            await self.stop()

        for id, node in self._nodes_by_sorted_rssi():
            # Anything equal to or below -127 is not in connection range
            if node.rssi <= -127:
                continue
            _LOGGER.info(
                "%s: Connecting to node '%s' (%s), RSSI: %s",
                self.name,
                node.number,
                node.address,
                node.rssi,
            )
            self._ble_device = node.device
            self._advertisement_data = node.advert
            if await super()._async_ensure_connected():
                self._cancel_disconnect_timer()
                if self.connected:
                    _LOGGER.info(
                        "%s: Connected to node '%s' (%s), RSSI: %s",
                        self.name,
                        node.number,
                        node.address,
                        node.rssi,
                    )
                    return True

            if self.available:
                await self.stop()

        if not self.connected:
            _LOGGER.warning("%s: No connectable mesh nodes!", self.name)
            self._ble_device = None
            self._advertisement_data = None
        return self.connected

    ##
    ## Pair with device
    ##
    async def _async_pair_with_device(self) -> bool:
        """Login/Pair device"""
        _LOGGER.info("%s: Pairing with node '%s'...", self.name, self.address)
        assert self._connect_lock.locked(), "Lock not held"
        assert self.available, "Not connected"
        session_random = urandom(8)
        message = pckt.make_pair_packet(
            self.mesh_key.encode(), self.mesh_pass.encode(), session_random
        )
        pairReply = await self._async_write_characteristic(
            bytes(message), uuid=TELINK_UUID_PAIR_CHAR, withResponse=True
        )
        await asyncio.sleep(0.3)
        reply = await self._async_read_characteristic(uuid=TELINK_UUID_PAIR_CHAR)

        if reply[0] == 0x0D:
            self._mesh_session = pckt.make_session_key(
                self.mesh_key.encode(),
                self.mesh_pass.encode(),
                session_random,
                reply[1:9],
            )
            return True
        elif reply[0] == 0x0E:
            _LOGGER.error(
                "%s: Node '%s', authentication error: known mesh credentials not accepted. Did you re-pair them to your Hao Deng app with a different account?",
                self.name,
                self.address,
            )
        else:
            _LOGGER.warning(
                "%s: Node '%s', returned unexpected pair value : %s",
                self.name,
                self.address,
                repr(reply),
            )
        return False

    ##
    ## Notification Handler
    ##
    def _notification_handler(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle notification responses."""
        message = pckt.decrypt_packet(self.mesh_session, self.address, data)
        if not message or not self.channels:
            _LOGGER.debug(
                "%s: Encrypted notification from node '%s' [%s],\nData: %s",
                self.name,
                self.address,
                sender.handle,
                data.hex(),
            )
            return

        try:
            # 0  - 129,     ??
            # 1  - 152,     ??
            # 2  - 93,      ??
            # 3  - 0,       Mesh ID - LSB
            # 4  - 0,       Mesh ID - MSB
            # 5  - 39,      ??
            # 6  - 52,      ??
            # 7  - 220,     Command #
            # 8  - 17,      ?Responding Node ID?
            # 9  - 2,       ??
            # 10 - 17,      Node 1 ID
            # 11 - 177,     Node 1 Connected
            # 12 - 100,     Node 1 Brightness
            # 13 - 47,      Node 1 Value 1
            # 14 - 127,     Node 1 Value 2
            # 15 - 16,      Node 2 ID
            # 16 - 69,      Node 2 Connected
            # 17 - 0,       Node 2 Brightness
            # 18 - 0,       Node 2 Value 1
            # 19 - 0        Node 2 Value 2
            #
            _LOGGER.debug(f"{self.address}: Mesh message: {repr(list(message))}")
            command = struct.unpack("B", message[7:8])[0]
            if command == C_NOTIFICATION_RECEIVED:
                self._model.parse_notifications(
                    self, sender.handle, struct.unpack("BBBBB", message[10:15])
                )
                self._model.parse_notifications(
                    self, sender.handle, struct.unpack("BBBBB", message[15:20])
                )
                self._last_notification_time = time.monotonic()
                self._last_notification_data = ()
                self._notification_event.set()
                self._fire_callbacks()
                return
            elif command == C_GET_STATUS_RECEIVED:
                mesh_address = struct.unpack("B", message[3:4])[0]
                _LOGGER.info(
                    "%s: C_GET_STATUS_RECEIVED - %s", self.address, mesh_address
                )
            else:
                _LOGGER.debug(f"{self.address}: Unknown command: {hex(command)}")
        except ParseNotificationError as ex:
            _LOGGER.warning(
                "%s: Notification parser failed! - %s",
                self.name,
                str(ex),
            )
        except Exception as ex:
            _LOGGER.warning(
                "%s: Notification parser exception!",
                self.name,
                exc_info=True,
            )

    async def _async_start_notify(self) -> bool:
        """Start notification."""
        # Huge thanks to '@cocoto' for helping figure this issue out with Zengge!
        # await self.send_packet(0x01, bytes([]), self.mesh_uuid, uuid=TELINK_UUID_STATUS_CHAR)
        await self._async_send_mesh_command(
            0x01, bytes([]), uuid=TELINK_UUID_STATUS_CHAR
        )
        await asyncio.sleep(0.3)
        return await super()._async_start_notify()

    async def _async_send_mesh_command(
        self,
        command: int,
        data: bytes,
        withResponse: bool = True,
        retry: int = 0,
        uuid=TELINK_UUID_COMMAND_CHAR,
    ) -> Any:
        """Send mesh command"""
        packet = pckt.make_command_packet(
            self.mesh_session, self.address, self.mesh_uuid, command, data
        )

        _LOGGER.debug(
            "%s: Command '%s' packet: %s",
            self.name,
            hex(command),
            packet,
        )

        reply = await self._async_write_characteristic(packet, uuid, withResponse)
        return reply

    async def _async_write_characteristic(
        self,
        data,
        uuid=TELINK_UUID_COMMAND_CHAR,
        withResponse: bool | None = None,
    ) -> Any:
        """Write GATT Characteristic"""
        if not data:
            return None
        try:
            _LOGGER.debug(
                "%s: Write to UUID: %s, Data: %s", self.name, uuid, repr(data)
            )
            assert self.available, "Not connected"
            reply = await self._client.write_gatt_char(uuid, data, withResponse)
        except Exception as ex:
            _LOGGER.debug(
                "%s: Exception %s while writing to UUID: %s.", self.name, str(ex), uuid
            )
            return None
        if withResponse and reply:
            _LOGGER.debug(
                "%s: Reply from UUID: %s, Data: %s", self.name, uuid, repr(reply)
            )
        return reply

    async def _async_read_characteristic(
        self, uuid=TELINK_UUID_COMMAND_CHAR, timeout: int = 0
    ) -> Any:
        """Read GATT Characteristic"""
        try:
            assert self.available, "Not connected"
            data = await self._client.read_gatt_char(uuid)
        except Exception as ex:
            _LOGGER.debug(
                "%s: Excepiotn %s while reading from UUID: %s.",
                self.name,
                str(ex),
                uuid,
            )
            return None
        else:
            _LOGGER.debug(
                "%s: Read from UUID: %s, Data: %s", self.name, uuid, data.hex()
            )
        return data
