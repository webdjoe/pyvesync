"""VeSync API for controling fans and purifiers."""

import json
import logging
import sys
from abc import abstractmethod
from typing import Any, Dict, List, Tuple, Union, Optional
from pyvesync.vesyncbasedevice import (
    VeSyncBaseDevice, STATUS_ON, STATUS_OFF, MODE_ADVANCED_SLEEP, MODE_AUTO,
    MODE_DIM, MODE_HUMIDITY, MODE_MANUAL, MODE_NORMAL, MODE_PET, MODE_SLEEP, MODE_TURBO,
)
from .helpers import Helpers, EConfig, Timer, EDeviceFamily, ERR_REQ_TIMEOUTS, build_model_dict

module_fan = sys.modules[__name__]

# --8<-- [start:humid_configs]
humid_configs: dict = {
    'Classic300S': {
        EConfig.CLASS: 'VeSyncHumid200300S',
        EConfig.MODELS: ['Classic300S', 'LUH-A601S-WUSB', 'LUH-A601S-AUSW'],
        EConfig.FEATURES: ['nightlight'],
        EConfig.MIST_MODES: [MODE_AUTO, MODE_SLEEP, MODE_MANUAL],
        EConfig.MIST_LEVELS: list(range(1, 10))
    },
    'Classic200S': {
        EConfig.CLASS: 'VeSyncHumid200S',
        EConfig.MODELS: ['Classic200S'],
        EConfig.FEATURES: [],
        EConfig.MIST_MODES: [MODE_AUTO, MODE_MANUAL],
        EConfig.MIST_LEVELS: list(range(1, 10))
    },
    'Dual200S': {
        EConfig.CLASS: 'VeSyncHumid200300S',
        EConfig.MODELS: ['Dual200S', 'LUH-D301S-WUSR', 'LUH-D301S-WJP',
                   'LUH-D301S-WEU'],
        EConfig.FEATURES: [],
        EConfig.MIST_MODES: [MODE_AUTO, MODE_MANUAL],
        EConfig.MIST_LEVELS: list(range(1, 3))
    },
    'LV600S': {
        EConfig.CLASS: 'VeSyncHumid200300S',
        EConfig.MODELS: ['LUH-A602S-WUSR', 'LUH-A602S-WUS', 'LUH-A602S-WEUR',
                   'LUH-A602S-WEU', 'LUH-A602S-WJP', 'LUH-A602S-WUSC'],
        EConfig.FEATURES: ['warm_mist', 'nightlight'],
        EConfig.MIST_MODES: [MODE_HUMIDITY, MODE_SLEEP, MODE_MANUAL],
        EConfig.MIST_LEVELS: list(range(1, 10)),
        EConfig.MIST_LEVELS_WARM: list(range(0, 4))
    },
    'OASISMISTEU': {
        EConfig.CLASS: 'VeSyncHumid200300S',
        EConfig.MODELS: ['LUH-O451S-WEU'],
        EConfig.FEATURES: ['warm_mist', 'nightlight'],
        EConfig.MIST_MODES: [MODE_AUTO, MODE_MANUAL],
        EConfig.MIST_LEVELS: list(range(1, 10)),
        EConfig.MIST_LEVELS_WARM: list(range(0, 4))
    },
    'OASISMIST': {
        EConfig.CLASS: 'VeSyncHumid200300S',
        EConfig.MODELS: ['LUH-O451S-WUS', 'LUH-O451S-WUSR', 'LUH-O601S-WUS',
                    'LUH-O601S-KUS'],
        EConfig.FEATURES: ['warm_mist'],
        EConfig.MIST_MODES: [MODE_AUTO, MODE_HUMIDITY, MODE_SLEEP, MODE_MANUAL],
        EConfig.MIST_LEVELS: list(range(1, 10)),
        EConfig.MIST_LEVELS_WARM: list(range(0, 4)),
    },
    'OASISMIST1000S': {
        EConfig.CLASS: 'VeSyncHumid1000S',
        EConfig.MODELS: ['LUH-M101S-WUS'],
        EConfig.FEATURES: [],
        EConfig.MIST_MODES: [MODE_AUTO, MODE_SLEEP, MODE_MANUAL],
        EConfig.MIST_LEVELS: list(range(1, 10))
    },
    'Superior6000S': {
        EConfig.CLASS: 'VeSyncSuperior6000S',
        EConfig.MODELS: ['LEH-S601S-WUS', 'LEH-S601S-WUSR'],
        EConfig.FEATURES: [],
        EConfig.MIST_MODES: [MODE_AUTO, MODE_HUMIDITY, MODE_SLEEP, MODE_MANUAL],
        EConfig.MIST_LEVELS: list(range(1, 10))
    }
}
# --8<-- [end:humid_configs]


# --8<-- [start:air_configs]
air_configs: dict = {
    'Core200S': {
        EConfig.CLASS: 'VeSyncAirBypass',
        EConfig.MODELS: ['Core200S', 'LAP-C201S-AUSR', 'LAP-C202S-WUSR'],
        EConfig.MODES: [MODE_SLEEP, STATUS_OFF, MODE_MANUAL],
        EConfig.FEATURES: ['reset_filter'],
        EConfig.LEVELS: list(range(1, 4))
    },
    'Core300S': {
        EConfig.CLASS: 'VeSyncAirBypass',
        EConfig.MODELS: ['Core300S', 'LAP-C301S-WJP', 'LAP-C302S-WUSB', 'LAP-C301S-WAAA'],
        EConfig.MODES: [MODE_SLEEP, STATUS_OFF, MODE_AUTO, MODE_MANUAL],
        EConfig.FEATURES: ['air_quality'],
        EConfig.LEVELS: list(range(1, 5))
    },
    'Core400S': {
        EConfig.CLASS: 'VeSyncAirBypass',
        EConfig.MODELS: ['Core400S', 'LAP-C401S-WJP', 'LAP-C401S-WUSR',
                   'LAP-C401S-WAAA'],
        EConfig.MODES: [MODE_SLEEP, STATUS_OFF, MODE_AUTO, MODE_MANUAL],
        EConfig.FEATURES: ['air_quality'],
        EConfig.LEVELS: list(range(1, 5))
    },
    'Core600S': {
        EConfig.CLASS: 'VeSyncAirBypass',
        EConfig.MODELS: ['Core600S', 'LAP-C601S-WUS', 'LAP-C601S-WUSR',
                   'LAP-C601S-WEU'],
        EConfig.MODES: [MODE_SLEEP, STATUS_OFF, MODE_AUTO, MODE_MANUAL],
        EConfig.FEATURES: ['air_quality'],
        EConfig.LEVELS: list(range(1, 5))
    },
    'LV-PUR131S': {
        EConfig.CLASS: 'VeSyncAir131',
        EConfig.MODELS: ['LV-PUR131S', 'LV-RH131S'],
        EConfig.MODES: [MODE_MANUAL, MODE_AUTO, MODE_SLEEP, STATUS_OFF],
        EConfig.FEATURES: ['air_quality'],
        EConfig.LEVELS: list(range(1, 3))
    },
    'Vital100S': {
        EConfig.CLASS: 'VeSyncAirBaseV2',
        EConfig.MODELS: ['LAP-V102S-AASR', 'LAP-V102S-WUS', 'LAP-V102S-WEU',
                   'LAP-V102S-AUSR', 'LAP-V102S-WJP'],
        EConfig.MODES: [MODE_MANUAL, MODE_AUTO, MODE_SLEEP, STATUS_OFF, MODE_PET],
        EConfig.FEATURES: ['air_quality'],
        EConfig.LEVELS: list(range(1, 5))
    },
    'Vital200S': {
        EConfig.CLASS: 'VeSyncAirBaseV2',
        EConfig.MODELS: ['LAP-V201S-AASR', 'LAP-V201S-WJP', 'LAP-V201S-WEU',
                   'LAP-V201S-WUS', 'LAP-V201-AUSR', 'LAP-V201S-AUSR',
                   'LAP-V201S-AEUR'],
        EConfig.MODES: [MODE_MANUAL, MODE_AUTO, MODE_SLEEP, STATUS_OFF, MODE_PET],
        EConfig.FEATURES: ['air_quality'],
        EConfig.LEVELS: list(range(1, 5))
    },
    'EverestAir': {
        EConfig.CLASS: 'VeSyncAirBaseV2',
        EConfig.MODELS: ['LAP-EL551S-AUS', 'LAP-EL551S-AEUR', 'LAP-EL551S-WEU',
                   'LAP-EL551S-WUS'],
        EConfig.MODES: [MODE_MANUAL, MODE_AUTO, MODE_SLEEP, STATUS_OFF, MODE_TURBO],
        EConfig.FEATURES: ['air_quality', 'fan_rotate'],
        EConfig.LEVELS: list(range(1, 4))
    },
    'SmartTowerFan': {
        EConfig.CLASS: 'VeSyncTowerFan',
        EConfig.MODELS: ['LTF-F422S-KEU', 'LTF-F422S-WUSR', 'LTF-F422_WJP', 'LTF-F422S-WUS'],
        EConfig.MODES: [MODE_NORMAL, MODE_AUTO, MODE_ADVANCED_SLEEP, MODE_TURBO, STATUS_OFF],
        EConfig.FEATURES: ['fan_speed'],
        EConfig.LEVELS: list(range(1, 13))
    }
}
# --8<-- [end:air_configs]


logger = logging.getLogger(__name__)

fan_configs           = {**air_configs, **humid_configs}
fan_classes           = build_model_dict(fan_configs, EConfig.CLASS)
fan_features          = build_model_dict(fan_configs, EConfig.FEATURES)
fan_modes             = build_model_dict(fan_configs, EConfig.MODES)
fan_levels            = build_model_dict(fan_configs, EConfig.LEVELS)
fan_mist_levels       = build_model_dict(fan_configs, EConfig.MIST_LEVELS)
fan_mist_modes        = build_model_dict(fan_configs, EConfig.MIST_MODES)
fan_mist_levels_warm  = build_model_dict(fan_configs, EConfig.MIST_LEVELS_WARM)

