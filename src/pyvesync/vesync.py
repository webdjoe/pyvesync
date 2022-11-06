"""VeSync API Device Libary."""

import logging
import re
import time
from itertools import chain
from typing import Tuple
from pyvesync.helpers import Helpers
import pyvesync.helpers as helpermodule
from pyvesync.vesyncbasedevice import VeSyncBaseDevice
from pyvesync.vesyncbulb import *   # noqa: F403, F401
import pyvesync.vesyncbulb as bulb_mods
from pyvesync.vesyncfan import *   # noqa: F403, F401
import pyvesync.vesyncfan as fan_mods
from pyvesync.vesyncoutlet import *   # noqa: F403, F401
import pyvesync.vesyncoutlet as outlet_mods
from pyvesync.vesyncswitch import *   # noqa: F403, F401
import pyvesync.vesynckitchen as kitchen_mods
import pyvesync.vesyncswitch as switch_mods

logger = logging.getLogger(__name__)

API_RATE_LIMIT: int = 30
DEFAULT_TZ: str = 'America/New_York'

DEFAULT_ENER_UP_INT: int = 21600


def object_factory(dev_type, config, manager) -> Tuple[str, VeSyncBaseDevice]:
    """Get device type and instantiate class."""
    def fans(dev_type, config, manager):
        fan_cls = fan_mods.fan_modules[dev_type]  # noqa: F405
        fan_obj = getattr(fan_mods, fan_cls)
        return 'fans', fan_obj(config, manager)

    def outlets(dev_type, config, manager):
        outlet_cls = outlet_mods.outlet_modules[dev_type]  # noqa: F405
        outlet_obj = getattr(outlet_mods, outlet_cls)
        return 'outlets', outlet_obj(config, manager)

    def switches(dev_type, config, manager):
        switch_cls = switch_mods.switch_modules[dev_type]  # noqa: F405
        switch_obj = getattr(switch_mods, switch_cls)
        return 'switches', switch_obj(config, manager)

    def bulbs(dev_type, config, manager):
        bulb_cls = bulb_mods.bulb_modules[dev_type]  # noqa: F405
        bulb_obj = getattr(bulb_mods, bulb_cls)
        return 'bulbs', bulb_obj(config, manager)

    def kitchen(dev_type, config, manager):
        kitchen_cls = kitchen_mods.kitchen_modules[dev_type]
        kitchen_obj = getattr(kitchen_mods, kitchen_cls)
        return 'kitchen', kitchen_obj(config, manager)

    if dev_type in fan_mods.fan_modules:  # type: ignore  # noqa: F405
        type_str, dev_obj = fans(dev_type, config, manager)
    elif dev_type in outlet_mods.outlet_modules:  # type: ignore  # noqa: F405
        type_str, dev_obj = outlets(dev_type, config, manager)
    elif dev_type in switch_mods.switch_modules:  # type: ignore  # noqa: F405
        type_str, dev_obj = switches(dev_type, config, manager)
    elif dev_type in bulb_mods.bulb_modules:  # type: ignore  # noqa: F405
        type_str, dev_obj = bulbs(dev_type, config, manager)
    elif dev_type in kitchen_mods.kitchen_modules:
        type_str, dev_obj = kitchen(dev_type, config, manager)
    else:
        logger.debug('Unknown device named %s model %s',
                     config.get('deviceName', ''),
                     config.get('deviceType', '')
                     )
        type_str = 'unknown'
        dev_obj = None
    return type_str, dev_obj


class VeSync:  # pylint: disable=function-redefined
    """VeSync API functions."""

    def __init__(self, username, password, time_zone=DEFAULT_TZ,
                 debug=False, redact=True):
        """Initialize VeSync class with username, password and time zone."""
        self.debug = debug
        if debug:  # pragma: no cover
            logger.setLevel(logging.DEBUG)
            bulb_mods.logger.setLevel(logging.DEBUG)
            switch_mods.logger.setLevel(logging.DEBUG)
            outlet_mods.logger.setLevel(logging.DEBUG)
            fan_mods.logger.setLevel(logging.DEBUG)
            helpermodule.logger.setLevel(logging.DEBUG)
            kitchen_mods.logger.setLevel(logging.DEBUG)
        self._redact = redact
        if redact:
            self.redact = redact
        self.username = username
        self.password = password
        self.token = None
        self.account_id = None
        self.country_code = None
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
        self.kitchen = []

        self._dev_list = {
            'fans': self.fans,
            'outlets': self.outlets,
            'switches': self.switches,
            'bulbs': self.bulbs,
            'kitchen': self.kitchen
        }

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
    def debug(self) -> bool:
        """Return debug flag."""
        return self._debug

    @debug.setter
    def debug(self, new_flag: bool) -> None:
        """Set debug flag."""
        log_modules = [bulb_mods,
                       switch_mods,
                       outlet_mods,
                       fan_mods,
                       helpermodule]
        if new_flag:
            logger.setLevel(logging.DEBUG)
            for m in log_modules:
                m.logger.setLevel(logging.DEBUG)
        elif new_flag is False:
            logger.setLevel(logging.WARNING)
            for m in log_modules:
                m.logger.setLevel(logging.WARNING)
        self._debug = new_flag

    @property
    def redact(self) -> bool:
        """Return debug flag."""
        return self._redact

    @redact.setter
    def redact(self, new_flag: bool) -> None:
        """Set debug flag."""
        if new_flag:
            Helpers.shouldredact = True
        elif new_flag is False:
            Helpers.shouldredact = False
        self._redact = new_flag

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
            try:
                device_str, device_obj = object_factory(dev_type, dev, self)
                device_list = getattr(self, device_str)
                device_list.append(device_obj)
            except AttributeError as err:
                logger.debug('Error - %s', err)
                logger.debug('%s device not added', dev_type)
                continue

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
            headers=Helpers.req_header_bypass(),
            json_object=Helpers.req_body(self, 'devicelist'),
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
            json_object=Helpers.req_body(self, 'login')
        )

        if Helpers.code_check(response) and 'result' in response:
            self.token = response.get('result').get('token')
            self.account_id = response.get('result').get('accountID')
            self.country_code = response.get('result').get('countryCode')
            self.enabled = True
            logger.debug('Login successful')
            logger.debug('token %s', self.token)
            logger.debug('account_id %s', self.account_id)

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

            logger.debug('Start updating the device details one by one')
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
