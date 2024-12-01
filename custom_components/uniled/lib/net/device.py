"""UniLED NETwork Device Handler."""

from __future__ import annotations
from typing import Any, Final, Optional
from ..discovery import UniledDiscovery
from ..device import UniledDevice
from .model import UniledNetModel
from ..const import (
    ATTR_UL_IP_ADDRESS,
    ATTR_UL_LOCAL_NAME,
    ATTR_UL_MAC_ADDRESS,
    ATTR_UL_MODEL_NAME,
    ATTR_UL_POWER,
    UNILED_COMMAND_SETTLE_DELAY as UNILED_NET_COMMAND_SETTLE_DELAY,
    UNILED_DISCONNECT_DELAY as UNILED_NET_DISCONNECT_DELAY,
    UNILED_TRANSPORT_NET,
)
from .retrys import _socket_retry

import time
import select
import socket
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

UNILED_NET_DEVICE_TIMEOUT: Final = 5.0


##
## UniLed NETwork Device Handler
##
class UniledNetDevice(UniledDevice):
    """UniLED NETwork Device Class"""

    ##
    ## Initialize device instance
    ##
    def __init__(
        self,
        discovery: UniledDiscovery,
        timeout: float = UNILED_NET_DEVICE_TIMEOUT,
        options: Optional[Any] = None,
    ) -> None:
        """Init the UniLED BLE Model"""
        self._socket: Optional[socket.socket] = None
        self._lock = asyncio.Lock()
        self._timeout: float = timeout
        self._available = False
        self._discovery = discovery

        assert isinstance(discovery, UniledDiscovery)
        self._model = discovery.model
        assert self._model is not None

        _LOGGER.debug(
            "%s: Inititalizing (%s)...",
            self.name,
            self.model_name if not None else "-?-",
        )

        super().__init__(options)
        self._create_channels()

    @property
    def transport(self) -> str:
        """Return the device transport."""
        return UNILED_TRANSPORT_NET

    @property
    def name(self) -> str:
        """Get the name of the device."""
        if self._discovery and self._discovery.get(ATTR_UL_LOCAL_NAME):
            name = self._discovery.get(ATTR_UL_LOCAL_NAME, self.model_name)
            if name is not None:
                return name
        return self.short_address(self.address)

    @property
    def host(self) -> str | None:
        """Get the hostname of the device."""
        if self._discovery and self._discovery.get(ATTR_UL_IP_ADDRESS):
            return self._discovery[ATTR_UL_IP_ADDRESS]
        return None

    @property
    def port(self) -> int:
        """Return the network port."""
        assert self._model is not None  # nosec
        return self._model.port

    @property
    def address(self) -> str | None:
        """Return the (mac) address of the device."""
        if self._discovery and self._discovery.get(ATTR_UL_MAC_ADDRESS):
            return self._discovery[ATTR_UL_MAC_ADDRESS]
        return None

    @property
    def available(self) -> bool:
        """Return if the UniLED device available."""
        if self._model and self._available:
            return True
        return False

    @property
    def discovery(self) -> Optional[UniledDiscovery]:
        """Return the discovery data."""
        return self._discovery

    @discovery.setter
    def discovery(self, value: UniledDiscovery) -> None:
        """Set the discovery data."""
        self._discovery = value

    def set_available(self, reason: str) -> None:
        _LOGGER.debug("%s: Set available: %s", self.name, reason)
        self._unavailable_reason = None
        self._available = True

    def set_unavailable(self, reason: str) -> None:
        _LOGGER.debug("%s: Set unavailable: %s", self.name, reason)
        self._unavailable_reason = reason
        self._available = False
        self._close()

    async def update(self, retry: int | None = None) -> bool:
        """Update the device."""
        _LOGGER.debug("%s: Update!", self.name)
        if not (query := self.model.build_state_query(self)):
            raise Exception("Update - Failed: no state query command available!")
        if not await self.send(query, retry):
            return False
        valid = 0
        for channel in self.channel_list:
            if channel.status.has(ATTR_UL_POWER):
                valid += 1
            _LOGGER.debug(
                "%s: %s - Status: %s",
                self.name,
                channel.identity,
                channel.status.dump(),
            )

        if valid != self.channels:
            _LOGGER.warning("%s: Invalid channel status", self.name)
            return False
        return True

    async def stop(self) -> None:
        """Stop the device"""
        if self.available:
            _LOGGER.debug("%s: Stop", self.name)
            async with self._lock:
                self._close()
                self.set_unavailable("Stopped")

    async def send(
        self, commands: list[bytes] | bytes, retry: int | None = None
    ) -> bool:
        """Send command(s) to a device."""

        if not commands:
            _LOGGER.debug("%s: Send command ignored, no data to send.", self.name)
            return False

        if not isinstance(commands, list):
            commands = [commands]

        if self._lock.locked():
            _LOGGER.debug(
                "%s: Operation already in progress, waiting for it to complete...",
                self.name,
            )

        try:
            async with self._lock:
                self._connect_if_disconnected()
                to_send = len(commands)
                for command in commands:
                    if self.available and command:
                        await self._execute_command(command)
                    await asyncio.sleep(UNILED_NET_COMMAND_SETTLE_DELAY)
        except Exception as ex:
            _LOGGER.warning(
                "%s: Send exception!",
                self.name,
                exc_info=True,
            )
            self._close()
            return False

        if self._model.close_after_send:
            self._close()
        return True

    async def _execute_command(self, command: bytes) -> None:
        """Execute a single command."""

        self._send_bytes(command)
        if (expected := self._model.length_response_header(self, command)) == 0:
            return

        header = self._read_bytes(expected)
        if len(header) != expected:
            raise Exception(
                f"Response Header Error: read {len(header)}, expected {expected}"
            )

        expected = self._model.decode_response_header(self, command, header)
        if expected == -1:
            raise Exception(f"Response Header Error")
        elif expected is None or expected == 0:
            return

        payload = self._read_bytes(expected)
        if len(payload) != expected:
            raise Exception(
                f"Response Payload Error: read {len(payload)}, expected {expected}"
            )

        try:
            if (
                self._model.decode_response_payload(self, command, header, payload)
                is True
            ):
                _LOGGER.debug("%s: Transaction successful", self.name)
                self._fire_callbacks()
                return
            else:
                _LOGGER.debug("%s: Transaction failed", self.name)

        except Exception as ex:
            _LOGGER.warning(
                "%s: Response decoder exception!",
                self.name,
                exc_info=True,
            )

    @_socket_retry(attempts=2)  # type: ignore
    def _send_bytes(self, bytes: bytearray) -> None:
        assert self._socket is not None
        _LOGGER.debug(
            "%s => %s (%d)",
            self.name,
            "".join(f"{x:02X}" for x in bytes),
            len(bytes),
        )
        self._socket.send(bytes)

    def _read_bytes(self, expected: int) -> bytearray:
        assert self._socket is not None
        remaining = expected
        rx = bytearray()
        begin = time.monotonic()
        while remaining > 0:
            timeout_left = self._timeout - (time.monotonic() - begin)
            if timeout_left <= 0:
                break
            try:
                self._socket.setblocking(False)
                read_ready, _, _ = select.select([self._socket], [], [], timeout_left)
                if not read_ready:
                    _LOGGER.debug("%s: timed out reading %d bytes", self.name, expected)
                    break
                chunk = self._socket.recv(remaining)
                _LOGGER.debug(
                    "%s <= %s (%d)",
                    self.name,
                    "".join(f"{x:02X}" for x in chunk),
                    len(chunk),
                )
                if chunk:
                    begin = time.monotonic()
                remaining -= len(chunk)
                rx.extend(chunk)
            except OSError as ex:
                _LOGGER.debug("%s: socket error (%s): %s", self.name, self.host, ex)
                pass
            finally:
                self._socket.setblocking(True)
        return rx

    def _connect_if_disconnected(self) -> None:
        """Connect only if not already connected."""
        if self._socket is None:
            self._connect()

    @_socket_retry(attempts=0)  # type: ignore
    def _connect(self) -> None:
        self._close()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self._timeout)
        _LOGGER.debug("%s: Connect %s:%d...", self.name, self.host, self.port)
        self._socket.connect((self.host, self.port))

    def _close(self) -> None:
        if self._socket is None:
            return
        try:
            self._socket.close()
        except OSError:
            pass
        finally:
            self._socket = None
        _LOGGER.debug("%s: Socket closed", self.name)
