import logging
from abc import ABCMeta, abstractmethod

from pyvesync.helpers import Helpers as helpers
from pyvesync.vesyncbasedevice import VeSyncBaseDevice

logger = logging.getLogger(__name__)

# Possible features - dimmable, color_temp, rgb_shift
feature_dict = {
    'ESL100': ['dimmable']
}


class VeSyncBulb(VeSyncBaseDevice):
    """Base class for VeSync Bulbs."""
    __metaclass__ = ABCMeta

    def __init__(self, details, manager):
        super(VeSyncBulb, self).__init__(details, manager)
        self._brightness = None

    @property
    def brightness(self):
        """Return brightness of vesync bulb."""
        if self.dimmable_feature:
            return self._brightness

    @property
    def dimmable_feature(self):
        """Return true if dimmable bulb."""
        if 'dimmable' in feature_dict.get(self.device_type):
            return True
        else:
            return False

    @property
    def bulb_temp_feature(self):
        """Return true in color temperature can be changed."""
        if 'color_temp' in feature_dict.get(self.device_type):
            return True
        else:
            return False

    @property
    def color_change_feature(self):
        """Return True if bulb supports changing color."""
        if 'rgb_shit' in feature_dict.get(self.device_type):
            return True
        else:
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
