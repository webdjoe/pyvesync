"""VeSync API for controling fans and purifiers."""

import json
import logging
from typing import Dict, Tuple, Union, Optional
from pyvesync.vesyncbasedevice import VeSyncBaseDevice
from pyvesync.helpers import Helpers


humid_features: dict = {
    'Classic300S': {
        'module': 'VeSyncHumid200300S',
        'models': ['Classic300S', 'LUH-A601S-WUSB'],
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
                   'LUH-A602S-WJP'],
        'features': ['warm_mist', 'nightlight'],
        'mist_modes': ['humidity', 'sleep', 'manual'],
        'mist_levels': list(range(1, 10)),
        'warm_mist_levels': [0, 1, 2, 3]
    },
    'OASISMIST': {
            'module': 'VeSyncHumid200300S',
            'models': ['LUH-O451S-WUS'],
            'features': ['warm_mist'],
            'mist_modes': ['humidity', 'sleep', 'manual'],
            'mist_levels': list(range(1, 10)),
            'warm_mist_levels': list(range(4))
        },
}


air_features: dict = {
    'Core200S': {
        'module': 'VeSyncAirBypass',
        'models': ['Core200S', 'LAP-C201S-AUSR', 'LAP-C202S-WUSR'],
        'modes': ['sleep', 'off', 'manual'],
        'features': [],
        'levels': list(range(1, 4))
    },
    'Core300S': {
        'module': 'VeSyncAirBypass',
        'models': ['Core300S', 'LAP-C301S-WJP', 'LAP-C302S-WUSB'],
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
        'features': ['air_quality']
    },
}


logger = logging.getLogger(__name__)


def model_dict() -> dict:
    """Build purifier and humidifier model dictionary."""
    model_modules = {}
    for dev_dict in {**air_features, **humid_features}.values():
        for model in dev_dict['models']:
            model_modules[model] = dev_dict['module']
    return model_modules


def model_features(dev_type: str) -> dict:
    """Get features from device type."""
    for dev_dict in {**air_features, **humid_features}.values():
        if dev_type in dev_dict['models']:
            return dev_dict
    raise ValueError('Device not configured')


fan_classes: set = {v['module']
                    for k, v in {**air_features, **humid_features}.items()}

fan_modules: dict = model_dict()

__all__: list = list(fan_classes) + ['fan_modules']