__all__: list = list(fan_classes.values()) + [
    'fan_classes', 'fan_configs', 'fan_features', 'fan_modes', 'fan_levels',
    'fan_levels', 'fan_mist_levels', 'fan_mist_modes', 'fan_mist_levels_warm', 'VeSyncFan'
]

class VeSyncFan(VeSyncBaseDevice):

    device_family = EDeviceFamily.FAN
    enabled: bool = False
    modes: list
    levels: list

    def __init__(self, details: Dict[str, list], manager):
        """Initialize VeSync Air Purifier Bypass Base Class."""
        super().__init__(details, manager, fan_features, EDeviceFamily.FAN)
        self.modes = fan_modes.get(self.device_type)
        self.levels = fan_levels.get(self.device_type)
        self.enabled = True

    def build_api_dict(self, method: str, config: list[str], data: dict = None) -> Dict:
        """Build humidifier api call header and body."""
        body = {
            **self.manager.req_body_bypass_v2(),
            'cid': self.cid,
        }
        for value in config:
            body[value] = self.config_module

        body['payload'] = {
            'method': method,
            'source': 'APP'
        }
        if not (data is None):
            body['payload']['data'] = data
        return body


class VeSyncAirBypass(VeSyncFan):
    """Initialize air purifier devices.

    Instantiated by VeSync manager object. Inherits from
    VeSyncBaseDevice class.

    Parameters:
        details (dict): Dictionary of device details
        manager (VeSync): Instantiated VeSync object used to make API calls

    Attributes:
        modes (list): List of available operation modes for device
        air_quality_feature (bool): True if device has air quality sensor
        details (dict): Dictionary of device details
        timer (Timer): Timer object for device, None if no timer exists. See
            [pyveysnc.helpers.Timer][`Timer`] class
        config (dict): Dictionary of device configuration

    Notes:
        The `details` attribute holds device information that is updated when
        the `update()` method is called. An example of the `details` attribute:
    ```python
    >>> json.dumps(self.details, indent=4)
        {
            'filter_life': 0,
            'mode': 'manual',
            'level': 0,
            'display': False,
            'child_lock': False,
            'night_light': 'off',
            'air_quality': 0 # air quality level
            'air_quality_value': 0, # PM2.5 value from device,
            'display_forever': False
        }
    ```
    """
    modes: list = []
    air_quality_feature: bool = False
    timer: Optional[Timer] = None
    config: Dict[str, Union[str, int, float, bool]] = {
            'display': False,
            'display_forever': False
        }

    def __init__(self, details: Dict[str, list], manager):
        """Initialize VeSync Air Purifier Bypass Base Class."""
        super().__init__(details, manager)
        self.air_quality_feature = self.supports('air_quality')
        self.details: Dict[str, Any] = {
            'filter_life': 0,
            'mode': MODE_MANUAL,
            'level': 0,
            'display': False,
            'child_lock': False,
            'night_light': STATUS_OFF,
        }
        self.timer: Optional[Timer] = None
        if self.air_quality_feature is True:
            self.details['air_quality'] = 0

    def build_api_dict(self, method: str, config=['configModule'], data = None) -> Tuple[Dict, Dict]:
        body = super().build_api_dict(method, config, data)
        return body

    def build_purifier_dict(self, dev_dict: dict) -> None:
        """Build Bypass purifier status dictionary.

        Populates `self.details` and instance variables with device details.

        Args:
            dev_dict (dict): Dictionary of device details from API

        Examples:
            >>> dev_dict = {
            ...     'enabled': True,
            ...     'filter_life': 0,
            ...     'mode': 'manual',
            ...     'level': 0,
            ...     'display': False,
            ...     'child_lock': False,
            ...     'night_light': 'off',
            ...     'display': False,
            ...     'display_forever': False,
            ...     'air_quality_value': 0,
            ...     'air_quality': 0
            ... }
            >>> build_purifier_dict(dev_dict)
            >>> print(self.details)
            {
                'filter_life': 0,
                'mode': 'manual',
                'level': 0,
                'display': False,
                'child_lock': False,
                'night_light': 'off',
                'display': False,
                'display_forever': False,
                'air_quality_value': 0,
                'air_quality': 0
            }
        """
        self.enabled = dev_dict.get('enabled', False)
        if self.enabled:
            self.device_status = STATUS_ON
        else:
            self.device_status = STATUS_OFF
        self.details['filter_life'] = dev_dict.get('filter_life', 0)
        self.mode = dev_dict.get('mode', MODE_MANUAL)
        self.speed = dev_dict.get('level', 0)
        self.details['display'] = dev_dict.get('display', False)
        self.details['child_lock'] = dev_dict.get('child_lock', False)
        self.details['night_light'] = dev_dict.get('night_light', STATUS_OFF)
        self.details['display'] = dev_dict.get('display', False)
        self.details['display_forever'] = dev_dict.get('display_forever',
                                                       False)
        if self.air_quality_feature is True:
            self.details['air_quality_value'] = dev_dict.get('air_quality_value', 0)
            self.details['air_quality'] = dev_dict.get('air_quality', 0)

    def build_config_dict(self, conf_dict: Dict[str, str]) -> None:
        """Build configuration dict for Bypass purifier.

        Used by the `update()` method to populate the `config` attribute.

        Args:
            conf_dict (dict): Dictionary of device configuration
        """
        self.config['display'] = conf_dict.get('display', False)
        self.config['display_forever'] = conf_dict.get('display_forever',
                                                       False)

    def get_details(self) -> None:
        """Build Bypass Purifier details dictionary."""
        body = self.build_api_dict('getPurifierStatus', data={})
        r = self.manager.post_device_managed_v2(body)
        if not isinstance(r, dict):
            logger.debug('Error in purifier response')
            return
        if not isinstance(r.get('result'), dict):
            logger.debug('Error in purifier response')
            return

        if Helpers.code_check(r):
            outer_result = r.get('result', {})
            if outer_result:
                inner_result = r.get('result', {}).get('result')
                if inner_result is not None:
                    if outer_result.get('code') == 0:
                        self.build_purifier_dict(inner_result)
                    else:
                        logger.debug('error in inner result dict from purifier')
                    if inner_result.get('configuration', {}):
                        self.build_config_dict(inner_result.get('configuration', {}))
                    else:
                        logger.debug('No configuration found in purifier status')
            else:
                logger.debug('Error in purifier response')

    def update(self):
        """Update Purifier details."""
        self.get_details()

    def get_timer(self) -> Optional[Timer]:
        """Retrieve running timer from purifier.

        Returns Timer object if timer is running, None if no timer is running.

        Args:
            None

        Returns:
            Timer | None : Timer object if timer is running, None if no timer is running

        Notes:
            Timer object tracks the time remaining based on the last update. Timer
            properties include `status`, `time_remaining`, `duration`, `action`,
            `paused` and `done`. The methods `start()`, `end()` and `pause()`
            are available but should be called through the purifier object
            to update through the API.

        See Also:
            [pyvesync.helpers.Time][`Timer`] : Timer object used to hold status of timer

        """
        body = self.build_api_dict('getTimer', data={})
        r = self.manager.post_device_managed_v2(body)
        if not isinstance(r, dict):
            logger.debug('Error in purifier response')
            return None
        if r.get('code') != 0:
            logger.debug('Error in purifier response, code %s', r.get('code', 'unknown'))
            return None
        if r.get('result', {}).get('code') != 0:
            logger.debug('Error in purifier result response, code %s',
                         r.get('result', {}).get('code', 'unknown'))
            return None
        timers = r.get('result', {}).get('result', {}).get('timers', [])
        if not isinstance(timers, list) or len(timers) < 1:
            self.timer = None
            logger.debug('No timer found')
            return None

        timer = timers[0]
        if self.timer is None:
            self.timer = Timer(
                timer_duration=timer.get("duration", timer.get("total", 0)),
                action=timer.get("action"),
                id=timer.get("id"),
                remaining=timer.get("remaining", timer.get("remain"))
            )
        else:
            self.timer.update(time_remaining=timer.get('remaining'))
        logger.debug('Timer found: %s', str(self.timer))
        return self.timer

    def set_timer(self, timer_duration: int) -> bool:
        """Set timer for Purifier.

        Args:
            timer_duration (int): Duration of timer in seconds

        Returns:
            bool : True if timer is set, False if not

        """
        if self.device_status != STATUS_ON:
            logger.debug("Can't set timer when device is off")
        data = {
            'total': timer_duration,
            'action': STATUS_OFF,
        }
        body = self.build_api_dict('addTimer', data=data)
        r = self.manager.post_device_managed_v2(body)

        if r.get('code') != 0:
            logger.debug('Error in purifier response, code %s', r.get('code', 'unknown'))
            return False
        if r.get('result', {}).get('code') != 0:
            logger.debug('Error in purifier result response, code %s',
                         r.get('result', {}).get('code', 'unknown'))
            return False
        timer_id = r.get('result', {}).get('result', {}).get('id')
        if timer_id is not None:
            self.timer = Timer(timer_duration=timer_duration,
                               action=STATUS_OFF,
                               id=timer_id)
        else:
            self.timer = Timer(timer_duration=timer_duration,
                               action=STATUS_OFF)
        return True

    def clear_timer(self) -> bool:
        """Clear timer.

        Returns True if no error is returned from API call.

        Returns:
            bool : True if timer is cleared, False if not
        """
        self.get_timer()
        if self.timer is None:
            logger.debug('No timer to clear')
            return False
        if self.timer.id is None:
            logger.debug("Timer doesn't have an ID, can't clear")

        body = self.build_api_dict('delTimer', data={'id': self.timer.id})
        r = self.manager.post_device_managed_v2(body)
        if r.get('code') != 0:
            logger.debug('Error in purifier response, code %s', r.get('code', 'unknown'))
            return False
        logger.debug("Timer cleared")
        return True

    def change_fan_speed(self, speed=None) -> bool:
        """Change fan speed based on levels in configuration dict.

        If no value is passed, the next speed in the list is selected.

        Args:
            speed (int, optional): Speed to set fan. Defaults to None.

        Returns:
            bool : True if speed is set, False if not
        """
        current_speed = self.speed

        if speed is not None:
            if speed not in self.levels:
                logger.debug("%s is invalid speed - valid speeds are %s",
                             speed, str(self.levels))
                return False
            new_speed = speed
        else:
            if current_speed == self.levels[-1]:
                new_speed = self.levels[0]
            else:
                current_index = self.levels.index(current_speed)
                new_speed = self.levels[current_index + 1]

        data = {
            'id': 0,
            'level': new_speed,
            'type': 'wind',
            'mode': MODE_MANUAL,
        }
        body = self.build_api_dict('setLevel', data=data)
        r = self.manager.post_device_managed_v2(body)

        if Helpers.code_check(r):
            self.speed = new_speed
            return True
        logger.debug('Error changing %s speed', self.device_name)
        return False

    def child_lock_on(self) -> bool:
        """Turn Bypass child lock on."""
        return self.set_child_lock(True)

    def child_lock_off(self) -> bool:
        """Turn Bypass child lock off.

        Returns:
            bool : True if child lock is turned off, False if not
        """
        return self.set_child_lock(False)

    def set_child_lock(self, mode: bool) -> bool:
        """Set Bypass child lock.

        Set child lock to on or off. Internal method used by `child_lock_on` and
        `child_lock_off`.

        Args:
            mode (bool): True to turn child lock on, False to turn off

        Returns:
            bool : True if child lock is set, False if not

        """
        if mode not in (True, False):
            logger.debug('Invalid mode passed to set_child_lock - %s', mode)
            return False

        body = self.build_api_dict('setChildLock', data={'child_lock': mode})
        r = self.manager.post_device_managed_v2(body)

        if Helpers.code_check(r):
            self.details['child_lock'] = mode
            return True
        if isinstance(r, dict):
            logger.debug('Error toggling child lock')
        else:
            logger.debug('Error in api return json for %s', self.device_name)
        return False

    def reset_filter(self) -> bool:
        """Reset filter to 100%.

        Returns:
            bool : True if filter is reset, False if not
        """
        if self.supports('reset_filter'):
            logger.debug("Filter reset not implemented for %s", self.device_type)
            return False

        body = self.build_api_dict('resetFilter', data={})
        r = self.manager.post_device_managed_v2(body)

        if Helpers.code_check(r):
            return True
        logger.debug('Error resetting filter')
        return False

    def mode_turn(self, mode: str) -> bool:
        """Set purifier mode - sleep or manual.

        Set purifier mode based on devices available modes.

        Args:
            mode (str): Mode to set purifier. Based on device modes in attribute `modes`

        Returns:
            bool : True if mode is set, False if not

        """
        if mode.lower() not in self.modes:
            logger.debug('Invalid purifier mode used - %s',
                         mode)
            return False
        if mode == MODE_MANUAL:
            data = {
                'id': 0,
                'level': 1,
                'type': 'wind'
            }
            body = self.build_api_dict('setLevel', data=data)
            body['payload']['type'] = 'APP'
            del body['payload']['source']
        else:
            data = {
                'mode': mode.lower()
            }
            body = self.build_api_dict('setPurifierMode', data=data)
        r = self.manager.post_device_managed_v2(body)

        if Helpers.code_check(r):
            if mode.lower() == MODE_MANUAL:
                self.speed = 1
                self.mode = MODE_MANUAL
            else:
                self.mode = mode
                self.speed = 0
            return True
        logger.debug('Error setting purifier mode')
        return False

    def manual_mode(self) -> bool:
        """Set mode to manual.

        Calls method [pyvesync.VeSyncAirBypass.mode_turn][`self.mode_turn('manual')`]
        to set mode to manual.

        Returns:
            bool : True if mode is set, False if not
        """
        if MODE_MANUAL not in self.modes:
            logger.debug('%s does not have manual mode', self.device_name)
            return False
        return self.mode_turn(MODE_MANUAL)

    def sleep_mode(self) -> bool:
        """Set sleep mode to on.

        Calls method [pyvesync.VeSyncAirBypass.mode_turn][`self.mode_turn('sleep')`]

        Returns:
            bool : True if mode is set, False if not
        """
        if MODE_SLEEP not in self.modes:
            logger.debug('%s does not have sleep mode', self.device_name)
            return False
        return self.mode_turn(MODE_SLEEP)

    def auto_mode(self) -> bool:
        """Set mode to auto.

        Calls method [pyvesync.VeSyncAirBypass.mode_turn][`self.mode_turn('sleep')`]

        Returns:
            bool : True if mode is set, False if not
        """
        if MODE_AUTO not in self.modes:
            logger.debug('%s does not have auto mode', self.device_name)
            return False
        return self.mode_turn(MODE_AUTO)

    def turn(self, status: str) -> bool:
        """Turn purifier on/off.

        Helper method for `turn_on()` and `turn_off()` methods.

        Args:
            status (str): 'on' to turn on, 'off' to turn off

        Returns:
            bool : True if purifier is turnd, False if not
        """
        if status in (STATUS_OFF, STATUS_ON):
            turn = (status == STATUS_ON)
        else:
            logger.debug('Invalid turn value %s for %s switch', status, self.device_name)
            return False

        body = self.build_api_dict('setSwitch', data={'enabled': turn, 'id': 0})
        r = self.manager.post_device_managed_v2(body)

        if Helpers.code_check(r):
            self.device_status = status
            return True
        logger.debug("Error toggling purifier - %s",
                     self.device_name)
        return False

    def set_display(self, mode: bool) -> bool:
        """Turn display on/off.

        Called by `turn_on_display()` and `turn_off_display()` methods.

        Args:
            mode (bool): True to turn display on, False to turn off

        Returns:
            bool : True if display is turnd, False if not
        """
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        body = self.build_api_dict('setDisplay', data={'state': mode})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug("Error toggling purifier display - %s",
                     self.device_name)
        return False

    def turn_on_display(self) -> bool:
        """Turn Display on.

        Calls method [pyvesync.VeSyncAirBypass.set_display][`self.set_display(True)`]

        Returns:
            bool : True if display is turned on, False if not
        """
        return self.set_display(True)

    def turn_off_display(self):
        """Turn Display off.

        Calls method [pyvesync.VeSyncAirBypass.set_display][`self.set_display(False)`]

        Returns:
            bool : True if display is turned off, False if not
        """
        return self.set_display(False)

    def set_night_light(self, mode: str) -> bool:
        """Set night light.

        Possible modes are on, off or dim.

        Args:
            mode (str): Mode to set night light

        Returns:
            bool : True if night light is set, False if not
        """
        if mode.lower() not in [STATUS_ON, STATUS_OFF, MODE_DIM]:
            logger.debug('Invalid nightlight mode used (on, off or dim)- %s',
                         mode)
            return False
        body = self.build_api_dict('setNightLight', data={'night_light': mode.lower()})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            self.details['night_light'] = mode.lower()
            return True
        logger.debug('Error setting nightlight mode')
        return False

    @property
    def air_quality(self):
        """Get air quality value (ug/m3)."""
        if self.air_quality_feature is not True:
            logger.debug("%s does not have air quality sensor",
                         self.device_type)
        try:
            return int(self.details['air_quality'])
        except KeyError:
            return 0

    @property
    def fan_level(self):
        """Get current fan level."""
        try:
            speed = int(self.speed)
        except ValueError:
            speed = self.speed
        return speed

    @property
    def filter_life(self) -> int:
        """Get percentage of filter life remaining."""
        try:
            return int(self.details['filter_life'])
        except KeyError:
            return 0

    @property
    def display_state(self) -> bool:
        """Get display state.

        See [pyvesync.VeSyncAirBypass.display_status][`self.display_status`]
        """
        return bool(self.details['display'])

    @property
    def screen_status(self) -> bool:
        """Get display status.

        Returns:
            bool : True if display is on, False if off
        """
        return bool(self.details['display'])

    @property
    def child_lock(self) -> bool:
        """Get child lock state.

        Returns:
            bool : True if child lock is enabled, False if not.
        """
        return bool(self.details['child_lock'])

    @property
    def night_light(self) -> str:
        """Get night light state.

        Returns:
            str : Night light state (on, dim, off)
        """
        return str(self.details['night_light'])

    def display(self) -> None:
        """Print formatted device info to stdout.

        Builds on the `display()` method from the `VeSyncBaseDevice` class.

        See Also:
            [pyvesync.VeSyncBaseDevice.display][`VeSyncBaseDevice.display`]
        """
        super().display()
        disp = [
            ('Mode', self.mode, ''),
            ('Filter Life', self.details['filter_life'], '%'),
            ('Fan Level', self.speed, ''),
            ('Display', self.details['display'], ''),
            ('Child Lock', self.details['child_lock'], ''),
            ('Night Light', self.details['night_light'], ''),
            ('Display Config', self.config['display'], ''),
            ('Display_Forever Config', self.config['display_forever'], '')
        ]
        if self.air_quality_feature:
            disp.extend([
                ('Air Quality Level', self.details.get('air_quality', ''), ''),
                ('Air Quality Value', self.details.get('air_quality_value', ''), 'ug/m3')
            ])
        for line in disp:
            print(f"{line[0]+': ':.<30} {' '.join(line[1:])}")

    def displayJSON(self) -> str:  # noqa: N802
        """Return air purifier status and properties in JSON output.

        Returns:
            str : JSON formatted string of air purifier details
        """
        sup = super().displayJSON()
        sup_val = json.loads(sup)
        sup_val.update(
            {
                'Mode': self.mode,
                'Filter Life': str(self.details['filter_life']),
                'Fan Level': str(self.speed),
                'Display': self.details['display'],
                'Child Lock': self.details['child_lock'],
                'Night Light': str(self.details['night_light']),
                'Display Config': self.config['display'],
                'Display_Forever Config': self.config['display_forever'],
            }
        )
        if self.air_quality_feature is True:
            sup_val.update(
                {'Air Quality Level': str(self.details.get('air_quality', ''))}
            )
            sup_val.update(
                {'Air Quality Value': str(self.details.get('air_quality_value', ''))}
            )
        return json.dumps(sup_val, indent=4)


