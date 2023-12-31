"""UniLED BLE Devices - SP LED (BanlanX v3)"""
from __future__ import annotations
from itertools import chain
from typing import Final

from ..const import *  # I know!
from ..channel import UniledChannel
from ..features import (
    UniledAttribute,
    LightStripFeature,
    LightModeFeature,
    EffectTypeFeature,
    EffectSpeedFeature,
    AudioSensitivityFeature,
    AudioInputFeature,
    ChipOrderFeature,
    EffectLoopFeature,
)
from ..effects import (
    UNILED_EFFECT_TYPE_DYNAMIC,
    UNILED_EFFECT_TYPE_STATIC,
    UNILED_EFFECT_TYPE_SOUND,
    UNILEDEffects,
)
from .device import (
    UUID_BASE_FORMAT as BANLANX_UUID_FORMAT,
    BANLANX_MANUFACTURER,
    BANLANX_MANUFACTURER_ID,
    ParseNotificationError,
    UniledBleDevice,
    UniledBleModel,
)

from ..chips import UNILED_CHIP_ORDER_RGB, UNILED_CHIP_ORDER_RGBW

import logging

_LOGGER = logging.getLogger(__name__)

BANLANX3_AUDIO_INPUTS: Final = {
    0x00: UNILED_AUDIO_INPUT_INTMIC,
    0x01: UNILED_AUDIO_INPUT_PLAYER,
    0x02: UNILED_AUDIO_INPUT_EXTMIC,
}

BANLANX3_MAX_SENSITIVITY: Final = 16
BANLANX3_MAX_EFFECT_SPEED: Final = 10

BANLANX3_LIGHT_MODE_SINGULAR: Final = 0x00
BANLANX3_LIGHT_MODE_AUTO_DYNAMIC: Final = 0x01
BANLANX3_LIGHT_MODE_AUTO_SOUND: Final = 0x02

BANLANX3_LIGHT_MODES: Final = {
    BANLANX3_LIGHT_MODE_SINGULAR: "Single FX",
    BANLANX3_LIGHT_MODE_AUTO_DYNAMIC: "Cycle Dynamic FX's",
    BANLANX3_LIGHT_MODE_AUTO_SOUND: "Cycle Sound FX's",
}

BANLANX3_EFFECT_DYNAMIC: Final = 0x01
BANLANX3_EFFECT_SOLID: Final = 0x63
BANLANX3_EFFECT_CUSTOM: Final = 0x64
BANLANX3_EFFECT_SOUND: Final = 0x65
BANLANX3_EFFECT_WHITE: Final = 0xCC

BANLANX3_EFFECTS_RGB: Final = {
    BANLANX3_EFFECT_SOLID: UNILEDEffects.SOLID_COLOR,
    BANLANX3_EFFECT_DYNAMIC + 0: UNILEDEffects.GRADIENT_SEVEN_COLOR,
    BANLANX3_EFFECT_DYNAMIC + 1: UNILEDEffects.JUMP_SEVEN_COLOR,
    BANLANX3_EFFECT_DYNAMIC + 2: UNILEDEffects.BREATH_SEVEN_COLOR,
    BANLANX3_EFFECT_DYNAMIC + 3: UNILEDEffects.STROBE_SEVEN_COLOR,
    BANLANX3_EFFECT_DYNAMIC + 4: UNILEDEffects.BREATH_RED,
    BANLANX3_EFFECT_DYNAMIC + 5: UNILEDEffects.BREATH_GREEN,
    BANLANX3_EFFECT_DYNAMIC + 6: UNILEDEffects.BREATH_BLUE,
    BANLANX3_EFFECT_DYNAMIC + 7: UNILEDEffects.BREATH_YELLOW,
    BANLANX3_EFFECT_DYNAMIC + 8: UNILEDEffects.BREATH_CYAN,
    BANLANX3_EFFECT_DYNAMIC + 9: UNILEDEffects.BREATH_PURPLE,
    BANLANX3_EFFECT_DYNAMIC + 10: UNILEDEffects.BREATH_WHITE,
    BANLANX3_EFFECT_DYNAMIC + 11: UNILEDEffects.STROBE_RED,
    BANLANX3_EFFECT_DYNAMIC + 12: UNILEDEffects.STROBE_GREEN,
    BANLANX3_EFFECT_DYNAMIC + 13: UNILEDEffects.STROBE_BLUE,
    BANLANX3_EFFECT_DYNAMIC + 14: UNILEDEffects.STROBE_YELLOW,
    BANLANX3_EFFECT_DYNAMIC + 15: UNILEDEffects.STROBE_CYAN,
    BANLANX3_EFFECT_DYNAMIC + 16: UNILEDEffects.STROBE_PURPLE,
    BANLANX3_EFFECT_DYNAMIC + 17: UNILEDEffects.STROBE_WHITE,
    BANLANX3_EFFECT_DYNAMIC + 31: "Adjustable Color Breath",  # Colorable
    BANLANX3_EFFECT_DYNAMIC + 32: "Adjustable Color Strobe",  # Colorable
    BANLANX3_EFFECT_CUSTOM: UNILEDEffects.CUSTOM,
}

