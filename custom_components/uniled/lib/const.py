"""UniLED Constants."""

from typing import Final
from dataclasses import dataclass
from datetime import timedelta
from enum import IntEnum
from .helpers import StrEnum

UNILED_DEVICE_TIMEOUT: Final = 40
UNILED_REFRESH_DELAY: Final = 1.0
UNILED_DISCONNECT_DELAY: Final = 10.0
UNILED_COMMAND_SETTLE_DELAY: Final = 0.4
UNILED_STATE_CHANGE_LATENCY: Final = 2.0

UNILED_DISCOVERY: Final = "uniled_discovery"
UNILED_DISCOVERY_INTERVAL: Final = timedelta(minutes=15)
UNILED_DISCOVERY_DIRECTED_TIMEOUT: Final = 15
UNILED_DISCOVERY_STARTUP_TIMEOUT: Final = 5
UNILED_DISCOVERY_SCAN_TIMEOUT: Final = 10

# Uniled Config and Options Keys
CONF_UL_TRANSPORT: Final = "transport"
UNILED_TRANSPORT_BLE: Final = "ble"
UNILED_TRANSPORT_ZNG: Final = "zng"
UNILED_TRANSPORT_NET: Final = "net"

UNILED_TRANSPORTS: Final = [
    UNILED_TRANSPORT_BLE,
    UNILED_TRANSPORT_ZNG,
    UNILED_TRANSPORT_NET,
]

CONF_UL_RETRY_COUNT: Final = "retry_count"
UNILED_DEVICE_RETRYS: Final = 3
UNILED_MIN_DEVICE_RETRYS: Final = 1
UNILED_DEF_DEVICE_RETRYS: Final = UNILED_DEVICE_RETRYS
UNILED_MAX_DEVICE_RETRYS: Final = 5

CONF_UL_UPDATE_INTERVAL: Final = "update_interval"
UNILED_UPDATE_SECONDS: Final = 30
UNILED_MIN_UPDATE_INTERVAL: Final = 10
UNILED_DEF_UPDATE_INTERVAL: Final = UNILED_UPDATE_SECONDS
UNILED_MAX_UPDATE_INTERVAL: Final = 60

UNILED_CHANNEL: Final = "Channel"
UNILED_MASTER: Final = "Master"
UNILED_UNKNOWN: Final = "Unknown"

UNILED_DEFAULT_MIN_KELVIN: Final = 2000
UNILED_DEFAULT_MAX_KELVIN: Final = 6500
UNILED_DEFAULT_MIN_MIREDS: Final = 153  # 6500 K
UNILED_DEFAULT_MAX_MIREDS: Final = 500  # 2000 K

UNILED_AUDIO_INPUT_AUX_IN: Final = "Aux In"
UNILED_AUDIO_INPUT_INTMIC: Final = "Int. Mic"
UNILED_AUDIO_INPUT_EXTMIC: Final = "Ext. Mic"
UNILED_AUDIO_INPUT_PLAYER: Final = "Player"

# Home Assistant Config Keys
CONF_HA_ADDRESS: Final = "address"
CONF_HA_CODE: Final = "code"
CONF_HA_HOST: Final = "host"
CONF_HA_MODEL: Final = "model"
CONF_HA_NAME: Final = "name"
CONF_UL_OPTIONS: Final = "options"
CONF_UL_SOURCE: Final = "source"

# Home Assistant Supported Light Attributes
COLOR_MODE_UNKNOWN = "unknown"
COLOR_MODE_ONOFF = "onoff"
COLOR_MODE_BRIGHTNESS = "brightness"
COLOR_MODE_COLOR_TEMP = "color_temp"
COLOR_MODE_HS = "hs"
COLOR_MODE_XY = "xy"
COLOR_MODE_RGB = "rgb"
COLOR_MODE_RGBW = "rgbw"
COLOR_MODE_RGBWW = "rgbww"
COLOR_MODE_WHITE = "white"

