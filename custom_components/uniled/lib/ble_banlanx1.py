"""UniLED BLE Devices - SP601E - SP LED (BanlanX v1)"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, cast
from enum import IntEnum

from .artifacts import (
    UNKNOWN,
    UNILEDModelType,
    # UNILEDChipOrder,
    UNILEDMode,
    UNILEDInput,
    UNILEDEffectType,
    UNILEDEffects,
)
from .states import UNILEDStatus
from .classes import UNILEDDevice, UNILEDChannel
from .ble_model import UNILEDBLEModel, BASE_UUID_FORMAT as BANLANX1_UUID_FORMAT

import logging

_LOGGER = logging.getLogger(__name__)

BANLANX1_MANUFACTURER_ID: Final = 20563
BANLANX1_MANUFACTURER: Final = "SPLED (BanlanX)"
BANLANX1_MODEL_NUMBER_SP601E: Final = 0x601E
BANLANX1_MODEL_NAME_SP601E: Final = "SP601E"
BANLANX1_LOCAL_NAME_SP601E: Final = BANLANX1_MODEL_NAME_SP601E

BANLANX1_MODE_OFF: Final = 0xFF
BANLANX1_SCENE_NONE: Final = 0xFF
BANLANX1_EFFECT_PATTERN: Final = 0x01
BANLANX1_EFFECT_SOLID: Final = 0x19
BANLANX1_EFFECT_SOUND: Final = 0x65

BANLANX1_INPUTS: Final = {
    0x00: UNILEDInput.INTMIC,
}

BANLANX1_MODES: Final = {
    0x00: UNILEDMode.MANUAL,
    0x01: UNILEDMode.AUTO_SCENE,
    BANLANX1_MODE_OFF: UNILEDMode.OFF,
}


@dataclass(frozen=True)
class _FXType(IntEnum):
    STATIC = 0x00
    PATTERN = 0x01
    SOUND = 0x02


BANLANX1_EFFECT_TYPES: dict(int, str) = {
    _FXType.STATIC.value: UNILEDEffectType.STATIC,
    _FXType.PATTERN.value: UNILEDEffectType.PATTERN,
    _FXType.SOUND.value: UNILEDEffectType.SOUND,
}

BANLANX1_EFFECTS: Final = {
    BANLANX1_EFFECT_SOLID: UNILEDEffects.SOLID,
    BANLANX1_EFFECT_PATTERN + 0: UNILEDEffects.RAINBOW,  # Directional
    BANLANX1_EFFECT_PATTERN + 1: UNILEDEffects.RAINBOW_STARS,
    BANLANX1_EFFECT_PATTERN + 2: UNILEDEffects.STARS_TWINKLE,  # Colorable
    BANLANX1_EFFECT_PATTERN + 3: UNILEDEffects.FIRE,  # Directional
    BANLANX1_EFFECT_PATTERN + 4: UNILEDEffects.STACKING,  # Colorable & Directional
    BANLANX1_EFFECT_PATTERN + 5: UNILEDEffects.COMET,  # Colorable & Directional
    BANLANX1_EFFECT_PATTERN + 6: UNILEDEffects.WAVE,  # Colorable & Directional
    BANLANX1_EFFECT_PATTERN + 7: "Chasing",  # Colorable & Directional
    BANLANX1_EFFECT_PATTERN + 8: "Red/Blue/White",  # Directional
    BANLANX1_EFFECT_PATTERN + 9: "Green/Yellow/White",  # Directional
    BANLANX1_EFFECT_PATTERN + 10: "Red/Green/White",  # Directional
    BANLANX1_EFFECT_PATTERN + 11: "Red/Yellow",  # Directional
    BANLANX1_EFFECT_PATTERN + 12: "Red/White",  # Directional
    BANLANX1_EFFECT_PATTERN + 13: "Green/White",  # Directional
    BANLANX1_EFFECT_PATTERN + 14: UNILEDEffects.GRADIENT,
    BANLANX1_EFFECT_PATTERN + 15: "Wiping",  # Colorable & Directional
    BANLANX1_EFFECT_PATTERN + 16: UNILEDEffects.BREATH,  # Colorable
    BANLANX1_EFFECT_PATTERN + 17: "Full Color Comet Wiping",
    BANLANX1_EFFECT_PATTERN + 18: "Comet Wiping",  # Colorable
    BANLANX1_EFFECT_PATTERN + 19: "Pixel Dot Wiping",  # Colorable
    BANLANX1_EFFECT_PATTERN + 20: "Full Color Meteor Rain",  # Directional
    BANLANX1_EFFECT_PATTERN + 21: "Meteor Rain",  # Colorable & Directional
    BANLANX1_EFFECT_PATTERN + 22: "Color Dots",  # Directional
    BANLANX1_EFFECT_PATTERN + 23: "Color Block",  # Directional
    BANLANX1_EFFECT_SOUND + 0: UNILEDEffects.SOUND_RHYTHM_SPECTRUM_FULL,
    BANLANX1_EFFECT_SOUND + 1: UNILEDEffects.SOUND_RHYTHM_SPECTRUM_SINGLE,  # Colorable
    BANLANX1_EFFECT_SOUND + 2: UNILEDEffects.SOUND_RHYTHM_STARS_FULL,
    BANLANX1_EFFECT_SOUND + 3: UNILEDEffects.SOUND_RHYTHM_STARS_SINGLE,  # Colorable
    BANLANX1_EFFECT_SOUND + 4: "Sound - Full Color Beat Injection",  # Directional
    BANLANX1_EFFECT_SOUND + 5: "Sound - Beat Injection",  # Colorable & Directional
    BANLANX1_EFFECT_SOUND + 6: UNILEDEffects.SOUND_ENERGY_GRADIENT,
    BANLANX1_EFFECT_SOUND + 7: UNILEDEffects.SOUND_ENERGY_SINGLE,  # Colorable
    BANLANX1_EFFECT_SOUND + 8: UNILEDEffects.SOUND_PULSE_GRADIENT,
    BANLANX1_EFFECT_SOUND + 9: UNILEDEffects.SOUND_PULSE_SINGLE,  # Colorable
    BANLANX1_EFFECT_SOUND + 10: "Sound - Full Color Ripple",
    BANLANX1_EFFECT_SOUND + 11: "Sound - Ripple",  # Colorable
    BANLANX1_EFFECT_SOUND + 12: UNILEDEffects.SOUND_LOVE_AND_PEACE,
    BANLANX1_EFFECT_SOUND + 13: UNILEDEffects.SOUND_CHRISTMAS,
    BANLANX1_EFFECT_SOUND + 14: UNILEDEffects.SOUND_HEARTBEAT,
    BANLANX1_EFFECT_SOUND + 15: UNILEDEffects.SOUND_PARTY,
}

BANLANX1_SCENES: Final = {
    BANLANX1_SCENE_NONE: "None",
    0x00: "Scene 1",
    0x01: "Scene 2",
    0x02: "Scene 3",
    0x03: "Scene 4",
    0x04: "Scene 5",
    0x05: "Scene 6",
    0x06: "Scene 7",
    0x07: "Scene 8",
    0x08: "Scene 9",
}

_STATUS_FLAG_1 = 0x53
_STATUS_FLAG_2 = 0x43
_HEADER_LENGTH = 5
_PACKET_NUMBER = 2
_MESSAGE_LENGTH = 3
_PAYLOAD_LENGTH = 4


@dataclass(frozen=True)
class _BANLANX1(UNILEDBLEModel):
    """BanlanX v1 Protocol Implementation"""

    ##
    ## Device Control
    ##
    def construct_status_query(self, device: UNILEDDevice) -> bytearray:
        """The bytes to send for a state query."""
        return self.construct_message(bytearray([0xAA, 0x2F, 0x00]))

    def async_decode_notifications(
        self, device: UNILEDDevice, sender: int, data: bytearray
    ) -> UNILEDStatus | None:
        """Handle notification responses."""

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
                    _LOGGER.debug(
                        "%s: Packet 1 - payload size: %s, message length: %s",
                        device.name,
                        payload_length,
                        message_length,
                    )
                    return None
                data = data[_HEADER_LENGTH:]
            else:

                if (
                    len((last := device.last_notification_data)) == 0
                    or last[_PACKET_NUMBER] != packet_number - 1
                ):
                    _LOGGER.debug("%s: Skip out of sequence Packet!", device.name)
                    device.save_notification_data(())
                    return None

                payload_so_far = last[_PAYLOAD_LENGTH] + data[_PAYLOAD_LENGTH]

                _LOGGER.debug(
                    "%s: Packet %s - payload size: %s, payload so far: %s, message length: %s (%s)",
                    device.name,
                    packet_number,
                    payload_length,
                    payload_so_far,
                    message_length,
                    last[_MESSAGE_LENGTH],
                )

                if payload_so_far < last[_MESSAGE_LENGTH]:
                    last[_PACKET_NUMBER] = packet_number
                    last[_PAYLOAD_LENGTH] = payload_so_far
                    device.save_notification_data(last + data[_HEADER_LENGTH:])
                    return None

                if (
                    payload_so_far > message_length
                    or message_length != last[_MESSAGE_LENGTH]
                ):
                    _LOGGER.debug("%s: Bad Packet!", device.name)
                    last[_MESSAGE_LENGTH] = 0
                    return None

                data = last[_HEADER_LENGTH:] + data[_HEADER_LENGTH:]

            if len(data) == message_length:
                #
                # 0  = Channel 1 Power State
                # 1  = Channel 1 Effect
                # 2  = Channel 1 Color Order
                # 3  = Channel 1 Level (0x00 - 0xFF)
                # 4  = Channel 1 Effect Speed (0x01 - 0x1E)
                # 5  = Channel 1 Effect Length (0x01 - 0x96)
                # 6  = Channel 1 Effect Direction? (0x00 = Backwards, 0x01 = Forwards)
                # 7  = Channel 1 Red Level (0x00 - 0xFF)
                # 8  = Channel 1 Green Level (0x00 - 0xFF)
                # 9  = Channel 1 Blue Level (x00 - 0xFF)
                # 10 = Channel 1 Gain/Sensitivity (0x01 - 0x0F)
                # 11 = Channel 2 Power State
                # 12 = Channel 2 Effect
                # 13 = Channel 2 Color Order
                # 14 = Channel 2 Level (0x00 - 0xFF)
                # 15 = Channel 2 Effect Speed (0x01 - 0x1E)
                # 16 = Channel 2 Effect Length (0x01 - 0x96)
                # 17 = Channel 2 Effect Direction? (0x00 = Backwards, 0x01 = Forwards)
                # 18 = Channel 2 Red Level (0x00 - 0xFF)
                # 19 = Channel 2 Green Level (0x00 - 0xFF)
                # 20 = Channel 2 Blue Level (x00 - 0xFF)
                # 21 = Channel 2 Gain/Sensitivity (0x01 - 0x0F)
                # 22 = Unknown
                # 23 = Auto Mode (0x00 = Off, 0x01 = On)
                #
                _LOGGER.debug("%s: Good Status Message: %s", device.name, data.hex())

                device.channels[1].set_status(
                    UNILEDStatus(
                        power=data[0] == 0x01,
                        effect=data[1],
                        fxtype=self.codeof_channel_effect_type(
                            device.channels[1], data[1]
                        ),
                        level=data[3],
                        speed=data[4],
                        length=data[5],
                        direction=data[6],
                        rgb=(data[7], data[8], data[9]),
                        gain=data[10],
                        chip_order=data[2],
                    )
                )

                device.channels[2].set_status(
                    UNILEDStatus(
                        power=data[11] == 0x01,
                        effect=data[12],
                        fxtype=self.codeof_channel_effect_type(
                            device.channels[2], data[12]
                        ),
                        level=data[14],
                        speed=data[15],
                        length=data[16],
                        direction=data[17],
                        rgb=(data[18], data[19], data[20]),
                        gain=data[21],
                        chip_order=data[13],
                    )
                )

                master_power = data[0] + data[11]
                mode = data[message_length - 1]
                return UNILEDStatus(
                    power=master_power,
                    mode=mode if master_power else BANLANX1_MODE_OFF,
                    effect=BANLANX1_SCENE_NONE,
                    level=cast(int, (data[3] + data[14]) / 2),
                    extra={
                        "unknown": data[22] if message_length == 24 else None,
                    },
                )

        _LOGGER.debug("%s: Unknown/Invalid Packet!", device.name)
        device.save_notification_data(())
        return None

    ##
    ## Channel Control
    ##
    def construct_power_change(
        self, channel: UNILEDChannel, turn_on: int
    ) -> list[bytearray] | None:
        """The bytes to send for a power state change"""
        cnum = 0x02 if not channel.number else channel.number - 1
        return [
            self.construct_message(
                bytearray([0xAA, 0x22, 0x02, cnum, 0x01 if turn_on else 0x00])
            ),
            self.construct_status_query(channel.device),
        ]

    def construct_mode_change(
        self, channel: UNILEDChannel, mode: int
    ) -> list[bytearray] | None:
        """The bytes to send for a mode change."""
        if mode == BANLANX1_MODE_OFF:
            return self.construct_power_change(channel.device.master, False)
        return [
            self.construct_message(bytearray([0xAA, 0x30, 0x01, mode])),
            self.construct_status_query(channel.device),
        ]

    def construct_level_change(
        self, channel: UNILEDChannel, level: int
    ) -> list[bytearray] | None:
        """The bytes to send for a color level change."""
        cnum = 0x02 if not channel.number else channel.number - 1
        return [
            self.construct_message(bytearray([0xAA, 0x25, 0x02, cnum, level])),
            self.construct_status_query(channel.device),
        ]

    def construct_color_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int, white: int | None
    ) -> bytearray | None:
        """The bytes to send for a color change."""
        cnum = 0x02 if not channel.number else channel.number - 1
        return self.construct_message(
            bytearray([0xAA, 0x29, 0x05, cnum, red, green, blue, 0xFF])
        )

    def construct_effect_change(
        self, channel: UNILEDChannel, effect: int
    ) -> bytearray | None:
        """The bytes to send for an effect change."""
        if channel.number:
            cnum = 0x02 if not channel.number else channel.number - 1
            return self.construct_message(bytearray([0xAA, 0x23, 0x02, cnum, effect]))
        # Master Channel, change to a scene (0-8)
        return [
            self.construct_message(bytearray([0xAA, 0x2E, 0x01, effect])),
            self.construct_status_query(channel.device),
        ]

    def construct_effect_speed_change(
        self, channel: UNILEDChannel, speed: int
    ) -> bytearray | None:
        """The bytes to send for an effect speed change."""
        cnum = 0x02 if not channel.number else channel.number - 1
        return self.construct_message(bytearray([0xAA, 0x26, 0x02, cnum, speed]))

    def construct_effect_length_change(
        self, channel: UNILEDChannel, length: int
    ) -> bytearray | None:
        """The bytes to send for an efect length change."""
        cnum = 0x02 if not channel.number else channel.number - 1
        return self.construct_message(bytearray([0xAA, 0x27, 0x02, cnum, length]))

    def construct_effect_direction_change(
        self, channel: UNILEDChannel, direction: int
    ) -> bytearray | None:
        """The bytes to send for an efect direction change."""
        cnum = 0x02 if not channel.number else channel.number - 1
        return self.construct_message(bytearray([0xAA, 0x2A, 0x02, cnum, direction]))

    def construct_input_gain_change(
        self, channel: UNILEDChannel, gain: int
    ) -> list[bytearray] | None:
        """The bytes to send for a gain/sensitivity change"""
        cnum = 0x02 if not channel.number else channel.number - 1
        return self.construct_message(bytearray([0xAA, 0x2B, 0x02, cnum, gain]))

    ##
    ## Device Informational
    ##
    def nameof_device_input_type(
        self, device: UNILEDDevice, audio_input: int | None = None
    ) -> str | None:
        """Name a device input type."""
        if audio_input is None:
            audio_input = device.input
        if audio_input in BANLANX1_INPUTS:
            return BANLANX1_INPUTS[audio_input]
        return None

    def listof_device_inputs(self, device: UNILEDDevice) -> list | None:
        """List of available device inputs."""
        return list(BANLANX1_INPUTS.values())

    ##
    ## Channel Informational
    ##
    def listof_channel_modes(self, channel: UNILEDChannel) -> list | None:
        """List of available channel modes"""
        return list(BANLANX1_MODES.values())

    def codeof_channel_mode(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named mode"""
        if name is None:
            return channel.status.mode
        return [k for k in BANLANX1_MODES.items() if k[1] == name][0][0]

    def nameof_channel_mode(
        self, channel: UNILEDChannel, mode: int | None = None
    ) -> str | None:
        """Name a mode."""
        if mode is None:
            mode = channel.status.mode
        if mode in BANLANX1_MODES:
            return BANLANX1_MODES[mode]
        return None

    def listof_channel_effects(self, channel: UNILEDChannel) -> list | None:
        """List of available channel effects"""
        if channel.number:
            return list(BANLANX1_EFFECTS.values())
        return list(BANLANX1_SCENES.values())

    def codeof_channel_effect(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named channel effect"""
        if name is None:
            return channel.status.effect
        if channel.number:
            return [k for k in BANLANX1_EFFECTS.items() if k[1] == name][0][0]
        return [k for k in BANLANX1_SCENES.items() if k[1] == name][0][0]

    def nameof_channel_effect(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> str | None:
        """Name an effect."""
        if effect is None:
            effect = channel.status.effect
        if not channel.number:
            if effect in BANLANX1_SCENES:
                return BANLANX1_SCENES[effect]
        elif effect in BANLANX1_EFFECTS:
            return BANLANX1_EFFECTS[effect]
        return None

    def codeof_channel_effect_type(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> int | None:
        """Code of channel effect type from effect code"""
        if not channel.number:
            return None
        if effect is None:
            effect = channel.status.effect
        if effect < BANLANX1_EFFECT_SOLID:
            return _FXType.PATTERN.value
        elif effect >= BANLANX1_EFFECT_SOUND:
            return _FXType.SOUND.value
        return _FXType.STATIC.value

    def nameof_channel_effect_type(
        self, channel: UNILEDChannel, fxtype: int | None = None
    ) -> str | None:
        """Name an effects type."""
        if not channel.number:
            return None
        if fxtype is None:
            fxtype = channel.status.fxtype
        if fxtype in BANLANX1_EFFECT_TYPES:
            return BANLANX1_EFFECT_TYPES[fxtype]
        return f"{UNKNOWN} ({fxtype})"

    def rangeof_channel_effect_speed(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        if channel.number:
            return (1, 10, 1)
        return None

    def rangeof_channel_effect_length(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect length (min,max,step)."""
        if channel.number:
            return (1, 150, 1)
        return None

    def rangeof_channel_input_gain(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of input gain (min,max,step)."""
        if channel.number:
            return (1, 16, 1)
        return None


##
## SP601E
##
SP601E = _BANLANX1(
    model_num=BANLANX1_MODEL_NUMBER_SP601E,
    model_name=BANLANX1_MODEL_NAME_SP601E,
    model_type=UNILEDModelType.STRIP,
    description="BLE Dual Channel RGB (Music) Controller",
    manufacturer=BANLANX1_MANUFACTURER,
    manufacturer_id=BANLANX1_MANUFACTURER_ID,
    manufacturer_data=b"\x01\x02",
    resolve_protocol=False,
    channels=2,
    needs_on=True,
    sends_status_on_commands=False,
    local_names=[BANLANX1_LOCAL_NAME_SP601E],
    service_uuids=[BANLANX1_UUID_FORMAT.format(part) for part in ["ffe0", "ffb0"]],
    write_uuids=[BANLANX1_UUID_FORMAT.format(part) for part in ["ffe1"]],
    read_uuids=[],
)
