
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfPower, UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_MAP
from .coordinator import SolaxCoordinator

PARALLEL_UPDATES = 0

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator: SolaxCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for device in coordinator.devices:
        wifi_sn = device["wifi_sn"]
        name = device.get("name") or wifi_sn
        battery_kwh = float(device.get("battery_kwh", 0))

        # basic sensors
        for key, meta in SENSOR_MAP.items():
            entities.append(SolaxValueSensor(coordinator, wifi_sn, name, key, meta))

        # ETA sensors (minutes + text)
        entities.append(SolaxEtaMinutesSensor(coordinator, wifi_sn, name, battery_kwh))
        entities.append(SolaxEtaTextSensor(coordinator, wifi_sn, name, battery_kwh))

    async_add_entities(entities, update_before_add=True)

class SolaxBase(CoordinatorEntity[SolaxCoordinator], SensorEntity):
    def __init__(self, coordinator: SolaxCoordinator, wifi_sn: str, base_name: str, kind: str) -> None:
        super().__init__(coordinator)
        self._wifi_sn = wifi_sn
        self._base_name = base_name
        self._kind = kind

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._wifi_sn)},
            "name": f"SolaX {self._base_name}",
            "manufacturer": "SolaX",
            "model": "Cloud",
        }

    def _val(self, key: str):
        return (self.coordinator.data.get(self._wifi_sn) or {}).get(key)

class SolaxValueSensor(SolaxBase):
    def __init__(self, coordinator, wifi_sn, base_name, key, meta):
        super().__init__(coordinator, wifi_sn, base_name, key)
        self._attr_name = f"{base_name} {meta['name']}"
        self._attr_unique_id = f"{wifi_sn}_{key}"
        unit = meta["unit"]
        if unit == "W":
            self._attr_native_unit_of_measurement = UnitOfPower.WATT
            self._attr_device_class = SensorDeviceClass.POWER
        elif unit == "°C":
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        elif unit == "%":
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_device_class = SensorDeviceClass.BATTERY
        else:
            self._attr_native_unit_of_measurement = unit
            self._attr_device_class = None

    @property
    def native_value(self):
        return self._val(self._kind)

class SolaxEtaMinutesSensor(SolaxBase):
    """Minutes until empty/full based on batPower and SoC."""
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator, wifi_sn, base_name, battery_kwh: float):
        super().__init__(coordinator, wifi_sn, base_name, "eta_minutes")
        self._battery_kwh = battery_kwh
        self._attr_name = f"{base_name} Battery ETA (min)"
        self._attr_unique_id = f"{wifi_sn}_eta_minutes"

    @property
    def native_value(self):
        soc = float(self._val("soc") or 0.0)
        p = float(self._val("batPower") or 0.0)
        cap = float(self._battery_kwh or 0.0)
        if cap <= 0.0 or p == 0.0:
            return None
        if p < 0:
            # discharge: energy until empty
            e_kwh = (soc / 100.0) * cap
            hrs = e_kwh / (abs(p) / 1000.0)
        else:
            # charge: energy until full
            e_kwh = ((100.0 - soc) / 100.0) * cap
            hrs = e_kwh / (p / 1000.0)
        mins = max(0, round(hrs * 60))
        return mins

class SolaxEtaTextSensor(SolaxBase):
    """Friendly string for ETA."""
    def __init__(self, coordinator, wifi_sn, base_name, battery_kwh: float):
        super().__init__(coordinator, wifi_sn, base_name, "eta_text")
        self._battery_kwh = battery_kwh
        self._attr_name = f"{base_name} Battery ETA"
        self._attr_unique_id = f"{wifi_sn}_eta_text"

    @property
    def native_value(self):
        soc = float(self._val("soc") or 0.0)
        p = float(self._val("batPower") or 0.0)
        cap = float(self._battery_kwh or 0.0)
        if cap <= 0.0 or p == 0.0:
            return "—"
        if p < 0:
            e_kwh = (soc / 100.0) * cap
            hrs = e_kwh / (abs(p) / 1000.0)
            mins = max(0, round(hrs * 60))
            h, m = divmod(mins, 60)
            return f"Bis leer (~{round(soc)}% → 0%): {h}h {m:02d}m"
        else:
            e_kwh = ((100.0 - soc) / 100.0) * cap
            hrs = e_kwh / (p / 1000.0)
            mins = max(0, round(hrs * 60))
            h, m = divmod(mins, 60)
            return f"Bis voll ({round(soc)}% → 100%): {h}h {m:02d}m"