# Float that represents transition time in seconds to make change.
ATTR_HA_TRANSITION = "transition"
ATTR_HA_RGB_COLOR = "rgb_color"
ATTR_HA_RGBW_COLOR = "rgbw_color"
ATTR_HA_RGBWW_COLOR = "rgbww_color"
ATTR_HA_XY_COLOR = "xy_color"
ATTR_HA_HS_COLOR = "hs_color"
ATTR_HA_COLOR_TEMP = "color_temp"  # Deprecated in HA Core 2022.11
ATTR_HA_KELVIN = "kelvin"  # Deprecated in HA Core 2022.11
ATTR_HA_MIN_MIREDS = "min_mireds"  # Deprecated in HA Core 2022.11
ATTR_HA_MAX_MIREDS = "max_mireds"  # Deprecated in HA Core 2022.11
ATTR_HA_COLOR_TEMP_KELVIN = "color_temp_kelvin"
ATTR_HA_MIN_COLOR_TEMP_KELVIN = "min_color_temp_kelvin"
ATTR_HA_MAX_COLOR_TEMP_KELVIN = "max_color_temp_kelvin"
ATTR_HA_COLOR_NAME = "color_name"
ATTR_HA_WHITE = "white"
ATTR_HA_BRIGHTNESS = "brightness"
ATTR_HA_FLASH = "flash"
ATTR_HA_EFFECT_LIST = "effect_list"
ATTR_HA_EFFECT = "effect"
ATTR_HA_ONOFF = "onoff"
ATTR_HA_COLOR_MODE = "color_mode"
ATTR_HA_SUPPORTED_COLOR_MODES = "supported_color_modes"

ATTR_UL_AUDIO_INPUT = "audio_input"
ATTR_UL_CCT_COLOR = "cct_color"  # (kelvin, cool, warm, level)
ATTR_UL_CHANNELS = "channels"
ATTR_UL_CHIP_ORDER = "chip_order"
ATTR_UL_CHIP_TYPE = "chip_type"
ATTR_UL_COEXISTENCE = "coexistence"
ATTR_UL_DEVICE_NEEDS_ON = "device_needs_on"
ATTR_UL_DEVICE_FORCE_REFRESH = "device_force_refresh"
ATTR_UL_EFFECT = ATTR_HA_EFFECT
ATTR_UL_EFFECT_COLOR = "effect_color"
ATTR_UL_EFFECT_DIRECTION = "effect_direction"
ATTR_UL_EFFECT_LAYOUT = "effect_layout"
ATTR_UL_EFFECT_LENGTH = "effect_length"
ATTR_UL_EFFECT_LOOP = "effect_loop"
ATTR_UL_EFFECT_NUMBER = "effect_number"
ATTR_UL_EFFECT_PLAY = "effect_play"
ATTR_UL_EFFECT_SPEED = "effect_speed"
ATTR_UL_EFFECT_TYPE = "effect_type"
ATTR_UL_EFFECT_COLOR = "effect_white"
ATTR_UL_FREQUENCY = "frequency"
ATTR_UL_INFO_FIRMWARE = "info_firmware"
ATTR_UL_INFO_HARDWARE = "info_hardware"
ATTR_UL_INFO_MODEL_NAME = "info_model_name"
ATTR_UL_INFO_MANUFACTURER = "info_manufacturer"
ATTR_UL_IP_ADDRESS = "ip_address"
ATTR_UL_COLOR_LEVEL = "color_level"
ATTR_UL_LIGHT_MODE = "light_mode"
ATTR_UL_LIGHT_MODE_NUMBER = "light_mode_number"
ATTR_UL_LIGHT_TYPE = "light_type"
ATTR_UL_LIGHT_TYPE_NUMBER = "light_type_number"
ATTR_UL_LOCAL_NAME = "local_name"
ATTR_UL_MAC_ADDRESS = "mac_address"
ATTR_UL_MATRIX_HEIGHT = "matrix_height"
ATTR_UL_MATRIX_LAYOUT = "matrix_layout"
ATTR_UL_MATRIX_WIDTH = "matrix_width"
ATTR_UL_MATRIX_MODES = "matrix_modes"
ATTR_UL_MODE = "mode"
ATTR_UL_MODEL_CODE = "model_code"
ATTR_UL_MODEL_NAME = "model_name"
ATTR_UL_NODE_ID = "node_id"
ATTR_UL_NODE_TYPE = "node_type"
ATTR_UL_NODE_WIRING = "node_wiring"
ATTR_UL_ON_POWER = "on_power"
ATTR_UL_ONOFF_EFFECT = "onoff_effect"
ATTR_UL_ONOFF_SPEED = "onoff_speed"
ATTR_UL_ONOFF_PIXELS = "onoff_pixels"
ATTR_UL_OPTIONS = "options"
ATTR_UL_POWER = ATTR_HA_ONOFF
ATTR_UL_POWER_FUN_SWITCH = "power_fun_switch"
ATTR_UL_RGB2_COLOR = "rgb2_color"
ATTR_UL_RSSI = "RSSI"
ATTR_UL_SCENE = "scene"
ATTR_UL_SCENE_LOOP = "scene_loop"
ATTR_UL_SEGMENT = "segment"
ATTR_UL_SEGMENT_COUNT = "segment_count"
ATTR_UL_SEGMENT_PIXELS = "segment_pixels"
ATTR_UL_SENSITIVITY = "sensitivity"
ATTR_UL_SOURCE = "source"
ATTR_UL_STATIC_COLOR = "static_color"
ATTR_UL_STATIC_WHITE = "static_white"
ATTR_UL_STATUS = "status"
ATTR_UL_STRIP_MODES = "strip_modes"
ATTR_UL_SUGGESTED_AREA = "suggested_area"
ATTR_UL_TIMERS = "timers"
ATTR_UL_TOTAL_PIXELS = "total_pixels"
ATTR_UL_TRANSPORT = CONF_UL_TRANSPORT
ATTR_UL_TRANSITION_TIME = "transition_time"
ATTR_UL_WIFI_SSID = "wifi_ssid"

