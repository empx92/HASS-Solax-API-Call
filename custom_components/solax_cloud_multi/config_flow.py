
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_DEVICES,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)

STEP_USER_SCHEMA = vol.Schema({vol.Required(CONF_TOKEN): str})

DEVICE_ADD_SCHEMA = vol.Schema(
    {
        vol.Required("wifi_sn"): str,
        vol.Optional("name"): str,
        vol.Optional("battery_kwh", default=10.0): vol.Coerce(float),
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(int, vol.Range(min=5, max=300))}
)

class SolaxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA)
        await self.async_set_unique_id("solax_cloud_multi_singleton")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="SolaX Cloud (Multi)", data={CONF_TOKEN: user_input[CONF_TOKEN]})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SolaxOptionsFlow(config_entry)

class SolaxOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry):
        self.entry = entry

    @property
    def _devices(self) -> list[dict[str, Any]]:
        return list(self.entry.options.get(CONF_DEVICES, []))

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_device", "remove_device", "set_options"],
        )

    async def async_step_set_options(self, user_input=None):
        if user_input is not None:
            options = dict(self.entry.options)
            options[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            return self.async_create_entry(title="", data=options)
        return self.async_show_form(step_id="set_options", data_schema=OPTIONS_SCHEMA)

    async def async_step_add_device(self, user_input=None):
        if user_input is not None:
            devices = self._devices
            devices.append(
                {"wifi_sn": user_input["wifi_sn"], "name": user_input.get("name") or user_input["wifi_sn"], "battery_kwh": user_input["battery_kwh"]}
            )
            options = dict(self.entry.options)
            options[CONF_DEVICES] = devices
            return self.async_create_entry(title="", data=options)
        return self.async_show_form(step_id="add_device", data_schema=DEVICE_ADD_SCHEMA)

    async def async_step_remove_device(self, user_input=None):
        devices = self._devices
        if not devices:
            return self.async_abort(reason="no_devices")

        choices = {
            d["wifi_sn"]: f"{d.get('name') or d['wifi_sn']} ({d['wifi_sn']})"
            for d in devices
            if d.get("wifi_sn")
        }

        if not choices:
            return self.async_abort(reason="no_devices")

        schema = vol.Schema(
            {
                vol.Required(
                    "wifi_sn", default=next(iter(choices))
                ): vol.In(choices)
            }
        )

        if user_input is not None:
            wifi = user_input["wifi_sn"]
            devices = [d for d in self._devices if d.get("wifi_sn") != wifi]
            options = dict(self.entry.options)
            options[CONF_DEVICES] = devices
            return self.async_create_entry(title="", data=options)
        return self.async_show_form(step_id="remove_device", data_schema=schema)
