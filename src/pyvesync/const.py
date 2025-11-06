"""pyvesync library constants.

All device states and information are defined by Enums in this module.

Attributes:
    DEFAULT_LANGUAGE (str): Default language for the VeSync app.
    API_BASE_URL (str): Base URL for the VeSync API. If not specified,
        a region-specific API URL is automatically selected.
    API_TIMEOUT (int): Timeout for API requests.
    USER_AGENT (str): User agent for API requests.
    DEFAULT_TZ (str): Default timezone for VeSync devices, updated by API after
        login.
    DEFAULT_REGION (str): Default region for VeSync devices,
        updated by API when retrieving devices.
    APP_VERSION (str): Version of the VeSync app.
    APP_ID (str): ID of the app. VeSync uses a random 8-letter string, but any non-empty
        string works.
    PHONE_BRAND (str): Brand of the phone used to login to the VeSync app.
    PHONE_OS (str): Operating system of the phone used to login to the VeSync app.
    MOBILE_ID (str): Unique identifier for the phone used to login to the VeSync app.
    USER_TYPE (str): User type for the VeSync app - internal app usage.
    BYPASS_APP_V (str): Bypass app version
    BYPASS_HEADER_UA (str): Bypass header user agent
    TERMINAL_ID (str): Unique identifier for new API calls
"""

from __future__ import annotations

import platform
import string
import uuid
from enum import Enum, IntEnum, StrEnum
from random import choices, randint
from types import MappingProxyType

from pyvesync.utils.enum_utils import IntEnumMixin

MAX_API_REAUTH_RETRIES = 3
DEFAULT_LANGUAGE = 'en'
API_BASE_URL = None  # Global URL (non-EU regions): "https://smartapi.vesync.com"
# If device is out of reach, the cloud api sends a timeout response after 7 seconds,
# using 8 here so there is time enough to catch that message
API_BASE_URL_US = 'https://smartapi.vesync.com'
API_BASE_URL_EU = 'https://smartapi.vesync.eu'
REGION_API_MAP = {
    'US': API_BASE_URL_US,
    'EU': API_BASE_URL_EU,
}
NON_EU_COUNTRY_CODES = ['US', 'CA', 'MX', 'JP']
API_TIMEOUT = 8
USER_AGENT = (
    'VeSync/3.2.39 (com.etekcity.vesyncPlatform; build:5; iOS 15.5.0) Alamofire/5.2.1'
)
DEFAULT_TZ = 'America/New_York'
DEFAULT_REGION = 'US'
APP_VERSION = '5.6.60'
APP_ID = ''.join(choices(string.ascii_lowercase + string.digits, k=8))  # noqa: S311
PHONE_BRAND = 'pyvesync'
PHONE_OS = 'Android'
MOBILE_ID = str(randint(1000000000000000, 9999999999999999))  # noqa: S311
USER_TYPE = '1'
BYPASS_APP_V = f'VeSync {APP_VERSION}'
BYPASS_HEADER_UA = 'okhttp/3.12.1'
TERMINAL_ID = '2' + (
    uuid.uuid5(uuid.NAMESPACE_DNS, f'{uuid.getnode():x}-{platform.node() or ""}').hex
)

CLIENT_TYPE = 'vesyncApp'

STATUS_OK = 200


# Generic Constants

KELVIN_MIN = 2700
KELVIN_MAX = 6500


class ProductLines(StrEnum):
    """High level product line."""

    WIFI_LIGHT = 'wifi-light'
    WIFI_AIR = 'wifi-air'
    WIFI_KITCHEN = 'wifi-kitchen'
    SWITCHES = 'Switches'
    WIFI_SWITCH = 'wifi-switch'
    THERMOSTAT = 'thermostat'


class ProductTypes(StrEnum):
    """General device types enum."""

    OUTLET = 'outlet'
    BULB = 'bulb'
    SWITCH = 'switch'
    PURIFIER = 'purifier'
    FAN = 'fan'
    HUMIDIFIER = 'humidifier'
    AIR_FRYER = 'air fryer'
    KITCHEN_THERMOMETER = 'kitchen thermometer'
    THERMOSTAT = 'thermostat'


class IntFlag(IntEnum):
    """DEPRECATED. Integer flag to indicate if a device is not supported.

    This is used by data models as a default value for feature attributes
    that are not supported by all devices.

    The default value is -999.

    Attributes:
        NOT_SUPPORTED: Device is not supported, -999
    """

    NOT_SUPPORTED = -999

    def __str__(self) -> str:
        """Return string representation of IntFlag."""
        return str(self.name)


