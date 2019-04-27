import logging
import time
import re

from pyvesync.helpers import Helpers as helpers
from pyvesync.vesyncoutlet import (VeSyncOutlet7A, VeSyncOutlet10A,
                                   VeSyncOutlet15A)
from pyvesync.vesyncswitch import VeSyncWallSwitch
from pyvesync.vesyncfan import VeSyncAir131

logger = logging.getLogger(__name__)

API_RATE_LIMIT = 30
DEFAULT_TZ = 'America/New_York'

DEFAULT_ENER_UP_INT = 21600


class VSFactory(object):
    @staticmethod
    def getDevice(device_type, config, manager):
        if device_type == 'wifi-switch-1.3':
            return VeSyncOutlet7A(config, manager)
        elif device_type in ['ESW03-USA', 'ESW10-EU']:
            return VeSyncOutlet10A(config, manager)
        elif device_type == 'ESW15-USA':
            return VeSyncOutlet15A(config, manager)
        elif device_type in ['ESWL01', 'ESWL03']:
            return VeSyncWallSwitch(config, manager)
        elif device_type == 'LV-PUR131S':
            return VeSyncAir131(config, manager)
        else:
            logger.debug('Unknown device found - ' + device_type)


class VeSync(object):
    def __init__(self, username, password, time_zone=DEFAULT_TZ):
        self.username = username
        self.password = password
        self.token = None
        self.account_id = None
        self.devices = None
        self.outlets = None
        self.switches = None
        self.fans = None
        self.enabled = False
        self.update_interval = API_RATE_LIMIT
        self.last_update_ts = None
        self.in_process = False
        self._energy_update_interval = DEFAULT_ENER_UP_INT
        self._energy_check = True

        if isinstance(time_zone, str) and len(time_zone) > 0:
            reg_test = r"[^a-zA-Z/_]"
            if bool(re.search(reg_test, time_zone)):
                self.time_zone = DEFAULT_TZ
                logger.debug("Invalid characters in time zone - " + time_zone)
            else:
                self.time_zone = time_zone
        else:
            self.time_zone = DEFAULT_TZ
            logger.debug("Time zone is not a string")

    @property
    def energy_update_interval(self):
        """Return energy update interval"""
        return self._energy_update_interval

    @energy_update_interval.setter
    def energy_update_interval(self, new_energy_update):
        """"Set energy update interval in seconds"""
        if new_energy_update > 0:
            self._energy_update_interval = new_energy_update

    @property
    def energy_update_check(self):
        """Return true or false to enable/disable
            check for energy update interval"""
        return self._energy_check

    @energy_update_check.setter
    def energy_update_check(self, check: bool):
        """Enable/Disable energy update interval check"""
        self._energy_check = check

    def process_devices(self, devices):
        outlets = []
        switches = []
        fans = []
        # bulbs = []

        outlet_types = ['wifi-switch-1.3', 'ESW03-USA',
                        'ESW10-EU', 'ESW15-USA']
        switch_types = ['ESWL01', 'ESWL03']
        fan_types = ['LV-PUR131S']
        # bulb_types = ['ESL100']

        for dev in devices:
            devType = dev['deviceType']

            if 'type' in dev:
                if devType in outlet_types:
                    outlets.append(VSFactory.getDevice(devType, dev, self))
                elif devType in fan_types:
                    fans.append(VSFactory.getDevice(devType, dev, self))
                elif devType in switch_types:
                    switches.append(VSFactory.getDevice(devType, dev, self))
                # elif devType in bulb_types:
                #    bulbs.append(VSFactory.getDevice(devType, dev, self))
                else:
                    logger.debug('Unknown device ' + devType)
            else:
                logger.debbug('type key not found')

        return (outlets, switches, fans)

    def get_devices(self) -> list:
        """Return list of VeSync devices"""

        if not self.enabled:
            return None

        self.in_process = True

        response, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/devices',
            'post',
            headers=helpers.req_headers(self),
            json=helpers.req_body(self, 'devicelist')
        )

        if response and helpers.check_response(response, 'get_devices'):
            if 'result' in response and 'list' in response['result']:
                device_list = response['result']['list']
                outlets, switches, fans = self.process_devices(device_list)
            else:
                logger.error('Device list in response not found')
        else:
            logger.error('Error retrieving device list')

        self.in_process = False

        return (outlets, switches, fans)

    def login(self):
        """Return True if log in request succeeds"""
        user_check = isinstance(self.username, str) and len(self.username) > 0
        pass_check = isinstance(self.password, str) and len(self.password) > 0

        if user_check and pass_check:
            response, _ = helpers.call_api(
                '/cloud/v1/user/login',
                'post',
                json=helpers.req_body(self, 'login')
            )

            if response and helpers.check_response(response, 'login'):
                self.token = response['result']['token']
                self.account_id = response['result']['accountID']
                self.enabled = True

                return True
            else:
                logger.error('Error logging in with username and password')
                return False

        else:
            if user_check is False:
                logger.error('Username invalid')
            if pass_check is False:
                logger.error('Password invalid')

        return False

    def device_time_check(self) -> bool:
        if self.last_update_ts is None or (
                time.time() - self.last_update_ts) > self.update_interval:
            return True
        else:
            return False

    def update(self):
        """Fetch updated information about devices"""

        if self.device_time_check():

            if not self.in_process:
                outlets, switches, fans = self.get_devices()

                self.outlets = helpers.resolve_updates(self.outlets, outlets)
                self.switches = helpers.resolve_updates(
                    self.switches, switches)
                self.fans = helpers.resolve_updates(self.fans, fans)

                self.last_update_ts = time.time()

    def update_energy(self):
        """Fetch updated energy information about devices"""
        for outlet in self.outlets:
            outlet.update_energy()
