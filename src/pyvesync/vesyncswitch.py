import logging
from abc import ABCMeta, abstractmethod

from pyvesync.helpers import Helpers as helpers
from pyvesync.vesyncbasedevice import VeSyncBaseDevice

logger = logging.getLogger(__name__)
feature_dict = {
    'ESWL01': [],
    'ESWD16': ['dimmable']
}


class VeSyncSwitch(VeSyncBaseDevice):
    __metaclasss__ = ABCMeta

    def __init__(self, details, manager):
        super().__init__(details, manager)
        self.details = {}

    def is_dimmable(self):
        if 'dimmable' in feature_dict.get(self.device_type):
            return True
        else:
            return False

    @abstractmethod
    def get_details(self):
        """Get Device Details"""

    @abstractmethod
    def turn_on(self):
        """Turn Switch On"""

    @abstractmethod
    def turn_off(self):
        """Turn switch off"""

    @abstractmethod
    def get_config(self):
        """Get configuration and firmware deatils"""

    @property
    def active_time(self):
        """Get active time of switch"""
        return self.details.get('active_time', 0)

    def update(self):
        self.get_details()


class VeSyncWallSwitch(VeSyncSwitch):
    def __init__(self, details, manager):
        super(VeSyncWallSwitch, self).__init__(details, manager)

    def get_details(self):
        body = helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/inwallswitch/v1/device/devicedetail',
            'post',
            headers=head,
            json=body
        )

        if r is not None and helpers.check_response(r, 'walls_detail'):
            self.device_status = r.get('deviceStatus', self.device_status)
            self.details['active_time'] = r.get('activeTime', 0)
            self.connection_status = r.get('connectionStatus',
                                           self.connection_status)
        else:
            logger.debug('Error getting {} details'.format(self.device_name))

    def get_config(self):
        body = helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/inwallswitch/v1/device/configurations',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body)

        if helpers.check_response(r, 'config'):
            self.config = helpers.build_config_dict(r)

    def turn_off(self):
        body = helpers.req_body(self.manager, 'devicestatus')
        body['status'] = 'off'
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/inwallswitch/v1/device/devicestatus',
            'put',
            headers=head,
            json=body
        )

        if r is not None and helpers.check_response(r, 'walls_toggle'):
            self.device_status = 'off'
            return True
        else:
            logger.warning('Error turning {} off'.format(self.device_name))
            return False

    def turn_on(self):
        body = helpers.req_body(self.manager, 'devicestatus')
        body['status'] = 'on'
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/inwallswitch/v1/device/devicestatus',
            'put',
            headers=head,
            json=body
        )

        if r is not None and helpers.check_response(r, 'walls_toggle'):
            self.device_status = 'on'
            return True
        else:
            logger.warning('Error turning {} on'.format(self.device_name))
            return False


