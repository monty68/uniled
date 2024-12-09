"""UniLED Network Device Discovery (with thanks to flux_led)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
import contextlib
import logging
import time
from typing import Any

from homeassistant import config_entries
from homeassistant.components import network
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_CODE, CONF_HOST, CONF_MODEL, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, discovery_flow
from homeassistant.util.network import is_ip_address

from .const import (
    ATTR_UL_IP_ADDRESS,
    ATTR_UL_LOCAL_NAME,
    ATTR_UL_MAC_ADDRESS,
    ATTR_UL_MODEL_NAME,
    CONF_UL_TRANSPORT as CONF_TRANSPORT,
    DOMAIN,
    UNILED_DISCOVERY,
    UNILED_DISCOVERY_DIRECTED_TIMEOUT,
)
from .lib.device import UniledDevice
from .lib.discovery import CONF_TO_DISCOVERY, UniledDiscovery
from .lib.net.scanner import UniledNetScanner

_LOGSCAN = logging.getLogger("uniled_scanner")
_LOGGER = logging.getLogger(__name__)


class UniledUDPScanner(asyncio.DatagramProtocol):
    """UniLED UDP Scanner Class."""

    def __init__(
        self,
        destination: tuple[str, int],
        on_response: Callable[[bytes, tuple[str, int]], None],
    ) -> None:
        """Init the discovery protocol."""
        self.transport = None
        self.destination = destination
        self.on_response = on_response

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Trigger on_response."""
        self.on_response(data, addr)

    def error_received(self, exc: Exception | None) -> None:
        """Handle error."""
        _LOGSCAN.debug("UniledUDPScanner error: %s", exc)

    def connection_lost(self, exc: Exception | None) -> None:
        """Lost connection."""


class UniledScanner(UniledNetScanner):
    """UniLED Network Scanner."""

    def __init__(self) -> None:
        """Initialize the scanner."""
        self.loop = asyncio.get_running_loop()
        super().__init__()

    async def _async_send_messages(
        self,
        messages: list[bytes],
        sender: asyncio.DatagramTransport,
        destination: tuple[str, int],
    ) -> None:
        """Send messages with a short delay between them."""
        last_idx = len(messages) - 1
        for idx, message in enumerate(messages):
            self._send_message(sender, destination, message)
            if idx != last_idx:
                await asyncio.sleep(self.MESSAGE_SEND_INTERLEAVE_DELAY)

    async def _async_run_scan(
        self,
        transport: asyncio.DatagramTransport,
        destination: tuple[str, int],
        timeout: int,
        found_all_future: asyncio.Future[bool],
    ) -> None:
        """Send the scans."""
        discovery_messages = self._get_discovery_messages()
        await self._async_send_messages(discovery_messages, transport, destination)
        quit_time = time.monotonic() + timeout
        time_out = timeout / self.BROADCAST_FREQUENCY
        while True:
            try:
                async with asyncio.timeout(time_out):
                    await asyncio.shield(found_all_future)
            except TimeoutError:
                pass
            else:
                return  # found_all
            time_out = min(
                quit_time - time.monotonic(), timeout / self.BROADCAST_FREQUENCY
            )
            if time_out <= 0:
                return
            # No response, send broadcast again in case it got lost
            await self._async_send_messages(discovery_messages, transport, destination)

    async def async_scan(
        self, timeout: int = 10, address: str | None = None
    ) -> list[UniledDiscovery]:
        """Discover UNILED (SpNet) Devices."""
        sock = self._create_socket()
        destination = self._destination_from_address(address)
        found_all_future: asyncio.Future[bool] = self.loop.create_future()

        def _on_response(data: bytes, addr: tuple[str, int]) -> None:
            # Ignore echo's
            if data in self.ALL_MESSAGES:
                return
            _LOGSCAN.debug("Response: %s <= %s (%d)", addr, data.hex(), len(data))
            if self._process_response(data, addr, address, self._discoveries):
                with contextlib.suppress(asyncio.InvalidStateError):
                    found_all_future.set_result(True)

        transport_proto = await self.loop.create_datagram_endpoint(
            lambda: UniledUDPScanner(
                destination=destination,
                on_response=_on_response,
            ),
            sock=sock,
        )
        transport = transport_proto[0]
        try:
            await self._async_run_scan(
                transport, destination, timeout, found_all_future
            )
        finally:
            transport.close()

        return self.found_devices


async def async_discover_devices(
    hass: HomeAssistant | None, timeout: int, address: str | None = None
) -> list[UniledDiscovery]:
    """Discover devices."""

    if address:
        _LOGSCAN.debug("Probing device '%s'", address)
        targets = [address]
    else:
        _LOGGER.debug("Scanning started")
        targets = [
            str(address)
            for address in await network.async_get_ipv4_broadcast_addresses(hass)
        ]

    scanner = UniledScanner()
    for idx, discovered in enumerate(
        await asyncio.gather(
            *[
                scanner.async_scan(timeout=timeout, address=address)
                for address in targets
            ],
            return_exceptions=True,
        )
    ):
        if isinstance(discovered, Exception):
            _LOGGER.debug(
                "Scanning '%s' failed with error: %s", targets[idx], discovered
            )
            continue

    if not address:
        _LOGGER.debug("Scanning complete")
        return scanner.get_device_info()

    _LOGSCAN.debug("Probe complete %s", scanner.get_device_info())

    return [
        device
        for device in scanner.get_device_info()
        if device[ATTR_UL_IP_ADDRESS] == address
    ]


