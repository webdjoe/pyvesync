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
import uuid
from dataclasses import dataclass
from enum import Enum, IntEnum, StrEnum
from random import randint
from types import MappingProxyType

from pyvesync.utils.enum_utils import IntEnumMixin

MAX_API_REAUTH_RETRIES = 3
"""Most re-logins after a rejected token within `REAUTH_WINDOW_SECONDS`."""
REAUTH_WINDOW_SECONDS = 300
"""Window for `MAX_API_REAUTH_RETRIES`; the count starts over once it passes."""
API_TOKEN_KEYS = ('token', 'tk')
"""Request body (`token`) and header (`tk`) keys that carry the login token."""
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
APP_ID = 'eldodkfj'
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

UNKNOWN_ERROR_CODE = '-999999999'
"""`ErrorCodes.errors` key of the `UNKNOWN` entry (the app's `CloudErrorCode.UNKNOWN`)."""


# Generic Constants

KELVIN_MIN = 2700
KELVIN_MAX = 6500

# RGB nightlight constants
RGB_STALE_DATA_TIMEOUT = 180  # Seconds to ignore stale API data after setting values
RGB_FULL_BRIGHTNESS = 100  # Full brightness percentage


class TimeUnits(StrEnum):
    """Time units for VeSync devices.

    Attributes:
        MINUTES: Time in minutes.
        SECONDS: Time in seconds.
        HOURS: Time in hours.
    """

    MINUTES = 'minutes'
    SECONDS = 'seconds'
    HOURS = 'hours'


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


class TemperatureUnits(StrEnum):
    """Temperature units for VeSync devices.

    Attributes:
        CELSIUS: Temperature in Celsius.
        FAHRENHEIT: Temperature in Fahrenheit.
    """

    CELSIUS = 'c'
    FAHRENHEIT = 'f'

    @property
    def code(self) -> str:
        """Return the code for the temperature unit 'f' or 'c'."""
        return self.value

    @property
    def label(self) -> str:
        """Return the label for the temperature unit, 'celsius' or 'fahrenheit'.

        The CS137/CS158 air fryer sends this as ``tempUnit``.
        """
        return self.name.lower()

    @classmethod
    def from_string(cls, value: str) -> TemperatureUnits:
        """Convert string value to corresponding TemperatureUnit.

        Matches on the first letter, case-insensitive and ignoring surrounding
        whitespace, so the API's spellings ('c', 'celsius', 'f', 'fahrenheit')
        and misspellings of either unit are accepted.

        Args:
            value (str): The unit string, or a ``TemperatureUnits`` member.

        Returns:
            TemperatureUnits: The matching unit.

        Raises:
            ValueError: If the value is not a string starting with 'c' or 'f'.
        """
        first = value.strip().lower()[:1] if isinstance(value, str) else ''
        if first == 'c':
            return cls.CELSIUS
        if first == 'f':
            return cls.FAHRENHEIT
        exc_msg = f'Invalid temperature unit: {value} value'
        raise ValueError(exc_msg)

    @classmethod
    def to_celsius(cls, value: float, unit: TemperatureUnits) -> float:
        """Convert temperature to Celsius.

        Args:
            value (float): The temperature in ``unit``.
            unit (TemperatureUnits): The unit of ``value``.

        Returns:
            float: The temperature in Celsius; ``value`` unchanged if ``unit``
            is already Celsius.
        """
        if unit == cls.FAHRENHEIT:
            return (value - 32) * 5.0 / 9.0
        return value

    @classmethod
    def to_fahrenheit(cls, value: float, unit: TemperatureUnits) -> float:
        """Convert temperature to Fahrenheit.

        Args:
            value (float): The temperature in ``unit``.
            unit (TemperatureUnits): The unit of ``value``.

        Returns:
            float: The temperature in Fahrenheit; ``value`` unchanged if
            ``unit`` is already Fahrenheit.
        """
        if unit == cls.CELSIUS:
            return (value * 9.0 / 5.0) + 32
        return value


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
        RGB_NIGHTLIGHT: RGB nightlight with color control.
    """

    ONOFF = 'onoff'
    CHILD_LOCK = 'child_lock'
    NIGHTLIGHT = 'night_light'
    WATER_LEVEL = 'water_level'
    WARM_MIST = 'warm_mist'
    AUTO_STOP = 'auto_stop'
    NIGHTLIGHT_BRIGHTNESS = 'nightlight_brightness'
    DRYING_MODE = 'drying_mode'
    RGB_NIGHTLIGHT = 'rgb_nightlight'


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
        ENERGY_HISTORY: Energy history retrieval support.
        NIGHTLIGHT: Nightlight status.
    """

    ONOFF = 'onoff'
    ENERGY_MONITOR = 'energy_monitor'
    ENERGY_HISTORY = 'energy_history'
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
    SLEEP = 'sleep'
    TURBO = 'turbo'
    PET = 'pet'
    ECO = 'eco'
    UNKNOWN = 'unknown'


