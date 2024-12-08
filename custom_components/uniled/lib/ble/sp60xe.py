"""UniLED BLE Devices - SP LED (BanlanX SP60xE)"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Final, cast

from ..attributes import (
    ButtonAttribute,
    SceneAttribute,
    SelectAttribute,
    UniledAttribute,
    UniledGroup,
)
from ..channel import UniledChannel
from ..chips import UNILED_CHIP_ORDER_RGB
from ..const import *  # I know!
from ..effects import UNILEDEffects, UNILEDEffectType
from ..features import (
    AudioInputFeature,
    AudioSensitivityFeature,
    ChipOrderFeature,
    EffectDirectionFeature,
    EffectLengthFeature,
    EffectSpeedFeature,
    EffectTypeFeature,
    LightStripFeature,
    SceneLoopFeature,
)
from .device import (
    BANLANX_MANUFACTURER,
    BANLANX_MANUFACTURER_ID,
    UUID_BASE_FORMAT as BANLANX_UUID_FORMAT,
    ParseNotificationError,
    UniledBleDevice,
    UniledBleModel,
)
from .sp601e import (
    ATTR_UL_SCENE_SAVE_BUTTON,
    ATTR_UL_SCENE_SAVE_SELECT,
    BANLANX601_AUDIO_INPUTS as BANLANX60X_AUDIO_INPUTS,
    BANLANX601_EFFECT_PATTERN as BANLANX60X_EFFECT_PATTERN,
    BANLANX601_EFFECT_SOLID as BANLANX60X_EFFECT_SOLID,
    BANLANX601_EFFECT_SOUND as BANLANX60X_EFFECT_SOUND,
    BANLANX601_EFFECTS as BANLANX60X_EFFECTS,
    SceneSaveButton,
    SceneSaveSelect,
)

_LOGGER = logging.getLogger(__name__)

BANLANX60X_MAX_SENSITIVITY = 16
BANLANX60X_MAX_SCENES = 9
BANLANX60X_MAX_EFFECT_SPEED = 10
BANLANX60X_MAX_EFFECT_LENGTH = 240


##
## BanlanX - SP60xE Protocol Implementation
##
class SP60xE(UniledBleModel):
    """BanlanX - SP60xE Protocol Implementation."""

    triggers: int

    def __init__(
        self,
        code: int,
        name: str,
        info: str,
        data: bytes,
        channels: int,
        triggers: int,
    ):
        super().__init__(
            model_code=code,
            model_name=name,
            model_info=info,
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

        _STATUS_FLAG_1 = 0x36
        _STATUS_FLAG_2 = 0x38
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

            CHANNEL_DATA_SIZE = 11

            if len(data) == message_length:
                # _LOGGER.debug("%s: Message: %s", device.name, data.hex())
                master_power = 0
                master_level = 0
                channel_id = 0
                while len(data) > CHANNEL_DATA_SIZE and channel_id < self.channels:
                    channel_id += 1
                    fxtype = UNILED_UNKNOWN

                    if (channel := device.channel(channel_id)) is not None:
                        # 0  = Power State
                        # 1  = Effect
                        # 2  = Color Order
                        # 3  = Level (0x00 - 0xFF)
                        # 4  = Effect Speed (0x01 - 0x0A)
                        # 5  = Effect Length MSB (0x01 - 0xF0)
                        # 6  = Effect Length LSB (0x01 - 0xF0)
                        # 7  = Effect Direction (0x00 = Backwards, 0x01 = Forwards)
                        # 8  = Red Level (0x00 - 0xFF)
                        # 9  = Green Level (0x00 - 0xFF)
                        # 10 = Blue Level (x00 - 0xFF)
                        #
                        # 00 01 02 03 04 05 06 07 08 09 10
                        # --------------------------------
                        # 00 01 02 ff 0a 00 14 88 ff 00 00
                        #
                        _LOGGER.debug(
                            "%s: Channel %s: %s",
                            device.name,
                            channel_id,
                            data[:CHANNEL_DATA_SIZE].hex(),
                        )
                        power = data[0]
                        effect = data[1]
                        order = data[2]
                        level = data[3]
                        speed = data[4]
                        length = int.from_bytes(data[5:7], byteorder="big")
                        direction = data[7]
                        rgb = (data[8], data[9], data[10])
                        master_power += power

                        channel.status.replace(
                            {
                                ATTR_UL_DEVICE_FORCE_REFRESH: True,
                                ATTR_UL_CHIP_ORDER: self.chip_order_name(
                                    UNILED_CHIP_ORDER_RGB, order
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
                                fxtype = UNILEDEffectType.SOUND
                            elif effect != BANLANX60X_EFFECT_SOLID:
                                fxtype = UNILEDEffectType.DYNAMIC
                            else:
                                fxtype = UNILEDEffectType.STATIC
                            channel.status.set(ATTR_UL_EFFECT_TYPE, str(fxtype))

                            if fx.speedable:
                                channel.status.set(ATTR_UL_EFFECT_SPEED, speed)
                            if fx.sizeable:
                                channel.status.set(ATTR_UL_EFFECT_LENGTH, length)
                            if fx.directional:
                                channel.status.set(
                                    ATTR_UL_EFFECT_DIRECTION, bool(direction)
                                )
                            if fx.colorable:
                                channel.status.set(ATTR_HA_RGB_COLOR, rgb)

                            if fxtype != UNILEDEffectType.SOUND:
                                channel.status.set(ATTR_HA_BRIGHTNESS, level)
                                master_level += level
                            else:
                                master_level += 255

                        if not channel.features:
                            channel.features = [
                                LightStripFeature(extra=UNILED_CONTROL_ATTRIBUTES),
                                EffectTypeFeature(),
                                EffectSpeedFeature(BANLANX60X_MAX_EFFECT_SPEED),
                                EffectLengthFeature(BANLANX60X_MAX_EFFECT_LENGTH),
                                EffectDirectionFeature(),
                                ChipOrderFeature(),
                            ]

                    # Next Channels Data?
                    #
                    data = data[CHANNEL_DATA_SIZE:]

                # Master Channel
                #
                last_save_scene = device.master.status.get(
                    ATTR_UL_SCENE_SAVE_SELECT, str(BANLANX60X_MAX_SCENES)
                )

                device.master.status.replace(
                    {
                        ATTR_UL_DEVICE_FORCE_REFRESH: True,
                        ATTR_UL_CHANNELS: channel_id,
                        ATTR_UL_POWER: True if master_power != 0 else False,
                        ATTR_HA_BRIGHTNESS: cast(int, master_level / channel_id),
                        ATTR_UL_SCENE: BANLANX60X_MAX_SCENES,
                        # ATTR_UL_SCENE_SAVE_SELECT: last_save_scene,
                        # ATTR_UL_SCENE_SAVE_BUTTON: False,
                    }
                )

                if (
                    gain := data.pop(0) if len(data) >= 1 else None
                ) is not None and master_power:
                    device.master.status.set(ATTR_UL_SENSITIVITY, gain)

                if timers := data.pop(0) if len(data) >= 1 else 0:
                    TIMER_DATA_SIZE = 7
                    timer_id = 0
                    while len(data) >= TIMER_DATA_SIZE and timer_id < timers:
                        timer_id += 1
                        timer_data = data[:TIMER_DATA_SIZE]
                        data = data[TIMER_DATA_SIZE:]
                        _LOGGER.debug(
                            "%s: Timer %s: %s",
                            device.name,
                            timer_id,
                            timer_data.hex(),
                        )

                TRIGGER_DATA_SIZE = 13
                trigger_id = 0
                while len(data) >= TRIGGER_DATA_SIZE and trigger_id < self.triggers:
                    trigger_id += 1
                    trigger_data = data[:TRIGGER_DATA_SIZE]
                    data = data[TRIGGER_DATA_SIZE:]
                    _LOGGER.debug(
                        "%s: Trigger %s: %s",
                        device.name,
                        trigger_id,
                        trigger_data.hex(),
                    )

                if (loop := data.pop(0) if len(data) >= 1 else None) is not None:
                    device.master.status.set(ATTR_UL_SCENE_LOOP, loop)

                input = None
                if input is not None and master_power:
                    audio_input = self.str_if_key_in(input, BANLANX60X_AUDIO_INPUTS)
                    device.master.status.set(ATTR_UL_AUDIO_INPUT, audio_input)

                if not device.master.features:
                    device.master.features = [
                        LightStripFeature(extra=UNILED_CONTROL_ATTRIBUTES),
                        SceneLoopFeature(),
                        # SceneSaveSelect(),
                        # SceneSaveButton(),
                    ]

                    for b in range(BANLANX60X_MAX_SCENES):
                        device.master.features.append(
                            SceneAttribute(b, UNILED_CONTROL_ATTRIBUTES)
                        )

                    if gain is not None:
                        device.master.features.append(
                            AudioSensitivityFeature(BANLANX60X_MAX_SENSITIVITY)
                        )

                    if input is not None:
                        device.master.features.append(AudioInputFeature())

                return True
        raise ParseNotificationError("Unknown/Invalid Packet!")

    # 88 95 0a 01 01 04 00 1e 01 ff 00 00 ff
    # 88 98 0a 01 03 05 00 1e 01 ff 00 00 ff
    # 88 96 0a ff 03 05 00 1e 01 ff 00 00 ff
    # 88 97 00 - ??

    # Enable Triggers??
    #
    # 88 99 04 00 01 01 01
    # 88 99 04 01 01 02 01
    # 88 99 04 02 01 04 01
    # 88 99 04 03 01 08 01
    # 88 99 04 01 01 0f 03
    #

    def build_on_connect(self, device: UniledBleDevice) -> list[bytearray] | None:
        """Build on connect message(s)"""
        return None

    def build_state_query(self, device: UniledBleDevice) -> bytearray:
        """Build a state query message"""
        return bytearray([0x88, 0x8F, 0x00])

    def build_onoff_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: int
    ) -> bytearray:
        """Build power on or off message"""
        cnum = 0xFF if not channel.number else 1 << (channel.number - 1)
        return bytearray([0x88, 0x82, 0x02, cnum, 0x01 if state else 0x00])

    def build_brightness_command(
        self, device: UniledBleDevice, channel: UniledChannel, level: int
    ) -> bytearray:
        """The bytes to send for a brightness level change"""
        cnum = 0xFF if not channel.number else 1 << (channel.number - 1)
        return bytearray([0x88, 0x85, 0x02, cnum, level])

    def build_rgb_color_command(
        self, device: UniledBleDevice, channel: UniledChannel, rgb: tuple[int, int, int]
    ) -> bytearray | None:
        """The bytes to send for a color level change"""
        red, green, blue = rgb
        cnum = 0xFF if not channel.number else 1 << (channel.number - 1)
        return bytearray([0x88, 0x89, 0x05, cnum, red, green, blue, 0xFF])

    def build_effect_command(
        self,
        device: UniledBleDevice,
        channel: UniledChannel,
        value: Any,
    ) -> bytearray | None:
        """The bytes to send for an effect change"""
        if not channel.number:
            return None
        if isinstance(value, str):
            effect = BANLANX60X_EFFECT_SOLID
            for id, fx in BANLANX60X_EFFECTS.items():
                if fx.name == value:
                    effect = id
                    break
        elif (effect := int(value)) not in BANLANX60X_EFFECTS:
            return None
        cnum = 0xFF if not channel.number else 1 << (channel.number - 1)
        return bytearray([0x88, 0x83, 0x02, cnum, effect])

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
        cnum = 0xFF if not channel.number else 1 << (channel.number - 1)
        return bytearray([0x88, 0x86, 0x02, cnum, speed])

    def build_effect_length_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: int
    ) -> bytearray | None:
        """The bytes to send for an effect length change."""
        # 88 87 03 01 00 f0 = Length?
        if not 1 <= value <= BANLANX60X_MAX_EFFECT_LENGTH:
            return None
        length = int(value).to_bytes(2, byteorder="big")
        cnum = 0xFF if not channel.number else 1 << (channel.number - 1)
        return bytearray([0x88, 0x87, 0x03, cnum, length[0], length[1]])

    def build_effect_direction_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray | None:
        """The bytes to send for an effect direction change."""
        # 88 8a 02 01 00 = Direction?
        cnum = 0xFF if not channel.number else 1 << (channel.number - 1)
        return bytearray([0x88, 0x8A, 0x02, cnum, 0x01 if state else 0x00])

    def build_audio_input_command(
        self, device: UniledBleDevice, channel: UniledChannel, value: str
    ) -> bytearray | None:
        """The bytes to send for an input change"""
        input = self.int_if_str_in(value, BANLANX60X_AUDIO_INPUTS, 0x00)
        cnum = 0xFF if not channel.number else 1 << (channel.number - 1)
        return bytearray([0x88, 0x88, 0x02, cnum, input])  ## ????? 0x88 ?????

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
        cnum = 0xFF if not channel.number else 1 << (channel.number - 1)
        return bytearray([0x88, 0x8B, 0x02, cnum, gain])

    def build_scene_command(
        self, device: UniledBleDevice, channel: UniledChannel, scene: int
    ) -> bytearray:
        """Build scene message(s)"""
        return bytearray([0x88, 0x8E, 0x01, scene])

    def build_scene_loop_command(
        self, device: UniledBleDevice, channel: UniledChannel, state: bool
    ) -> bytearray:
        """Build scene loop message(s)"""
        return bytearray([0x88, 0x90, 0x01, 0x01 if state else 0x00])

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
        cnum = 0xFF if not channel.number else 1 << (channel.number - 1)
        if (
            order := self.chip_order_index(UNILED_CHIP_ORDER_RGB, str(value))
        ) is not None:
            return bytearray([0x88, 0x84, 0x02, cnum, order])
        return None

    def fetch_chip_order_list(
        self, device: UniledBleDevice, channel: UniledChannel
    ) -> list | None:
        """Return list of chip orders"""
        return self.chip_order_list(UNILED_CHIP_ORDER_RGB)


##
## Device Signatures
##
SP602E = SP60xE(
    code=0x02,
    name="SP602E",
    info="4xSPI RGB (Music) Controller",
    data=b"\x02",
    channels=4,
    triggers=4,
)

SP608E = SP60xE(
    code=0x05,
    name="SP608E",
    info="8xSPI RGB (Music) Controller",
    data=b"\x05",
    channels=8,
    triggers=4,
)
