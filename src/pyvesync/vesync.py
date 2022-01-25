"""VeSync API Device Libary."""

import logging
import re
import time
from itertools import chain
from collections import defaultdict
from typing import List, Dict, DefaultDict, Union, Any, Type

from pyvesync.helpers import Helpers
from pyvesync.vesyncbasedevice import VeSyncBaseDevice
from pyvesync.vesyncbulb import VeSyncBulbESL100, VeSyncBulbESL100CW
from pyvesync.vesyncfan import (
    VeSyncAir131,
    VeSyncHumid200300S,
    VeSyncAir200S,
    VeSyncAir300S400S,
)
from pyvesync.vesyncoutlet import (
    VeSyncOutlet7A,
    VeSyncOutlet10A,
    VeSyncOutlet15A,
    VeSyncOutdoorPlug,
)
from pyvesync.vesyncswitch import VeSyncWallSwitch, VeSyncDimmerSwitch

logger = logging.getLogger(__name__)

API_RATE_LIMIT: int = 30
DEFAULT_TZ: str = 'America/New_York'

DEFAULT_ENER_UP_INT: int = 21600

# Class dictionary based on device type

_DEVICE_CLASS: Dict[str, Type[VeSyncBaseDevice]] = {
    'wifi-switch-1.3': VeSyncOutlet7A,
    'ESW03-USA': VeSyncOutlet10A,
    'ESW01-EU': VeSyncOutlet10A,
    'ESW15-USA': VeSyncOutlet15A,
    'ESWL01': VeSyncWallSwitch,
    'ESWL03': VeSyncWallSwitch,
    'LV-PUR131S': VeSyncAir131,
    'ESO15-TB': VeSyncOutdoorPlug,
    'ESL100': VeSyncBulbESL100,
    'ESL100CW': VeSyncBulbESL100CW,
    'ESWD16': VeSyncDimmerSwitch,
    'Classic200S': VeSyncHumid200300S,
    'Classic300S': VeSyncHumid200300S,
    'Dual200S': VeSyncHumid200300S,
    'Core200S': VeSyncAir200S,
    'Core300S': VeSyncAir300S400S,
    'Core400S': VeSyncAir300S400S,
    'LUH-D301S-WEU': VeSyncHumid200300S,
    'LAP-C201S-AUSR': VeSyncAir200S,
    'LAP-C401S-WUSR': VeSyncAir300S400S,
}

_DEVICE_TYPES_DICT: Dict[str, List[str]] = dict(
    outlets=['wifi-switch-1.3', 'ESW03-USA',
             'ESW01-EU', 'ESW15-USA', 'ESO15-TB'],
    switches=['ESWL01', 'ESWL03', 'ESWD16'],
    fans=['LV-PUR131S', 'Classic200S', 'Classic300S', 'Core200S',
          'Core300S', 'Core400S', 'Dual200S',
          'LUH-D301S-WEU', 'LAP-C201S-AUSR', 'LAP-C401S-WUSR'],
    bulbs=['ESL100', 'ESL100CW'],
)

_DEVICE_TYPES: DefaultDict[str, list] = defaultdict(list, _DEVICE_TYPES_DICT)


