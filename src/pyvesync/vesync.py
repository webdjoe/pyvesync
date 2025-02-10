"""VeSync API Device Libary."""

import logging
import re
import time
from typing import List, Optional, Any,  Callable, Sequence

from .vesync_enums import EDeviceFamily
from .const import (
    API_RATE_LIMIT, DEFAULT_ENER_UP_INT, MOBILE_ID, USER_TYPE,
    APP_VERSION, PHONE_BRAND, PHONE_OS,
    DEFAULT_TZ, DEFAULT_REGION, BYPASS_HEADER_UA,
    ENERGY_WEEK, ENERGY_MONTH, ENERGY_YEAR,
)
from .helpers import Helpers, logger, REQUEST_T
from .logs import LibraryLogger, VesyncLoginError
from .vesyncbasedevice import VeSyncBaseDevice
from .vesyncbulb import factory as bulb_factory
from .vesyncfan import factory as fan_factory
from .vesynckitchen import factory as kitchen_factory
from .vesyncoutlet import factory as outlet_factory
from .vesyncswitch import factory as switch_factory

FACTORIES: Sequence[Callable] = [
    bulb_factory, fan_factory, kitchen_factory, outlet_factory, switch_factory
]


class VeSync:  # pylint: disable=function-redefined
    """VeSync Manager Class."""

    API_LOGIN = 'login'
    API_CONFIG = 'configurations'
    API_DEVICE_LIST = 'devices'
    API_DETAIL = 'devicedetail'
    API_STATUS = 'devicestatus'
    API_ENERGY = 'energy'
    API_BYPASS_V1 = 'bypass'
    API_BYPASS_V2 = 'bypassV2'
    API_FIRMWARE = 'firmwareUpdateInfo'

    _debug: bool
    _redact: bool
    username: str
    password: str
    token: Optional[str] = None
    account_id: Optional[str] = None
    country_code: Optional[str] = None
    enabled: float = False
    update_interval: int = API_RATE_LIMIT
    last_update_ts: Optional[float] = None
    in_process: bool = False
    _energy_update_interval: int = DEFAULT_ENER_UP_INT
    _energy_check: bool = True
    time_zone: str = DEFAULT_TZ

    def __init__(
            self,
            username: str,
            password: str,
            time_zone: str = DEFAULT_TZ,
            debug: bool = False,
            redact: bool = True
    ) -> None:
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
                List of VeSyncBaseDevice objects (all devices)
            token : str
                VeSync API token
            account_id : str
                VeSync account ID
            enabled : bool
                True if logged in to VeSync, False if not
        """
        self.debug = debug
        self.redact = redact
        self.username = username
        self.password = password
        self._device_list: list[VeSyncBaseDevice] = []

        if isinstance(time_zone, str) and time_zone:
            reg_test = r'[^a-zA-Z/_]'
            if bool(re.search(reg_test, time_zone)):
                logger.warning(
                    'Invalid characters in time zone %s - using default!',
                    time_zone
                )
            else:
                self.time_zone = time_zone
        else:
            logger.warning('Time zone is not a string - using default!')

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
            for dev in self._device_list:
                if (
                    dev.cid == new_dev.get('cid')
                    and new_dev.get('subDeviceNo', 0) == dev.sub_device_no
                ):
                    return False
        return True

    def remove_old_devices(self, devices: list) -> bool:
        """Remove devices not found in device list return."""
        before = len(self._device_list)
        self._device_list = [
            x
            for x in self._device_list
            if self.remove_dev_test(x, devices)
        ]
        after = len(self._device_list)
        if before != after:
            logger.debug('%s devices removed', str((before - after)))
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

    def object_factory(self, details: dict) -> VeSyncBaseDevice:
        """Get device type and instantiate class.

        Pulls the device types from each module to determine the type of device and
        instantiates the device object.

        Args:
            details (dict): Device configuration from `VeSync.get_devices()` API call

        Returns:
            VeSyncBaseDevice: instantiated device object or None for unsupported devices.

        Note:
            Each device type implements a factory for the supported device types.
            the newly created device instance is added to the device list.
        """
        dev_type = details.get('deviceType')
        dev_name = details.get('deviceName', '#MISS#')
        for factory in FACTORIES:
            try:
                device = factory(dev_type, details, self)
                if device:
                    self._device_list.append(device)
                    break
            except AttributeError as err:
                logger.debug(
                    'Error - %s: device %s(%s) not added',
                    err, dev_name, dev_type
                )

        if (device is None):
            logger.debug('Unknown device %s (%s) - not added!', dev_type, dev_name)

        return device

    def process_devices(self, dev_list: list) -> bool:
        """Instantiate Device Objects.

        Internal method run by `get_devices()` to instantiate device objects.

        """
        devices = VeSync.set_dev_id(dev_list)

        num_devices = len(devices)

        if not devices:
            logger.warning('No devices found in api return')
            return False
        if num_devices == 0:
            logger.debug('New device list initialized')
        else:
            self.remove_old_devices(devices)

        devices[:] = [x for x in devices if self.add_dev_test(x)]
        self._device_list = []
        detail_keys = ['deviceType', 'deviceName', 'deviceStatus']
        for dev_details in devices:
            if not all(k in dev_details for k in detail_keys):
                logger.debug('Error adding device')
                continue
            self.object_factory(dev_details)

        return True

    def get_devices(self) -> bool:
        """Return tuple listing outlets, switches, and fans of devices.

        This is an internal method called by `update()`
        """
        if not self.enabled:
            return False

        self.in_process = True

        proc_return = False
        r = Helpers.call_api(
            '/cloud/v1/deviceManaged/devices',
            method='post',
            headers=VeSync.req_header_bypass(),
            json_object=self.req_body_devices()
        )

        if Helpers.code_check(r):
            if (r is not None):
                if ('result' in r):
                    result = r['result']
                    if ('list' in result):
                        device_list = result['list']
                        proc_return = self.process_devices(device_list)
                    else:
                        logger.error('Device list in response not found')
                else:
                    logger.error('Device list in response not found')
            else:
                logger.error('Result in response not found')
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

        r = Helpers.call_api(
            '/cloud/v1/user/login',
            'post',
            json_object=self.req_body_login()
        )

        if Helpers.code_check(r):
            if (r is not None):
                if ('result' in r):
                    result: dict[str, Any] = r.get('result', {})
                    self.token = result.get('token')
                    self.account_id = result.get('accountID')
                    self.country_code = result.get('countryCode')
                    self.enabled = True
                    logger.debug('Login successful')
                    logger.debug('token %s', self.token)
                    logger.debug('account_id %s', self.account_id)
                    return True
        if isinstance(r, dict) and isinstance(r.get('msg'), str):
            message = r['msg']
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

            logger.debug('Start updating the device details one by one')
            self.update_all_devices()

            self.last_update_ts = time.time()

    def update_energy(self, bypass_check: bool = False) -> None:
        """Fetch updated energy information for outlet devices."""
        for outlet in self.outlets:
            outlet.update_energy(bypass_check)

    def update_all_devices(self) -> None:
        """Run `get_details()` for each device and update state."""
        for dev in self._device_list:
            dev.update()

    @property
    def bulbs(self) -> List[VeSyncBaseDevice]:
        """Returns a list of all registered bulbs."""
        return [
            dev
            for dev in self._device_list
            if dev.device_family == EDeviceFamily.BULB
        ]

    @property
    def fans(self) -> List[VeSyncBaseDevice]:
        """Returns a list of all registered fans."""
        return [
            dev
            for dev in self._device_list
            if dev.device_family == EDeviceFamily.FAN
        ]

    @property
    def kitchen(self) -> List[VeSyncBaseDevice]:
        """Returns a list of all registered kitchen devices."""
        return [
            dev
            for dev in self._device_list
            if dev.device_family == EDeviceFamily.KITCHEN
        ]

    @property
    def outlets(self) -> List[VeSyncBaseDevice]:
        """Returns a list of all registered outlets."""
        return [
            dev
            for dev in self._device_list
            if dev.device_family == EDeviceFamily.OUTLET
        ]

    @property
    def switches(self) -> List[VeSyncBaseDevice]:
        """Returns a list of all registered switches."""
        return [
            dev
            for dev in self._device_list
            if dev.device_family == EDeviceFamily.SWITCH
        ]

    @property
    def device_list(self) -> List[VeSyncBaseDevice]:
        """Returns a list of all registered devices."""
        return self._device_list.copy()

    def req_headers(self) -> REQUEST_T:
        """Build header for legacy api GET requests.

        Returns:
            dict: Header dictionary for api requests.

        Examples:
            >>> req_headers(manager)
            {
                'accept-language': 'en',
                'accountId': manager.account_id,
                'appVersion': APP_VERSION,
                'content-type': 'application/json',
                'tk': manager.token,
                'tz': manager.time_zone,
            }

        """
        return {
            'accept-language': 'en',
            'accountId': self.account_id,
            'appVersion': APP_VERSION,
            'content-type': 'application/json',
            'tk': self.token,
            'tz': self.time_zone,
        }

    @staticmethod
    def req_header_bypass() -> REQUEST_T:
        """Build header for api requests on 'bypass' endpoint.

        Returns:
            dict: Header dictionary for api requests.

        Examples:
            >>> req_header_bypass()
            {
                'Content-Type': 'application/json; charset=UTF-8',
                'User-Agent': BYPASS_HEADER_UA,
            }
        """
        return {
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': BYPASS_HEADER_UA,
        }

    def post_device_managed_v1(self, body):
        """Return the response for a bypass V^ request with the given body."""
        response = Helpers.call_api(
            api='/cloud/v1/deviceManaged/bypass',
            method='post',
            headers=self.req_headers(),
            json_object=body
        )
        return response

    def post_device_managed_v2(self, body):
        """Return the response for a bypass V2 request with the given body."""
        return Helpers.call_api(
            api='/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=VeSync.req_header_bypass(),
            json_object=body
        )

    def req_body_details(self, method: str, args: Optional[dict] = None) -> REQUEST_T:
        """Detail keys for api requests.

        Returns:
            dict: Detail keys for api requests.

        Examples:
            >>> req_body_details('dummy')
            {
                'appVersion': APP_VERSION,
                'phoneBrand': PHONE_BRAND,
                'phoneOS': PHONE_OS,
                'traceId': str(int(time.time())),
                'method': 'dummy'
            }
        """
        details = {
            'appVersion': APP_VERSION,
            'phoneBrand': PHONE_BRAND,
            'phoneOS': PHONE_OS,
            'traceId': str(int(time.time())),
            'method': method
        }
        if isinstance(args, dict):
            details |= args
        return details

    def req_body_base(self) -> REQUEST_T:
        """Return universal keys for body of api requests.

        Returns:
            dict: Body dictionary for api requests.

        Examples:
            >>> req_body_base(manager)
            {
                'timeZone': manager.time_zone,
                'acceptLanguage': 'en',
            }
        """
        return {
            'timeZone': self.time_zone,
            'acceptLanguage': 'en'
        }

    def req_body_auth(self) -> REQUEST_T:
        """Keys for authenticating api requests.

        Returns:
            dict: Authentication keys for api requests.

        Examples:
            >>> req_body_auth(manager)
            {
                'accountID': manager.account_id,
                'token': manager.token,
            }
        """
        return {
            'accountID': self.account_id,
            'token': self.token
        }

    def req_body_login(self) -> REQUEST_T:
        """Return the body for the login request."""
        return {
            **self.req_body_base(),
            **self.req_body_details(VeSync.API_LOGIN),
            'email': self.username,
            'password': Helpers.hash_password(self.password),
            'devToken': '',
            'userType': USER_TYPE,
        }

    def req_body_status(self, args: Optional[dict] = None) -> REQUEST_T:
        """Return the body for the status request."""
        body: REQUEST_T = {
            **self.req_body_base(),
            **self.req_body_auth()
        }
        if (isinstance(args, dict)):
            body |= args
        return body

    def req_body_devices(self, args: Optional[dict] = None) -> REQUEST_T:
        """Return the body for the device list request."""
        devices: REQUEST_T = {
            **self.req_body_status(),
            **self.req_body_details(VeSync.API_DEVICE_LIST, args),
            'pageNo': '1',
            'pageSize': '100'
        }
        return devices

    def req_body_device_detail(self) -> REQUEST_T:
        """Return the body for the device detail request."""
        return {
            **self.req_body_status(),
            **self.req_body_details(VeSync.API_DETAIL),
            'mobileId': MOBILE_ID
        }

    def req_body_device_configuration(self) -> REQUEST_T:
        """Return the body for the device configuration request."""
        return {
            **self.req_body_status(),
            **self.req_body_details(VeSync.API_CONFIG),
            'mobileId': MOBILE_ID
        }

    def req_body_energy(self, period: str) -> REQUEST_T:
        """Return the body for the energy request."""
        return {
            **self.req_body_status(),
            **self.req_body_details(f'energy{period}'),
            'mobileId': MOBILE_ID
        }

    def req_body_energy_week(self) -> REQUEST_T:
        """Return the body for the weekly energy request."""
        return self.req_body_energy(ENERGY_WEEK)

    def req_body_energy_month(self) -> REQUEST_T:
        """Return the body for the monthly energy request."""
        return self.req_body_energy(ENERGY_MONTH)

    def req_body_energy_year(self) -> REQUEST_T:
        """Return the body for the yearly energy request."""
        return self.req_body_energy(ENERGY_YEAR)

    def req_body_bypass_v1(self, args: Optional[dict] = None) -> REQUEST_T:
        """Return teh body for the bypass V1 request."""
        return {
            **self.req_body_base(),
            **self.req_body_auth(),
            **self.req_body_details(VeSync.API_BYPASS_V1, args)
        }

    def req_body_bypass_v2(self, args: Optional[dict] = None) -> REQUEST_T:
        """Return teh body for the bypass V2 request."""
        return {
            **self.req_body_base(),
            **self.req_body_auth(),
            **self.req_body_details(VeSync.API_BYPASS_V2, args),
            'deviceRegion': DEFAULT_REGION,
            'debugMode': False
        }

    def req_body_firmware(self, args: Optional[dict] = None) -> REQUEST_T:
        """Return the body for the firmware request."""
        return {
            **self.req_body_base(),
            **self.req_body_auth(),
            **self.req_body_details(VeSync.API_FIRMWARE, args),
        }

    def req_body(self, api: str) -> REQUEST_T:
        """Builder for body of api requests.

        Args:
            api (str): path of the api request.

        Returns:
            dict: Body dictionary for api requests.

        Note:
            The body dictionary will be built based on the request's method.
            Known api are:
            - login
            - devicelist
            - devicedetail
            - devicestatus
            - configurations
            - energy_week
            - energy_month
            - energy_year
            - bypass
            - bypassV2
            - firmwareUpdateInfo
        """
        if (api == VeSync.API_LOGIN):
            return self.req_body_login()
        if (api == VeSync.API_DEVICE_LIST):
            return self.req_body_devices()
        if (api == VeSync.API_DETAIL):
            return self.req_body_device_detail()
        if (api == VeSync.API_CONFIG):
            return self.req_body_device_configuration()
        if (api == VeSync.API_STATUS):
            return self.req_body_status()
        if (api == f'{VeSync.API_ENERGY}_{ENERGY_WEEK}'):
            return self.req_body_energy_week()
        if (api == f'{VeSync.API_ENERGY}_{ENERGY_MONTH}'):
            return self.req_body_energy_month()
        if (api == f'{VeSync.API_ENERGY}_{ENERGY_YEAR}'):
            return self.req_body_energy_year()
        if (api == VeSync.API_BYPASS_V1):
            return self.req_body_bypass_v1()
        if (api == VeSync.API_BYPASS_V2):
            return self.req_body_bypass_v2()
        if (api == VeSync.API_FIRMWARE):
            return self.req_body_firmware()

        logger.warning('pyvesync: building request-body for unknown method "%s"!', api)
        return {
            **self.req_body_base(),
            **self.req_body_auth(),
            **self.req_body_details(api),
        }