class VeSyncAirBypass(VeSyncBaseDevice):
    """Base class for Levoit Purifier Bypass API Calls."""

    def __init__(self, details: Dict[str, list], manager):
        """Initialize air devices."""
        super().__init__(details, manager)
        self.enabled = True
        self.config_dict = model_features(self.device_type)
        self.features = self.config_dict.get('features', [])
        if not isinstance(self.config_dict.get('modes'), list):
            logger.error(
                'Please set modes for %s in the configuration',
                self.device_type)
            raise KeyError(f'Modes not set in configuration for {self.device_name}')
        self.modes = self.config_dict['modes']
        if 'air_quality' in self.features:
            self.air_quality_feature = True
        else:
            self.air_quality_feature = False
        self.details: Dict[str, Union[str, int, float, bool]] = {
            'filter_life': 0,
            'mode': 'manual',
            'level': 0,
            'display': False,
            'child_lock': False,
            'night_light': 'off',
        }
        if self.air_quality_feature is True:
            self.details['air_quality'] = 0
        self.config: Dict[str, Union[str, int, float, bool]] = {
            'display': False,
            'display_forever': False
        }

    def build_api_dict(self, method: str) -> Tuple[Dict, Dict]:
        """Build device api body dictionary.

        standard modes are: ['getPurifierStatus', 'setSwitch',
        'setNightLight',
        'setLevel', 'setPurifierMode', 'setDisplay',
        'setChildLock']
        """
        modes = ['getPurifierStatus', 'setSwitch', 'setNightLight',
                 'setLevel', 'setPurifierMode', 'setDisplay',
                 'setChildLock', 'setIndicatorLight']
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
        """Build Bypass purifier status dictionary."""
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

    def build_config_dict(self, conf_dict: Dict[str, str]) -> None:
        """Build configuration dict for Bypass purifier."""
        self.config['display'] = conf_dict.get('display', False)
        self.config['display_forever'] = conf_dict.get('display_forever',
                                                       False)

    def get_details(self) -> None:
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

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        if not isinstance(r, dict):
            logger.debug('Error in purifier response')
            return
        if not isinstance(r.get('result'), dict):
            logger.debug('Error in purifier response')
            return
        outer_result = r.get('result', {})
        inner_result = None

        if outer_result:
            inner_result = r.get('result', {}).get('result')
        if inner_result is not None and Helpers.code_check(r):
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

    def change_fan_speed(self,
                         speed=None) -> bool:
        """Change fan speed based on levels in configuration dict."""
        speeds: list = self.config_dict.get('levels', [])
        current_speed = self.speed

        if speed is not None:
            if speed not in speeds:
                logger.debug("%s is invalid speed - valid speeds are %s",
                             speed, str(speeds))
                return False
            new_speed = speed
        else:
            if current_speed == speeds[-1]:
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

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
            self.speed = new_speed
            return True
        logger.debug('Error changing %s speed', self.device_name)
        return False

    def child_lock_on(self) -> bool:
        """Turn Bypass child lock on."""
        return self.set_child_lock(True)

    def child_lock_off(self) -> bool:
        """Turn Bypass child lock off."""
        return self.set_child_lock(False)

    def set_child_lock(self, mode: bool) -> bool:
        """Set Bypass child lock."""
        if mode not in (True, False):
            logger.debug('Invalid mode passed to set_child_lock - %s', mode)
            return False

        head, body = self.build_api_dict('setChildLock')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'child_lock': mode
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
            self.details['child_lock'] = mode
            return True
        if isinstance(r, dict):
            logger.debug('Error toggling child lock')
        else:
            logger.debug('Error in api return json for %s', self.device_name)
        return False

    def mode_toggle(self, mode: str) -> bool:
        """Set purifier mode - sleep or manual."""
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

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if Helpers.code_check(r):
            if mode.lower() == 'manual':
                self.speed = 1
                self.mode = 'manual'
            else:
                self.mode = mode
                self.speed = 0
            return True
        logger.debug('Error setting purifier mode')
        return False

    def manual_mode(self) -> bool:
        """Set mode to manual."""
        if 'manual' not in self.modes:
            logger.debug('%s does not have manual mode', self.device_name)
            return False
        return self.mode_toggle('manual')

    def sleep_mode(self) -> bool:
        """Set sleep mode to on."""
        if 'sleep' not in self.modes:
            logger.debug('%s does not have sleep mode', self.device_name)
            return False
        return self.mode_toggle('sleep')

    def auto_mode(self) -> bool:
        """Set mode to auto."""
        if 'auto' not in self.modes:
            logger.debug('%s does not have auto mode', self.device_name)
            return False
        return self.mode_toggle('auto')

    def toggle_switch(self, toggle: bool) -> bool:
        """Toggle purifier on/off."""
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

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
            if toggle:
                self.device_status = 'on'
            else:
                self.device_status = 'off'
            return True
        logger.debug("Error toggling purifier - %s",
                     self.device_name)
        return False

    def turn_on(self) -> bool:
        """Turn bypass Purifier on."""
        return self.toggle_switch(True)

    def turn_off(self):
        """Turn Bypass Purifier off."""
        return self.toggle_switch(False)

    def set_display(self, mode: bool) -> bool:
        """Toggle display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        head, body = self.build_api_dict('setDisplay')

        body['payload']['data'] = {
            'state': mode
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
            return True
        logger.debug("Error toggling purifier display - %s",
                     self.device_name)
        return False

    def turn_on_display(self) -> bool:
        """Turn Display on."""
        return self.set_display(True)

    def turn_off_display(self):
        """Turn Display off."""
        return self.set_display(False)

    def set_night_light(self, mode: str) -> bool:
        """Set night list  - on, off or dim."""
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

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
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
        """Get current fan level (1-3)."""
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
        """Get display state."""
        return bool(self.details['display'])

    @property
    def screen_status(self) -> bool:
        """Get display status."""
        return bool(self.details['display'])

    @property
    def child_lock(self) -> bool:
        """Get child lock state."""
        return bool(self.details['child_lock'])

    @property
    def night_light(self) -> str:
        """Get night light state (on/dim/off)."""
        return str(self.details['night_light'])

    def display(self) -> None:
        """Return formatted device info to stdout."""
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
        """Return air purifier status and properties in JSON output."""
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


class VeSyncAir131(VeSyncBaseDevice):
    """Levoit Air Purifier Class."""

    def __init__(self, details, manager):
        """Initilize air purifier class."""
        super().__init__(details, manager)

        self.details: Dict = {}

    def get_details(self) -> None:
        """Build Air Purifier details dictionary."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        head = Helpers.req_headers(self.manager)

        r, _ = Helpers.call_api(
            '/131airPurifier/v1/device/deviceDetail',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
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
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = Helpers.call_api(
            '/131airpurifier/v1/device/configurations',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
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

    def turn_on(self) -> bool:
        """Turn Air Purifier on."""
        if self.device_status != 'on':
            body = Helpers.req_body(self.manager, 'devicestatus')
            body['uuid'] = self.uuid
            body['status'] = 'on'
            head = Helpers.req_headers(self.manager)

            r, _ = Helpers.call_api(
                '/131airPurifier/v1/device/deviceStatus', 'put',
                json_object=body, headers=head
            )

            if r is not None and Helpers.code_check(r):
                self.device_status = 'on'
                return True
            logger.debug('Error turning %s on', self.device_name)
            return False
        return False

    def turn_off(self) -> bool:
        """Turn Air Purifier Off."""
        if self.device_status == 'on':
            body = Helpers.req_body(self.manager, 'devicestatus')
            body['uuid'] = self.uuid
            body['status'] = 'off'
            head = Helpers.req_headers(self.manager)

            r, _ = Helpers.call_api(
                '/131airPurifier/v1/device/deviceStatus', 'put',
                json_object=body, headers=head
            )

            if r is not None and Helpers.code_check(r):
                self.device_status = 'off'
                return True
            logger.debug('Error turning %s off', self.device_name)
            return False
        return True

    def auto_mode(self) -> bool:
        """Set mode to auto."""
        return self.mode_toggle('auto')

    def manual_mode(self) -> bool:
        """Set mode to manual."""
        return self.mode_toggle('manual')

    def sleep_mode(self) -> bool:
        """Set sleep mode to on."""
        return self.mode_toggle('sleep')

    def change_fan_speed(self, speed: Optional[int] = None) -> bool:
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
        else:
            if (level + 1) > 3:
                body['level'] = 1
            else:
                body['level'] = int(level + 1)

        r, _ = Helpers.call_api(
            '/131airPurifier/v1/device/updateSpeed', 'put',
            json_object=body, headers=head
        )

        if r is not None and Helpers.code_check(r):
            self.details['level'] = body['level']
            return True
        logger.debug('Error changing %s speed', self.device_name)
        return False

    def mode_toggle(self, mode: str) -> bool:
        """Set mode to manual, auto or sleep."""
        head = Helpers.req_headers(self.manager)
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        if mode != self.mode and mode in ['sleep', 'auto', 'manual']:
            body['mode'] = mode
            if mode == 'manual':
                body['level'] = 1

            r, _ = Helpers.call_api(
                '/131airPurifier/v1/device/updateMode', 'put',
                json_object=body, headers=head
            )

            if r is not None and Helpers.code_check(r):
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
            ('Active Time : ', self.active_time, ' minutes'),
            ('Fan Level: ', self.fan_level, ''),
            ('Air Quality: ', self.air_quality, ''),
            ('Mode: ', self.mode, ''),
            ('Screen Status: ', self.screen_status, ''),
            ('Filter Life: ', json.dumps(self.filter_life), ' percent')
            ]
        for line in disp:
            print(f'{line[0]:.<30} {line[1]} {line[2]}')

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


class VeSyncHumid200300S(VeSyncBaseDevice):
    """200S/300S Humidifier Class."""

    def __init__(self, details, manager):
        """Initialize 200S/300S Humidifier class."""
        super().__init__(details, manager)
        self.enabled = True
        self.config_dict = model_features(self.device_type)
        self.mist_levels = self.config_dict.get('mist_levels')
        self.mist_modes = self.config_dict.get('mist_modes')
        self.features = self.config_dict.get('features')
        if 'warm_mist' in self.features:
            self.warm_mist_levels = self.config_dict.get(
                'warm_mist_levels', [])
            self.warm_mist_feature = True
        else:
            self.warm_mist_feature = False
            self.warm_mist_levels = []
        if 'nightlight' in self.config_dict.get('features', []):
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

    def build_api_dict(self, method: str) -> Tuple[Dict, Dict]:
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

    def build_humid_dict(self, dev_dict: Dict[str, str]) -> None:
        """Build humidifier status dictionary."""
        self.enabled = dev_dict.get('enabled')
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

    def build_config_dict(self, conf_dict):
        """Build configuration dict for 300s humidifier."""
        self.config['auto_target_humidity'] = conf_dict.get(
            'auto_target_humidity', 0)
        self.config['display'] = conf_dict.get('display', False)
        self.config['automatic_stop'] = conf_dict.get('automatic_stop', True)

    def get_details(self) -> None:
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

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        if r is None or not isinstance(r, dict):
            logger.debug("Error getting status of %s ", self.device_name)
            return
        outer_result = r.get('result', {})
        inner_result = None

        if outer_result is not None:
            inner_result = r.get('result', {}).get('result')
        if inner_result is not None and Helpers.code_check(r):
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
        """Update 200S/300S Humidifier details."""
        self.get_details()

    def toggle_switch(self, toggle: bool) -> bool:
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

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
            if toggle:
                self.device_status = 'on'
            else:
                self.device_status = 'off'

            return True
        logger.debug("Error toggling 300S humidifier - %s", self.device_name)
        return False

    def turn_on(self) -> bool:
        """Turn 200S/300S Humidifier on."""
        return self.toggle_switch(True)

    def turn_off(self):
        """Turn 200S/300S Humidifier off."""
        return self.toggle_switch(False)

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

        head, body = self.build_api_dict('setAutomaticStop')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'enabled': mode
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
            return True
        if isinstance(r, dict):
            logger.debug('Error toggling automatic stop')
        else:
            logger.debug('Error in api return json for %s', self.device_name)
        return False

    def set_display(self, mode: bool) -> bool:
        """Toggle display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        head, body = self.build_api_dict('setDisplay')

        body['payload']['data'] = {
            'state': mode
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
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
        head, body = self.build_api_dict('setTargetHumidity')

        if not head and not body:
            return False

        body['payload']['data'] = {
            'target_humidity': humidity
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
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
        head, body = self.build_api_dict('setNightLightBrightness')

        if not head and not body:
            return False

        body['payload']['data'] = {
            'night_light_brightness': brightness
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
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
        head, body = self.build_api_dict('setHumidityMode')
        if not head and not body:
            return False
        body['payload']['data'] = {
            'mode': mode.lower()
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
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
        head, body = self.build_api_dict('setLevel')

        if not head and not body:
            return False

        body['payload']['data'] = {
            'type': 'warm',
            'level': warm_level,
            'id': 0,
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
            return True
        logger.debug('Error setting warm')
        return False

    def set_auto_mode(self):
        """Set auto mode for humidifiers."""
        if 'auto' in self.mist_modes:
            call_str = 'auto'
        elif 'humidity' in self.mist_modes:
            call_str = 'humidity'
        else:
            logger.debug('Trying auto mode, mode not set for this model, '
                         'please ensure %s model '
                         'is in configuration dictionary', self.device_type)
            call_str = 'auto'
        set_auto = self.set_humidity_mode(call_str)
        return set_auto

    def set_manual_mode(self):
        """Set humifier to manual mode with 1 mist level."""
        return self.set_humidity_mode('manual')

    def set_mist_level(self, level) -> bool:
        """Set humidifier mist level with int between 0 - 9."""
        try:
            level = int(level)
        except ValueError:
            level = str(level)
        if level not in self.mist_levels:
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

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
            return True
        logger.debug('Error setting mist level')
        return False

    @property
    def humidity(self):
        """Get Humidity level."""
        return self.details['humidity']

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
        if self.details.get('mode') == 'auto' \
                or self.details.get('mode') == 'humidity':
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
        sup_val = json.loads(sup)
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
        return json.dumps(sup_val, indent=4)


class VeSyncHumid200S(VeSyncHumid200300S):
    """Levoit Classic 200S Specific class."""

    def __init__(self, details, manager):
        """Initialize levoit 200S device class."""
        super().__init__(details, manager)
        self._api_modes = ['getHumidifierStatus', 'setAutomaticStop',
                           'setSwitch', 'setVirtualLevel', 'setTargetHumidity',
                           'setHumidityMode', 'setIndicatorLightSwitch']

    def set_display(self, mode: bool) -> bool:
        """Toggle display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        head, body = self.build_api_dict('setIndicatorLightSwitch')

        body['payload']['data'] = {
            'enabled': mode,
            'id': 0
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        if r is not None and Helpers.code_check(r):
            return True
        logger.debug("Error toggling 200S display - %s", self.device_name)
        return False