# Air Fryer Constants

AIRFRYER_PID_MAP = {
    'WiFi_SKA_AirFryer137_US': 'wnxwqs76gknqyzjn',
    'WiFi_SKA_AirFryer158_US': '2cl8hmafsthl65bd',
    'WiFi_AirFryer_CS158-AF_EU': '8t8op7pcvzlsbosm',
}
"""PID's for VeSync Air Fryers based on ConfigModule."""


BYPASSV2_SUB_DEVICE_PAYLOAD: MappingProxyType[str, int | str] = MappingProxyType(
    {'subDeviceNo': 0, 'subDeviceType': ''}
)
"""Payload keys the VeSync app sends on every kitchen bypassV2 request.

Source: ``ApiManagerKt.deviceGlobalParamProvider`` in the APK.
"""


AIRFRYER_PRESET_RECIPE_TYPE = 3
"""recipeType of every APK preset (KitchenPresetModel.recipeType)."""

CUSTOM_RECIPE_ID = 1
"""Recipe ID of the CS137/CS158 Manual Cooking preset."""
CUSTOM_RECIPE_TYPE = AIRFRYER_PRESET_RECIPE_TYPE
"""Recipe type of the CS137/CS158 Manual Cooking preset."""
CUSTOM_RECIPE_NAME = 'Manual Cooking'
"""Recipe name of the CS137/CS158 Manual Cooking preset."""
CUSTOM_COOK_MODE = 'custom'
"""API mode string of the CS137/CS158 Manual Cooking preset."""


@dataclass
class AirFryerPresetRecipe:
    """Recipe for ``VeSyncFryer.set_mode_from_recipe()``.

    Get a fryer's presets with ``get_mode_recipe()`` and change them with
    ``dataclasses.replace``. The recipe ID, name and type are sent as given.
    The cook mode must be one of the fryer's modes and the times must be
    valid, otherwise ``set_mode_from_recipe()`` returns False without a
    request.

    Attributes:
        recipe_id (int): Recipe ID.
        recipe_type (int): Recipe type.
        recipe_name (str): Recipe name.
        cook_mode (str): The API mode string (for example ``'AirFry'``) or an
            ``AirFryerCookModes`` key. The mode's API string is sent.
        target_temp (int): Target temperature in ``temp_unit``.
        temp_unit (str): Temperature unit ('f' or 'c', or any string
            ``TemperatureUnits.from_string()`` accepts).
        cook_time (int): Cooking time in seconds, at least 1 (60 on the
            CS137/CS158).
        preheat_time (int | None): Preheating time in seconds, if any. Adds a
            preheat phase only on fryers with the ``PREHEAT`` feature, where
            it must be 0 or at least one API time unit.
    """

    recipe_name: str
    cook_mode: str
    recipe_id: int
    recipe_type: int
    target_temp: int
    temp_unit: str
    cook_time: int
    preheat_time: int | None = None


