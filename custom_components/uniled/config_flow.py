"""Config flow for UniLED integration."""
from __future__ import annotations
from typing import Any

from homeassistant import config_entries as flow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.components import onboarding
from homeassistant.components.bluetooth import (
    async_discovered_service_info,
    BluetoothServiceInfoBleak,
)
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from homeassistant.const import (
    CONF_ADDRESS,
    CONF_COUNTRY,
    CONF_DEVICES,
    CONF_HOST,
    CONF_IP_ADDRESS,
    CONF_LOCATION,
    CONF_MODEL,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_USERNAME,
)
from .lib.net.device import UNILED_TRANSPORT_NET, UniledNetDevice, UniledNetModel
from .lib.ble.device import UNILED_TRANSPORT_BLE, UniledBleDevice, UniledBleModel
from .lib.zng.cloud import MagicHue, MAGICHUE_DEFAULT_COUNTRY
from .lib.zng.manager import (
    CONF_ZNG_ACTIVE_SCAN as CONF_ACTIVE_SCAN,
    CONF_ZNG_MESH_DATA as CONF_MESH_DATA,
    CONF_ZNG_MESH_ID as CONF_MESH_ID,
    CONF_ZNG_MESH_KEY as CONF_MESH_KEY,
    CONF_ZNG_MESH_NAME as CONF_MESH_NAME,
    CONF_ZNG_MESH_PASS as CONF_MESH_PASS,
    CONF_ZNG_MESH_TOKEN as CONF_MESH_TOKEN,
    UNILED_TRANSPORT_ZNG,
    ZENGGE_UPDATE_SECONDS as DEFAULT_MESH_UPDATE_INTERVAL,
    ZENGGE_DESCRIPTION,
    ZenggeManager,
)
from .const import (
    DOMAIN,
    CONF_UL_RETRY_COUNT as CONF_RETRY_COUNT,
    CONF_UL_TRANSPORT as CONF_TRANSPORT,
    CONF_UL_UPDATE_INTERVAL as CONF_UPDATE_INTERVAL,
    UNILED_MIN_DEVICE_RETRYS as MIN_DEVICE_RETRYS,
    UNILED_DEF_DEVICE_RETRYS as DEFAULT_RETRY_COUNT,
    UNILED_MAX_DEVICE_RETRYS as MAX_DEVICE_RETRYS,
    UNILED_MIN_UPDATE_INTERVAL as MIN_UPDATE_INTERVAL,
    UNILED_DEF_UPDATE_INTERVAL as DEFAULT_UPDATE_INTERVAL,
    UNILED_MAX_UPDATE_INTERVAL as MAX_UPDATE_INTERVAL,
)
import voluptuous as vol
import functools
import operator
import time
import logging

_LOGGER = logging.getLogger(__name__)