class VeSyncAirBaseV2(VeSyncAirBypass):
    """Levoit V2 Air Purifier Class.

    Inherits from VeSyncAirBypass and VeSyncBaseDevice class.

    Args:
        details (dict): Dictionary of device details
        manager (VeSync): Instantiated VeSync object

    Attributes:
        set_speed_level (int): Set speed level for device
        auto_prefences (list): List of auto preferences for device
        modes (list): List of available operation modes for device
        air_quality_feature (bool): True if device has air quality sensor
        details (dict): Dictionary of device details
        timer (Timer): Timer object for device, None if no timer exists. See
            [pyveysnc.helpers.Timer][`Timer`] class
        config (dict): Dictionary of device configuration

    """

    set_speed_level: Optional[int] = None
    auto_prefences: List[str] = ['default', 'efficient', 'quiet']

    def __init__(self, details: Dict[str, list], manager):
        """Initialize the VeSync Base API V2 Air Purifier Class."""
        super().__init__(details, manager)

    def build_api_dict(self, method: str, config=['configModule', 'configModel'], data=None) -> dict:
        """Return default body for Bypass V2 API."""
        body = super().build_api_dict(method, config, data)
        body['deviceId'] = self.cid
        return body

    @property
    def light_detection(self) -> bool:
        """Return true if light detection feature is enabled."""
        return self.details['light_detection_switch']

    @light_detection.setter
    def light_detection(self, turn: bool) -> None:
        """Set light detection feature."""
        self.details['light_detection_switch'] = turn

    @property
    def light_detection_state(self) -> bool:
        """Return true if light is detected."""
        return self.details['environment_light_state']

    def get_details(self) -> None:
        """Build API V2 Purifier details dictionary."""
        body = self.build_api_dict('getPurifierStatus', data={})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.nested_code_check(r) is False or not isinstance(r, dict):
            logger.debug('Error getting purifier details')
            self.connection_status = 'offline'
            return

        inner_result = r.get('result', {}).get('result')

        if inner_result is not None:
            self.build_purifier_dict(inner_result)
        else:
            self.connection_status = 'offline'
            logger.debug('error in inner result dict from purifier')
        if inner_result.get('configuration', {}):
            self.build_config_dict(inner_result.get('configuration', {}))

    def build_purifier_dict(self, dev_dict: dict) -> None:
        """Build Bypass purifier status dictionary."""
        self.connection_status = 'online'
        power_switch = bool(dev_dict.get('powerSwitch', 0))
        self.enabled = power_switch
        self.device_status = STATUS_ON if power_switch is True else STATUS_OFF
        self.mode = dev_dict.get('workMode', MODE_MANUAL)

        self.speed = dev_dict.get('fanSpeedLevel', 0)

        self.set_speed_level = dev_dict.get('manualSpeedLevel', 1)

        self.details['filter_life'] = dev_dict.get('filterLifePercent', 0)
        self.details['child_lock'] = bool(dev_dict.get('childLockSwitch', 0))
        self.details['display'] = bool(dev_dict.get('screenState', 0))
        self.details['light_detection_switch'] = bool(
            dev_dict.get('lightDetectionSwitch', 0))
        self.details['environment_light_state'] = bool(
            dev_dict.get('environmentLightState', 0))
        self.details['screen_switch'] = bool(dev_dict.get('screenSwitch', 0))

        if self.air_quality_feature is True:
            self.details['air_quality_value'] = dev_dict.get('PM25', 0)
            self.details['air_quality'] = dev_dict.get('AQLevel', 0)
        if 'PM1' in dev_dict:
            self.details['pm1'] = dev_dict['PM1']
        if 'PM10' in dev_dict:
            self.details['pm10'] = dev_dict['PM10']
        if 'AQPercent' in dev_dict:
            self.details['aq_percent'] = dev_dict['AQPercent']
        if 'fanRotateAngle' in dev_dict:
            self.details['fan_rotate_angle'] = dev_dict['fanRotateAngle']
        if 'filterOpenState' in dev_dict:
            self.details['filter_open_state'] = bool(dev_dict['filterOpenState'])
        if dev_dict.get('timerRemain', 0) > 0:
            self.timer = Timer(dev_dict['timerRemain'], STATUS_OFF)
        if isinstance(dev_dict.get('autoPreference'), dict):
            self.details['auto_preference_type'] = dev_dict.get(
                'autoPreference', {}).get('autoPreferenceType', 'default')
        else:
            self.details['auto_preference_type'] = None

    def turbo_mode(self) -> bool:
        """Turn on Turbo mode for compatible devices."""
        if MODE_TURBO in self.modes:
            return self.mode_turn(MODE_TURBO)
        logger.debug("Turbo mode not available for %s", self.device_name)
        return False

    def pet_mode(self) -> bool:
        """Set Pet Mode for compatible devices."""
        if MODE_PET in self.modes:
            return self.mode_turn(MODE_PET)
        logger.debug("Pet mode not available for %s", self.device_name)
        return False

    def set_night_light(self, mode: str) -> bool:
        """TODO: Set night light."""
        logger.debug("Night light feature not configured")
        return False

    def set_light_detection(self, turn: bool) -> bool:
        """Enable/Disable Light Detection Feature."""
        turn_id = int(turn)
        if self.details['light_detection_switch'] == turn_id:
            logger.debug("Light Detection is already set to %s", turn_id)
            return True

        body = self.build_api_dict('setLightDetection', data={'lightDetectionSwitch': turn_id})
        r = self.manager.post_device_managed_v2(body)
        if r is not None and Helpers.nested_code_check(r):
            self.details['light_detection'] = turn
            return True
        logger.debug("Error toggling purifier - %s",
                     self.device_name)
        return False

    def set_light_detection_on(self) -> bool:
        """Turn on light detection feature."""
        return self.set_light_detection(True)

    def set_light_detection_off(self) -> bool:
        """Turn off light detection feature."""
        return self.set_light_detection(False)

    def turn(self, status: str) -> bool:
        """Turn purifier on/off."""
        if not status in(STATUS_ON, STATUS_OFF):
            logger.debug('Invalid turn value for purifier switch')
            return False
        power = int(status == STATUS_ON)

        data = {
                'powerSwitch': power,
                'switchIdx': 0
            }
        body = self.build_api_dict('setSwitch', data=data)
        body['deviceId'] = self.cid
        r = self.manager.post_device_managed_v2(body)
        if r is not None and Helpers.nested_code_check(r):
            self.device_status = status
            return True
        logger.debug("Error toggling purifier - %s",
                     self.device_name)
        return False

    def set_child_lock(self, mode: bool) -> bool:
        """Levoit 100S/200S set Child Lock.

        Parameters:
            mode (bool): True to turn child lock on, False to turn off

        Returns:
            bool : True if successful, False if not
        """
        turn_id = int(mode)

        body = self.build_api_dict('setChildLock', data={'childLockSwitch': turn_id})
        r = self.manager.post_device_managed_v2(body)
        if r is not None and Helpers.nested_code_check(r):
            self.details['child_lock'] = mode
            return True

        logger.debug("Error toggling purifier child lock - %s", self.device_name)
        return False

    def set_display(self, mode: bool) -> bool:
        """Levoit Vital 100S/200S Set Display on/off with True/False."""
        mode_id = int(mode)

        body = self.build_api_dict('setDisplay', data={'screenSwitch': mode_id})
        r = self.manager.post_device_managed_v2(body)
        if r is not None and Helpers.nested_code_check(r):
            self.details['screen_switch'] = mode
            return True
        logger.debug("Error toggling purifier display - %s", self.device_name)
        return False

    def set_timer(self, timer_duration: int, action: str = STATUS_OFF,
                  method: str = 'powerSwitch') -> bool:
        """Set timer for Levoit 100S.

        Parameters:
            timer_duration (int):
                Timer duration in seconds.
            action (str | None):
                Action to perform, on or off, by default STATUS_OFF
            method (str | None):
                Method to use, by default 'powerSwitch' - TODO: Implement other methods

        Returns:
            bool : True if successful, False if not
        """
        if action not in [STATUS_ON, STATUS_OFF]:
            logger.debug('Invalid action for timer')
            return False
        if method not in ['powerSwitch']:
            logger.debug('Invalid method for timer')
            return False
        action_id = 1 if action == STATUS_ON else 0

        data = {
            "startAct": [{
                "type": method,
                "num": 0,
                "act": action_id,
            }],
            "total": timer_duration,
            "subDeviceNo": 0
        }
        body = self.build_api_dict('addTimerV2', data=data)
        body['payload']['subDeviceNo'] = 0

        r = self.manager.post_device_managed_v2(body)

        if r is not None and Helpers.nested_code_check(r):
            self.timer = Timer(timer_duration, action)
            return True

        logger.debug("Error setting timer for - %s", self.device_name)
        return False

    def clear_timer(self) -> bool:
        """Clear running timer."""
        body = self.build_api_dict('delTimerV2', data={'id': 1, "subDeviceNo": 0})
        body['payload']['subDeviceNo'] = 0
        r = self.manager.post_device_managed_v2(body)
        if r is not None and Helpers.nested_code_check(r):
            self.timer = None
            return True

        logger.debug("Error setting timer for - %s", self.device_name)
        return False

    def set_auto_preference(self, preference: str = 'default',
                            room_size: int = 600) -> bool:
        """Set Levoit Vital 100S/200S auto mode.

        Parameters:
            preference (str | None):
                Preference for auto mode, default 'default' (default, efficient, quiet)
            room_size (int | None):
                Room size in square feet, by default 600
        """
        if preference not in self.auto_prefences:
            logger.debug("%s is invalid preference -"
                         " valid preferences are default, efficient, quiet",
                         preference)
            return False

        data = {
            'autoPreference': preference,
            'roomSize': room_size,
        }
        body = self.build_api_dict('setAutoPreference', data=data)
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            self.details['auto_preference'] = preference
            return True

        logger.debug("Error setting auto preference for - %s", self.device_name)
        return False

    def change_fan_speed(self, speed=None) -> bool:
        """Change fan speed based on levels in configuration dict.

        The levels are defined in the configuration dict for the device. If no level is
        passed, the next valid level will be used. If the current level is the last level.

        Parameters:
            speed (int | None): Speed to set based on levels in configuration dict
        """
        current_speed = self.set_speed_level or 0

        if speed is not None:
            if speed not in self.levels:
                logger.debug("%s is invalid speed - valid speeds are %s",
                             speed, str(self.levels))
                return False
            new_speed = speed
        else:
            if current_speed in [self.levels[-1], 0]:
                new_speed = self.levels[0]
            else:
                current_index = self.levels.index(current_speed)
                new_speed = self.levels[current_index + 1]

        data= {
            'levelIdx': 0,
            'manualSpeedLevel': new_speed,
            'levelType': 'wind'
        }
        body = self.build_api_dict('setLevel', data=data)
        body['deviceId'] = self.cid
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            self.set_speed_level = new_speed
            self.mode = MODE_MANUAL
            return True
        logger.debug('Error changing %s speed', self.device_name)
        return False

    def mode_turn(self, mode: str) -> bool:
        """Set Levoit 100S purifier mode.

        Parameters:
            mode (str): Mode to set purifier to, options are: auto, manual, sleep

        Returns:
            bool : True if successful, False if not
        """
        if mode.lower() not in self.modes:
            logger.debug('Invalid purifier mode used - %s',
                         mode)
            return False

        # Call change_fan_speed if mode is set to manual
        if mode == MODE_MANUAL:
            if self.speed is None or self.speed == 0:
                return self.change_fan_speed(1)
            return self.change_fan_speed(self.speed)

        if mode == STATUS_OFF:
            return self.turn_off()

        body = self.build_api_dict('setPurifierMode', data={'workMode': mode})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            self.mode = mode
            return True
        logger.debug('Error setting purifier mode')
        return False

    def displayJSON(self) -> str:
        """Return air purifier status and properties in JSON output.

        Returns:
            str : JSON formatted string of air purifier details
        """
        sup = super().displayJSON()
        sup_val = json.loads(sup)
        sup_val.update(
            {
                'Mode': self.mode,
                'Filter Life': str(self.details['filter_life']),
                'Fan Level': str(self.speed),
                'Display On': self.details['display'],
                'Child Lock': self.details['child_lock'],
                'Night Light': str(self.details['night_light']),
                'Display Set On': self.details['screen_switch'],
                'Light Detection Enabled': self.details['light_detection_switch'],
                'Environment Light State': self.details['environment_light_state']
            }
        )
        if self.air_quality_feature is True:
            sup_val.update(
                {'Air Quality Level': str(self.details.get('air_quality', ''))}
            )
            sup_val.update(
                {'Air Quality Value': str(self.details.get('air_quality_value', ''))}
            )
        everest_keys = {
            'pm1': 'PM1',
            'pm10': 'PM10',
            'fan_rotate_angle': 'Fan Rotate Angle',
            'filter_open_state': 'Filter Open State'
        }
        for key, value in everest_keys.items():
            if key in self.details:
                sup_val.update({value: str(self.details[key])})
        return json.dumps(sup_val, indent=4)


