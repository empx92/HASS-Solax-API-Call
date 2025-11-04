"""Sensor platform for SolaX Cloud Multi."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    CONF_DEVICES,
    CONF_WIFI_SN,
    CONF_NAME,
    CONF_USE_PREFIX,
    SENSOR_MAP,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    devices = entry.options.get(CONF_DEVICES)
    if devices is None:
        devices = entry.data.get(CONF_DEVICES, [])
    use_prefix = entry.options.get(CONF_USE_PREFIX, False)

    entities = []

    for device in devices:
        wifi_sn = device.get(CONF_WIFI_SN)
        if not wifi_sn:
            continue
        name = device.get(CONF_NAME) or wifi_sn
        prefix = f"{name} " if use_prefix else ""

        for key, config in SENSOR_MAP.items():
            device_class_name = config.get("device_class")
            device_class = None
            if isinstance(device_class_name, str):
                device_class = getattr(
                    SensorDeviceClass, device_class_name.upper(), None
                )

            state_class = None
            if device_class == SensorDeviceClass.POWER:
                state_class = SensorStateClass.MEASUREMENT

            icon = config.get("icon")
            if not icon and key == "export_power":
                icon = "mdi:export"
            elif not icon and key == "import_power":
                icon = "mdi:import"

            description = SensorEntityDescription(
                key=key,
                name=f"{prefix}{config['name']}".strip(),
                native_unit_of_measurement=config.get("unit"),
                device_class=device_class,
                state_class=state_class,
                icon=icon,
            )
            entities.append(
                SolaxSensor(
                    coordinator,
                    entry_id=entry.entry_id,
                    wifi_sn=wifi_sn,
                    device_name=name,
                    description=description,
                )
            )

    async_add_entities(entities)


class SolaxSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SolaX Cloud sensor."""

    def __init__(
        self,
        coordinator,
        *,
        entry_id: str,
        wifi_sn: str,
        device_name: str,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self._wifi_sn = wifi_sn
        self._device_name = device_name
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{wifi_sn}_{description.key}"

    @property
    def available(self) -> bool:
        return bool(self._device_data()) and super().available

    @property
    def device_info(self) -> DeviceInfo:
        data = self._device_data()
        model = data.get("inverterSn") or data.get("model")
        serial = data.get("sn") or self._wifi_sn
        sw_version = data.get("uploadTime")

        return DeviceInfo(
            identifiers={(DOMAIN, self._wifi_sn)},
            manufacturer=MANUFACTURER,
            name=self._device_name,
            model=model,
            serial_number=serial,
            sw_version=sw_version,
        )

    @property
    def native_value(self) -> Any:
        data = self._device_data()
        feedin = data.get("feedinpower")

        if self.entity_description.key == "export_power":
            if feedin is None:
                return None
            return feedin if feedin > 0 else 0

        if self.entity_description.key == "import_power":
            if feedin is None:
                return None
            return abs(feedin) if feedin < 0 else 0

        return data.get(self.entity_description.key)

    def _device_data(self) -> dict[str, Any]:
        coordinator_data = self.coordinator.data or {}
        return coordinator_data.get(self._wifi_sn, {})
