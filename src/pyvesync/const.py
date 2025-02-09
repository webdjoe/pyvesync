"""pyvesync library constants."""
from enum import Enum


# Error Codes
RATE_LIMIT_CODES = [-11103086, -11000086]
LOGIN_ERROR_CODES = [-11201022, -11202022]


class DeviceTypes(Enum):
    """General device types enum."""

    OUTLET = "outlet"
    BULB = "bulb"
    SWITCH = "switch"
    PURIFIER = "purifier"
    FAN = "fan"
    HUMIDIFIER = "humidifier"
    KITCHEN = "kitchen"