class VeSyncTowerFan(VeSyncAirBaseV2):
    """Levoit Tower Fan Device Class."""

    def __init__(self, details: Dict[str, list], manager):
        """Initialize the VeSync Base API V2 Fan Class."""
        super().__init__(details, manager)

    def build_api_dict(self, method, config=['configModel', 'configModule'], data=None):
        body = super().build_api_dict(method, config, data)
        return body

    def get_details(self) -> None:
        """Build API V2 Fan details dictionary."""
        body = self.build_api_dict('getTowerFanStatus', data={})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.nested_code_check(r) is False or not isinstance(r, dict):
            logger.debug('Error getting purifier details')
            self.connection_status = 'offline'
            return

        inner_result = r.get('result', {}).get('result')

        if inner_result is not None:
            self.build_purifier_dict(inner_result)
        else:
            self.connection_status = 'offline'
            logger.debug('error in inner result dict from purifier')
        if inner_result.get('configuration', {}):
            self.build_config_dict(inner_result.get('configuration', {}))

    def mode_turn(self, mode: str) -> bool:
        """Set Levoit Tower Fan purifier mode.

        Parameters:
            mode : str
                Mode to set purifier to, set by `config_dict`

        Returns:
            bool : True if successful, False if not
        """
        if mode.lower() not in [x.lower() for x in self.modes]:
            logger.debug('Invalid purifier mode used - %s',
                         mode)
            return False

        if mode == STATUS_OFF:
            return self.turn_off()

        body = self.build_api_dict('setTowerFanMode', data={'workMode': mode})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            self.mode = mode
            return True
        logger.debug('Error setting purifier mode')
        return False

    def normal_mode(self):
        """Set mode to normal."""
        return self.mode_turn(MODE_NORMAL)

    def manual_mode(self):
        """Adapter to set mode to normal."""
        return self.normal_mode()

    def advanced_sleep_mode(self) -> bool:
        """Set advanced sleep mode."""
        return self.mode_turn(MODE_ADVANCED_SLEEP)

    def sleep_mode(self) -> bool:
        """Adapter to set advanced sleep mode."""
        return self.advanced_sleep_mode()


