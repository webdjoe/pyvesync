from pyvesync.vesyncbasedevice import VeSyncBaseDevice
from pyvesync.helpers import Helpers as helpers
import logging

logger = logging.getLogger(__name__)


class VeSyncAir131(VeSyncBaseDevice):

    def __init__(self, details, manager):
        super(VeSyncAir131, self).__init__(details, manager)

        self.details = {}

    def get_details(self):
        """Build details dictionary"""
        body = helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/131airPurifier/v1/device/deviceDetail',
            method='post',
            headers=head,
            json=body
        )

        if r is not None and helpers.check_response(r, 'airpur_detail'):
            self.device_status = r.get('deviceStatus', 'unknown')
            self.connection_status = r.get('connectionStatus', 'unknown')
            self.details['active_time'] = r.get('activeTime', 0)
            self.details['filter_life'] = r.get('filterLife', {})
            self.details['screen_status'] = r.get('screenStatus', 'unknown')
            self.mode = r.get('mode', self.mode)
            self.details['level'] = r.get('level', 0)
            self.details['air_quality'] = r.get('airQuality', 'unknown')
        else:
            logger.debug('Error getting {} details'.format(self.device_name))

    def get_config(self):
        body = helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/131airpurifier/v1/device/configurations',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body)

        if helpers.check_response(r, 'config'):
            self.config = helpers.build_config_dict(r)

    @property
    def active_time(self):
        """Return total time active"""
        return self.details.get('active_time', 0)

    @property
    def fan_level(self):
        """Get current fan level (1-3)"""
        return self.details.get('level', 0)

    @property
    def filter_life(self):
        """Get percentage of filter life remaining"""
        try:
            return self.details['filter_life'].get('percent', 0)
        except KeyError:
            return 0

    @property
    def air_quality(self):
        """Get Air Quality"""
        return self.details.get('air_quality', 'unknown')

    @property
    def screen_status(self):
        """Return Screen status (on/off)"""
        return self.details.get('screen_status', 'unknown')

    def turn_on(self):
        """Turn Air Purifier on"""
        if self.device_status != 'on':
            body = helpers.req_body(self.manager, 'devicestatus')
            body['uuid'] = self.uuid
            body['status'] = 'on'
            head = helpers.req_headers(self.manager)

            r, _ = helpers.call_api(
                '/131airPurifier/v1/device/deviceStatus',
                'put',
                json=body,
                headers=head
            )

            if r is not None and helpers.check_response(r, 'airpur_status'):
                self.device_status = 'on'
                return True
            else:
                logger.warning('Error turning {} on'.format(self.device_name))
                return False

    def turn_off(self):
        """Turn Air Purifier Off"""
        if self.device_status == 'on':
            body = helpers.req_body(self.manager, 'devicestatus')
            body['uuid'] = self.uuid
            body['status'] = 'off'
            head = helpers.req_headers(self.manager)

            r, _ = helpers.call_api(
                '/131airPurifier/v1/device/deviceStatus',
                'put',
                json=body,
                headers=head
            )

            if r is not None and helpers.check_response(r, 'airpur_status'):
                self.device_status = 'off'
                return True
            else:
                logger.warning('Error turning {} off'.format(self.device_name))
                return False

    def auto_mode(self):
        """Set mode to auto"""
        return self.mode_toggle('auto')

    def manual_mode(self):
        """Set mode to manual"""
        return self.mode_toggle('manual')

    def sleep_mode(self):
        """Set sleep mode to on"""
        return self.mode_toggle('sleep')

    def change_fan_speed(self, speed: int = None) -> bool:
        """Adjust Fan Speed by Specifying 1,2,3 as argument or cycle
            through speeds increasing by one"""
        if self.mode != 'manual':
            logger.debug(
                '{} not in manual mode, cannot change speed'.format(
                    self.device_name))
            return False

        try:
            level = self.details['level']
        except KeyError:
            logger.debug(
                'Cannot change fan speed, no level set for {}'.format(
                    self.device_name))
            return False

        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)
        if speed is not None:
            if speed == level:
                return True
            elif speed in [1, 2, 3]:
                body['level'] = speed
            else:
                logger.debug(
                    'Invalid fan speed for {}'.format(self.device_name))
                return False
        else:
            if (level + 1) > 3:
                body['level'] = 1
            else:
                body['level'] = int(level + 1)

        r, _ = helpers.call_api(
            '/131airPurifier/v1/device/updateSpeed',
            'put',
            json=body,
            headers=head
        )

        if r is not None and helpers.check_response(r, 'airpur_status'):
            self.details['level'] = body['level']
            return True
        else:
            logger.warning(
                'Error changing {} speed'.format(self.device_name))
            return False

    def mode_toggle(self, mode: str) -> bool:
        """Set mode to manual, auto or sleep"""
        head = helpers.req_headers(self.manager)
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        if mode != self.mode and mode in ['sleep', 'auto', 'manual']:
            body["mode"] = mode
            if mode == 'manual':
                body['level'] = 1

            r, _ = helpers.call_api(
                '/131airPurifier/v1/device/updateMode',
                'put',
                json=body,
                headers=head
            )

            if r is not None and helpers.check_response(r, 'airpur_status'):
                self.mode = mode
                return True

        return False

    def update(self):
        """Run function to get device details"""
        self.get_details()

    def display(self):
        super(VeSyncAir131, self).display()
        disp1 = [("Active Time : ", self.active_time, ' minutes'),
                 ("Fan Level: ", self.fan_level, ""),
                 ("Air Quality: ", self.air_quality, ""),
                 ("Mode: ", self.mode, ""),
                 ("Screen Status: ", self.screen_status, ""),
                 ("Filter List: ", self.filter_life, " percent")]
        for line in disp1:
            print("{:.<15} {} {}".format(line[0], line[1], line[2]))
