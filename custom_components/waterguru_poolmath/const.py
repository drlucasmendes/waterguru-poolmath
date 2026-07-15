"""Constants for WaterGuru to PoolMath."""

from homeassistant.const import Platform

DOMAIN = "waterguru_poolmath"
PLATFORMS = [Platform.BUTTON, Platform.SENSOR]

CONF_AUTHORIZATION = "authorization"
CONF_AUTH_METHOD = "auth_method"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_POOL_ID = "pool_id"
CONF_POOL_NAME = "pool_name"
CONF_USER_ID = "user_id"

AUTH_METHOD_LOGIN = "login"
AUTH_METHOD_BASIC = "basic"

# Required daily WaterGuru/SENSE measurements.
CONF_FC_ENTITY = "fc_entity"
CONF_PH_ENTITY = "ph_entity"
CONF_TEMPERATURE_ENTITY = "temperature_entity"

# Optional values that PoolMath's test-log endpoint supports.
CONF_CC_ENTITY = "cc_entity"
CONF_CYA_ENTITY = "cya_entity"
CONF_CH_ENTITY = "ch_entity"
CONF_TA_ENTITY = "ta_entity"
CONF_SALT_ENTITY = "salt_entity"
CONF_BOR_ENTITY = "bor_entity"
CONF_TDS_ENTITY = "tds_entity"
CONF_CSI_ENTITY = "csi_entity"

# Optional WaterGuru values without a matching PoolMath test-log field.
CONF_TOTAL_HARDNESS_ENTITY = "total_hardness_entity"
CONF_PHOSPHATE_ENTITY = "phosphate_entity"
CONF_COPPER_ENTITY = "copper_entity"
CONF_IRON_ENTITY = "iron_entity"

POOLMATH_OPTIONAL_ENTITY_FIELDS = {
    "cc": CONF_CC_ENTITY,
    "cya": CONF_CYA_ENTITY,
    "ch": CONF_CH_ENTITY,
    "ta": CONF_TA_ENTITY,
    "salt": CONF_SALT_ENTITY,
    "bor": CONF_BOR_ENTITY,
    "tds": CONF_TDS_ENTITY,
    "csi": CONF_CSI_ENTITY,
}

UNMAPPED_WATERGURU_ENTITY_FIELDS = {
    "total_hardness": CONF_TOTAL_HARDNESS_ENTITY,
    "phosphate": CONF_PHOSPHATE_ENTITY,
    "copper": CONF_COPPER_ENTITY,
    "iron": CONF_IRON_ENTITY,
}

OPT_SUBMIT_TIME = "submit_time"
OPT_TIME_ZONE = "time_zone"
OPT_AUTO_SUBMIT = "auto_submit"
OPT_MAX_READING_AGE_HOURS = "max_reading_age_hours"

DEFAULT_SUBMIT_TIME = "10:30:00"
DEFAULT_AUTO_SUBMIT = True
DEFAULT_MAX_READING_AGE_HOURS = 30

API_BASE_URL = "https://api.poolmathapp.com"
API_AUTH_URL = f"{API_BASE_URL}/auth"
API_POOLS_URL = f"{API_BASE_URL}/pools/list"
API_TESTLOGS_URL = f"{API_BASE_URL}/testlogs"

CLIENT_VERSION = "512 (512371)"
LOGIN_DEVICE_NAME = "Home Assistant WaterGuru to PoolMath"
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
ATTR_LAST_UNMAPPED_VALUES = "last_unmapped_values"
ATTR_LAST_SIGNATURE = "last_signature"
