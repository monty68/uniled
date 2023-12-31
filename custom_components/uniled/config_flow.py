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
    Platform,
)
from .lib.net.device import UNILED_TRANSPORT_NET, UniledNetDevice, UniledNetModel
from .lib.ble.device import UNILED_TRANSPORT_BLE, UniledBleDevice, UniledBleModel
from .lib.zng.cloud import MagicHue, MAGICHUE_DEFAULT_COUNTRY
from .lib.zng.manager import (
    CONF_ZNG_ACTIVE_SCAN as CONF_ACTIVE_SCAN,
    CONF_ZNG_MESH_UUID as CONF_MESH_UUID,
    CONF_ZNG_MESH_ID as CONF_MESH_ID,
    UNILED_TRANSPORT_ZNG,
    ZENGGE_UPDATE_SECONDS as DEFAULT_MESH_UPDATE_INTERVAL,
    ZENGGE_DESCRIPTION,
    ZenggeManager,
)
from .const import (
    DOMAIN,
    ATTR_UL_CHIP_TYPE,
    ATTR_UL_LIGHT_TYPE,
    CONF_UL_RETRY_COUNT as CONF_RETRY_COUNT,
    CONF_UL_TRANSPORT as CONF_TRANSPORT,
    CONF_UL_UPDATE_INTERVAL as CONF_UPDATE_INTERVAL,
    UNILED_MIN_DEVICE_RETRYS as MIN_DEVICE_RETRYS,
    UNILED_DEF_DEVICE_RETRYS as DEFAULT_RETRY_COUNT,
    UNILED_MAX_DEVICE_RETRYS as MAX_DEVICE_RETRYS,
    UNILED_MIN_UPDATE_INTERVAL as MIN_UPDATE_INTERVAL,
    UNILED_DEF_UPDATE_INTERVAL as DEFAULT_UPDATE_INTERVAL,
    UNILED_MAX_UPDATE_INTERVAL as MAX_UPDATE_INTERVAL,
    UNILED_OPTIONS_ATTRIBUTES,
)
from .coordinator import UniledUpdateCoordinator

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import functools
import operator
import time
import logging

_LOGGER = logging.getLogger(__name__)


