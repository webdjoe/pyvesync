"""VeSync API Device Libary."""

import logging
import re
import time
from itertools import chain
from typing import Any, TYPE_CHECKING, Optional
from aiohttp import ClientSession
from pyvesync.helpers import Helpers
import pyvesync.vesyncbulb as bulb_mods
import pyvesync.vesyncfan as fan_mods
import pyvesync.vesyncoutlet as outlet_mods
import pyvesync.vesynckitchen as kitchen_mods
import pyvesync.vesyncswitch as switch_mods
from pyvesync.logs import LibraryLogger, VesyncLoginError

if TYPE_CHECKING:
    from pyvesync.vesyncbasedevice import VeSyncBaseDevice  # ignore=F401

logger = logging.getLogger(__name__)

API_RATE_LIMIT: int = 30
DEFAULT_TZ: str = 'America/New_York'

DEFAULT_ENER_UP_INT: int = 21600


def object_factory(dev_model: str,
                   config: dict,
                   manager: 'VeSync') -> tuple[str, Optional['VeSyncBaseDevice']]:
    """Get device type and instantiate class.

    Pulls the device types from each module to determine the type of device and
    instantiates the device object.

    Args:
        dev_model (str): Device model type returned from API
        config (dict): Device configuration from `VeSync.get_devices()` API call
        manager (VeSync): VeSync manager object

    Returns:
        Tuple[str, VeSyncBaseDevice]: Tuple of device type classification and
        instantiated device object

    Note:
        Device types are pulled from the `*_mods` attribute of each device module.
        See [pyvesync.vesyncbulb.bulb_mods], [pyvesync.vesyncfan.fan_mods],
        [pyvesync.vesyncoutlet.outlet_mods], [pyvesync.vesyncswitch.switch_mods],
        and [pyvesync.vesynckitchen.kitchen_mods] for more information.
    """
    device_handler: dict[str, dict[str, Any]] = {
        'fans': {'device_dict': fan_mods.fan_modules, 'device_module': fan_mods},
        'outlets': {
            'device_dict': outlet_mods.outlet_modules,
            'device_module': outlet_mods,
        },
        'switches': {
            'device_dict': switch_mods.switch_modules,
            'device_module': switch_mods,
        },
        'bulbs': {'device_dict': bulb_mods.bulb_modules, 'device_module': bulb_mods},
        'kitchen': {
            'device_dict': kitchen_mods.kitchen_modules,
            'device_module': kitchen_mods,
        },
    }

    for key, type_dict in device_handler.items():
        if dev_model in type_dict['device_dict']:
            device_type = key
            dev_object = getattr(
                type_dict['device_module'], type_dict['device_dict'][dev_model]
            )
            return device_type, dev_object(config, manager)

    logger.debug(
        'Unknown device named %s model %s',
        config.get('deviceName', ''),
        config.get('deviceType', ''),
    )
    return 'unknown', None


