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

UNILED_COMMAND_SETTLE_DELAY = 0.2


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
        self, ble_device: BLEDevice, advertisement_data: AdvertisementData | None = None
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
        self._resolve_protocol_event = asyncio.Event()
        super().__init__()
        _LOGGER.debug("%s: Init BLE Device", self.name)
        self.set_device_and_advertisement(ble_device, advertisement_data)

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
        return self._ble_device.rssi

    async def update(self, force: bool = False):
        """Update the UniLED BLE device."""
        _LOGGER.debug("%s: Update (forced=%s)", self.name, force)
        await self._ensure_connected()
        await self.send_command(self.model.construct_status_query(self))

    async def stop(self) -> None:
        """Stop the UniLED BLE device."""
        _LOGGER.debug("%s: Stop", self.name)
        await self._execute_disconnect()

    def set_device_and_advertisement(
        self, ble_device: BLEDevice, advertisement: AdvertisementData
    ) -> None:
        """Set the ble device."""
        self._ble_device = ble_device
        self._advertisement_data = advertisement or self._advertisement_data
        _LOGGER.debug("%s: Set device %s", self.name, advertisement)

        if self._advertisement_data and self._model is None:
            self._model = self.match_valid_device(ble_device, advertisement)
            if self._model is not None:
                self._create_channels()

    async def send_command(
        self, commands: list[bytes] | bytes, retry: int | None = None
    ) -> bool:
        """Send command to device and read response."""
        await self._ensure_connected()
        # await self._resolve_protocol()
        if commands:
            if not isinstance(commands, list):
                commands = [commands]
            await self._send_command_while_connected(commands, retry)
            return True
        return False

    async def _notification_handler(self, _sender: int, data: bytearray) -> None:
        """Handle notification responses."""
        _LOGGER.debug("%s: Notification received: %s", self.name, data.hex())
        if self._model:
            new_master_state = await self._model.async_decode_notifications(
                self, _sender, data
            )
            if new_master_state is not None:
                self.master.set_status(new_master_state)

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

            if self._read_char:
                _LOGGER.debug("%s: Subscribe to notifications", self.name)
                await client.start_notify(self._read_char, self._notification_handler)
                if not self._model:
                    await self._resolve_protocol()
                else:
                    # Send any "on connection" message(s)
                    await self.send_command(self._model.construct_connect_message())

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
            await asyncio.sleep(BLEAK_BACKOFF_TIME)
            _LOGGER.debug(
                "%s: RSSI: %s; Backing off %ss; Disconnecting due to error: %s",
                self.name,
                self.rssi,
                BLEAK_BACKOFF_TIME,
                ex,
            )
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
        assert self._client is not None  # nosec
        if not self._write_char:
            raise CharacteristicMissingError("Write characteristic missing")
        if not self._read_char:
            raise CharacteristicMissingError("Read characteristic missing")
        to_send = len(commands)
        for command in commands:
            _LOGGER.debug("%s: Sending command: %s ", self.name, command.hex())
            await self._client.write_gatt_char(self._write_char, command, False)
            if to_send > 1:
                await asyncio.sleep(UNILED_COMMAND_SETTLE_DELAY)

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
        if self._expected_disconnect:
            _LOGGER.debug("%s: Disconnected from device", self.name)
            return
        _LOGGER.warning(
            "%s: Device unexpectedly disconnected; RSSI: %s", self.name, self.rssi
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
            read_char = self._read_char
            client = self._client
            self._expected_disconnect = True
            self._client = None
            self._read_char = None
            self._write_char = None
            if client and client.is_connected:
                await client.stop_notify(read_char)
                await client.disconnect()

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
        return bool(self._read_char and self._write_char)

    async def _resolve_protocol(self) -> None:
        """Resolve protocol."""
        if self._model.resolve_protocol:
            if self._resolve_protocol_event.is_set():
                _LOGGER.debug("%s: resolver in progress", self.name)
                return
            await self.send_command(self._model.construct_status_query(self))
            async with async_timeout.timeout(10):
                await self._resolve_protocol_event.wait()

    @staticmethod
    async def contactable(
        device: BLEDevice, advertisement: AdvertisementData | None = None
    ) -> str:
        """Test if a BLE device is contactable"""
        _LOGGER.debug("%s: Contactable", device.name)
        error = "not_supported"

        if UNILEDBLE.match_valid_device(device, advertisement):
            instance = UNILEDBLE(device, advertisement)
            try:
                await instance.update()
            except BLEAK_EXCEPTIONS:
                error = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error")
                error = "unknown"
            else:
                await instance.stop()
                error = ""
        return error

    @staticmethod
    def match_valid_device(
        device: BLEDevice, advertisement: AdvertisementData | None = None
    ) -> UNILEDBLEModel:
        """Test if a BLE device is valid"""

        for model in UNILED_BLE_MODELS:
            # _LOGGER.debug("Probing: %s - %s", model.model_name, advertisement)
            if model.is_device_valid(device, advertisement):
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
