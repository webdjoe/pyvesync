"""VeSync API for controling fans and purifiers."""

import logging
from typing import Any, TYPE_CHECKING
import orjson
from pyvesync.vesyncbasedevice import VeSyncBaseDevice
from pyvesync.helpers import Helpers, Timer
from pyvesync.logs import LibraryLogger
from pyvesync.errors import ErrorCodes

if TYPE_CHECKING:
    from pyvesync import VeSync


humid_features: dict = {
    'Classic300S': {
        'module': 'VeSyncHumid200300S',
        'models': ['Classic300S', 'LUH-A601S-WUSB', 'LUH-A601S-AUSW'],
        'features': ['nightlight'],
        'mist_modes': ['auto', 'sleep', 'manual'],
        'mist_levels': list(range(1, 10))
    },
    'Classic200S': {
        'module': 'VeSyncHumid200S',
        'models': ['Classic200S'],
        'features': [],
        'mist_modes': ['auto', 'manual'],
        'mist_levels': list(range(1, 10))
    },
    'Dual200S': {
        'module': 'VeSyncHumid200300S',
        'models': ['Dual200S',
                   'LUH-D301S-WUSR',
                   'LUH-D301S-WJP',
                   'LUH-D301S-WEU'],
        'features': [],
        'mist_modes': ['auto', 'manual'],
        'mist_levels': list(range(1, 3))
    },
    'LV600S': {
        'module': 'VeSyncHumid200300S',
        'models': ['LUH-A602S-WUSR',
                   'LUH-A602S-WUS',
                   'LUH-A602S-WEUR',
                   'LUH-A602S-WEU',
                   'LUH-A602S-WJP',
                   'LUH-A602S-WUSC'],
        'features': ['warm_mist', 'nightlight'],
        'mist_modes': ['humidity', 'sleep', 'manual'],
        'mist_levels': list(range(1, 10)),
        'warm_mist_levels': [0, 1, 2, 3]
    },
    'OASISMISTEU': {
            'module': 'VeSyncHumid200300S',
            'models': ['LUH-O451S-WEU'],
            'features': ['warm_mist', 'nightlight'],
            'mist_modes': ['auto', 'manual'],
            'mist_levels': list(range(1, 10)),
            'warm_mist_levels': list(range(4))
    },
    'OASISMIST': {
            'module': 'VeSyncHumid200300S',
            'models': ['LUH-O451S-WUS',
                       'LUH-O451S-WUSR',
                       'LUH-O601S-WUS',
                       'LUH-O601S-KUS'],
            'features': ['warm_mist'],
            'mist_modes': ['auto', 'humidity', 'sleep', 'manual'],
            'mist_levels': list(range(1, 10)),
            'warm_mist_levels': list(range(4))
    },
    'OASISMIST1000S': {
            'module': 'VeSyncHumid1000S',
            'models': ['LUH-M101S-WUS'],
            'features': [],
            'mist_modes': ['auto', 'sleep', 'manual'],
            'mist_levels': list(range(1, 10))
    },
    'Superior6000S': {
            'module': 'VeSyncSuperior6000S',
            'models': ['LEH-S601S-WUS', 'LEH-S601S-WUSR'],
            'features': [],
            'mist_modes': ['auto', 'humidity', 'sleep', 'manual'],
            'mist_levels': list(range(1, 10))
    }
}


air_features: dict = {
    'Core200S': {
        'module': 'VeSyncAirBypass',
        'models': ['Core200S', 'LAP-C201S-AUSR', 'LAP-C202S-WUSR'],
        'modes': ['sleep', 'off', 'manual'],
        'features': ['reset_filter'],
        'levels': list(range(1, 4))
    },
    'Core300S': {
        'module': 'VeSyncAirBypass',
        'models': ['Core300S', 'LAP-C301S-WJP', 'LAP-C302S-WUSB', 'LAP-C301S-WAAA'],
        'modes': ['sleep', 'off', 'auto', 'manual'],
        'features': ['air_quality'],
        'levels': list(range(1, 5))
    },
    'Core400S': {
        'module': 'VeSyncAirBypass',
        'models': ['Core400S',
                   'LAP-C401S-WJP',
                   'LAP-C401S-WUSR',
                   'LAP-C401S-WAAA'],
        'modes': ['sleep', 'off', 'auto', 'manual'],
        'features': ['air_quality'],
        'levels': list(range(1, 5))
    },
    'Core600S': {
        'module': 'VeSyncAirBypass',
        'models': ['Core600S',
                   'LAP-C601S-WUS',
                   'LAP-C601S-WUSR',
                   'LAP-C601S-WEU'],
        'modes': ['sleep', 'off', 'auto', 'manual'],
        'features': ['air_quality'],
        'levels': list(range(1, 5))
    },
    'LV-PUR131S': {
        'module': 'VeSyncAir131',
        'models': ['LV-PUR131S', 'LV-RH131S'],
        'modes': ['manual', 'auto', 'sleep', 'off'],
        'features': ['air_quality'],
        'levels': list(range(1, 3))
    },
    'Vital100S': {
        'module': 'VeSyncAirBaseV2',
        'models': ['LAP-V102S-AASR', 'LAP-V102S-WUS', 'LAP-V102S-WEU',
                   'LAP-V102S-AUSR', 'LAP-V102S-WJP'],
        'modes': ['manual', 'auto', 'sleep', 'off', 'pet'],
        'features': ['air_quality'],
        'levels': list(range(1, 5))
    },
    'Vital200S': {
        'module': 'VeSyncAirBaseV2',
        'models': ['LAP-V201S-AASR', 'LAP-V201S-WJP', 'LAP-V201S-WEU',
                   'LAP-V201S-WUS', 'LAP-V201-AUSR', 'LAP-V201S-AUSR',
                   'LAP-V201S-AEUR'],
        'modes': ['manual', 'auto', 'sleep', 'off', 'pet'],
        'features': ['air_quality'],
        'levels': list(range(1, 5))
    },
    'EverestAir': {
        'module': 'VeSyncAirBaseV2',
        'models': ['LAP-EL551S-AUS', 'LAP-EL551S-AEUR',
                   'LAP-EL551S-WEU', 'LAP-EL551S-WUS'],
        'modes': ['manual', 'auto', 'sleep', 'off', 'turbo'],
        'features': ['air_quality', 'fan_rotate'],
        'levels': list(range(1, 4))
    },
    'SmartTowerFan': {
        'module': 'VeSyncTowerFan',
        'models': ['LTF-F422S-KEU', 'LTF-F422S-WUSR', 'LTF-F422_WJP', 'LTF-F422S-WUS'],
        'modes': ['normal', 'auto', 'advancedSleep', 'turbo', 'off'],
        'set_mode_method': 'setTowerFanMode',
        'features': ['fan_speed'],
        'levels': list(range(1, 13))
    }
}


logger = logging.getLogger(__name__)


def model_dict() -> dict:
    """Build purifier and humidifier model dictionary.

    Internal function to build a dictionary of device models and their associated
    classes. Used by the `vesync.object_factory` to determine the class to instantiate.
    """
    model_modules = {}
    for dev_dict in {**air_features, **humid_features}.values():
        for model in dev_dict['models']:
            model_modules[model] = dev_dict['module']
    return model_modules


def model_features(dev_type: str) -> dict:
    """Get features from device type.

    Used by classes to determine the features of the device.

    Parameters:
        dev_type (str): Device model type

    Returns:
        dict: Device dictionary

    Raises:
        ValueError: Device not configured in `air_features` or `humid_features`
    """
    for dev_dict in {**air_features, **humid_features}.values():
        if dev_type in dev_dict['models']:
            return dev_dict
    raise ValueError('Device not configured')


fan_classes: set = {v['module']
                    for k, v in {**air_features, **humid_features}.items()}

fan_modules: dict = model_dict()

__all__: list = [*fan_classes, 'fan_modules']  # noqa: PLE0604