class UniledMeshHandler:
    """Common methods for mesh config and option flows"""

    def _mesh_title(self, mesh_uuid: int | None = None) -> str:
        """Mesh title"""
        if mesh_uuid is None:
            mesh_uuid = self.context.get(CONF_MESH_UUID, 0)
        return f"{ZENGGE_DESCRIPTION} ({hex(mesh_uuid)})"

    def _mesh_set_context(self) -> None:
        """Set context with current mesh details"""
        if hasattr(self, "config_entry"):
            self.context = self.context | {**self.config_entry.data}
        if not hasattr(self.context, "title_placeholders"):
            self.context["title_placeholders"] = dict()
        self.context["title_placeholders"]["name"] = self._mesh_title()

    def _mesh_get_context(self) -> dict:
        """Get current mesh details from context"""
        if hasattr(self, "options"):
            options = self.options
        else:
            options = {
                CONF_UPDATE_INTERVAL: DEFAULT_MESH_UPDATE_INTERVAL,
                CONF_RETRY_COUNT: DEFAULT_RETRY_COUNT,
                CONF_ACTIVE_SCAN: True,
            }

        return {
            "title": self.context["title_placeholders"]["name"],
            "data": {
                CONF_TRANSPORT: self.context.get(CONF_TRANSPORT, UNILED_TRANSPORT_ZNG),
                CONF_USERNAME: self.context.get(CONF_USERNAME, ""),
                CONF_PASSWORD: self.context.get(CONF_PASSWORD, ""),
                CONF_COUNTRY: self.context.get(CONF_COUNTRY, MAGICHUE_DEFAULT_COUNTRY),
                CONF_MESH_ID: self.context.get(CONF_MESH_ID, None),
                CONF_MESH_UUID: self.context.get(CONF_MESH_UUID, 0),
            },
            "options": options,
        }

    async def async_step_mesh_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Menu step"""
        mesh_uuid = self.context.get(CONF_MESH_UUID, 0)

        return self.async_show_menu(
            step_id="mesh_menu",
            menu_options=["mesh_cloud", "tune_comms"],
            description_placeholders={
                "mesh_title": self._mesh_title(mesh_uuid),
                "mesh_uuid": hex(mesh_uuid),
            },
        )

    async def async_step_mesh_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Mesh cloud step"""
        cloud_username = self.context.get(CONF_USERNAME, "")
        cloud_password = self.context.get(CONF_PASSWORD, "")
        cloud_country = self.context.get(CONF_COUNTRY, "US")
        mesh_uuid = self.context.get(CONF_MESH_UUID, 0)
        errors = {}

        if user_input is not None:
            has_changed = False

            if user_input.get(CONF_USERNAME, cloud_username) != cloud_username:
                cloud_username = user_input.get(CONF_USERNAME)
                self.context[CONF_USERNAME] = cloud_username
                has_changed = True
            if user_input.get(CONF_PASSWORD, cloud_password) != cloud_password:
                cloud_password = user_input.get(CONF_PASSWORD)
                self.context[CONF_PASSWORD] = cloud_password
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
                if self.context.get(CONF_COUNTRY) != cloud.country:
                    self.context[CONF_COUNTRY] = cloud_country = cloud.country
                    has_changed = True
                device_count = 0
                for location in cloud.meshes:
                    for device in location["deviceList"]:
                        if device["meshUUID"] != mesh_uuid:
                            continue
                        device_count += 1
                if device_count:
                    info = self._mesh_get_context()
                    if hasattr(self, "config_entry"):
                        if has_changed:
                            # _LOGGER.info(f"Updating configuration: {info['data']}")
                            self.hass.config_entries.async_update_entry(
                                self.config_entry, data=info["data"]
                            )
                        return self.async_create_entry(title="", data=info["options"])
                    return self.async_create_entry(
                        title=self.context["title_placeholders"]["name"],
                        data=info["data"],
                        options=info["options"],
                    )
                else:
                    errors[CONF_COUNTRY] = "mesh_no_devices"

        if user_input is None or errors:
            return self.async_show_form(
                step_id="mesh_cloud",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_USERNAME, default=cloud_username): str,
                        vol.Required(CONF_PASSWORD, default=cloud_password): str,
                        vol.Required(
                            CONF_COUNTRY, default=cloud_country
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
                description_placeholders={
                    "mesh_title": self._mesh_title(mesh_uuid),
                    "mesh_uuid": hex(mesh_uuid),
                },
                errors=errors,
            )

        return self.async_abort(reason="mesh_not_supported")