class StrFlag(StrEnum):
    """DEPRECATED. String flag to indicate if a device is not supported.

    This is used by data models as a default value for feature attributes
    that are not supported by all devices.

    The default value is "not_supported".

    Attributes:
        NOT_SUPPORTED: Device is not supported, "not_supported"
    """

    NOT_SUPPORTED = 'not_supported'


class NightlightStatus(StrEnum):
    """Nightlight status for VeSync devices.

    Values can be converted to int and bool.

    Attributes:
        ON: Nightlight is on.
        OFF: Nightlight is off.
        AUTO: Nightlight is in auto mode.
        UNKNOWN: Nightlight status is unknown.

    Usage:
        ```python
        NightlightStatus.ON
        # <NightlightStatus.ON: 'on'>
        int(NightlightStatus.ON)
        # 1
        bool(NightlightStatus.ON)
        # True
        ```
    """

    ON = 'on'
    OFF = 'off'
    AUTO = 'auto'
    UNKNOWN = 'unknown'

    def __bool__(self) -> bool:
        """Return True if nightlight is on or auto."""
        return self in [NightlightStatus.ON, NightlightStatus.AUTO]

    def __int__(self) -> int:
        """Return integer representation of the enum."""
        if self not in [NightlightStatus.ON, NightlightStatus.OFF]:
            raise ValueError('Only ON and OFF are valid values for int conversion')
        return int(self == NightlightStatus.ON)


class DeviceStatus(StrEnum):
    """VeSync device status enum.

    In addition to converting to int and bool values,
    this enum can be used to convert from bool and int values
    to corresponding string values.

    Attributes:
        ON: Device is on.
        OFF: Device is off.
        PAUSED: Device is paused.
        STANDBY: Device is in standby mode.
        IDLE: Device is idle.
        RUNNING: Device is running.
        UNKNOWN: Device status is unknown.

    Usage:
        ```python
        DeviceStatus.ON
        # <DeviceStatus.ON: 'on'>
        bool(DeviceStatus.ON)
        # True
        int(DeviceStatus.ON)
        # 1
        DeviceStatus.from_int(1)
        # 'on'
        DeviceStatus.from_bool(True)
        # 'on'
        ```
    """

    ON = 'on'
    OFF = 'off'
    PAUSED = 'paused'
    STANDBY = 'standby'
    IDLE = 'idle'
    RUNNING = 'running'
    UNKNOWN = 'unknown'

    def __bool__(self) -> bool:
        """Return True if device is on or running."""
        return self in [DeviceStatus.ON, DeviceStatus.RUNNING]

    def __int__(self) -> int:
        """Return integer representation of the enum.

        1 is ON and RUNNING, 0 is OFF, PAUSED, STANDBY, IDLE.
        -1 is UNKNOWN.
        """
        match self:
            case DeviceStatus.ON | DeviceStatus.RUNNING:
                return 1
            case (
                DeviceStatus.OFF
                | DeviceStatus.PAUSED
                | DeviceStatus.STANDBY
                | DeviceStatus.IDLE
            ):
                return 0
        return -1

    @classmethod
    def from_int(cls, value: int | None) -> str:
        """Convert integer value to corresponding string.

        If value is 1, return ON and if 0, return OFF.
        If value is -999, return NOT_SUPPORTED.
        """
        if value == 1:
            return cls.ON
        if value == 0:
            return cls.OFF
        if value == IntFlag.NOT_SUPPORTED:
            return StrFlag.NOT_SUPPORTED
        return cls.UNKNOWN

    @classmethod
    def from_bool(cls, value: bool | str) -> DeviceStatus:
        """Convert boolean value to corresponding string."""
        if isinstance(value, str):
            return cls.from_bool_string(value)
        return cls.ON if value is True else cls.OFF

    @classmethod
    def from_bool_string(cls, value: str) -> DeviceStatus:
        """Convert boolean value to corresponding string."""
        return cls.ON if value == 'true' else cls.OFF


