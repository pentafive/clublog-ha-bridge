"""Configuration module for ClubLog HA Bridge (Docker mode)."""

import os
import sys

VERSION = "0.2.1"
USER_AGENT = f"clublog-ha-bridge/{VERSION}"


def str_to_bool(value: str) -> bool:
    """Convert string to boolean."""
    return value.strip().lower() in ("true", "1", "yes", "on")


def str_to_int(value: str, default: int) -> int:
    """Convert string to integer with default."""
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return default


# ClubLog API credentials (REQUIRED)
CLUBLOG_API_KEY = os.environ.get("CLUBLOG_API_KEY", "")
CLUBLOG_EMAIL = os.environ.get("CLUBLOG_EMAIL", "")
CLUBLOG_APP_PASSWORD = os.environ.get("CLUBLOG_APP_PASSWORD", "")
MY_CALLSIGN = os.environ.get("MY_CALLSIGN", "")

# Validate required settings
if not all([CLUBLOG_API_KEY, CLUBLOG_EMAIL, CLUBLOG_APP_PASSWORD, MY_CALLSIGN]):
    print("ERROR: CLUBLOG_API_KEY, CLUBLOG_EMAIL, CLUBLOG_APP_PASSWORD, and MY_CALLSIGN are required")
    sys.exit(1)

# Home Assistant MQTT Broker (REQUIRED)
HA_MQTT_BROKER = os.environ.get("HA_MQTT_BROKER", "")
HA_MQTT_PORT = str_to_int(os.environ.get("HA_MQTT_PORT", "1883"), 1883)
HA_MQTT_USER = os.environ.get("HA_MQTT_USER", "")
HA_MQTT_PASS = os.environ.get("HA_MQTT_PASS", "")

if not HA_MQTT_BROKER:
    print("ERROR: HA_MQTT_BROKER is required")
    sys.exit(1)

# Polling intervals (seconds)
MATRIX_INTERVAL = str_to_int(os.environ.get("MATRIX_INTERVAL", "3600"), 3600)
WATCH_INTERVAL = str_to_int(os.environ.get("WATCH_INTERVAL", "600"), 600)
MOST_WANTED_INTERVAL = str_to_int(os.environ.get("MOST_WANTED_INTERVAL", "604800"), 604800)
ACTIVITY_INTERVAL = str_to_int(os.environ.get("ACTIVITY_INTERVAL", "86400"), 86400)
EXPEDITIONS_INTERVAL = str_to_int(os.environ.get("EXPEDITIONS_INTERVAL", "3600"), 3600)
LIVESTREAMS_INTERVAL = str_to_int(os.environ.get("LIVESTREAMS_INTERVAL", "600"), 600)

# Jitter
JITTER_FACTOR = 0.1

# Home Assistant Discovery
HA_DISCOVERY_PREFIX = os.environ.get("HA_DISCOVERY_PREFIX", "homeassistant")
HA_ENTITY_BASE = os.environ.get("HA_ENTITY_BASE", "clublog")

# Debugging
DEBUG_MODE = str_to_bool(os.environ.get("DEBUG_MODE", "False"))
