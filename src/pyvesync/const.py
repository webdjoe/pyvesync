"""pyvesync library constants."""
from random import randint

from enum import StrEnum, IntEnum, Enum
from types import MappingProxyType

DEFAULT_LANGUAGE = "en"
API_BASE_URL = "https://smartapi.vesync.com"
# If device is out of reach, the cloud api sends a timeout response after 7 seconds,
# using 8 here so there is time enough to catch that message
API_TIMEOUT = 8
USER_AGENT = (
    "VeSync/3.2.39 (com.etekcity.vesyncPlatform; build:5; iOS 15.5.0) Alamofire/5.2.1"
)
DEFAULT_TZ = "America/New_York"
DEFAULT_REGION = "US"
APP_VERSION = "2.8.6"
PHONE_BRAND = "SM N9005"
PHONE_OS = "Android"
# MOBILE_ID = "1234567890123456"
MOBILE_ID = str(randint(1000000000000000, 9999999999999999))  # noqa: S311
USER_TYPE = "1"
BYPASS_APP_V = "VeSync 3.0.51"
BYPASS_HEADER_UA = "okhttp/3.12.1"


class AirQualityLevel(Enum):
    """Representation of air quality levels as string and integers.

    Attributes:
        EXCELLENT: Air quality is excellent.
        GOOD: Air quality is good.
        MODERATE: Air quality is moderate.
        POOR: Air quality is poor.
        UNKNOWN: Air quality is unknown.

    Note:
        Alias for "very good" is "excellent".
        Alias for "bad" is "poor".

    Usage:
        >>> AirQualityLevels.EXCELLENT
        <AirQualityLevels.EXCELLENT: 1>
        >>> AirQualityLevels.from_string("excellent")
        1
        >>> AirQualityLevels.from_int(1)
        "excellent"
        >>> int(AirQualityLevels.EXCELLENT)
        1
        >>> str(AirQualityLevels.EXCELLENT)
        "excellent"
    """
    EXCELLENT = 1
    GOOD = 2
    MODERATE = 3
    POOR = 4
    UNKNOWN = -1

    _string_to_enum = MappingProxyType({
        "excellent": EXCELLENT,
        "very good": EXCELLENT,  # Alias
        "good": GOOD,
        "moderate": MODERATE,
        "poor": POOR,
        "bad": POOR,  # Alias
        "unknown": UNKNOWN
    })

    _enum_to_string = MappingProxyType({
        EXCELLENT: "excellent",
        GOOD: "good",
        MODERATE: "moderate",
        POOR: "poor"
    })

    def __int__(self) -> int:
        """Return integer representation of the enum."""
        return self.value

    def __str__(self) -> str:
        """Return string representation of the enum."""
        return AirQualityLevel._enum_to_string.value[self.value]

    @classmethod
    def from_string(cls, value: str | None) -> 'AirQualityLevel':
        """Convert string value to corresponding integer."""
        if isinstance(value, str) and value.lower() in cls._string_to_enum.value:
            return AirQualityLevel(cls._string_to_enum.value[value.lower()])
        return cls.UNKNOWN

    @classmethod
    def from_int(cls, value: int | None) -> 'AirQualityLevel':
        """Convert integer value to corresponding string."""
        if value in [itm.value for itm in cls]:
            return cls(value)
        return cls.UNKNOWN


class IntFlag(IntEnum):
    """Integer flag to indicate if a device is not supported."""
    NOT_SUPPORTED = -999

    def __str__(self) -> str:
        """Return string representation of IntFlag."""
        return str(self.name)


class StrFlag(StrEnum):
    """String flag to indicate if a device is not supported."""
    NOT_SUPPORTED = "not_supported"


class PurifierAutoPreference(StrEnum):
    """Preference Levels for Purifier Auto Mode."""
    DEFAULT = "default"
    EFFICIENT = "efficient"
    QUIET = "quiet"
    UNKNOWN = "unknown"


class FanSleepPreference(StrEnum):
    """Sleep mode for VeSync fans."""
    DEFAULT = "default"
    ADVANCED = "advanced"
    TURBO = "turbo"
    EFFICIENT = "efficient"
    QUIET = "quiet"
    UNKNOWN = "unknown"


class NightlightStatus(StrEnum):
    """Nightlight status for VeSync devices."""
    ON = "on"
    OFF = "off"
    AUTO = "auto"
    UNKNOWN = "unknown"

    def __bool__(self) -> bool:
        """Return True if nightlight is on or auto."""
        return self in [NightlightStatus.ON, NightlightStatus.AUTO]

    def __int__(self) -> int:
        """Return integer representation of the enum."""
        if self not in [NightlightStatus.ON, NightlightStatus.OFF]:
            raise ValueError("Only ON and OFF are valid values for int conversion")
        return int(self == NightlightStatus.ON)