class ConnectionStatus(StrEnum):
    """VeSync device connection status enum.

    Corresponding boolean value is True if device is online.

    Attributes:
        ONLINE: Device is online.
        OFFLINE: Device is offline.
        UNKNOWN: Device connection status is unknown.

    Methods:
        from_bool(value: bool | None) -> ConnectionStatus:
            Convert boolean value to corresponding string.

    Usage:
        ```python
        ConnectionStatus.ONLINE
        # <ConnectionStatus.ONLINE: 'online'>
        bool(ConnectionStatus.ONLINE)
        # True
        ConnectionStatus.ONLINE == ConnectionStatus.ONLINE
        # True
        ```
    """

    ONLINE = 'online'
    OFFLINE = 'offline'
    UNKNOWN = 'unknown'

    def __bool__(self) -> bool:
        """Return True if device is online."""
        return self == ConnectionStatus.ONLINE

    @classmethod
    def from_bool(cls, value: bool | None) -> ConnectionStatus:
        """Convert boolean value to corresponding string.

        Returns ConnectionStatus.ONLINE if True, else ConnectionStatus.OFFLINE.
        """
        return cls.ONLINE if value else cls.OFFLINE


class NightlightModes(StrEnum):
    """Nightlight modes.

    Attributes:
        ON: Nightlight is on.
        OFF: Nightlight is off.
        DIM: Nightlight is dimmed.
        AUTO: Nightlight is in auto mode.
        UNKNOWN: Nightlight status is unknown.
    """

    ON = 'on'
    OFF = 'off'
    DIM = 'dim'
    AUTO = 'auto'
    UNKNOWN = 'unknown'

    def __bool__(self) -> bool:
        """Return True if nightlight is on or auto.

        Off and unknown are False, all other True.
        """
        return self in [NightlightModes.ON, NightlightModes.AUTO, NightlightModes.DIM]


class ColorMode(StrEnum):
    """VeSync bulb color modes.

    Attributes:
        RGB: RGB color mode.
        HSV: HSV color mode.
        WHITE: White color mode.
        COLOR: Color mode.
    """

    RGB = 'rgb'
    HSV = 'hsv'
    WHITE = 'white'
    COLOR = 'color'


# Purifier Constants


class AirQualityLevel(Enum):
    """Representation of air quality levels as string and integers.

    Attributes:
        EXCELLENT: Air quality is excellent.
        GOOD: Air quality is good.
        MODERATE: Air quality is moderate.
        POOR: Air quality is poor.
        UNKNOWN: Air quality is unknown.

    Methods:
        from_string(value: str | None) -> AirQualityLevel:
            Convert string value to corresponding integer.
        from_int(value: int | None) -> AirQualityLevel:
            Convert integer value to corresponding string.

    Note:
        Alias for "very good" is "excellent".
        Alias for "bad" is "poor".

    Usage:
        ```python
        AirQualityLevels.EXCELLENT
        # <AirQualityLevels.EXCELLENT: 1>
        AirQualityLevels.from_string("excellent")
        # 1
        AirQualityLevels.from_int(1)
        # "excellent"
        int(AirQualityLevels.EXCELLENT)
        # 1
        str(AirQualityLevels.EXCELLENT)
        # "excellent"
        from_string("good")
        # <AirQualityLevels.GOOD: 2>
        from_int(2)
        # "good"
        ```
    """

    EXCELLENT = 1
    GOOD = 2
    MODERATE = 3
    POOR = 4
    UNKNOWN = -1

    def __int__(self) -> int:
        """Return integer representation of the enum."""
        return self.value

    def __str__(self) -> str:
        """Return string representation of the enum."""
        return self.name.lower()

    @classmethod
    def from_string(cls, value: str | None) -> AirQualityLevel:
        """Convert string value to corresponding integer.

        Get enum from string value to normalize different values of the same
        format.

        Note:
            Values are excellent, good, moderate and poor. Aliases are:
            very good for excellent and bad for poor. Unknown is returned
            if value is None or not in the list.
        """
        _string_to_enum = MappingProxyType(
            {
                'excellent': cls.EXCELLENT,
                'very good': cls.EXCELLENT,  # Alias
                'good': cls.GOOD,
                'moderate': cls.MODERATE,
                'poor': cls.POOR,
                'bad': cls.POOR,  # Alias
                'unknown': cls.UNKNOWN,
            }
        )
        if isinstance(value, str) and value.lower() in _string_to_enum:
            return AirQualityLevel(_string_to_enum[value.lower()])
        return cls.UNKNOWN

    @classmethod
    def from_int(cls, value: int | None) -> AirQualityLevel:
        """Convert integer value to corresponding string."""
        if value in [itm.value for itm in cls]:
            return cls(value)
        return cls.UNKNOWN


