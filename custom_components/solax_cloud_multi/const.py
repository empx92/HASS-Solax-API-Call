from datetime import timedelta

DOMAIN = "solax_cloud_multi"

CONF_TOKEN = "token_id"
CONF_DEVICES = "devices"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_USE_PREFIX = "use_prefix"

DEFAULT_SCAN_INTERVAL = 60

API_URL = "https://www.solaxcloud.com/api/v2/dataAccess/realtimeInfo/get"
API_TIMEOUT = 20

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
    "export_power": {"name": "Export Power", "unit": "W", "device_class": "power"},
    "import_power": {"name": "Import Power", "unit": "W", "device_class": "power"},
    "batPower": {"name": "Battery Power", "unit": "W", "device_class": "power"},
    "soc": {"name": "Battery SoC", "unit": "%", "device_class": "battery"},
    "battemper": {"name": "Battery Temperature", "unit": "°C", "device_class": "temperature"},
    "batcycle": {"name": "Battery Cycles", "unit": None, "device_class": None},
}
