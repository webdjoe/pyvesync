import logging
from abc import ABCMeta, abstractmethod

from pyvesync.helpers import Helpers as helpers
from pyvesync.vesyncbasedevice import VeSyncBaseDevice

logger = logging.getLogger(__name__)


class VeSyncSwitch(VeSyncBaseDevice):
    __metaclasss__ = ABCMeta

    def __init__(self, details, manager):
        super().__init__(details, manager)
        self.details = {}

    def is_dimmable(self):
        if self.device_type == 'ESWL02-D':
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