class VeSyncAir131(VeSyncFan):
    """Levoit Air Purifier Class."""

    def __init__(self, details, manager):
        """Initilize air purifier class."""
        super().__init__(details, manager)
        self.enabled = True
        self.air_quality_feature = self.supports('air_quality')

    def call_api(self, api, method, body):
        r = Helpers.call_api(f'/131airPurifier/v1/device/{api}',
            method=method,
            headers=self.manager.req_headers(),
            json_object=body,
        )
        return r

    def get_details(self) -> None:
        """Build Air Purifier details dictionary."""
        body = self.manager.req_body_device_detail()
        body['uuid'] = self.uuid

        r = self.call_api('deviceDetail', 'post', body)

        if Helpers.code_check(r):
            self.device_status = r.get('deviceStatus', 'unknown')
            self.connection_status = r.get('connectionStatus', 'unknown')
            self.details['active_time'] = r.get('activeTime', 0)
            self.details['filter_life'] = r.get('filterLife', {})
            self.details['screen_status'] = r.get('screenStatus', 'unknown')
            self.mode = r.get('mode', self.mode)
            self.details['level'] = r.get('level', 0)
            self.details['air_quality'] = r.get('airQuality', 'unknown')
        else:
            logger.debug('Error getting %s details', self.device_name)

    def get_config(self) -> None:
        """Get configuration info for air purifier."""
        body = self.manager.req_body_device_detail()
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r = self.call_api('configurations', 'post', body)

        if Helpers.code_check(r):
            self.config = Helpers.build_config_dict(r)
        else:
            logger.debug('Unable to get config info for %s',
                         self.device_name)

    @property
    def active_time(self) -> int:
        """Return total time active in minutes."""
        return self.details.get('active_time', 0)

    @property
    def fan_level(self) -> int:
        """Get current fan level (1-3)."""
        return self.details.get('level', 0)

    @property
    def filter_life(self) -> int:
        """Get percentage of filter life remaining."""
        try:
            return self.details['filter_life'].get('percent', 0)
        except KeyError:
            return 0

    @property
    def air_quality(self) -> str:
        """Get Air Quality."""
        return self.details.get('air_quality', 'unknown')

    @property
    def screen_status(self) -> str:
        """Return Screen status (on/off)."""
        return self.details.get('screen_status', 'unknown')

    def turn_on_display(self) -> bool:
        """Turn display on."""
        return self.turn_display(STATUS_ON)

    def turn_off_display(self) -> bool:
        """Turn display off."""
        return self.turn_display(STATUS_OFF)

    def turn_display(self, status: str) -> bool:
        """Turn Display on/off VeSync LV-PUR131."""
        if status.lower() not in [STATUS_ON, STATUS_OFF]:
            logger.debug('Invalid display status - %s', status)
            return False
        body = self.manager.req_body_status()
        body['status'] = status.lower()

        r = self.call_api('updateScreen', 'put', body)
        if Helpers.code_check(r):
            self.details['screen_status'] = status.lower()
            return True
        logger.debug('Error toggling display for %s', self.device_name)
        return False

    def turn(self, status: str) -> bool:
        """Turn Air Purifier on/off."""
        if self.device_status != status:
            body = self.manager.req_body_status()
            body['uuid'] = self.uuid
            body['status'] = status

            r = self.call_api('deviceStatus', 'put', body)

            if Helpers.code_check(r):
                self.device_status = status
                return True
            logger.debug('Error turning %s on', self.device_name)
            return False
        return False

    def auto_mode(self) -> bool:
        """Set mode to auto."""
        return self.mode_turn(MODE_AUTO)

    def manual_mode(self) -> bool:
        """Set mode to manual."""
        return self.mode_turn(MODE_MANUAL)

    def sleep_mode(self) -> bool:
        """Set sleep mode to on."""
        return self.mode_turn(MODE_SLEEP)

    def change_fan_speed(self, speed: Optional[int] = None) -> bool:
        """Adjust Fan Speed for air purifier.

        Specifying 1,2,3 as argument or call without argument to cycle
        through speeds increasing by one.
        """
        if self.mode != MODE_MANUAL:
            logger.debug('%s not in manual mode, cannot change speed',
                         self.device_name)
            return False

        try:
            level = self.details['level']
        except KeyError:
            logger.debug(
                'Cannot change fan speed, no level set for %s',
                self.device_name
            )
            return False

        body = self.manager.req_body_status()
        body['uuid'] = self.uuid
        if speed is not None:
            if speed == level:
                return True
            if speed in [1, 2, 3]:
                body['level'] = speed
            else:
                logger.debug('Invalid fan speed for %s',
                             self.device_name)
                return False
        else:
            body['level'] = int((level % 3) + 1)

        r = self.call_api('updateSpeed', 'put', body)

        if Helpers.code_check(r):
            self.details['level'] = body['level']
            return True
        logger.debug('Error changing %s speed', self.device_name)
        return False

    def mode_turn(self, mode: str) -> bool:
        """Set mode to manual, auto or sleep."""
        body = self.manager.req_body_status()
        body['uuid'] = self.uuid
        if mode != self.mode and mode in [MODE_SLEEP, MODE_AUTO, MODE_MANUAL]:
            body['mode'] = mode
            if mode == MODE_MANUAL:
                body['level'] = 1

            r = self.call_api('updateMode', 'put', body)

            if Helpers.code_check(r):
                self.mode = mode
                return True

        logger.debug('Error setting %s mode - %s', self.device_name, mode)
        return False

    def update(self) -> None:
        """Run function to get device details."""
        self.get_details()

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp = [
            ('Active Time', str(self.active_time), 'min'),
            ('Fan Level', str(self.fan_level), ''),
            ('Air Quality', self.air_quality, ''),
            ('Mode', self.mode, ''),
            ('Screen Status', self.screen_status, ''),
            ('Filter Life', json.dumps(self.filter_life), '%')
            ]
        for line in disp:
            print(f"{line[0]+': ':.<30} {' '.join(line[1:])}")

    def displayJSON(self) -> str:
        """Return air purifier status and properties in JSON output."""
        sup = super().displayJSON()
        sup_val = json.loads(sup)
        sup_val.update(
            {
                'Active Time': str(self.active_time),
                'Fan Level': self.fan_level,
                'Air Quality': self.air_quality,
                'Mode': self.mode,
                'Screen Status': self.screen_status,
                'Filter Life': str(self.filter_life)
            }
        )
        return json.dumps(sup_val, indent=4)


