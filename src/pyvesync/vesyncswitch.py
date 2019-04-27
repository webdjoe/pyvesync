from pyvesync.vesyncbasedevice import VeSyncBaseDevice
from pyvesync.helpers import Helpers as helpers
from abc import ABCMeta, abstractmethod


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
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api('/inwallswitch/v1/device/devicedetail',
                                'post', headers=head, json=body)

        if r is not None and helpers.check_response(r, 'walls_detail'):
            self.device_status = r['deviceStatus']
            self.details['active_time'] = r['activeTime']
            self.details['connection_status'] = r['connectionStatus']
            self.connection_status = r['connectionStatus']

    def turn_off(self):
        body = helpers.req_body(self.manager, 'devicestatus')
        body['status'] = 'off'
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api('/inwallswitch/v1/device/devicedetail',
                                'post', headers=head, json=body)

        if r is not None and helpers.check_response(r, 'walls_toggle'):
            self.device_status = 'off'
            return True
        else:
            return False

    def turn_on(self):
        body = helpers.req_body(self.manager, 'devicestatus')
        body['status'] = 'on'
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api('/inwallswitch/v1/device/devicedetail',
                                'post', headers=head, json=body)

        if r is not None and helpers.check_response(r, 'walls_toggle'):
            self.device_status = 'on'
            return True
        else:
            return False