UNILED_ENTITY_ATTRIBUTES: Final = [
    ATTR_HA_COLOR_MODE,
    ATTR_HA_SUPPORTED_COLOR_MODES,
    ATTR_HA_TRANSITION,
    ATTR_HA_ONOFF,
    ATTR_HA_WHITE,
    ATTR_HA_BRIGHTNESS,
    ATTR_HA_RGB_COLOR,
    ATTR_HA_RGBW_COLOR,
    ATTR_HA_RGBWW_COLOR,
    ATTR_HA_XY_COLOR,
    ATTR_HA_HS_COLOR,
    ATTR_HA_COLOR_TEMP,
    ATTR_HA_KELVIN,
    ATTR_HA_MIN_MIREDS,
    ATTR_HA_MAX_MIREDS,
    ATTR_HA_COLOR_TEMP_KELVIN,
    ATTR_HA_MIN_COLOR_TEMP_KELVIN,
    ATTR_HA_MAX_COLOR_TEMP_KELVIN,
    ATTR_HA_COLOR_NAME,
    ATTR_HA_FLASH,
    ATTR_HA_EFFECT_LIST,
    ATTR_HA_EFFECT,
]

UNILED_STATUS_ATTRIBUTES: Final = [
    ATTR_UL_CCT_COLOR,
    ATTR_UL_CHANNELS,
    ATTR_UL_DEVICE_NEEDS_ON,
    ATTR_UL_DEVICE_FORCE_REFRESH,
    ATTR_UL_EFFECT_LAYOUT,
    ATTR_UL_EFFECT_NUMBER,
    ATTR_UL_EFFECT_TYPE,
    ATTR_UL_INFO_FIRMWARE,
    ATTR_UL_INFO_HARDWARE,
    ATTR_UL_INFO_MODEL_NAME,
    ATTR_UL_INFO_MANUFACTURER,
    ATTR_UL_COLOR_LEVEL,
    ATTR_UL_LIGHT_MODE_NUMBER,
    ATTR_UL_LIGHT_TYPE_NUMBER,
    ATTR_UL_MAC_ADDRESS,
    ATTR_UL_NODE_ID,
    ATTR_UL_NODE_TYPE,
    ATTR_UL_NODE_WIRING,
    ATTR_UL_RGB2_COLOR,
    ATTR_UL_RSSI,
    ATTR_UL_SCENE,
    ATTR_UL_STATUS,
    ATTR_UL_SUGGESTED_AREA,
    ATTR_UL_TOTAL_PIXELS,
    ATTR_UL_TRANSITION_TIME,
]

# These are ordered to ensure correct sequence of commands
# DO NOT CHANGE
UNILED_CONTROL_ATTRIBUTES: Final = [
    ATTR_UL_POWER,
    ATTR_UL_LIGHT_TYPE,
    ATTR_UL_LIGHT_MODE,
    ATTR_UL_EFFECT,
    ATTR_UL_EFFECT_LOOP,
    ATTR_UL_EFFECT_PLAY,
    ATTR_UL_EFFECT_SPEED,
    ATTR_UL_EFFECT_LENGTH,
    ATTR_UL_EFFECT_DIRECTION,
    ATTR_UL_SCENE_LOOP,
    ATTR_UL_AUDIO_INPUT,
    ATTR_UL_SENSITIVITY,
]

# These are ordered for a more logical sequence for users
# when changing a devices configuration - DO NOT CHANGE
UNILED_OPTIONS_ATTRIBUTES: Final = [
    ATTR_UL_LIGHT_TYPE,
    ATTR_UL_CHIP_TYPE,
    ATTR_UL_CHIP_ORDER,
    ATTR_UL_SEGMENT_COUNT,
    ATTR_UL_SEGMENT_PIXELS,
    ATTR_UL_ONOFF_EFFECT,
    ATTR_UL_ONOFF_SPEED,
    ATTR_UL_ONOFF_PIXELS,
    ATTR_UL_COEXISTENCE,
    ATTR_UL_ON_POWER,
]
