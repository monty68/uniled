"""UniLED BLE Device Handler."""
from __future__ import annotations

import asyncio
import async_timeout

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.backends.service import BleakGATTCharacteristic, BleakGATTServiceCollection
from bleak.exc import BleakDBusError
from bleak_retry_connector import (
    BLEAK_RETRY_EXCEPTIONS as BLEAK_EXCEPTIONS,
    BleakClientWithServiceCache,
    BleakError,
    BleakNotFoundError,
    BleakConnectionError,
    establish_connection,
)

from .ble_model import UNILEDBLEModel
from .ble_retry import (
    retry_bluetooth_connection_error,
    BLEAK_DISCONNECT_DELAY,
    BLEAK_BACKOFF_TIME,
)
from .classes import UNILEDDevice
from .models_db import UNILED_TRANSPORT_BLE, UNILED_BLE_MODELS

import logging

_LOGGER = logging.getLogger(__name__)

BLE_MULTI_COMMAND_SETTLE_DELAY = 0.3
BLE_NOTFICATION_TIMEOUT = 2.0


class CharacteristicMissingError(Exception):
    """Raised when a characteristic is missing."""


class ChannelMissingError(Exception):
    """Raised when a channel is missing."""


##
## UniLed BLE Device Handler
##
class UNILEDBLE(UNILEDDevice):
    """UniLED BLE Device Class"""

    def __init__(
        self,
        ble_device: BLEDevice,
        advertisement_data: AdvertisementData | None = None,
        model_name: str | None = None,
    ) -> None:
        """Init the UniLED BLE Model"""
        self._ble_device = ble_device
        self._advertisement_data = advertisement_data
        self._connect_lock: asyncio.Lock = asyncio.Lock()
        self._operation_lock = asyncio.Lock()
        self._read_char: BleakGATTCharacteristic | None = None
        self._write_char: BleakGATTCharacteristic | None = None
        self._disconnect_timer: asyncio.TimerHandle | None = None
        self._client: BleakClientWithServiceCache | None = None
        self._expected_disconnect = False
        self.loop = asyncio.get_running_loop()
        self._notification_event = asyncio.Event()
        super().__init__()

        _LOGGER.debug("%s: Init BLE Device (Model: %s)", ble_device.name, model_name)

        if model_name is not None:
            self._set_model(self._lookup_model(model_name))

        if not self._model and (
            model := self.match_known_device(ble_device, advertisement_data)
        ):
            if not model.resolve_protocol:
                self._set_model(model)
            else:
                _LOGGER.warning("%s: Needs model resolving", ble_device.name)

    def __del__(self):
        """Destroy the UniLED BLE Model"""
        _LOGGER.debug("Device Destroyed")

    @property
    def transport(self) -> str:
        """Return the device transport."""
        return UNILED_TRANSPORT_BLE

    @property
    def name(self) -> str:
        """Get the name of the device."""
        return self._ble_device.name or self._ble_device.address

    @property
    def address(self) -> str:
        """Return the address of the device."""
        return self._ble_device.address

    @property
    def rssi(self) -> int | None:
        """Get the rssi of the device."""
        if self._advertisement_data:
            return self._advertisement_data.rssi
        return self._ble_device.rssi

    @property
    def available(self) -> bool:
        """Return if the UniLED device available."""
        if (self._model and self._client) and self._client.is_connected:
            return True
        return False

    async def update(self) -> bool:
        """Update the UniLED BLE device."""
        _LOGGER.debug("%s: Update", self.name)
        self._notification_event.clear()
        if not await self.send_command(self.model.construct_status_query(self)):
            return False

        # Wait for actual response!
        _LOGGER.debug("%s: Awaiting status notification", self.name)
        async with self._operation_lock:
            try:
                async with async_timeout.timeout(BLE_NOTFICATION_TIMEOUT):
                    await self._notification_event.wait()
                    return True
            except asyncio.TimeoutError:
                _LOGGER.debug("%s: Timeout waiting for status notification", self.name)
        return False

    async def stop(self) -> None:
        """Stop the UniLED BLE device."""
        _LOGGER.debug("%s: Stop", self.name)
        async with self._operation_lock:
            try:
                await self._execute_disconnect()
            finally:
                pass

    async def resolve_model(self, do_disconnect: bool = True) -> UNILEDBLEModel | None:
        """Resolve device model"""
        if self._model is not None:
            return self._model
        for model in UNILED_BLE_MODELS:
            if not model.resolve_protocol:
                continue
            for uuid in model.service_uuids:
                if uuid in self._advertisement_data.service_uuids:
                    _LOGGER.debug(
                        "%s: Resolve model = %s?", self.name, model.model_name
                    )
                    self._model = model
                    if await self.update():
                        if do_disconnect:
                            await self.stop()
                        return self._model
        await self.stop()
        return None

    def set_device_and_advertisement(
        self, ble_device: BLEDevice, advertisement: AdvertisementData
    ) -> None:
        """Update the ble device/advertisement."""
        self._ble_device = ble_device
        self._advertisement_data = advertisement or self._advertisement_data
        ##_LOGGER.debug(
        ##    "%s: Update device (RSSI: %s) %s",
        ##    ble_device.name,
        ##    ble_device.rssi,
        ##    advertisement,
        ##)

    def _lookup_model(self, model_name: str) -> UNILEDBLEModel | None:
        """Lookup model from name"""
        for model in UNILED_BLE_MODELS:
            if model.model_name == model_name:
                return model
        return None

    def _set_model(self, model: UNILEDBLEModel) -> None:
        """Set the device model"""
        if self._model is None and model is not None:
            _LOGGER.debug("%s: Set model %s", self.name, model.model_name)
            self._model = model
            self._create_channels()

    def _notification_handler(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle notification responses."""
        _LOGGER.debug(
            "%s: Handle:%s, notification data: %s", self.name, sender.handle, data.hex()
        )
        if self._model:
            self._notification_event.clear()
            new_master_state = self._model.async_decode_notifications(
                self, sender.handle, data
            )
            if new_master_state is not None:
                self.master.set_status(new_master_state)
                self._last_notification_data = ()
                self._notification_event.set()

    async def send_command(
        self, commands: list[bytes] | bytes, retry: int | None = None
    ) -> bool:
        """Send command to device and read response."""
        try:
            await self._ensure_connected()
        except BleakConnectionError as ex:
            _LOGGER.debug(
                "%s: connection failed: %s; RSSI: %s",
                self.name,
                ex,
                self.rssi,
                exc_info=True,
            )
            return False

        if commands:
            if not isinstance(commands, list):
                commands = [commands]
            await self._send_command_while_connected(commands, retry)
            return True
        return False

    async def _ensure_connected(self) -> None:
        """Ensure connection to device is established."""
        if self._connect_lock.locked():
            _LOGGER.debug(
                "%s: Connection already in progress, waiting for it to complete; RSSI: %s",
                self.name,
                self.rssi,
            )
        if self._client and self._client.is_connected:
            self._reset_disconnect_timer()
            return
        async with self._connect_lock:
            # Check again while holding the lock
            if self._client and self._client.is_connected:
                self._reset_disconnect_timer()
                return
            _LOGGER.debug("%s: Connecting; RSSI: %s", self.name, self.rssi)
            client = await establish_connection(
                BleakClientWithServiceCache,
                self._ble_device,
                self.name,
                self._disconnected,
                use_services_cache=True,
                ble_device_callback=lambda: self._ble_device,
            )

            _LOGGER.debug("%s: Connected", self.name)
            resolved = self._resolve_characteristics(client.services)
            if not resolved:
                # Try to handle services failing to load
                await asyncio.sleep(BLEAK_BACKOFF_TIME)
                # services = await client.get_services()
                services = client.services
                resolved = self._resolve_characteristics(services)

            self._client = client
            self._reset_disconnect_timer()

            if client and self._read_char:
                _LOGGER.debug("%s: Subscribe to notifications", self.name)
                self._last_notification_data = ()
                await client.start_notify(self._read_char, self._notification_handler)

        if (client and self._model) and (
            on_connect := self._model.construct_connect_message(self)
        ) is not None:
            # Send any "on connection" message(s)
            await self.send_command(on_connect)
            await asyncio.sleep(BLE_MULTI_COMMAND_SETTLE_DELAY)

    async def _send_command_while_connected(
        self, commands: list[bytes], retry: int | None = None
    ) -> None:
        """Send command to device and read response."""
        _LOGGER.debug("%s: Sending %d command(s)", self.name, len(commands))
        if self._operation_lock.locked():
            _LOGGER.debug(
                "%s: Operation already in progress, waiting for it to complete",
                self.name,
            )
        async with self._operation_lock:
            try:
                await self._send_command_locked(commands)
                return
            except BleakNotFoundError:
                _LOGGER.error(
                    "%s: device not found, no longer in range, or poor RSSI: %s",
                    self.name,
                    self.rssi,
                    exc_info=True,
                )
                raise
            except CharacteristicMissingError as ex:
                _LOGGER.debug(
                    "%s: characteristic missing: %s; RSSI: %s",
                    self.name,
                    ex,
                    self.rssi,
                    exc_info=True,
                )
                raise
            except BLEAK_EXCEPTIONS:
                _LOGGER.debug("%s: communication failed", self.name, exc_info=True)
                raise

        raise RuntimeError("Unreachable")

    @retry_bluetooth_connection_error
    async def _send_command_locked(self, commands: list[bytes]) -> None:
        """Send command to device and read response."""
        try:
            await self._execute_command_locked(commands)
        except BleakDBusError as ex:
            # Disconnect so we can reset state and try again
            _LOGGER.debug(
                "%s: RSSI: %s; Backing off %ss; Disconnecting due to error: %s",
                self.name,
                self.rssi,
                BLEAK_BACKOFF_TIME,
                ex,
            )
            await asyncio.sleep(BLEAK_BACKOFF_TIME)
            await self._execute_disconnect()
            raise
        except BleakError as ex:
            # Disconnect so we can reset state and try again
            _LOGGER.debug(
                "%s: RSSI: %s; Disconnecting due to error: %s", self.name, self.rssi, ex
            )
            await self._execute_disconnect()
            raise

    async def _execute_command_locked(self, commands: list[bytes]) -> None:
        """Execute command and read response."""
        # assert self._client is not None  # nosec
        if not self._client:
            raise BleakNotFoundError("No Bleak Client!")
        if not self._write_char:
            raise CharacteristicMissingError("Write characteristic missing")
        if not self._read_char:
            raise CharacteristicMissingError("Read characteristic missing")
        to_send = len(commands)
        for command in commands:
            _LOGGER.debug("%s: Sending command: %s ", self.name, command.hex())
            await self._client.write_gatt_char(self._write_char, command, False)
            if to_send > 1:
                await asyncio.sleep(BLE_MULTI_COMMAND_SETTLE_DELAY)

    def _reset_disconnect_timer(self) -> None:
        """Reset disconnect timer."""
        if self._disconnect_timer:
            self._disconnect_timer.cancel()
        self._expected_disconnect = False
        self._disconnect_timer = self.loop.call_later(
            BLEAK_DISCONNECT_DELAY, self._disconnect
        )

    def _disconnected(self, client: BleakClientWithServiceCache) -> None:
        """Disconnected callback."""
        self._last_notification_data = ()
        _LOGGER.debug(
            "%s: Device disconnected (expected: %s); RSSI: %s",
            self.name,
            self._expected_disconnect,
            self.rssi,
        )

    def _disconnect(self) -> None:
        """Disconnect from device."""
        self._disconnect_timer = None
        asyncio.create_task(self._execute_timed_disconnect())

    async def _execute_timed_disconnect(self) -> None:
        """Execute timed disconnection."""
        _LOGGER.debug(
            "%s: Disconnecting after timeout of %d", self.name, BLEAK_DISCONNECT_DELAY
        )
        await self._execute_disconnect()

    async def _execute_disconnect(self) -> None:
        """Execute disconnection."""
        async with self._connect_lock:
            _LOGGER.debug("%s: Disconnecting from device", self.name)
            if self._disconnect_timer:
                self._disconnect_timer.cancel()

            self._expected_disconnect = True
            read_char = self._read_char
            client = self._client

            self._client = None
            self._read_char = None
            self._write_char = None

            if client:
                if read_char:
                    await client.stop_notify(read_char)
                    _LOGGER.debug("%s: Stopped notifications from device", self.name)
                if client.is_connected:
                    await client.disconnect()
                    _LOGGER.debug("%s: Disconnected from device", self.name)

    def _resolve_characteristics(self, services: BleakGATTServiceCollection) -> bool:
        """Resolve characteristics."""
        if self._model:
            for characteristic in self._model.write_uuids:
                if char := services.get_characteristic(characteristic):
                    self._write_char = char
                    break
            if self._model.read_uuids:
                for characteristic in self._model.read_uuids:
                    if char := services.get_characteristic(characteristic):
                        self._read_char = char
                        break
            if not self._read_char:
                self._read_char = self._write_char
        _LOGGER.debug("%s: Read Characteristic: %s", self.name, self._read_char)
        _LOGGER.debug("%s: Write Characteristic: %s", self.name, self._write_char)
        return bool(self._read_char and self._write_char)

    @staticmethod
    def match_known_service(
        device: BLEDevice, advertisement: AdvertisementData
    ) -> bool:
        """Test if a BLE device has a known service UUID"""
        for model in UNILED_BLE_MODELS:
            for uuid in model.service_uuids:
                if uuid in advertisement.service_uuids:
                    return True
        return False

    @staticmethod
    def match_known_device(
        device: BLEDevice, advertisement: AdvertisementData | None = None
    ) -> UNILEDBLEModel:
        """Test if a BLE device is valid"""

        for model in UNILED_BLE_MODELS:
            if model.is_device_valid(device, advertisement):
                if not model.resolve_protocol:
                    _LOGGER.debug(
                        "Identified '%s' as '%s', by '%s'",
                        device.name,
                        model.model_name,
                        model.manufacturer,
                    )
                    return model
        return None

    @staticmethod
    def short_address(address: str) -> str:
        """Convert a Bluetooth address to a short address."""
        split_address = address.replace("-", ":").split(":")
        return f"{split_address[-2].upper()}{split_address[-1].upper()}"[-4:]

    @staticmethod
    def simpler_address(address: str) -> str:
        """Convert a Bluetooth address to a simpler address."""
        return address.replace(":", "").lower()

    @staticmethod
    def human_readable_name(name: str | None, local_name: str, address: str) -> str:
        """Return a human readable name for the given name, local_name, and address."""
        return f"{name or local_name} ({UNILEDBLE.short_address(address)})"
