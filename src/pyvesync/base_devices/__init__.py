"""Base devices and state classes for VeSync devices.

This module contains the base classes for VeSync devices, as well as the state classes
for each device type. The base classes are used to create the device objects, while the
state classes are used to store the current state of the device.
"""

from .vesyncbasedevice import VeSyncBaseDevice, VeSyncBaseToggleDevice, DeviceState
from .bulb_base import VeSyncBulb, BulbState
from .switch_base import VeSyncSwitch, SwitchState
from .outlet_base import VeSyncOutlet, OutletState
from .fan_base import VeSyncFanBase, FanState
from .purifier_base import VeSyncPurifier, PurifierState
from .humidifier_base import VeSyncHumidifier, HumidifierState
from .fryer_base import VeSyncFryer, FryerState

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