BANLANX3_EFFECTS_RGBW: Final = dict(
    chain.from_iterable(
        d.items()
        for d in (
            {BANLANX3_EFFECT_WHITE: UNILEDEffects.SOLID_WHITE},
            BANLANX3_EFFECTS_RGB,
        )
    )
)

BANLANX3_EFFECTS_SOUND: Final = {
    BANLANX3_EFFECT_SOUND + 0: UNILEDEffects.SOUND_MUSIC_BREATH,  # 65
    BANLANX3_EFFECT_SOUND + 1: UNILEDEffects.SOUND_MUSIC_JUMP,  # 66
    BANLANX3_EFFECT_SOUND + 2: UNILEDEffects.SOUND_MUSIC_MONO_BREATH,  # 67 - Colorable
}

BANLANX3_EFFECTS_RGB_SOUND: Final = dict(
    chain.from_iterable(
        d.items()
        for d in (
            BANLANX3_EFFECTS_RGB,
            BANLANX3_EFFECTS_SOUND,
        )
    )
)

BANLANX3_EFFECTS_RGBW_SOUND: Final = dict(
    chain.from_iterable(
        d.items()
        for d in (
            BANLANX3_EFFECTS_RGBW,
            BANLANX3_EFFECTS_SOUND,
        )
    )
)

BANLANX3_COLORABLE_EFFECTS: Final = (
    BANLANX3_EFFECT_SOLID,
    32,  #  Adjustable Color Breath
    33,  #  Adjustable Color Strobe
    103,  # Monochrome Music Breath
)