class VeSync:  # pylint: disable=function-redefined
    """VeSync Manager Class."""

    def __init__(self,
                 username: str,
                 password: str,
                 session: ClientSession | None = None,
                 time_zone: str = DEFAULT_TZ,
                 debug: bool = False,
                 redact: bool = True) -> None:
        """Initialize VeSync Manager.

        This class is used as the manager for all VeSync objects, all methods and
        API calls are performed from this class. Time zone, debug and redact are
        optional. Time zone must be a string of an IANA time zone format. Once
        class is instantiated, call `manager.login()` to log in to VeSync servers,
        which returns `True` if successful. Once logged in, call `manager.update()`
        to retrieve devices and update device details.

        Parameters:
            username : str
                VeSync account username (usually email address)
            password : str
                VeSync account password
            time_zone : str, optional
                Time zone for device from IANA database, by default DEFAULT_TZ
            debug : bool, optional
                Enable debug logging, by default False
            redact : bool, optional
                Redact sensitive information in logs, by default True

        Attributes:
            session : ClientSession
                Client session for API calls
            fans : list
                List of VeSyncFan objects for humidifiers and air purifiers
            outlets : list
                List of VeSyncOutlet objects for smart plugs
            switches : list
                List of VeSyncSwitch objects for wall switches
            bulbs : list
                List of VeSyncBulb objects for smart bulbs
            kitchen : list
                List of VeSyncKitchen objects for smart kitchen appliances
            dev_list : dict
                Dictionary of device lists
            token : str
                VeSync API token
            account_id : str
                VeSync account ID
            enabled : bool
                True if logged in to VeSync, False if not
        """
        self.session = session
        self.debug = debug
        self._redact = redact
        if redact:
            self.redact = redact
        self.username: str = username
        self.password: str = password
        self.token: str | None = None
        self.account_id: str | None = None
        self.country_code: str | None = None
        self.enabled = False
        self.update_interval = API_RATE_LIMIT
        self.last_update_ts: float | None = None
        self.in_process = False
        self._energy_update_interval = DEFAULT_ENER_UP_INT
        self._energy_check = True
        self.outlets: list[VeSyncBaseDevice] = []
        self.switches: list[VeSyncBaseDevice] = []
        self.fans: list[VeSyncBaseDevice] = []
        self.bulbs: list[VeSyncBaseDevice] = []
        self.scales: list[VeSyncBaseDevice] = []
        self.kitchen: list[VeSyncBaseDevice] = []

        self._dev_list = {
            'fans': self.fans,
            'outlets': self.outlets,
            'switches': self.switches,
            'bulbs': self.bulbs,
            'kitchen': self.kitchen
        }
        self.time_zone: str
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
        if new_flag:
            LibraryLogger.configure_logger(logging.DEBUG)
        else:
            LibraryLogger.configure_logger(logging.WARNING)
        self._debug = new_flag

    @property
    def redact(self) -> bool:
        """Return debug flag."""
        return self._redact

    @redact.setter
    def redact(self, new_flag: bool) -> None:
        """Set debug flag."""
        if new_flag:
            LibraryLogger.shouldredact = True
        elif new_flag is False:
            LibraryLogger.shouldredact = False
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

    def _remove_stale_devices(self, devices: list) -> None:
        """Remove devices not found in device list return."""
        new_dev_ids = {dev['cid'] for dev in devices}

        # FIX THIS HACK - cannot modify _dev_list keys from instance attributes
        dev_obj_list = {
            "outlets": self.outlets,
            "switches": self.switches,
            "fans": self.fans,
            "bulbs": self.bulbs,
            "kitchen": self.kitchen
        }

        before = len(list(chain(*dev_obj_list)))
        after = 0
        for attr_name, obj_list in dev_obj_list.items():
            obj_list[:] = [dev for dev in obj_list if dev.cid in new_dev_ids]
            setattr(self, attr_name, obj_list)
            after += len(obj_list)
        if before != after:
            logger.debug('%s removed', str(before - after))

    def _find_new_devices(self, devices: list) -> list:
        """Filter return list API for devices not in instance."""
        dev_obj_list = {
            "outlets": self.outlets,
            "switches": self.switches,
            "fans": self.fans,
            "bulbs": self.bulbs,
            "kitchen": self.kitchen
        }
        current_ids = {dev.cid for dev in chain(*dev_obj_list.values())}
        return [dev for dev in devices if dev.get('cid') not in current_ids]

    @staticmethod
    def set_dev_id(devices: list) -> list:
        """Correct devices without cid or uuid."""
        clean_devices: list[dict[str, str | int]] = []
        for d in devices:
            d["cid"] = d.get("cid") or next(
                (d.get(k) for k in ["macid", "uuid"] if d.get(k)), None)
            if d.get("cid") is not None:
                clean_devices.append(d)
            else:
                logger.debug('Device without cid, uuid, or macid found %s',
                             d.get("deviceName"))
        return clean_devices

    def process_devices(self, dev_list: list) -> bool:
        """Instantiate Device Objects.

        Internal method run by `get_devices()` to instantiate device objects.

        """
        devices = self.set_dev_id(dev_list)
        if not devices:
            logger.warning('No devices found in api return')
            return False

        cur_dev_count = len(list(chain(*self._dev_list.values())))

        if cur_dev_count == 0:
            logger.debug('New device list initialized')
        else:
            self._remove_stale_devices(devices)

        new_devices = self._find_new_devices(devices)

        # Will be handled by validation
        # detail_keys = ['deviceType', 'deviceName', 'deviceStatus']
        for dev in new_devices:
            # if not all(k in dev for k in detail_keys):
            #     logger.debug('Error adding device')
            #     continue
            dev_type = dev.get('deviceType')
            if dev_type is None:
                logger.debug('Error adding device - Device without deviceType found')
                continue
            device_str, device_obj = object_factory(dev_type, dev, self)
            device_list = getattr(self, device_str, None)
            if device_list is not None and device_obj is not None:
                device_list.append(device_obj)
            else:
                logger.debug('Error adding device %s', dev_type)
            continue

        return True

    def get_devices(self) -> bool:
        """Return tuple listing outlets, switches, and fans of devices.

        This is an internal method called by `update()`
        """
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
        """Log into VeSync server.

        Username and password are provided when class is instantiated.

        Returns:
            True if login successful, False if not

        Raises:
            VesyncLoginError: If login fails
        """
        if not isinstance(self.username, str) or len(self.username) == 0 \
                or not isinstance(self.password, str) or len(self.password) == 0:
            raise VesyncLoginError('Invalid username or password')

        response, _ = Helpers.call_api(
            '/cloud/v1/user/login', 'post',
            json_object=Helpers.req_body(self, 'login')
        )

        if isinstance(response, dict) and response.get('code') == 0:
            self.token = response.get('result', {}).get('token')
            self.account_id = response.get('result', {}).get('accountID')
            self.country_code = response.get('result', {}).get('countryCode')
            self.enabled = True
            logger.debug('Login successful')
            return True
        if isinstance(response, dict) and isinstance(response.get('msg'), str):
            message = response['msg']
        else:
            message = 'Unknown error logging in'
        raise VesyncLoginError(message)

    def device_time_check(self) -> bool:
        """Test if update interval has been exceeded."""
        return (
            self.last_update_ts is None
            or (time.time() - self.last_update_ts) > self.update_interval
        )

    def update(self) -> None:
        """Fetch updated information about devices.

        Pulls devices list from VeSync and instantiates any new devices. Devices
        are stored in the instance attributes `outlets`, `switches`, `fans`, and
        `bulbs`. The `_device_list` attribute is a dictionary of these attributes.
        """
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

    def update_energy(self, bypass_check: bool = False) -> None:
        """Fetch updated energy information for outlet devices."""
        if self.outlets:
            for outlet in self.outlets:
                if isinstance(outlet, outlet_mods.VeSyncOutlet):
                    outlet.update_energy(bypass_check)

    def update_all_devices(self) -> None:
        """Run `get_details()` for each device and update state."""
        devices = list(self._dev_list.values())
        for dev in chain(*devices):
            dev.update()
