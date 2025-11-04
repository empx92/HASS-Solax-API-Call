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
        tasks = [
            self._fetch_device(session, token, wifi_sn)
            for wifi_sn in wifi_sns
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        data: dict[str, dict[str, Any]] = {}
        for wifi_sn, result in zip(wifi_sns, results):
            if isinstance(result, Exception):
                _LOGGER.error("Error fetching %s: %s", wifi_sn, result)
                data[wifi_sn] = {}
                continue

            data[wifi_sn] = self._normalize_result(wifi_sn, result)

        return data

    async def _fetch_device(
        self, session, token: str, wifi_sn: str
    ) -> dict[str, Any]:
        last_error: UpdateFailed | None = None

        for method, url, mode in API_ENDPOINTS:
            request_kwargs: dict[str, Any] = {
                "timeout": ClientTimeout(total=API_TIMEOUT),
                "headers": {"Accept": "application/json"},
            }

            if mode == "params":
                request_kwargs["params"] = {"tokenId": token, "sn": wifi_sn}
            elif mode == "form":
                request_kwargs["data"] = {"tokenId": token, "sn": wifi_sn}
                request_kwargs["headers"]["Content-Type"] = (
                    "application/x-www-form-urlencoded"
                )
            else:  # json
                request_kwargs["json"] = {"sn": wifi_sn}
                request_kwargs["headers"]["tokenId"] = token

            try:
                async with session.request(method, url, **request_kwargs) as response:
                    response.raise_for_status()
                    data: dict[str, Any] = await response.json(content_type=None)
            except (
                asyncio.TimeoutError,
                ClientError,
                ContentTypeError,
                ValueError,
            ) as err:
                last_error = UpdateFailed(
                    f"Network error fetching {wifi_sn} via {url}: {err}"
                )
                continue

            if not isinstance(data, dict):
                last_error = UpdateFailed(
                    f"Malformed response for {wifi_sn} via {url}: {data}"
                )
                continue

            if not data.get("success", True):
                message = (
                    data.get("exception")
                    or data.get("message")
                    or "unknown error"
                )
                if "param invalid" in message.lower():
                    last_error = UpdateFailed(
                        f"API error for {wifi_sn}: {message}"
                    )
                    continue
                raise UpdateFailed(f"API error for {wifi_sn}: {message}")

            return data

        if last_error is not None:
            raise last_error

        raise UpdateFailed(f"No valid response for {wifi_sn}")

    def _normalize_result(self, wifi_sn: str, response: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] | None = response.get("result")
        if result is None and isinstance(response.get("data"), dict):
            result = response["data"]
        if not isinstance(result, dict):
            return {}

        normalized: dict[str, Any] = {}
        for key, value in result.items():
            normalized[key] = self._coerce_value(key, value)

        # Preserve metadata from the top-level response when available
        for meta_key in ("sn", "inverterSn", "uploadTime"):
            if meta_key not in normalized and meta_key in response:
                normalized[meta_key] = response[meta_key]

        normalized.setdefault("sn", response.get("sn") or response.get("inverterSn") or wifi_sn)
        normalized.setdefault("wifi_sn", wifi_sn)

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