class BanlanX3(UniledBleModel):
    """BanlanX v3 Protocol Implementation"""

    colors: int
    intmic: bool

    def __init__(
        self, id: int, name: str, info: str, data: bytes, colors: int, intmic: bool
    ):
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
        self.colors = colors
        self.intmic = intmic

    ## 02 07 10 a7 a6 00 e0 f1 04
    ## 01 02 03 04 05 b3 00 02
    ## 1e 01 01
    ## 1e 01 02
    ## 1a 01 0a 01 64 00 00 00 ff 00 00 00 ff (set DIY colors, 3rd byte number of data bytes)
    ## 1a 01 0a 01 64 00 00 00 65 00 00 00 ff
    ## 1f 03 00 ff 00

    ## 11 01 03             - Calibration
    ## 12 01 ff             - Level
    ## 13 04 b3 00 ff ff    - Color & Level
    ## 14 01 09             - Speed
    ## 15 01 01             - Effect 0x63 = Solid, 0x65 = Music, 0x01+ = Pattern
    ## 16 01 00             - Auto Mode 0x00 = Off, 0x01 Auto Pattern, 0x02 Auto Music
    ## 17 01 0f             - Gain/Sensitivity (0x01 - 0x0F)
    ## 19 01 01             - Input

    def parse_notifications(
        self,
        device: UniledBleDevice,
        sender: int,
        data: bytearray,
    ) -> bool:
        """Parse notification message(s)"""

        _PACKET_NUMBER = 0
        _MESSAGE_LENGTH = 1
        _PAYLOAD_LENGTH = 2
        _HEADER_LENGTH = 3

        packet_number = data[_PACKET_NUMBER]

        if packet_number == 1:
            message_length = data[_MESSAGE_LENGTH]
            payload_length = data[_PAYLOAD_LENGTH]

            data = device.save_notification_data(data)
            if message_length > payload_length:
                return False
            data = data[_HEADER_LENGTH:]
        else:
            if (
                len((last := device.last_notification_data)) == 0
                or last[_PACKET_NUMBER] != packet_number - 1
            ):
                raise ParseNotificationError("Skip out of sequence Packet!")

            message_length = last[_MESSAGE_LENGTH]
            payload_length = data[_MESSAGE_LENGTH]
            payload_so_far = last[_PAYLOAD_LENGTH] + payload_length

            if payload_so_far < message_length:
                last[_PACKET_NUMBER] = packet_number
                last[_PAYLOAD_LENGTH] = payload_so_far
                device.save_notification_data(last + data[2:])
                return False

            if (
                payload_so_far > message_length
                or message_length != last[_MESSAGE_LENGTH]
            ):
                raise ParseNotificationError("Bad Packet!")
            data = last[_HEADER_LENGTH:] + data[2:]

        if len(data) != message_length:
            raise ParseNotificationError("Unknown/Invalid Packet!")

        #
        # 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
        # --------------------------------------------------------------------------
        # 01 ff 0a 00 65 00 00 ff ff 10 01 03 ff 00 00 00 ff 00 00 00 ff 00 01 40 00
        #                                  D# R1 G1 B1 R2 G2 B2 R3 G3 B3 T# AI CW WW
        #
        # 0  = Power State
        # 1  = level
        # 2  = Speed
        # 3  = Chip Order (Calibration)
        # 4  = Effect
        # 5  = Auto Mode (0x00 = Off, 0x01 = Cycle FX, 0x02 = Cycle Sound)
        # 6  = Red Level (0x00 - 0xFF)
        # 7  = Green Level (0x00 - 0xFF)
        # 8  = Blue Level (x00 - 0xFF)
        # 9  = Gain/Sensitivity (0x01 - 0x0F)
        # 10 = DIY Effect Type
        # 11 = DIY # Colors
        # 12 = DIY FX - Color 1 - Red Level
        # 13 = DIY FX - Color 1 - Green Level
        # 14 = DIY FX - Color 1 - Blue Level
        #
        # SP613E & SP614E - 3rd from last byte in message is the sound input type
        #
        # SP614E Only - Last two bytes in message are cool and warm white levels.
        #
        # xx = Cool White Level
        # xx = Warm White Level (Not used on SP614E)
        #
        _LOGGER.debug("%s: Good Status Message: %s", device.name, data.hex())

        if not device.master.features:
            features = [
                LightStripFeature(extra=UNILED_CONTROL_ATTRIBUTES),
                EffectTypeFeature(),
                EffectSpeedFeature(BANLANX3_MAX_EFFECT_SPEED),
                ChipOrderFeature(),
            ]

            if self.intmic:
                features.append(LightModeFeature()),
                features.append(AudioInputFeature())
                features.append(AudioSensitivityFeature(BANLANX3_MAX_SENSITIVITY))
            else:
                features.append(EffectLoopFeature())
            device.master.features = features

        level = data[1]
        speed = data[2]
        chip_order = data[3]
        effect = data[4]
        mode = data[5]
        rgb = (data[6], data[7], data[8])
        gain = data[9]
        input = data[message_length - 3]
        cold = data[message_length - 2]
        # warm = data[message_length - 1]

        device.master.status.replace(
            {
                ATTR_UL_DEVICE_FORCE_REFRESH: True,
                ATTR_UL_POWER: data[0] == 1,
                ATTR_HA_SUPPORTED_COLOR_MODES: [COLOR_MODE_BRIGHTNESS],
                ATTR_HA_COLOR_MODE: COLOR_MODE_BRIGHTNESS,
                ATTR_UL_CHIP_ORDER: self.chip_order_name(
                    UNILED_CHIP_ORDER_RGBW
                    if self.colors == 4
                    else UNILED_CHIP_ORDER_RGB,
                    chip_order,
                ),
                ATTR_UL_LIGHT_MODE_NUMBER: mode,
                ATTR_UL_LIGHT_MODE: self.str_if_key_in(
                    mode, BANLANX3_LIGHT_MODES, UNILED_UNKNOWN
                ),
                ATTR_UL_EFFECT_NUMBER: 0,
                ATTR_HA_EFFECT: UNILED_UNKNOWN,
                ATTR_UL_EFFECT_TYPE: UNILED_UNKNOWN,
                ATTR_UL_EFFECT_LOOP: True if mode != 0 else False,
                ATTR_HA_BRIGHTNESS: level,
                ATTR_HA_RGB_COLOR: rgb,
            }
        )

        if mode == BANLANX3_LIGHT_MODE_SINGULAR:
            device.master.set(ATTR_UL_EFFECT_NUMBER, effect)
            device.master.set(
                ATTR_HA_EFFECT,
                self.str_if_key_in(effect, BANLANX3_EFFECTS_RGBW_SOUND, UNILED_UNKNOWN),
            )
            if self.colors == 4:
                device.master.set(ATTR_HA_WHITE, cold)
                device.master.set(
                    ATTR_HA_SUPPORTED_COLOR_MODES, [COLOR_MODE_RGB, COLOR_MODE_WHITE]
                )
            else:
                device.master.set(ATTR_HA_SUPPORTED_COLOR_MODES, [COLOR_MODE_RGB])

            if effect >= BANLANX3_EFFECT_SOUND and effect < BANLANX3_EFFECT_WHITE:
                device.master.set(ATTR_UL_EFFECT_TYPE, UNILED_EFFECT_TYPE_SOUND)
                device.master.set(ATTR_UL_SENSITIVITY, gain)
                device.master.set(
                    ATTR_UL_AUDIO_INPUT,
                    self.str_if_key_in(input, BANLANX3_AUDIO_INPUTS, UNILED_UNKNOWN),
                )
                device.master.set(ATTR_HA_SUPPORTED_COLOR_MODES, [COLOR_MODE_ONOFF])
                device.master.set(ATTR_HA_COLOR_MODE, COLOR_MODE_ONOFF)
                device.master.set(ATTR_UL_COLOR_LEVEL, level)
                device.master.set(ATTR_HA_BRIGHTNESS, None)
            elif effect == BANLANX3_EFFECT_SOLID or effect == BANLANX3_EFFECT_WHITE:
                device.master.set(ATTR_UL_EFFECT_TYPE, UNILED_EFFECT_TYPE_STATIC)
                if effect == BANLANX3_EFFECT_WHITE:
                    device.master.set(
                        ATTR_HA_SUPPORTED_COLOR_MODES,
                        [COLOR_MODE_RGB, COLOR_MODE_WHITE],
                    )
                    device.master.set(ATTR_HA_COLOR_MODE, COLOR_MODE_WHITE)
                    device.master.set(ATTR_HA_BRIGHTNESS, cold)
                    device.master.set(ATTR_UL_COLOR_LEVEL, level)
                    return True
            else:
                device.master.set(ATTR_UL_EFFECT_SPEED, speed)
                device.master.set(ATTR_UL_EFFECT_TYPE, UNILED_EFFECT_TYPE_DYNAMIC)

            if effect in BANLANX3_COLORABLE_EFFECTS:
                device.master.set(ATTR_HA_COLOR_MODE, COLOR_MODE_RGB)

        elif mode == BANLANX3_LIGHT_MODE_AUTO_DYNAMIC:
            device.master.set(ATTR_UL_EFFECT_TYPE, UNILED_EFFECT_TYPE_DYNAMIC)
            device.master.set(ATTR_UL_EFFECT_SPEED, speed)
        elif mode == BANLANX3_LIGHT_MODE_AUTO_SOUND:
            device.master.set(ATTR_UL_EFFECT_TYPE, UNILED_EFFECT_TYPE_SOUND)
            device.master.set(ATTR_UL_SENSITIVITY, gain)
            device.master.set(ATTR_HA_SUPPORTED_COLOR_MODES, [COLOR_MODE_ONOFF])
            device.master.set(ATTR_HA_COLOR_MODE, COLOR_MODE_ONOFF)
            device.master.set(ATTR_UL_COLOR_LEVEL, level)
            device.master.set(ATTR_HA_BRIGHTNESS, None)
        return True

    def build_on_connect(self, device: UniledBleDevice) -> list[bytearray] | None:
        """Build on connect message(s)"""
        return None

    def build_state_query(self, device: UniledBleDevice) -> bytearray:
        """Build a state query message"""
        return bytearray([0x1D, 0x00])

    def build_light_mode_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str
    ) -> list[bytearray] | None:
        """The bytes to send for a light mode change."""
        if isinstance(value, str):
            mode = self.int_if_str_in(
                value, BANLANX3_LIGHT_MODES, BANLANX3_LIGHT_MODE_SINGULAR
            )
        elif (mode := int(value)) not in BANLANX3_LIGHT_MODES:
            return None
        return bytearray([0x16, 0x01, mode])

    def fetch_light_mode_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light modes"""
        return list(BANLANX3_LIGHT_MODES.values())

    def build_onoff_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray:
        """Build power on/off state message(s)"""
        return bytearray([0x0F, 0x01, 0x01 if state else 0x00])

    def build_white_command(
        self, device: UniledBleDevice, channel: UniledChannel, white: int
    ) -> bytearray | None:
        """The bytes to send for a white mode change."""
        if channel.status.effect_number != BANLANX3_EFFECT_WHITE:
            return self.build_effect_command(device, channel, BANLANX3_EFFECT_WHITE)
        return None

    def build_brightness_command(
        self, device: UniledBleDevice, channel: UniledChannel, level: int
    ) -> bytearray:
        """The bytes to send for a brightness level change"""
        if channel.status.effect_number == BANLANX3_EFFECT_WHITE:
            return bytearray([0x21, 0x02, level & 0xFF, 0xFF])
        return bytearray([0x12, 0x01, level & 0xFF])

    def build_rgb_color_command(
        self, device: UniledBleDevice, channel: UniledChannel, rgb: tuple[int, int, int]
    ) -> bytearray | None:
        """The bytes to send for an RGB color change"""
        channel.set(ATTR_HA_RGB_COLOR, rgb)
        commands = []

        if channel.status.effect_number not in BANLANX3_COLORABLE_EFFECTS:
            commands.append(
                self.build_effect_command(device, channel, BANLANX3_EFFECT_SOLID)
            )

        red, green, blue = rgb
        level = channel.get(ATTR_UL_COLOR_LEVEL, channel.get(ATTR_HA_BRIGHTNESS, 0xFF))
        commands.append(bytearray([0x13, 0x04, red, green, blue, level]))
        return commands

    def build_effect_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str | int
    ) -> bytearray | None:
        """The bytes to send for an effect change"""
        if isinstance(value, str):
            effect = self.int_if_str_in(
                value, BANLANX3_EFFECTS_RGBW_SOUND, BANLANX3_EFFECT_SOLID
            )
        elif (effect := int(value)) not in BANLANX3_EFFECTS_RGBW_SOUND:
            return None
        if effect == BANLANX3_EFFECT_WHITE:
            channel.set(ATTR_HA_COLOR_MODE, COLOR_MODE_WHITE)
            channel.set(ATTR_HA_BRIGHTNESS, channel.get(ATTR_HA_WHITE, 0xFF))
        elif effect == BANLANX3_EFFECT_SOLID:
            channel.set(ATTR_HA_COLOR_MODE, COLOR_MODE_RGB)
        return bytearray([0x15, 0x01, effect])

    def fetch_effect_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of effect names"""
        if not self.intmic:
            if self.colors == 4:
                return list(BANLANX3_EFFECTS_RGBW.values())
            else:
                return list(BANLANX3_EFFECTS_RGB.values())
        if self.colors == 4:
            return list(BANLANX3_EFFECTS_RGBW_SOUND.values())
        return list(BANLANX3_EFFECTS_RGBW_SOUND.values())

    def build_effect_speed_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect speed change."""
        speed = int(value) & 0xFF
        if not 1 <= speed <= BANLANX3_MAX_EFFECT_SPEED:
            return None
        return bytearray([0x14, 0x01, speed])

    def build_effect_loop_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """The bytes to send for an effect loop change."""
        return self.build_light_mode_command(device, channel, 0x01 if state else 0x00)

    def build_sensitivity_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for a gain/sensitivity change"""
        gain = int(value) & 0xFF
        if not 1 <= gain <= BANLANX3_MAX_SENSITIVITY:
            return None
        return bytearray([0x17, 0x01, gain])

    def build_audio_input_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str
    ) -> bytearray | None:
        """The bytes to send for an input change"""
        if (
            input := self.int_if_str_in(
                str(value), BANLANX3_AUDIO_INPUTS, channel.status.audio_input
            )
        ) is None:
            return None
        return bytearray([0x19, 0x01, input])

    def fetch_audio_input_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light modes"""
        return list(BANLANX3_AUDIO_INPUTS.values())

    def build_chip_order_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str | None = None
    ) -> bytearray | None:
        """Build chip order message(s)"""
        sequence = UNILED_CHIP_ORDER_RGBW if self.colors == 4 else UNILED_CHIP_ORDER_RGB
        if (order := self.chip_order_index(sequence, value)) is not None:
            return bytearray([order & 0xFF, 0x00, 0x00, self.cmd.SET_CHIP_ORDER])
        return None

    def fetch_chip_order_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of chip orders"""
        if self.colors == 4:
            return self.chip_order_list(UNILED_CHIP_ORDER_RGBW)
        return self.chip_order_list(UNILED_CHIP_ORDER_RGB)


##
## Device Signatures
##
SP613E = BanlanX3(
    id=0x613E,
    name="SP613E",
    info="PWM RGB (Music) Controller",
    data=b"\x09\x00",
    colors=3,
    intmic=True,
)

SP614E = BanlanX3(
    id=0x614E,
    name="SP614E",
    info="PWM RGBW (Music) Controller",
    # Fix: Issue #42 - Second byte can be different so only check first byte is '0x0a'
    data=b"\x0a",
    # data=[b"\x0a\x00", b"\x0a\x21"],
    colors=4,
    intmic=True,
)

SP623E = BanlanX3(
    id=0x623E,
    name="SP623E",
    info="Mini PWM RGB Controller",
    data=b"\x0e\x00",
    colors=3,
    intmic=False,
)

SP624E = BanlanX3(
    id=0x624E,
    name="SP624E",
    info="Mini PWM RGBB Controller",
    data=b"\x0f\x00",
    colors=4,
    intmic=False,
)
