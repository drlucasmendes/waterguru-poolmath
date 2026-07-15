"""Constants for WaterGuru to PoolMath."""

from homeassistant.const import Platform

DOMAIN = "waterguru_poolmath"
PLATFORMS = [Platform.BUTTON, Platform.SENSOR]

CONF_AUTHORIZATION = "authorization"
CONF_POOL_ID = "pool_id"
CONF_FC_ENTITY = "fc_entity"
CONF_PH_ENTITY = "ph_entity"
CONF_TEMPERATURE_ENTITY = "temperature_entity"

OPT_SUBMIT_TIME = "submit_time"
OPT_AUTO_SUBMIT = "auto_submit"
OPT_MAX_READING_AGE_HOURS = "max_reading_age_hours"

DEFAULT_SUBMIT_TIME = "10:30:00"
DEFAULT_AUTO_SUBMIT = True
DEFAULT_MAX_READING_AGE_HOURS = 30

API_URL = "https://api.poolmathapp.com/testlogs"
CLIENT_VERSION = "512 (512371)"
ORIGIN = "WaterGuru"

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = "waterguru_poolmath"

STATUS_IDLE = "idle"
STATUS_SUBMITTING = "submitting"
STATUS_SUCCESS = "success"
STATUS_DUPLICATE = "duplicate"
STATUS_INVALID = "invalid"
STATUS_ERROR = "error"
STATUS_AUTH_ERROR = "authentication_error"

ATTR_LAST_ERROR = "last_error"
ATTR_LAST_LOG_ID = "last_log_id"
ATTR_LAST_VALUES = "last_values"
ATTR_LAST_SIGNATURE = "last_signature"