def _device_builder(device_type: str,
                    config: Dict[str, Union[str, int, float, None]],
                    manager) -> Any:
    """Build instantiated device objects from name."""
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
            reg_test = r'[^a-zA-Z/_]'
            if bool(re.search(reg_test, time_zone)):
                self.time_zone = DEFAULT_TZ
                logger.debug('Invalid characters in time zone - %s',
                             time_zone)
            else:
                self.time_zone = time_zone
        else:
            self.time_zone = DEFAULT_TZ
            logger.debug('Time zone is not a string')

    @property
    def energy_update_interval(self) -> int:
        """Return energy update interval."""
        return self._energy_update_interval

    @energy_update_interval.setter
    def energy_update_interval(self, new_energy_update: int) -> None:
        """Set energy update interval in seconds."""
        if new_energy_update > 0:
            self._energy_update_interval = new_energy_update

    @staticmethod
    def remove_dev_test(device, new_list: list) -> bool:
        """Test if device should be removed - False = Remove."""
        if isinstance(new_list, list) and device.cid:
            for item in new_list:
                device_found = False
                if 'cid' in item:
                    if device.cid == item['cid']:
                        device_found = True
                        break
                else:
                    logger.debug('No cid found in - %s', str(item))
            if not device_found:
                logger.debug(
                    'Device removed - %s - %s',
                    device.device_name, device.device_type
                )
                return False
        return True

    def add_dev_test(self, new_dev: dict) -> bool:
        """Test if new device should be added - True = Add."""
        if 'cid' in new_dev:
            for _, v in self._dev_list.items():
                for dev in v:
                    if (
                        dev.cid == new_dev.get('cid')
                        and new_dev.get('subDeviceNo', 0) == dev.sub_device_no
                    ):
                        return False
        return True

    def remove_old_devices(self, devices: list) -> bool:
        """Remove devices not found in device list return."""
        for k, v in self._dev_list.items():
            before = len(v)
            v[:] = [x for x in v if self.remove_dev_test(x, devices)]
            after = len(v)
            if before != after:
                logger.debug('%s %s removed', str((before - after)), k)
        return True

    @staticmethod
    def set_dev_id(devices: list) -> list:
        """Correct devices without cid or uuid."""
        dev_num = 0
        dev_rem = []
        for dev in devices:
            if dev.get('cid') is None:
                if dev.get('macID') is not None:
                    dev['cid'] = dev['macID']
                elif dev.get('uuid') is not None:
                    dev['cid'] = dev['uuid']
                else:
                    dev_rem.append(dev_num)
                    logger.warning('Device with no ID  - %s',
                                   dev.get('deviceName'))
            dev_num += 1
            if dev_rem:
                devices = [i for j, i in enumerate(
                            devices) if j not in dev_rem]
        return devices

    def process_devices(self, dev_list: list) -> bool:
        """Instantiate Device Objects."""
        devices = VeSync.set_dev_id(dev_list)

        num_devices = 0
        for _, v in self._dev_list.items():
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

    def get_devices(self) -> bool:
        """Return tuple listing outlets, switches, and fans of devices."""
        if not self.enabled:
            return False

        self.in_process = True
        proc_return = False
        response, _ = Helpers.call_api(
            '/cloud/v1/deviceManaged/devices',
            'post',
            headers=Helpers.req_headers(self),
            json=Helpers.req_body(self, 'devicelist'),
        )

        if response and Helpers.code_check(response):
            if 'result' in response and 'list' in response['result']:
                device_list = response['result']['list']

                proc_return = self.process_devices(device_list)
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

        response, _ = Helpers.call_api(
            '/cloud/v1/user/login', 'post',
            json=Helpers.req_body(self, 'login')
        )

        if Helpers.code_check(response) and 'result' in response:
            self.token = response.get('result').get('token')
            self.account_id = response.get('result').get('accountID')
            self.enabled = True

            return True
        logger.error('Error logging in with username and password')
        return False

    def device_time_check(self) -> bool:
        """Test if update interval has been exceeded."""
        if (
            self.last_update_ts is None
            or (time.time() - self.last_update_ts) > self.update_interval
        ):
            return True
        return False

    def update(self) -> None:
        """Fetch updated information about devices."""
        if self.device_time_check():

            if not self.enabled:
                logger.error('Not logged in to VeSync')
                return
            self.get_devices()

            devices = list(self._dev_list.values())

            for device in chain(*devices):
                device.update()

            self.last_update_ts = time.time()

    def update_energy(self, bypass_check=False) -> None:
        """Fetch updated energy information about devices."""
        if self.outlets:
            for outlet in self.outlets:
                outlet.update_energy(bypass_check)

    def update_all_devices(self) -> None:
        """Run get_details() for each device."""
        devices = list(self._dev_list.keys())
        for dev in chain(*devices):
            dev.get_details()