class UniledConfigFlowHandler(flow.ConfigFlow, domain=DOMAIN):
    """Handle a UniLED config flow."""

    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: flow.ConfigEntry,
    ) -> UniledOptionsFlowHandler:
        """Get the options flow for this handler."""
        return UniledOptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_ble_info: BluetoothServiceInfoBleak | None = None
        self._discovered_ble_devices: dict[str, BluetoothServiceInfoBleak] = {}
        self._discovered_zng_meshes: dict[str, int] = {}

    async def async_step_bluetooth(
        self, discovery: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        if not await self._async_bluetooth_check_device(discovery):
            return self.async_abort(reason="not_supported")
        if (
            transport := self.context.get(CONF_TRANSPORT, None)
        ) == UNILED_TRANSPORT_BLE:
            self._discovery_ble_info = discovery
            return await self.async_step_bluetooth_confirm()
        elif transport == UNILED_TRANSPORT_ZNG:
            return await self.async_step_mesh_cloud()
        return self.async_abort(reason="not_supported")

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm BLE discovery."""
        if user_input is not None or not onboarding.async_is_onboarded(self.hass):
            return self._async_bluetooth_create_entry()
        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context["title_placeholders"],
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]

            if address in self._discovered_zng_meshes:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                mesh_id = self._discovered_zng_meshes[address]
                self.context[CONF_TRANSPORT] = UNILED_TRANSPORT_ZNG
                self.context[CONF_MESH_ID] = mesh_id
                self.context[CONF_MESH_NAME] = address
                self.context["title_placeholders"] = {
                    "name": f"{ZENGGE_DESCRIPTION} ({hex(mesh_id)})",
                }
                return await self.async_step_mesh_cloud()

            discovery = self._discovered_ble_devices[address]
            if not await self._async_bluetooth_check_device(
                discovery, raise_on_progress=False
            ):
                return self.async_abort(reason="not_supported")
            return self._async_bluetooth_create_entry()

        if discovery := self._discovery_ble_info:
            self._discovered_ble_devices[discovery.address] = discovery
        else:
            current_addresses = self._async_current_ids()
            for discovery in async_discovered_service_info(self.hass):
                mesh_id, mesh_name = ZenggeManager.mesh_id_name(
                    discovery.device, discovery.advertisement
                )
                if mesh_id is not None:
                    _LOGGER.info(
                        "Discovered '%s' mesh '%s' device",
                        discovery.address,
                        hex(mesh_id),
                    )
                    if mesh_name in self._async_current_ids():
                        continue
                    if mesh_name not in self._discovered_zng_meshes:
                        self._discovered_zng_meshes[mesh_name] = mesh_id
                    continue
                elif (
                    discovery.address in current_addresses
                    or discovery.address in self._discovered_ble_devices
                    or (
                        model := UniledBleDevice.match_known_device(
                            discovery.device, discovery.advertisement
                        )
                    )
                    is None
                ):
                    continue
                self._discovered_ble_devices[discovery.address] = discovery
                _LOGGER.info("Discovered '%s' ble device", discovery.address)

        if not self._discovered_ble_devices and not self._discovered_zng_meshes:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        dict(
                            functools.reduce(
                                operator.or_,
                                [
                                    {
                                        mesh_token: f"{ZENGGE_DESCRIPTION} ({hex(mesh_id)})"
                                        for mesh_token, mesh_id in self._discovered_zng_meshes.items()
                                    },
                                    {
                                        service_info.address: f"{service_info.name} ({service_info.address})"
                                        for service_info in self._discovered_ble_devices.values()
                                    },
                                ],
                            )
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_mesh_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the step to connect to mesh cloud."""
        cloud_username: str = self.context.get(CONF_USERNAME, "")
        cloud_password: str = self.context.get(CONF_PASSWORD, "")
        cloud_county: str = self.context.get(CONF_COUNTRY, MAGICHUE_DEFAULT_COUNTRY)
        cloud_location: str = self.context.get(CONF_LOCATION, "")
        mesh_id: str = self.context.get(CONF_MESH_ID, "")
        mesh_token: str = self.context.get(CONF_MESH_TOKEN, "")
        errors = {}

        if user_input is not None:
            cloud_username: str = user_input.get(CONF_USERNAME, "")
            cloud_password: str = user_input.get(CONF_PASSWORD, "")
            cloud_county: str = user_input.get(CONF_COUNTRY, "US")
            cloud = MagicHue(cloud_username, cloud_password, cloud_county)
            if not errors and await cloud.login() is not True:
                errors[CONF_PASSWORD] = "mesh_login"
            if not errors and await cloud.get_meshes() is not True:
                errors[CONF_COUNTRY] = "mesh_fetch"
            if not errors and await cloud.get_devices() is not True:
                errors[CONF_COUNTRY] = "mesh_devices"
            else:
                self.context[CONF_USERNAME] = cloud_username
                self.context[CONF_PASSWORD] = cloud_password
                self.context[CONF_COUNTRY] = cloud.country
                self.context[CONF_MESH_DATA] = cloud.meshes

                if len(cloud.meshes) == 1:
                    if len(cloud.meshes[0]["deviceList"]):
                        return self.async_abort(reason="mesh_no_devices")
                    self.context[CONF_LOCATION] = cloud.meshes[0]["placeUniID"]
                    self.context[CONF_MESH_KEY] = cloud.meshes[0]["meshKey"]
                    self.context[CONF_MESH_PASS] = cloud.meshes[0]["meshPassword"]
                    self.context[CONF_MESH_TOKEN] = cloud.meshes[0]["meshLTK"]
                    self.context[CONF_DEVICES] = cloud.meshes[0]["deviceList"]
                    return await self.async_step_mesh_config()
                elif len(cloud.meshes) > 1:
                    return await self.async_step_mesh_location()
                else:
                    return self.async_abort(reason="mesh_no_locations")

        if user_input is None or errors:
            return self.async_show_form(
                step_id="mesh_cloud",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_USERNAME, default=cloud_username): str,
                        vol.Required(CONF_PASSWORD, default=cloud_password): str,
                        vol.Required(
                            CONF_COUNTRY, default=cloud_county
                        ): SelectSelector(
                            SelectSelectorConfig(
                                mode=SelectSelectorMode.DROPDOWN,
                                options=[
                                    SelectOptionDict(value=k, label=v)
                                    for k, v in MagicHue.countries()
                                ],
                            )
                        ),
                    }
                ),
                errors=errors,
            )
        return self.async_abort(reason="mesh_not_supported")

    async def async_step_mesh_location(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the step to select mesh location."""
        mesh_location: str = self.context.get(CONF_LOCATION, "")
        mesh_data = self.context.get(CONF_MESH_DATA, None)
        locations = {}
        errors = {}

        if not mesh_data or not len(mesh_data):
            return self.async_abort(reason="mesh_no_locations")

        if user_input is not None:
            _LOGGER.debug(user_input)
            mesh_location = user_input.get(CONF_LOCATION)
            for location in mesh_data:
                if location["placeUniID"] != mesh_location:
                    continue
                if len(location["deviceList"]):
                    self.context[CONF_LOCATION] = location["placeUniID"]
                    self.context[CONF_DEVICES] = location["deviceList"]
                    self.context[CONF_MESH_KEY] = location["meshKey"]
                    self.context[CONF_MESH_PASS] = location["meshPassword"]
                    self.context[CONF_MESH_TOKEN] = location["meshLTK"]
                    return await self.async_step_mesh_config()
                else:
                    errors[CONF_LOCATION] = "mesh_no_devices"

        for location in mesh_data:
            locations[location["placeUniID"]] = location["displayName"]

        return self.async_show_form(
            step_id="mesh_location",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOCATION, default=mesh_location): vol.In(
                        locations
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_mesh_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the step to configure a mesh."""
        mesh_key: str = self.context.get(CONF_MESH_KEY, "")
        mesh_pass: str = self.context.get(CONF_MESH_PASS, "")
        mesh_token: str = self.context.get(CONF_MESH_TOKEN, "")
        errors = {}

        if user_input is not None:
            mesh_key = user_input.get(CONF_MESH_KEY)
            if len(mesh_key) > 16:
                errors[CONF_MESH_KEY] = "max_length_16"
            mesh_pass = user_input.get(CONF_MESH_PASS)
            if len(mesh_pass) > 16:
                errors[CONF_MESH_PASS] = "max_length_16"
            mesh_token = user_input.get(CONF_MESH_TOKEN)
            if len(mesh_token) > 16:
                errors[CONF_MESH_TOKEN] = "max_length_16"

            if not errors:
                self.context[CONF_MESH_KEY] = mesh_key
                self.context[CONF_MESH_PASS] = mesh_pass
                self.context[CONF_MESH_TOKEN] = mesh_token
                return self._async_mesh_create_entry()

        if user_input is None or errors:
            # Skip to creating entry!
            if mesh_key and mesh_pass and mesh_token:
                return self._async_mesh_create_entry()

            return self.async_show_form(
                step_id="mesh_config",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_MESH_KEY, default=mesh_key): str,
                        vol.Required(CONF_MESH_PASS, default=mesh_pass): str,
                        vol.Required(CONF_MESH_TOKEN, default=mesh_token): str,
                    }
                ),
                errors=errors,
            )

        return self._async_mesh_create_entry()

    def _async_mesh_create_entry(self):
        """Get/Create entry"""
        return self.async_create_entry(
            title=self.context["title_placeholders"]["name"],
            data={
                CONF_TRANSPORT: self.context.get(CONF_TRANSPORT, UNILED_TRANSPORT_ZNG),
                CONF_MESH_NAME: self.context.get(CONF_MESH_NAME, None),
                CONF_MESH_ID: self.context.get(CONF_MESH_ID, None),
                CONF_MESH_KEY: self.context.get(CONF_MESH_KEY, None),
                CONF_MESH_PASS: self.context.get(CONF_MESH_PASS, None),
                CONF_MESH_TOKEN: self.context.get(CONF_MESH_TOKEN, None),
            },
            options={
                CONF_UPDATE_INTERVAL: DEFAULT_MESH_UPDATE_INTERVAL,
                CONF_RETRY_COUNT: DEFAULT_RETRY_COUNT,
                CONF_ACTIVE_SCAN: True,
                CONF_COUNTRY: self.context.get(CONF_COUNTRY, MAGICHUE_DEFAULT_COUNTRY),
                CONF_USERNAME: self.context.get(CONF_USERNAME, None),
                CONF_PASSWORD: self.context.get(CONF_PASSWORD, None),
                CONF_LOCATION: self.context.get(CONF_LOCATION, None),
                CONF_DEVICES: self.context.get(CONF_DEVICES, None),
            },
        )

    async def _async_bluetooth_check_device(
        self, discovery: BluetoothServiceInfoBleak, raise_on_progress: bool = True
    ) -> bool:
        """Check device device is support"""
        mesh_id, mesh_name = ZenggeManager.mesh_id_name(
            discovery.device, discovery.advertisement
        )
        if mesh_id is not None:
            if mesh_name not in self._discovered_zng_meshes:
                self._discovered_zng_meshes[mesh_name] = mesh_id
                await self.async_set_unique_id(
                    mesh_name, raise_on_progress=raise_on_progress
                )
                self._abort_if_unique_id_configured()

                self.context[CONF_TRANSPORT] = UNILED_TRANSPORT_ZNG
                self.context[CONF_MESH_ID] = mesh_id
                self.context[CONF_MESH_NAME] = mesh_name
                self.context["title_placeholders"] = {
                    "name": f"{ZENGGE_DESCRIPTION} ({hex(mesh_id)})",
                }
                return True
            return False
        elif (
            model := UniledBleDevice.match_known_device(
                discovery.device, discovery.advertisement
            )
        ) is not None:
            await self.async_set_unique_id(
                discovery.address, raise_on_progress=raise_on_progress
            )
            self._abort_if_unique_id_configured()
            self.context[CONF_TRANSPORT] = UNILED_TRANSPORT_BLE
            self.context[CONF_ADDRESS] = discovery.address
            self.context[CONF_MODEL] = (
                model.model_name if isinstance(model, UniledBleModel) else None
            )
            self.context["title_placeholders"] = {
                "name": UniledBleDevice.human_readable_name(
                    None, discovery.name, discovery.address
                )
            }
            return True
        return False

    def _async_bluetooth_create_entry(self):
        """Get/Create entry"""
        _LOGGER.debug(self.context)

        return self.async_create_entry(
            title=self.context["title_placeholders"]["name"],
            data={
                CONF_TRANSPORT: self.context.get(CONF_TRANSPORT, ""),
                CONF_ADDRESS: self.context.get(CONF_ADDRESS, ""),
                CONF_MODEL: self.context.get(CONF_MODEL, None),
            },
            options={
                CONF_RETRY_COUNT: DEFAULT_RETRY_COUNT,
                CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
            },
        )


