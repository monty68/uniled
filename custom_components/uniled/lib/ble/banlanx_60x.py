"""UniLED BLE Devices - SP LED (BanlanX SP60xE)"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Final, cast

from ..const import *  # I know!
from ..channel import UniledChannel
from ..features import (
    UniledAttribute,
    UniledGroup,
    ButtonAttribute,
    SceneAttribute,
    SelectAttribute,
    LightStripFeature,
    SceneLoopFeature,
    EffectTypeFeature,
    EffectSpeedFeature,
    EffectLengthFeature,
    EffectDirectionFeature,
    AudioSensitivityFeature,
    AudioInputFeature,
    ChipOrderFeature,
)
from ..effects import (
    UNILEDEffectType,
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

from ..chips import UNILED_CHIP_ORDER_RGB

import logging

_LOGGER = logging.getLogger(__name__)


##
## Effects
##
@dataclass(frozen=True)
class _FX_STATIC:
    """Effect and Attributes"""

    name: str = UNILEDEffects.SOLID
    colorable: bool = True
    directional: bool = False
    sizeable: bool = False
    speedable: bool = False


@dataclass(frozen=True)
class _FX_DYNAMIC:
    """BanlanX Effect and Attributes"""

    name: str
    colorable: bool = False
    directional: bool = False
    sizeable: bool = False
    speedable: bool = True


@dataclass(frozen=True)
class _FX_SOUND:
    """BanlanX Sound Effect and Attributes"""

    name: str
    colorable: bool = False
    directional: bool = False
    sizeable: bool = False
    speedable: bool = False


BANLANX60X_AUDIO_INPUTS: Final = {
    0x00: UNILED_AUDIO_INPUT_INTMIC,
    0x01: UNILED_AUDIO_INPUT_PLAYER,
    0x02: UNILED_AUDIO_INPUT_AUX_IN,
}

BANLANX60X_MAX_SENSITIVITY = 16
BANLANX60X_MAX_SCENES = 9
BANLANX60X_MAX_EFFECT_SPEED = 30
BANLANX60X_MAX_EFFECT_LENGTH = 96

BANLANX60X_EFFECT_PATTERN: Final = 0x01
BANLANX60X_EFFECT_SOLID: Final = 0x19
BANLANX60X_EFFECT_SOUND: Final = 0x65

BANLANX60X_EFFECTS: Final = {
    BANLANX60X_EFFECT_SOLID: _FX_STATIC(),
    BANLANX60X_EFFECT_PATTERN + 0: _FX_DYNAMIC(UNILEDEffects.RAINBOW, False, True),
    BANLANX60X_EFFECT_PATTERN + 1: _FX_DYNAMIC(UNILEDEffects.RAINBOW_STARS),
    BANLANX60X_EFFECT_PATTERN + 2: _FX_DYNAMIC(UNILEDEffects.STARS_TWINKLE, True),
    BANLANX60X_EFFECT_PATTERN + 3: _FX_DYNAMIC(UNILEDEffects.FIRE, False, True),
    BANLANX60X_EFFECT_PATTERN + 4: _FX_DYNAMIC(UNILEDEffects.STACKING, True, True),
    BANLANX60X_EFFECT_PATTERN + 5: _FX_DYNAMIC(UNILEDEffects.COMET, True, True),
    BANLANX60X_EFFECT_PATTERN + 6: _FX_DYNAMIC(UNILEDEffects.WAVE, True, True),
    BANLANX60X_EFFECT_PATTERN + 7: _FX_DYNAMIC("Chasing", True, True),
    BANLANX60X_EFFECT_PATTERN + 8: _FX_DYNAMIC("Red/Blue/White", False, True),
    BANLANX60X_EFFECT_PATTERN + 9: _FX_DYNAMIC("Green/Yellow/White", False, True),
    BANLANX60X_EFFECT_PATTERN + 10: _FX_DYNAMIC("Red/Green/White", False, True),
    BANLANX60X_EFFECT_PATTERN + 11: _FX_DYNAMIC("Red/Yellow", False, True),
    BANLANX60X_EFFECT_PATTERN + 12: _FX_DYNAMIC("Red/White", False, True),
    BANLANX60X_EFFECT_PATTERN + 13: _FX_DYNAMIC("Green/White", False, True),
    BANLANX60X_EFFECT_PATTERN + 14: _FX_DYNAMIC(UNILEDEffects.GRADIENT),
    BANLANX60X_EFFECT_PATTERN + 15: _FX_DYNAMIC("Wiping", True, True),
    BANLANX60X_EFFECT_PATTERN + 16: _FX_DYNAMIC(UNILEDEffects.BREATH, True),
    BANLANX60X_EFFECT_PATTERN + 17: _FX_DYNAMIC("Full Color Comet Wiping", True),
    BANLANX60X_EFFECT_PATTERN + 18: _FX_DYNAMIC("Comet Wiping", True),
    BANLANX60X_EFFECT_PATTERN + 19: _FX_DYNAMIC("Pixel Dot Wiping", True),
    BANLANX60X_EFFECT_PATTERN + 20: _FX_DYNAMIC("Full Color Meteor Rain", False, True),
    BANLANX60X_EFFECT_PATTERN + 21: _FX_DYNAMIC("Meteor Rain", True, True),
    BANLANX60X_EFFECT_PATTERN + 22: _FX_DYNAMIC("Color Dots", False, True),
    BANLANX60X_EFFECT_PATTERN + 23: _FX_DYNAMIC("Color Block", False, True),
    BANLANX60X_EFFECT_SOUND + 0: _FX_SOUND(UNILEDEffects.SOUND_RHYTHM_SPECTRUM_FULL),
    BANLANX60X_EFFECT_SOUND
    + 1: _FX_SOUND(UNILEDEffects.SOUND_RHYTHM_SPECTRUM_SINGLE, True),
    BANLANX60X_EFFECT_SOUND + 2: _FX_SOUND(UNILEDEffects.SOUND_RHYTHM_STARS_FULL),
    BANLANX60X_EFFECT_SOUND
    + 3: _FX_SOUND(UNILEDEffects.SOUND_RHYTHM_STARS_SINGLE, True),
    BANLANX60X_EFFECT_SOUND
    + 4: _FX_SOUND("Sound - Full Color Beat Injection", False, True),
    BANLANX60X_EFFECT_SOUND + 5: _FX_SOUND("Sound - Beat Injection", True, True),
    BANLANX60X_EFFECT_SOUND + 6: _FX_SOUND(UNILEDEffects.SOUND_ENERGY_GRADIENT),
    BANLANX60X_EFFECT_SOUND + 7: _FX_SOUND(UNILEDEffects.SOUND_ENERGY_SINGLE, True),
    BANLANX60X_EFFECT_SOUND + 8: _FX_SOUND(UNILEDEffects.SOUND_PULSE_GRADIENT),
    BANLANX60X_EFFECT_SOUND + 9: _FX_SOUND(UNILEDEffects.SOUND_PULSE_SINGLE, True),
    BANLANX60X_EFFECT_SOUND + 10: _FX_SOUND("Sound - Full Color Ripple"),
    BANLANX60X_EFFECT_SOUND + 11: _FX_SOUND("Sound - Ripple", True),
    BANLANX60X_EFFECT_SOUND + 12: _FX_SOUND(UNILEDEffects.SOUND_LOVE_AND_PEACE),
    BANLANX60X_EFFECT_SOUND + 13: _FX_SOUND(UNILEDEffects.SOUND_CHRISTMAS),
    BANLANX60X_EFFECT_SOUND + 14: _FX_SOUND(UNILEDEffects.SOUND_HEARTBEAT),
    BANLANX60X_EFFECT_SOUND + 15: _FX_SOUND(UNILEDEffects.SOUND_PARTY),
}

ATTR_UL_SCENE_SAVE_SELECT: Final = "scene_to_save"
ATTR_UL_SCENE_SAVE_BUTTON: Final = "scene_save"


class SceneSaveSelect(SelectAttribute):
    def __init__(self):
        super().__init__(
            ATTR_UL_SCENE_SAVE_SELECT,
            "Save to which scene",
            "mdi:star-settings",
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )


class SceneSaveButton(ButtonAttribute):
    def __init__(self):
        super().__init__(
            ATTR_UL_SCENE_SAVE_BUTTON,
            "Save to Scene",
            "mdi:star-plus",
            group=UniledGroup.CONFIGURATION,
            enabled=False,
        )


##
## BanlanX - SP60xE Protocol Implementation
##
class BanlanX60X(UniledBleModel):
    """BanlanX - SP60xE Protocol Implementation"""

    triggers: int

    def __init__(
        self,
        id: int,
        name: str,
        info: str,
        data: bytes,
        channels: int,
        triggers: int = 0,
    ):
        super().__init__(
            model_num=id,
            model_name=name,
            description=info,
            manufacturer=BANLANX_MANUFACTURER,
            channels=channels,
            ble_manufacturer_id=BANLANX_MANUFACTURER_ID,
            ble_service_uuids=[BANLANX_UUID_FORMAT.format(part) for part in ["ffe0"]],
            ble_write_uuids=[BANLANX_UUID_FORMAT.format(part) for part in ["ffe1"]],
            ble_read_uuids=[],
            ble_notify_uuids=[],
            ble_manufacturer_data=data,
        )
        self.triggers = triggers

    @property
    def master_channel(self):
        """Flag we need a true master channel"""
        return True

    def parse_notifications(
        self,
        device: UniledBleDevice,
        sender: int,
        data: bytearray,
    ) -> bool:
        """Parse notification message(s)"""

        _STATUS_FLAG_1 = 0x53
        _STATUS_FLAG_2 = 0x43
        _HEADER_LENGTH = 5
        _PACKET_NUMBER = 2
        _MESSAGE_LENGTH = 3
        _PAYLOAD_LENGTH = 4

        if (
            (len(data) > _HEADER_LENGTH)
            and data[0] == _STATUS_FLAG_1
            and data[1] == _STATUS_FLAG_2
        ):
            packet_number = data[_PACKET_NUMBER]
            message_length = data[_MESSAGE_LENGTH]
            payload_length = data[_PAYLOAD_LENGTH]

            if packet_number == 1:
                data = device.save_notification_data(data)
                if message_length > payload_length:
                    return False
                data = data[_HEADER_LENGTH:]
            else:
                if (
                    len((last := device.last_notification_data)) == 0
                    or last[_PACKET_NUMBER] != packet_number - 1
                ):
                    raise ParseNotificationError("Out of sequence packet!")

                payload_so_far = last[_PAYLOAD_LENGTH] + data[_PAYLOAD_LENGTH]

                if payload_so_far < last[_MESSAGE_LENGTH]:
                    last[_PACKET_NUMBER] = packet_number
                    last[_PAYLOAD_LENGTH] = payload_so_far
                    device.save_notification_data(last + data[_HEADER_LENGTH:])
                    return False

                if (
                    payload_so_far > message_length
                    or message_length != last[_MESSAGE_LENGTH]
                ):
                    raise ParseNotificationError("Bad packet size!")

                data = last[_HEADER_LENGTH:] + data[_HEADER_LENGTH:]

            # RAW: 53 43 01 18 0f 00 01 02 ff 0a 1e 01 ff 00 00 10 00 01 02 ff
            #      53 43 02 18 09 0a 1e 00 00 ff 00 10 00 00
            #
            # 00 01 02 03 04 05 06 07 08 09 10|11 12 13 14 15 16 17 18 19 20 21|22 23
            # <-- Channel 1                -->|<-- Channel 2                -->|?? AM
            # --------------------------------|--------------------------------|-----
            # 00 01 02 ff 0a 1e 01 ff 00 00 10|00 01 02 ff 0a 1e 00 00 ff 00 10 00 00
            #
            CHANNEL_DATA_SIZE = 11
            if len(data) == message_length:
                _LOGGER.debug("%s: Message: %s", device.name, data.hex())
                master_power = 0
                master_level = 0
                channel_id = 0
                while len(data) > CHANNEL_DATA_SIZE:
                    channel_id += 1
                    fxtype = UNILED_UNKNOWN

                    if (channel := device.channel(channel_id)) is not None:
                        # 0  = Power State
                        # 1  = Effect
                        # 2  = Color Order
                        # 3  = Level (0x00 - 0xFF)
                        # 4  = Effect Speed (0x01 - 0x1E)
                        # 5  = Effect Length (0x01 - 0x96)
                        # 6  = Effect Direction (0x00 = Backwards, 0x01 = Forwards)
                        # 7  = Red Level (0x00 - 0xFF)
                        # 8  = Green Level (0x00 - 0xFF)
                        # 9  = Blue Level (x00 - 0xFF)
                        # 10 = Gain/Sensitivity (0x01 - 0x0F)
                        _LOGGER.debug(
                            "%s: Channel %s: %s",
                            device.name,
                            channel_id,
                            data[:CHANNEL_DATA_SIZE].hex(),
                        )
                        effect = data[1]
                        power = data[0]
                        master_power += power
                        master_level += data[3]

                        channel.status.replace(
                            {
                                ATTR_UL_DEVICE_FORCE_REFRESH: True,
                                ATTR_UL_CHIP_ORDER: self.chip_order_name(
                                    UNILED_CHIP_ORDER_RGB, data[2]
                                ),
                                ATTR_UL_POWER: True if power != 0 else False,
                                ATTR_UL_EFFECT: effect,
                                ATTR_UL_EFFECT_TYPE: UNILED_UNKNOWN,
                                ATTR_UL_EFFECT_NUMBER: effect,
                            }
                        )

                        if (
                            fx := None
                            if effect not in BANLANX60X_EFFECTS
                            else BANLANX60X_EFFECTS[effect]
                        ) is not None:
                            channel.status.set(ATTR_HA_EFFECT, str(fx.name))

                            if effect >= BANLANX60X_EFFECT_SOUND:
                                if power:
                                    channel.status.set(ATTR_UL_SENSITIVITY, data[10])
                                fxtype = UNILEDEffectType.SOUND
                            elif effect != BANLANX60X_EFFECT_SOLID:
                                fxtype = UNILEDEffectType.DYNAMIC
                            else:
                                fxtype = UNILEDEffectType.STATIC
                            channel.status.set(ATTR_UL_EFFECT_TYPE, str(fxtype))

                            if fx.speedable:
                                channel.status.set(ATTR_UL_EFFECT_SPEED, data[4])
                            if fx.sizeable:
                                channel.status.set(ATTR_UL_EFFECT_LENGTH, data[5])
                            if fx.directional:
                                channel.status.set(
                                    ATTR_UL_EFFECT_DIRECTION, bool(data[6])
                                )
                            if fx.colorable:
                                channel.status.set(
                                    ATTR_HA_RGB_COLOR, (data[7], data[8], data[9])
                                )
                                if fxtype != UNILEDEffectType.SOUND:
                                    channel.status.set(ATTR_HA_BRIGHTNESS, data[3])

                        if not channel.features:
                            channel.features = [
                                LightStripFeature(extra=UNILED_CONTROL_ATTRIBUTES),
                                EffectTypeFeature(),
                                EffectSpeedFeature(BANLANX60X_MAX_EFFECT_SPEED),
                                EffectLengthFeature(BANLANX60X_MAX_EFFECT_LENGTH),
                                EffectDirectionFeature(),
                                AudioSensitivityFeature(BANLANX60X_MAX_SENSITIVITY),
                                ChipOrderFeature(),
                            ]

                    # Next Channels Data?
                    #
                    data = data[CHANNEL_DATA_SIZE:]

                # Master Channel
                #
                input = None
                loop = None
                if len(data) > 0:
                    # 0  = Audio Input
                    # 1  = Auto Mode (0x00 = Off, 0x01 = On)
                    _LOGGER.debug("%s: Residual : %s", device.name, data.hex())
                    input = data[0] if self.model_num > 0x601E else None
                    loop = True if data[1] != 0 else False

                last_save_scene = device.master.status.get(
                    ATTR_UL_SCENE_SAVE_SELECT, str(BANLANX60X_MAX_SCENES)
                )

                level = cast(int, master_level / channel_id)

                device.master.status.replace(
                    {
                        ATTR_UL_DEVICE_FORCE_REFRESH: True,
                        ATTR_UL_CHANNELS: channel_id,
                        ATTR_UL_POWER: True if master_power != 0 else False,
                        ATTR_HA_BRIGHTNESS: level,
                        ATTR_UL_SCENE: True,
                        ATTR_UL_SCENE_LOOP: loop,
                        # ATTR_UL_SCENE_SAVE_SELECT: last_save_scene,
                        # ATTR_UL_SCENE_SAVE_BUTTON: False,
                    }
                )

                if input is not None and master_power:
                    audio_input = self.str_if_key_in(input, BANLANX60X_AUDIO_INPUTS)
                    device.master.status.set(ATTR_UL_AUDIO_INPUT, audio_input)

                if not device.master.features:
                    device.master.features = [
                        LightStripFeature(extra=[ATTR_UL_SCENE_LOOP]),
                        SceneLoopFeature(),
                        # SceneSaveSelect(),
                        # SceneSaveButton(),
                    ]

                    for b in range(BANLANX60X_MAX_SCENES):
                        device.master.features.append(
                            SceneAttribute(b, UNILED_CONTROL_ATTRIBUTES)
                        )

                    if input is not None:
                        device.master.features.append(AudioInputFeature())
                return True
        raise ParseNotificationError("Unknown/Invalid Packet!")

    def build_on_connect(self, device: UniledBleDevice) -> list[bytearray] | None:
        """Build on connect message(s)"""
        return None

    def build_state_query(self, device: UniledBleDevice) -> bytearray:
        """Build a state query message"""
        return bytearray([0xAA, 0x2F, 0x00])

    def build_onoff_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: int
    ) -> bytearray:
        """Build power on or off message"""
        cnum = device.channels - 1 if not channel.number else channel.number - 1
        return bytearray([0xAA, 0x22, 0x02, cnum, 0x01 if state else 0x00])

    def build_brightness_command(
        self, device: UniledBleDevice, channel: UniledChannel, level: int
    ) -> bytearray:
        """The bytes to send for a brightness level change"""
        cnum = device.channels - 1 if not channel.number else channel.number - 1
        return bytearray([0xAA, 0x25, 0x02, cnum, level])

    def build_rgb_color_command(
        self, device: UniledBleDevice, channel: UniledChannel, rgb: tuple[int, int, int]
    ) -> bytearray | None:
        """The bytes to send for a color level change"""
        red, green, blue = rgb
        cnum = device.channels - 1 if not channel.number else channel.number - 1
        return bytearray([0xAA, 0x29, 0x05, cnum, red, green, blue, 0xFF])

    def build_effect_command(
        self,
        device: UniledBleDevice,
        channel: UniledChannel,
        value: Any,
    ) -> bytearray | None:
        """The bytes to send for an effect change"""
        if not channel.number:
            return None
        cnum = device.channels - 1 if not channel.number else channel.number - 1

        if isinstance(value, str):
            effect = self.int_if_str_in(
                value, BANLANX60X_EFFECTS, BANLANX60X_EFFECT_SOLID
            )
        elif (effect := int(value)) not in BANLANX60X_EFFECTS:
            return None
        return bytearray([0xAA, 0x23, 0x02, cnum, effect])

    def fetch_effect_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list:
        """Return list of effect names"""
        effects = list()
        if channel.number:
            for fx in BANLANX60X_EFFECTS:
                effects.append(str(BANLANX60X_EFFECTS[fx].name))
        return effects

    def build_effect_speed_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect speed change."""
        speed = int(value) & 0xFF
        if not 1 <= speed <= BANLANX60X_MAX_EFFECT_SPEED:
            return None
        cnum = device.channels - 1 if not channel.number else channel.number - 1
        return bytearray([0xAA, 0x26, 0x02, cnum, speed])

    def build_effect_length_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect length change."""
        length = int(value) & 0xFF
        if not 1 <= length <= BANLANX60X_MAX_EFFECT_LENGTH:
            return None
        cnum = device.channels - 1 if not channel.number else channel.number - 1
        return bytearray([0xAA, 0x27, 0x02, cnum, length])

    def build_effect_direction_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """The bytes to send for an effect direction change."""
        cnum = device.channels - 1 if not channel.number else channel.number - 1
        return bytearray([0xAA, 0x2A, 0x02, cnum, 0x01 if state else 0x00])

    def build_audio_input_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str
    ) -> bytearray | None:
        """The bytes to send for an input change"""
        input = self.int_if_str_in(value, BANLANX60X_AUDIO_INPUTS, 0x00)
        cnum = device.channels - 1 if not channel.number else channel.number - 1
        return bytearray([0xAA, 0x28, 0x02, cnum, input])  ## ????? 0x28 ?????

    def fetch_audio_input_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of light modes"""
        return list(BANLANX60X_AUDIO_INPUTS.values())

    def build_sensitivity_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for a gain/sensitivity change"""
        gain = int(value) & 0xFF
        if not 1 <= gain <= BANLANX60X_MAX_SENSITIVITY:
            return None
        cnum = device.channels - 1 if not channel.number else channel.number - 1
        return bytearray([0xAA, 0x2B, 0x02, cnum, gain])

    def build_scene_command(
        self, device: UniledBleDevice, channel: UniledChannel, scene: int
    ) -> bytearray:
        """Build scene message(s)"""
        return bytearray([0xAA, 0x2E, 0x01, scene])

    def build_scene_loop_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray:
        """Build scene loop message(s)"""
        return bytearray([0xAA, 0x30, 0x01, 0x01 if state else 0x00])

    def build_scene_save_command(
        self, device: UniledBleDevice, channel: UniledChannel, scene: int
    ) -> bytearray:
        """Build scene save message(s)"""

    def fetch_scene_to_save_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> bytearray:
        """Return list of scene numbers"""
        scenes = list()
        for b in range(BANLANX60X_MAX_SCENES):
            scenes.append(str(b + 1))
        return scenes

    def build_chip_order_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str | None = None
    ) -> list[bytearray]:
        """Build chip order message(s)"""
        cnum = device.channels - 1 if not channel.number else channel.number - 1
        if (
            order := self.chip_order_index(UNILED_CHIP_ORDER_RGB, str(value))
        ) is not None:
            return bytearray([0xAA, 0x24, 0x02, cnum, order])
        return None

    def fetch_chip_order_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of chip orders"""
        return self.chip_order_list(UNILED_CHIP_ORDER_RGB)


##
## Device Signatures
##
SP601E = BanlanX60X(
    id=0x601E,
    name="SP601E",
    info="2xSPI RGB (Music) Controller",
    data=b"\x01\x02",
    channels=2,
)

SP602E = BanlanX60X(
    id=0x602E,
    name="SP602E",
    info="4xSPI RGB (Music) Controller",
    data=b"\x02\x02",
    channels=4,
    triggers=4,
)

SP608E = BanlanX60X(
    id=0x608E,
    name="SP608E",
    info="8xSPI RGB (Music) Controller",
    data=b"\x08\x02",
    channels=8,
    triggers=4,
)