@dataclass(frozen=True)
class AirFryerTempLimits:
    """Temperature limits of one cook mode in one unit (APK tempRangeC/F).

    Attributes:
        min_temp (int): Lowest temperature the mode accepts.
        max_temp (int): Highest temperature the mode accepts.
        step (int): Temperature step of the mode. A requested temperature
            is rounded to the nearest step, not rejected.
    """

    min_temp: int
    max_temp: int
    step: int


@dataclass(frozen=True)
class AirFryerTimeLimits:
    """Cook time limits of one cook mode, in seconds (APK time range and precision).

    Attributes:
        min_seconds (int): Shortest time the mode accepts.
        max_seconds (int): Longest time the mode accepts.
        step_seconds (int): Allowed increment from the minimum. A time off the
            step is rejected, not rounded.
    """

    min_seconds: int
    max_seconds: int
    step_seconds: int

    def accepts(self, seconds: float | str) -> bool:
        """Return whether a cook time is within the range and on a step.

        Args:
            seconds (float | str): Requested time. A whole number given as a
                float or string counts; a fraction or a boolean does not.

        Returns:
            bool: Whether the mode accepts the time.
        """
        if isinstance(seconds, bool):
            return False
        try:
            value = float(seconds)
        except (TypeError, ValueError):
            return False
        if not value.is_integer():
            return False
        whole = int(value)
        return (
            self.min_seconds <= whole <= self.max_seconds
            and (whole - self.min_seconds) % self.step_seconds == 0
        )


@dataclass(frozen=True)
class AirFryerModeConfig:
    """One APK preset: its request values, default time and temperatures.

    Attributes:
        api_mode (str): Mode string sent to and reported by the API.
        recipe_id (int): Preset recipe ID sent with the mode.
        recipe_name (str): Preset label sent as the recipe name.
        cook_time (int): Default cook time in seconds. Not a limit; see
            ``time_limits``.
        temp_c (AirFryerTempLimits): Celsius limits.
        temp_f (AirFryerTempLimits): Fahrenheit limits.
        default_temp_c (int): Default temperature in Celsius.
        default_temp_f (int): Default temperature in Fahrenheit.
        recipe_type (int): Preset recipe type, 3 for every APK preset.
        time_limits (AirFryerTimeLimits | None): Cook time limits. None applies
            only the general minimum, with no upper limit or step.
    """

    api_mode: str
    recipe_id: int
    recipe_name: str
    cook_time: int
    temp_c: AirFryerTempLimits
    temp_f: AirFryerTempLimits
    default_temp_c: int
    default_temp_f: int
    recipe_type: int = AIRFRYER_PRESET_RECIPE_TYPE
    time_limits: AirFryerTimeLimits | None = None

    def limits(self, temp_unit: TemperatureUnits) -> AirFryerTempLimits:
        """Return the limits in the given unit.

        Args:
            temp_unit (TemperatureUnits): The unit to return.

        Returns:
            AirFryerTempLimits: The Fahrenheit or Celsius limits.
        """
        if temp_unit == TemperatureUnits.FAHRENHEIT:
            return self.temp_f
        return self.temp_c

    def to_recipe(self, temp_unit: TemperatureUnits) -> AirFryerPresetRecipe:
        """Return the preset as a recipe at its default time and temperature.

        Args:
            temp_unit (TemperatureUnits): The unit of the recipe's
                temperature.

        Returns:
            AirFryerPresetRecipe: The recipe, with no preheat.
        """
        target_temp = (
            self.default_temp_f
            if temp_unit == TemperatureUnits.FAHRENHEIT
            else self.default_temp_c
        )
        return AirFryerPresetRecipe(
            cook_mode=self.api_mode,
            recipe_name=self.recipe_name,
            recipe_id=self.recipe_id,
            recipe_type=self.recipe_type,
            target_temp=target_temp,
            temp_unit=temp_unit.code,
            cook_time=self.cook_time,
            preheat_time=None,
        )


