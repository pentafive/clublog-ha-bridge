"""Constants for the ClubLog HA Bridge integration."""

DOMAIN = "clublog"
VERSION = "0.2.1"
USER_AGENT = f"clublog-ha-bridge/{VERSION}"

# Jitter and timing
JITTER_FACTOR = 0.1
MIN_COORDINATOR_INTERVAL = 300  # 5 minutes — coordinator wake cycle

# Attribution
ATTRIBUTION = "Data provided by ClubLog (clublog.org)"

# ClubLog API
CLUBLOG_API_BASE = "https://clublog.org"
CLUBLOG_MATRIX_ENDPOINT = "/json_dxccchart.php"
CLUBLOG_WATCH_ENDPOINT = "/watch.php"
CLUBLOG_MOST_WANTED_ENDPOINT = "/mostwanted.php"
CLUBLOG_ACTIVITY_ENDPOINT = "/activity_json.php"
CLUBLOG_EXPEDITIONS_ENDPOINT = "/expeditions.php"
CLUBLOG_LIVESTREAMS_ENDPOINT = "/livestreams.php"
CLUBLOG_DXCC_ENDPOINT = "/dxcc"

# Configuration keys
CONF_API_KEY = "api_key"
CONF_EMAIL = "email"
CONF_APP_PASSWORD = "app_password"
CONF_CALLSIGN = "callsign"

# Polling intervals (seconds)
CONF_MATRIX_INTERVAL = "matrix_interval"
CONF_WATCH_INTERVAL = "watch_interval"
CONF_MOST_WANTED_INTERVAL = "most_wanted_interval"
CONF_ACTIVITY_INTERVAL = "activity_interval"
CONF_EXPEDITIONS_INTERVAL = "expeditions_interval"
CONF_LIVESTREAMS_INTERVAL = "livestreams_interval"

# Defaults
DEFAULT_MATRIX_INTERVAL = 3600  # 60 min (API cache is 60 min)
DEFAULT_WATCH_INTERVAL = 600  # 10 min
DEFAULT_MOST_WANTED_INTERVAL = 604800  # Weekly (per G7VJR)
DEFAULT_ACTIVITY_INTERVAL = 86400  # Daily (per G7VJR — updated few times/year)
DEFAULT_EXPEDITIONS_INTERVAL = 3600  # 60 min
DEFAULT_LIVESTREAMS_INTERVAL = 600  # 10 min

# DXCC matrix mode values
DXCC_MODE_ALL = 0
DXCC_MODE_CW = 1
DXCC_MODE_PHONE = 2
DXCC_MODE_DATA = 3

# DXCC matrix status values
DXCC_STATUS_CONFIRMED = 1
DXCC_STATUS_WORKED = 2
DXCC_STATUS_VERIFIED = 3

# MQTT discovery (Docker mode)
DEFAULT_HA_DISCOVERY_PREFIX = "homeassistant"
DEFAULT_HA_ENTITY_BASE = "clublog"
