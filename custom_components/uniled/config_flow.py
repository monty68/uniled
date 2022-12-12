"""Config flow for UniLED integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from typing import Any

from homeassistant.data_entry_flow import FlowResult
from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS, CONF_DEVICE_CLASS, CONF_MODEL
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
    # async_rediscover_address,
)
from bleak_retry_connector import BLEAK_RETRY_EXCEPTIONS as BLEAK_EXCEPTIONS
from .const import DOMAIN
from .lib.ble_device import UNILEDBLE
from .lib.models_db import (
    UNILED_TRANSPORT_BLE,
    # UNILED_TRANSPORT_NET,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BTF Bluetooth Controller."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": UNILEDBLE.human_readable_name(
                None, discovery_info.name, discovery_info.address
            )
        }
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug("User Input: %s", user_input)
            address = user_input[CONF_ADDRESS]
            discovery = self._discovered_devices[address]
            local_name = discovery.name

            await self.async_set_unique_id(discovery.address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            uniled = UNILEDBLE(discovery.device, discovery.advertisement, local_name)

            try:
                model = await uniled.resolve_model(do_disconnect=True)
            except BLEAK_EXCEPTIONS:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"
            else:
                if model is not None:
                    return self.async_create_entry(
                        title=discovery.name,
                        data={
                            CONF_DEVICE_CLASS: UNILED_TRANSPORT_BLE,
                            CONF_ADDRESS: discovery.address,
                            CONF_MODEL: model.model_name,
                        },
                    )
                return self.async_abort(reason="not_supported")

        if discovery := self._discovery_info:
            if UNILEDBLE.match_known_service(discovery.device, discovery.advertisement):
                _LOGGER.debug("Setting discovery: %s", discovery)
                self._discovered_devices[discovery.address] = discovery
        else:
            current_addresses = self._async_current_ids()
            for discovery in async_discovered_service_info(self.hass):
                if (
                    discovery.address in current_addresses
                    or discovery.address in self._discovered_devices
                    or not UNILEDBLE.match_known_service(
                        discovery.device, discovery.advertisement
                    )
                ):
                    continue
                self._discovered_devices[discovery.address] = discovery

        if not self._discovered_devices:
            return self.async_abort(reason="no_unconfigured_devices")

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): vol.In(
                    {
                        service_info.address: f"{service_info.name} ({service_info.address})"
                        for service_info in self._discovered_devices.values()
                    }
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
