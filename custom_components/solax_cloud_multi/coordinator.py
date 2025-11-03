"""Coordinator for SolaX Cloud Multi."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_DEVICES,
    CONF_WIFI_SN,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    API_URL,
    API_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

class SolaxDataUpdateCoordinator(DataUpdateCoordinator):
    """Fetch data from SolaX API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        update_interval = timedelta(seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        token = self.entry.data[CONF_TOKEN]
        devices = self.entry.options.get(CONF_DEVICES, [])
        wifi_sns = [d[CONF_WIFI_SN] for d in devices]

        if not wifi_sns:
            return {}

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)) as session:
            tasks = [self._fetch_device(session, token, sn) for sn in wifi_sns]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        data = {}
        for sn, result in zip(wifi_sns, results):
            if isinstance(result, Exception):
                _LOGGER.error(f"Error fetching {sn}: {result}")
                data[sn] = {}
            else:
                data[sn] = result.get("result", {})
        return data

    async def _fetch_device(self, session: aiohttp.ClientSession, token: str, wifi_sn: str):
        headers = {"tokenId": token}
        payload = {"wifiSn": wifi_sn}
        async with session.post(API_URL, headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}")
            return await resp.json()
