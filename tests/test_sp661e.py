"""Offline tests for the SP661E model (no Home Assistant, no Bluetooth).
Run from the repo root:  python -m unittest tests.test_sp661e -v
"""

import os
import sys
import unittest

sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "custom_components", "uniled")
)

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from lib.const import *  # noqa
from lib.ble.banlanx_661 import SP661E
from lib.ble.device import UniledBleDevice, ParseNotificationError
from lib.ble.banlanx_601 import SP601E
from lib.effects import UNILED_EFFECT_TYPE_STATIC

# Real status notification from the controller (solid mode, 100%, power on)
STATUS = bytes.fromhex(
    "53 02 00 01 00 62 01 0a 00 1c 01 00 06 56 31 2e 30 2e 30 32 63 09 01 03 03 00 00 07 80 00 20 01"
    " 60 10 07 a1 00 00 03 00 2a 01 01 00 01 00 78 02 01 00 ff ff ff 00 00 ff 00 03 00 00 10 00 ff 00"
    " 00 ff 00 01 03 01 ff 00 00 01 00 ff 00 01 00 00 ff 01 00 0c 00 0c 01 0a 00 00 00 00 00 00 00 00"
    " ff 00 0d 00 03 01 00 00"
)


class FakeStatus(dict):
    def replace(self, d):
        self.clear()
        self.update(d)


class FakeMaster:
    def __init__(self):
        self.features = []
        self.status = FakeStatus()

    def set(self, k, v):
        self.status[k] = v


class FakeDevice:
    name = "LMB"

    def __init__(self):
        self.master = FakeMaster()


class FakeStatusView:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class FakeChannel:
    def __init__(self, mode):
        self.status = FakeStatusView(light_mode_number=mode)


def with_bytes(base: bytes, **offs):
    b = bytearray(base)
    for k, v in offs.items():
        b[int(k[1:])] = v
    return bytes(b)


class ParseTests(unittest.TestCase):
    def test_packet_length_is_consistent(self):
        self.assertEqual(len(STATUS), STATUS[5] + 6)

    def test_parse_solid_full(self):
        dev = FakeDevice()
        self.assertTrue(SP661E.parse_notifications(dev, 0, bytearray(STATUS)))
        st = dev.master.status
        self.assertTrue(st[ATTR_UL_POWER])
        self.assertEqual(st[ATTR_HA_BRIGHTNESS], 0xFF)
        self.assertEqual(st[ATTR_UL_LIGHT_MODE_NUMBER], 2)
        self.assertEqual(st[ATTR_HA_EFFECT], "Solid Color")
        self.assertEqual(st[ATTR_UL_EFFECT_TYPE], UNILED_EFFECT_TYPE_STATIC)
        self.assertEqual(len(dev.master.features), 3)

    def test_parse_power_off_and_brightness(self):
        dev = FakeDevice()
        pkt = with_bytes(STATUS, o44=0, o51=0x33)
        SP661E.parse_notifications(dev, 0, bytearray(pkt))
        self.assertFalse(dev.master.status[ATTR_UL_POWER])
        self.assertEqual(dev.master.status[ATTR_HA_BRIGHTNESS], 0x33)

    def test_parse_dynamic_uses_fx_level_and_speed(self):
        dev = FakeDevice()
        pkt = with_bytes(STATUS, o47=4, o48=2, o50=0x80, o51=0x1A, o57=8)
        SP661E.parse_notifications(dev, 0, bytearray(pkt))
        st = dev.master.status
        self.assertEqual(st[ATTR_HA_EFFECT], "Strobe")
        self.assertEqual(st[ATTR_HA_BRIGHTNESS], 0x80)
        self.assertEqual(st[ATTR_UL_EFFECT_SPEED], 8)

    def test_rejects_bad_packets(self):
        dev = FakeDevice()
        with self.assertRaises(ParseNotificationError):
            SP661E.parse_notifications(dev, 0, bytearray(STATUS[:-1]))
        with self.assertRaises(ParseNotificationError):
            SP661E.parse_notifications(dev, 0, bytearray(b"\x00" + STATUS[1:]))


