"""UniLED Network Device Scanner (with thanks to flux_led)."""

from __future__ import annotations

import asyncio
import logging
import select
import socket
import time

from ..discovery import (  # noqa: TID252
    ATTR_UL_MODEL_NAME,
    UNILED_DISCOVERY_SOURCE_UDP,
    UniledDiscovery,
    discovery_model,
)
from .device import UNILED_TRANSPORT_NET, UniledDevice

# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger("uniled_scanner")


class UniledNetScanner:
    """UniLED Network Device Scanner Class."""

    SPNET_DISCOVERY_PORT = 6454
    SPNET_DISCOVERY_MESSAGE = bytes.fromhex("53704e65740000200000000002e0")
    SPNET_DISCOVERY_RESPONSE = bytes.fromhex("53704e6574000021000000000001")

    BROADCAST_FREQUENCY = 8
    BROADCAST_ADDRESS = "<broadcast>"
    MESSAGE_SEND_INTERLEAVE_DELAY = 0.4
    MAX_RESPONSE_SIZE = 40
    ALL_MESSAGES = {SPNET_DISCOVERY_MESSAGE}

    def __init__(self) -> None:
        """Initialize Network Scanner."""
        self._discoveries: dict[str, UniledDiscovery] = {}

    def _create_socket(self) -> socket.socket:
        """Create a UDP socket."""
        return self._create_udp_socket(self.SPNET_DISCOVERY_PORT)

    def _create_udp_socket(self, discovery_port: int) -> socket.socket:
        """Create a udp socket used for communicating with the device."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            # Legacy devices require source port to be the discovery port
            sock.bind(("", discovery_port))
        except OSError as err:
            _LOGGER.debug("Port %s is not available: %s", discovery_port, err)
            sock.bind(("", 0))
        sock.setblocking(False)
        return sock

    def _destination_from_address(self, address: str | None) -> tuple[str, int]:
        if address is None:
            address = self.BROADCAST_ADDRESS
        return (address, self.SPNET_DISCOVERY_PORT)

    def _get_discovery_messages(
        self,
    ) -> list[bytes]:
        return [self.SPNET_DISCOVERY_MESSAGE]

    def _send_message(
        self,
        sender: socket.socket | asyncio.DatagramTransport,
        destination: tuple[str, int],
        message: bytes,
    ) -> None:
        _LOGGER.debug(
            "Send UDP: %s => %s (%d)", destination, message.hex(), len(message)
        )
        sender.sendto(message, destination)

    def _send_messages(
        self,
        messages: list[bytes],
        sender: socket.socket | asyncio.DatagramTransport,
        destination: tuple[str, int],
    ) -> None:
        """Send messages with a short delay between them."""
        for idx, message in enumerate(messages):
            self._send_message(sender, destination, message)
            if idx != len(messages):
                time.sleep(self.MESSAGE_SEND_INTERLEAVE_DELAY)

    def _process_spnet(
        self,
        from_address: tuple[str, int],
        decoded_data: str,
        response_list: dict[str, UniledDiscovery],
    ) -> None:
        """Process 'SpNet' response data."""
        from_ipaddr = from_address[0]
        code = decoded_data[3]
        mac = UniledDevice.format_mac(decoded_data[5:11].hex())
        if (length := decoded_data[11]) != 0x00:
            name = str(decoded_data[12 : 12 + length - 1].decode("utf-8"))
        else:
            name = None

        # Already seen it!
        if from_ipaddr in response_list:
            return

        _LOGGER.debug(
            "Checking support for: '%s' (%s) - ID#: %s",
            from_ipaddr,
            name,
            hex(code),
        )

        discovery = UniledDiscovery(
            source=UNILED_DISCOVERY_SOURCE_UDP,
            transport=UNILED_TRANSPORT_NET,
            mac_address=mac,
            ip_address=from_ipaddr,
            local_name=name,
            model_code=code,
            model_name=None,
        )

        data = response_list.setdefault(from_ipaddr, discovery)

        if (model := discovery_model(discovery)) is not None:
            _LOGGER.debug(
                "Device '%s' (%s) identified as '%s', by %s",
                from_ipaddr,
                name,
                model.model_name,
                model.manufacturer,
            )
            data.update({ATTR_UL_MODEL_NAME: model.model_name})
            return

        _LOGGER.debug(
            "Device '%s' (%s) is unknown or not supported, ID#: %s",
            from_ipaddr,
            name,
            hex(code),
        )

    def _process_response(
        self,
        data: bytes | None,
        from_address: tuple[str, int],
        address: str | None,
        response_list: dict[str, UniledDiscovery],
    ) -> bool:
        """Process a response.

        Returns True if processing should stop
        """
        if data is None:
            return False
        if data in self.ALL_MESSAGES:
            return False
        if not data.startswith(self.SPNET_DISCOVERY_RESPONSE):
            return False
        try:
            self._process_spnet(
                from_address, data[len(self.SPNET_DISCOVERY_RESPONSE) :], response_list
            )
        except Exception:  # noqa: BLE001
            _LOGGER.warning(
                "Response decoder exception!",
                exc_info=True,
            )
            return False

        if address is None or address not in response_list:
            return False
        # response = response_list[address]
        return True

    def scan(
        self, timeout: int = 10, address: str | None = None
    ) -> list[UniledDiscovery]:
        """Scan for devices.

        If an address is provided, the scan will return
        as soon as it gets a response from that address
        """
        discovery_messages = self._get_discovery_messages()
        sock = self._create_socket()
        destination = self._destination_from_address(address)
        quit_time = time.monotonic() + timeout
        found_all = False
        while not found_all:
            if time.monotonic() > quit_time:
                break
            self._send_messages(discovery_messages, sock, destination)
            while True:
                sock.settimeout(1)
                remain_time = quit_time - time.monotonic()
                time_out = min(remain_time, timeout / self.BROADCAST_FREQUENCY)
                if time_out <= 0:
                    break
                read_ready, _, _ = select.select([sock], [], [], time_out)
                if not read_ready:
                    if time.monotonic() < quit_time:
                        # No response, send broadcast again in case it got lost
                        self._send_messages(discovery_messages, sock, destination)
                    continue
                try:
                    data, addr = sock.recvfrom(self.MAX_RESPONSE_SIZE)
                    if data in discovery_messages:
                        continue
                    _LOGGER.debug(
                        "Response: %s <= %s (%d)", addr, data.hex(), len(data)
                    )
                except TimeoutError:
                    continue
                if self._process_response(data, addr, address, self._discoveries):
                    found_all = True
                    break
        return self.found_devices

    @property
    def found_devices(self) -> list[UniledDiscovery]:
        """Return only complete device discoveries."""
        return [info for info in self._discoveries.values() if info["mac_address"]]

    def get_device_info_by_mac(self, mac: str) -> UniledDiscovery:
        """Get discovered device by mac address."""
        for b in self.found_devices:
            if b["mac_address"] == mac:
                return b
        return b

    def get_device_info(self) -> list[UniledDiscovery]:
        """Get discovered devices."""
        return self.found_devices
