"""VeSync API Device Libary."""

import logging
import time
import re
from ast import literal_eval
from itertools import chain
from pyvesync.helpers import Helpers as helpers
from pyvesync.vesyncoutlet import (VeSyncOutlet7A, VeSyncOutlet10A,
                                   VeSyncOutlet15A, VeSyncOutdoorPlug)
from pyvesync.vesyncswitch import VeSyncWallSwitch, VeSyncDimmerSwitch
from pyvesync.vesyncfan import VeSyncAir131
from pyvesync.vesyncbulb import VeSyncBulbESL100, VeSyncBulbESL100CW

logger = logging.getLogger(__name__)

API_RATE_LIMIT = 30
DEFAULT_TZ = 'America/New_York'

DEFAULT_ENER_UP_INT = 21600

# Class dictionary based on device type
_DEVICE_CLASS = {
    'wifi-switch-1.3': VeSyncOutlet7A,
    'ESW03-USA': VeSyncOutlet7A,
    'ESW01-EU': VeSyncOutlet10A,
    'ESW15-USA': VeSyncOutlet15A,
    'ESWL01': VeSyncWallSwitch,
    'ESWL03': VeSyncWallSwitch,
    'LV-PUR131S': VeSyncAir131,
    'ESO15-TB': VeSyncOutdoorPlug,
    'ESL100': VeSyncBulbESL100,
    'ESL100CW': VeSyncBulbESL100CW,
    'ESWD16': VeSyncDimmerSwitch
}

_DEVICE_TYPES = {
    'outlets': ['wifi-switch-1.3', 'ESW03-USA', 'ESW01-EU', 'ESW15-USA', 'ESO15-TB'],
    'switches': ['ESWL01', 'ESWL03', 'ESWD16'],
    'fans': ['LV-PUR131S'],
    'bulbs': ['ESL100', 'ESL100CW']
}


def _device_builder(device_type: str, config: dict, manager):
    """Build instantiated device objects from name"""
    device_name = _DEVICE_CLASS.get(device_type)
    if device_name:
        return device_name(config, manager)
    logger.debug('Unknown device found - %s', device_type)
    return None


