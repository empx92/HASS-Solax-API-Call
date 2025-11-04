"""Sensor platform for SolaX Cloud Multi."""
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
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
    devices = entry.options.get(CONF_DEVICES, [])
    use_prefix = entry.options.get(CONF_USE_PREFIX, False)

    entities = []

    for device in devices:
        wifi_sn = device[CONF_WIFI_SN]
        name = device.get(CONF_NAME, "Unknown")
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
            entities.append(SolaxSensor(coordinator, wifi_sn, description))

    async_add_entities(entities)


class SolaxSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, wifi_sn, description):
        super().__init__(coordinator)
        self._wifi_sn = wifi_sn
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{wifi_sn}_{description.key}"

    @property
    def native_value(self):
        coordinator_data = self.coordinator.data or {}
        data = coordinator_data.get(self._wifi_sn) or {}
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
