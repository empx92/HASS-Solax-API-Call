
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
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
        session = async_get_clientsession(self.hass)
        headers = {"Content-Type": "application/json", "tokenId": self._token}

        async def fetch_one(wifi_sn: str) -> tuple[str, dict[str, Any] | None]:
            payload = json.dumps({"wifiSn": wifi_sn})

            # simple retry/backoff: 3 attempts
            for attempt in range(3):
                try:
                    async with session.post(API_URL, headers=headers, data=payload, timeout=API_TIMEOUT) as resp:
                        data = await resp.json(content_type=None)
                        if isinstance(data, dict) and data.get("success") and "result" in data:
                            res = data.get("result") or {}
                            filtered = {k: res.get(k) for k in KEYS}
                            feed = res.get("feedinpower")
                            export_power: float | None
                            import_power: float | None
                            if feed is None:
                                export_power = None
                                import_power = None
                            else:
                                try:
                                    feed_val = float(feed)
                                except (TypeError, ValueError):
                                    feed_val = 0.0
                                if feed_val > 0:
                                    export_power = feed_val
                                    import_power = 0.0
                                elif feed_val < 0:
                                    export_power = 0.0
                                    import_power = abs(feed_val)
                                else:
                                    export_power = 0.0
                                    import_power = 0.0
                            filtered["export"] = export_power
                            filtered["import"] = import_power
                            return wifi_sn, filtered
                        _LOGGER.warning("Bad response for %s (try %s): %s", wifi_sn, attempt+1, data)
                except (ClientError, asyncio.TimeoutError) as exc:
                    _LOGGER.warning("Request error %s (try %s): %s", wifi_sn, attempt+1, exc)
                await asyncio.sleep(1 + attempt)  # backoff

            raise UpdateFailed(f"Failed to fetch after retries: {wifi_sn}")

        devices = [d.get("wifi_sn") for d in self.devices if d.get("wifi_sn")]
        if not devices:
            _LOGGER.debug("No devices configured for %s", DOMAIN)
            return {}
        results: dict[str, dict[str, Any]] = {}
        fetched = await asyncio.gather(*(fetch_one(sn) for sn in devices))
        for wifi_sn, result in fetched:
            results[wifi_sn] = result or {}
        return results