class AirFryerPresets:
    """Library preset recipes, used as each fryer's ``default_preset``.

    Their times and temperatures are library defaults, not a fryer's app
    defaults; use ``VeSyncFryer.get_mode_recipe()`` for those.

    Attributes:
        custom (AirFryerPresetRecipe): CS137/CS158 Manual Cooking, the
            ``default_preset`` of the CS137/CS158.
        air_fry (AirFryerPresetRecipe): Air Fry, the ``default_preset`` of the
            bypassV2 fryers.
        broil (AirFryerPresetRecipe): Broil (bypassV2 mode string).
        roast (AirFryerPresetRecipe): Roast (bypassV2 mode string).
        bake (AirFryerPresetRecipe): Bake (bypassV2 mode string).
    """

    custom: AirFryerPresetRecipe = AirFryerPresetRecipe(
        cook_mode=CUSTOM_COOK_MODE,
        recipe_name=CUSTOM_RECIPE_NAME,
        recipe_id=CUSTOM_RECIPE_ID,
        recipe_type=CUSTOM_RECIPE_TYPE,
        target_temp=350,
        temp_unit='f',
        cook_time=10 * 60,
    )
    air_fry: AirFryerPresetRecipe = AirFryerPresetRecipe(
        cook_mode='AirFry',
        recipe_name='Air Fry',
        recipe_id=14,
        recipe_type=AIRFRYER_PRESET_RECIPE_TYPE,
        target_temp=400,
        temp_unit='f',
        cook_time=10 * 60,
    )
    # The Broil temperature (450 F) matches the CAF-DC601S Broil preset (its
    # time does not) and is above the CAF-P583S maximum of 400 F;
    # set_mode_from_recipe rejects it on devices whose range it exceeds.
    broil: AirFryerPresetRecipe = AirFryerPresetRecipe(
        cook_mode='Broil',
        recipe_name='Broil',
        recipe_id=17,
        recipe_type=AIRFRYER_PRESET_RECIPE_TYPE,
        target_temp=450,
        temp_unit='f',
        cook_time=12 * 60,
    )
    roast: AirFryerPresetRecipe = AirFryerPresetRecipe(
        cook_mode='Roast',
        recipe_name='Roast',
        recipe_id=13,
        recipe_type=AIRFRYER_PRESET_RECIPE_TYPE,
        target_temp=380,
        temp_unit='f',
        cook_time=30 * 60,
    )
    bake: AirFryerPresetRecipe = AirFryerPresetRecipe(
        cook_mode='Bake',
        recipe_name='Bake',
        recipe_id=9,
        recipe_type=AIRFRYER_PRESET_RECIPE_TYPE,
        target_temp=340,
        temp_unit='f',
        cook_time=30 * 60,
    )


class AirFryerCookModes(StrEnum):
    """Cooking modes for VeSync Air Fryers.

    One member covers the same food on different fryers; the API mode string
    and label of each fryer are in its device map ``cook_modes``.

    Attributes:
        CUSTOM: Custom (manual) cooking mode.
        ROAST: Roast cooking mode.
        BAKE: Bake cooking mode.
        REHEAT: Reheat cooking mode.
        DEHYDRATE: Dehydrate cooking mode.
        FROZEN: Frozen food cooking mode.
        PROOF: Proof cooking mode.
        BROIL: Broil cooking mode.
        WARM: Warm cooking mode.
        AIRFRY: Air fry cooking mode.
        DRY: Dry cooking mode.
        GRILL: Grill cooking mode.
        PREHEAT: Preheat mode.
        STEAK: Steak preset.
        CHICKEN: Chicken (poultry) preset.
        SEAFOOD: Seafood (fish) preset.
        BACON: Bacon preset.
        VEGETABLES: Vegetables preset.
        ROOT_VEGETABLES: Root vegetables preset.
        DESSERTS: Desserts preset.
        SHRIMP: Shrimp preset.
        BREAD: Bread preset.
        FRENCH_FRIES: French fries preset.
    """

    CUSTOM = 'custom'
    ROAST = 'roast'
    BAKE = 'bake'
    REHEAT = 'reheat'
    DEHYDRATE = 'dehydrate'
    FROZEN = 'frozen'
    PROOF = 'proof'
    BROIL = 'broil'
    WARM = 'warm'
    AIRFRY = 'airfry'
    DRY = 'dry'
    GRILL = 'grill'
    PREHEAT = 'preheat'
    STEAK = 'steak'
    CHICKEN = 'chicken'
    SEAFOOD = 'seafood'
    BACON = 'bacon'
    VEGETABLES = 'vegetables'
    ROOT_VEGETABLES = 'root_vegetables'
    DESSERTS = 'desserts'
    SHRIMP = 'shrimp'
    BREAD = 'bread'
    FRENCH_FRIES = 'french_fries'


