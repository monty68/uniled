"""UniLED Network Device Scanner. (with thanks to flux_led)"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Union

from ..discovery import ATTR_UL_MODEL_NAME, UNILED_DISCOVERY_SOURCE_UDP, UniledDiscovery
from .device import UNILED_TRANSPORT_NET, UniledDevice

import logging
import asyncio
import select
import socket
import time

# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger("uniled_scanner")


class UniledNetScanner:
    """UniLED Network Device Scanner Class"""

    SPNET_DISCOVERY_PORT = 6454
    SPNET_DISCOVERY_MESSAGE = bytes.fromhex("53704e65740000200000000002e0")
    SPNET_DISCOVERY_RESPONSE = bytes.fromhex("53704e6574000021000000000001")

    BROADCAST_FREQUENCY = 8
    BROADCAST_ADDRESS = "<broadcast>"
    MESSAGE_SEND_INTERLEAVE_DELAY = 0.4
    MAX_RESPONSE_SIZE = 40
    ALL_MESSAGES = {SPNET_DISCOVERY_MESSAGE}

    def __init__(self) -> None:
        self._discoveries: Dict[str, UniledDiscovery] = {}

    def _create_socket(self) -> socket.socket:
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

    def _destination_from_address(self, address: Optional[str]) -> Tuple[str, int]:
        if address is None:
            address = self.BROADCAST_ADDRESS
        return (address, self.SPNET_DISCOVERY_PORT)

    def _get_discovery_messages(
        self,
    ) -> List[bytes]:
        return [self.SPNET_DISCOVERY_MESSAGE]

    def _send_message(
        self,
        sender: Union[socket.socket, asyncio.DatagramTransport],
        destination: Tuple[str, int],
        message: bytes,
    ) -> None:
        _LOGGER.debug("Send UDP: %s => %s", destination, message.hex())
        sender.sendto(message, destination)

    def _send_messages(
        self,
        messages: List[bytes],
        sender: Union[socket.socket, asyncio.DatagramTransport],
        destination: Tuple[str, int],
    ) -> None:
        """Send messages with a short delay between them."""
        for idx, message in enumerate(messages):
            self._send_message(sender, destination, message)
            if idx != len(messages):
                time.sleep(self.MESSAGE_SEND_INTERLEAVE_DELAY)

    def _process_spnet(
        self,
        from_address: Tuple[str, int],
        decoded_data: str,
        response_list: Dict[str, UniledDiscovery],
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
            "%s: Checking support for: '%s' (%s) - ID#: %s ...",
            from_ipaddr,
            mac,
            name,
            hex(code),
        )

        discovery = UniledDiscovery(
            source=UNILED_DISCOVERY_SOURCE_UDP,
            transport=UNILED_TRANSPORT_NET,
            mac_address=mac,
            ip_address=from_ipaddr,
            local_name=name,
            model_name=None,
            model_code=code,
        )

        data = response_list.setdefault(from_ipaddr, discovery)

        if (model := discovery.model) is not None:
            _LOGGER.debug(
                "%s: Device '%s' (%s) identified as '%s', by %s.",
                from_ipaddr,
                mac,
                name,
                model.model_name,
                model.manufacturer,
            )
            data.update({ATTR_UL_MODEL_NAME: model.model_name})
            return

        _LOGGER.debug(
            "%s: Device '%s' (%s) is unknown or not supported, ID#: %s.",
            from_ipaddr,
            mac,
            name,
            hex(code),
        )

    def _process_response(
        self,
        data: Optional[bytes],
        from_address: Tuple[str, int],
        address: Optional[str],
        response_list: Dict[str, UniledDiscovery],
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
        except Exception as ex:
            _LOGGER.warning(
                "Response decoder exception!",
                exc_info=True,
            )
            return False

        if address is None or address not in response_list:
            return False
        response = response_list[address]
        return True

    def scan(
        self, timeout: int = 10, address: Optional[str] = None
    ) -> List[UniledDiscovery]:
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
                    _LOGGER.debug("response: %s <= %s", addr, data.hex())
                except socket.timeout:
                    continue
                if self._process_response(data, addr, address, self._discoveries):
                    found_all = True
                    break
        return self.found_devices

    @property
    def found_devices(self) -> List[UniledDiscovery]:
        """Return only complete device discoveries."""
        return [info for info in self._discoveries.values() if info["mac_address"]]

    def get_device_info_by_mac(self, mac: str) -> UniledDiscovery:
        for b in self.found_devices:
            if b["mac_address"] == mac:
                return b
        return b

    def get_device_info(self) -> List[UniledDiscovery]:
        return self.found_devices