class VeSync:
    """VeSync API functions."""

    def __init__(self, username, password, time_zone=DEFAULT_TZ):
        """Initialize VeSync class with username, password and time zone."""
        self.username = username
        self.password = password
        self.token = None
        self.account_id = None
        self.devices = None
        self.enabled = False
        self.update_interval = API_RATE_LIMIT
        self.last_update_ts = None
        self.in_process = False
        self._energy_update_interval = DEFAULT_ENER_UP_INT
        self._energy_check = True
        self._dev_list = {}
        self.outlets = []
        self.switches = []
        self.fans = []
        self.bulbs = []
        self.scales = []

        for dt in _DEVICE_TYPES:
            self._dev_list[dt] = getattr(self, dt)

        if isinstance(time_zone, str) and time_zone:
            reg_test = r"[^a-zA-Z/_]"
            if bool(re.search(reg_test, time_zone)):
                self.time_zone = DEFAULT_TZ
                logger.debug("Invalid characters in time zone - %s", time_zone)
            else:
                self.time_zone = time_zone
        else:
            self.time_zone = DEFAULT_TZ
            logger.debug("Time zone is not a string")

    @property
    def energy_update_interval(self) -> int:
        """Return energy update interval."""
        return self._energy_update_interval

    @energy_update_interval.setter
    def energy_update_interval(self, new_energy_update):
        """Set energy update interval in seconds."""
        if new_energy_update > 0:
            self._energy_update_interval = new_energy_update

    @staticmethod
    def remove_dev_test(device, new_list: list) -> bool:
        """Test if device should be removed - False = Remove."""
        if isinstance(new_list, list) and device.cid:
            device_found = False
            for item in new_list:
                device_found = False
                if 'cid' in item:
                    if device.cid == item['cid']:
                        device_found = True
                        break
                else:
                    logger.error('No cid found in - %s', str(item))
            if not device_found:
                logger.debug("Device removed - %s - %s",
                             device.device_name, device.device_type)
                return False
        return True

    def add_dev_test(self, new_dev):
        """Test if new device should be added - True = Add."""
        if 'cid' in new_dev:
            for k, v in self._dev_list.items():
                for dev in v:
                    if dev.cid == new_dev.get(
                            'cid') and new_dev.get(
                            'subDeviceNo', 0) == dev.sub_device_no:
                        return False
        return True

    def remove_old_devices(self, devices):
        """Removes devices not found in device list return."""
        for k, v in self._dev_list.items():
            before = len(v)
            v[:] = [x for x in v if self.remove_dev_test(
                x, devices)]
            after = len(v)
            if before != after:
                logger.debug('%s %s removed', str((before-after)), k)
        return True

    def process_devices(self, devices: list) -> bool:
        """Instantiate Device Objects."""
        for d in devices:
            if d.get('cid') is None:
                if d.get('macID') is not None:
                    d['cid'] = d['macID']

                else:
                    logger.warning('Device with no ID  - %s',
                                   d.get('deviceName'))

        num_devices = 0
        for k, v in self._dev_list.items():
            if isinstance(v, list):
                num_devices += len(v)
            else:
                num_devices += 1

        if not devices:
            logger.warning('No devices found in api return')
            return False
        if num_devices == 0:
            logger.debug('New device list initialized')
        else:
            self.remove_old_devices(devices)

        devices[:] = [x for x in devices if self.add_dev_test(x)]

        detail_keys = ['deviceType', 'deviceName', 'deviceStatus']
        for dev in devices:
            if not all(k in dev for k in detail_keys):
                logger.debug('Error adding device')
                continue
            dev_type = dev.get('deviceType')
            for dt, v in self._dev_list.items():
                if dev_type in _DEVICE_TYPES.get(dt, []):
                    v.append(_device_builder(dev_type, dev, self))
        return True

    def get_devices(self):
        """Return tuple listing outlets, switches, and fans of devices."""
        outlets = []
        switches = []
        fans = []
        bulbs = []
        if not self.enabled:
            return

        self.in_process = True
        proc_return = False
        response, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/devices',
            'post',
            headers=helpers.req_headers(self),
            json=helpers.req_body(self, 'devicelist')
        )

        if response and helpers.code_check(response):
            if 'result' in response and 'list' in response['result']:
                device_list = response['result']['list']

                proc_return = self.process_devices(
                    device_list)
            else:
                logger.error('Device list in response not found')
        else:
            logger.warning('Error retrieving device list')

        self.in_process = False

        return proc_return

    def login(self) -> bool:
        """Return True if log in request succeeds."""
        user_check = isinstance(self.username, str) and len(self.username) > 0
        pass_check = isinstance(self.password, str) and len(self.password) > 0
        if user_check is False:
            logger.error('Username invalid')
            return False
        if pass_check is False:
            logger.error('Password invalid')
            return False

        response, _ = helpers.call_api(
            '/cloud/v1/user/login',
            'post',
            json=helpers.req_body(self, 'login')
        )

        if helpers.code_check(response) and 'result' in response:
            self.token = response.get('result').get('token')
            self.account_id = response.get('result').get('accountID')
            self.enabled = True

            return True
        logger.error('Error logging in with username and password')
        return False

    def device_time_check(self) -> bool:
        """Test if update interval has been exceeded."""
        if self.last_update_ts is None or (
                time.time() - self.last_update_ts) > self.update_interval:
            return True
        return False

    def update(self):
        """Fetch updated information about devices."""

        if self.device_time_check():

            if not self.enabled:
                logger.error('Not logged in to VeSync')
                return
            get_dev = self.get_devices()

            devices = [[i for i in self._dev_list[x]] for x in self._dev_list.keys()]

            [device.update() for device in chain(*devices)]

            self.last_update_ts = time.time()

    def update_energy(self, bypass_check=False):
        """Fetch updated energy information about devices."""
        if self.outlets:
            for outlet in self.outlets:
                outlet.update_energy(bypass_check)

    def update_all_devices(self):
        """Run get_details() for each device."""
        devices = [[i for i in self._dev_list[x]] for x in self._dev_list.keys()]
        for dev in chain(*devices):
            dev.get_details()
