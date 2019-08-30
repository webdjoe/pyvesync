import logging
from abc import ABCMeta, abstractmethod

from pyvesync.helpers import Helpers as helpers
from pyvesync.vesyncbasedevice import VeSyncBaseDevice

logger = logging.getLogger(__name__)

# Possible features - dimmable, color_temp, rgb_shift
feature_dict = {
    'ESL100': ['dimmable'],
    'ESL100CW': ['dimmable', 'color_temp']
}


def pct_to_kelvin(pct, max_k=6500, min_k=2700):
    """Convert percent to kelvin"""
    kelvin = ((max_k - min_k) * pct / 100) + min_k
    return kelvin


class VeSyncBulb(VeSyncBaseDevice):
    """Base class for VeSync Bulbs."""
    __metaclass__ = ABCMeta

    def __init__(self, details, manager):
        super(VeSyncBulb, self).__init__(details, manager)
        self._brightness = None
        self._color_temp = None

    @property
    def brightness(self):
        """Return brightness of vesync bulb."""
        if self.dimmable_feature and self._brightness is not None:
            return self._brightness

    @property
    def color_temp_kelvin(self):
        """Return Color Temp of bulb if supported in Kelvin"""
        if self.color_temp_feature and self._color_temp is not None:
            return int(pct_to_kelvin(self._color_temp))

    @property
    def color_temp_pct(self):
        """Return color temperature of bulb in percent"""
        if self.color_temp_feature and self._color_temp is not None:
            return int(self._color_temp)

    @property
    def dimmable_feature(self):
        """Return true if dimmable bulb."""
        if 'dimmable' in feature_dict.get(self.device_type):
            return True
        return False

    @property
    def color_temp_feature(self):
        """Return true in color temperature can be changed (tunable)."""
        if 'color_temp' in feature_dict.get(self.device_type):
            return True
        return False

    @property
    def rgb_shift_feature(self):
        """Return True if bulb supports changing color."""
        if 'rgb_shift' in feature_dict.get(self.device_type):
            return True
        return False

    @abstractmethod
    def get_details(self):
        """Get vesync bulb details."""

    @abstractmethod
    def toggle(self, status: int):
        """Toggle vesync lightbulb"""

    @abstractmethod
    def get_config(self):
        """Call api to get configuration details and firmware"""

    def turn_on(self):
        """Turn on vesync bulbs."""
        if self.toggle('on'):
            self.device_status = 'on'
            return True
        else:
            return False

    def turn_off(self):
        """Turn off vesync bulbs."""
        if self.toggle('off'):
            self.device_status = 'off'
            return True
        else:
            return False

    def update(self):
        """Update bulb details"""
        self.get_details()

    def display(self):
        super(VeSyncBulb, self).display()
        if self.connection_status == 'online':
            if self.dimmable_feature:
                disp1 = [("Brightness: ", self.brightness, "%")]
            for line in disp1:
                print("{:.<17} {} {}".format(line[0], line[1], line[2]))


class VeSyncBulbESL100(VeSyncBulb):
    """Object to hold VeSync ESL100 light bulb."""
    def __init__(self, details, manager):
        super(VeSyncBulbESL100, self).__init__(details, manager)
        self.details = {}

    def get_details(self):
        body = helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        r, _ = helpers.call_api(
            '/SmartBulb/v1/device/devicedetail',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
            )
        if helpers.check_response(r, 'bulb_detail'):
            self.connection_status = r.get('connectionStatus')
            self.device_status = r.get('deviceStatus')
            if self.dimmable_feature:
                self._brightness = int(r.get('brightNess'))
        else:
            logger.debug('Error getting {} details'.format(self.device_name))

    def get_config(self):
        body = helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/SmartBulb/v1/device/configurations',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body)

        if helpers.check_response(r, 'config'):
            self.config = helpers.build_config_dict(r)

    def toggle(self, status):
        """Toggle vesync bulb."""
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = status
        r, _ = helpers.call_api(
            '/SmartBulb/v1/device/devicestatus',
            'put',
            headers=helpers.req_headers(self.manager),
            json=body
            )
        if helpers.check_response(r, 'bulb_toggle'):
            self.device_status = status
            return True
        else:
            return False

    def set_brightness(self, brightness: int):
        """Set brightness of vesync bulb"""
        if self.dimmable_feature:
            if brightness > 0 and brightness <= 100:
                body = helpers.req_body(self.manager, 'devicestatus')
                body['uuid'] = self.uuid
                body['status'] = 'on'
                body['brightNess'] = str(brightness)
                r, _ = helpers.call_api(
                    '/SmartBulb/v1/device/updateBrightness',
                    'put',
                    headers=helpers.req_headers(self.manager),
                    json=body)

                if helpers.check_response(r, 'bulb_toggle'):
                    self._brightness = brightness
                    return True
                else:
                    logger.debug(
                        'Error setting brightness for {}'.format(
                            self.device_name))
                    return False
            else:
                logger.warning('Invalid brightness')
                return False
        else:
            logger.debug('{} is not dimmable - ', self.device_name)