async def async_discover_device(
    hass: HomeAssistant | None, host: str
) -> UniledDiscovery | None:
    """Direct discovery at a single ip instead of broadcast."""
    # If we are missing the unique_id we should be able to fetch it
    # from the device by doing a directed discovery at the host only
    for device in await async_discover_devices(
        hass, UNILED_DISCOVERY_DIRECTED_TIMEOUT, host
    ):
        if device[ATTR_UL_IP_ADDRESS] == host:
            return device
    return None


@callback
def async_trigger_discovery(
    hass: HomeAssistant,
    discovered_devices: list[UniledDiscovery],
) -> None:
    """Trigger config flows for discovered devices."""
    for device in discovered_devices:
        discovery_flow.async_create_flow(
            hass,
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={**device},
        )


@callback
def async_build_cached_discovery(entry: ConfigEntry) -> UniledDiscovery:
    """When discovery is unavailable, load it from the config entry."""
    data = entry.data
    return UniledDiscovery(
        transport=data.get(CONF_TRANSPORT),
        source="cfg",
        mac_address=dr.format_mac(entry.unique_id),
        ip_address=data[CONF_HOST],
        local_name=data.get(CONF_NAME),
        model_name=data.get(CONF_MODEL),
        model_code=data.get(CONF_CODE),
    )


@callback
def async_get_discovery(hass: HomeAssistant, host: str) -> UniledDiscovery | None:
    """Check if a device was already discovered via a broadcast discovery."""
    discoveries: list[UniledDiscovery] = hass.data[DOMAIN][UNILED_DISCOVERY]
    for discovery in discoveries:
        if discovery[ATTR_UL_IP_ADDRESS] == host:
            return discovery
    return None


@callback
def async_clear_discovery_cache(hass: HomeAssistant, host: str) -> None:
    """Clear the host from the discovery cache."""
    domain_data = hass.data[DOMAIN]
    discoveries: list[UniledDiscovery] = domain_data[UNILED_DISCOVERY]
    domain_data[UNILED_DISCOVERY] = [
        discovery for discovery in discoveries if discovery[ATTR_UL_IP_ADDRESS] != host
    ]


@callback
def async_name_from_discovery(device: UniledDiscovery) -> str:
    """Convert a UNILED discovery to a human readable name."""
    return UniledDevice.human_readable_name(
        None,
        device[ATTR_UL_LOCAL_NAME],
        device[ATTR_UL_MAC_ADDRESS],
    )


@callback
def async_populate_data_from_discovery(
    current_data: Mapping[str, Any],
    data_updates: dict[str, Any],
    device: UniledDiscovery,
) -> None:
    """Copy discovery data into config entry data."""
    for conf_key, discovery_key in CONF_TO_DISCOVERY.items():
        if (
            device.get(discovery_key) is not None
            and conf_key not in data_updates
            and current_data.get(conf_key) != device[discovery_key]  # type: ignore[literal-required]
        ):
            data_updates[conf_key] = device[discovery_key]  # type: ignore[literal-required]


@callback
def async_update_entry_from_discovery(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    device: UniledDiscovery,
    allow_update_mac: bool = False,
) -> bool:
    """Update a config entry from a UNILED discovery."""
    data_updates: dict[str, Any] = {}
    mac_address = device[ATTR_UL_MAC_ADDRESS]
    assert mac_address is not None
    formatted_mac = dr.format_mac(mac_address)
    updates: dict[str, Any] = {}

    if not entry.unique_id or (
        allow_update_mac
        and entry.unique_id != formatted_mac
        and UniledDevice.mac_matches_by_one(formatted_mac, entry.unique_id)
    ):
        updates["unique_id"] = formatted_mac
    async_populate_data_from_discovery(entry.data, data_updates, device)

    device_title = async_name_from_discovery(device)
    title_matches_name = entry.title == device_title
    if not title_matches_name:
        updates["title"] = device_title

    # _LOGGER.error(entry.title)
    # _LOGGER.error(entry.data)
    # _LOGGER.error(data_updates)
    # _LOGGER.error(device)

    if data_updates or title_matches_name:
        _LOGGER.debug("Update entry: %s", data_updates)
        updates["data"] = {**entry.data, **data_updates}

    # If the title has changed and the config entry is loaded, a listener is
    # in place, and we should not reload
    if updates and not ("title" in updates and entry.state is ConfigEntryState.LOADED):
        return hass.config_entries.async_update_entry(entry, **updates)
    return False
