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

    #@staticmethod
    #@callback
    #def async_get_options_flow(
    #    config_entry: flow.ConfigEntry,
    #) -> UniledOptionsFlowHandler:
    #    """Get the options flow for this handler."""
    #    return UniledOptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_ble_info: BluetoothServiceInfoBleak | None = None
        self._discovered_ble_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        transport = UNILED_TRANSPORT_BLE

        if (
            model := UniledBleDevice.match_known_device(
                discovery_info.device, discovery_info.advertisement
            )
        ) is None:
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovery_ble_info = discovery_info

        self.context["title_placeholders"] = {
            "name": UniledBleDevice.human_readable_name(
                None, discovery_info.name, discovery_info.address
            )
        }
        self.context[CONF_ADDRESS] = discovery_info.address
        self.context[CONF_MODEL] = model.model_name if isinstance(model, UniledBleModel) else None
        self.context[CONF_DEVICE_CLASS] = transport

        return await self.async_step_bluetooth_confirm()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug("User Input: %s", user_input)
            return self.async_abort(reason="not_supported")

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

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None or not onboarding.async_is_onboarded(self.hass):
            return self._async_create_entry()

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context["title_placeholders"],
        )

    def _async_create_entry(self, model=None):
        """Get/Create entry"""
        if self.context.get("source") != "bluetooth":
            return self.async_abort(reason="not_supported")

        address = self.context.get(CONF_ADDRESS, "")
        transport = self.context.get(CONF_DEVICE_CLASS, "")

        _LOGGER.warning("Address: %s", address)
        _LOGGER.warning(self.context)

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
