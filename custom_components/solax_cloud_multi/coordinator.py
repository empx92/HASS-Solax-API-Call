
from __future__ import annotations

import asyncio
import json
import logging
from datetime import timedelta
from typing import Any

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    API_URL,
    API_TIMEOUT,
    DEFAULT_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_DEVICES,
    CONF_SCAN_INTERVAL,
    KEYS,
)

_LOGGER = logging.getLogger(__name__)

class SolaxCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]] ]):
    """Fetch data for multiple SolaX devices in parallel."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        scan_interval = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._token = entry.data[CONF_TOKEN]

    @property
    def devices(self) -> list[dict[str, Any]]:
        return list(self.entry.options.get(CONF_DEVICES, []))

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Return a mapping wifi_sn -> result dict."""
        session = self.hass.helpers.aiohttp_client.async_get_clientsession()
        headers = {"Content-Type": "application/json", "tokenId": self._token}

        async def fetch_one(wifi_sn: str) -> tuple[str, dict[str, Any] | None]:
            payload = json.dumps({"wifiSn": wifi_sn})
            try:
                async with session.post(API_URL, headers=headers, data=payload, timeout=API_TIMEOUT) as resp:
                    data = await resp.json(content_type=None)
            except (ClientError, asyncio.TimeoutError) as exc:
                raise UpdateFailed(f"Request error {wifi_sn}: {exc}") from exc
            if not isinstance(data, dict) or not data.get("success") or "result" not in data:
                raise UpdateFailed(f"Bad response for {wifi_sn}: {data}")
            res = data.get("result") or {}
            filtered = {k: res.get(k) for k in KEYS}
            return wifi_sn, filtered

        tasks = [fetch_one(d.get("wifi_sn")) for d in self.devices if d.get("wifi_sn")]
        results: dict[str, dict[str, Any]] = {}
        if tasks:
            for wifi_sn, result in await asyncio.gather(*tasks):
                results[wifi_sn] = result or {}
        return results