class AirFryerFeatures(Features):
    """VeSync Air Fryer features.

    Attributes:
        DUAL_BLAZE: Not used by the library.
        PREHEAT: The fryer accepts a preheat phase (``preheat_time``).
        DUAL_CHAMBER: Two chambers; adds ``CHAMBER_2`` and ``BOTH`` to
            ``supported_chambers``.
        RESUMABLE: ``stop()`` / ``resume()`` pause and resume a cook. Declared
            on the CS137/CS158 and the CAF-DC111S-AEU; ``VeSyncDualAirFryer``
            refuses both without it.
        WHOLE_CHAMBER: Single merged basket with the divider removed
            (workChamber 3); adds ``WHOLE`` to ``supported_chambers``.
        CHAMBER_MODES: ``set_chamber_modes()`` is available: separate recipes
            in Sync, or one recipe in both chambers in Match.
        COOK_CONFIG_SHAKE_TIME: ``startMultiCook`` cook configs include
            ``shakeTime``. Other dual-chamber fryers leave it out.
    """

    DUAL_BLAZE = 'dual_blaze'
    PREHEAT = 'preheat'
    DUAL_CHAMBER = 'dual_chamber'
    RESUMABLE = 'resumable'
    WHOLE_CHAMBER = 'whole_chamber'
    CHAMBER_MODES = 'chamber_modes'
    COOK_CONFIG_SHAKE_TIME = 'cook_config_shake_time'


class AirFryerCookStatus(StrEnum):
    """Cooking status for VeSync Air Fryers.

    Each fryer's device map ``status_map`` maps its API status strings to
    these members; not every fryer reports every status.

    Attributes:
        COOKING: Cooking. The CAF-P583S also reports keep-warm as cooking.
        COOK_STOP: Cook paused.
        COOK_END: Cook finished.
        PULL_OUT: Basket pulled out.
        COMPLETED: Not reported by any mapped fryer.
        HEATING: Preheating.
        UNKNOWN: Not reported by any mapped fryer.
        STANDBY: Idle.
        PREHEAT_END: Preheat finished, waiting for ``cook_from_preheat()``
            (CS137/CS158).
        PREHEAT_STOP: Preheat paused.
        READY: Cook programmed, waiting for the start button.
        APPOINTING: Delayed start scheduled; waiting to start (CS158
            ``appointing``).
        HOLD: Sync cook: this chamber waits so both chambers finish
            together (dual-chamber fryers, ``hold``). The remaining cook time
            is the wait, and the total time remaining includes the cook. Both
            count down only while the other chamber cooks.
    """

    COOKING = 'cooking'
    COOK_STOP = 'cookStop'
    COOK_END = 'cookEnd'
    PULL_OUT = 'pullOut'
    COMPLETED = 'completed'
    HEATING = 'heating'
    UNKNOWN = 'unknown'
    STANDBY = 'standby'
    PREHEAT_END = 'preheatEnd'
    PREHEAT_STOP = 'preheatStop'
    READY = 'ready'
    APPOINTING = 'appointing'
    HOLD = 'hold'


