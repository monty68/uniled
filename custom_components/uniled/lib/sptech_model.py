"""UniLED SPTech Common Components"""

from __future__ import annotations
from collections import namedtuple
from typing import Any, Final

from .const import *  # I know!
from .device import UniledDevice
from .channel import UniledChannel
from .sptech_conf import (
    UNILEDEffectType,
    UNILEDEffects,
    SPTechConf,
    SPTechFX,
)
from .features import (
    UniledAttribute,
    LightStripFeature,
    EffectTypeFeature,
    EffectLoopFeature,
    EffectPlayFeature,
    EffectSpeedFeature,
    EffectLengthFeature,
    EffectDirectionFeature,
    AudioInputFeature,
    AudioSensitivityFeature,
    LightModeFeature,
    LightTypeFeature,
    ChipOrderFeature,
    OnOffEffectFeature,
    OnOffSpeedFeature,
    OnOffPixelsFeature,
    CoexistenceFeature,
    OnPowerFeature,
)

import logging

_LOGGER = logging.getLogger(__name__)

RGB = namedtuple("RGB", ["r", "g", "b"])
RGBW = namedtuple("RGBW", ["r", "g", "b", "w"])
RGBWW = namedtuple("RGBWW", ["r", "g", "b", "cw", "ww"])


##
## BanlanX - SPTech Common Model Implementation
##
class SPTechModel(SPTechFX):
    """BanlanX - SPTech Common Model Implementation"""

    MANUFACTURER_NAME: Final = "SPLED (BanlanX)"

    HEADER_NET_PACKET: Final = bytes.fromhex("53505445434800")  # 'SPTECH\0'
    HEADER_BLE_PACKET: Final = bytes.fromhex("53")  # 'S'

    HEADER_PAYLOAD_LENGTH: Final = 6
    HEADER_PAYLOAD_COMMAND: Final = 0x00
    HEADER_PAYLOAD_KEY: Final = 0x01
    HEADER_PAYLOAD_SIZE_HI: Final = 0x04
    HEADER_PAYLOAD_SIZE_LO: Final = 0x05

    DICTOF_ONOFF_EFFECTS: Final = {
        0x01: UNILEDEffects.FLOW_FORWARD,
        0x02: UNILEDEffects.FLOW_BACKWARD,
        0x03: UNILEDEffects.GRADIENT,
        0x04: UNILEDEffects.STARS,
    }

    DICTOF_ONOFF_SPEEDS: Final = {
        0x01: "Slow",
        0x02: "Medium",
        0x03: "Fast",
    }

    MIN_ONOFF_PIXELS: Final = 1
    MAX_ONOFF_PIXELS: Final = 600

    DICTOF_ON_POWER_STATES: Final = {
        0x00: "Light Off",
        0x01: "Light On",
        0x02: "Last state",
    }

    MIN_CUSTOM_SLOT_PIXELS: Final = 0
    MAX_CUSTOM_SLOT_PIXELS: Final = 150

    MAX_EFFECT_SPEED: Final = 10
    MAX_EFFECT_LENGTH: Final = 150
    MAX_SENSITIVITY: Final = 16

    DICTOF_AUDIO_INPUTS: Final = {
        0x00: UNILED_AUDIO_INPUT_INTMIC,
        0x01: UNILED_AUDIO_INPUT_PLAYER,
        0x02: UNILED_AUDIO_INPUT_EXTMIC,
    }

    @dataclass
    class DIYSolidSlot:
        pixels: int = 0
        color: RGB = RGB(0, 0, 0)

        def __init__(self, data: bytearray):
            self.pixels = data[0] & 0xFF
            self.color = RGB(data[1], data[2], data[3])

    @dataclass(frozen=True)
    class cmd(IntEnum):
        STATUS_QUERY = 0x02
        ONOFF_OPTIONS = 0x08
        COEXISTENCE = 0x0A
        ON_POWER = 0x0B
        POWER = 0x50
        BRIGHTNESS = 0x51
        STATIC_COLOR = 0x52
        LIGHT_MODE = 0x53
        EFFECT_MODE = LIGHT_MODE
        EFFECT_SPEED = 0x54
        EFFECT_LENGTH = 0x55
        EFFECT_DIRECTION = 0x56
        EFFECT_COLOR = 0x57
        EFFECT_LOOP = 0x58
        AUDIO_INPUT = 0x59
        AUDIO_GAIN = 0x5A
        EFFECT_PLAY = 0x5D
        EFFECT_CCT = 0x60
        STATIC_CCT = 0x61
        LIGHT_TYPE = 0x6A
        CHIP_ORDER = 0x6B

    configs: dict[int, SPTechConf] | None = None
    encoder_key: int = 0

    def __encoder(self, device: UniledDevice, cmd: int, data: bytearray) -> bytearray:
        """Encode BanlanX Message. (currently not supported)"""
        bytes: int = len(data) & 0xFFFF
        message = self.__header_magic(device)
        message.append(cmd & 0xFF)
        message.append(self.encoder_key & 0xFF)
        if device.transport == UNILED_TRANSPORT_NET:
            message.append(0x00)
            message.append(0x00)
            message.extend(bytes.to_bytes(2, byteorder="big"))
        else:
            message.append(0x01)
            message.append(0x00)
            message.append(bytes & 0xFF)
        message.extend(data)
        return message

    def __header_magic(self, device: UniledDevice) -> bytearray:
        """Return Message Header Magic Byte(s)"""
        return bytearray(
            self.HEADER_NET_PACKET
            if device.transport == UNILED_TRANSPORT_NET
            else self.HEADER_BLE_PACKET
        )

    def __header_validate(
        self, device: UniledDevice, header: bytearray
    ) -> bytearray | None:
        """Validate and return message header payload"""
        magic_data = self.__header_magic(device)
        magic_size = len(magic_data)
        if not header.startswith(magic_data):
            None
        return header[magic_size:]

    def __header_extract_command(
        self, device: UniledDevice, header: bytearray
    ) -> int | None:
        """Return Message Header Command Byte"""
        if (payload := self.__header_validate(device, header)) is not None:
            return payload[self.HEADER_PAYLOAD_COMMAND]
        return None

    def length_response_header(self, device: UniledDevice, command: bytearray) -> int:
        """Expected header length of a command response"""
        if (payload := self.__header_validate(device, command)) is not None:
            if payload[self.HEADER_PAYLOAD_COMMAND] == self.cmd.STATUS_QUERY:
                return len(self.__header_magic(device)) + self.HEADER_PAYLOAD_LENGTH
        return 0

    def decode_response_header(
        self, device: UniledDevice, command: bytearray, header: bytearray
    ) -> int | None:
        """Decode a response header"""
        if (header := self.__header_validate(device, header)) is None:
            raise Exception(f"Response Header Invalid")
        payload_size = int.from_bytes(
            header[self.HEADER_PAYLOAD_SIZE_HI : self.HEADER_PAYLOAD_SIZE_LO + 1],
            byteorder="big",
        )
        return payload_size

    ## Decode Response Payload
    ##
    def decode_response_payload(
        self,
        device: UniledDevice,
        command: bytearray,
        header: bytearray,
        data: bytearray,
    ) -> bool:
        """Decode response payload data"""
        # Packet Format, 0x00 = 1 Byte Length Fields, 0x01 = 2 Byte Length Fields
        length_fields = data.pop(0)
        while len(data):
            chunk_type = data.pop(0)
            chunk_size = int.from_bytes(data[0 : 1 + length_fields], byteorder="big")
            data = data[length_fields + 1 :]
            if len(data) < chunk_size:
                raise Exception(
                    f"{device.name}: Message Chunk #{chunk_type} underun, expected: {chunk_size}, have: {len(data)}."
                )

            chunk_method = f"decode_chunk_{chunk_type}"
            chunk_decoder = getattr(self, chunk_method, None)
            if callable(chunk_decoder):
                try:
                    undecoded = chunk_decoder(device, chunk_type, data[:chunk_size])
                    if undecoded is not None and len(undecoded):
                        _LOGGER.debug(
                            "%s: Undecoded Chunk #%d bytes: %s (%d)",
                            device.name,
                            chunk_type,
                            undecoded.hex(),
                            len(undecoded),
                        )
                except Exception as ex:
                    _LOGGER.warning(
                        "%s: Exception decoding chunk %d: %s",
                        device.name,
                        chunk_type,
                        str(ex),
                    )
            else:
                _LOGGER.debug(
                    "%s: Unknown Chunk #%d: %s (%d)",
                    device.name,
                    chunk_type,
                    data[:chunk_size].hex(),
                    chunk_size,
                )
            # Next chunk
            data = data[chunk_size:]

        return True

    ## Message Chunk 1 - Settings - Device Firmware Version, Light Type & Power On/Off Settings
    ##
    def decode_chunk_1(
        self,
        device: UniledDevice,
        chunk: int,
        data: bytearray,
    ) -> bytearray | None:
        """Decode Chunk Type #1"""
        device.master.status.replace(
            {
                ATTR_UL_DEVICE_FORCE_REFRESH: True,
                "unknown1.0": data[0],
                "unknown1.1": data[1],
                ATTR_UL_INFO_FIRMWARE: data[2:10].decode("utf-8"),
                ATTR_UL_ONOFF_EFFECT: data[11],
                ATTR_UL_ONOFF_SPEED: data[12],
                ATTR_UL_ONOFF_PIXELS: int.from_bytes(data[13:15], byteorder="big"),
                ATTR_UL_ON_POWER: data[16],
            }
        )

        device.features = [
            OnOffEffectFeature(),
            OnOffSpeedFeature(),
            OnOffPixelsFeature(self.MAX_ONOFF_PIXELS),
            OnPowerFeature(),
        ]

        cfg: SPTechConf = self.match_light_type_config(data[10])
        if not cfg:
            raise Exception("Missing light type config!")

        device.master.context = cfg
        if self.configs and len(self.configs) > 1:
            device.master.features.append(LightTypeFeature())
            device.master.status.set(ATTR_UL_LIGHT_TYPE, cfg.name)

        if cfg.coexistence:
            device.master.features.append(CoexistenceFeature())
            device.master.status.set(ATTR_UL_COEXISTENCE, bool(data[15]))
        return None

    ## Message Chunk 2 - Device Mode, Status & Settings
    ##
    def decode_chunk_2(
        self,
        device: UniledDevice,
        chunk: int,
        data: bytearray,
    ) -> bytearray | None:
        """Decode Chunk Type #2 (and #3)"""
        device.master.status.update(
            {"unknown2.0": data[0], ATTR_UL_POWER: bool(power := data[1])}
        )

        loop = data[2]
        order = data[3]
        mode = data[4]
        effect = data[5]
        play = data[6]
        level_color = data[7]
        level_white = data[8]
        static_color = (data[9], data[10], data[11])
        static_white = (data[12], data[13])
        speed = data[14]
        length = data[15]
        direction = data[16]
        gain = data[17]
        input = data[18]
        effect_color = (data[19], data[20], data[21])
        effect_white = (data[22], data[23])
        data = data[24:]

        if not (cfg := device.master.context) or not isinstance(cfg, SPTechConf):
            return True

        if cfg.order and len(cfg.order) > 1:
            device.master.features.append(ChipOrderFeature())
            device.master.status.set(ATTR_UL_CHIP_ORDER, 
                self.chip_order_name(cfg.order, order)
            )

        device.master.status.update(
            {
                ATTR_UL_LIGHT_MODE_NUMBER: mode,
                ATTR_UL_LIGHT_MODE: (
                    UNILED_UNKNOWN
                    if mode not in self.DICTOF_MODES
                    else self.DICTOF_MODES[mode]
                ),
                ATTR_UL_EFFECT_NUMBER: effect,
                ATTR_UL_EFFECT: UNILED_UNKNOWN,
                ATTR_UL_EFFECT_TYPE: UNILED_UNKNOWN,
            }
        )

        if (fxlist := cfg.dictof_mode_effects(mode)) is not None:
            if fxattr := None if effect not in fxlist else fxlist[effect]:
                # _LOGGER.warn("%s: FXATTR: (%s) %s", device.name, cfg.name, fxattr)
                device.master.features.extend(
                    [
                        LightStripFeature(extra=UNILED_CONTROL_ATTRIBUTES),
                        LightModeFeature(),
                        EffectTypeFeature(),
                        EffectLoopFeature(),
                        EffectPlayFeature(),
                        EffectSpeedFeature(self.MAX_EFFECT_SPEED),
                        EffectLengthFeature(self.MAX_EFFECT_LENGTH),
                        EffectDirectionFeature(),
                        AudioInputFeature(),
                        AudioSensitivityFeature(self.MAX_SENSITIVITY),
                    ]
                )

                device.master.set(ATTR_HA_EFFECT, str(fxattr.name))

                device.master.set(
                    ATTR_UL_EFFECT_TYPE,
                    str(self.match_channel_effect_type(device.master, effect, mode)),
                )
                device.master.set(
                    ATTR_UL_EFFECT_LOOP,
                    bool(loop) if self.is_loop_mode(mode) else None,
                )
                device.master.set(
                    ATTR_UL_EFFECT_PLAY, bool(play) if fxattr.pausable else None
                )
                device.master.set(
                    ATTR_UL_EFFECT_SPEED, speed if fxattr.speedable else None
                )
                device.master.set(
                    ATTR_UL_EFFECT_LENGTH, length if fxattr.sizeable else None
                )
                device.master.set(
                    ATTR_UL_EFFECT_DIRECTION,
                    bool(direction) if fxattr.directional else None,
                )

                audio_input = (
                    self.str_if_key_in(input, self.DICTOF_AUDIO_INPUTS)
                    if power and self.is_sound_mode(mode)
                    else None
                )
                device.master.set(ATTR_UL_AUDIO_INPUT, audio_input)
                device.master.set(
                    ATTR_UL_SENSITIVITY, gain if audio_input is not None else None
                )

                if self.is_sound_mode(mode):
                    # In sound modes, irrespective of coexistence setting
                    # the color and white(s) are separatly controlled when
                    # supported by the effect, but brightness changes are
                    # not supported.
                    #
                    if self.is_white_mode(mode) and fxattr.colorable and cfg.cct:
                        device.master.set(ATTR_HA_BRIGHTNESS, 255)
                        device.master.set(ATTR_HA_WHITE, 255)
                        device.master.set(
                            ATTR_UL_CCT_COLOR,
                            (effect_white[0], effect_white[1], 255, None),
                        )
                    elif self.is_color_mode(mode) and fxattr.colorable and cfg.hue:
                        device.master.set(ATTR_HA_BRIGHTNESS, 255)
                        device.master.set(ATTR_HA_RGB_COLOR, effect_color)
                elif self.is_dynamic_mode(mode):
                    # In dynamic modes, irrespective of coexistence setting
                    # the color and white(s) are separatly controlled when
                    # supported by the effect, brightness changes are also
                    # supported.
                    #
                    if self.is_white_mode(mode) and fxattr.colorable and cfg.cct:
                        device.master.set(
                            ATTR_UL_CCT_COLOR,
                            (effect_white[0], effect_white[1], level_white, None),
                        )
                    elif self.is_color_mode(mode) and fxattr.colorable and cfg.hue:
                        device.master.set(ATTR_HA_RGB_COLOR, effect_color)
                    device.master.set(
                        ATTR_HA_BRIGHTNESS,
                        level_white if self.is_white_mode(mode) else level_color,
                    )
                elif self.is_static_mode(mode):
                    coexistence = device.master.get(ATTR_UL_COEXISTENCE, False)

                    if cfg.hue and cfg.cct and coexistence:
                        device.master.set(
                            ATTR_HA_RGBWW_COLOR,
                            static_color + static_white,
                            # (data[37], data[38], data[39], data[40], data[41]),
                        )
                    elif cfg.hue and cfg.white and coexistence:
                        device.master.set(
                            ATTR_HA_RGBW_COLOR,
                            static_color + (level_white),
                            # (data[37], data[38], data[39], level_white),
                        )
                    elif cfg.hue or cfg.cct or cfg.white:
                        white_mode = COLOR_MODE_BRIGHTNESS
                        supported_color_modes = set()

                        if cfg.hue:
                            device.master.set(ATTR_HA_RGB_COLOR, static_color)
                            supported_color_modes.add(COLOR_MODE_RGB)
                        if cfg.cct:
                            device.master.set(
                                ATTR_UL_CCT_COLOR,
                                static_white + (level_white, None),
                                # (data[40], data[41], white_level, None),
                            )
                            white_mode = COLOR_MODE_COLOR_TEMP
                            supported_color_modes.add(white_mode)
                        elif cfg.white and cfg.hue:
                            device.master.set(ATTR_HA_WHITE, level_white)
                            white_mode = COLOR_MODE_WHITE
                            supported_color_modes.add(white_mode)
                        else:
                            # Fix Issues #73 and #77
                            # supported_color_modes = set(white_mode)
                            supported_color_modes.add(white_mode)

                        device.master.set(
                            ATTR_HA_SUPPORTED_COLOR_MODES, supported_color_modes
                        )
                        device.master.set(
                            ATTR_HA_COLOR_MODE,
                            COLOR_MODE_RGB if self.is_color_mode(mode) else white_mode,
                        )
                    device.master.set(
                        ATTR_HA_BRIGHTNESS,
                        level_white if self.is_white_mode(mode) else level_color,
                    )
                elif mode in self.LISTOF_CUSTOM_MODES:
                    device.master.set(ATTR_HA_BRIGHTNESS, level_color)
            else:
                _LOGGER.debug("%s: Unknown effect: %d", device.name, effect)
        else:
            _LOGGER.debug("%s: Unknown light mode: %d", device.name, mode)

        ## DIY Solid Configuration Slots
        diy_solid_mode = data.pop(0)
        diy_solid_slot_count = data.pop(0)
        for slot in range(diy_solid_slot_count):
            slot_pixels = data.pop(0)
            slot_r = data.pop(0)
            slot_g = data.pop(0)
            slot_b = data.pop(0)

        return data

    ## Message Chunk 3 - Extended Device Status & Settings
    ##
    def decode_chunk_3(
        self,
        device: UniledDevice,
        chunk: int,
        data: bytearray,
    ) -> bytearray | None:
        """Decode Chunk Type #3"""
        device.master.status.update(
            {
                "unknown3.0": data.pop(0),
                ATTR_UL_LIGHT_TYPE_NUMBER: data.pop(0),
            }
        )
        data = self.decode_chunk_2(device, chunk, data)

        ## DIY Gradient Configuration Slots
        diy_gradient_mode = data.pop(0)
        diy_gradient_slot_count = data.pop(0)
        for slot in range(diy_gradient_slot_count):
            slot_level = data.pop(0)
            slot_r = data.pop(0)
            slot_g = data.pop(0)
            slot_b = data.pop(0)

        return data

    ## Message Chunk 4 - Timer
    ##
    def decode_chunk_4(
        self,
        device: UniledDevice,
        chunk: int,
        data: bytearray,
    ) -> bytearray | None:
        """Decode Chunk Type #4"""
        # _LOGGER.debug("%s: Decode Chunk #%d: %s (%d)", device.name, chunk, data.hex(), len(data))
        timers: dict[int, dict[str, Any]] = device.master.get(ATTR_UL_TIMERS, {})

        # 01 01 01 6a 01 12 38 - On  @ 07:30 PM - Sun, Tue, Thu, Sat & Enabled
        # 02 01 00 15 00 65 f4 - Off @ 07:15 AM - Mon, Wed, Fri & Enabled
        # 02 01 00 15 00 69 78 - Off @ 07:30 AM - Mon, Wed, Fri & Enabled
        #
        # For each timer set, there are 7 bytes
        #
        # 01 - Timer ID Number
        # 02 - State, 0=Disabled, 1=Enabled
        # 03 - Action, 0=Turn Off, 1=Turn On
        # 04 - Days, Bits: |?|S|S|M|T|W|T|F|
        # 05 - ? 0=AM, 1=PM
        # 06 - ?
        # 07 - ?
        #
        id = data[0]
        time = int.from_bytes(data[5:], byteorder="big")
        timers.update({id: {
            ATTR_UL_STATUS: bool(data[1]),
            ATTR_UL_POWER: bool(data[2]),
            "days": data[3],
            "meridiem": data[4],
            "time": time,
        }})
        device.master.set(ATTR_UL_TIMERS, timers)
        return None

    ## Message Chunk 5 - Effect Layout
    ##
    def decode_chunk_5(
        self,
        device: UniledDevice,
        chunk: int,
        data: bytearray,
    ) -> bytearray | None:
        """Decode Chunk Type #5"""
        device.master.status.update(
            {
                "unknown5.0": data.pop(0),
                ATTR_UL_EFFECT_LAYOUT: data.pop(0),
                ATTR_UL_MATRIX_WIDTH: data.pop(0),
                ATTR_UL_MATRIX_HEIGHT: data.pop(0),
                ATTR_UL_MATRIX_LAYOUT: data.pop(0),
            }
        )

        sound_strip_modes = {}
        strip_mode_count = data.pop(0)
        for strip_mode in range(strip_mode_count):
            segment_count = data.pop(0)
            sound_strip_modes[strip_mode] = {}
            for segment in range(segment_count):
                # Note: Total Segment Pixels <= 1200
                sound_strip_modes[strip_mode][segment] = {
                    ATTR_UL_SEGMENT: data[0],
                    ATTR_UL_SEGMENT_PIXELS: int.from_bytes(data[1:3], byteorder="big"),
                    ATTR_UL_EFFECT_DIRECTION: data[3],
                    ATTR_UL_EFFECT_NUMBER: data[4],
                    ATTR_UL_FREQUENCY: data[5],
                    ATTR_HA_RGB_COLOR: (data[6], data[7], data[8]),
                }
                data = data[9:]

        # if sound_strip_modes:
        #    device.master.set(ATTR_UL_STRIP_MODES, sound_strip_modes)

        sound_matrix_modes = {}
        matrix_mode_count = data.pop(0)
        for matrix_mode in range(matrix_mode_count):
            data = data[28:]

        # if sound_matrix_modes:
        #    device.master.set(ATTR_UL_MATRIX_MODES, sound_matrix_modes)

        return data

    ## Message Chunk 6 - Network Information
    ##
    def decode_chunk_6(
        self,
        device: UniledDevice,
        chunk: int,
        data: bytearray,
    ) -> bytearray | None:
        """Decode Chunk Type #6"""
        string_count = int.from_bytes(data[0:2], byteorder="big")
        data = data[2:]
        for string_idx in range(string_count):
            string_length = data.pop(0)
            string = str(data[:string_length].decode("utf-8"))
            data = data[string_length:]
            if string_length:
                if string_idx == 0:
                    device.master.set(ATTR_UL_WIFI_SSID, string)
                elif string_idx == 1:
                    device.master.set(ATTR_UL_IP_ADDRESS, string)
        data = data[2:]  # ??
        return data

    ## Message Chunk 7 - Fun Switch (experimental)
    ##
    def decode_chunk_7(
        self,
        device: UniledDevice,
        chunk: int,
        data: bytearray,
    ) -> bytearray | None:
        """Decode Chunk Type #7"""
        device.master.set(ATTR_UL_POWER_FUN_SWITCH, data.pop(0))
        return data

    ## Message Chunk 10 - Unknown
    ##
    def decode_chunk_10(
        self,
        device: UniledDevice,
        chunk: int,
        data: bytearray,
    ) -> bytearray | None:
        """Decode Chunk Type #10"""
        # 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16
        # --------------------------------------------------
        # 01 00 19 56 32 2e 30 2e 30 38 20 03 00 04 03 01 00
        #          V  2  .  0  .  0  8  SP
        return data

    ##
    ## Command Handlers
    ##
    def build_on_connect(self, device: UniledDevice) -> list[bytearray] | None:
        """Build on connect message(s)"""
        return None

    def build_state_query(self, device: UniledDevice) -> bytearray | None:
        """Build a state query message"""
        cmd = self.cmd.STATUS_QUERY
        if device.transport == UNILED_TRANSPORT_NET:
            return self.__encoder(device, cmd, bytearray())
        return self.__encoder(device, cmd, bytearray([0x01]))

    def build_onoff_effect_command(
        self, device: UniledDevice, channel: UniledChannel, value: str
    ) -> bytearray | None:
        """Build On/Off effect message(s)"""
        effect = self.fetch_onoff_effect_code(channel, value)
        speed = self.fetch_onoff_speed_code(channel)
        pixels = channel.status.onoff_pixels
        return self.__encoder(
            device,
            self.cmd.ONOFF_OPTIONS,
            bytearray([0x01, effect, speed]) + bytearray(pixels.to_bytes(2, "big")),
        )

    def fetch_onoff_effect_code(
        self, channel: UniledChannel, value: str | None = None
    ) -> int:
        """Return key for On/Off effect string"""
        value = channel.status.onoff_effect if value is None else value
        return self.int_if_str_in(value, self.DICTOF_ONOFF_EFFECTS, 0x01)

    def fetch_onoff_effect_list(
        self, device: UniledDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of On/Off modes"""
        return list(self.DICTOF_ONOFF_EFFECTS.values())

    def build_onoff_speed_command(
        self, device: UniledDevice, channel: UniledChannel, value: str
    ) -> bytearray | None:
        """Build On/Off speed message(s)"""
        effect = self.fetch_onoff_effect_code(channel)
        speed = self.fetch_onoff_speed_code(channel, value)
        pixels = channel.status.onoff_pixels
        return self.__encoder(
            device,
            self.cmd.ONOFF_OPTIONS,
            bytearray([0x01, effect, speed]) + bytearray(pixels.to_bytes(2, "big")),
        )

    def fetch_onoff_speed_code(
        self, channel: UniledChannel, value: str | None = None
    ) -> int:
        """Return key for On/Off speed string"""
        value = channel.status.onoff_speed if value is None else value
        return self.int_if_str_in(value, self.DICTOF_ONOFF_SPEEDS, 0x02)

    def fetch_onoff_speed_list(
        self, device: UniledDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of On/Off speeds"""
        return list(self.DICTOF_ONOFF_SPEEDS.values())

    def build_onoff_pixels_command(
        self, device: UniledDevice, channel: UniledChannel, pixels: int
    ) -> bytearray | None:
        """Build On/Off speed message(s)"""
        if not self.MIN_ONOFF_PIXELS <= pixels <= self.MAX_ONOFF_PIXELS:
            return None
        effect = self.fetch_onoff_effect_code(channel)
        speed = self.fetch_onoff_speed_code(channel)
        return self.__encoder(
            device,
            self.cmd.ONOFF_OPTIONS,
            bytearray([0x01, effect, speed])
            + bytearray(int(pixels).to_bytes(2, "big")),
        )

    def build_coexistence_command(
        self, device: UniledDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """Build color/white coexistence message(s)"""
        return self.__encoder(
            device, self.cmd.COEXISTENCE, bytearray([0x01 if state else 0x00])
        )

    def build_on_power_command(
        self, device: UniledDevice, channel: UniledChannel, value: Any
    ) -> bytearray | None:
        """Build on power restore message(s)"""
        if isinstance(value, str):
            mode = self.int_if_str_in(
                value, self.DICTOF_ON_POWER_STATES, channel.status.on_power
            )
        elif (mode := int(value)) not in self.DICTOF_ON_POWER_STATES:
            return None
        return self.__encoder(self.cmd.ON_POWER, bytearray([mode]))

    def fetch_on_power_list(
        self, device: UniledDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light modes"""
        return list(self.DICTOF_ON_POWER_STATES.values())

    def build_onoff_command(
        self, device: UniledDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """Build power on/off state message(s)"""
        return self.__encoder(
            device, self.cmd.POWER, bytearray([0x01 if state else 0x00])
        )

    def build_white_command(
        self, device: UniledDevice, channel: UniledChannel, level: int
    ) -> bytearray | None:
        """The bytes to send for a change to white mode"""
        if self.is_white_mode(channel.status.light_mode_number):
            _LOGGER.warning("Skip white mode change as already white")
            return None
        if self.is_sound_mode(channel.status.light_mode_number):
            mode = self.MODE_SOUND_WHITE
        elif self.is_dynamic_mode(channel.status.light_mode_number):
            mode = self.MODE_DYNAMIC_WHITE
        else:
            mode = self.MODE_STATIC_WHITE
        channel.status.set(ATTR_HA_COLOR_MODE, COLOR_MODE_WHITE)
        return self.build_light_mode_command(device, channel, mode)

    def build_brightness_command(
        self, device: UniledDevice, channel: UniledChannel, level: int
    ) -> bytearray | None:
        """The bytes to send for a brightness level change"""
        if self.is_sound_mode(channel.status.light_mode_number):
            _LOGGER.warning("Ignore brightness change in sound mode")
            channel.status.set(ATTR_HA_BRIGHTNESS, 255)
            return None
        which = 0x00 if self.is_color_mode(channel.status.light_mode_number) else 0x01
        return self.__encoder(device, self.cmd.BRIGHTNESS, bytearray([which, level]))

    def build_rgb_color_command(
        self, device: UniledDevice, channel: UniledChannel, rgb: tuple[int, int, int]
    ) -> bytearray | None:
        """The bytes to send for RGB color level change"""
        red, green, blue = rgb
        if self.is_static_mode(channel.status.light_mode_number):
            level = channel.status.brightness
            if level is None:
                level = 0xFF
            return self.__encoder(
                device, self.cmd.STATIC_COLOR, bytearray([red, green, blue, level])
            )
        return self.__encoder(
            device, self.cmd.EFFECT_COLOR, bytearray([red, green, blue])
        )

    def build_rgbw_color_command(
        self,
        device: UniledDevice,
        channel: UniledChannel,
        rgbw: tuple[int, int, int, int],
    ) -> bytearray | None:
        """The bytes to send for RGBW color level change"""
        red, green, blue, white = rgbw
        return [
            self.build_rgb_color_command(device, channel, (red, green, blue)),
            self.__encoder(device, self.cmd.BRIGHTNESS, bytearray([0x01, white])),
        ]

    def build_rgbww_color_command(
        self,
        device: UniledDevice,
        channel: UniledChannel,
        rgbww: tuple[int, int, int, int, int],
    ) -> list[bytearray] | None:
        """The bytes to send for RGBWW color level change"""
        red, green, blue, cold, warm = rgbww
        level = channel.status.brightness
        if level is None:
            level = 0xFF
        return [
            self.build_rgb_color_command(device, channel, (red, green, blue)),
            self.build_cct_color_command(device, channel, (cold, warm, level, None)),
        ]

    def build_cct_color_command(
        self,
        device: UniledDevice,
        channel: UniledChannel,
        cct: tuple[int, int, int, int],
    ) -> bytearray | None:
        """The bytes to send for a temperature color change."""
        cold, warm, level, kelvin = cct
        if self.is_static_mode(channel.status.light_mode_number):
            return self.__encoder(device, self.cmd.STATIC_CCT, bytearray([cold, warm]))
        return self.__encoder(device, self.cmd.EFFECT_CCT, bytearray([cold, warm]))

    def build_light_mode_command(
        self,
        device: UniledDevice,
        channel: UniledChannel,
        value: Any,
        effect: int | None = None,
    ) -> list[bytearray] | None:
        """The bytes to send for a light mode change."""
        cfg: SPTechConf = channel.context
        if isinstance(value, str):
            mode = self.int_if_str_in(
                value, self.DICTOF_MODES, channel.status.light_mode_number
            )
        elif (mode := int(value)) not in self.DICTOF_MODES:
            return None
        if not cfg or (fxlist := cfg.dictof_mode_effects(mode)) is None:
            return None
        if effect is None:
            effect = channel.status.effect_number
        force_refresh = False
        if mode != channel.status.light_mode_number:
            if effect not in fxlist:
                effect = next(iter(fxlist))
            force_refresh = True
        commands = [
            self.__encoder(device, self.cmd.LIGHT_MODE, bytearray([mode, effect]))
        ]
        if force_refresh or not channel.status.get(ATTR_UL_DEVICE_FORCE_REFRESH):
            commands.append(self.build_state_query(device))
        return commands

    def fetch_light_mode_list(
        self, device: UniledDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light modes"""
        return list(self.fetch_light_mode_dict(channel).values())

    def fetch_light_mode_dict(self, channel: UniledChannel) -> dict:
        """Channel mode dictionary"""
        modes = dict()
        cfg: SPTechConf = channel.context
        if cfg is not None and cfg.effects:
            for m in cfg.effects:
                modes[m] = str(self.DICTOF_MODES[m])
        return modes

    def build_effect_command(
        self,
        device: UniledDevice,
        channel: UniledChannel,
        effect: Any,
        mode: int | None = None,
    ) -> list[bytearray] | None:
        """The bytes to send for an effect change"""
        if mode is None:
            mode = channel.status.light_mode_number
        if isinstance(effect, str):
            cfg: SPTechConf = channel.context
            if not cfg:
                return None
            effect = self.int_if_str_in(
                effect, cfg.dictof_channel_effects(mode), channel.status.effect_number
            )
        return self.build_light_mode_command(device, channel, mode, effect)

    def fetch_effect_list(
        self, device: UniledDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of effect names"""
        cfg: SPTechConf = channel.context
        mode = channel.status.light_mode_number
        if cfg and mode is not None:
            if (fxlist := cfg.dictof_mode_effects(mode)) is not None:
                effects = list()
                for fx in fxlist:
                    effects.append(str(fxlist[fx].name))
                return effects
        return None

    def build_effect_speed_command(
        self, device: UniledDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect speed change."""
        speed = int(value) & 0xFF
        if not 1 <= speed <= self.MAX_EFFECT_SPEED:
            return None
        return self.__encoder(device, self.cmd.EFFECT_SPEED, bytearray([speed]))

    def build_effect_length_command(
        self, device: UniledDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect length change."""
        length = int(value) & 0xFF
        if not 1 <= length <= self.MAX_EFFECT_LENGTH:
            return None
        return self.__encoder(device, self.cmd.EFFECT_LENGTH, bytearray([length]))

    def build_effect_direction_command(
        self, device: UniledDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """The bytes to send for an effect direction change."""
        return self.__encoder(
            device, self.cmd.EFFECT_DIRECTION, bytearray([0x01 if state else 0x00])
        )

    def build_effect_loop_command(
        self, device: UniledDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """The bytes to send to enable/disable looping effects."""
        return self.__encoder(
            device, self.cmd.EFFECT_LOOP, bytearray([0x01 if state else 0x00])
        )

    def build_audio_input_command(
        self, device: UniledDevice, channel: UniledChannel, value: str
    ) -> bytearray | None:
        """The bytes to send for an input change"""
        input = self.int_if_str_in(str(value), self.DICTOF_AUDIO_INPUTS, 0x00)
        return self.__encoder(device, self.cmd.AUDIO_INPUT, bytearray([input]))

    def fetch_audio_input_list(
        self, device: UniledDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light modes"""
        return list(self.DICTOF_AUDIO_INPUTS.values())

    def build_sensitivity_command(
        self, device: UniledDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for a gain/sensitivity change"""
        gain = int(value) & 0xFF
        if not 1 <= gain <= self.MAX_SENSITIVITY:
            return None
        return self.__encoder(device, self.cmd.AUDIO_GAIN, bytearray([gain]))

    def build_effect_play_command(
        self, device: UniledDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """The bytes to send to play/pause effects."""
        return self.__encoder(
            device, self.cmd.EFFECT_PLAY, bytearray([0x01 if state else 0x00])
        )

    def build_light_type_command(
        self, device: UniledDevice, channel: UniledChannel, value: str
    ) -> list[bytearray]:
        """Build light type message(s)"""
        if (
            light := self.int_if_str_in(str(value), self.fetch_light_type_dict())
        ) is None:
            return None
        cfg: SPTechConf = self.match_light_type_config(light)
        if cfg is None:
            return None
        channel.context = cfg
        order = (
            None
            if cfg.order is None
            else self.chip_order_index(cfg.order, channel.status.chip_order)
        )
        if order is None:
            order = 0x00
        mode = channel.status.light_mode_number
        effect = channel.status.effect_number

        if mode not in cfg.effects:
            mode = next(iter(cfg.effects))

        commands = []
        if power := channel.status.onoff:
            commands.append(self.build_onoff_command(device, channel, False))
        commands.append(
            self.__encoder(device, self.cmd.LIGHT_TYPE, bytearray([0x01, light & 0x7F]))
        )
        commands.append(self.__encoder(device, self.cmd.CHIP_ORDER, bytearray([order])))
        commands.extend(self.build_light_mode_command(device, channel, mode))
        return commands

    def fetch_light_type_dict(self) -> dict | None:
        """Mode effects dictionary"""
        types = dict()
        if self.configs is not None:
            for key, cfg in self.configs.items():
                types[key] = cfg.name
        return types

    def fetch_light_type_list(
        self, device: UniledDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light types"""
        listing = list()
        if self.configs is not None:
            for _, cfg in self.configs.items():
                listing.append(str(cfg.name))
        return listing

    def build_chip_order_command(
        self, device: UniledDevice, channel: UniledChannel, value: str | None = None
    ) -> list[bytearray]:
        """Build chip order message(s)"""
        cfg: SPTechConf = channel.context
        if cfg is not None and cfg.order:
            order = self.chip_order_index(cfg.order, value)
            return self.__encoder(device, self.cmd.CHIP_ORDER, bytearray([order]))
        return None

    def fetch_chip_order_list(
        self, device: UniledDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of chip orders"""
        cfg: SPTechConf = channel.context
        if cfg is not None and cfg.order:
            return self.chip_order_list(cfg.order)
        return None

    ##
    ## Helpers
    ##
    def match_light_type_config(self, light_type: int) -> SPTechConf | None:
        """Light type dictionary"""
        if self.configs is not None:
            if light_type in self.configs:
                return self.configs[light_type]
            if len(self.configs) > 1:
                return next(iter(self.configs))
        return None

    def match_channel_effect_type(
        self, channel: UniledChannel, effect: int | None = None, mode: int | None = None
    ) -> str:
        """Code of channel effect type from effect code"""
        if effect is None:
            effect = channel.status.effect
        if mode is None:
            mode = channel.status.mode
        if self.is_custom_mode(mode):
            cfg: SPTechConf = channel.context
            if cfg and cfg.spi and effect == 0x01:
                return UNILEDEffectType.STATIC
        if self.is_static_mode(mode):
            return UNILEDEffectType.STATIC
        if self.is_sound_mode(mode):
            return UNILEDEffectType.SOUND
        return UNILEDEffectType.DYNAMIC

    def is_dynamic_mode(self, mode: int | None) -> bool:
        """Is a dynamic mode"""
        if (mode is not None) and mode in self.LISTOF_DYNAMIC_MODES:
            return True
        return False

    def is_static_mode(self, mode: int | None) -> bool:
        """Is a static mode"""
        if (mode is not None) and mode in self.LISTOF_STATIC_MODES:
            return True
        return False

    def is_sound_mode(self, mode: int | None) -> bool:
        """Is a sound mode"""
        if (mode is not None) and mode in self.LISTOF_SOUND_MODES:
            return True
        return False

    def is_color_mode(self, mode: int | None) -> bool:
        """Is a color mode"""
        if (mode is not None) and mode in self.LISTOF_COLOR_MODES:
            return True
        return False

    def is_white_mode(self, mode: int | None) -> bool:
        """Is a white mode"""
        if (mode is not None) and mode in self.LISTOF_WHITE_MODES:
            return True
        return False

    def is_loop_mode(self, mode: int | None) -> bool:
        """Is a loopable mode"""
        if (mode is not None) and mode in self.LISTOF_LOOPABLE_MODES:
            return True
        return False

    def is_custom_mode(self, mode: int | None) -> bool:
        """Is a custom mode"""
        if (mode is not None) and mode in self.LISTOF_CUSTOM_MODES:
            return True
        return False
