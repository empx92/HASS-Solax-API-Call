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
    MIN_SCAN_INTERVAL,
    MAX_SCAN_INTERVAL,
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
        existing_options = dict(self.config_entry.options)
        existing_devices: list[dict[str, Any]] = []
        for device in existing_options.get(CONF_DEVICES, []):
            device_copy = dict(device)
            wifi_sn = device_copy.get(CONF_WIFI_SN)
            if wifi_sn:
                device_copy[CONF_WIFI_SN] = wifi_sn.strip().upper()
            existing_devices.append(device_copy)

        if user_input is not None:
            add_device = user_input.pop("add_device", None)
            remove_device = user_input.pop("remove_device", None)

            devices = existing_devices

            if add_device:
                wifi_sn = add_device[CONF_WIFI_SN].strip().upper()
                name = add_device[CONF_NAME].strip() or wifi_sn
                existing = next(
                    (device for device in devices if device.get(CONF_WIFI_SN) == wifi_sn),
                    None,
                )
                if existing:
                    existing[CONF_NAME] = name
                else:
                    devices.append({CONF_WIFI_SN: wifi_sn, CONF_NAME: name})

            if remove_device:
                devices = [
                    device
                    for device in devices
                    if device.get(CONF_WIFI_SN) != remove_device
                ]

            options: dict[str, Any] = dict(existing_options)
            options[CONF_USE_PREFIX] = user_input.get(
                CONF_USE_PREFIX,
                existing_options.get(CONF_USE_PREFIX, False),
            )
            options[CONF_SCAN_INTERVAL] = user_input.get(
                CONF_SCAN_INTERVAL,
                existing_options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            )
            options[CONF_DEVICES] = devices

            return self.async_create_entry(title="", data=options)

        device_labels: dict[str, str] = {}
        for device in existing_devices:
            wifi_sn = device.get(CONF_WIFI_SN)
            if not wifi_sn:
                continue
            label = device.get(CONF_NAME) or wifi_sn
            device_labels[wifi_sn] = label
        removal_choices = list(device_labels)

        schema_dict: dict[Any, Any] = {
            vol.Optional(
                CONF_USE_PREFIX,
                default=existing_options.get(CONF_USE_PREFIX, False),
            ): bool,
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=existing_options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
            ),
            vol.Optional("add_device"): vol.Schema(
                {
                    vol.Required(CONF_WIFI_SN): str,
                    vol.Required(CONF_NAME): str,
                }
            ),
        }

        if removal_choices:
            schema_dict[vol.Optional("remove_device")] = vol.In(removal_choices)

        schema = vol.Schema(schema_dict)

        device_list = ", ".join(
            f"{device_labels[sn]} ({sn})" if device_labels[sn] != sn else sn
            for sn in removal_choices
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={"devices": device_list or "Keine"},
        )
