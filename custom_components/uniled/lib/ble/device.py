"""UniLED BLE Device Handler."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Final

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
    UNILED_DISCONNECT_DELAY as UNILED_BLE_DISCONNECT_DELAY,
    UNILED_COMMAND_SETTLE_DELAY as UNILED_BLE_COMMAND_SETTLE_DELAY,
)

import async_timeout
import asyncio
import time
import logging

_LOGGER = logging.getLogger(__name__)

UNILED_TRANSPORT_BLE: Final = "ble"

UNILED_BLE_BAD_RSSI = -127
UNILED_BLE_ERROR_BACKOFF_TIME = 0.25
UNILED_BLE_NOTFICATION_TIMEOUT = 5.0

UUID_MANUFACTURER = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x2A29)
UUID_FIRMWARE_REV = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x2A26)
UUID_HARDWARE_REV = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x2A27)
UUID_MODEL_NBR = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x2A24)

UUID_BASE_FORMAT = "0000{}-0000-1000-8000-00805f9b34fb"

BANLANX_MANUFACTURER: Final = "SPLED (BanlanX)"
BANLANX_MANUFACTURER_ID: Final = 20563


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
    ble_notify_uuids: list[str]

    def match_ble_device(
        self, device: BLEDevice, advertisement: AdvertisementData | None = None
    ) -> bool:
        """Is a BLE device supported by UniLED."""
        if not hasattr(advertisement, "manufacturer_data"):
            return False
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
                        # _LOGGER.debug(
                        #    "Device '%s' (%s) identified as '%s', by %s.",
                        #    device.name,
                        #    device.address,
                        #    self.model_name,
                        #    self.manufacturer,
                        # )
                        return True
                    # _LOGGER.debug(
                    #    "%s : %s NOT in %s",
                    #    mid,
                    #    manu_data.hex(),
                    #    data.hex(),
                    # )
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
            if hasattr(model, "match_ble_model"):
                return model.match_ble_model(model_name)
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

        if not device:
            return None

        _LOGGER.debug(
            "Checking support for: '%s' (%s)... %s",
            device.address,
            device.name,
            advertisement,
        )

        found = None
        for model in UNILED_BLE_MODELS:
            match = model.match_ble_device(device, advertisement)

            if isinstance(match, UniledBleModel):
                _LOGGER.debug(
                    "Device '%s' (%s) identified as '%s', by %s.",
                    device.address,
                    device.name,
                    match.model_name,
                    match.manufacturer,
                )
                found = match
            elif match is True:
                if found is not None:
                    if found := UniledBleDevice.match_model_name(device.name):
                        _LOGGER.debug(
                            "Device '%s' name '%s' matches model '%s' by %s.",
                            device.address,
                            device.name,
                            found.model_name,
                            found.manufacturer,
                        )
                        return found
                    _LOGGER.debug(
                        "Device '%s' (%s) needs protocol resolving!",
                        device.address,
                        device.name,
                    )
                    return True
                else:
                    found = model

        if found is None:
            _LOGGER.debug(
                "Device '%s' (%s) not supported!",
                device.address or "??:??:??:??:??:??",
                device.name,
            )
        else:
            _LOGGER.debug(
                "Device '%s' (%s) is supported!",
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
        config: Any,
        ble_device: BLEDevice | None,
        advertisement_data: AdvertisementData | None = None,
        model_name: str | None = None,
    ) -> None:
        """Init the UniLED BLE Model"""
        self._ble_device = ble_device
        self._advertisement_data = advertisement_data
        self._loop = asyncio.get_event_loop()
        self._connect_lock = asyncio.Lock()
        self._operation_lock = asyncio.Lock()
        self._notification_event = asyncio.Event()
        self._expected_disconnect: bool = False
        self._disconnect_timer: asyncio.TimerHandle | None = None
        self._timed_disconnect_task: asyncio.Task[None] | None = None
        self._client: BleakClientWithServiceCache | None = None
        self._read_char: BleakGATTCharacteristic | None = None
        self._write_char: BleakGATTCharacteristic | None = None
        self._notify_char: BleakGATTCharacteristic | None = None

        _LOGGER.debug(
            "%s: Inititalizing (%s)...", self.name, model_name if not None else "-?-"
        )
        super().__init__(config)

        if model_name is not None and self._model is None:
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
        if not self._ble_device:
            return self.model_name
        return self._ble_device.name or self._ble_device.address

    @property
    def address(self) -> str:
        """Return the address of the device."""
        if isinstance(self._ble_device, BLEDevice):
            return self._ble_device.address
        return None

    @property
    def rssi(self) -> int | None:
        """Get the rssi of the device."""
        if isinstance(self._advertisement_data, AdvertisementData):
            return self._advertisement_data.rssi
        return UNILED_BLE_BAD_RSSI

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
        _LOGGER.debug("%s: Update!", self.name)

        if not (query := self.model.build_state_query(self)):
            raise Exception("Update - Failed, no state query command available!")

        if retry is None:
            retry = self.retry_count

        _LOGGER.debug("%s: Update - Send State Query... (retrys=%s)", self.name, retry)
        self._notification_event.clear()
        if not await self.send(query, retry):
            return False

        if not self.available:
            _LOGGER.warning("%s: Update - Failed, device not available.", self.name)
            return False

        if not self._notification_event.is_set():
            # Wait for actual response!
            async with self._operation_lock:
                _LOGGER.debug(
                    "%s: Update - Awaiting %s seconds for status notification...",
                    self.name,
                    UNILED_BLE_NOTFICATION_TIMEOUT,
                )
                try:
                    async with async_timeout.timeout(UNILED_BLE_NOTFICATION_TIMEOUT):
                        await self._notification_event.wait()
                except asyncio.TimeoutError:
                    _LOGGER.warning(
                        "%s: Update - Failed, notification timeout.", self.name
                    )
                    return False
                except Exception as ex:
                    _LOGGER.warning(
                        "%s: Update - Failed, exception: %s", self.name, str(ex)
                    )
                    return False

        for channel in self.channel_list:
            _LOGGER.debug(
                "%s: %s, Status: %s",
                self.name,
                channel.identity,
                channel.status.dump(),
            )
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
                    await self._async_invoke_forced_disconnect()
                finally:
                    pass
                self._last_notification_time = None
        elif isinstance(self._ble_device, BLEDevice):
            await close_stale_connections(self._ble_device)
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
            _LOGGER.debug("%s: Send command failed!", self.name)
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
            retry = self.retry_count

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
                    )
                    return False
                except CharacteristicMissingError as ex:
                    _LOGGER.error(
                        "%s: Characteristic missing: %s; Stopping trying; RSSI: %s",
                        self.name,
                        ex,
                        self.rssi,
                        exc_info=True,
                    )
                    raise
                except BLEAK_RETRY_EXCEPTIONS as ex:
                    if attempt == retry:
                        _LOGGER.error(
                            "%s: Communication failed; Stopping trying; RSSI: %s - %s",
                            self.name,
                            self.rssi,
                            str(ex),
                        )
                        return False

                    _LOGGER.debug(
                        "%s: Communication failed with: %s", self.name, str(ex)
                    )
                    await asyncio.sleep(UNILED_BLE_ERROR_BACKOFF_TIME)
                except AttributeError:
                    raise

        raise RuntimeError("Unreachable")

    async def _send_commands_locked(self, commands: list[bytes]) -> bool:
        """Send command(s) to device and read response."""
        if not await self._async_ensure_connected():
            return False
        try:
            return await self._execute_commands_locked(commands)
        except BleakDBusError as ex:
            # Disconnect so we can reset state and try again
            _LOGGER.debug(
                "%s: Backing off %ss; Disconnecting due to error: %s",
                self.name,
                UNILED_BLE_ERROR_BACKOFF_TIME,
                ex,
            )
            await asyncio.sleep(UNILED_BLE_ERROR_BACKOFF_TIME)
            await self._async_invoke_forced_disconnect()
            raise
        except BLEAK_RETRY_EXCEPTIONS as ex:
            # Disconnect so we can reset state and try again
            _LOGGER.debug(
                "%s: RSSI: %s; Disconnecting due to error: %s", self.name, self.rssi, ex
            )
            await self._async_invoke_forced_disconnect()
            raise
        except AttributeError:
            raise

    async def _execute_commands_locked(self, commands: list[bytes]) -> bool:
        """Execute command."""
        if not self._client:
            return False
        if not self._write_char:
            raise CharacteristicMissingError("Write characteristic missing")

        to_send = len(commands)
        for command in commands:
            if self._client.is_connected and command:
                _LOGGER.debug("%s: Sending command: %s", self.name, command.hex())
                reply = await self._client.write_gatt_char(
                    self._write_char, command, True
                )  # None)
                # await self._client.write_gatt_char(self._write_char, command, False) # Do not use!
                if reply is not None:
                    _LOGGER.debug("%s: Command Reply: %s", self.name, repr(reply))
                if to_send > 1:
                    await asyncio.sleep(UNILED_BLE_COMMAND_SETTLE_DELAY)
        return True

    ##
    ## Ensure Connected
    ##
    async def _async_ensure_connected(self, context: Any = None) -> bool:
        """Ensure connection to device is established."""
        if self._connect_lock.locked():
            _LOGGER.debug(
                "%s: Connection already in progress, waiting for it to complete...",
                self.name,
            )
        if self._client and self._client.is_connected:
            # _LOGGER.debug(
            #    "%s: Already connected before obtaining lock, resetting timer.",
            #    self.name,
            # )
            # self._reset_disconnect_timer()
            return True
        async with self._connect_lock:
            # Check again while holding the lock
            if self._client and self._client.is_connected:
                # _LOGGER.debug(
                #    "%s: Already connected after obtaining lock, resetting timer.",
                #    self.name,
                # )
                # self._reset_disconnect_timer()
                return True
            await close_stale_connections(self._ble_device)
            _LOGGER.debug(
                "%s: Connecting '%s'; RSSI: %s", self.name, self.address, self.rssi
            )
            client: BleakClientWithServiceCache = await establish_connection(
                BleakClientWithServiceCache,
                self._ble_device,
                self.name,
                self._disconnected,
                use_services_cache=True,
                ble_device_callback=lambda: self._device,
            )

            _LOGGER.debug(
                "%s: Connected '%s'; RSSI: %s", self.name, client.address, self.rssi
            )
            self._client = client
            await asyncio.sleep(UNILED_BLE_COMMAND_SETTLE_DELAY)

            if not self._resolve_characteristics(client.services):
                _LOGGER.warning(
                    "%s: Characteristic(s) missing, clearing cache.", self.name
                )
                await client.clear_cache()
                self._cancel_disconnect_timer()
                await self._async_execute_disconnect_with_lock()
                raise CharacteristicMissingError(
                    "Missing read/write/notify characteristic(s)."
                )

            self._last_notification_data = ()
            self._reset_disconnect_timer()

            if not await self._async_pair_with_device(context):
                _LOGGER.warning(
                    "%s: Pairing with '%s' failed!", self.name, client.address
                )
                self._cancel_disconnect_timer()
                await self._async_execute_disconnect_with_lock()
                return False

            return await self._async_start_notify(context)

    ##
    ## Pair & Notify
    ##
    async def _async_pair_with_device(self, context: Any = None) -> bool:
        """Login/Pair device"""
        return True

    async def _async_start_notify(self, context: Any = None) -> bool:
        """Start notification."""
        _LOGGER.debug(
            "%s: Subscribe to '%s' notifications: %s",
            self.name,
            self.address,
            self._notify_char,
        )

        # Gudard against long bleak notify attempts
        self._cancel_disconnect_timer()

        try:
            reply = await self._client.start_notify(
                self._notify_char, self._notification_handler
            )
        except BleakDBusError as ex:
            _LOGGER.warning(
                "%s: Starting '%s' notifications: %s!", self.name, self.address, str(ex)
            )
            self._cancel_disconnect_timer()
            await self._async_execute_disconnect_with_lock()
            return False

        # Probaly shouldn't reneable, as cancelled eleswhere!
        # self._reset_disconnect_timer()
        return True

    ##
    ## Notification Handler
    ##
    def _notification_handler(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle notification responses."""
        _LOGGER.debug(
            "%s: Notification from '%s' [%s],\nData: %s",
            self.name,
            self.address,
            sender.handle,
            data.hex(),
        )
        if self._model:
            if not self.channels:
                self._create_channels()
            try:
                if self._model.parse_notifications(self, sender.handle, data) is True:
                    self._last_notification_time = time.monotonic()
                    self._last_notification_data = ()
                    self._notification_event.set()
                    self._fire_callbacks()
                    return
            except ParseNotificationError as ex:
                _LOGGER.warning(
                    "%s: Notification parser failed! - %s",
                    self.name,
                    str(ex),
                )
            except Exception as ex:
                _LOGGER.warning(
                    "%s: Notification parser exception!",
                    self.name,
                    exc_info=True,
                )
        else:
            _LOGGER.debug(
                "%s: Device has no valid model, notification ignored", self.name
            )

    ##
    ## Disconnection Timer
    ##
    def _reset_disconnect_timer(self):
        """Reset disconnect timer."""
        self._cancel_disconnect_timer()
        self._expected_disconnect = False
        self._disconnect_timer = self._loop.call_later(
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
            self._async_invoke_timed_disconnect()
        )

    ##
    ## Disconnection Callback
    ##
    def _disconnected(self, client: BleakClientWithServiceCache) -> None:
        """Disconnected callback."""
        if client.address != self.address:
            _LOGGER.debug(
                "%s: Disconnection from '%s' ignored.", self.name, client.address
            )
            return
        if self._expected_disconnect:
            _LOGGER.debug(
                "%s: Disconnected from '%s'.",
                self.name,
                self.address,
            )
            return
        _LOGGER.warning(
            "%s: Disconnected from '%s' unexpectedly!",
            self.name,
            self.address,
        )
        self._cancel_disconnect_timer()

    ##
    ## Invoke a disconnection
    ##
    async def _async_invoke_forced_disconnect(self) -> None:
        """Execute forced disconnection."""
        self._cancel_disconnect_timer()
        _LOGGER.debug(
            "%s: Executing forced disconnect",
            self.name,
        )
        await self._async_execute_disconnect()

    async def _async_invoke_timed_disconnect(self) -> None:
        """Execute timed disconnection."""
        _LOGGER.debug(
            "%s: Executing timed disconnect after timeout of %s",
            self.name,
            UNILED_BLE_DISCONNECT_DELAY,
        )
        await self._async_execute_disconnect()

    ##
    ## Execute a disconnection
    ##
    async def _async_execute_disconnect(self) -> None:
        """Execute disconnection."""
        _LOGGER.debug("%s: Executing disconnect", self.name)
        async with self._connect_lock:
            await self._async_execute_disconnect_with_lock()

    async def _async_execute_disconnect_with_lock(self) -> None:
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

        if client and client.is_connected:
            try:
                _LOGGER.debug("%s: Disconnecting '%s'...", self.name, self.address)
                await client.disconnect()
            except BLEAK_RETRY_EXCEPTIONS as ex:
                _LOGGER.warning(
                    "%s: Disconnecting '%s' failed: %s.",
                    self.name,
                    self.address,
                    ex,
                )
                return
            else:
                _LOGGER.debug(
                    "%s: Disconnecting '%s' successful.",
                    self.name,
                    self.address,
                )
        else:
            _LOGGER.debug("%s: Already disconnected.", self.name)

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
            if self._model.ble_notify_uuids:
                for characteristic in self._model.ble_notify_uuids:
                    if char := services.get_characteristic(characteristic):
                        self._notify_char = char
                        break
            if not self._read_char:
                self._read_char = self._write_char
            if not self._notify_char:
                self._notify_char = self._read_char
        # _LOGGER.debug("%s: Read Characteristic: %s", self.name, self._read_char)
        # _LOGGER.debug("%s: Write Characteristic: %s", self.name, self._write_char)
        # _LOGGER.debug("%s: Notify Characteristic: %s", self.name, self._notify_char)
        return bool(self._read_char and self._write_char and self._notify_char)

    ##
    ## Utilities
    ##
    def set_device_and_advertisement(
        self, ble_device: BLEDevice, advertisement: AdvertisementData
    ) -> None:
        """Update the BLE device/advertisement."""
        if ble_device.address != self.address:
            _LOGGER.debug(
                "%s: Ignored '%s' advertisement update, as wrong target; RSSI: %s",
                self.name,
                ble_device.address,
                advertisement.rssi,
            )
            return
        if self._connect_lock.locked() or self._operation_lock.locked():
            _LOGGER.debug(
                "%s: Ignored '%s' advertisement update as busy; RSSI: %s",
                self.name,
                self.address,
                advertisement.rssi,
            )
            return
        self._ble_device = ble_device
        self._advertisement_data = advertisement or self._advertisement_data
        _LOGGER.debug(
            "%s: Updated '%s' advertisement; RSSI: %s\n%s",
            self.name,
            self.address,
            self.rssi,
            self._advertisement_data,
        )

    async def resolve_model(
        self, skip_local_name: bool = False, do_disconnect: bool = True
    ) -> UniledBleModel | None:
        """Resolve device model"""
        from .models import UNILED_BLE_MODELS

        if self._model is not None:
            return self._model

        for model in UNILED_BLE_MODELS:
            self._set_model(model)
            if await self.update(retry=0):
                if do_disconnect:
                    await self.stop()
                return self._model
            else:
                self._model = None

        await self.stop()
        _LOGGER.error("%s: Failed to resolve device model.", self.name)
        return None

    def _set_model(self, model: UniledBleModel) -> None:
        """Set the device model"""
        if self._model is None and isinstance(model, UniledBleModel):
            _LOGGER.debug(
                "%s: Set model as '%s' by %s",
                self.name,
                model.model_name,
                model.manufacturer,
            )
            self._model = model
            self._create_channels()
