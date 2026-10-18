"""UniLED BLE Devices - SP LED (BanlanX SP661E, single colour PWM)

Protocol notes: see docs/SP661E_PROTOCOL.md. Frames are
`53 CMD 00 01 00 LEN DATA` on FFE1; control payloads start with channel `01`.
"""

from __future__ import annotations
from typing import Final

from ..const import *  # I know!
from ..channel import UniledChannel
from ..features import (
    LightStripFeature,
    EffectTypeFeature,
    EffectSpeedFeature,
)
from ..effects import (
    UNILED_EFFECT_TYPE_DYNAMIC,
    UNILED_EFFECT_TYPE_STATIC,
)
from .device import (
    UUID_BASE_FORMAT as BANLANX_UUID_FORMAT,
    BANLANX_MANUFACTURER,
    BANLANX_MANUFACTURER_ID,
    ParseNotificationError,
    UniledBleDevice,
    UniledBleModel,
)

import logging

_LOGGER = logging.getLogger(__name__)

BANLANX661_HEADER: Final = 0x53
BANLANX661_HEADER_LENGTH: Final = 6
BANLANX661_MSG_STATUS: Final = 0x02

# Command codes
BANLANX661_CMD_QUERY: Final = 0x02
BANLANX661_CMD_MODE: Final = 0x53
BANLANX661_CMD_POWER: Final = 0x50
BANLANX661_CMD_LEVEL: Final = 0x51
BANLANX661_CMD_SPEED: Final = 0x54

# Offsets in the status notification (header included)
BANLANX661_OFS_POWER: Final = 44
BANLANX661_OFS_MODE: Final = 47
BANLANX661_OFS_EFFECT: Final = 48
BANLANX661_OFS_LEVEL_FX: Final = 50
BANLANX661_OFS_LEVEL_SOLID: Final = 51
BANLANX661_OFS_SPEED: Final = 57
BANLANX661_MIN_STATUS_LENGTH: Final = 58

BANLANX661_MODE_SOLID: Final = 0x02
BANLANX661_MODE_DYNAMIC: Final = 0x04

BANLANX661_MAX_EFFECT_SPEED: Final = 10

# Effect id = (mode << 4) | effect number
BANLANX661_EFFECTS: Final = {
    0x21: "Solid Color",
    0x41: "Triangle",
    0x42: "Strobe",
    0x43: "Heart Beat",
}


def _encode(cmd: int, data: list[int] | bytes) -> bytearray:
    """Encode a BanlanX SP661E message."""
    return bytearray(
        [BANLANX661_HEADER, cmd & 0xFF, 0x00, 0x01, 0x00, len(data) & 0xFF]
    ) + bytearray(data)