class UniledOptionsFlowHandler(flow.OptionsFlowWithConfigEntry):
    """Handle Uniled options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        _LOGGER.debug(self.config_entry.data)
        if self.config_entry.data.get(CONF_TRANSPORT) == UNILED_TRANSPORT_ZNG:
            return await self.async_step_menu()
        return await self.async_step_tune()

    async def async_step_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Menu step"""
        return self.async_show_menu(
            step_id="menu",
            menu_options=["tune", "mesh"],
            description_placeholders={
                "model": "Example model",
            }
        )

    async def async_step_mesh(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Mesh step"""
        cloud_username = self.config_entry.data.get(CONF_USERNAME, "")
        cloud_password = self.config_entry.data.get(CONF_PASSWORD, "")
        cloud_country = self.config_entry.data.get(CONF_COUNTRY, "US")
        mesh_id = self.config_entry.data.get(CONF_MESH_ID, 0)
        errors = {}

        if user_input is not None:
            conf = {**self.config_entry.data}
            has_changed = False

            if user_input.get(CONF_USERNAME, cloud_username) != cloud_username:
                cloud_username = user_input.get(CONF_USERNAME)
                conf[CONF_USERNAME] = cloud_username
                has_changed = True
            if user_input.get(CONF_PASSWORD, cloud_password) != cloud_password:
                cloud_password = user_input.get(CONF_PASSWORD)
                conf[CONF_PASSWORD] = cloud_password
                has_changed = True
            cloud_country = user_input.get(CONF_COUNTRY)

            cloud = MagicHue(cloud_username, cloud_password, cloud_country)
            if not errors and await cloud.login() is not True:
                errors[CONF_PASSWORD] = "mesh_login"
            if not errors and await cloud.get_meshes() is not True:
                errors[CONF_COUNTRY] = "mesh_fetch"
            if not errors and await cloud.get_devices() is not True:
                errors[CONF_COUNTRY] = "mesh_devices"
            elif not errors:
                if conf.get(CONF_COUNTRY) != cloud.country:           
                    conf[CONF_COUNTRY] = cloud_country = cloud.country
                    has_changed = True
                device_count = 0
                for location in cloud.meshes:
                    for device in location["deviceList"]:
                        if device["meshUUID"] != mesh_id:
                            continue
                        device_count += 1
                if device_count:
                    if has_changed:
                        _LOGGER.warn(f"Updating configuration: {conf}")
                        self.hass.config_entries.async_update_entry(self.config_entry, data=conf)
                    return self.async_create_entry(title="", data=self.options)
                else:
                    errors[CONF_COUNTRY] = "mesh_no_devices"

        if user_input is None or errors:
            return self.async_show_form(
                step_id="mesh",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_USERNAME, default=cloud_username): str,
                        vol.Required(CONF_PASSWORD, default=cloud_password): str,
                        vol.Required(CONF_COUNTRY, default=cloud_country): 
                            SelectSelector(
                                SelectSelectorConfig(
                                    mode=SelectSelectorMode.DROPDOWN,
                                    options=[
                                        SelectOptionDict(value=k, label=v)
                                        for k, v in MagicHue.countries()
                                    ],
                                )
                            ),
                    }
                ),
                errors=errors,
            )
        return self.async_abort(reason="mesh_not_supported")

    async def async_step_tune(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Common device tuning step"""
        if user_input is not None:
            data = self.options | user_input
            return self.async_create_entry(title="", data=data)
        
        return self.async_show_form(
            step_id="tune",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RETRY_COUNT,
                        default=self.options.get(
                            CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_DEVICE_RETRYS, max=MAX_DEVICE_RETRYS),
                    ),
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=self.options.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                }
            ),
        )