class CommandTests(unittest.TestCase):
    def test_query(self):
        self.assertEqual(
            SP661E.build_state_query(None).hex(" "), "53 02 00 01 00 01 01"
        )

    def test_power(self):
        self.assertEqual(
            SP661E.build_onoff_command(None, None, True).hex(" "),
            "53 50 00 01 00 02 01 01",
        )
        self.assertEqual(
            SP661E.build_onoff_command(None, None, False).hex(" "),
            "53 50 00 01 00 02 01 00",
        )

    def test_brightness_solid_and_fx(self):
        self.assertEqual(
            SP661E.build_brightness_command(None, FakeChannel(2), 255).hex(" "),
            "53 51 00 01 00 03 01 80 ff",
        )
        self.assertEqual(
            SP661E.build_brightness_command(None, FakeChannel(4), 0x40).hex(" "),
            "53 51 00 01 00 03 01 00 40",
        )

    def test_effects(self):
        exp = {
            "Solid Color": "53 53 00 01 00 03 01 02 01",
            "Triangle": "53 53 00 01 00 03 01 04 01",
            "Strobe": "53 53 00 01 00 03 01 04 02",
            "Heart Beat": "53 53 00 01 00 03 01 04 03",
        }
        for name, frame in exp.items():
            self.assertEqual(
                SP661E.build_effect_command(None, None, name).hex(" "), frame
            )
        self.assertIsNone(SP661E.build_effect_command(None, None, "Nope"))

    def test_speed(self):
        self.assertEqual(
            SP661E.build_effect_speed_command(None, None, 8).hex(" "),
            "53 54 00 01 00 02 01 08",
        )
        self.assertIsNone(SP661E.build_effect_speed_command(None, None, 0x80))


class MatchTests(unittest.TestCase):
    @staticmethod
    def adv(data: bytes):
        return AdvertisementData(
            local_name="LMB",
            manufacturer_data={0x5053: data},
            service_data={},
            service_uuids=["0000e0ff-0000-1000-8000-00805f9b34fb"],
            tx_power=None,
            rssi=-60,
            platform_data=(),
        )

    @staticmethod
    def dev():
        return BLEDevice(
            "AA:BB:CC:DD:D3:EA",
            "LMB",
            {},
        )

    def test_sp661e_wins_over_sp601e(self):
        m = UniledBleDevice.match_known_device(
            self.dev(), self.adv(bytes.fromhex("01007a5c123062d3ea000000"))
        )
        self.assertIs(m, SP661E)

    def test_other_01_prefix_still_sp601e(self):
        m = UniledBleDevice.match_known_device(
            self.dev(), self.adv(bytes.fromhex("01027a5c123062d3ea000000"))
        )
        self.assertIs(m, SP601E)


class RestoreTests(unittest.TestCase):
    def test_model_found_by_stored_name(self):
        """A saved config entry only stores the model name; it must resolve to SP661E."""
        self.assertIs(UniledBleDevice.match_model_name("SP661E"), SP661E)
        self.assertIs(UniledBleDevice.match_model_name("SP601E"), SP601E)

    def test_unknown_name_is_none(self):
        self.assertIsNone(UniledBleDevice.match_model_name("LMB"))


class NamingTests(unittest.TestCase):
    def test_named_after_model_not_advertised_name(self):
        self.assertTrue(SP661E.use_model_name)
        # advertised name may be junk such as "3" or "LMB"
        for junk in ("3", "LMB", ""):
            self.assertEqual(
                UniledBleDevice.human_readable_name(
                    SP661E.model_name, junk, "AA:BB:CC:DD:D3:EA"
                ),
                "SP661E (D3EA)",
            )

    def test_other_models_keep_advertised_name(self):
        self.assertFalse(getattr(SP601E, "use_model_name", False))


class WriteModeTests(unittest.TestCase):
    def test_sp661e_writes_without_response(self):
        self.assertFalse(SP661E.write_with_response)

    def test_other_models_keep_default(self):
        self.assertTrue(getattr(SP601E, "write_with_response", True))


class DeviceConstructionTests(unittest.IsolatedAsyncioTestCase):
    """Regression: building the device must not touch attributes before __init__ sets them."""

    @staticmethod
    def make(ble_name, model_name):
        ble = BLEDevice("AA:BB:CC:DD:D3:EA", ble_name, {})
        adv = MatchTests.adv(bytes.fromhex("01007a5c123062d3ea000000"))
        return UniledBleDevice({}, ble, adv, model_name)

    async def test_name_with_junk_advertised_name(self):
        dev = self.make("3", "SP661E")
        self.assertIs(dev.model, SP661E)
        self.assertEqual(dev.name, "SP661E (D3EA)")

    async def test_model_resolved_from_advertisement(self):
        dev = self.make("3", None)
        self.assertIs(dev.model, SP661E)
        self.assertEqual(dev.name, "SP661E (D3EA)")

    async def test_other_model_keeps_advertised_name(self):
        ble = BLEDevice("AA:BB:CC:DD:D3:EA", "SP601E-test", {})
        adv = MatchTests.adv(bytes.fromhex("01027a5c123062d3ea000000"))
        dev = UniledBleDevice({}, ble, adv, None)
        self.assertEqual(dev.name, "SP601E-test")

    def test_del_survives_failed_init(self):
        from lib.device import UniledDevice

        broken = UniledDevice.__new__(UniledDevice)  # __init__ never ran
        broken._ble_device = None
        UniledDevice.__del__(broken)  # must not raise


if __name__ == "__main__":
    unittest.main()
