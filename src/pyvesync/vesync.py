"""VeSync API Device Libary."""

import logging
import time
import re
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


def get_device(device_type, config, manager):
    """Return initilized device from API response."""
    if device_type == 'wifi-switch-1.3':
        return VeSyncOutlet7A(config, manager)
    if device_type in ['ESW03-USA', 'ESW01-EU']:
        return VeSyncOutlet10A(config, manager)
    if device_type == 'ESW15-USA':
        return VeSyncOutlet15A(config, manager)
    if device_type in ['ESWL01', 'ESWL03']:
        return VeSyncWallSwitch(config, manager)
    if device_type == 'LV-PUR131S':
        return VeSyncAir131(config, manager)
    if device_type == 'ESO15-TB':
        return VeSyncOutdoorPlug(config, manager)
    if device_type == 'ESL100':
        return VeSyncBulbESL100(config, manager)
    if device_type == 'ESL100CW':
        return VeSyncBulbESL100CW(config, manager)
    if device_type == 'ESWD16':
        return VeSyncDimmerSwitch(config, manager)
    logger.debug('Unknown device found - %s', device_type)
    return None


class VeSync:
    """VeSync API functions."""

    def __init__(self, username, password, time_zone=DEFAULT_TZ):
        """Initilize VeSync class with username, password and time zone."""
        self.username = username
        self.password = password
        self.token = None
        self.account_id = None
        self.devices = None
        self.outlets = []
        self.switches = []
        self.fans = []
        self.bulbs = []
        self.enabled = False
        self.update_interval = API_RATE_LIMIT
        self.last_update_ts = None
        self.in_process = False
        self._energy_update_interval = DEFAULT_ENER_UP_INT
        self._energy_check = True

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
    def remove_dev_test(device, new_list):
        """Test if device should be removed - False = Remove."""
        if isinstance(new_list, list) and device.cid:
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
            devices = [self.outlets, self.bulbs, self.switches, self.fans]
            was_found = False
            for dev in chain(*devices):
                if dev.cid == new_dev.get('cid') and\
                        new_dev.get('subDeviceNo', 0) == dev.sub_device_no:
                    was_found = True
                    break
            if not was_found:
                logger.debug("Adding device - %s", new_dev)
                return True
        return False

    def process_devices(self, devices) -> tuple:
        """Call VSFactory to instantiate device classes."""
        outlets = []
        switches = []
        fans = []
        bulbs = []

        outlet_types = [
            'wifi-switch-1.3', 'ESW03-USA', 'ESW01-EU', 'ESW15-USA', 'ESO15-TB'
        ]
        switch_types = ['ESWL01', 'ESWL03', 'ESWD16']
        fan_types = ['LV-PUR131S']
        bulb_types = ['ESL100', 'ESL100CW']

        num_devices = len(self.outlets) + len(self.switches) + len(self.fans) \
            + len(self.bulbs)

        if not num_devices and devices:
            logger.debug('New device list initialized')
        elif not devices:
            logger.warning('No devices found in api return')
        else:
            self.outlets[:] = [x for x in self.outlets if self.remove_dev_test(
                x, devices)]
            for dev in self.outlets:
                logger.debug('Outlets updated - %s', str(dev))

            self.fans[:] = [x for x in self.fans if self.remove_dev_test(
                x, devices)]
            for dev in self.fans:
                logger.debug('Fans Updated - %s', str(dev))

            self.switches[:] = [x for x in self.switches if
                                self.remove_dev_test(x, devices)]
            for dev in self.switches:
                logger.debug('Switches Updated - %s', str(dev))

            self.bulbs[:] = [x for x in self.bulbs if self.remove_dev_test(
                x, devices)]
            for dev in self.bulbs:
                logger.debug('Bulbs - %s', str(dev))

            devices[:] = [x for x in devices if self.add_dev_test(x)]

        for dev in devices:
            detail_keys = ['deviceType', 'deviceName', 'deviceStatus']
            if all(k in dev for k in detail_keys):
                dev_type = dev['deviceType']
                if dev_type in outlet_types:
                    outlets.append(get_device(dev_type, dev, self))
                elif dev_type in fan_types:
                    fans.append(get_device(dev_type, dev, self))
                elif dev_type in switch_types:
                    switches.append(get_device(dev_type, dev, self))
                elif dev_type in bulb_types:
                    bulbs.append(get_device(dev_type, dev, self))
                else:
                    logger.warning('Unknown device %s', dev_type)
            else:
                logger.error('Details keys not found %s', str(dev))

        return outlets, switches, fans, bulbs

    def get_devices(self) -> tuple:
        """Return tuple listing outlets, switches, and fans of devices."""
        outlets = []
        switches = []
        fans = []
        bulbs = []
        if not self.enabled:
            return None

        self.in_process = True

        response, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/devices',
            'post',
            headers=helpers.req_headers(self),
            json=helpers.req_body(self, 'devicelist')
        )

        if response and helpers.code_check(response):
            if 'result' in response and 'list' in response['result']:
                device_list = response['result']['list']
                outlets, switches, fans, bulbs = self.process_devices(
                    device_list)
            else:
                logger.error('Device list in response not found')
        else:
            logger.warning('Error retrieving device list')

        self.in_process = False

        return (outlets, switches, fans, bulbs)

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

            if not self.in_process and self.enabled:
                outlets, switches, fans, bulbs = self.get_devices()

                self.outlets.extend(outlets)
                self.switches.extend(switches)
                self.fans.extend(fans)
                self.bulbs.extend(bulbs)

                devices = [self.outlets, self.bulbs, self.switches, self.fans]

                [device.update() for device in chain(*devices)]

                self.last_update_ts = time.time()
            else:
                logger.error('You are not logged in to VeSync')

    def update_energy(self, bypass_check=False):
        """Fetch updated energy information about devices."""
        for outlet in self.outlets:
            outlet.update_energy(bypass_check)

    def update_all_devices(self):
        """Run get_details() for each device."""
        dev_list = [self.outlets, self.fans, self.bulbs, self.switches]
        for dev in chain(*dev_list):
            dev.get_details()