class VeSyncHumid200300S(VeSyncFan):
    """200S/300S Humidifier Class."""
    mist_levels: list = []
    mist_modes: list = []
    _features: list = []
    warm_mist_levels: list = []
    warm_mist_feature: list = []
    night_light: bool = False
    config = {
        'auto_target_humidity': 0,
        'display': False,
        'automatic_stop': True
    }

    def __init__(self, details, manager):
        """Initialize 200S/300S Humidifier class."""
        super().__init__(details, manager)
        self.mist_levels = fan_mist_levels.get(self.device_type)
        self.mist_modes = fan_mist_modes.get(self.device_type)
        self.warm_mist_feature = self.supports('warm_mist')
        self.warm_mist_levels = fan_mist_levels_warm.get(self.device_type, [])
        self.night_light = self.supports('nightlight')
        self.details = {
            MODE_HUMIDITY: 0,
            'mist_virtual_level': 0,
            'mist_level': 0,
            'mode': MODE_MANUAL,
            'water_lacks': False,
            'humidity_high': False,
            'water_tank_lifted': False,
            'display': False,
            'automatic_stop_reach_target': False,
        }
        if self.night_light is True:
            self.details['night_light_brightness'] = 0

    def build_api_dict(self, method: str, config:list[str]=['configModule'], data:dict=None) -> Tuple[Dict, Dict]:
        """Build humidifier api call header and body."""
        body = super().build_api_dict(method, config, data)
        return body

    def build_humid_dict(self, dev_dict: Dict[str, str]) -> None:
        """Build humidifier status dictionary."""
        self.enabled = dev_dict.get('enabled')
        self.device_status = STATUS_ON if self.enabled else STATUS_OFF
        self.mode = dev_dict.get('mode', None)
        self.details[MODE_HUMIDITY] = dev_dict.get(MODE_HUMIDITY, 0)
        self.details['mist_virtual_level'] = dev_dict.get(
            'mist_virtual_level', 0)
        self.details['mist_level'] = dev_dict.get('mist_level', 0)
        self.details['mode'] = dev_dict.get('mode', MODE_MANUAL)
        self.details['water_lacks'] = dev_dict.get('water_lacks', False)
        self.details['humidity_high'] = dev_dict.get('humidity_high', False)
        self.details['water_tank_lifted'] = dev_dict.get(
            'water_tank_lifted', False)
        self.details['automatic_stop_reach_target'] = dev_dict.get(
            'automatic_stop_reach_target', True
        )
        if self.night_light:
            self.details['night_light_brightness'] = dev_dict.get(
                'night_light_brightness', 0)
        if self.warm_mist_feature:
            self.details['warm_mist_level'] = dev_dict.get(
                'warm_level', 0)
            self.details['warm_mist_enabled'] = dev_dict.get(
                'warm_enabled', False)
        try:
            self.details['display'] = dev_dict['display']
        except KeyError:
            self.details['display'] = dev_dict.get(
                'indicator_light_switch', False)

    def build_config_dict(self, conf_dict):
        """Build configuration dict for 300s humidifier."""
        self.config['auto_target_humidity'] = conf_dict.get(
            'auto_target_humidity', 0)
        self.config['display'] = conf_dict.get('display', False)
        self.config['automatic_stop'] = conf_dict.get('automatic_stop', True)

    def get_details(self) -> None:
        """Build 200S/300S Humidifier details dictionary."""
        body = self.build_api_dict('getHumidifierStatus', data={})
        r = self.manager.post_device_managed_v2(body)

        if r is None or not isinstance(r, dict):
            logger.debug("Error getting status of %s ", self.device_name)
            return
        if Helpers.code_check(r):
            outer_result = r.get('result', {})
            if outer_result is not None:
                inner_result = r.get('result', {}).get('result')
                if inner_result is not None:
                    if outer_result.get('code') == 0:
                        self.build_humid_dict(inner_result)
                    else:
                        logger.debug('error in inner result dict from humidifier')
                    if inner_result.get('configuration', {}):
                        self.build_config_dict(inner_result.get('configuration', {}))
                    else:
                        logger.debug('No configuration found in humidifier status')
            return
        logger.debug('Error in humidifier response')

    def update(self):
        """Update 200S/300S Humidifier details."""
        self.get_details()

    def turn(self, status: str) -> bool:
        """Turn humidifier on/off."""
        if not status in (STATUS_ON, STATUS_OFF):
            logger.debug('Invalid turn value for humidifier switch')
            return False
        turn = (status == STATUS_ON)

        body = self.build_api_dict('setSwitch', data={'enabled': turn, 'id': 0})
        r = self.manager.post_device_managed_v2(body)

        if Helpers.code_check(r):
            self.device_status = status
            return True
        logger.debug("Error toggling 300S humidifier - %s", self.device_name)
        return False

    def automatic_stop_on(self) -> bool:
        """Turn 200S/300S Humidifier automatic stop on."""
        return self.set_automatic_stop(True)

    def automatic_stop_off(self) -> bool:
        """Turn 200S/300S Humidifier automatic stop on."""
        return self.set_automatic_stop(False)

    def set_automatic_stop(self, mode: bool) -> bool:
        """Set 200S/300S Humidifier to automatic stop."""
        if mode not in (True, False):
            logger.debug(
                'Invalid mode passed to set_automatic_stop - %s', mode)
            return False

        body = self.build_api_dict('setAutomaticStop', data={'enabled': mode})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        if isinstance(r, dict):
            logger.debug('Error toggling automatic stop')
        else:
            logger.debug('Error in api return json for %s', self.device_name)
        return False

    def set_display(self, mode: bool) -> bool:
        """Turn display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        body = self.build_api_dict('setDisplay', data={'state': mode})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug("Error toggling 300S display - %s", self.device_name)
        return False

    def turn_on_display(self) -> bool:
        """Turn 200S/300S Humidifier on."""
        return self.set_display(True)

    def turn_off_display(self):
        """Turn 200S/300S Humidifier off."""
        return self.set_display(False)

    def set_humidity(self, humidity: int) -> bool:
        """Set target 200S/300S Humidifier humidity."""
        if humidity < 30 or humidity > 80:
            logger.debug("Humidity value must be set between 30 and 80")
            return False

        body = self.build_api_dict('setTargetHumidity', data={'target_humidity': humidity})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug('Error setting humidity')
        return False

    def set_night_light_brightness(self, brightness: int) -> bool:
        """Set target 200S/300S Humidifier night light brightness."""
        if not self.night_light:
            logger.debug('%s is a %s does not have a nightlight',
                         self.device_name, self.device_type)
            return False
        if brightness < 0 or brightness > 100:
            logger.debug("Brightness value must be set between 0 and 100")
            return False

        body = self.build_api_dict('setNightLightBrightness', data={'night_light_brightness': brightness})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug('Error setting humidity')
        return False

    def set_humidity_mode(self, mode: str) -> bool:
        """Set humidifier mode - sleep or auto."""
        if mode.lower() not in self.mist_modes:
            logger.debug('Invalid humidity mode used - %s',
                         mode)
            logger.debug('Proper modes for this device are - %s',
                         str(self.mist_modes))
            return False

        body = self.build_api_dict('setHumidityMode', data={'mode': mode.lower()})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug('Error setting humidity mode')
        return False

    def set_warm_level(self, warm_level) -> bool:
        """Set target 600S Humidifier mist warmth."""
        if not self.warm_mist_feature:
            logger.debug('%s is a %s does not have a mist warmer',
                         self.device_name, self.device_type)
            return False
        if not isinstance(warm_level, int):
            try:
                warm_level = int(warm_level)
            except ValueError:
                logger.debug('Error converting warm mist level to a integer')
        if warm_level not in self.warm_mist_levels:
            logger.debug("warm_level value must be - %s",
                         str(self.warm_mist_levels))
            return False

        data = {
            'type': 'warm',
            'level': warm_level,
            'id': 0,
        }
        body = self.build_api_dict('setLevel', data=data)
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug('Error setting warm')
        return False

    def set_auto_mode(self):
        """Set auto mode for humidifiers."""
        if MODE_AUTO in self.mist_modes:
            call_str = MODE_AUTO
        elif MODE_HUMIDITY in self.mist_modes:
            call_str = MODE_HUMIDITY
        else:
            logger.debug('Trying auto mode, mode not set for this model, '
                         'please ensure %s model '
                         'is in configuration dictionary', self.device_type)
            call_str = MODE_AUTO
        set_auto = self.set_humidity_mode(call_str)
        return set_auto

    def set_manual_mode(self):
        """Set humifier to manual mode with 1 mist level."""
        return self.set_humidity_mode(MODE_MANUAL)

    def set_mist_level(self, level) -> bool:
        """Set humidifier mist level with int between 0 - 9."""
        try:
            level = int(level)
        except ValueError:
            level = str(level)
        if level not in self.mist_levels:
            logger.debug('Humidifier mist level must be between 0 and 9')
            return False

        data = {
            'id': 0,
            'level': level,
            'type': 'mist'
        }
        body = self.build_api_dict('setVirtualLevel', data=data)
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug('Error setting mist level')
        return False

    @property
    def humidity(self):
        """Get Humidity level."""
        return self.details[MODE_HUMIDITY]

    @property
    def mist_level(self):
        """Get current mist level."""
        return self.details['mist_virtual_level']

    @property
    def water_lacks(self):
        """If tank is empty return true."""
        return self.details['water_lacks']

    @property
    def auto_humidity(self):
        """Auto target humidity."""
        return self.config['auto_target_humidity']

    @property
    def auto_enabled(self):
        """Auto mode is enabled."""
        if self.details.get('mode') == MODE_AUTO \
                or self.details.get('mode') == MODE_HUMIDITY:
            return True
        return False

    @property
    def warm_mist_enabled(self):
        """Warm mist feature enabled."""
        if self.warm_mist_feature:
            return self.details['warm_mist_enabled']
        return False

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp = [
            ('Mode', self.details['mode'], ''),
            ('Humidity', self.details[MODE_HUMIDITY], '%'),
            ('Mist Virtual Level', self.details['mist_virtual_level'], ''),
            ('Mist Level', self.details['mist_level'], ''),
            ('Water Lacks', self.details['water_lacks'], ''),
            ('Humidity High', self.details['humidity_high'], ''),
            ('Water Tank Lifted', self.details['water_tank_lifted'], ''),
            ('Display', self.details['display'], ''),
            ('Automatic Stop Reach Target', self.details['automatic_stop_reach_target'], ''),
            ('Auto Target Humidity', self.config['auto_target_humidity'], '%'),
            ('Automatic Stop', self.config['automatic_stop'], ''),
        ]
        if self.night_light:
            disp.append(('Night Light Brightness', self.details.get('night_light_brightness', ''), '%'))
        if self.warm_mist_feature:
            disp.append(('Warm mist enabled', self.details.get('warm_mist_enabled', ''), ''))
            disp.append(('Warm mist level', self.details.get('warm_mist_level', ''), ''))
        for line in disp:
            print(f"{line[0] + ': ':.<30} {' '.join(line[1:])}")

    def displayJSON(self) -> str:
        """Return air purifier status and properties in JSON output."""
        sup = super().displayJSON()
        sup_val = json.loads(sup)
        sup_val.update(
            {
                'Mode': self.details['mode'],
                'Humidity': str(self.details[MODE_HUMIDITY]),
                'Mist Virtual Level': str(
                    self.details['mist_virtual_level']),
                'Mist Level': str(self.details['mist_level']),
                'Water Lacks': self.details['water_lacks'],
                'Humidity High': self.details['humidity_high'],
                'Water Tank Lifted': self.details['water_tank_lifted'],
                'Display': self.details['display'],
                'Automatic Stop Reach Target': self.details[
                    'automatic_stop_reach_target'],
                'Auto Target Humidity': str(self.config[
                    'auto_target_humidity']),
                'Automatic Stop': self.config['automatic_stop'],
            }
        )
        if self.night_light:
            sup_val['Night Light Brightness'] = self.details[
                'night_light_brightness']
        if self.warm_mist_feature:
            sup_val['Warm mist enabled'] = self.details['warm_mist_enabled']
            sup_val['Warm mist level'] = self.details['warm_mist_level']
        return json.dumps(sup_val, indent=4)


class VeSyncHumid200S(VeSyncHumid200300S):
    """Levoit Classic 200S Specific class."""

    def __init__(self, details, manager):
        """Initialize levoit 200S device class."""
        super().__init__(details, manager)

    def set_display(self, mode: bool) -> bool:
        """Turn display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        data = {
            'enabled': mode,
            'id': 0
        }
        body = self.build_api_dict('setIndicatorLightSwitch', data=data)
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug("Error toggling 200S display - %s", self.device_name)
        return False


