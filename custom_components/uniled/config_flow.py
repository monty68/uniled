"""Config flow for UniLED integration."""
from __future__ import annotations
from typing import Any

from homeassistant import config_entries as flow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.components import onboarding
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_DEVICE, CONF_ADDRESS, CONF_MODEL

from .lib.ble.device import UniledBleDevice, UniledBleModel, UNILED_TRANSPORT_BLE
from .lib.net.device import UniledNetDevice, UniledNetModel, UNILED_TRANSPORT_NET

# from .lib.zng.device import UniledZngDevice, UNILED_TRANSPORT_ZNG
from .const import DOMAIN, UNILED_DEVICE_RETRYS, CONF_RETRY_COUNT

import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)


class UniledConfigFlowHandler(flow.ConfigFlow, domain=DOMAIN):
    """Handle a UniLED config flow."""

    VERSION = 1

    # @staticmethod
    # @callback
    # def async_get_options_flow(
    #    config_entry: flow.ConfigEntry,
    # ) -> UniledOptionsFlowHandler:
    #    """Get the options flow for this handler."""
    #    return UniledOptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_ble_info: BluetoothServiceInfoBleak | None = None
        self._discovered_ble_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        if not await self._async_ble_check_device(discovery):
            return self.async_abort(reason="not_supported")
        
        await self.async_set_unique_id(discovery.address)
        self._abort_if_unique_id_configured()
        self._discovery_ble_info = discovery

        return await self.async_step_bluetooth_confirm()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            discovery = self._discovered_ble_devices[address]

            await self.async_set_unique_id(discovery.address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            if not await self._async_ble_check_device(discovery):
                return self.async_abort(reason="not_supported")
            return self._async_ble_create_entry()

        if discovery := self._discovery_ble_info:
            self._discovered_ble_devices[discovery.address] = discovery
        else:
            current_addresses = self._async_current_ids()
            for discovery in async_discovered_service_info(self.hass):
                if (
                    discovery.address in current_addresses
                    or discovery.address in self._discovered_ble_devices
                    or not (
                        model := UniledBleDevice.match_known_device(
                            discovery.device, discovery.advertisement
                        )
                    )
                ):
                    continue
                self._discovered_ble_devices[discovery.address] = discovery

        if not self._discovered_ble_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            service_info.address: f"{service_info.name} ({service_info.address})"
                            for service_info in self._discovered_ble_devices.values()
                        }
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None or not onboarding.async_is_onboarded(self.hass):
            return self._async_ble_create_entry()

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context["title_placeholders"],
        )

    async def _async_ble_check_device(
        self, discovery: BluetoothServiceInfoBleak
    ) -> bool:
        """Check device device is support"""
        transport = UNILED_TRANSPORT_BLE

        if (
            model := UniledBleDevice.match_known_device(
                discovery.device, discovery.advertisement
            )
        ) is None:
            return False

        self.context["title_placeholders"] = {
            "name": UniledBleDevice.human_readable_name(
                None, discovery.name, discovery.address
            )
        }
        self.context[CONF_ADDRESS] = discovery.address
        self.context[CONF_MODEL] = (
            model.model_name if isinstance(model, UniledBleModel) else None
        )
        self.context[CONF_DEVICE_CLASS] = transport

        return True

    def _async_ble_create_entry(self):
        """Get/Create entry"""
        model = self.context.get(CONF_MODEL, None)
        address = self.context.get(CONF_ADDRESS, "")
        transport = self.context.get(CONF_DEVICE_CLASS, "")

        return self.async_create_entry(
            title=self.context["title_placeholders"]["name"],
            data={
                CONF_DEVICE_CLASS: transport,
                CONF_ADDRESS: address,
                CONF_MODEL: model,
            },
        )


class UniledOptionsFlowHandler(flow.OptionsFlow):
    """Handle Uniled options flow."""

    def __init__(self, config_entry: flow.ConfigEntry) -> None:
        """Initialize UniLED options flow."""
        self.config_entry = config_entry
