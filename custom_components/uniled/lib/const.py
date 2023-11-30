"""UniLED Constants."""
from typing import Final
from dataclasses import dataclass
from enum import IntEnum
from .helpers import StrEnum

# Home Assistant Config Keys
CONF_RETRY_COUNT = "retry_count"

UNILED_DEVICE_TIMEOUT: Final = 40
UNILED_DEVICE_RETRYS: Final = 3
UNILED_UPDATE_SECONDS: Final = 30
UNILED_REFRESH_DELAY: Final = 2.0
UNILED_DISCONNECT_DELAY: Final = 8.5
UNILED_COMMAND_SETTLE_DELAY: Final = 0.3
UNILED_STATE_CHANGE_LATENCY: Final = 2.0

UNILED_TRANSPORT_BLE = "ble"
UNILED_TRANSPORT_NET = "net"
UNILED_TRANSPORT_ZNG = "zng"

UNILED_UNKNOWN = "Unknown"
UNILED_MASTER = "Master"
UNILED_CHANNEL = "Channel"

UNILED_DEFAULT_MIN_KELVIN: Final = 1900
UNILED_DEFAULT_MAX_KELVIN: Final = 6600

UNILED_AUDIO_INPUT_AUX_IN: Final = "Aux In"
UNILED_AUDIO_INPUT_INTMIC: Final = "Int. Mic"
UNILED_AUDIO_INPUT_EXTMIC: Final = "Ext. Mic"
UNILED_AUDIO_INPUT_PLAYER: Final = "Player"


# Home Assistant Supported Light Attributes
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

# UniLED Specific Attributes
UNILED_EXTRA_ATTRIBUTE_TYPE = "extra"

ATTR_UL_INFO_FIRMWARE = "info_firmware"
ATTR_UL_INFO_HARDWARE = "info_hardware"
ATTR_UL_INFO_MODEL_NAME = "info_model_name"
ATTR_UL_INFO_MANUFACTURER = "info_manufacturer"

ATTR_UL_DEVICE_NEEDS_ON = "device_needs_on"
ATTR_UL_DEVICE_FORCE_REFRESH = "device_force_refresh"

ATTR_UL_POWER = ATTR_HA_ONOFF
ATTR_UL_ONOFF_EFFECT = "onoff_effect"
ATTR_UL_ONOFF_SPEED = "onoff_speed"
ATTR_UL_ONOFF_PIXELS ="onoff_pixels"
ATTR_UL_ON_POWER = "on_power"
ATTR_UL_COEXISTENCE = "coexistence"
ATTR_UL_CHIP_TYPE = "chip_type"
ATTR_UL_CHIP_ORDER = "chip_order"
ATTR_UL_SEGMENT_COUNT = "segment_count"
ATTR_UL_SEGMENT_PIXELS = "segment_pixels"
ATTR_UL_TOTAL_PIXELS = "total_pixels"
ATTR_UL_AUDIO_INPUT = "audio_input"
ATTR_UL_SENSITIVITY = "sensitivity"
ATTR_UL_LIGHT_MODE_NUMBER = "light_mode_number"
ATTR_UL_LIGHT_MODE = "light_mode"
ATTR_UL_LIGHT_TYPE = "light_type"
ATTR_UL_CCT_COLOR = "cct_color"  # (kelvin, cool, warm, level)
ATTR_UL_RGB2_COLOR = "rgb2_color"
ATTR_UL_EFFECT = ATTR_HA_EFFECT
ATTR_UL_EFFECT_NUMBER = "effect_number"
ATTR_UL_EFFECT_LOOP = "effect_loop"
ATTR_UL_EFFECT_PLAY = "effect_play"
ATTR_UL_EFFECT_TYPE = "effect_type"
ATTR_UL_EFFECT_SPEED = "effect_speed"
ATTR_UL_EFFECT_LENGTH = "effect_length"
ATTR_UL_EFFECT_DIRECTION = "effect_direction"
ATTR_UL_SCENE = "scene"
ATTR_UL_SCENE_LOOP = "scene_loop"
