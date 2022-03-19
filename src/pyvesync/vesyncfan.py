"""VeSync API for controling fans and purifiers."""

import json
import logging

from typing import Dict, Tuple, Union
from pyvesync.vesyncbasedevice import VeSyncBaseDevice
from pyvesync.helpers import Helpers

air_features = {
    'Dual200S': [],
    'Classic200S': [],
    'LUH-D301S-WEU': [],
    'LAP-C201S-AUSR': [],
    'Classic300S': ['nightlight'],
    'LAP-C401S-WUSR': [],
    'LAP-C401S-WAAA': [],
    'LAP-C601S-WUS': []
}

logger = logging.getLogger(__name__)


class VeSyncAir200S(VeSyncBaseDevice):
    """Core200S Purifier Class."""

    def __init__(self, details, manager):
        """Initilize Core200S Purifier class."""
        super().__init__(details, manager)
        self.enabled = True
        self.details: Dict[str, Union[str, int, float, bool]] = {
            'filter_life': 0,
            'mode': "manual",
            'level': 0,
            'display': False,
            'child_lock': False,
            'night_light': "off"
        }
        self.config: Dict[str, Union[str, int, float, bool]] = {
            'display': False,
            'display_forever': False
        }

    def __build_api_dict(self, method: str) -> Tuple[Dict, Dict]:
        """Build Core200S api call header and body.

        Available methods are: 'getPurifierStatus', 'setSwitch',
        'setNightLight', 'setLevel', 'setDisplay'
        'setPurifierMode', 'setChildLock'
        """
        modes = ['getPurifierStatus', 'setSwitch', 'setNightLight',
                 'setLevel', 'setPurifierMode', 'setDisplay',
                 'setChildLock']
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

    def build_purifier_dict(self, dev_dict: Dict):
        """Build Core200S purifier status dictionary."""
        self.enabled = dev_dict.get('enabled')
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

    def build_config_dict(self, conf_dict):
        """Build configuration dict for Core200S purifier."""
        self.config['display'] = conf_dict.get('display', False)
        self.config['display_forever'] = conf_dict.get('display_forever',
                                                       False)

    def get_details(self) -> None:
        """Build Core200S Purifier details dictionary."""
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
            json=body,
        )
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
        """Update Core200S Purifier details."""
        self.get_details()

    @property
    def fan_level(self) -> int:
        """Get current fan level (1-3)."""
        return int(self.speed)

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
    def child_lock(self) -> bool:
        """Get child lock state."""
        return bool(self.details['child_lock'])

    @property
    def night_light(self) -> str:
        """Get night light state (on/dim/off)."""
        return str(self.details['night_light'])

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
            json=body,
        )

        if Helpers.code_check(r):
            return True
        logger.debug("Error toggling Core200S purifier - %s",
                     self.device_name)
        return False

    def turn_on(self) -> bool:
        """Turn Core200S Purifier on."""
        return self.toggle_switch(True)

    def turn_off(self):
        """Turn Core200S Purifier off."""
        return self.toggle_switch(False)

    def child_lock_on(self) -> bool:
        """Turn Core200S child lock on."""
        return self.set_child_lock(True)

    def child_lock_off(self) -> bool:
        """Turn Core200S child lock off."""
        return self.set_child_lock(False)

    def set_child_lock(self, mode: bool) -> bool:
        """Set Core200S child lock."""
        if mode not in (True, False):
            logger.debug('Invalid mode passed to set_child_lock - %s', mode)
            return False

        head, body = self.__build_api_dict('setChildLock')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'child_lock': mode
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if r is not None and Helpers.code_check(r):
            self.details['child_lock'] = mode
            return True
        if isinstance(r, dict):
            logger.debug('Error toggling child lock')
        else:
            logger.debug('Error in api return json for %s', self.device_name)
        return False

    def set_display(self, mode: bool) -> bool:
        """Toggle display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        head, body = self.__build_api_dict('setDisplay')

        body['payload']['data'] = {
            'state': mode
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if Helpers.code_check(r):
            return True
        logger.debug("Error toggling Core200S display - %s",
                     self.device_name)
        return False

    def turn_on_display(self) -> bool:
        """Turn Display on."""
        return self.set_display(True)

    def turn_off_display(self):
        """Turn Display off."""
        return self.set_display(False)

    def change_fan_speed(self, speed: int = None) -> bool:
        """1,2,3 or call without argument to increment by 1."""
        if self.mode != 'manual':
            logger.debug('%s not in manual mode, cannot change speed',
                         self.device_name)
            return False

        try:
            level = int(self.speed)
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
                level = speed
            else:
                logger.debug('Invalid fan speed for %s',
                             self.device_name)
                return False
        else:
            if (level + 1) > 3:
                level = 1
            else:
                level = int(level + 1)

        head, body = self.__build_api_dict('setLevel')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'id': 0,
            'level': level,
            'type': 'wind'
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if r is not None and Helpers.code_check(r):
            self.speed = level
            return True
        logger.warning('Error changing %s speed', self.device_name)
        return False

    def set_night_light(self, mode: str) -> bool:
        """Set night list  - on, off or dim."""
        if mode.lower() not in ['on', 'off', 'dim']:
            logger.debug('Invalid nightlight mode used (on, off or dim)- %s',
                         mode)
            return False
        head, body = self.__build_api_dict('setNightLight')
        if not head and not body:
            return False
        body['payload']['data'] = {
            'night_light': mode.lower()
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if r is not None and Helpers.code_check(r):
            self.details['night_light'] = mode.lower()
            return True
        logger.debug('Error setting nightlight mode')
        return False

    def mode_toggle(self, mode: str) -> bool:
        """Set purifier mode - sleep or manual."""
        if mode.lower() not in ['sleep', 'manual']:
            logger.debug('Invalid purifier mode used (sleep or manual)- %s',
                         mode)
            return False
        head, body = self.__build_api_dict('setPurifierMode')
        if not head and not body:
            return False
        body['payload']['data'] = {
            'mode': mode.lower()
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if Helpers.code_check(r):
            return True
        logger.debug('Error setting purifier mode')
        return False

    def manual_mode(self) -> bool:
        """Set mode to manual."""
        return self.mode_toggle('manual')

    def sleep_mode(self) -> bool:
        """Set sleep mode to on."""
        return self.mode_toggle('sleep')

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp1 = [
            ('Mode: ', self.mode, ''),
            ('Filter Life: ', self.details['filter_life'], 'percent'),
            ('Fan Level: ', self.speed, ''),
            ('Display: ', self.details['display'], ''),
            ('Child Lock: ', self.details['child_lock'], ''),
            ('Night Light: ', self.details['night_light'], ''),
            ('Display Config: ', self.config['display'], ''),
            ('Display_Forever Config: ', self.config['display_forever'], '')
        ]
        for line in disp1:
            print(f'{line[0]:.<20} {line[0]} {line[0]}')

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
        return json.dumps(sup_val)


class VeSyncAir300S400S(VeSyncBaseDevice):
    """Core300S/400S Purifier Class."""

    def __init__(self, details, manager):
        """Initilize Core300S/400S Purifier class."""
        super().__init__(details, manager)
        self.enabled = True
        self.details: Dict[str, Union[str, int, float, bool]] = {
            'filter_life': 0,
            'mode': 'manual',
            'level': 0,
            'air_quality': 0,
            'display': False,
            'child_lock': False,
            'night_light': 'off',
        }
        self.config: Dict[str, Union[str, int, float, bool]] = {
            'display': False,
            'display_forever': False,
        }

    def __build_api_dict(self, method: str) -> Tuple[Dict, Dict]:
        """Build Core300S/400S api call header and body.

        Available methods are: 'getPurifierStatus', 'setSwitch',
        'setNightLight', 'setLevel', 'setDisplay'
        'setPurifierMode', 'setChildLock'
        """
        modes = ['getPurifierStatus', 'setSwitch', 'setNightLight',
                 'setLevel', 'setPurifierMode', 'setDisplay',
                 'setChildLock']
        if method not in modes:
            logger.debug('Invalid mode - %s', method)
            return {}, {}
        head = Helpers.bypass_header()
        body = Helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': method,
            'source': 'APP',
        }
        return head, body

    def build_purifier_dict(self, dev_dict: Dict):
        """Build Core300S/400S purifier status dictionary."""
        self.enabled = dev_dict.get('enabled')
        if self.enabled:
            self.device_status = 'on'
        else:
            self.device_status = 'off'
        self.details['filter_life'] = dev_dict.get('filter_life', 0)
        self.details['air_quality'] = dev_dict.get('air_quality_value', 0)
        self.mode = dev_dict.get('mode', 'manual')
        self.speed = dev_dict.get('level', 0)
        self.details['display'] = dev_dict.get('display', False)
        self.details['child_lock'] = dev_dict.get('child_lock', False)
        self.details['night_light'] = dev_dict.get('night_light', 'off')
        self.details['display'] = dev_dict.get('display', False)
        self.details['display_forever'] = dev_dict.get('display_forever',
                                                       False)

    def build_config_dict(self, conf_dict):
        """Build configuration dict for Core200S/300S purifier."""
        self.config['display'] = conf_dict.get('display', False)
        self.config['display_forever'] = conf_dict.get('display_forever',
                                                       False)

    def get_details(self) -> None:
        """Build Core300S/400S Purifier details dictionary."""
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
            json=body,
        )

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
        """Update Core300S/400S Purifier details."""
        self.get_details()

    @property
    def fan_level(self) -> int:
        """Get current fan level (1-4)."""
        return int(self.speed)

    @property
    def filter_life(self) -> int:
        """Get percentage of filter life remaining."""
        try:
            return int(self.details['filter_life'])
        except KeyError:
            return 0

    @property
    def air_quality(self) -> int:
        """Get air quality value (ug/m3)."""
        try:
            return int(self.details['air_quality'])
        except KeyError:
            return 0

    @property
    def display_state(self) -> bool:
        """Get display state."""
        return bool(self.details['display'])

    @property
    def child_lock(self) -> bool:
        """Get child lock state."""
        return bool(self.details['child_lock'])

    @property
    def night_light(self) -> str:
        """Get night light state (on/dim/off)."""
        return str(self.details['night_light'])

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
            json=body,
        )

        if Helpers.code_check(r):
            return True
        logger.debug("Error toggling Core200S/300S purifier - %s",
                     self.device_name)
        return False

    def turn_on(self) -> bool:
        """Turn Core300S/400S Purifier on."""
        return self.toggle_switch(True)

    def turn_off(self):
        """Turn Core300S/400S Purifier off."""
        return self.toggle_switch(False)

    def child_lock_on(self) -> bool:
        """Turn Core300S/400S child lock on."""
        return self.set_child_lock(True)

    def child_lock_off(self) -> bool:
        """Turn Core300S/400S child lock off."""
        return self.set_child_lock(False)

    def set_child_lock(self, mode: bool) -> bool:
        """Set Core300S/400S child lock."""
        if mode not in (True, False):
            logger.debug('Invalid mode passed to set_child_lock - %s', mode)
            return False

        head, body = self.__build_api_dict('setChildLock')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'child_lock': mode
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if r is not None and Helpers.code_check(r):
            self.details['child_lock'] = mode
            return True
        if isinstance(r, dict):
            logger.debug('Error toggling child lock')
        else:
            logger.debug('Error in api return json for %s', self.device_name)
        return False

    def set_display(self, mode: bool) -> bool:
        """Toggle display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        head, body = self.__build_api_dict('setDisplay')

        body['payload']['data'] = {
            'state': mode
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if Helpers.code_check(r):
            return True
        logger.debug("Error toggling Core200S/300S display - %s",
                     self.device_name)
        return False

    def turn_on_display(self) -> bool:
        """Turn Display on."""
        return self.set_display(True)

    def turn_off_display(self):
        """Turn Display off."""
        return self.set_display(False)

    def change_fan_speed(self, speed: int = None) -> bool:
        """1,2,3,4 or call without argument to increment by 1."""
        if self.mode != 'manual':
            logger.debug('%s not in manual mode, cannot change speed',
                         self.device_name)
            return False

        try:
            level = int(self.speed)
        except KeyError:
            logger.debug(
                'Cannot change fan speed, no level set for %s',
                self.device_name,
            )
            return False

        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        head = Helpers.req_headers(self.manager)
        if speed is not None:
            if speed == level:
                return True
            if speed in [1, 2, 3, 4]:
                level = speed
            else:
                logger.debug('Invalid fan speed for %s',
                             self.device_name)
                return False
        else:
            if (level + 1) > 4:
                level = 1
            else:
                level = int(level + 1)

        head, body = self.__build_api_dict('setLevel')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'id': 0,
            'level': level,
            'type': 'wind',
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if r is not None and Helpers.code_check(r):
            self.speed = level
            return True
        logger.warning('Error changing %s speed', self.device_name)
        return False

    def set_night_light(self, mode: str) -> bool:
        """Set night list  - on, off or dim."""
        if mode.lower() not in ['on', 'off', 'dim']:
            logger.debug('Invalid nightlight mode used (on, off or dim)- %s',
                         mode)
            return False
        head, body = self.__build_api_dict('setNightLight')
        if not head and not body:
            return False
        body['payload']['data'] = {
            'night_light': mode.lower()
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if r is not None and Helpers.code_check(r):
            self.details['night_light'] = mode.lower()
            return True
        logger.debug('Error setting nightlight mode')
        return False

    def mode_toggle(self, mode: str) -> bool:
        """Set purifier mode - sleep or manual or auto."""
        if mode.lower() not in ['sleep', 'manual', 'auto']:
            logger.debug(
                'Invalid purifier mode used (sleep or manual or auto)- %s',
                mode,
            )
            return False
        head, body = self.__build_api_dict('setPurifierMode')
        if not head and not body:
            return False
        body['payload']['data'] = {
            'mode': mode.lower()
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if Helpers.code_check(r):
            return True
        logger.debug('Error setting purifier mode')
        return False

    def auto_mode(self) -> bool:
        """Set mode to auto."""
        return self.mode_toggle('auto')

    def manual_mode(self) -> bool:
        """Set mode to manual."""
        return self.mode_toggle('manual')

    def sleep_mode(self) -> bool:
        """Set sleep mode to on."""
        return self.mode_toggle('sleep')

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp1 = [
            ('Mode: ', self.mode, ''),
            ('Filter Life: ', self.details['filter_life'], 'percent'),
            ('Air Quality: ', self.details['air_quality'], 'ug/m3'),
            ('Fan Level: ', self.speed, ''),
            ('Display: ', self.details['display'], ''),
            ('Child Lock: ', self.details['child_lock'], ''),
            ('Night Light: ', self.details['night_light'], ''),
            ('Display Config: ', self.config['display'], ''),
            ('Display_Forever Config: ', self.config['display_forever'], ''),
        ]
        for line in disp1:
            print(f'{line[0]:.<20} {line[1]} {line[2]}')

    def displayJSON(self) -> str:
        """Return air purifier status and properties in JSON output."""
        sup = super().displayJSON()
        sup_val = json.loads(sup)
        sup_val.update(
            {
                'Mode': self.mode,
                'Filter Life': str(self.details['filter_life']),
                'Air Quality': str(self.details['air_quality']),
                'Fan Level': str(self.speed),
                'Display': self.details['display'],
                'Child Lock': self.details['child_lock'],
                'Night Light': str(self.details['night_light']),
                'Display Config': self.config['display'],
                'Display_Forever Config': self.config['display_forever'],
            }
        )
        return json.dumps(sup_val)


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
                             self.device_name)
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
            ('Filter Life: ', self.filter_life, ' percent'),
        ]
        for line in disp1:
            print(f'{line[0]:.<15} {line[1]} {line[2]}')

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
                'Filter Life': str(self.filter_life),
            }
        )
        return sup_val


