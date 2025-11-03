"""Sensor platform for SolaX Cloud Multi."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import POWER_WATT, PERCENTAGE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_DEVICES,
    CONF_WIFI_SN,
    CONF_USE_PREFIX,
    SENSOR_MAP,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    devices = entry.options.get(CONF_DEVICES, [])
    use_prefix = entry.options.get(CONF_USE_PREFIX, False)

    entities = []

    for device in devices:
        wifi_sn = device[CONF_WIFI_SN]
        name = device.get("name", "Unknown")
        prefix = f"{name} " if use_prefix else ""

        for key, config in SENSOR_MAP.items():
            description = SensorEntityDescription(
                key=key,
                name=f"{prefix}{config['name']}".strip(),
                native_unit_of_measurement=config["unit"],
                device_class=getattr(SensorDeviceClass, config["device_class"].upper(), None),
                state_class=SensorStateClass.MEASUREMENT if "power" in config["device_class"] else None,
                icon="mdi:export" if key == "export_power" else "mdi:import" if key == "import_power" else None,
            )
            entities.append(SolaxSensor(coordinator, wifi_sn, description))

    async_add_entities(entities)


class SolaxSensor(CoordinatorEntity, SensorEntity):
    """SolaX Sensor – berechnet Import/Export aus feedinpower."""

    def __init__(self, coordinator, wifi_sn: str, description: SensorEntityDescription):
        super().__init__(coordinator)
        self._wifi_sn = wifi_sn
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{wifi_sn}_{description.key}"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data.get(self._wifi_sn, {})
        feedin = data.get("feedinpower", 0)

        if self.entity_description.key == "export_power":
            return feedin if feedin > 0 else 0
        if self.entity_description.key == "import_power":
            return abs(feedin) if feedin < 0 else 0

        return data.get(self.entity_description.key)