class VeSyncSuperior6000S(VeSyncFan):
    """Superior 6000S Humidifier."""

    _config_dict: dict = {}
    mist_levels: list[int] = []
    mist_modes: list[str] = []
    connection_status: str = None

    def __init__(self, details, manager):
        """Initialize Superior 6000S Humidifier class."""
        super().__init__(details, manager)
        self.mist_levels = fan_mist_levels.get(self.device_type, [])
        self.mist_modes = fan_mist_modes.get(self.device_type, [])
        self.connection_status = details.get('deviceProp', {}).get('connectionStatus')

    def build_api_dict(self, method: str, config: list[str] = ['configModule'], data: dict = None):
        body = super().build_api_dict(method, config, data)
        return body

    def build_humid_dict(self, dev_dict: Dict[str, str]) -> None:
        """Build humidifier status dictionary."""
        self.device_status = STATUS_OFF if dev_dict.get('powerSwitch', 0) == 0 else STATUS_ON
        self.mode = MODE_AUTO if dev_dict.get('workMode', '') == 'autoPro' \
            else dev_dict.get('workMode', '')
        self.details[MODE_HUMIDITY] = dev_dict.get(MODE_HUMIDITY, 0)
        self.details['target_humidity'] = dev_dict.get('targetHumidity', None)
        self.details['mist_virtual_level'] = dev_dict.get(
            'virtualLevel', 0)
        self.details['mist_level'] = dev_dict.get('mistLevel', 0)
        self.details['water_lacks'] = dev_dict.get('waterLacksState', False)
        self.details['water_tank_lifted'] = dev_dict.get(
            'waterTankLifted', False)
        self.details['filter_life_percentage'] = dev_dict.get('filterLifePercent', 0)
        self.details['temperature'] = dev_dict.get('temperature', 0)
        self.details['display'] = dev_dict.get('screenSwitch', None)
        self.details['drying_mode'] = dev_dict.get('dryingMode', {})

    def build_config_dict(self, _):
        """Build configuration dict for humidifier."""

    def get_details(self) -> None:
        """Build Humidifier details dictionary."""
        body = self.build_api_dict('getHumidifierStatus', data={})
        r = self.manager.post_device_managed_v2(body)

        if not Helpers.code_check(r):
            logger.debug("Error getting status of %s ", self.device_name)
            return
        outer_result = r.get('result', {})
        inner_result = None

        if outer_result is not None:
            inner_result = r.get('result', {}).get('result')
        if inner_result is not None:
            if outer_result.get('code') == 0:
                self.build_humid_dict(inner_result)
            else:
                logger.debug('error in inner result dict from humidifier')
            if inner_result.get('configuration', {}):
                self.build_config_dict(inner_result.get('configuration', {}))
            else:
                logger.debug('No configuration found in humidifier status')
        else:
            logger.debug('Error in humidifier response')

    def update(self):
        """Update humidifier details."""
        self.get_details()

    def turn(self, status: str) -> bool:
        """Turn humidifier on/off."""
        if not status in(STATUS_ON, STATUS_OFF):
            logger.debug('Invalid turn value for humidifier switch')
            return False
        turn = (status == STATUS_ON)

        body = self.build_api_dict('setSwitch', data={'powerSwitch': int(turn), 'switchIdx': 0})
        r = self.manager.post_device_managed_v2(body)

        if Helpers.code_check(r):
            self.device_status = status
            return True
        logger.debug("Error toggling humidifier - %s", self.device_name)
        return False

    def set_drying_mode_enabled(self, mode: bool) -> bool:
        """enable/disable drying filters after turning off."""
        if mode not in (True, False):
            logger.debug(
                'Invalid turn passed to set_drying_mode_enabled - %s', mode
            )
            return False

        body = self.build_api_dict('setDryingMode', data={'autoDryingSwitch': int(mode)})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        if isinstance(r, dict):
            logger.debug('Error in set_drying_mode_enabled response')
        else:
            logger.debug(
                'Error in set_drying_mode_enabled api return json for %s',
                self.device_name
            )
        return False

    def set_display_enabled(self, mode: bool) -> bool:
        """Turn display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        body = self.build_api_dict('setDisplay', data={'screenSwitch': int(mode)})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug("Error toggling display - %s", self.device_name)
        return False

    def turn_on_display(self) -> bool:
        """Turn display on."""
        return self.set_display_enabled(True)

    def turn_off_display(self):
        """Turn display off."""
        return self.set_display_enabled(False)

    def set_humidity(self, humidity: int) -> bool:
        """Set target humidity for humidity mode."""
        if humidity < 30 or humidity > 80:
            logger.debug("Humidity value must be set between 30 and 80")
            return False

        body = self.build_api_dict('setTargetHumidity', data={'targetHumidity': humidity})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug('Error setting humidity')
        return False

    def set_humidity_mode(self, mode: str) -> bool:
        """Set humidifier mode."""
        if mode not in self.mist_modes:
            logger.debug('Invalid humidity mode used - %s',
                         mode)
            logger.debug('Proper modes for this device are - %s',
                         str(self.mist_modes))
            return False
        data = {'workMode': 'autoPro' if mode == MODE_AUTO else mode}
        body = self.build_api_dict('setHumidityMode', data=data)
        r = self.manager.post_device_managed_v2(body)

        if Helpers.code_check(r):
            return True
        logger.debug('Error setting humidity mode')
        return False

    def set_auto_mode(self) -> bool:
        """Set humidity mode to auto."""
        return self.set_humidity_mode(MODE_AUTO)

    def set_manual_mode(self) -> bool:
        """Set humidity mode to manual."""
        return self.set_humidity_mode(MODE_MANUAL)

    def automatic_stop_on(self) -> bool:
        """Set humidity mode to auto."""
        return self.set_humidity_mode(MODE_AUTO)

    def automatic_stop_off(self) -> bool:
        """Set humidity mode to manual."""
        return self.set_humidity_mode(MODE_MANUAL)

    def set_mist_level(self, level) -> bool:
        """Set humidifier mist level with int between 0 - 9."""
        try:
            level = int(level)
        except ValueError:
            level = str(level)
        if level not in self.mist_levels:
            logger.debug('Humidifier mist level must be between 0 and 9')
            return False

        data = {
            'levelIdx': 0,
            'virtualLevel': level,
            'levelType': 'mist'
        }
        body = self.build_api_dict('setVirtualLevel', data=data)
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug('Error setting mist level')
        return False

    @property
    def humidity_level(self):
        """Get Humidity level."""
        return self.details[MODE_HUMIDITY]

    @property
    def mist_level(self):
        """Get current mist level."""
        return self.details['mist_level']

    @property
    def mist_virtual_level(self):
        """Get current mist virtual level."""
        return self.details['mist_virtual_level']

    @property
    def water_lacks(self):
        """If tank is empty return true."""
        if 'water_lacks' in self.details:
            return bool(self.details['water_lacks'])
        return None

    @property
    def drying_mode_state(self):
        """True if humidifier is currently drying the filters, false otherwise."""
        state = self.details.get('drying_mode', {}).get('dryingState')
        if state == 1:
            return STATUS_ON
        if state == 2:
            return STATUS_OFF
        return None

    @property
    def drying_mode_seconds_remaining(self):
        """If drying_mode_state is on, how many seconds are remaining."""
        return self.details.get('drying_mode', {}).get('dryingRemain')

    @property
    def drying_mode_enabled(self):
        """Checks if drying mode is enabled.

        Returns:
            bool: True if enabled, false if disabled

        """
        enabled = self.details.get('drying_mode', {}).get('autoDryingSwitch')
        return None if enabled is None else bool(enabled)

    @property
    def drying_mode_level(self):
        """Drying mode level 1 = low, 2 = high."""
        level = self.details.get('drying_mode', {}).get('dryingLevel')
        if level == 1:
            return 'low'
        if level == 2:
            return 'high'
        return None

    @property
    def temperature(self):
        """Current temperature."""
        return self.details['temperature']

    @property
    def auto_humidity(self):
        """Auto target humidity."""
        return self.config['target_humidity']

    @property
    def target_humidity(self):
        """The target humidity when in humidity mode."""
        return self.details['target_humidity']

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp = [
            ('Temperature', self.temperature, ''),
            ('Humidity', self.humidity_level, '%'),
            ('Target Humidity', self.target_humidity, '%'),
            ('Mode', self.mode, ''),
            ('Mist Virtual Level', self.details['mist_virtual_level'], ''),
            ('Mist Level', self.details['mist_level'], ''),
            ('Water Lacks', self.water_lacks, ''),
            ('Water Tank Lifted', bool(self.details['water_tank_lifted']), ''),
            ('Display On', bool(self.details['display']), ''),
            ('Filter Life', self.details['filter_life_percentage'], '%'),
            ('Drying Mode Enabled', self.drying_mode_enabled, ''),
            ('Drying Mode State', self.drying_mode_state, ''),
            ('Drying Mode Level', self.drying_mode_level, ''),
            ('Drying Mode Time Remaining', self.drying_mode_seconds_remaining, 'sec'),
        ]
        for line in disp:
            print(f"{line[0]+': ':.<30} {' '.join(line[1:])}")

    def displayJSON(self) -> str:
        """Return air purifier status and properties in JSON output."""
        sup = super().displayJSON()
        sup_val = json.loads(sup)
        sup_val.update(
            {
                'Temperature': self.temperature,
                'Humidity': self.humidity_level,
                'Target Humidity': self.target_humidity,
                'Mode': self.mode,
                'Mist Virtual Level': self.mist_virtual_level,
                'Mist Level': self.mist_level,
                'Water Lacks': self.details['water_lacks'],
                'Water Tank Lifted': bool(self.details['water_tank_lifted']),
                'Display On': bool(self.details['display']),
                'Filter Life': self.details['filter_life_percentage'],
                'Drying Mode Enabled': self.drying_mode_enabled,
                'Drying Mode State': self.drying_mode_state,
                'Drying Mode Level': self.drying_mode_level,
                'Drying Mode Time Remaining': self.drying_mode_seconds_remaining,
            }
        )
        return json.dumps(sup_val, indent=4)


class VeSyncHumid1000S(VeSyncHumid200300S):
    """Levoit OasisMist 1000S Specific class."""

    def __init__(self, details, manager):
        """Initialize levoit 1000S device class."""
        super().__init__(details, manager)
        self.connection_status = details.get('deviceProp', {}).get('connectionStatus', None)

    def build_humid_dict(self, dev_dict: Dict[str, str]) -> None:
        """Build humidifier status dictionary."""
        super().build_humid_dict(dev_dict)
        self.device_status = STATUS_OFF if dev_dict.get('powerSwitch', 0) == 0 else STATUS_ON
        self.details['mist_virtual_level'] = dev_dict.get( 'virtualLevel', 0)
        self.details['mist_level'] = dev_dict.get('mistLevel', 0)
        self.details['mode'] = dev_dict.get('workMode', MODE_MANUAL)
        self.details['water_lacks'] = bool(dev_dict.get('waterLacksState', 0))
        self.details['humidity_high'] = bool(int(dev_dict.get('targetHumidity', 0)) <
                                             int(dev_dict.get(MODE_HUMIDITY, 0)))
        self.details['water_tank_lifted'] = bool(dev_dict.get('waterTankLifted', 0))
        self.details['automatic_stop_reach_target'] = bool(dev_dict.get('autoStopState', 1))
        self.details['display'] = bool(dev_dict['screenState'])

    def build_config_dict(self, conf_dict):
        """Build configuration dict for humidifier."""
        self.config['auto_target_humidity'] = conf_dict.get('targetHumidity', 0)
        self.config['display'] = bool(conf_dict.get('screenSwitch', 0))
        self.config['automatic_stop'] = bool(conf_dict.get('autoStopSwitch', 1))

    def build_api_dict(self, method: str, config: list[str] = ['configModule'], data: dict=None):
        body = super().build_api_dict(method, config, data)
        return body

    def get_details(self) -> None:
        """Build Humidifier details dictionary."""
        body = self.build_api_dict('getHumidifierStatus', data={})
        r = self.manager.post_device_managed_v2(body)

        if not Helpers.code_check(r):
            logger.debug("Error getting status of %s ", self.device_name)
            return
        if r.get('code') in ERR_REQ_TIMEOUTS:
            logger.debug('%s device offline', self.device_name)
            self.connection_status = 'offline'
            self.device_status = STATUS_OFF
            return

        outer_result = r.get('result', {})
        if outer_result is not None:
            inner_result = r.get('result', {}).get('result')
            if inner_result is not None:
                if outer_result.get('code') == 0:
                    self.connection_status = 'online'
                    self.build_humid_dict(inner_result)
                    self.build_config_dict(inner_result)
                else:
                    logger.debug('error in inner result dict from humidifier')
            return
        logger.debug('Error in humidifier response')

    def set_display(self, mode: bool) -> bool:
        """Turn display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        body = self.build_api_dict('setDisplay', data={'screenSwitch': int(mode)})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug("Error toggling purifier display - %s",
                     self.device_name)
        return False

    def set_humidity_mode(self, mode: str) -> bool:
        """Set humidifier mode - sleep, auto or manual."""
        if mode.lower() not in self.mist_modes:
            logger.debug('Invalid humidity mode used - %s',
                         mode)
            logger.debug('Proper modes for this device are - %s',
                         str(self.mist_modes))
            return False

        body = self.build_api_dict('setHumidityMode', data={'workMode': mode.lower()})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug('Error setting humidity mode')
        return False

    def set_sleep_mode(self):
        """Set humifier to manual mode with 1 mist level."""
        return self.set_humidity_mode(MODE_SLEEP)

    def set_mist_level(self, level) -> bool:
        """Set humidifier mist level with int."""
        try:
            level = int(level)
        except ValueError:
            level = str(level)
        if level not in self.mist_levels:
            logger.debug('Humidifier mist level out of range')
            return False

        data = {
            'levelIdx': 0,
            'virtualLevel': level,
            'levelType': 'mist'
        }
        body = self.build_api_dict('setVirtualLevel', data=data)
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug('Error setting mist level')
        return False

    def turn(self, status: str) -> bool:
        """Turn humidifier on/off."""
        if not status in(STATUS_ON, STATUS_OFF):
            logger.debug('Invalid turn value for humidifier switch')
            return False
        turn = (status == STATUS_ON)

        data = {
            'powerSwitch': int(turn),
            'switchIdx': 0
        }
        body = self.build_api_dict('setSwitch', data=data)
        r = self.manager.post_device_managed_v2(body)

        if Helpers.code_check(r):
            self.device_status = status
            return True
        logger.debug("Error toggling humidifier - %s", self.device_name)
        return False

    def set_humidity(self, humidity: int) -> bool:
        """Set target Humidifier humidity."""
        if humidity < 30 or humidity > 80:
            logger.debug("Humidity value must be set between 30 and 80")
            return False

        body = self.build_api_dict('setTargetHumidity', data={'targetHumidity': humidity})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        logger.debug('Error setting humidity')
        return False

    def set_automatic_stop(self, mode: bool) -> bool:
        """Set  Humidifier to automatic stop."""
        if mode not in (True, False):
            logger.debug(
                'Invalid mode passed to set_automatic_stop - %s', mode)
            return False

        body = self.build_api_dict('setAutoStopSwitch', data={'autoStopSwitch': int(mode)})
        r = self.manager.post_device_managed_v2(body)
        if Helpers.code_check(r):
            return True
        if isinstance(r, dict):
            logger.debug('Error toggling automatic stop')
        else:
            logger.debug('Error in api return json for %s', self.device_name)
        return False


def factory(module: str, details: dict, manager) -> VeSyncFan:
    try:
        class_name = fan_classes[module]
        fan = getattr(module_fan, class_name)
        return fan(details, manager)
    except:
        return None