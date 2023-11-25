"""UniLED BLE Device Handler."""
from __future__ import annotations
from dataclasses import dataclass

from bleak.exc import BleakDBusError
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.backends.service import BleakGATTCharacteristic, BleakGATTServiceCollection
from bleak_retry_connector import (
    BLEAK_RETRY_EXCEPTIONS,
    BleakClientWithServiceCache,
    BleakError,
    BleakNotFoundError,
    BleakConnectionError,
    retry_bluetooth_connection_error,
    ble_device_has_changed,
    close_stale_connections,
    establish_connection,
    get_device,
)

from ..device import UniledDevice, ParseNotificationError
from ..model import UniledModel
from ..const import (
    UNILED_TRANSPORT_BLE,
    UNILED_DEVICE_RETRYS as UNILED_BLE_DEVICE_RETRYS,
    UNILED_DISCONNECT_DELAY as UNILED_BLE_DISCONNECT_DELAY,
    UNILED_COMMAND_SETTLE_DELAY as UNILED_BLE_COMMAND_SETTLE_DELAY,
)

import async_timeout
import asyncio
import time
import logging

_LOGGER = logging.getLogger(__name__)

BASE_UUID_FORMAT = "0000{}-0000-1000-8000-00805f9b34fb"

UNILED_BLE_ERROR_BACKOFF_TIME = 0.25
UNILED_BLE_NOTFICATION_TIMEOUT = 2.0


class CharacteristicMissingError(Exception):
    """Raised when a characteristic is missing."""


class ChannelMissingError(Exception):
    """Raised when a channel is missing."""


##
## UniLed BLE Model Handler
##
@dataclass(frozen=True)
class UniledBleModel(UniledModel):
    """UniLED BLE Model Class"""

    ble_manufacturer_id: list[int]
    ble_manufacturer_data: bytearray | list[bytearray]
    ble_service_uuids: list[str]
    ble_write_uuids: list[str]
    ble_read_uuids: list[str]

    def match_ble_device(
        self, device: BLEDevice, advertisement: AdvertisementData | None = None
    ) -> bool:
        """Is a BLE device supported by UniLED."""
        for mid, data in advertisement.manufacturer_data.items():
            if isinstance(self.ble_manufacturer_id, list):
                if mid not in self.ble_manufacturer_id:
                    continue
            elif mid != self.ble_manufacturer_id:
                continue
            if self.ble_manufacturer_data is not None:
                manu_list = self.ble_manufacturer_data
                if not isinstance(manu_list, list):
                    manu_list = [manu_list]
                for manu_data in manu_list:
                    if data.startswith(manu_data):
                        _LOGGER.debug(
                            "Device '%s' (%s) identified as '%s', by %s.",
                            device.name,
                            device.address,
                            self.model_name,
                            self.manufacturer,
                        )
                        return True
                    _LOGGER.debug(
                        "%s : %s NOT in %s",
                        mid,
                        manu_data.hex(),
                        data.hex(),
                    )
            else:
                pass
        return False