class UniledOptionsFlowHandler(flow.OptionsFlowWithConfigEntry, UniledMeshHandler):
    """Handle Uniled options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        self.coordinator: UniledUpdateCoordinator = self.hass.data[DOMAIN][
            self.config_entry.entry_id
        ]

        if self.config_entry.data.get(CONF_TRANSPORT) == UNILED_TRANSPORT_ZNG:
            self._mesh_set_context()
            return await self.async_step_mesh_menu()

        config_options = 0
        for channel in self.coordinator.device.channel_list:
            if not channel.features:
                continue
            for feature in channel.features:
                if feature.attr in UNILED_OPTIONS_ATTRIBUTES:
                    config_options += 1

        if config_options:
            return await self.async_step_conf_menu()
        return await self.async_step_tune_comms()

    async def async_step_conf_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configuration menu step"""
        if not self.coordinator.device.available:
            return self.async_abort(reason="not_available")
        return self.async_show_menu(
            step_id="conf_menu",
            menu_options=["channels", "tune_comms"],
        )

    async def async_step_channels(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Channels Menu"""
        if self.coordinator.device.channels > 1:
            if user_input is not None:
                channel_id = int(user_input.get("channel", 0))
            else:
                channels = {}
                for channel in self.coordinator.device.channel_list:
                    if not channel.features:
                        continue
                    for feature in channel.features:
                        if feature.attr in UNILED_OPTIONS_ATTRIBUTES:
                            channels[channel.number] = channel.name
                            break

                if len(channels) > 1:
                    data_schema = vol.Schema(
                        {
                            vol.Required("channel"): vol.In(
                                {number: name for number, name in channels.items()}
                            ),
                        }
                    )
                    return self.async_show_form(
                        step_id="channels",
                        data_schema=data_schema,
                    )
                elif len(channels) == 1:
                    channel_id = next(iter(channels))
                else:
                    return self.async_abort(reason="no_configurable")
        else:
            channel_id = 0
        channel = self.coordinator.device.channel(channel_id)
        self.context["channel"] = channel
        if channel.has(ATTR_UL_LIGHT_TYPE) or channel.has(ATTR_UL_CHIP_TYPE):
            return await self.async_step_conf_type()
        return await self.async_step_conf_channel()

    async def async_step_conf_type(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure type"""
        errors: dict[str, str] = {}
        channel = self.context.get("channel", None)

        if (conf_value := channel.get(ATTR_UL_LIGHT_TYPE, None)) is not None:
            conf_attr = ATTR_UL_LIGHT_TYPE
        elif (conf_value := channel.get(ATTR_UL_CHIP_TYPE, None)) is not None:
            conf_attr = ATTR_UL_CHIP_TYPE
        else:
            return await self.async_step_conf_channel()

        if not self.coordinator.device.available:
            errors[conf_attr] = "not_available"

        if user_input is not None and not errors:
            conf_value = user_input.get(conf_attr, conf_value)
            if conf_value != channel.get(conf_attr, conf_value):
                if await self.coordinator.device.async_set_state(
                    channel, conf_attr, conf_value
                ):
                    self.options[conf_attr] = conf_value
                    return self.async_create_entry(title="", data=self.options)
                else:
                    errors[conf_attr] = "unknown"
            else:
                return await self.async_step_conf_channel()

        data_schema = vol.Schema(
            {
                vol.Required(conf_attr, default=conf_value): SelectSelector(
                    SelectSelectorConfig(
                        mode=SelectSelectorMode.DROPDOWN,
                        options=self.coordinator.device.get_list(channel, conf_attr),
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="conf_type",
            data_schema=data_schema,
            description_placeholders={
                "channel_name": channel.name,
            },
            errors=errors,
        )

    async def async_step_conf_channel(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a channel"""
        errors: dict[str, str] = {}
        channel = self.context.get("channel", None)

        if user_input is not None and not errors:
            for conf_attr, conf_value in user_input.items():
                _LOGGER.warn("%s = %s", conf_attr, conf_value)
                if not self.coordinator.device.available:
                    errors[conf_attr] = "not_available"
                elif conf_value != channel.get(conf_attr, conf_value):
                    if await self.coordinator.device.async_set_state(
                        channel, conf_attr, conf_value
                    ):
                        self.options[conf_attr] = conf_value
                    else:
                        errors[conf_attr] = "unknown"

        if user_input is None or errors:
            schema = None
            for conf_attr in UNILED_OPTIONS_ATTRIBUTES:
                if conf_attr == ATTR_UL_LIGHT_TYPE or conf_attr == ATTR_UL_CHIP_TYPE:
                    continue
                for feature in channel.features:
                    if feature.attr != conf_attr:
                        continue
                    if (conf_value := channel.get(conf_attr, None)) is None:
                        break
                    if feature.platform == Platform.NUMBER:
                        option = {
                            vol.Required(conf_attr, default=conf_value): vol.All(
                                vol.Coerce(int),
                                vol.Range(min=feature.min_value, max=feature.max_value),
                            ),
                        }
                    elif feature.platform == Platform.SELECT:
                        option = {
                            vol.Required(conf_attr, default=conf_value): SelectSelector(
                                SelectSelectorConfig(
                                    mode=SelectSelectorMode.DROPDOWN,
                                    options=self.coordinator.device.get_list(
                                        channel, conf_attr
                                    ),
                                )
                            ),
                        }
                    elif feature.platform == Platform.SWITCH:
                        option = {vol.Required(conf_attr, default=conf_value): cv.boolean}
                    else:
                        _LOGGER.warning(
                            "Unsupported feature platform: '%s' for '%s'.",
                            feature.platform,
                            feature.attr,
                        )
                        break
                    if option and schema is None:
                        schema = vol.Schema(option)
                    elif option and schema:
                        schema = schema.extend(option)
                    break

            if schema is not None:
                return self.async_show_form(
                    step_id="conf_channel",
                    data_schema=schema,
                    description_placeholders={
                        "channel_name": channel.name,
                        "light_type": channel.get(ATTR_UL_LIGHT_TYPE, None),
                        "chip_type": channel.get(ATTR_UL_CHIP_TYPE, None),
                    },
                    errors=errors,
                )

        if not self.coordinator.device.available:
            return self.async_abort(reason="not_available")
        return self.async_create_entry(title="", data=self.options)

    async def async_step_tune_comms(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Common device tuning step"""
        if user_input is not None:
            data = self.options | user_input
            return self.async_create_entry(title="", data=data)

        return self.async_show_form(
            step_id="tune_comms",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RETRY_COUNT,
                        default=self.options.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT),
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


class UniledConfigFlowHandler(UniledMeshHandler, flow.ConfigFlow, domain=DOMAIN):
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
                mesh_uuid = self._discovered_zng_meshes[address]
                self.context[CONF_TRANSPORT] = UNILED_TRANSPORT_ZNG
                self.context[CONF_MESH_UUID] = mesh_uuid
                self.context[CONF_MESH_ID] = address
                self.context["title_placeholders"] = {
                    "name": self._mesh_title(mesh_uuid),
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
                mesh_uuid, mesh_unique = ZenggeManager.mesh_uuid_unique(
                    discovery.device, discovery.advertisement
                )
                if mesh_uuid is not None:
                    _LOGGER.info(
                        "Discovered '%s' mesh '%s' device",
                        discovery.address,
                        hex(mesh_uuid),
                    )
                    if mesh_unique in self._async_current_ids():
                        continue
                    if mesh_unique not in self._discovered_zng_meshes:
                        self._discovered_zng_meshes[mesh_unique] = mesh_uuid
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
                                        mesh_unique: self._mesh_title(mesh_uuid)
                                        for mesh_unique, mesh_uuid in self._discovered_zng_meshes.items()
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

    async def _async_bluetooth_check_device(
        self, discovery: BluetoothServiceInfoBleak, raise_on_progress: bool = True
    ) -> bool:
        """Check device device is support"""
        mesh_uuid, mesh_unique = ZenggeManager.mesh_uuid_unique(
            discovery.device, discovery.advertisement
        )
        if mesh_uuid is not None:
            if mesh_unique not in self._discovered_zng_meshes:
                self._discovered_zng_meshes[mesh_unique] = mesh_uuid
                await self.async_set_unique_id(
                    mesh_unique, raise_on_progress=raise_on_progress
                )
                self._abort_if_unique_id_configured()

                self.context[CONF_TRANSPORT] = UNILED_TRANSPORT_ZNG
                self.context[CONF_MESH_UUID] = mesh_uuid
                self.context[CONF_MESH_ID] = mesh_unique
                self.context["title_placeholders"] = {
                    "name": self._mesh_title(mesh_uuid),
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