class VeSyncAirBypass(VeSyncBaseDevice):
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

    def __init__(self, details: dict[str, list], manager: 'VeSync') -> None:
        """Initialize VeSync Air Purifier Bypass Base Class."""
        super().__init__(details, manager)
        self.enabled = True
        self._config_dict = model_features(self.device_type)
        self._features = self._config_dict.get('features', [])
        if not isinstance(self._config_dict.get('modes'), list):
            logger.error(
                'Please set modes for %s in the configuration',
                self.device_type)
            raise KeyError(f'Modes not set in configuration for {self.device_name}')
        self.modes = self._config_dict['modes']
        if 'air_quality' in self._features:
            self.air_quality_feature = True
        else:
            self.air_quality_feature = False
        self.details: dict[str, Any] = {
            'filter_life': 0,
            'mode': 'manual',
            'level': 0,
            'display': False,
            'child_lock': False,
            'night_light': 'off',
        }
        self.timer: Timer | None = None
        if self.air_quality_feature is True:
            self.details['air_quality'] = 0
        self.config: dict[str, str | int | float | bool] = {
            'display': False,
            'display_forever': False
        }

    def build_api_dict(self, method: str) -> tuple[dict, dict]:
        """Build device api body dictionary.

        This method is used internally as a helper function to build API
        requests.

        Parameters:
            method (str): API method to call

        Returns:
            Tuple(dict, dict): Tuple of headers and body dictionaries

        Notes:
            Possible methods are:

            1. 'getPurifierStatus'
            2. 'setSwitch'
            3. 'setNightLight'
            4. 'setLevel'
            5. 'setPurifierMode'
            6. 'setDisplay'
            7. 'setChildLock'
            8. 'setIndicatorLight'
            9. 'getTimer'
            10. 'addTimer'
            11. 'delTimer'
            12. 'resetFilter'

        """
        modes = ['getPurifierStatus', 'setSwitch', 'setNightLight',
                 'setLevel', 'setPurifierMode', 'setDisplay',
                 'setChildLock', 'setIndicatorLight', 'getTimer',
                 'addTimer', 'delTimer', 'resetFilter']
        if method not in modes:
            logger.debug('Invalid mode - %s', method)
            return {}, {}
        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': method,
            'source': 'APP'
        }
        return head, body

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
            self.device_status = 'on'
        else:
            self.device_status = 'off'
        self.details['filter_life'] = dev_dict.get('filter_life', 0)
        self.mode = dev_dict.get('mode', 'manual')
        self.speed = dev_dict.get('level', 0)
        self.details['display'] = dev_dict.get('display', False)
        self.details['child_lock'] = dev_dict.get('child_lock', False)
        self.details['night_light'] = dev_dict.get('night_light', 'off')
        self.details['display'] = dev_dict.get('display', False)
        self.details['display_forever'] = dev_dict.get('display_forever',
                                                       False)
        if self.air_quality_feature is True:
            self.details['air_quality_value'] = dev_dict.get(
                'air_quality_value', 0)
            self.details['air_quality'] = dev_dict.get('air_quality', 0)

    def build_config_dict(self, conf_dict: dict[str, str]) -> None:
        """Build configuration dict for Bypass purifier.

        Used by the `update()` method to populate the `config` attribute.

        Args:
            conf_dict (dict): Dictionary of device configuration
        """
        self.config['display'] = conf_dict.get('display', False)
        self.config['display_forever'] = conf_dict.get('display_forever',
                                                       False)

    async def get_details(self) -> None:
        """Build Bypass Purifier details dictionary."""
        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': 'getPurifierStatus',
            'source': 'APP',
            'data': {}
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return
        if not isinstance(r.get('result', {}).get("result"), dict):
            LibraryLogger.log_api_response_parse_error(
                logger,
                self.device_name,
                self.device_type,
                "get_details",
                "Result not found in response"
            )
            return
        inner_result = r.get('result', {}).get('result')
        if inner_result is not None:
            self.build_purifier_dict(inner_result)

    async def update(self) -> None:
        """Update Purifier details."""
        await self.get_details()

    async def get_timer(self) -> Timer | None:
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
        head, body = self.build_api_dict('getTimer')
        body['payload']['data'] = {}
        if not head and not body:
            return None

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_timer", self, r_bytes)
        if r is None:
            return None

        timer_list = r.get('result', {}).get('result', {}).get('timers')
        if not isinstance(timer_list, list):
            LibraryLogger.log_api_response_parse_error(
                logger,
                self.device_name,
                self.device_type,
                "get_timer",
                "Timer list not found in response"
            )
            return None
        if not timer_list:
            logger.debug("No timers found")
            return None

        timer = timer_list[0]
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

    async def set_timer(self, timer_duration: int) -> bool:
        """Set timer for Purifier.

        Args:
            timer_duration (int): Duration of timer in seconds

        Returns:
            bool : True if timer is set, False if not

        """
        if self.device_status != 'on':
            logger.debug("Can't set timer when device is off")
        head, body = self.build_api_dict('addTimer')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'total': timer_duration,
            'action': 'off',
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_timer", self, r_bytes)
        if r is None:
            return False

        result = r.get('result', {})
        if result.get('code') != 0:
            result_code = result.get('code')
            error_info = ErrorCodes.get_error_info(result_code)
            if error_info.device_online is False:
                self.device_status = 'off'
                self.connection_status = 'offline'
            LibraryLogger.log_api_response_parse_error(
                logger, self.device_name, self.device_type,
                "set_timer", error_info.error_message
            )
            return False

        timer_id = result.get('result', {}).get('id')
        if timer_id is not None:
            self.timer = Timer(timer_duration=timer_duration,
                               action='off',
                               id=timer_id)
        else:
            self.timer = Timer(timer_duration=timer_duration,
                               action='off')
        return True

    async def clear_timer(self) -> bool:
        """Clear timer.

        Returns True if no error is returned from API call.

        Returns:
            bool : True if timer is cleared, False if not
        """
        await self.get_timer()
        if self.timer is None:
            logger.debug('No timer to clear')
            return False
        if self.timer.id is None:
            logger.debug("Timer doesn't have an ID, can't clear")
        head, body = self.build_api_dict('delTimer')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'id': self.timer.id
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "clear_timer", self, r_bytes)
        if r is None:
            return False

        logger.debug("Timer cleared")
        return True

    async def change_fan_speed(self,
                               speed: None | int = None) -> bool:
        """Change fan speed based on levels in configuration dict.

        If no value is passed, the next speed in the list is selected.

        Args:
            speed (int, optional): Speed to set fan. Defaults to None.

        Returns:
            bool : True if speed is set, False if not
        """
        speeds: list = self._config_dict.get('levels', [])
        current_speed = self.speed

        if speed is not None:
            if speed not in speeds:
                logger.debug("%s is invalid speed - valid speeds are %s",
                             speed, str(speeds))
                return False
            new_speed = speed
        elif current_speed == speeds[-1]:
            new_speed = speeds[0]
        else:
            current_index = speeds.index(current_speed)
            new_speed = speeds[current_index + 1]

        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid

        head, body = self.build_api_dict('setLevel')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'id': 0,
            'level': new_speed,
            'type': 'wind',
            'mode': 'manual',
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "change_fan_speed", self, r_bytes)
        if r is None:
            return False

        self.speed = new_speed
        return True

    async def child_lock_on(self) -> bool:
        """Turn Bypass child lock on."""
        return await self.set_child_lock(True)

    async def child_lock_off(self) -> bool:
        """Turn Bypass child lock off.

        Returns:
            bool : True if child lock is turned off, False if not
        """
        return self.set_child_lock(False)

    async def set_child_lock(self, mode: bool) -> bool:
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

        head, body = self.build_api_dict('setChildLock')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'child_lock': mode
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_child_lock", self, r_bytes)
        if r is None:
            return False

        self.details['child_lock'] = mode
        return True

    async def reset_filter(self) -> bool:
        """Reset filter to 100%.

        Returns:
            bool : True if filter is reset, False if not
        """
        if 'reset_filter' not in self._features:
            logger.debug("Filter reset not implemented for %s", self.device_type)
            return False

        head, body = self.build_api_dict('resetFilter')
        if not head and not body:
            return False

        body['payload']['data'] = {}

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "reset_filter", self, r_bytes)
        return bool(r)

    async def mode_toggle(self, mode: str) -> bool:
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
        head, body = self.build_api_dict('setPurifierMode')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'mode': mode.lower()
        }
        if mode == 'manual':
            body['payload'] = {
                'data': {
                    'id': 0,
                    'level': 1,
                    'type': 'wind'
                },
                'method': 'setLevel',
                'type': 'APP'
            }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "mode_toggle", self, r_bytes)
        if r is None:
            return False

        if mode.lower() == 'manual':
            self.speed = 1
            self.mode = 'manual'
        else:
            self.mode = mode
            self.speed = 0
        return True

    async def manual_mode(self) -> bool:
        """Set mode to manual.

        Calls method [pyvesync.VeSyncAirBypass.mode_toggle][`self.mode_toggle('manual')`]
        to set mode to manual.

        Returns:
            bool : True if mode is set, False if not
        """
        if 'manual' not in self.modes:
            logger.debug('%s does not have manual mode', self.device_name)
            return False
        return await self.mode_toggle('manual')

    async def sleep_mode(self) -> bool:
        """Set sleep mode to on.

        Calls method [pyvesync.VeSyncAirBypass.mode_toggle][`self.mode_toggle('sleep')`]

        Returns:
            bool : True if mode is set, False if not
        """
        if 'sleep' not in self.modes:
            logger.debug('%s does not have sleep mode', self.device_name)
            return False
        return await self.mode_toggle('sleep')

    async def auto_mode(self) -> bool:
        """Set mode to auto.

        Calls method [pyvesync.VeSyncAirBypass.mode_toggle][`self.mode_toggle('sleep')`]

        Returns:
            bool : True if mode is set, False if not
        """
        if 'auto' not in self.modes:
            logger.debug('%s does not have auto mode', self.device_name)
            return False
        return await self.mode_toggle('auto')

    async def toggle_switch(self, toggle: bool) -> bool:
        """Toggle purifier on/off.

        Helper method for `turn_on()` and `turn_off()` methods.

        Args:
            toggle (bool): True to turn on, False to turn off

        Returns:
            bool : True if purifier is toggled, False if not
        """
        if not isinstance(toggle, bool):
            logger.debug('Invalid toggle value for purifier switch')
            return False

        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'data': {
                'enabled': toggle,
                'id': 0
            },
            'method': 'setSwitch',
            'source': 'APP'
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        if toggle:
            self.device_status = 'on'
        else:
            self.device_status = 'off'
        return True

    async def turn_on(self) -> bool:
        """Turn bypass Purifier on.

        Calls method [pyvesync.VeSyncAirBypass.toggle_switch][`self.toggle_switch(True)`]

        Returns:
            bool : True if purifier is turned on, False if not
        """
        return await self.toggle_switch(True)

    async def turn_off(self) -> bool:
        """Turn Bypass Purifier off.

        Calls method [pyvesync.VeSyncAirBypass.toggle_switch][`self.toggle_switch(False)`]

        Returns:
            bool : True if purifier is turned off, False if not
        """
        return await self.toggle_switch(False)

    async def set_display(self, mode: bool) -> bool:
        """Toggle display on/off.

        Called by `turn_on_display()` and `turn_off_display()` methods.

        Args:
            mode (bool): True to turn display on, False to turn off

        Returns:
            bool : True if display is toggled, False if not
        """
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        head, body = self.build_api_dict('setDisplay')

        body['payload']['data'] = {
            'state': mode
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_display", self, r_bytes)

        return bool(r)

    async def turn_on_display(self) -> bool:
        """Turn Display on.

        Calls method [pyvesync.VeSyncAirBypass.set_display][`self.set_display(True)`]

        Returns:
            bool : True if display is turned on, False if not
        """
        return await self.set_display(True)

    async def turn_off_display(self) -> bool:
        """Turn Display off.

        Calls method [pyvesync.VeSyncAirBypass.set_display][`self.set_display(False)`]

        Returns:
            bool : True if display is turned off, False if not
        """
        return await self.set_display(False)

    async def set_night_light(self, mode: str) -> bool:
        """Set night light.

        Possible modes are on, off or dim.

        Args:
            mode (str): Mode to set night light

        Returns:
            bool : True if night light is set, False if not
        """
        if mode.lower() not in ['on', 'off', 'dim']:
            logger.debug('Invalid nightlight mode used (on, off or dim)- %s',
                         mode)
            return False
        head, body = self.build_api_dict('setNightLight')
        if not head and not body:
            return False
        body['payload']['data'] = {
            'night_light': mode.lower()
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_night_light", self, r_bytes)
        if r is None:
            return False

        self.details['night_light'] = mode.lower()
        return True

    @property
    def air_quality(self) -> int:
        """Get air quality value (ug/m3)."""
        if self.air_quality_feature is not True:
            logger.debug("%s does not have air quality sensor",
                         self.device_type)
        try:
            return int(self.details['air_quality'])
        except KeyError:
            return 0

    @property
    def fan_level(self) -> int | None:
        """Get current fan level."""
        return self.speed

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
            ('Mode: ', self.mode, ''),
            ('Filter Life: ', self.details['filter_life'], 'percent'),
            ('Fan Level: ', self.speed, ''),
            ('Display: ', self.details['display'], ''),
            ('Child Lock: ', self.details['child_lock'], ''),
            ('Night Light: ', self.details['night_light'], ''),
            ('Display Config: ', self.config['display'], ''),
            ('Display_Forever Config: ',
             self.config['display_forever'], '')
        ]
        if self.air_quality_feature:
            disp.extend([
                ('Air Quality Level: ',
                    self.details.get('air_quality', ''), ''),
                ('Air Quality Value: ',
                    self.details.get('air_quality_value', ''), 'ug/m3')
                ])
        for line in disp:
            print(f'{line[0]:.<30} {line[1]} {line[2]}')

    def displayJSON(self) -> str:
        """Return air purifier status and properties in JSON output.

        Returns:
            str : JSON formatted string of air purifier details
        """
        sup = super().displayJSON()
        sup_val = orjson.loads(sup)
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
        return orjson.dumps(
            sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode()


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

    def __init__(self, details: dict[str, list], manager: 'VeSync') -> None:
        """Initialize the VeSync Base API V2 Air Purifier Class."""
        super().__init__(details, manager)
        self.set_speed_level: int | None = None
        self.auto_prefences: list[str] = ['default', 'efficient', 'quiet']

    def build_api_dict(self, method: str) -> tuple[dict, dict]:
        """Return default body for Bypass V2 API."""
        header = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['deviceId'] = self.cid
        body['configModule'] = self.config_module
        body['configModel'] = self.config_module
        body['payload'] = {
            'method': method,
            'source': 'APP',
            'data': {}
        }
        return header, body

    @property
    def light_detection(self) -> bool:
        """Return true if light detection feature is enabled."""
        return self.details['light_detection_switch']

    @light_detection.setter
    def light_detection(self, toggle: bool) -> None:
        """Set light detection feature."""
        self.details['light_detection_switch'] = toggle

    @property
    def light_detection_state(self) -> bool:
        """Return true if light is detected."""
        return self.details['environment_light_state']

    async def get_details(self) -> None:
        """Build API V2 Purifier details dictionary."""
        head, body = self.build_api_dict('getPurifierStatus')

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        result = r.get('result', {})
        result_code = result.get('code')
        if result_code != 0:
            error_info = ErrorCodes.get_error_info(result_code)
            if error_info.device_online is False:
                self.device_status = 'off'
                self.connection_status = 'offline'
            LibraryLogger.log_api_response_parse_error(
                logger, self.device_name, self.device_type,
                "get_details", error_info.error_message
            )
            return

        inner_result = result.get('result')

        if isinstance(inner_result, dict):
            self.build_purifier_dict(inner_result)
            if inner_result.get('configuration', {}):
                self.build_config_dict(inner_result.get('configuration', {}))
                return
        LibraryLogger.log_api_response_parse_error(
            logger,
            self.device_name,
            self.device_type,
            "get_details",
            "Error in response nested results"
        )

    def build_purifier_dict(self, dev_dict: dict) -> None:
        """Build Bypass purifier status dictionary."""
        self.connection_status = 'online'
        power_switch = bool(dev_dict.get('powerSwitch', 0))
        self.enabled = power_switch
        self.device_status = 'on' if power_switch is True else 'off'
        self.mode = dev_dict.get('workMode', 'manual')

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
            self.details['air_quality_value'] = dev_dict.get(
                'PM25', 0)
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
            self.timer = Timer(dev_dict['timerRemain'], 'off')
        if isinstance(dev_dict.get('autoPreference'), dict):
            self.details['auto_preference_type'] = dev_dict.get(
                'autoPreference', {}).get('autoPreferenceType', 'default')
        else:
            self.details['auto_preference_type'] = None

    async def turbo_mode(self) -> bool:
        """Turn on Turbo mode for compatible devices."""
        if 'turbo' in self.modes:
            return await self.mode_toggle('turbo')
        logger.debug("Turbo mode not available for %s", self.device_name)
        return False

    async def pet_mode(self) -> bool:
        """Set Pet Mode for compatible devices."""
        if 'pet' in self.modes:
            return await self.mode_toggle('pet')
        logger.debug("Pet mode not available for %s", self.device_name)
        return False

    async def set_night_light(self, mode: str) -> bool:
        """TODO: Set night light."""
        logger.debug("Night light feature not configured")
        return False

    async def set_light_detection(self, toggle: bool) -> bool:
        """Enable/Disable Light Detection Feature."""
        toggle_id = int(toggle)
        if self.details['light_detection_switch'] == toggle_id:
            logger.debug("Light Detection is already set to %s", toggle_id)
            return True

        head, body = self.build_api_dict('setLightDetection')
        body['payload']['data']['lightDetectionSwitch'] = toggle_id
        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_light_detection", self, r_bytes)
        if r is None:
            return False

        self.details['light_detection'] = toggle
        return True

    async def set_light_detection_on(self) -> bool:
        """Turn on light detection feature."""
        return await self.set_light_detection(True)

    async def set_light_detection_off(self) -> bool:
        """Turn off light detection feature."""
        return await self.set_light_detection(False)

    async def toggle_switch(self, toggle: bool) -> bool:
        """Toggle purifier on/off."""
        if not isinstance(toggle, bool):
            logger.debug('Invalid toggle value for purifier switch')
            return False

        head, body = self.build_api_dict('setSwitch')
        power = int(toggle)
        body['payload']['data'] = {
                'powerSwitch': power,
                'switchIdx': 0
            }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        if toggle is True:
            self.device_status = 'on'
        else:
            self.device_status = 'off'
        return True

    async def set_child_lock(self, mode: bool) -> bool:
        """Levoit 100S/200S set Child Lock.

        Parameters:
            mode (bool): True to turn child lock on, False to turn off

        Returns:
            bool : True if successful, False if not
        """
        toggle_id = int(mode)
        head, body = self.build_api_dict('setChildLock')
        body['payload']['data'] = {
            'childLockSwitch': toggle_id
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_child_lock", self, r_bytes)
        if r is None:
            return False

        self.details['child_lock'] = mode
        return True

    async def set_display(self, mode: bool) -> bool:
        """Levoit Vital 100S/200S Set Display on/off with True/False."""
        mode_id = int(mode)
        head, body = self.build_api_dict('setDisplay')
        body['payload']['data'] = {
            'screenSwitch': mode_id
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_display", self, r_bytes)
        if r is None:
            return False

        self.details['screen_switch'] = mode
        return True

    async def set_timer(self, timer_duration: int, action: str = 'off',
                        method: str = 'powerSwitch') -> bool:
        """Set timer for Levoit 100S.

        Parameters:
            timer_duration (int):
                Timer duration in seconds.
            action (str | None):
                Action to perform, on or off, by default 'off'
            method (str | None):
                Method to use, by default 'powerSwitch' - TODO: Implement other methods

        Returns:
            bool : True if successful, False if not
        """
        if action not in ['on', 'off']:
            logger.debug('Invalid action for timer')
            return False
        if method not in ['powerSwitch']:
            logger.debug('Invalid method for timer')
            return False
        action_id = 1 if action == 'on' else 0

        head, body = self.build_api_dict('addTimerV2')
        body['payload']['subDeviceNo'] = 0
        body['payload']['data'] = {
            "startAct": [{
                "type": method,
                "num": 0,
                "act": action_id,
            }],
            "total": timer_duration,
            "subDeviceNo": 0
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_timer", self, r_bytes)
        if r is None:
            return False

        self.timer = Timer(timer_duration, action)
        return True

    async def clear_timer(self) -> bool:
        """Clear running timer."""
        head, body = self.build_api_dict('delTimerV2')
        body['payload']['subDeviceNo'] = 0
        body['payload']['data'] = {'id': 1, "subDeviceNo": 0}

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "clear_timer", self, r_bytes)
        if r is None:
            return False

        self.timer = None
        return True

    async def set_auto_preference(self, preference: str = 'default',
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
        head, body = self.build_api_dict('setAutoPreference')
        body['payload']['data'] = {
            'autoPreference': preference,
            'roomSize': room_size,
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_auto_preference", self, r_bytes)
        if r is None:
            return False

        self.details['auto_preference'] = preference
        return True

    async def change_fan_speed(self, speed: None | int = None) -> bool:
        """Change fan speed based on levels in configuration dict.

        The levels are defined in the configuration dict for the device. If no level is
        passed, the next valid level will be used. If the current level is the last level.

        Parameters:
            speed (int | None): Speed to set based on levels in configuration dict
        """
        speeds: list = self._config_dict.get('levels', [])
        current_speed = self.set_speed_level or 0

        if speed is not None:
            if speed not in speeds:
                logger.debug("%s is invalid speed - valid speeds are %s",
                             speed, str(speeds))
                return False
            new_speed = speed
        elif current_speed in [speeds[-1], 0]:
            new_speed = speeds[0]
        else:
            current_index = speeds.index(current_speed)
            new_speed = speeds[current_index + 1]

        head, body = self.build_api_dict('setLevel')
        if not head or not body:
            return False
        body['payload']['data'] = {
            'levelIdx': 0,
            'manualSpeedLevel': new_speed,
            'levelType': 'wind'
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "change_fan_speed", self, r_bytes)
        if r is None:
            return False

        self.set_speed_level = new_speed
        self.mode = 'manual'
        return True

    async def mode_toggle(self, mode: str) -> bool:
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
        if mode == 'manual':
            if self.speed is None or self.speed == 0:
                return self.change_fan_speed(1)
            return self.change_fan_speed(self.speed)

        if mode == 'off':
            return self.turn_off()

        head, body = self.build_api_dict('setPurifierMode')
        if not head and not body:
            return False

        body['deviceId'] = self.cid
        body['payload']['data'] = {
            'workMode': mode
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "mode_toggle", self, r_bytes)
        if r is None:
            return False

        self.mode = mode
        return True

    def displayJSON(self) -> str:
        """Return air purifier status and properties in JSON output."""
        sup = super().displayJSON()
        sup_val = orjson.loads(sup)
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
        return orjson.dumps(
            sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode()


class VeSyncAir131(VeSyncBaseDevice):
    """Levoit Air Purifier Class."""

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initilize air purifier class."""
        super().__init__(details, manager)
        self.enabled = True
        self._config_dict = model_features(self.device_type)
        self._features = self._config_dict.get('features', [])
        if not isinstance(self._config_dict.get('modes'), list):
            logger.error(
                'Please set modes for %s in the configuration',
                self.device_type)
            raise KeyError(f'Modes not set in configuration for {self.device_name}')
        self.modes = self._config_dict['modes']
        if 'air_quality' in self._features:
            self.air_quality_feature = True
        else:
            self.air_quality_feature = False
        self.details: dict = {}

    async def get_details(self) -> None:
        """Build Air Purifier details dictionary."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        head = Helpers.req_headers(self.manager)

        r_bytes, _ = await self.manager.call_api(
            '/131airPurifier/v1/device/deviceDetail',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        self.device_status = r.get('deviceStatus', 'unknown')
        self.connection_status = r.get('connectionStatus', 'unknown')
        self.details['active_time'] = r.get('activeTime', 0)
        self.details['filter_life'] = r.get('filterLife', {})
        self.details['screen_status'] = r.get('screenStatus', 'unknown')
        self.mode = r.get('mode', self.mode)
        self.details['level'] = r.get('level', 0)
        self.details['air_quality'] = r.get('airQuality', 'unknown')

    async def get_config(self) -> None:
        """Get configuration info for air purifier."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/131airpurifier/v1/device/configurations',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_config", self, r_bytes)
        if r is None:
            return

        self.config = Helpers.build_config_dict(r)

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

    async def turn_on_display(self) -> bool:
        """Turn display on."""
        return await self.toggle_display('on')

    async def turn_off_display(self) -> bool:
        """Turn display off."""
        return await self.toggle_display('off')

    async def toggle_display(self, status: str) -> bool:
        """Toggle Display of VeSync LV-PUR131."""
        if status.lower() not in ['on', 'off']:
            logger.debug('Invalid display status - %s', status)
            return False
        head = Helpers.req_headers(self.manager)
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['status'] = status.lower()
        r_bytes, _ = await self.manager.call_api(
            '/131airPurifier/v1/device/updateScreen', 'put',
            json_object=body, headers=head
        )
        r = Helpers.process_api_response(logger, "toggle_display", self, r_bytes)
        if r is None:
            return False

        self.details['screen_status'] = status.lower()
        return True

    async def turn_on(self) -> bool:
        """Turn Air Purifier on."""
        if self.device_status != 'on':
            body = Helpers.req_body(self.manager, 'devicestatus')
            body['uuid'] = self.uuid
            body['status'] = 'on'
            head = Helpers.req_headers(self.manager)

            r_bytes, _ = await self.manager.call_api(
                '/131airPurifier/v1/device/deviceStatus', 'put',
                json_object=body, headers=head
            )
            r = Helpers.process_api_response(logger, "turn_on", self, r_bytes)
            if r is None:
                return False

            self.device_status = 'on'
            return True

        return False

    async def turn_off(self) -> bool:
        """Turn Air Purifier Off."""
        if self.device_status == 'on':
            body = Helpers.req_body(self.manager, 'devicestatus')
            body['uuid'] = self.uuid
            body['status'] = 'off'
            head = Helpers.req_headers(self.manager)

            r_bytes, _ = await self.manager.call_api(
                '/131airPurifier/v1/device/deviceStatus', 'put',
                json_object=body, headers=head
            )
            r = Helpers.process_api_response(logger, "turn_off", self, r_bytes)
            if r is None:
                return False

            self.device_status = 'off'
            return True
        return True

    async def auto_mode(self) -> bool:
        """Set mode to auto."""
        return await self.mode_toggle('auto')

    async def manual_mode(self) -> bool:
        """Set mode to manual."""
        return await self.mode_toggle('manual')

    async def sleep_mode(self) -> bool:
        """Set sleep mode to on."""
        return await self.mode_toggle('sleep')

    async def change_fan_speed(self, speed: int | None = None) -> bool:
        """Adjust Fan Speed for air purifier.

        Specifying 1,2,3 as argument or call without argument to cycle
        through speeds increasing by one.
        """
        if self.mode != 'manual':
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

        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        head = Helpers.req_headers(self.manager)
        if speed is not None:
            if speed == level:
                return True
            if speed in [1, 2, 3]:
                body['level'] = speed
            else:
                logger.debug('Invalid fan speed for %s',
                             self.device_name)
                return False
        elif (level + 1) > 3:
            body['level'] = 1
        else:
            body['level'] = int(level + 1)

        r_bytes, _ = await self.manager.call_api(
            '/131airPurifier/v1/device/updateSpeed', 'put',
            json_object=body, headers=head
        )
        r = Helpers.process_api_response(logger, "change_fan_speed", self, r_bytes)
        if r is None:
            return False

        self.details['level'] = body['level']
        return True

    async def mode_toggle(self, mode: str) -> bool:
        """Set mode to manual, auto or sleep."""
        head = Helpers.req_headers(self.manager)
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        if mode != self.mode and mode in ['sleep', 'auto', 'manual']:
            body['mode'] = mode
            if mode == 'manual':
                body['level'] = 1

            r_bytes, _ = await self.manager.call_api(
                '/131airPurifier/v1/device/updateMode', 'put',
                json_object=body, headers=head
            )
            r = Helpers.process_api_response(logger, "mode_toggle", self, r_bytes)
            if r is None:
                return False

            self.mode = mode
            return True

        logger.debug('Error setting %s mode - %s', self.device_name, mode)
        return False

    async def update(self) -> None:
        """Run function to get device details."""
        await self.get_details()

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp = [
            ('Active Time : ', self.active_time, ' minutes'),
            ('Fan Level: ', self.fan_level, ''),
            ('Air Quality: ', self.air_quality, ''),
            ('Mode: ', self.mode, ''),
            ('Screen Status: ', self.screen_status, ''),
            ('Filter Life: ', orjson.dumps(
                self.filter_life, option=orjson.OPT_NON_STR_KEYS), ' percent')
            ]
        for line in disp:
            print(f'{line[0]:.<30} {line[1]} {line[2]}')

    def displayJSON(self) -> str:
        """Return air purifier status and properties in JSON output."""
        sup = super().displayJSON()
        sup_val = orjson.loads(sup)
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
        return orjson.dumps(
            sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode()


class VeSyncTowerFan(VeSyncAirBaseV2):
    """Levoit Tower Fan Device Class."""

    def __init__(self, details: dict[str, list], manager: 'VeSync') -> None:
        """Initialize the VeSync Base API V2 Fan Class."""
        super().__init__(details, manager)

    async def get_details(self) -> None:
        """Build API V2 Fan details dictionary."""
        head, body = self.build_api_dict('getTowerFanStatus')
        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        inner_result = r.get('result', {}).get('result')

        if inner_result is not None:
            self.build_purifier_dict(inner_result)
        else:
            self.connection_status = 'offline'
            logger.debug('error in inner result dict from purifier')
        if inner_result.get('configuration', {}):
            self.build_config_dict(inner_result.get('configuration', {}))

    async def mode_toggle(self, mode: str) -> bool:
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

        if mode == 'off':
            return self.turn_off()

        head, body = self.build_api_dict('setTowerFanMode')
        if not head and not body:
            return False

        body['deviceId'] = self.cid
        body['payload']['data'] = {
            'workMode': mode
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "mode_toggle", self, r_bytes)
        if r is None:
            return False

        self.mode = mode
        return True

    async def normal_mode(self) -> bool:
        """Set mode to normal."""
        return await self.mode_toggle('normal')

    async def manual_mode(self) -> bool:
        """Adapter to set mode to normal."""
        return await self.normal_mode()

    async def advanced_sleep_mode(self) -> bool:
        """Set advanced sleep mode."""
        return await self.mode_toggle('advancedSleep')

    async def sleep_mode(self) -> bool:
        """Adapter to set advanced sleep mode."""
        return await self.advanced_sleep_mode()


class VeSyncHumid200300S(VeSyncBaseDevice):
    """200S/300S Humidifier Class."""

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initialize 200S/300S Humidifier class."""
        super().__init__(details, manager)
        self.enabled: str | bool = True
        self._config_dict = model_features(self.device_type)
        self.mist_levels = self._config_dict.get('mist_levels')
        self.mist_modes = self._config_dict.get('mist_modes')
        self._features = self._config_dict.get('features')
        if isinstance(self._features, list) and 'warm_mist' in self._features:
            self.warm_mist_levels = self._config_dict.get(
                'warm_mist_levels', [])
            self.warm_mist_feature = True
        else:
            self.warm_mist_feature = False
            self.warm_mist_levels = []
        if 'nightlight' in self._config_dict.get('features', []):
            self.night_light = True
        else:
            self.night_light = False
        self.details = {
            'humidity': 0,
            'mist_virtual_level': 0,
            'mist_level': 0,
            'mode': 'manual',
            'water_lacks': False,
            'humidity_high': False,
            'water_tank_lifted': False,
            'display': False,
            'automatic_stop_reach_target': False,
        }
        if self.night_light is True:
            self.details['night_light_brightness'] = 0
        self.config = {
            'auto_target_humidity': 0,
            'display': False,
            'automatic_stop': True
        }
        self._api_modes = ['getHumidifierStatus', 'setAutomaticStop',
                           'setSwitch', 'setNightLightBrightness',
                           'setVirtualLevel', 'setTargetHumidity',
                           'setHumidityMode', 'setDisplay', 'setLevel']

    def build_api_dict(self, method: str) -> tuple[dict, dict]:
        """Build humidifier api call header and body.

        Available methods are: 'getHumidifierStatus', 'setAutomaticStop',
        'setSwitch', 'setNightLightBrightness', 'setVirtualLevel',
        'setTargetHumidity', 'setHumidityMode'
        """
        if method not in self._api_modes:
            logger.debug('Invalid mode - %s', method)
            raise ValueError
        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': method,
            'source': 'APP'
        }
        return head, body

    def build_humid_dict(self, dev_dict: dict[str, str]) -> None:
        """Build humidifier status dictionary."""
        self.enabled = dev_dict.get('enabled', False)
        self.device_status = 'on' if self.enabled else 'off'
        self.mode = dev_dict.get('mode')
        self.details['humidity'] = dev_dict.get('humidity', 0)
        self.details['mist_virtual_level'] = dev_dict.get(
            'mist_virtual_level', 0)
        self.details['mist_level'] = dev_dict.get('mist_level', 0)
        self.details['mode'] = dev_dict.get('mode', 'manual')
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

    def build_config_dict(self, conf_dict: dict) -> None:
        """Build configuration dict for 300s humidifier."""
        self.config['auto_target_humidity'] = conf_dict.get(
            'auto_target_humidity', 0)
        self.config['display'] = conf_dict.get('display', False)
        self.config['automatic_stop'] = conf_dict.get('automatic_stop', True)

    async def get_details(self) -> None:
        """Build 200S/300S Humidifier details dictionary."""
        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': 'getHumidifierStatus',
            'source': 'APP',
            'data': {}
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return False

        outer_result = r.get('result', {})
        inner_result = outer_result.get('result')

        if outer_result.get("code") != 0:
            outer_error = ErrorCodes.get_error_info(outer_result.get('code'))
            if outer_error.device_online is False:
                self.connection_status = 'offline'
            LibraryLogger.log_device_code_error(
                logger,
                self.device_name,
                self.device_type,
                'get_details',
                outer_result.get('code'),
                outer_error.message
            )
            return False

        if not inner_result or not outer_result:
            LibraryLogger.log_api_response_parse_error(
                logger,
                self.device_name,
                self.device_type,
                "get_details",
                "Error in inner result dict from humidifier",
            )
            return False

        self.build_humid_dict(inner_result)
        if inner_result.get('configuration', {}):
            self.build_config_dict(inner_result.get('configuration', {}))
            return True

        LibraryLogger.log_api_response_parse_error(
            logger,
            self.device_name,
            self.device_type,
            "get_details",
            "Error in configuration dict from humidifier",
        )
        return False

    async def update(self) -> None:
        """Update 200S/300S Humidifier details."""
        await self.get_details()

    async def toggle_switch(self, toggle: bool) -> bool:
        """Toggle humidifier on/off."""
        if not isinstance(toggle, bool):
            logger.debug('Invalid toggle value for humidifier switch')
            return False

        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'data': {
                'enabled': toggle,
                'id': 0
            },
            'method': 'setSwitch',
            'source': 'APP'
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        if toggle:
            self.device_status = 'on'
        else:
            self.device_status = 'off'
        return True

    async def turn_on(self) -> bool:
        """Turn 200S/300S Humidifier on."""
        return await self.toggle_switch(True)

    async def turn_off(self) -> bool:
        """Turn 200S/300S Humidifier off."""
        return await self.toggle_switch(False)

    async def automatic_stop_on(self) -> bool:
        """Turn 200S/300S Humidifier automatic stop on."""
        return await self.set_automatic_stop(True)

    async def automatic_stop_off(self) -> bool:
        """Turn 200S/300S Humidifier automatic stop on."""
        return await self.set_automatic_stop(False)

    async def set_automatic_stop(self, mode: bool) -> bool:
        """Set 200S/300S Humidifier to automatic stop."""
        if mode not in (True, False):
            logger.debug(
                'Invalid mode passed to set_automatic_stop - %s', mode)
            return False

        head, body = self.build_api_dict('setAutomaticStop')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'enabled': mode
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_automatic_stop", self, r_bytes)
        # TODO: SET STATE
        return bool(r)

    async def set_display(self, mode: bool) -> bool:
        """Toggle display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        head, body = self.build_api_dict('setDisplay')

        body['payload']['data'] = {
            'state': mode
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_display", self, r_bytes)
        # TODO: SET STATE
        return bool(r)

    async def turn_on_display(self) -> bool:
        """Turn 200S/300S Humidifier on."""
        return await self.set_display(True)

    async def turn_off_display(self) -> bool:
        """Turn 200S/300S Humidifier off."""
        return await self.set_display(False)

    async def set_humidity(self, humidity: int) -> bool:
        """Set target 200S/300S Humidifier humidity."""
        if humidity < 30 or humidity > 80:
            logger.debug("Humidity value must be set between 30 and 80")
            return False
        head, body = self.build_api_dict('setTargetHumidity')

        if not head and not body:
            return False

        body['payload']['data'] = {
            'target_humidity': humidity
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_humidity", self, r_bytes)
        # TODO: SET STATE
        return bool(r)

    async def set_night_light_brightness(self, brightness: int) -> bool:
        """Set target 200S/300S Humidifier night light brightness."""
        if not self.night_light:
            logger.debug('%s is a %s does not have a nightlight',
                         self.device_name, self.device_type)
            return False
        if brightness < 0 or brightness > 100:
            logger.debug("Brightness value must be set between 0 and 100")
            return False
        head, body = self.build_api_dict('setNightLightBrightness')

        if not head and not body:
            return False

        body['payload']['data'] = {
            'night_light_brightness': brightness
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_night_light_brightness", self, r_bytes)

        # TODO: SET STATE
        return bool(r)

    async def set_humidity_mode(self, mode: str) -> bool:
        """Set humidifier mode - sleep or auto."""
        if isinstance(self.mist_modes, list) and mode.lower() not in self.mist_modes:
            logger.debug('Invalid humidity mode used - %s',
                         mode)
            logger.debug('Proper modes for this device are - %s',
                         str(self.mist_modes))
            return False
        head, body = self.build_api_dict('setHumidityMode')
        if not head and not body:
            return False
        body['payload']['data'] = {
            'mode': mode.lower()
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_humidity_mode", self, r_bytes)
        return bool(r)

    async def set_warm_level(self, warm_level: int) -> bool:
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
        head, body = self.build_api_dict('setLevel')

        if not head and not body:
            return False

        body['payload']['data'] = {
            'type': 'warm',
            'level': warm_level,
            'id': 0,
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_warm_level", self, r_bytes)
        return bool(r)

    async def set_auto_mode(self) -> bool:
        """Set auto mode for humidifiers."""
        if isinstance(self.mist_modes, list) and 'auto' in self.mist_modes:
            call_str = 'auto'
        elif isinstance(self.mist_modes, list) and 'humidity' in self.mist_modes:
            call_str = 'humidity'
        else:
            logger.debug('Trying auto mode, mode not set for this model, '
                         'please ensure %s model '
                         'is in configuration dictionary', self.device_type)
            call_str = 'auto'
        return await self.set_humidity_mode(call_str)

    async def set_manual_mode(self) -> bool:
        """Set humifier to manual mode with 1 mist level."""
        return await self.set_humidity_mode('manual')

    async def set_mist_level(self, level: int | str) -> bool:
        """Set humidifier mist level with int between 0 - 9."""
        try:
            level = int(level)
        except ValueError:
            level = str(level)
        if not self.mist_levels or \
                (isinstance(self.mist_levels, list) and level not in self.mist_levels):
            logger.debug('Humidifier mist level must be between 0 and 9')
            return False

        head, body = self.build_api_dict('setVirtualLevel')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'id': 0,
            'level': level,
            'type': 'mist'
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_mist_level", self, r_bytes)
        return bool(r)

    @property
    def humidity(self) -> int:
        """Get Humidity level."""
        return self.details['humidity']  # type: ignore[return-value]

    @property
    def mist_level(self) -> int:
        """Get current mist level."""
        return self.details['mist_virtual_level']  # type: ignore[return-value]

    @property
    def water_lacks(self) -> bool:
        """If tank is empty return true."""
        return self.details['water_lacks']  # type: ignore[return-value]

    @property
    def auto_humidity(self) -> int:
        """Auto target humidity."""
        return self.config['auto_target_humidity']

    @property
    def auto_enabled(self) -> bool:
        """Auto mode is enabled."""
        return self.details.get('mode') == 'auto' \
            or self.details.get('mode') == 'humidity'

    @property
    def warm_mist_enabled(self) -> bool:
        """Warm mist feature enabled."""
        if self.warm_mist_feature:
            return self.details['warm_mist_enabled']  # type: ignore[return-value]
        return False

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp = [
            ('Mode: ', self.details['mode'], ''),
            ('Humidity: ', self.details['humidity'], 'percent'),
            ('Mist Virtual Level: ', self.details['mist_virtual_level'], ''),
            ('Mist Level: ', self.details['mist_level'], ''),
            ('Water Lacks: ', self.details['water_lacks'], ''),
            ('Humidity High: ', self.details['humidity_high'], ''),
            ('Water Tank Lifted: ', self.details['water_tank_lifted'], ''),
            ('Display: ', self.details['display'], ''),
            ('Automatic Stop Reach Target: ',
                self.details['automatic_stop_reach_target'], ''),
            ('Auto Target Humidity: ',
                self.config['auto_target_humidity'], 'percent'),
            ('Automatic Stop: ', self.config['automatic_stop'], ''),
        ]
        if self.night_light:
            disp.append(('Night Light Brightness: ',
                         self.details.get('night_light_brightness', ''), 'percent'))
        if self.warm_mist_feature:
            disp.append(('Warm mist enabled: ',
                         self.details.get('warm_mist_enabled', ''), ''))
            disp.append(('Warm mist level: ',
                         self.details.get('warm_mist_level', ''), ''))
        for line in disp:
            print(f'{line[0]:.<30} {line[1]} {line[2]}')

    def displayJSON(self) -> str:
        """Return air purifier status and properties in JSON output."""
        sup = super().displayJSON()
        sup_val = orjson.loads(sup)
        sup_val.update(
            {
                'Mode': self.details['mode'],
                'Humidity': str(self.details['humidity']),
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
        return orjson.dumps(
            sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode()


class VeSyncHumid200S(VeSyncHumid200300S):
    """Levoit Classic 200S Specific class."""

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initialize levoit 200S device class."""
        super().__init__(details, manager)
        self._api_modes = ['getHumidifierStatus', 'setAutomaticStop',
                           'setSwitch', 'setVirtualLevel', 'setTargetHumidity',
                           'setHumidityMode', 'setIndicatorLightSwitch']

    async def set_display(self, mode: bool) -> bool:
        """Toggle display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        head, body = self.build_api_dict('setIndicatorLightSwitch')

        body['payload']['data'] = {
            'enabled': mode,
            'id': 0
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_display", self, r_bytes)
        return bool(r)


class VeSyncSuperior6000S(VeSyncBaseDevice):
    """Superior 6000S Humidifier."""

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initialize Superior 6000S Humidifier class."""
        super().__init__(details, manager)
        self._config_dict = model_features(self.device_type)
        self.mist_levels = self._config_dict.get('mist_levels')
        self.mist_modes = self._config_dict.get('mist_modes')
        self.connection_status = details.get('deviceProp', {}).get(
            'connectionStatus', None)
        self.details: dict = {}
        self.config = {}
        self._api_modes = [
            'getHumidifierStatus',
            'setSwitch',
            'setVirtualLevel',
            'setTargetHumidity',
            'setHumidityMode',
            'setDisplay',
            'setDryingMode',
        ]

    def build_api_dict(self, method: str) -> tuple[dict, dict]:
        """Build humidifier api call header and body.

        Available methods are: 'getHumidifierStatus', 'setSwitch',
        'setVirtualLevel', 'setTargetHumidity', 'setHumidityMode',
        'setDisplay', 'setDryingMode'
        """
        if method not in self._api_modes:
            logger.debug('Invalid mode - %s', method)
            raise ValueError
        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': method,
            'source': 'APP'
        }
        return head, body

    def build_humid_dict(self, dev_dict: dict[str, str]) -> None:
        """Build humidifier status dictionary."""
        self.device_status = 'off' if dev_dict.get('powerSwitch', 0) == 0 else 'on'
        self.mode = 'auto' if dev_dict.get('workMode', '') == 'autoPro' \
            else dev_dict.get('workMode', '')
        self.details['humidity'] = dev_dict.get('humidity', 0)
        self.details['target_humidity'] = dev_dict.get('targetHumidity')
        self.details['mist_virtual_level'] = dev_dict.get(
            'virtualLevel', 0)
        self.details['mist_level'] = dev_dict.get('mistLevel', 0)
        self.details['water_lacks'] = dev_dict.get('waterLacksState', False)
        self.details['water_tank_lifted'] = dev_dict.get(
            'waterTankLifted', False)
        self.details['filter_life_percentage'] = dev_dict.get('filterLifePercent', 0)
        self.details['temperature'] = dev_dict.get('temperature', 0)
        self.details['display'] = dev_dict.get('screenSwitch')
        self.details['drying_mode'] = dev_dict.get('dryingMode', {})

    def build_config_dict(self, _: dict) -> None:
        """Build configuration dict for humidifier."""

    async def get_details(self) -> None:
        """Build Humidifier details dictionary."""
        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': 'getHumidifierStatus',
            'source': 'APP',
            'data': {}
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        outer_result = r.get('result', {})
        inner_result = outer_result.get('result')

        outer_code = outer_result.get('code')
        if outer_code != 0:
            error_info = ErrorCodes.get_error_info(outer_code)
            if error_info.device_online is False:
                self.connection_status = 'offline'
            LibraryLogger.log_device_code_error(
                logger,
                self.device_name,
                self.device_type,
                'get_details',
                outer_code,
                error_info.message
            )
            return

        if inner_result is not None:
            self.build_humid_dict(inner_result)
            self.build_config_dict(inner_result.get('configuration', {}))
            return
        LibraryLogger.log_api_response_parse_error(
            logger,
            self.device_name,
            self.device_type,
            "get_details",
            "Error in inner result dict from humidifier",
        )
        return

    async def update(self) -> None:
        """Update humidifier details."""
        await self.get_details()

    async def toggle_switch(self, toggle: bool) -> bool:
        """Toggle humidifier on/off."""
        if not isinstance(toggle, bool):
            logger.debug('Invalid toggle value for humidifier switch')
            return False

        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'data': {
                'powerSwitch': int(toggle),
                'switchIdx': 0
            },
            'method': 'setSwitch',
            'source': 'APP'
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        if toggle:
            self.device_status = 'on'
        else:
            self.device_status = 'off'

        return True

    async def turn_on(self) -> bool:
        """Turn humidifier on."""
        return await self.toggle_switch(True)

    async def turn_off(self) -> bool:
        """Turn humidifier off."""
        return await self.toggle_switch(False)

    async def set_drying_mode_enabled(self, mode: bool) -> bool:
        """enable/disable drying filters after turning off."""
        if mode not in (True, False):
            logger.debug(
                'Invalid toggle passed to set_drying_mode_enabled - %s', mode
            )
            return False
        head, body = self.build_api_dict('setDryingMode')
        body['payload']['data'] = {
            'autoDryingSwitch': int(mode)
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_drying_mode_enabled", self, r_bytes)
        return bool(r)

    async def set_display_enabled(self, mode: bool) -> bool:
        """Toggle display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        head, body = self.build_api_dict('setDisplay')

        body['payload']['data'] = {
            'screenSwitch': int(mode)
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_display", self, r_bytes)
        return bool(r)

    async def turn_on_display(self) -> bool:
        """Turn display on."""
        return self.set_display_enabled(True)

    async def turn_off_display(self) -> bool:
        """Turn display off."""
        return self.set_display_enabled(False)

    async def set_humidity(self, humidity: int) -> bool:
        """Set target humidity for humidity mode."""
        if humidity < 30 or humidity > 80:
            logger.debug("Humidity value must be set between 30 and 80")
            return False
        head, body = self.build_api_dict('setTargetHumidity')

        if not head and not body:
            return False

        body['payload']['data'] = {
            'targetHumidity': humidity
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_humidity", self, r_bytes)
        return bool(r)

    async def set_humidity_mode(self, mode: str) -> bool:
        """Set humidifier mode."""
        if not self.mist_modes or \
                (isinstance(self.mist_modes, list) and mode not in self.mist_modes):
            logger.debug('Invalid humidity mode used - %s',
                         mode)
            logger.debug('Proper modes for this device are - %s',
                         str(self.mist_modes))
            return False
        head, body = self.build_api_dict('setHumidityMode')
        if not head and not body:
            return False
        body['payload']['data'] = {
            'workMode': 'autoPro' if mode == 'auto' else mode
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_humidity_mode", self, r_bytes)
        return bool(r)

    async def set_auto_mode(self) -> bool:
        """Set humidity mode to auto."""
        return await self.set_humidity_mode('auto')

    async def set_manual_mode(self) -> bool:
        """Set humidity mode to manual."""
        return await self.set_humidity_mode('manual')

    async def automatic_stop_on(self) -> bool:
        """Set humidity mode to auto."""
        return await self.set_humidity_mode('auto')

    async def automatic_stop_off(self) -> bool:
        """Set humidity mode to manual."""
        return await self.set_humidity_mode('manual')

    async def set_mist_level(self, level: int) -> bool:
        """Set humidifier mist level with int between 0 - 9."""
        if not self.mist_levels or \
                (isinstance(self.mist_levels, list) and level not in self.mist_levels):
            logger.debug('Humidifier mist level must be between 0 and 9')
            return False

        head, body = self.build_api_dict('setVirtualLevel')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'levelIdx': 0,
            'virtualLevel': level,
            'levelType': 'mist'
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_mist_level", self, r_bytes)
        return bool(r)

    @property
    def humidity_level(self) -> int:
        """Get Humidity level."""
        return self.details['humidity']

    # Duplicate for compatibility
    @property
    def humidity(self) -> int:
        """Get Humidity level."""
        return self.details['humidity']

    @property
    def mist_level(self) -> int:
        """Get current mist level."""
        return self.details['mist_level']

    @property
    def mist_virtual_level(self) -> int:
        """Get current mist virtual level."""
        return self.details['mist_virtual_level']

    @property
    def water_lacks(self) -> bool | None:
        """If tank is empty return true."""
        if 'water_lacks' in self.details:
            return bool(self.details['water_lacks'])
        return None

    @property
    def drying_mode_state(self) -> str | None:
        """True if humidifier is currently drying the filters, false otherwise."""
        state = self.details.get('drying_mode', {}).get('dryingState')
        if state == 1:
            return 'on'
        if state == 2:
            return 'off'
        return None

    @property
    def drying_mode_seconds_remaining(self) -> int:
        """If drying_mode_state is on, how many seconds are remaining."""
        return self.details.get('drying_mode', {}).get('dryingRemain')

    @property
    def drying_mode_enabled(self) -> bool | None:
        """Checks if drying mode is enabled.

        Returns:
            bool: True if enabled, false if disabled

        """
        enabled = self.details.get('drying_mode', {}).get('autoDryingSwitch')
        return None if enabled is None else bool(enabled)

    @property
    def drying_mode_level(self) -> str | None:
        """Drying mode level 1 = low, 2 = high."""
        level = self.details.get('drying_mode', {}).get('dryingLevel')
        if level == 1:
            return 'low'
        if level == 2:
            return 'high'
        return None

    @property
    def temperature(self) -> int:
        """Current temperature."""
        return self.details['temperature']

    @property
    def auto_humidity(self) -> int:
        """Auto target humidity."""
        return self.config['target_humidity']

    @property
    def target_humidity(self) -> int:
        """The target humidity when in humidity mode."""
        return self.details['target_humidity']

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp = [
            ('Temperature', self.temperature, ''),
            ('Humidity: ', self.humidity_level, 'percent'),
            ('Target Humidity', self.target_humidity, 'percent'),
            ('Mode: ', self.mode, ''),
            ('Mist Virtual Level: ', self.details['mist_virtual_level'], ''),
            ('Mist Level: ', self.details['mist_level'], ''),
            ('Water Lacks: ', self.water_lacks, ''),
            ('Water Tank Lifted: ', bool(self.details['water_tank_lifted']), ''),
            ('Display On: ', bool(self.details['display']), ''),
            ('Filter Life', self.details['filter_life_percentage'], 'percent'),
            ('Drying Mode Enabled', self.drying_mode_enabled, ''),
            ('Drying Mode State', self.drying_mode_state, ''),
            ('Drying Mode Level', self.drying_mode_level, ''),
            ('Drying Mode Time Remaining', self.drying_mode_seconds_remaining, 'seconds'),
        ]
        for line in disp:
            print(f'{line[0]:.<30} {line[1]} {line[2]}')

    def displayJSON(self) -> str:
        """Return air purifier status and properties in JSON output."""
        sup = super().displayJSON()
        sup_val = orjson.loads(sup)
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
        return orjson.dumps(
            sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode()


class VeSyncHumid1000S(VeSyncHumid200300S):
    """Levoit OasisMist 1000S Specific class."""

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initialize levoit 1000S device class."""
        super().__init__(details, manager)
        self.connection_status = details.get('deviceProp', {}).get(
            'connectionStatus', None)

        self._api_modes = ['getHumidifierStatus', 'setAutoStopSwitch',
                           'setSwitch', 'setVirtualLevel', 'setTargetHumidity',
                           'setHumidityMode', 'setDisplay']

    def build_humid_dict(self, dev_dict: dict[str, str]) -> None:
        """Build humidifier status dictionary."""
        super().build_humid_dict(dev_dict)
        self.device_status = 'off' if dev_dict.get('powerSwitch', 0) == 0 else 'on'
        self.details['mist_virtual_level'] = dev_dict.get(
            'virtualLevel', 0)
        self.details['mist_level'] = dev_dict.get('mistLevel', 0)
        self.details['mode'] = dev_dict.get('workMode', 'manual')
        self.details['water_lacks'] = bool(dev_dict.get('waterLacksState', 0))
        self.details['humidity_high'] = bool(int(dev_dict.get('targetHumidity', 0)) <
                                             int(dev_dict.get('humidity', 0)))
        self.details['water_tank_lifted'] = bool(dev_dict.get(
            'waterTankLifted', 0))
        self.details['automatic_stop_reach_target'] = bool(dev_dict.get(
            'autoStopState', 1
        ))
        self.details['display'] = bool(dev_dict['screenState'])

    def build_config_dict(self, conf_dict: dict) -> None:
        """Build configuration dict for humidifier."""
        self.config['auto_target_humidity'] = conf_dict.get(
            'targetHumidity', 0)
        self.config['display'] = bool(conf_dict.get('screenSwitch', 0))
        self.config['automatic_stop'] = bool(conf_dict.get('autoStopSwitch', 1))

    async def get_details(self) -> None:
        """Build Humidifier details dictionary."""
        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': 'getHumidifierStatus',
            'source': 'APP',
            'data': {}
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        outer_result = r.get('result', {})
        inner_result = outer_result.get('result', {})

        if outer_result is None or inner_result is None:
            LibraryLogger.log_api_response_parse_error(
                logger,
                self.device_name,
                self.device_type,
                "get_details",
                "Error in inner result dict from humidifier",
            )
            return
        if outer_result.get('code') != 0:
            error_info = ErrorCodes.get_error_info(outer_result.get('code'))
            if error_info.device_online is False:
                self.connection_status = 'offline'
            LibraryLogger.log_device_code_error(
                logger,
                self.device_name,
                self.device_type,
                'get_details',
                outer_result.get('code'),
                error_info.message
            )
            return

        self.connection_status = 'online'
        self.build_humid_dict(inner_result)
        self.build_config_dict(inner_result.get('configuration', {}))
        return

    async def set_display(self, mode: bool) -> bool:
        """Toggle display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        head, body = self.build_api_dict('setDisplay')

        body['payload']['data'] = {
            'screenSwitch': int(mode)
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_display", self, r_bytes)
        return bool(r)

    async def set_humidity_mode(self, mode: str) -> bool:
        """Set humidifier mode - sleep, auto or manual."""
        if not self.mist_modes or \
                (isinstance(self.mist_modes, list) and
                 mode.lower() not in self.mist_modes):
            logger.debug('Invalid humidity mode used - %s',
                         mode)
            logger.debug('Proper modes for this device are - %s',
                         str(self.mist_modes))
            return False
        head, body = self.build_api_dict('setHumidityMode')
        if not head and not body:
            return False
        body['payload']['data'] = {
            'workMode': mode.lower()
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_humidity_mode", self, r_bytes)
        return bool(r)

    async def set_sleep_mode(self) -> bool:
        """Set humifier to manual mode with 1 mist level."""
        return await self.set_humidity_mode('sleep')

    async def set_mist_level(self, level: int | str) -> bool:
        """Set humidifier mist level with int."""
        if not self.mist_levels or \
                (isinstance(self.mist_levels, list) and level not in self.mist_levels):
            logger.debug('Humidifier mist level out of range')
            return False

        head, body = self.build_api_dict('setVirtualLevel')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'levelIdx': 0,
            'virtualLevel': level,
            'levelType': 'mist'
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_mist_level", self, r_bytes)
        return bool(r)

    async def toggle_switch(self, toggle: bool) -> bool:
        """Toggle humidifier on/off."""
        if not isinstance(toggle, bool):
            logger.debug('Invalid toggle value for humidifier switch')
            return False

        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'data': {
                'powerSwitch': int(toggle),
                'switchIdx': 0
            },
            'method': 'setSwitch',
            'source': 'APP'
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        if toggle:
            self.device_status = 'on'
        else:
            self.device_status = 'off'
        return True

    async def set_humidity(self, humidity: int) -> bool:
        """Set target Humidifier humidity."""
        if humidity < 30 or humidity > 80:
            logger.debug("Humidity value must be set between 30 and 80")
            return False
        head, body = self.build_api_dict('setTargetHumidity')

        if not head and not body:
            return False

        body['payload']['data'] = {
            'targetHumidity': humidity
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_humidity", self, r_bytes)
        return bool(r)

    async def set_automatic_stop(self, mode: bool) -> bool:
        """Set  Humidifier to automatic stop."""
        if mode not in (True, False):
            logger.debug(
                'Invalid mode passed to set_automatic_stop - %s', mode)
            return False

        head, body = self.build_api_dict('setAutoStopSwitch')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'autoStopSwitch': int(mode)
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_automatic_stop", self, r_bytes)
        return bool(r)