class AirFryer158Command(StrEnum):
    """CS137/CS158 ``cookStatus`` / ``preheatStatus`` command values.

    Sent in the ``cookMode`` and ``preheat`` commands (CS158 captures).

    Attributes:
        COOKING: Start or resume the cook (``cookStatus``).
        HEATING: Start or resume the preheat (``preheatStatus``).
        STOP: Pause the cook or preheat.
        END: End the cook or preheat.
    """

    COOKING = 'cooking'
    HEATING = 'heating'
    STOP = 'stop'
    END = 'end'


class AirFryerSyncType(IntEnum):
    """Dual fryer ``syncType`` values (APK ``SyncType``).

    Attributes:
        OFF: Chambers run independently (APK ``SYNC_OFF``).
        MATCH: App label "Match" (APK ``SYNC_COOK``).
        SYNC: App label "Sync": both chambers finish together (APK
            ``SYNC_FINISH``).
    """

    OFF = 0
    MATCH = 1
    SYNC = 2


class AirFryerChamber(IntEnum):
    """Air fryer chamber (basket) selection.

    Values match the API ``workChamber`` / ``chamber`` fields (APK
    ``WorkChamberType``).

    Attributes:
        CHAMBER_1: Left chamber on the TF101S/TF102S, upper on the DC111S;
            the only basket on single-chamber fryers.
        CHAMBER_2: Right chamber on the TF101S/TF102S, lower on the DC111S.
        WHOLE: Divider removed, one large basket (TwinFry models only).
        BOTH: Both chambers cooking in sync (``workChamber`` 4).
    """

    CHAMBER_1 = 1
    CHAMBER_2 = 2
    WHOLE = 3
    BOTH = 4


PREHEAT_STATUSES = [
    AirFryerCookStatus.PREHEAT_END,
    AirFryerCookStatus.PREHEAT_STOP,
    AirFryerCookStatus.HEATING,
]
"""Statuses counted as preheat mode (``FryerState.is_in_preheat_mode``).

``PULL_OUT`` also counts while preheat time remains.
"""

COOK_STATUSES = [
    AirFryerCookStatus.COOKING,
    AirFryerCookStatus.COOK_STOP,
    AirFryerCookStatus.COOK_END,
    AirFryerCookStatus.READY,
    AirFryerCookStatus.HOLD,
]
"""Statuses counted as cook mode (``FryerState.is_in_cook_mode``).

``PULL_OUT`` also counts when no preheat time remains.
"""

RESUMABLE_STATUSES = [
    AirFryerCookStatus.COOK_STOP,
    AirFryerCookStatus.PREHEAT_STOP,
]
"""Paused statuses (``FryerState.can_resume``)."""

RUNNING_STATUSES = [
    AirFryerCookStatus.COOKING,
    AirFryerCookStatus.HEATING,
    AirFryerCookStatus.HOLD,
]
"""Statuses whose remaining times count down; setting one stamps ``last_timestamp``.

A ``HOLD`` chamber's stamp is cleared by the dual fryer's ``update()`` while
the other chamber is not cooking, which stops its countdown.
"""


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

    @classmethod
    def from_int(cls, value: int) -> DryingModes | None:
        """Convert integer value to corresponding string.

        If value is 1, return ON and if 0, return OFF.
        If value is -999, return NOT_SUPPORTED.
        """
        if value == 0:
            return cls.DONE
        if value == 1:
            return cls.RUNNING
        if value == 2:  # noqa: PLR2004
            return cls.PAUSE
        return None

    def __int__(self) -> int:
        """Return integer representation of the enum."""
        match self:
            case DryingModes.DONE:
                return 0
            case DryingModes.RUNNING:
                return 1
            case DryingModes.PAUSE:
                return 2


DRYING_MODES: dict[str, int] = {
    DryingModes.DONE: 0,
    DryingModes.RUNNING: 1,
    DryingModes.PAUSE: 2,
}
