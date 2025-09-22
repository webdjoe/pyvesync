"""Base devices and state classes for VeSync devices.

This module contains the base classes for VeSync devices, as well as the state classes
for each device type. The base classes are used to create the device objects, while the
state classes are used to store the current state of the device.
"""

from .bulb_base import BulbState, VeSyncBulb
from .fan_base import FanState, VeSyncFanBase
from .fryer_base import FryerState, VeSyncFryer
from .humidifier_base import HumidifierState, VeSyncHumidifier
from .outlet_base import OutletState, VeSyncOutlet
from .purifier_base import PurifierState, VeSyncPurifier
from .switch_base import SwitchState, VeSyncSwitch
from .vesyncbasedevice import DeviceState, VeSyncBaseDevice, VeSyncBaseToggleDevice

__all__ = [
    'BulbState',
    'DeviceState',
    'FanState',
    'FryerState',
    'HumidifierState',
    'OutletState',
    'PurifierState',
    'SwitchState',
    'VeSyncBaseDevice',
    'VeSyncBaseToggleDevice',
    'VeSyncBulb',
    'VeSyncFanBase',
    'VeSyncFryer',
    'VeSyncHumidifier',
    'VeSyncOutlet',
    'VeSyncPurifier',
    'VeSyncSwitch',
]
