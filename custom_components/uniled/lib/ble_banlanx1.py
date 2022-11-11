"""UniLED BLE Devices - SP601E - SP LED (BanlanX)"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .artifacts import (
    UNILEDModelType,
    UNILEDColorOrder,
    UNILEDInputs,
    UNILEDEffectType,
    UNILEDEffects,
)
from .states import (
    UNILED_STATE_SETUP,
    UNILED_STATE_INPUT,
    UNILED_STATE_AUTO,
    UNILEDSetup,
    UNILEDStatus,
)
from .classes import UNILEDDevice, UNILEDChannel
from .ble_model import UNILEDBLEModel, BASE_UUID_FORMAT as BANLANX1_UUID_FORMAT

import logging

_LOGGER = logging.getLogger(__name__)

BANLANX1_MANUFACTURER_ID: Final = 20563
BANLANX1_MANUFACTURER: Final = "SPLED (BanlanX)"

BANLANX1_TYPE_SOLID: Final = 0x25
BANLANX1_TYPE_SOUND: Final = 0x65

BANLANX1_LED_ORDERS: Final = {
    0x00: UNILEDColorOrder.RGB,
    0x01: UNILEDColorOrder.RBG,
    0x02: UNILEDColorOrder.GRB,
    0x03: UNILEDColorOrder.GBR,
    0x04: UNILEDColorOrder.BRG,
    0x05: UNILEDColorOrder.BGR,
}

BANLANX1_INPUTS: Final = {
    0x00: UNILEDInputs.INTMIC,
}

BANLANX1_EFFECTS: Final = {
    0x19: UNILEDEffects.SOLID,
    0x01: UNILEDEffects.RAINBOW,  # Directional
    0x02: UNILEDEffects.RAINBOW_STARS,
    0x03: "Twinkle Stars",  # Colorable
    0x04: UNILEDEffects.FIRE,  # Directional
    0x05: UNILEDEffects.STACKING,  # Colorable & Directional
    0x06: UNILEDEffects.COMET,  # Colorable & Directional
    0x07: UNILEDEffects.WAVE,  # Colorable & Directional
    0x08: "Chasing",  # Colorable & Directional
    0x09: "Red/Blue/White",  # Directional
    0x0A: "Green/Yellow/White",  # Directional
    0x0B: "Red/Green/White",  # Directional
    0x0C: "Red/Yellow",  # Directional
    0x0D: "Red/White",  # Directional
    0x0E: "Green/White",  # Directional
    0x0F: UNILEDEffects.GRADIENT,
    0x10: "Wiping",  # Colorable & Directional
    0x11: UNILEDEffects.BREATH,  # Colorable
    0x12: "Full Color Comet Wiping",
    0x13: "Comet Wiping",  # Colorable
    0x14: "Pixel Dot Wiping",  # Colorable
    0x15: "Full Color Meteor Rain",  # Directional
    0x16: "Meteor Rain",  # Colorable & Directional
    0x17: "Color Dots",  # Directional
    0x18: "Color Block",  # Directional
    0x65: UNILEDEffects.SOUND_RHYTHM_SPECTRUM_FULL,
    0x66: UNILEDEffects.SOUND_RHYTHM_SPECTRUM_SINGLE,  # Colorable
    0x67: UNILEDEffects.SOUND_RHYTHM_STARS_FULL,
    0x68: UNILEDEffects.SOUND_RHYTHM_STARS_SINGLE,  # Colorable
    0x69: "Full Color Beat Injection",  # Directional
    0x6A: "Beat Injection",  # Colorable & Directional
    0x6B: UNILEDEffects.SOUND_ENERGY_GRADIENT,
    0x6C: UNILEDEffects.SOUND_ENERGY_SINGLE,  # Colorable
    0x6D: UNILEDEffects.SOUND_PULSE_GRADIENT,
    0x6E: UNILEDEffects.SOUND_PULSE_SINGLE,  # Colorable
    0x6F: "Full Color Ripple",
    0x70: "Ripple",  # Colorable
    0x71: UNILEDEffects.SOUND_LOVE_AND_PEACE,
    0x72: UNILEDEffects.SOUND_CHRISTMAS,
    0x73: UNILEDEffects.SOUND_HEARTBEAT,
    0x74: UNILEDEffects.SOUND_PARTY,
}


@dataclass(frozen=True)
class _BANLANX1(UNILEDBLEModel):
    """BanlanX v2 Protocol Implementation"""

    ##
    ## Device Control
    ##
    def construct_connect_message(self) -> bytearray | None:
        """The bytes to send when first connecting."""
        #return self.construct_message(bytearray([0xAA, 0x2A, 0x02, 0x00, 0x01]))
        return None

    def construct_status_query(self, device: UNILEDDevice) -> bytearray:
        """The bytes to send for a state query."""
        return self.construct_message(bytearray([0xAA, 0x2F, 0x00]))

    async def async_decode_notifications(
        self, device: UNILEDDevice, sender: int, data: bytearray
    ) -> UNILEDStatus | None:
        """Handle notification responses."""

        if data[0] == 0x53 and data[1] == 0x43:
            if data[2] == 0x01 and data[3] != 0x17:
                # Do nothing (for now) on the first status packet
                device.save_notification_data(data)
                return None

            if data[2] == 0x02:
                #
                # Combine this data (minus first 5 bytes) with the previous
                # notification data (also minus its first 5 bytes).
                #
                data = device.save_notification_data(
                    device.last_notification_data[5:] + data[5:]
                )

                # This leaves a byte array with the following layout:
                #
                # -----------------------------------------------------------------------
                # 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23
                # -----------------------------------------------------------------------
                # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
                # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Auto Mode (0x00 = Off, 0x01 = On)
                # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Unknown
                # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Channel 2 Gain/Sensitivity (0x01 - 0x0F)
                # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Channel 2 Blue Level (x00 - 0xFF)
                # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Channel 2 Green Level (0x00 - 0xFF)
                # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Channel 2 Red Level (0x00 - 0xFF)
                # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Channel 2 Effect Direction? (0x00 = Backwards, 0x01 = Forwards)
                # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Channel 2 Effect Length (0x01 - 0x96)
                # |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  Channel 2 Effect Speed (0x01 - 0x1E)
                # |  |  |  |  |  |  |  |  |  |  |  |  |  |  Channel 2 Level (0x00 - 0xFF)
                # |  |  |  |  |  |  |  |  |  |  |  |  |  Channel 2 Color Order
                # |  |  |  |  |  |  |  |  |  |  |  |  Channel 2 Effect
                # |  |  |  |  |  |  |  |  |  |  |  Channel 2 Power State
                # |  |  |  |  |  |  |  |  |  |  Channel 1 Gain/Sensitivity (0x01 - 0x0F)
                # |  |  |  |  |  |  |  |  |  Channel 1 Blue Level (x00 - 0xFF)
                # |  |  |  |  |  |  |  |  Channel 1 Green Level (0x00 - 0xFF)
                # |  |  |  |  |  |  |  Channel 1 Red Level (0x00 - 0xFF)
                # |  |  |  |  |  |  Channel 1 Effect Direction? (0x00 = Backwards, 0x01 = Forwards)
                # |  |  |  |  |  Channel 1 Effect Length (0x01 - 0x96)
                # |  |  |  |  Channel 1 Effect Speed (0x01 - 0x1E)
                # |  |  |  Channel 1 Level (0x00 - 0xFF)
                # |  |  Channel 1 Color Order
                # |  Channel 1 Effect
                # Channel 1 Power State
                #
                if data[3] == 0x19:
                    return None

            elif data[2] == 0x03:
                #
                # Combine this data (minus first 5 bytes) with the previous
                # notification data saved as part of 0x02 packet.
                #
                data = device.save_notification_data(
                    device.last_notification_data + data[5:]
                )
            else:
                return None

            device.channels[1].set_status(
                UNILEDStatus(
                    power=data[0] == 0x01,
                    fxtype=data[1],
                    effect=data[1],
                    level=data[3],
                    speed=data[4],
                    length=data[5],
                    direction=data[6],
                    rgb=(data[7], data[8], data[9]),
                    gain=data[10],
                    extra={UNILED_STATE_SETUP: UNILEDSetup(order=data[2])},
                )
            )

            device.channels[2].set_status(
                UNILEDStatus(
                    power=data[11] == 0x01,
                    fxtype=data[12],
                    effect=data[12],
                    level=data[14],
                    speed=data[15],
                    length=data[16],
                    direction=data[17],
                    rgb=(data[18], data[19], data[20]),
                    gain=data[21],
                    extra={UNILED_STATE_SETUP: UNILEDSetup(order=data[13])},
                )
            )

            return UNILEDStatus(
                power=data[0] + data[11],
                level=(data[3] + data[14]) / 2,
                extra={
                    "unknown": data[22],
                    UNILED_STATE_AUTO: data[23],
                    UNILED_STATE_INPUT: 0x00,
                },
            )

        # Getting here means a notification has not changed the state
        #
        return None

    ##
    ## Channel Control
    ##
    def construct_power_change(
        self, channel: UNILEDChannel, turn_on: int
    ) -> bytearray | None:
        """The bytes to send for a power state change"""
        cnum = 0x02 if not channel.number else channel.number - 1
        return self.construct_message(
            bytearray([0xAA, 0x22, 0x02, cnum, 0x01 if turn_on else 0x00])
        )

    def construct_effect_change(
        self, channel: UNILEDChannel, effect: int
    ) -> bytearray | None:
        """The bytes to send for an effect change."""
        cnum = 0x02 if not channel.number else channel.number - 1
        return self.construct_message(bytearray([0xAA, 0x23, 0x02, cnum, effect]))

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

    def construct_level_change(
        self, channel: UNILEDChannel, level: int
    ) -> bytearray | None:
        """The bytes to send for a color level change."""
        cnum = 0x02 if not channel.number else channel.number - 1
        return self.construct_message(bytearray([0xAA, 0x25, 0x02, cnum, level]))

    def construct_color_change(
        self, channel: UNILEDChannel, red: int, green: int, blue: int, level: int
    ) -> bytearray | None:
        """The bytes to send for a color change."""
        cnum = 0x02 if not channel.number else channel.number - 1
        return self.construct_message(
            bytearray([0xAA, 0x29, 0x05, cnum, red, green, blue, 0xFF])
        )

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
    def listof_channel_effects(self, channel: UNILEDChannel) -> list | None:
        """List of available channel effects"""
        return list(BANLANX1_EFFECTS.values())

    def codeof_channel_effect(
        self, channel: UNILEDChannel, name: str | None = None
    ) -> int | None:
        """Code of named channel effect"""
        if name is None:
            return channel.status.effect
        return [k for k in BANLANX1_EFFECTS.items() if k[1] == name][0][0]

    def nameof_channel_effect(
        self, channel: UNILEDChannel, effect: int | None = None
    ) -> str | None:
        """Name an effect."""
        if effect is None:
            effect = channel.status.effect
        if effect in BANLANX1_EFFECTS:
            return BANLANX1_EFFECTS[effect]
        return None

    def nameof_channel_effect_type(
        self, channel: UNILEDChannel, fxtype: int | None = None
    ) -> str | None:
        """Name an effects type."""
        if fxtype is None:
            fxtype = channel.status.fxtype
        if fxtype == BANLANX1_TYPE_SOLID:
            return UNILEDEffectType.STATIC
        if fxtype >= BANLANX1_TYPE_SOUND:
            return UNILEDEffectType.SOUND
        return UNILEDEffectType.PATTERN

    def rangeof_channel_effect_speed(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect speed (min,max,step)."""
        return (1, 10, 1)

    def rangeof_channel_effect_length(
        self, channel: UNILEDChannel
    ) -> tuple(int, int, int) | None:
        """Range of effect length (min,max,step)."""
        return (1, 150, 1)


##
## SP601E
##
SP601E = _BANLANX1(
    model_num=0x601E,
    model_name="SP601E",
    model_type=UNILEDModelType.STRIP,
    description="BLE Dual Channel RGB (Music) Controller",
    manufacturer=BANLANX1_MANUFACTURER,
    manufacturer_id=BANLANX1_MANUFACTURER_ID,
    manufacturer_data=b"\x01\x02\x01\xb6",
    resolve_protocol=False,
    channels=2,
    extra_data={},
    service_uuids=[BANLANX1_UUID_FORMAT.format(part) for part in ["ffe0", "ffb0"]],
    write_uuids=[BANLANX1_UUID_FORMAT.format(part) for part in ["ffe1"]],
    read_uuids=[],
)