class VeSyncHumid200300S(VeSyncBaseDevice):
    """200S/300S Humidifier Class."""

    def __init__(self, details, manager):
        """Initialize 200S/300S Humidifier class."""
        super().__init__(details, manager)
        self.enabled = True
        if 'nightlight' in air_features.get(details['deviceType']):
            self.night_light = True
        else:
            self.night_light = False
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
        }
        if self.night_light:
            self.details['night_light_brightness'] = 0
        self.config: Dict[str, Union[str, int, float]] = {
            'auto_target_humidity': 0,
            'display': False,
            'automatic_stop': True
        }

    def __build_api_dict(self, method: str) -> Tuple[Dict, Dict]:
        """Build 200S/300S api call header and body.

        Available methods are: 'getHumidifierStatus', 'setAutomaticStop',
        'setSwitch', 'setNightLightBrightness', 'setVirtualLevel',
        'setTargetHumidity', 'setHumidityMode'
        """
        modes = ['getHumidifierStatus', 'setAutomaticStop',
                 'setSwitch', 'setNightLightBrightness', 'setVirtualLevel',
                 'setTargetHumidity', 'setHumidityMode', 'setDisplay']
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

    def build_humid_dict(self, dev_dict: Dict):
        """Build 200S/300S humidifier status dictionary."""
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
        if self.night_light:
            self.details['night_light_brightness'] = dev_dict.get(
                'night_light_brightness', 0)

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
            json=body,
        )

        if Helpers.code_check(r):
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

        head, body = self.__build_api_dict('setAutomaticStop')
        if not head and not body:
            return False

        body['payload']['data'] = {
            'enabled': mode
        }

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

    def set_display(self, mode: bool) -> bool:
        """Toggle display on/off."""
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        head, body = self.__build_api_dict('setDisplay')

        body['payload']['data'] = {
            'state': mode
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

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
        head, body = self.__build_api_dict('setTargetHumidity')

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
        head, body = self.__build_api_dict('setNightLightBrightness')

        if not head and not body:
            return False

        body['payload']['data'] = {
            'night_light_brightness': brightness
        }

        r, _ = Helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json=body,
        )

        if Helpers.code_check(r):
            return True
        logger.debug('Error setting humidity')
        return False

    def set_humidity_mode(self, mode: str) -> bool:
        """Set humidifier mode - sleep or auto."""
        if mode.lower() not in ['sleep', 'auto']:
            logger.debug('Invalid humidity mode used (sleep or auto)- %s',
                         mode)
            return False
        head, body = self.__build_api_dict('setHumidityMode')
        if not head and not body:
            return False
        body['payload']['data'] = {
            'mode': mode.lower()
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
        if level < 1 or level > 9:
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

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp1 = [
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
            disp1.append(('Night Light Brightness: ',
                          self.details['night_light_brightness'], 'percent'))
        for line in disp1:
            print(f'{line[0]:.<29} {line[1]} {line[2]}')

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
        return json.dumps(sup_val)
