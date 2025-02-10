"""pyvesync library constants."""

# Default time-zone
DEFAULT_TZ: str = 'America/New_York'

# Defaul region for time-zone
DEFAULT_REGION: str = 'US'

APP_VERSION = '4.3.40'

BYPASS_HEADER_UA = 'okhttp/3.12.1'

API_RATE_LIMIT: int = 30

PHONE_BRAND = 'SM N9005'
PHONE_OS = 'Android'

DEFAULT_ENER_UP_INT: int = 21600

ENERGY_WEEK: str = 'week'
ENERGY_MONTH: str = 'month'
ENERGY_YEAR: str = 'year'
PERIOD_2_DAYS: dict[str, int] = {ENERGY_WEEK: 7, ENERGY_MONTH: 30, ENERGY_YEAR: 365}

MOBILE_ID: str = '1234567890123456'
USER_TYPE: str = '1'

# Error Codes
ERR_DEV_OFFLINE: int = -11300027    # device offline
ERR_WRONG_ARG_1: int = -11000086    # Wrong argument
ERR_WRONG_ARG_2: int = -11103086    # Wrong argument
ERR_REQ_TIMEOUT_1: int = -11300030  # request timeout
ERR_REQ_TIMEOUT_2: int = -11302030  # request timeout
ERR_REQ_TIMEOUTS: list[int] = [ERR_REQ_TIMEOUT_1, ERR_REQ_TIMEOUT_2]
ERR_RATE_LIMITS: list[int] = [ERR_WRONG_ARG_1, ERR_WRONG_ARG_2]

STATUS_ON = 'on'
STATUS_OFF = 'off'

MODE_ADVANCED_SLEEP = 'advancedSleep'
MODE_AUTO = 'auto'
MODE_DIM = 'dim'
MODE_HUMIDITY = 'humidity'
MODE_MANUAL = 'manual'
MODE_NORMAL = 'normal'
MODE_PET = 'pet'
MODE_SLEEP = 'sleep'
MODE_TURBO = 'turbo'
