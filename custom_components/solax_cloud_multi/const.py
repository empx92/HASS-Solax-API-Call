from datetime import timedelta

DOMAIN = "solax_cloud_multi"

CONF_TOKEN = "token_id"
CONF_DEVICES = "devices"          # list of dicts: {wifi_sn,name,battery_kwh}
CONF_SCAN_INTERVAL = "scan_interval"
CONF_WIFI_SN = "wifi_sn"           # Neu: Definierte Konstante (war fehlend)
CONF_NAME = "name"                 # Neu: Für Name-Dropdown
CONF_USE_PREFIX = "use_prefix"     # Für clean names

DEFAULT_SCAN_INTERVAL = 60  # seconds

API_URL = "https://www.solaxcloud.com/api/v2/dataAccess/realtimeInfo/get"
API_TIMEOUT = 20

# Keys in API "result"
KEYS = [
    "acpower",
    "feedinpower",
    "batPower",
    "soc",
    "battemper",
    "batcycle",
    "inverterSn",
    "sn",
    "uploadTime",
]

SENSOR_MAP = {
    "acpower": {"name": "AC Power", "unit": "W", "device_class": "power"},
    "feedinpower": {"name": "Feed-in Power", "unit": "W", "device_class": "power"},
    "batPower": {"name": "Battery Power", "unit": "W", "device_class": "power"},
    "soc": {"name": "Battery SoC", "unit": "%", "device_class": "battery"},
    "battemper": {"name": "Battery Temperature", "unit": "°C", "device_class": "temperature"},
    "batcycle": {"name": "Battery Cycles", "unit": None, "device_class": None},
    # Neu: Export/Import (berechnet aus feedinpower)
    "export_power": {"name": "Export Power", "unit": "W", "device_class": "power"},
    "import_power": {"name": "Import Power", "unit": "W", "device_class": "power"},
}