class PurifierAutoPreference(StrEnum):
    """Preference Levels for Purifier Auto Mode.

    Attributes:
        DEFAULT: Default preference level.
        EFFICIENT: Efficient preference level.
        QUIET: Quiet preference level.
        UNKNOWN: Unknown preference level.
    """

    DEFAULT = 'default'
    EFFICIENT = 'efficient'
    QUIET = 'quiet'
    UNKNOWN = 'unknown'


# Fan Constants


class FanSleepPreference(StrEnum):
    """Sleep mode preferences for VeSync fans.

    Attributes:
        DEFAULT: Default sleep mode.
        ADVANCED: Advanced sleep mode.
        TURBO: Turbo sleep mode.
        EFFICIENT: Efficient sleep mode.
        QUIET: Quiet sleep mode.
        UNKNOWN: Unknown sleep mode.
    """

    DEFAULT = 'default'
    ADVANCED = 'advanced'
    TURBO = 'turbo'
    EFFICIENT = 'efficient'
    QUIET = 'quiet'
    TEMP_SENSE = 'tempSense'
    KIDS = 'kids'
    UNKNOWN = 'unknown'


# Device Features


class Features(StrEnum):
    """Base Class for Features Enum to appease typing."""


# Device Features


class HumidifierFeatures(Features):
    """VeSync humidifier features.

    Attributes:
        ONOFF: Device on/off status.
        CHILD_LOCK: Child lock status.
        NIGHTLIGHT: Nightlight status.
        WATER_LEVEL: Water level status.
        WARM_MIST: Warm mist status.
        AUTO_STOP: Auto stop when target humidity is reached.
            Different from auto, which adjusts fan level to maintain humidity.
    """

    ONOFF = 'onoff'
    CHILD_LOCK = 'child_lock'
    NIGHTLIGHT = 'night_light'
    WATER_LEVEL = 'water_level'
    WARM_MIST = 'warm_mist'
    AUTO_STOP = 'auto_stop'
    NIGHTLIGHT_BRIGHTNESS = 'nightlight_brightness'
    DRYING_MODE = 'drying_mode'


class PurifierFeatures(Features):
    """VeSync air purifier features.

    Attributes:
        CHILD_LOCK: Child lock status.
        NIGHTLIGHT: Nightlight status.
        AIR_QUALITY: Air quality status.
        VENT_ANGLE: Vent angle status.
        LIGHT_DETECT: Light detection status.
        PM25: PM2.5 level status.
        PM10: PM10 level status.
        PM1: PM1 level status.
        AQPERCENT: Air quality percentage status.
        RESET_FILTER: Reset filter status.
    """

    RESET_FILTER = 'reset_filter'
    CHILD_LOCK = 'child_lock'
    NIGHTLIGHT = 'night_light'
    AIR_QUALITY = 'air_quality'
    VENT_ANGLE = 'fan_rotate'
    LIGHT_DETECT = 'light_detect'
    PM25 = 'pm25'
    PM10 = 'pm10'
    PM1 = 'pm1'
    AQPERCENT = 'aq_percent'


class PurifierStringLevels(Features):
    """String levels for Air Purifier fan speed.

    Attributes:
        LOW: Low fan speed.
        MEDIUM: Medium fan speed.
        HIGH: High fan speed.
    """

    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'


class BulbFeatures(Features):
    """VeSync bulb features.

    Attributes:
        ONOFF: Device on/off status.
        DIMMABLE: Dimmable status.
        COLOR_TEMP: Color temperature status.
        MULTICOLOR: Multicolor status.
    """

    ONOFF = 'onoff'
    DIMMABLE = 'dimmable'
    COLOR_TEMP = 'color_temp'
    MULTICOLOR = 'multicolor'


class OutletFeatures(Features):
    """VeSync outlet features.

    Attributes:
        ONOFF: Device on/off status.
        ENERGY_MONITOR: Energy monitor status.
        NIGHTLIGHT: Nightlight status.
    """

    ONOFF = 'onoff'
    ENERGY_MONITOR = 'energy_monitor'
    NIGHTLIGHT = 'nightlight'


