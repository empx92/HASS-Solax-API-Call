"""Config flow for SolaX Cloud Multi."""
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_DEVICES,
    CONF_WIFI_SN,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_USE_PREFIX,
    DEFAULT_SCAN_INTERVAL,
)

class SolaxCloudMultiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_TOKEN])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="SolaX Cloud (Multi)", data=user_input)

        data_schema = vol.Schema({vol.Required(CONF_TOKEN): str})
        return self.async_show_form(step_id="user", data_schema=data_schema)

    @staticmethod
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            devices = self.config_entry.options.get(CONF_DEVICES, [])

            if "add_device" in user_input:
                devices.append({
                    CONF_WIFI_SN: user_input["add_device"][CONF_WIFI_SN],
                    CONF_NAME: user_input["add_device"][CONF_NAME],
                })

            if "remove_device" in user_input:
                name_to_remove = user_input["remove_device"]
                devices = [d for d in devices if d.get(CONF_NAME) != name_to_remove]

            user_input[CONF_DEVICES] = devices
            return self.async_create_entry(title="", data=user_input)

        devices = self.config_entry.options.get(CONF_DEVICES, [])
        device_names = {
            d[CONF_NAME]: d[CONF_NAME]
            for d in devices
            if d.get(CONF_NAME)
        }

        schema_dict: dict[Any, Any] = {
            vol.Optional(CONF_USE_PREFIX, default=False): bool,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=10, max=300)
            ),
            vol.Optional("add_device"): vol.Schema(
                {
                    vol.Required(CONF_WIFI_SN): str,
                    vol.Required(CONF_NAME): str,
                }
            ),
        }

        if device_names:
            schema_dict[vol.Optional("remove_device")] = vol.In(device_names)

        schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={"devices": ", ".join(device_names) or "Keine"},
        )