class BanlanX661(UniledBleModel):
    """BanlanX SP661E Protocol Implementation"""

    # Tell the matcher not to continue to other models once this one hit
    exclusive_match: bool = True
    # Advertised name is unreliable ("LMB", truncated), name after the model
    use_model_name: bool = True
    # The controller ignores state queries written with response
    write_with_response: bool = False

    def __init__(self, id: int, name: str, info: str, data: bytes):
        super().__init__(
            model_num=id,
            model_name=name,
            description=info,
            manufacturer=BANLANX_MANUFACTURER,
            channels=1,
            ble_manufacturer_id=BANLANX_MANUFACTURER_ID,
            ble_manufacturer_data=data,
            ble_service_uuids=[BANLANX_UUID_FORMAT.format(part) for part in ["ffe0"]],
            ble_write_uuids=[BANLANX_UUID_FORMAT.format(part) for part in ["ffe1"]],
            ble_read_uuids=[],
            ble_notify_uuids=[],
        )

    def parse_notifications(
        self,
        device: UniledBleDevice,
        sender: int,
        data: bytearray,
    ) -> bool:
        """Parse notification message(s)"""
        if len(data) < BANLANX661_HEADER_LENGTH:
            raise ParseNotificationError("Packet is undersized")
        if data[0] != BANLANX661_HEADER:
            raise ParseNotificationError("Packet is invalid")
        if len(data) != data[5] + BANLANX661_HEADER_LENGTH:
            raise ParseNotificationError(
                f"Packet payload size mismatch: {len(data)} vs {data[5] + 6}"
            )
        if data[1] != BANLANX661_MSG_STATUS:
            _LOGGER.debug("%s: Ignoring non-status packet %s", device.name, data.hex())
            return False
        if len(data) < BANLANX661_MIN_STATUS_LENGTH:
            raise ParseNotificationError("Status packet too short")

        _LOGGER.debug("%s: Good Status Message: %s", device.name, data.hex())

        if not device.master.features:
            device.master.features = [
                LightStripFeature(extra=UNILED_CONTROL_ATTRIBUTES),
                EffectTypeFeature(),
                EffectSpeedFeature(BANLANX661_MAX_EFFECT_SPEED),
            ]

        mode = data[BANLANX661_OFS_MODE]
        effect = data[BANLANX661_OFS_EFFECT]
        speed = data[BANLANX661_OFS_SPEED]
        fx_id = (mode << 4) | (effect & 0x0F)
        is_solid = mode == BANLANX661_MODE_SOLID
        # Solid mode brightness lives in [51], effect brightness in [50]
        level = data[
            BANLANX661_OFS_LEVEL_SOLID if is_solid else BANLANX661_OFS_LEVEL_FX
        ]

        device.master.status.replace(
            {
                ATTR_UL_DEVICE_FORCE_REFRESH: True,
                ATTR_UL_POWER: data[BANLANX661_OFS_POWER] == 1,
                ATTR_HA_SUPPORTED_COLOR_MODES: {COLOR_MODE_BRIGHTNESS},
                ATTR_HA_COLOR_MODE: COLOR_MODE_BRIGHTNESS,
                ATTR_HA_BRIGHTNESS: level,
                ATTR_UL_LIGHT_MODE_NUMBER: mode,
                ATTR_UL_EFFECT_NUMBER: fx_id,
                ATTR_HA_EFFECT: self.str_if_key_in(
                    fx_id, BANLANX661_EFFECTS, UNILED_UNKNOWN
                ),
                ATTR_UL_EFFECT_TYPE: (
                    UNILED_EFFECT_TYPE_STATIC
                    if is_solid
                    else UNILED_EFFECT_TYPE_DYNAMIC
                ),
            }
        )
        if not is_solid:
            device.master.set(ATTR_UL_EFFECT_SPEED, speed)
        return True

    def build_on_connect(self, device: UniledBleDevice) -> list[bytearray] | None:
        """Build on connect message(s)"""
        return None

    def build_state_query(self, device: UniledBleDevice) -> bytearray:
        """Build a state query message"""
        return _encode(BANLANX661_CMD_QUERY, [0x01])

    def build_onoff_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray:
        """Build power on/off state message(s)"""
        return _encode(BANLANX661_CMD_POWER, [0x01, 0x01 if state else 0x00])

    def build_brightness_command(
        self, device: UniledBleDevice, channel: UniledChannel, level: int
    ) -> bytearray:
        """The bytes to send for a brightness level change"""
        solid = channel.status.light_mode_number in (None, BANLANX661_MODE_SOLID)
        which = 0x80 if solid else 0x00
        return _encode(BANLANX661_CMD_LEVEL, [0x01, which, int(level) & 0xFF])

    def build_effect_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str | int
    ) -> bytearray | None:
        """The bytes to send for an effect change"""
        if isinstance(value, str):
            fx_id = self.int_if_str_in(value, BANLANX661_EFFECTS, None)
        else:
            fx_id = int(value)
        if fx_id is None or fx_id not in BANLANX661_EFFECTS:
            return None
        return _encode(BANLANX661_CMD_MODE, [0x01, fx_id >> 4, fx_id & 0x0F])

    def fetch_effect_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of effect names"""
        return list(BANLANX661_EFFECTS.values())

    def build_effect_speed_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect speed change."""
        speed = int(value) & 0xFF
        if not 0 <= speed <= BANLANX661_MAX_EFFECT_SPEED:
            return None
        return _encode(BANLANX661_CMD_SPEED, [0x01, speed])


##
## Device Signatures
##
# Manufacturer data starts with 01 00 (SP601E only checks the first byte)
SP661E = BanlanX661(
    id=0x661E,
    name="SP661E",
    info="Single Color PWM (Music) Controller",
    data=b"\x01\x00",
)
