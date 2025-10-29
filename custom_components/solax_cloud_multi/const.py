
from datetime import timedelta

DOMAIN = "solax_cloud_multi"

CONF_TOKEN = "token_id"
CONF_DEVICES = "devices"          # list of dicts: {wifi_sn,name,battery_kwh}
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 15  # seconds

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
}