class DeviceStatus(StrEnum):
    """VeSync device status enum."""
    ON = "on"
    OFF = "off"
    PAUSED = "paused"
    STANDBY = "standby"
    IDLE = "idle"
    RUNNING = "running"
    UNKNOWN = "unknown"

    def __bool__(self) -> bool:
        """Return True if device is on or running."""
        return self in [DeviceStatus.ON, DeviceStatus.RUNNING]

    def __int__(self) -> int:
        """Return integer representation of the enum."""
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
    def from_int(cls, value: int) -> str:
        """Convert integer value to corresponding string."""
        if value == 1:
            return cls.ON
        if value == 0:
            return cls.OFF
        if value == IntFlag.NOT_SUPPORTED:
            return StrFlag.NOT_SUPPORTED
        return cls.UNKNOWN

    @classmethod
    def from_bool(cls, value: bool) -> 'DeviceStatus':
        """Convert boolean value to corresponding string."""
        return cls.ON if value else cls.OFF


class ConnectionStatus(StrEnum):
    """VeSync device connection status enum."""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

    def __bool__(self) -> bool:
        """Return True if device is online."""
        return self == ConnectionStatus.ONLINE


class ProductTypes(StrEnum):
    """General device types enum."""
    OUTLET = "Outlet"
    BULB = "Bulb"
    SWITCH = "Switch"
    PURIFIER = "Purifier"
    FAN = "Fan"
    HUMIDIFIER = "Humidifier"
    AIR_FRYER = "Air Fryer"
    KITCHEN_THERMOMETER = "Kitchen Thermometer"


class NightlightModes(StrEnum):
    """Nightlight modes."""
    ON = "on"
    OFF = "off"
    DIM = "dim"
    AUTO = "auto"
    UNKNOWN = "unknown"

    def __bool__(self) -> bool:
        """Return True if nightlight is on or auto."""
        return self in [
            NightlightModes.ON, NightlightModes.AUTO, NightlightModes.DIM
            ]


class Features(StrEnum):
    """Base Class for Features Enum."""


# Color Modes
class ColorMode(StrEnum):
    """VeSync bulb color modes."""
    RGB = "rgb"
    HSV = "hsv"
    WHITE = "white"
    COLOR = "color"


# Device Features
class HumidifierFeatures(Features):
    """VeSync humidifier features."""
    ONOFF = "onoff"
    CHILD_LOCK = "child_lock"
    NIGHTLIGHT = "night_light"
    WATER_LEVEL = "water_level"
    WARM_MIST = "warm_mist"


class PurifierFeatures(Features):
    """VeSync air purifier features."""
    RESET_FILTER = "reset_filter"
    CHILD_LOCK = "child_lock"
    NIGHTLIGHT = "night_light"
    AIR_QUALITY = "air_quality"
    FAN_ROTATE = "fan_rotate"
    LIGHT_DETECT = "light_detect"


class PurifierStringLevels(Features):
    """String levels for Air Purifier fan speed."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BulbFeatures(Features):
    """VeSync bulb features."""
    ONOFF = "onoff"
    DIMMABLE = "dimmable"
    COLOR_TEMP = "color_temp"
    MULTICOLOR = "multicolor"


class OutletFeatures(Features):
    """VeSync outlet features."""
    ONOFF = "onoff"
    ENERGY_MONITOR = "energy_monitor"
    NIGHTLIGHT = "nightlight"


class SwitchFeatures(Features):
    """VeSync switch features."""
    ONOFF = "onoff"
    DIMMABLE = "dimmable"
    INDICATOR_LIGHT = "indicator_light"
    BACKLIGHT = "backlight"
    BACKLIGHT_RGB = "backlight_rgb"


# Modes

class PurifierModes(Features):
    """VeSync air purifier modes."""
    AUTO = "auto"
    MANUAL = "manual"
    SLEEP = "sleep"
    TURBO = "turbo"
    PET = "pet"
    UNKNOWN = "unknown"


class HumidifierModes(Features):
    """VeSync humidifier modes."""
    AUTO = "auto"
    MANUAL = "manual"
    HUMIDITY = "humidity"
    SLEEP = "sleep"
    TURBO = "turbo"
    PET = "pet"
    UNKNOWN = "unknown"
    AUTOPRO = "autopro"


class FanModes(StrEnum):
    """VeSync fan modes."""
    AUTO = "auto"
    NORMAL = "normal"
    MANUAL = "normal"
    SLEEP = "advancedSleep"
    TURBO = "turbo"
    PET = "pet"
    UNKNOWN = "unknown"
    ADVANCED_SLEEP = "advancedSleep"
