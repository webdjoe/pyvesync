"""VeSync API for controling fans and purifiers."""

import json
import logging

from typing import Dict, Tuple, Union
from pyvesync.vesyncbasedevice import VeSyncBaseDevice
from pyvesync.helpers import Helpers


logger = logging.getLogger(__name__)


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
            json=body,
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
            json=body,
        )

        if Helpers.code_check(r):
            self.config = Helpers.build_config_dict(r)
        else:
            logger.warning('Unable to get config info for %s',
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
                json=body, headers=head
            )

            if r is not None and Helpers.code_check(r):
                self.device_status = 'on'
                return True
            logger.warning('Error turning %s on', self.device_name)
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
                json=body, headers=head
            )

            if r is not None and Helpers.code_check(r):
                self.device_status = 'off'
                return True
            logger.warning('Error turning %s off', self.device_name)
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

    def change_fan_speed(self, speed: int = None) -> bool:
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
                             format(self.device_name))
                return False
        else:
            if (level + 1) > 3:
                body['level'] = 1
            else:
                body['level'] = int(level + 1)

        r, _ = Helpers.call_api(
            '/131airPurifier/v1/device/updateSpeed', 'put',
            json=body, headers=head
        )

        if r is not None and Helpers.code_check(r):
            self.details['level'] = body['level']
            return True
        logger.warning('Error changing %s speed', self.device_name)
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
                json=body, headers=head
            )

            if r is not None and Helpers.code_check(r):
                self.mode = mode
                return True

        logger.warning('Error setting %s mode - %s', self.device_name, mode)
        return False

    def update(self) -> None:
        """Run function to get device details."""
        self.get_details()

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp1 = [
            ('Active Time : ', self.active_time, ' minutes'),
            ('Fan Level: ', self.fan_level, ''),
            ('Air Quality: ', self.air_quality, ''),
            ('Mode: ', self.mode, ''),
            ('Screen Status: ', self.screen_status, ''),
            ('Filter List: ', self.filter_life, ' percent'),
        ]
        for line in disp1:
            print('{:.<15} {} {}'.format(line[0], line[1], line[2]))

    def displayJSON(self) -> str:
        """Return air purifier status and properties in JSON output."""
        sup = super().displayJSON()
        sup_val = json.loads(sup)
        sup_val.append(
            {
                'Active Time': str(self.active_time),
                'Fan Level': self.fan_level,
                'Air Quality': self.air_quality,
                'Mode': self.mode,
                'Screen Status': self.screen_status,
                'Filter Life': str(self.filter_life),
            }
        )
        return sup_val


