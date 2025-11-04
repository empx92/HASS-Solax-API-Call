"""Coordinator for SolaX Cloud Multi."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from aiohttp import ClientError, ClientTimeout, ContentTypeError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_DEVICES,
    CONF_WIFI_SN,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    API_ENDPOINTS,
    API_TIMEOUT,
    NUMERIC_SENSOR_KEYS,
)

_LOGGER = logging.getLogger(__name__)


class SolaxDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetch and cache data from the SolaX Cloud API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        update_interval = timedelta(
            seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        token = self.entry.data[CONF_TOKEN]
        devices = self.entry.options.get(CONF_DEVICES, [])
        wifi_sns = [device.get(CONF_WIFI_SN) for device in devices if device.get(CONF_WIFI_SN)]

        if not wifi_sns:
            return {}

        session = async_get_clientsession(self.hass)
        tasks = [self._fetch_device(session, token, wifi_sn) for wifi_sn in wifi_sns]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        data: dict[str, dict[str, Any]] = {}
        for wifi_sn, result in zip(wifi_sns, results):
            if isinstance(result, Exception):
                _LOGGER.error("Error fetching %s: %s", wifi_sn, result)
                data[wifi_sn] = {}
                continue

            data[wifi_sn] = self._normalize_result(result)

        return data

    async def _fetch_device(self, session, token: str, wifi_sn: str) -> dict[str, Any]:
        headers = {
            "tokenId": token,
            "Content-Type": "application/json",
        }
        payload = {"sn": wifi_sn}

        try:
            async with session.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=ClientTimeout(total=API_TIMEOUT),
            ) as response:
                response.raise_for_status()
                data: dict[str, Any] = await response.json()
        except (asyncio.TimeoutError, ClientError, ContentTypeError, ValueError) as err:
            raise UpdateFailed(f"Network error fetching {wifi_sn}: {err}") from err

        if not isinstance(data, dict):
            raise UpdateFailed(f"Malformed response for {wifi_sn}: {data}")

        if not data.get("success", True):
            message = data.get("exception") or data.get("message") or "unknown error"
            raise UpdateFailed(f"API error for {wifi_sn}: {message}")

        return data

    def _normalize_result(self, response: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] | None = response.get("result")
        if not isinstance(result, dict):
            return {}

        normalized: dict[str, Any] = {}
        for key, value in result.items():
            normalized[key] = self._coerce_value(key, value)

        # Preserve metadata from the top-level response when available
        for meta_key in ("sn", "inverterSn", "uploadTime"):
            if meta_key not in normalized and meta_key in response:
                normalized[meta_key] = response[meta_key]

        return normalized

    @staticmethod
    def _coerce_value(key: str, value: Any) -> Any:
        if value in ("", None, "NA", "N/A"):
            return None

        if key in NUMERIC_SENSOR_KEYS:
            if isinstance(value, (int, float)):
                return value
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return None
                try:
                    numeric = float(value)
                except ValueError:
                    return None
                return int(numeric) if numeric.is_integer() else numeric
            return None

        return value