class SwitchFeatures(Features):
    """VeSync switch features.

    Attributes:
        ONOFF: Device on/off status.
        DIMMABLE: Dimmable status.
        INDICATOR_LIGHT: Indicator light status.
        BACKLIGHT: Backlight status.
        BACKLIGHT_RGB: RGB backlight status.
    """

    ONOFF = 'onoff'
    DIMMABLE = 'dimmable'
    INDICATOR_LIGHT = 'indicator_light'
    BACKLIGHT = 'backlight'
    BACKLIGHT_RGB = 'backlight_rgb'


class FanFeatures(Features):
    """VeSync fan features."""

    OSCILLATION = 'oscillation'
    SET_OSCILLATION_RANGE = 'set_oscillation_range'
    SOUND = 'sound'
    DISPLAYING_TYPE = 'displaying_type'  # Unknown functionality
    HORIZONTAL_OSCILLATION = 'horizontal_oscillation'
    VERTICAL_OSCILLATION = 'vertical_oscillation'


# Modes


class PurifierModes(Features):
    """VeSync air purifier modes.

    Attributes:
        AUTO: Auto mode.
        MANUAL: Manual mode.
        SLEEP: Sleep mode.
        TURBO: Turbo mode.
        PET: Pet mode.
        UNKNOWN: Unknown mode.
    """

    AUTO = 'auto'
    MANUAL = 'manual'
    SLEEP = 'sleep'
    TURBO = 'turbo'
    PET = 'pet'
    UNKNOWN = 'unknown'


class HumidifierModes(Features):
    """VeSync humidifier modes.

    Attributes:
        AUTO: Auto mode.
        MANUAL: Manual mode.
        HUMIDITY: Humidity mode.
        SLEEP: Sleep mode.
        TURBO: Turbo mode.
        PET: Pet mode.
        UNKNOWN: Unknown mode.
        AUTOPRO: AutoPro mode.
    """

    AUTO = 'auto'
    MANUAL = 'manual'
    HUMIDITY = 'humidity'
    SLEEP = 'sleep'
    TURBO = 'turbo'
    PET = 'pet'
    UNKNOWN = 'unknown'


class FanModes(StrEnum):
    """VeSync fan modes.

    Attributes:
        AUTO: Auto mode.
        NORMAL: Normal mode.
        MANUAL: Manual mode.
        SLEEP: Sleep mode.
        TURBO: Turbo mode.
        PET: Pet mode.
        UNKNOWN: Unknown mode.
        ADVANCED_SLEEP: Advanced sleep mode.
    """

    AUTO = 'auto'
    NORMAL = 'normal'
    MANUAL = 'normal'
    SLEEP = 'advancedSleep'
    TURBO = 'turbo'
    PET = 'pet'
    ECO = 'eco'
    UNKNOWN = 'unknown'
    ADVANCED_SLEEP = 'advancedSleep'


# Air Fryer Constants

AIRFRYER_PID_MAP = {
    'WiFi_SKA_AirFryer137_US': 'wnxwqs76gknqyzjn',
    'WiFi_SKA_AirFryer158_US': '2cl8hmafsthl65bd',
    'WiFi_AirFryer_CS158-AF_EU': '8t8op7pcvzlsbosm',
}
"""PID's for VeSync Air Fryers based on ConfigModule."""


# Thermostat Constants


class ThermostatWorkModes(IntEnum):
    """Working modes for VeSync Aura thermostats.

    Based on the VeSync app and API values.

    Attributes:
        OFF: Thermostat is off (0).
        HEAT: Thermostat is in heating mode (1).
        COOL: Thermostat is in cooling mode (2).
        AUTO: Thermostat is in auto mode (3).
        EM_HEAT: Thermostat is in emergency heating mode (4).
        SMART_AUTO: Thermostat is in smart auto mode (5).
    """

    OFF = 0
    HEAT = 1
    COOL = 2
    AUTO = 3
    EM_HEAT = 4
    SMART_AUTO = 5


class ThermostatFanModes(IntEnum):
    """Fan modes for VeSync Aura thermostats.

    Based on the VeSync app and API values.

    Attributes:
        AUTO: Fan is in auto mode (1).
        ON: Fan is on (2).
        CIRCULATE: Fan is in circulate mode (3).
    """

    AUTO = 1
    ON = 2
    CIRCULATE = 3


