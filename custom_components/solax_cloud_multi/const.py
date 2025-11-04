from __future__ import annotations

DOMAIN = "solax_cloud_multi"

MANUFACTURER = "SolaX Power"

CONF_TOKEN = "token_id"
CONF_DEVICES = "devices"
CONF_WIFI_SN = "wifi_sn"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_USE_PREFIX = "use_prefix"

DEFAULT_SCAN_INTERVAL = 60  # seconds
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 300

API_TIMEOUT = 20

SENSOR_MAP: dict[str, dict[str, str | None]] = {
    "acpower": {"name": "AC Power", "unit": "W", "device_class": "power"},
    "feedinpower": {"name": "Feed-in Power", "unit": "W", "device_class": "power"},
    "batPower": {"name": "Battery Power", "unit": "W", "device_class": "power"},
    "soc": {"name": "Battery SoC", "unit": "%", "device_class": "battery"},
    "battemper": {
        "name": "Battery Temperature",
        "unit": "°C",
        "device_class": "temperature",
    },
    "batcycle": {"name": "Battery Cycles", "unit": None, "device_class": None},
    # Derived from the raw feed-in power value
    "export_power": {"name": "Export Power", "unit": "W", "device_class": "power"},
    "import_power": {"name": "Import Power", "unit": "W", "device_class": "power"},
}

NUMERIC_SENSOR_KEYS: tuple[str, ...] = (
    "acpower",
    "feedinpower",
    "batPower",
    "soc",
    "battemper",
    "batcycle",
)