class VeSync300S(VeSyncBaseDevice):
    """300S Humidifier Class."""

    def __init__(self, details, manager):
        """Initilize 300S Humidifier class."""
        super().__init__(details, manager)
        self.enabled = True
        self.details: Dict[str, Union[str, int, float]] = {
            'humidity': 0,
            'mist_virtual_level': 0,
            'mist_level': 0,
            'mode': 'manual',
            'water_lacks': False,
            'humidity_high': False,
            'water_tank_lifted': False,
            'display': False,
            'automatic_stop_reach_target': False,
            'night_light_brightness': 0
        }
        self.config: Dict[str, Union[str, int, float]] = {
            'auto_target_humidity': 0,
            'display': False,
            'automatic_stop': True
        }

    def __build_api_dict(self, method: str) -> Tuple[Dict, Dict]:
        """Build 300S api call header and body.

        Available methods are: 'getHumidifierStatus', 'setAutomaticStop',
        'setSwitch', 'setNightLightBrightness', 'setVirtualLevel',
        'setTargetHumidity', 'setHumidityMode'
        """
        modes = ['getHumidifierStatus', 'setAutomaticStop',
                 'setSwitch', 'setNightLightBrightness', 'setVirtualLevel',
                 'setTargetHumidity', 'setHumidityMode']
        if method not in modes:
            logger.debug('Invalid mode - %s', method)
            return {}, {}
        head = Helpers.bypass_header()
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': method,
            'source': 'APP'
        }
        return head, body

    def build_humid_dict(self, dev_dict: Dict):
        """Build 300S humidifier status dictionary."""
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
        self.details['display'] = dev_dict.get('display', False)
        self.details['automatic_stop_reach_target'] = dev_dict.get(
            'automatic_stop_reach_target', True
        )
        self.details['night_light_brightness'] = dev_dict.get(
            'night_light_brightness', 0)

    def build_config_dict(self, conf_dict):
        """Build configuration dict for 300s humidifier."""
        self.config['auto_target_humidity'] = conf_dict.get(
            'auto_target_humidity', 0)
        self.config['display'] = conf_dict.get('display', False)
        self.config['automatic_stop'] = conf_dict.get('automatic_stop', True)

    def get_details(self) -> None:
        """Build 300S Humidifier details dictionary."""
        head = Helpers.bypass_header()
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': 'getHumidifierStatus',
            'source': 'APP'
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )
        outer_result = r.get('result', {})
        inner_result = None
        
        if outer_result is not None:
            inner_result = r.get('result', {}).get('result')
        if inner_result is not None and Helpers.code_check(r):
            if outer_result.get('code') == 0:
                self.build_humid_dict(inner_result)
            else:
                logger.debug('error in inner result dict from humidifier')
            if inner_result.get('config', {}):
                self.build_config_dict(inner_result)
            else:
                logger.debug('No configuration found in humidifier status')
        else:
            logger.debug('Error in humidifier response')

    def update(self):
        """Update 300S Humidifier details."""
        self.get_details()

    def toggle_switch(self, toggle) -> bool:
        """Toggle humidifier on/off."""
        if toggle != 'on' and toggle != 'off':
            logger.debug('Invalid toggle value for humidifier switch')
            return False
        enable = bool(toggle == 'on')

        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'data': {
                'enabled': enable,
                'id': 0
            },
            'method': 'setSwitch',
            'source': 'APP'
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if Helpers.code_check(r):
            return True
        logger.debug("Error toggling 300S humidifier - %s", self.device_name)
        return False

    def turn_on(self) -> bool:
        """Turn 300S Humidifier on."""
        return self.toggle_switch('on')

    def turn_off(self):
        """Turn 300S Humidifier off."""
        return self.toggle_switch('off')

    def automatic_stop_on(self) -> bool:
        """Turn 300S Humidifier automatic stop on."""
        return self.set_automatic_stop('on')

    def automatic_stop_off(self) -> bool:
        """Turn 300S Humidifier automatic stop on."""
        return self.set_automatic_stop('off')

    def set_automatic_stop(self, mode: str = 'NotSet') -> bool:
        """Set 300S Humidifier to automatic stop."""
        if mode in ['True', 'on', 'true']:
            enable = True
        elif mode in ['False', 'off']:
            enable = False
        elif mode == 'NotSet':
            if self.details['automatic_stop_reach_target']:
                enable = False
            else:
                enable = True
        else:
            logger.debug(
                'Invalid mode passed to set_automatic_stop - %s', mode)
            return False

        head, body = self.__build_api_dict('setAutomaticStop')
        if not head and not body:
            return False
        body['payload']['data']['enabled'] = enable

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if Helpers.code_check(r):
            return True
        if isinstance(r, dict):
            logger.debug('Error toggling automatic stop')
        else:
            logger.debug('Error in api return json for %s', self.device_name)
        return False

    def set_humidity(self, humidity: int) -> bool:
        """Set target 300S Humidifier humidity."""
        if 0 > humidity > 100:
            logger.debug("Humidity value must be set between 0 and 100")
            return False
        head, body = self.__build_api_dict('setTargetHumidity')

        # This is a hack
        body['method'] = 'bypassV2'

        if not head and not body:
            return False

        body['payload']['data'] = {
            'target_humidity': humidity
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )
        print(body)
        if Helpers.code_check(r):
            return True
        logger.debug('Error setting humidity')
        return False

    def set_humidity_mode(self, mode: str) -> bool:
        """Set humidifier mode - sleep or auto."""
        if mode not in ['sleep', 'auto']:
            logger.debug('Invalid humidity mode used - %s', mode)
            return False
        head, body = self.__build_api_dict('setTargetHumidity')
        if not head and not body:
            return False
        body['payload']['data'] = {
            'mode': mode
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if Helpers.code_check(r):
            return True
        logger.debug('Error setting humidity mode')
        return False

    def set_mist_level(self, level: int) -> bool:
        """Set humidifier mist level with int between 0 - 9."""
        if 0 > level > 9:
            logger.debug('Humidifier mist level must be between 0 and 9')
            return False

        head, body = self.__build_api_dict('setVirtualLevel')
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
            json=body,
        )

        if Helpers.code_check(r):
            return True
        logger.debug('Error setting mist level')
        return False