class VeSyncBulbESL100CW(VeSyncBulb):
    """VeSync Tunable and Dimmable White Bulb"""
    def __init__(self, details, manager):
        super(VeSyncBulb, self).__init__(details, manager)

    def get_details(self):
        body = helpers.req_body(self.manager, 'bypass')
        body['cid'] = self.cid
        body['jsonCmd'] = {'getLightStatus': 'get'}
        body['configModule'] = self.config_module
        r, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/bypass',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body)
        if helpers.check_response(r, 'bypass'):
            if r.get('code') == 0 and r.get('result').get('light') is not None:
                light = r.get('result').get('light')
                self.connection_status = 'online'
                self.device_status = light.get('action', 'off')
                if self.dimmable_feature:
                    self._brightness = light.get('brightness')
                if self.color_temp_feature:
                    self._color_temp = light.get('colorTempe')
            elif r.get('code') == -11300027:
                logger.debug('%s device offline', self.device_name)
                self.connection_status = 'offline'
                self.device_status = 'off'
            else:
                logger.warning('%s - Unknown return code - %d with message %s',
                               self.device_name, r.get('code'), r.get('msg'))
        else:
            logger.debug('Error getting {} details'.format(self.device_name))

    def get_config(self):
        body = helpers.req_body(self.manager, 'bypass_config')
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/configurations',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body)

        if helpers.check_response(r, 'config'):
            self.config = helpers.build_config_dict(r)

    def toggle(self, status):
        """Toggle vesync bulb."""
        body = helpers.req_body(self.manager, 'bypass')
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['jsonCmd'] = {'light': {'action': status}}
        r, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/bypass',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body)
        if helpers.check_response(r, 'bypass'):
            if r.get('code') == 0:
                self.device_status = status
                return True
            else:
                logger.debug('%s offline', self.device_name)
                self.device_status = 'off'
                self.connection_status = 'offline'

        return False

    def set_brightness(self, brightness: int) -> bool:
        """Set brightness of vesync bulb"""
        if self.dimmable_feature:
            if brightness > 0 and brightness <= 100:
                body = helpers.req_body(self.manager, 'bypass')
                body['cid'] = self.cid
                body['configModule'] = self.config_module
                if self.device_status == 'off':
                    light_dict = {'action': 'on', 'brightness': brightness}
                else:
                    light_dict = {'brightness': brightness}
                body['jsonCmd'] = {'light': light_dict}
                r, _ = helpers.call_api(
                    '/cloud/v1/deviceManaged/bypass',
                    'post',
                    headers=helpers.req_headers(self.manager),
                    json=body)

                if helpers.check_response(r, 'bypass'):
                    if r.get('code') == 0:
                        self._brightness = brightness
                        return True
                    else:
                        self.device_status = 'off'
                        self.connection_status = 'offline'
                        logger.debug('%s offline', self.device_name)
                else:
                    logger.debug('Error setting brightness for {}'.format(
                        self.device_name))
            else:
                logger.warning('Invalid brightness')
        else:
            logger.debug('{} is not dimmable - ', self.device_name)
        return False

    def set_color_temp(self, color_temp: int) -> bool:
        """Set Color Temperature of VeSync Bulb in pct (1 - 100)"""
        if color_temp < 0 or color_temp > 100:
            logger.debug('Invalid color temperature - only between 0 and 100')
            return False
        body = helpers.req_body(self.manager, 'bypass')
        body['cid'] = self.cid
        body['jsonCmd'] = {'light': {}}
        if self.device_status == 'off':
            light_dict = {'action': 'on', 'colorTempe': color_temp}
        else:
            light_dict = {'colorTempe': color_temp}
        body['jsonCmd']['light'] = light_dict
        r, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/bypass',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body)
        if helpers.check_response(r, 'bypass'):
            if r.get('code') == -11300027:
                logger.debug('%s device offline', self.device_name)
                self.connection_status = 'offline'
                self.device_status = 'off'
                return False
            elif r.get('code') == 0:
                self.device_status = 'on'
                self._color_temp = color_temp
                return True
            else:
                logger.warning('%s - Unknown return code - %d with message %s',
                               self.device_name, r.get('code'), r.get('msg'))
        return False
