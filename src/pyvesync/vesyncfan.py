from pyvesync.vesyncbasedevice import VeSyncBaseDevice
from pyvesync.helpers import Helpers as helpers


class VeSyncAir131(VeSyncBaseDevice):

    def __init__(self, details, manager):
        super(VeSyncAir131, self).__init__(details, manager)
        self.filter_life = {}
        self.details = {}
        self.air_quality = None
        self.screen_status = None
        self.level = None

        self.details = {}

    def get_details(self):
        """Build details dictionary"""
        body = helpers.req_body(self.manager, 'devicedetail')
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api('/131airpurifier/v1/device/deviceDetail',
                                method='post', headers=head, json=body)

        if r is not None and helpers.check_response(r, 'airpur_detail'):
            self.device_status = r.get('deviceStatus', 'unknown')
            self.connection_status = r.get('connectionStatus', 'unknown')
            self.details['active_time'] = r.get('activeTime', 0)
            self.details['filter_life'] = r.get('filterLife', {})
            self.details['screeen_status'] = r.get('screenStatus', 'unknown')
            self.details['mode'] = r.get('mode', 'unknown')
            self.details['level'] = r.get('level', None)

    @property
    def fan_level(self):
        """Get current fan level (1-3)"""
        return self.details.get('level', 0)

    @property
    def filter_life(self):
        """Get percentage of filter life remaining"""
        return self.details['filter_life'].get('percentage', 0)

    def turn_on(self):
        """Turn Air Purifier on"""
        if self.device_status != 'on':
            body = helpers.req_body(self.manager, 'devicestatus')
            body['uuid'] = self.uuid
            body['status'] = 'on'
            head = helpers.req_headers(self.manager)

            r, _ = helpers.call_api('/131airPurifier/v1/device/deviceStatus',
                                    'put', json=body, headers=head)

            if r is not None and helpers.check_response(r, 'airpur_status'):
                self.device_status = 'on'
                return True
            else:
                return False

    def turn_off(self):
        """Turn Air Purifier Off"""
        if self.device_status == 'on':
            body = helpers.req_body(self.manager, 'devicestatus')
            body['uuid'] = self.uuid
            body['status'] = 'off'
            head = helpers.req_headers(self.manager)

            r, _ = helpers.call_api('/131airPurifier/v1/device/deviceStatus',
                                    'put', json=body, headers=head)

            if r is not None and helpers.check_response(r, 'airpur_status'):
                self.device_status = 'off'
                return True
            else:
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

    def fan_speed(self, speed: int = None) -> bool:
        """Adjust Fan Speed by Specifying 1,2,3 as argument or cycle
            through speeds increasing by one"""
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)
        if self.details.get('mode') != 'manual':
            self.mode_toggle('manual')
        else:
            if speed is not None:
                level = int(self.details.get('level'))
                if speed == level:
                    return False
                elif speed in [1, 2, 3]:
                    body['level'] = speed
            else:
                if (level + 1) > 3:
                    body['level'] = 1
                else:
                    body['level'] = int(level + 1)

            r, _ = helpers.call_api('/131airPurifier/v1/device/updateSpeed',
                                    'put', json=body, headers=head)

            if r is not None and helpers.check_response(r, 'airpur_status'):
                self.details['level'] = body['level']
                return True
            else:
                return False

    def mode_toggle(self, mode: str) -> bool:
        """Set mode to manual, auto or sleep"""
        head = helpers.req_headers(self.manager)
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        if mode != body['mode'] and mode in ['sleep', 'auto', 'manual']:
            body['mode'] = mode
            if mode == 'manual':
                body['level'] = 1

            r, _ = helpers.call_api('/131airPurifier/v1/device/updateMode',
                                    'put', json=body, headers=head)

            if r is not None and helpers.check_response(r, 'airpur_status'):
                self.details['mode'] = mode
                return True

        return False

    def update(self):
        """Run function to get device details"""
        self.get_details()