##
## UniLed BLE Device Handler
##
class UniledBleDevice(UniledDevice):
    """UniLED BLE Device Class"""

    @staticmethod
    def match_model_name(model_name: str) -> UniledBleModel | None:
        """Lookup model from name"""
        from .models import UNILED_BLE_MODELS

        for model in UNILED_BLE_MODELS:
            if model.model_name == model_name:
                return model
        return None

    @staticmethod
    def match_known_service(
        device: BLEDevice, advertisement: AdvertisementData
    ) -> bool:
        """Test if a BLE device has a known service UUID"""
        from .models import UNILED_BLE_MODELS

        for model in UNILED_BLE_MODELS:
            for uuid in model.ble_service_uuids:
                if uuid in advertisement.service_uuids:
                    return True
        return False

    @staticmethod
    def match_known_device(
        device: BLEDevice, advertisement: AdvertisementData | None = None
    ) -> UniledBleModel | bool | None:
        """Test if a BLE device is supported"""
        from .models import UNILED_BLE_MODELS

        _LOGGER.debug(
            "Checking support for: '%s' (%s)... %s",
            device.name,
            device.address,
            advertisement,
        )

        found = None
        for model in UNILED_BLE_MODELS:
            if model.match_ble_device(device, advertisement):
                if found is not None:
                    if (found := UniledBleDevice.match_model_name(device.name)):
                        _LOGGER.debug("Device '%s' name matches model.", device.name)
                        return found
                    _LOGGER.debug(
                        "Device '%s' (%s) needs protocol resolving!",
                        device.name,
                        device.address,
                    )
                    return None
                else:
                    found = model

        if found is None:
            _LOGGER.debug(
                "Device '%s' (%s) not supported!",
                device.name,
                device.address,
            )
        return found

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
        return f"{name or local_name} ({UniledBleDevice.short_address(address)})"

    ##
    ## Initialize device instance
    ##
    def __init__(
        self,
        ble_device: BLEDevice,
        advertisement_data: AdvertisementData | None = None,
        model_name: str | None = None,
        retry_count: int = UNILED_BLE_DEVICE_RETRYS,
    ) -> None:
        """Init the UniLED BLE Model"""
        _LOGGER.debug("%s: Init BLE Device (Model: %s)", ble_device.name, model_name)

        self._ble_device = ble_device
        self._advertisement_data = advertisement_data
        self._connect_lock = asyncio.Lock()
        self._operation_lock = asyncio.Lock()
        self._notification_event = asyncio.Event()
        self._disconnect_timer: asyncio.TimerHandle | None = None
        self._timed_disconnect_task: asyncio.Task[None] | None = None
        self._expected_disconnect = False
        self._retry_count = retry_count
        self.loop = asyncio.get_event_loop()
        self._client: BleakClientWithServiceCache | None = None
        self._read_char: BleakGATTCharacteristic | None = None
        self._write_char: BleakGATTCharacteristic | None = None
        # super().__init__()

        if model_name is not None:
            self._set_model(self.match_model_name(model_name))

        if not self._model and (
            model := self.match_known_device(ble_device, advertisement_data)
        ):
            self._set_model(model)

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
        return 0

    @property
    def available(self) -> bool:
        """Return if the UniLED device available."""
        if (self._model and self._client) and self._client.is_connected:
            return True
        return False

    ##
    ## Update Device
    ##
    async def update(self, retry: int | None = None) -> bool:
        """Update the device."""
        _LOGGER.debug("%s: Update - Send State Query...", self.name)
        self._notification_event.clear()
        if not await self.send(self.model.build_state_query(self), retry):
            return False
        if not self.available:
            _LOGGER.warning("%s: Update - Failed, device not available.", self.name)
            return False
        if not self._notification_event.is_set():
            # Wait for actual response!
            _LOGGER.debug("%s: Update - Awaiting status notification...", self.name)
            async with self._operation_lock:
                try:
                    async with async_timeout.timeout(UNILED_BLE_NOTFICATION_TIMEOUT):
                        await self._notification_event.wait()
                except asyncio.TimeoutError:
                    _LOGGER.warning(
                        "%s: Update - Failed, notification timeout.", self.name
                    )
                    return False
        for channel in self.channel_list:
            _LOGGER.debug("%s: Status: %s", self.name, channel.status.dump())
        return True

    ##
    ## Stop Device
    ##
    async def stop(self) -> None:
        """Stop the device"""
        if self.available:
            _LOGGER.debug("%s: Stop", self.name)
            async with self._operation_lock:
                try:
                    await self._invoke_forced_disconnect()
                finally:
                    pass
                self._last_notification_time = None
        _LOGGER.debug("%s: Stopped", self.name)

    ##
    ## Send to Device
    ##
    async def send(
        self, commands: list[bytes] | bytes, retry: int | None = None
    ) -> bool:
        """Send command(s) to a device."""
        if not commands:
            _LOGGER.debug("%s: Send command ignored, no data to send.", self.name)
            return False

        if not isinstance(commands, list):
            commands = [commands]

        try:
            if await self._send_command(commands, retry):
                self._cancel_disconnect_timer()
                return True
            _LOGGER.warning("%s: Send command failed!", self.name)
        except Exception as ex:
            _LOGGER.error(
                "%s: Send command faled due to an exception.",
                self.name,
                exc_info=True,
            )
        return False

    async def _send_command(
        self, commands: list[bytes], retry: int | None = None
    ) -> bool:
        """Send command to device and read response."""
        if retry is None:
            retry = self._retry_count

        if self._model and not self.available:
            if (on_connect := self._model.build_on_connect(self)) is not None:
                if not isinstance(on_connect, list):
                    on_connect = [on_connect]
                _LOGGER.debug("%s: Inserting 'on connection' command(s)", self.name)
                on_connect.extend(commands)
                commands = on_connect

        max_attempts = retry + 1

        if self._operation_lock.locked():
            _LOGGER.debug(
                "%s: Operation already in progress, waiting for it to complete; RSSI: %s",
                self.name,
                self.rssi,
            )
        async with self._operation_lock:
            for attempt in range(max_attempts):
                try:
                    _LOGGER.debug(
                        "%s: Send %d command(s), attempt %s of %s...",
                        self.name,
                        len(commands),
                        attempt + 1,
                        max_attempts,
                    )
                    return await self._send_commands_locked(commands)
                except BleakNotFoundError:
                    _LOGGER.error(
                        "%s: Device not found, no longer in range, or poor RSSI: %s",
                        self.name,
                        self.rssi,
                        exc_info=True,
                    )
                    raise
                except CharacteristicMissingError as ex:
                    if attempt == retry:
                        _LOGGER.error(
                            "%s: Characteristic missing: %s; Stopping trying; RSSI: %s",
                            self.name,
                            ex,
                            self.rssi,
                            exc_info=True,
                        )
                        raise

                    _LOGGER.debug(
                        "%s: characteristic missing: %s; RSSI: %s",
                        self.name,
                        ex,
                        self.rssi,
                        exc_info=True,
                    )
                except BLEAK_RETRY_EXCEPTIONS:
                    if attempt == retry:
                        _LOGGER.error(
                            "%s: Communication failed; Stopping trying; RSSI: %s",
                            self.name,
                            self.rssi,
                            exc_info=True,
                        )
                        raise

                    _LOGGER.debug(
                        "%s: Communication failed with:", self.name, exc_info=True
                    )
                except AttributeError:
                    raise

        raise RuntimeError("Unreachable")

    async def _send_commands_locked(self, commands: list[bytes]) -> bool:
        """Send command(s) to device and read response."""
        if not await self._ensure_connected():
            return False
        try:
            return await self._execute_commands_locked(commands)
        except BleakDBusError as ex:
            # Disconnect so we can reset state and try again
            await asyncio.sleep(UNILED_BLE_ERROR_BACKOFF_TIME)
            _LOGGER.debug(
                "%s: RSSI: %s; Backing off %ss; Disconnecting due to error: %s",
                self.name,
                self.rssi,
                UNILED_BLE_ERROR_BACKOFF_TIME,
                ex,
            )
            await self._invoke_forced_disconnect()
            raise
        except BLEAK_RETRY_EXCEPTIONS as ex:
            # Disconnect so we can reset state and try again
            _LOGGER.debug(
                "%s: RSSI: %s; Disconnecting due to error: %s", self.name, self.rssi, ex
            )
            await self._invoke_forced_disconnect()
            raise
        except AttributeError:
            raise

    async def _execute_commands_locked(self, commands: list[bytes]) -> bool:
        """Execute command."""
        if not self._client:
            return False
        if not self._write_char:
            raise CharacteristicMissingError("Write characteristic missing")
        if not self._read_char:
            raise CharacteristicMissingError("Read characteristic missing")

        to_send = len(commands)
        for command in commands:
            if self._client.is_connected and command:
                _LOGGER.debug("%s: Sending command: %s", self.name, command.hex())
                await self._client.write_gatt_char(self._write_char, command, None)
                # await self._client.write_gatt_char(self._write_char, command, False)
                if to_send > 1:
                    await asyncio.sleep(UNILED_BLE_COMMAND_SETTLE_DELAY)
        return True

    ##
    ## Ensure Connected
    ##
    async def _ensure_connected(self) -> bool:
        """Ensure connection to device is established."""
        if self._connect_lock.locked():
            _LOGGER.debug(
                "%s: Connection already in progress, waiting for it to complete; RSSI: %s",
                self.name,
                self.rssi,
            )
        if self._client and self._client.is_connected:
            # _LOGGER.debug(
            #    "%s: Already connected before obtaining lock, resetting timer; RSSI: %s",
            #    self.name,
            #    self.rssi,
            # )
            self._reset_disconnect_timer()
            return True
        async with self._connect_lock:
            # Check again while holding the lock
            if self._client and self._client.is_connected:
                _LOGGER.debug(
                    "%s: Already connected after obtaining lock, resetting timer; RSSI: %s",
                    self.name,
                    self.rssi,
                )
                self._reset_disconnect_timer()
                return True
            _LOGGER.debug("%s: Connecting; RSSI: %s", self.name, self.rssi)
            client: BleakClientWithServiceCache = await establish_connection(
                BleakClientWithServiceCache,
                self._ble_device,
                self.name,
                self._disconnected,
                use_services_cache=True,
                ble_device_callback=lambda: self._device,
            )

            _LOGGER.debug("%s: Connected; RSSI: %s", self.name, self.rssi)
            self._client = client

            if not self._resolve_characteristics(client.services):
                _LOGGER.debug(
                    "%s: Characteristic(s) missing, clearing cache; RSSI: %s",
                    self.name,
                    self.rssi,
                )
                await client.clear_cache()
                self._cancel_disconnect_timer()
                await self._execute_disconnect_with_lock()
                raise CharacteristicMissingError(
                    "Missing read/write characteristic(s)."
                )

            return await self._start_notify()

    ##
    ## Notification Handler
    ##
    def _notification_handler(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle notification responses."""
        _LOGGER.debug("%s: Notification (%s): %s", self.name, sender.handle, data.hex())
        if self._model:
            if not self.channels:
                self._create_channels()
            try:
                if self._model.parse_notifications(self, sender.handle, data):
                    self._last_notification_time = time.monotonic()
                    self._last_notification_data = ()
                    self._notification_event.set()
                    self._fire_callbacks()
                    return
            except Exception as ex:
                _LOGGER.debug(
                    "%s: Notification parser failed!", self.name, exc_info=True
                )
                raise  ## Hmmm!

    async def _start_notify(self) -> bool:
        """Start notification."""
        _LOGGER.debug("%s: Subscribe to notifications; RSSI: %s", self.name, self.rssi)
        self._last_notification_data = ()
        self._reset_disconnect_timer()
        await self._client.start_notify(self._read_char, self._notification_handler)
        return True

    ##
    ## Disconnection Timer
    ##
    def _reset_disconnect_timer(self):
        """Reset disconnect timer."""
        self._cancel_disconnect_timer()
        self._expected_disconnect = False
        self._disconnect_timer = self.loop.call_later(
            UNILED_BLE_DISCONNECT_DELAY, self._disconnect_with_timer
        )

    def _cancel_disconnect_timer(self):
        """Cancel disconnect timer."""
        if self._disconnect_timer:
            self._disconnect_timer.cancel()
            self._disconnect_timer = None

    def _disconnect_with_timer(self):
        """Disconnect from device."""
        if self._operation_lock.locked() and self._client.is_connected:
            _LOGGER.debug(
                "%s: Operation in progress, resetting disconnect timer; RSSI: %s",
                self.name,
                self.rssi,
            )
            self._reset_disconnect_timer()
            return
        self._cancel_disconnect_timer()
        self._timed_disconnect_task = asyncio.create_task(
            self._invoke_timed_disconnect()
        )

    ##
    ## Disconnection Callback
    ##
    def _disconnected(self, client: BleakClientWithServiceCache) -> None:
        """Disconnected callback."""
        if self._expected_disconnect:
            _LOGGER.debug(
                "%s: Disconnected from device; RSSI: %s", self.name, self.rssi
            )
            return
        _LOGGER.warning(
            "%s: Device unexpectedly disconnected; RSSI: %s",
            self.name,
            self.rssi,
        )
        self._cancel_disconnect_timer()

    ##
    ## Invoke a disconnection
    ##
    async def _invoke_forced_disconnect(self) -> None:
        """Execute forced disconnection."""
        self._cancel_disconnect_timer()
        _LOGGER.debug(
            "%s: Executing forced disconnect",
            self.name,
        )
        await self._execute_disconnect()

    async def _invoke_timed_disconnect(self) -> None:
        """Execute timed disconnection."""
        _LOGGER.debug(
            "%s: Executing timed disconnect after timeout of %s",
            self.name,
            UNILED_BLE_DISCONNECT_DELAY,
        )
        await self._execute_disconnect()

    ##
    ## Execute a disconnection
    ##
    async def _execute_disconnect(self) -> None:
        """Execute disconnection."""
        _LOGGER.debug("%s: Executing disconnect", self.name)
        async with self._connect_lock:
            await self._execute_disconnect_with_lock()

    async def _execute_disconnect_with_lock(self) -> None:
        """Execute disconnection while holding the lock."""
        assert self._connect_lock.locked(), "Lock not held"
        _LOGGER.debug("%s: Executing disconnect with lock", self.name)
        if self._disconnect_timer:  # If the timer was reset, don't disconnect
            _LOGGER.debug("%s: Skipping disconnect as timer reset", self.name)
            return
        client = self._client
        self._expected_disconnect = True
        self._client = None
        self._read_char = None
        self._write_char = None
        if not client:
            _LOGGER.debug("%s: Already disconnected", self.name)
            return
        _LOGGER.debug("%s: Disconnecting", self.name)
        try:
            await client.disconnect()
        except BLEAK_RETRY_EXCEPTIONS as ex:
            _LOGGER.warning(
                "%s: Error disconnecting: %s; RSSI: %s",
                self.name,
                ex,
                self.rssi,
            )
        else:
            _LOGGER.debug("%s: Disconnect completed successfully", self.name)

    ##
    ## Resolve Characteristics
    ##
    def _resolve_characteristics(self, services: BleakGATTServiceCollection) -> bool:
        """Resolve characteristics."""
        if self._model:
            for characteristic in self._model.ble_write_uuids:
                if char := services.get_characteristic(characteristic):
                    self._write_char = char
                    break
            if self._model.ble_read_uuids:
                for characteristic in self._model.ble_read_uuids:
                    if char := services.get_characteristic(characteristic):
                        self._read_char = char
                        break
            if not self._read_char:
                self._read_char = self._write_char
        _LOGGER.debug("%s: Read Characteristic: %s", self.name, self._read_char)
        _LOGGER.debug("%s: Write Characteristic: %s", self.name, self._write_char)
        return bool(self._read_char and self._write_char)

    ##
    ## Utilities
    ##
    def set_device_and_advertisement(
        self, ble_device: BLEDevice, advertisement: AdvertisementData
    ) -> None:
        """Update the BLE device/advertisement."""
        ##
        ## Should we wait until not busy, before doing update??
        ##
        if self._connect_lock.locked() or self._operation_lock.locked():
            _LOGGER.debug(
                "%s: Ignored advertisement update as busy; RSSI: %s",
                self.name,
                advertisement.rssi,
            )
            return
        self._ble_device = ble_device
        self._advertisement_data = advertisement or self._advertisement_data
        _LOGGER.debug("%s: Updated advertisement data; RSSI: %s", self.name, self.rssi)

    async def resolve_model(
        self, skip_local_name: bool = False, do_disconnect: bool = True
    ) -> UniledBleModel | None:
        """Resolve device model"""
        from .models import UNILED_BLE_MODELS

        if self._model is not None:
            return self._model

        _LOGGER.debug("%s: Resolving model...", self.name)

        for model in UNILED_BLE_MODELS:
            if skip_local_name and self.name in model.ble_local_names:
                continue
            for uuid in model.ble_service_uuids:
                if uuid in self._advertisement_data.service_uuids:
                    self._set_model(model)
                    if await self.update(retry=0):
                        if do_disconnect:
                            await self.stop()
                        return self._model
        await self.stop()
        _LOGGER.error("%s: Failed to resolve device model.", self.name)
        return None

    def _set_model(self, model: UniledBleModel) -> None:
        """Set the device model"""
        if self._model is None and model is not None:
            _LOGGER.debug(
                "%s: Set model as '%s' by %s",
                self.name,
                model.model_name,
                model.manufacturer,
            )
            self._model = model
            self._create_channels()