class ThermostatHoldOptions(IntEnumMixin):
    """Hold options for VeSync Aura thermostats.

    Attributes:
        UNTIL_NEXT_SCHEDULED_ITEM: Hold until next scheduled item (2).
        TWO_HOURS: Hold for two hours (3).
        FOUR_HOURS: Hold for four hours (4).
        PERMANENTLY: Hold permanently (5).
    """

    UNTIL_NEXT_SCHEDULED_ITEM = 2
    TWO_HOURS = 3
    FOUR_HOURS = 4
    PERMANENTLY = 5


class ThermostatHoldStatus(IntEnumMixin):
    """Set the hold status of the thermostat.

    Attributes:
        SET: Set the hold status (1).
        CANCEL: Cancel the hold status (0).
    """

    SET = 1
    CANCEL = 0


class ThermostatScheduleOrHoldOptions(IntEnumMixin):
    """Schedule or hold options for VeSync Aura thermostats."""

    NOT_SCHEDULE_NOT_HOLD = 0
    ON_SCHEDULE = 1
    ON_HOLD = 2
    VACATION = 3


class ThermostatEcoTypes(IntEnumMixin):
    """Eco types for VeSync Aura thermostats."""

    COMFORT_SECOND = 1
    COMFORT_FIRST = 2
    BALANCE = 3
    ECO_FIRST = 4
    ECO_SECOND = 5


class ThermostatRoutineTypes(IntEnumMixin):
    """Routine types for VeSync Aura thermostats."""

    HOME = 2
    AWAY = 1
    SLEEP = 3
    CUSTOM = 4


class ThermostatAlarmCodes(IntEnumMixin):
    """Alarm codes for VeSync Aura thermostats."""

    HEAT_COOL = 100
    ABOVE_SAFE_TEMP = 102
    HEAT_RUNNING_TIME_TOO_LONG = 104


class ThermostatReminderCodes(IntEnumMixin):
    """Reminder codes for VeSync Aura thermostats."""

    FILTER = 150
    HVAC = 151


class ThermostatWorkStatusCodes(IntEnumMixin):
    """Work status codes for VeSync Aura thermostats."""

    OFF = 0
    HEATING = 1
    COOLING = 2
    EM_HEATING = 3


class ThermostatFanStatus(IntEnumMixin):
    """Fan Status Enum for Aura Thermostats."""

    OFF = 0
    ON = 1


class ThermostatConst:
    """Constants for VeSync Aura thermostats."""

    ReminderCode = ThermostatReminderCodes
    AlarmCode = ThermostatAlarmCodes
    WorkMode = ThermostatWorkModes
    FanStatus = ThermostatFanStatus
    FanMode = ThermostatFanModes
    HoldOption = ThermostatHoldOptions
    EcoType = ThermostatEcoTypes
    RoutineType = ThermostatRoutineTypes
    ScheduleOrHoldOption = ThermostatScheduleOrHoldOptions
    WorkStatus = ThermostatWorkStatusCodes


#  ------------------- AIR FRYER CONST ------------------ #


CUSTOM_RECIPE_ID = 1
CUSTOM_RECIPE_TYPE = 3
CUSTOM_RECIPE_NAME = 'Manual Cook'
CUSTOM_COOK_MODE = 'custom'


# ------------------- OUTLET CONST ------------------ #


class EnergyIntervals(StrEnum):
    """Energy history periods for VeSync outlets.

    Attributes:
        DAILY: Daily energy history.
        WEEKLY: Weekly energy history.
        MONTHLY: Monthly energy history.
        YEARLY: Yearly energy history.
    """

    WEEK = 'week'
    MONTH = 'month'
    YEAR = 'year'


ENERGY_HISTORY_MAP = {
    EnergyIntervals.WEEK: 'getLastWeekEnergy',
    EnergyIntervals.MONTH: 'getLastMonthEnergy',
    EnergyIntervals.YEAR: 'getLastYearEnergy',
}

ENERGY_HISTORY_OFFSET_WHOGPLUG = {
    EnergyIntervals.WEEK: 500000,
    EnergyIntervals.MONTH: 2500000,
}

# ------------------- HUMIDIFIER CONST ------------------ #


class DryingModes(StrEnum):
    """Drying modes for VeSync humidifiers.

    Attributes:
        ON: Drying mode is on.
        OFF: Drying mode is off.
    """

    DONE = 'done'
    RUNNING = 'on'
    PAUSE = 'pause'


DRYING_MODES: dict[str, int] = {
    DryingModes.DONE: 0,
    DryingModes.RUNNING: 1,
    DryingModes.PAUSE: 2,
}