class VeSyncDimmerSwitch(VeSyncSwitch):
    """Vesync Dimmer Switch Class with RGB Faceplate"""
    def __init__(self, details, manager):
        super().__init__(details, manager)
        self._brightness = None
        self._rgb_value = {'red': 0, 'blue': 0, 'green': 0}
        self._rgb_status = None
        self._indicator_light = None

    def get_details(self):
        body = helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/dimmer/v1/device/devicedetail',
            'post',
            headers=head,
            json=body)

        if r is not None and helpers.check_response(r, 'walls_detail'):
            self.device_status = r.get('deviceStatus', self.device_status)
            self.details['active_time'] = r.get('activeTime', 0)
            self.connection_status = r.get('connectionStatus',
                                           self.connection_status)
            self._brightness = r.get('brightness')
            self._rgb_status = r.get('rgbStatus')
            self._rgb_value = r.get('rgbValue')
            self._indicator_light = r.get('indicatorlightStatus')
        else:
            logger.debug('Error getting {} details'.format(self.device_name))

    @property
    def brightness(self):
        return self._brightness

    @property
    def indicator_light_status(self):
        """Indicator light status property."""
        return self._indicator_light

    @property
    def rgb_light_status(self):
        """RGB Faceplate light status."""
        return self._rgb_status

    @property
    def rgb_light_value(self):
        """RGB Light Values."""
        return self._rgb_value

    def switch_toggle(self, status: str) -> bool:
        """Toggle switch status"""
        if status not in ['on', 'off']:
            logger.debug('Invalid status passed to wall switch')
            return False
        body = helpers.req_body(self.manager, 'devicestatus')
        body['status'] = status
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/dimmer/v1/device/devicestatus',
            'put',
            headers=head,
            json=body
        )

        if r is not None and helpers.check_response(r, 'walls_toggle'):
            self.device_status = status
            return True
        else:
            logger.warning('Error turning %s %s', self.device_name, status)
            return False

    def turn_on(self) -> bool:
        """Turn switch on."""
        return self.switch_toggle('on')

    def turn_off(self) -> bool:
        """Turn switch off."""
        return self.switch_toggle('off')

    def indicator_light_toggle(self, status: str) -> bool:
        """Toggle indicator light"""
        if status not in ['on', 'off']:
            logger.debug('Invalid status for wall switch')
            return False
        body = helpers.req_body(self.manager, 'devicestatus')
        body['status'] = status
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/dimmer/v1/device/indicatorlightstatus',
            'put',
            headers=head,
            json=body
        )

        if r is not None and helpers.check_response(r, 'walls_toggle'):
            self.device_status = status
            return True
        else:
            logger.warning('Error turning %s indicator light %s',
                           self.device_name, status)
            return False

    def indicator_light_on(self) -> bool:
        """Turn Indicator light on."""
        return self.indicator_light_toggle('on')

    def indicator_light_off(self) -> bool:
        """Turn indicator light off."""
        return self.indicator_light_toggle('off')

    def rgb_color_status(self, status: str, red: int = None,
                         blue: int = None, green: int = None) -> bool:
        """Set faceplate RGB color."""
        body = helpers.req_body(self.manager, 'devicestatus')
        body['status'] = status
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)
        if red is not None and blue is not None and green is not None:
            body['rgbValue'] = {'red': red, 'blue': blue, 'green': green}

        r, _ = helpers.call_api(
            '/dimmer/v1/device/devicergbstatus',
            'put',
            headers=head,
            json=body
        )

        if r is not None and helpers.check_response(r, 'walls_toggle'):
            self._rgb_status = status
            if body.get('rgbValue') is not None:
                self._rgb_value = {'red': red, 'blue': blue, 'green': green}
            return True
        else:
            logger.warning('Error turning {} off'.format(self.device_name))
            return False

    def rgb_color_off(self) -> bool:
        """Turn RGB Color Off."""
        return self.rgb_color_status('off')

    def rgb_color_on(self) -> bool:
        """Turn RGB Color Off."""
        return self.rgb_color_status('on')

    def rgb_color_set(self, red: int, green: int, blue: int) -> bool:
        """Set RGB Color of faceplate."""
        if (isinstance(red, int) and
                isinstance(green, int) and
                isinstance(blue, int)):
            for color in [red, green, blue]:
                if color < 0 or color > 255:
                    logger.warning('Invalid RGB value')
                    return False

            return self.rgb_color_status('on', red, green, blue)

    def set_brightness(self, brightness: int):
        """set brightness of dimmer - 1 - 100"""
        if isinstance(brightness, int) and \
                (brightness > 0 or brightness <= 100):

            body = helpers.req_body(self.manager, 'devicestatus')
            body['brightness'] = brightness
            body['uuid'] = self.uuid
            head = helpers.req_headers(self.manager)

            r, _ = helpers.call_api(
                '/dimmer/v1/device/updatebrightness',
                'put',
                headers=head,
                json=body)

            if r is not None and helpers.check_response(r, 'walls_toggle'):
                self._brightness = brightness
                return True
            else:
                logger.warning('Error setting %s brightness', self.device_name)
        else:
            logger.warning('Invalid brightness')
        return False
