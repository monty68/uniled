"""The UniLED integration."""

from __future__ import annotations

from typing import Any, Final, cast

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.match import (
    BluetoothCallbackMatcher,
    MANUFACTURER_ID,
    ADDRESS,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback, CoreState
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.entity_registry import async_get, async_migrate_entries
from homeassistant.helpers.event import (
    async_track_time_change,
    async_track_time_interval,
)
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.const import (
    CONF_ADDRESS,
    CONF_COUNTRY,
    CONF_HOST,
    CONF_MODEL,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from .lib.zng.manager import (
    CONF_ZNG_ACTIVE_SCAN as CONF_ACTIVE_SCAN,
    CONF_ZNG_MESH_ID as CONF_MESH_ID,
    CONF_ZNG_MESH_UUID as CONF_MESH_UUID,
    UNILED_TRANSPORT_ZNG,
    ZENGGE_MANUFACTURER_ID,
    ZenggeManager,
)
from .lib.ble.device import (
    UNILED_TRANSPORT_BLE,
    UniledBleDevice,
    close_stale_connections,
    get_device,
)
from .lib.net.device import (
    UNILED_TRANSPORT_NET,
    UniledNetDevice,
)
from .discovery import (
    UniledDiscovery,
    async_build_cached_discovery,
    async_clear_discovery_cache,
    async_get_discovery,
    async_discover_device,
    async_discover_devices,
    async_trigger_discovery,
    async_update_entry_from_discovery,
)
from .const import (
    DOMAIN,
    ATTR_UL_MAC_ADDRESS,
    CONF_UL_RETRY_COUNT as CONF_RETRY_COUNT,
    CONF_UL_TRANSPORT as CONF_TRANSPORT,
    CONF_UL_UPDATE_INTERVAL as CONF_UPDATE_INTERVAL,
    UNILED_COMMAND_SETTLE_DELAY,
    UNILED_DEVICE_RETRYS as DEFAULT_RETRY_COUNT,
    UNILED_UPDATE_SECONDS as DEFAULT_UPDATE_INTERVAL,
    UNILED_DEVICE_TIMEOUT,
    UNILED_OPTIONS_ATTRIBUTES,
    UNILED_DISCOVERY,
    UNILED_DISCOVERY_SIGNAL,
    UNILED_DISCOVERY_INTERVAL,
    UNILED_DISCOVERY_STARTUP_TIMEOUT,
    UNILED_DISCOVERY_SCAN_TIMEOUT,
    # UNILED_SIGNAL_STATE_UPDATED,
)

from .coordinator import UniledUpdateCoordinator

import async_timeout
import gc
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SCENE,
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.BUTTON,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the UNILED component."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data[UNILED_DISCOVERY] = await async_discover_devices(
        hass, UNILED_DISCOVERY_STARTUP_TIMEOUT
    )

    @callback
    def _async_start_background_discovery(*_: Any) -> None:
        """Run discovery in the background."""
        hass.async_create_background_task(_async_discovery(), UNILED_DISCOVERY)

    async def _async_discovery(*_: Any) -> None:
        async_trigger_discovery(
            hass, await async_discover_devices(hass, UNILED_DISCOVERY_SCAN_TIMEOUT)
        )

    async_trigger_discovery(hass, domain_data[UNILED_DISCOVERY])

    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STARTED, _async_start_background_discovery
    )

    async_track_time_interval(
        hass,
        _async_start_background_discovery,
        UNILED_DISCOVERY_INTERVAL,
        cancel_on_shutdown=True,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UNILED from a config entry."""
    transport: str = entry.data.get(CONF_TRANSPORT)

    if transport == UNILED_TRANSPORT_ZNG:
        mesh_id: str = entry.data.get(CONF_MESH_ID)
        mesh_uuid: str = entry.data.get(CONF_MESH_UUID, 0)
        mesh_user: str = entry.data.get(CONF_USERNAME, "")
        mesh_pass: str = entry.data.get(CONF_PASSWORD, "")
        mesh_area: str = entry.data.get(CONF_COUNTRY, "")
        scan_mode = (
            bluetooth.BluetoothScanningMode.ACTIVE
            if entry.options.get(CONF_ACTIVE_SCAN, True)
            else bluetooth.BluetoothScanningMode.PASSIVE
        )

        uniled = ZenggeManager(
            mesh_id, mesh_uuid, mesh_user, mesh_pass, mesh_area, entry.options
        )

        coordinator = UniledUpdateCoordinator(hass, uniled, entry)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

        _LOGGER.debug(
            "*** Added UniLED entry for: %s - %s (%s) %s HASS: %s",
            coordinator.device.name,
            entry.unique_id,
            entry.entry_id,
            scan_mode,
            hass.state,
        )

        @callback
        async def _async_startup(event=None) -> None:
            """Startup"""
            await coordinator.device.startup()
            try:
                await coordinator.async_config_entry_first_refresh()
                await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
            except ConfigEntryNotReady:
                _LOGGER.debug(
                    "%s: First update attempt failed!", coordinator.device.name
                )
                await _async_shutdown_coordinator(hass, coordinator)
                if hass.state != CoreState.running:
                    raise

        @callback
        def _async_ble_sniffer(
            service_info: bluetooth.BluetoothServiceInfoBleak,
            change: bluetooth.BluetoothChange,
        ) -> None:
            """Update from a ble callback."""
            coordinator.device.set_device_and_advertisement(
                service_info.device, service_info.advertisement
            )

        entry.async_on_unload(
            bluetooth.async_register_callback(
                hass,
                _async_ble_sniffer,
                BluetoothCallbackMatcher({MANUFACTURER_ID: ZENGGE_MANUFACTURER_ID}),
                scan_mode,
            )
        )

        entry.async_on_unload(
            hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STOP, coordinator.device.shutdown
            )
        )

        entry.async_on_unload(entry.add_update_listener(_async_update_listener))

        if hass.state == CoreState.running:
            await _async_startup()
        else:
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _async_startup)

        return True
    elif transport == UNILED_TRANSPORT_BLE:
        address: str = str(entry.data[CONF_ADDRESS]).upper()
        model_name: str = entry.data.get(CONF_MODEL, None)

        ble_device = bluetooth.async_ble_device_from_address(
            hass, address, True
        ) or await get_device(address)

        if not ble_device:
            raise ConfigEntryNotReady(
                f"Could not find BLE device with address {address}"
            )

        await close_stale_connections(ble_device)

        service_info = bluetooth.async_last_service_info(
            hass, address, connectable=True
        )

        if not service_info:
            bluetooth.async_rediscover_address(hass, address)
            raise ConfigEntryNotReady(
                f"Could not find service info for BLE device with address {address}"
            )

        _LOGGER.debug(
            "*** Setup UniLED BLE Device: %s v%s - %s %s",
            ble_device,
            entry.version,
            entry.data,
            service_info.advertisement,
        )

        uniled = UniledBleDevice(
            entry.options, ble_device, service_info.advertisement, model_name
        )

        if not uniled.model:
            model = await uniled.resolve_model(model_name is None, False)
            if model is None:
                raise ConfigEntryError(
                    f"Could not resolve model for BLE device with address {address}"
                )

        if uniled.model_name != model_name:
            new = {**entry.data}
            new[CONF_MODEL] = uniled.model_name
            hass.config_entries.async_update_entry(entry, data=new)
            _LOGGER.debug("%s: Updated HASS configuration: %s.", uniled.name, new)

        @callback
        def _async_update_ble(
            service_info: bluetooth.BluetoothServiceInfoBleak,
            change: bluetooth.BluetoothChange,
        ) -> None:
            """Update from a ble callback."""
            uniled.set_device_and_advertisement(
                service_info.device, service_info.advertisement
            )

        entry.async_on_unload(
            bluetooth.async_register_callback(
                hass,
                _async_update_ble,
                BluetoothCallbackMatcher({ADDRESS: address}),
                bluetooth.BluetoothScanningMode.PASSIVE,
            )
        )

    elif transport == UNILED_TRANSPORT_NET:
        discovery_cached = True
        host = entry.data[CONF_HOST]
        if discovery := async_get_discovery(hass, host):
            discovery_cached = False
        else:
            discovery = async_build_cached_discovery(entry)
        uniled = UniledNetDevice(discovery=discovery, options=entry.options)
        if not uniled.model:
            raise ConfigEntryError(f"Could not resolve model for device {host}")
    else:
        raise ConfigEntryError(
            f"Unable to communicate with device of unknown transport class: {transport}"
        )

    coordinator = UniledUpdateCoordinator(hass, uniled, entry)
    if not await coordinator.device.startup():
        raise ConfigEntryNotReady("Failed to startup")

    if not coordinator.device.available:
        ## Device is not available, so attempt first connection
        startup_event = asyncio.Event()
        cancel_first_update = coordinator.device.register_callback(
            lambda *_: startup_event.set()
        )
        _LOGGER.debug(
            "*** Awaiting UniLED Device: %s, first response...", coordinator.device.name
        )

        try:
            await coordinator.async_config_entry_first_refresh()
        except ConfigEntryNotReady:
            _LOGGER.warning("%s: First update attempt failed!", coordinator.device.name)
            cancel_first_update()
            await _async_shutdown_coordinator(hass, coordinator)
            del coordinator
            gc.collect()
            raise

        try:
            async with async_timeout.timeout(UNILED_DEVICE_TIMEOUT):
                await startup_event.wait()
                cancel_first_update()
                _LOGGER.debug(
                    "*** Response from UniLED Device: %s", coordinator.device.name
                )

        except asyncio.TimeoutError as ex:
            cancel_first_update()
            await _async_shutdown_coordinator(hass, coordinator)
            del coordinator
            gc.collect()
            raise ConfigEntryNotReady("No response from device") from ex
            return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def _async_stop(event: Event) -> None:
        """Close the connection."""
        await _async_shutdown_coordinator(hass, coordinator)

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )

    if transport == UNILED_TRANSPORT_NET:
        # UDP probe after successful connect only
        if discovery_cached:
            if directed_discovery := await async_discover_device(hass, host):
                uniled.discovery = discovery = directed_discovery
                discovery_cached = False

        if entry.unique_id and discovery.get(ATTR_UL_MAC_ADDRESS):
            mac = uniled.format_mac(cast(str, discovery[ATTR_UL_MAC_ADDRESS]))
            if not uniled.mac_matches_by_one(mac, entry.unique_id):
                # The device is offline and another device is now using the ip address
                raise ConfigEntryNotReady(
                    f"Unexpected device found at {host}; Expected {entry.unique_id}, found"
                    f" {mac}"
                )

        if not discovery_cached:
            # Only update the entry once we have verified the unique id
            # is either missing or we have verified it matches
            async_update_entry_from_discovery(
                hass, entry, discovery, uniled.model_name, True
            )

        async def _async_handle_discovered_device() -> None:
            """Handle device discovery."""
            # Force a refresh if the device is now available
            if not coordinator.last_update_success:
                coordinator.force_next_update = True
                await coordinator.async_refresh()

        entry.async_on_unload(
            async_dispatcher_connect(
                hass,
                UNILED_DISCOVERY_SIGNAL.format(entry_id=entry.entry_id),
                _async_handle_discovered_device,
            )
        )

    _LOGGER.debug(
        "*** Added UniLED device entry for: %s, ID: %s, Unique ID: %s",
        uniled.name,
        entry.entry_id,
        entry.unique_id,
    )

    return True


async def _async_shutdown_coordinator(
    hass: HomeAssistant, coordinator: UniledUpdateCoordinator, rediscover: bool = True
) -> None:
    """Shutdown coordinator device"""
    await coordinator.device.shutdown()
    if (
        coordinator.device.transport != UNILED_TRANSPORT_NET
        and coordinator.device.address
        and rediscover
    ):
        bluetooth.async_rediscover_address(hass, coordinator.device.address)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: UniledUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.info(
        "%s: Reloading due to config/options update...", coordinator.device.name
    )
    await asyncio.sleep(UNILED_COMMAND_SETTLE_DELAY)
    await _async_shutdown_coordinator(hass, coordinator, rediscover=False)
    await asyncio.sleep(UNILED_COMMAND_SETTLE_DELAY * 3)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry) -> bool:
    """Unload a config entry."""
    coordinator = None
    if entry.entry_id in hass.data[DOMAIN]:
        coordinator: UniledUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        _LOGGER.info("%s: Unloading...", coordinator.device.name)
        await coordinator.device.shutdown()

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if coordinator:
            if coordinator.device.transport != UNILED_TRANSPORT_NET:
                bluetooth.async_rediscover_address(hass, coordinator.device.address)
            elif coordinator.device.transport == UNILED_TRANSPORT_NET:
                # Make sure we probe the device again in case something has changed externally
                async_clear_discovery_cache(hass, entry.data[CONF_HOST])
            del coordinator
        gc.collect()

    return unload_ok


async def async_migrate_entry(hass, entry):
    """Migrate old entry."""
    if entry.version == 1:
        # Miserable, but needed :-(
        _LOGGER.error(
            "UniLED is unable to migrate this entities configuration, remove and re-install."
        )
        return False

    if entry.version == 2:
        ent_reg = async_get(hass)
        for entity in list(ent_reg.entities.values()):
            if entity.config_entry_id != entry.entry_id:
                continue
            if not ent_reg.entities.get_entry(entity.id):
                continue
            trash = UNILED_OPTIONS_ATTRIBUTES
            trash.extend([f"scene.{s}" for s in range(9)])
            for attr in trash:
                if entity.unique_id.endswith(attr):
                    _LOGGER.warn(f"Removing redundent entity: {entity.unique_id}")
                    ent_reg.async_remove(entity.entity_id)
                    break
        entry.version = 3
        _LOGGER.info("Migration to version %s successful", entry.version)

    return True
