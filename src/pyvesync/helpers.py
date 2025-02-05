"""Helper functions for VeSync API."""
from __future__ import annotations
import hashlib
import logging
import time
import json
import colorsys
from dataclasses import dataclass, field, InitVar
from typing import Any, NamedTuple, Union, Optional, TYPE_CHECKING
import re
import requests
from enum import Enum

if TYPE_CHECKING:
    from .vesync import VeSync


logger = logging.getLogger(__name__)

API_BASE_URL = 'https://smartapi.vesync.com'
API_RATE_LIMIT = 30
# If device is out of reach, the cloud api sends a timeout response after 7 seconds,
# using 8 here so there is time enough to catch that message
API_TIMEOUT = 8
USER_AGENT = ("VeSync/3.2.39 (com.etekcity.vesyncPlatform;"
              " build:5; iOS 15.5.0) Alamofire/5.2.1")

DEFAULT_TZ = 'America/New_York'
DEFAULT_REGION = 'US'

APP_VERSION = '2.8.6'
PHONE_BRAND = 'SM N9005'
PHONE_OS = 'Android'
MOBILE_ID = '1234567890123456'
USER_TYPE = '1'
BYPASS_APP_V = "VeSync 3.0.51"

BYPASS_HEADER_UA = 'okhttp/3.12.1'

NUMERIC = Union[int, float, str, None]

REQUEST_T = dict[str, Any]


ENERGY_WEEK  = 'week'
ENERGY_MONTH = 'month'
ENERGY_YEAR  = 'year'
PERIOD_2_DAYS = {ENERGY_WEEK: 7, ENERGY_MONTH: 30, ENERGY_YEAR: 365}

API_LOGIN       = 'login'
API_DEVICE_LIST = 'devices'
API_DETAIL      = 'devicedetail'
API_STATUS      = 'devicestatus'
API_ENERGY      = 'energy'
API_BYPASS_V1   = 'bypass'
API_BYPASS_V2   = 'bypassV2'
API_FIRMWARE    = 'firmwareUpdateInfo'

ERR_DEV_OFFLINE   = -11300027 # device offline
ERR_REQ_TIMEOUT_1 = -11300030 # request timeout
ERR_REQ_TIMEOUT_2 = -11302030 # request timeout
ERR_REQ_TIMEOUTS  = (ERR_REQ_TIMEOUT_1, ERR_REQ_TIMEOUT_2)

class EDeviceFamily(Enum):
    BULB = 'bulb'
    FAN = 'fan'
    KITCHEN = 'kitchen'
    OUTLET = 'outlet'
    SWITCH = 'switch'
    NOT_SUPPORTED = 'not supported'

class Helpers:
    """VeSync Helper Functions."""

    @staticmethod
    def req_headers(manager: VeSync) -> dict[str, str]:
        """Build header for legacy api GET requests.

        Args:
            manager (VeSyncManager): Instance of VeSyncManager.

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
            'accountId': manager.account_id,
            'appVersion': APP_VERSION,
            'content-type': 'application/json',
            'tk': manager.token,
            'tz': manager.time_zone,
        }

    @staticmethod
    def req_header_bypass() -> dict[str, str]:
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

    @staticmethod
    def req_body_base(manager: VeSync) -> dict[str, str]:
        """Return universal keys for body of api requests.

        Args:
            manager (VeSyncManager): Instance of VeSyncManager.

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
            'timeZone': manager.time_zone,
            'acceptLanguage': 'en'
        }

    @staticmethod
    def req_body_auth(manager: VeSync) -> REQUEST_T:
        """Keys for authenticating api requests.

        Args:
            manager (VeSyncManager): Instance of VeSyncManager.

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
            'accountID': manager.account_id,
            'token': manager.token
        }

    @staticmethod
    def req_body_details(method: str, args: Optional[dict] = None) -> REQUEST_T:
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
        if ((not args is None) 
            and (type(args) is dict)
            and (len(args))
        ):
            details |= args
        return details

    @classmethod
    def req_body(cls, manager: VeSync, api: str) -> REQUEST_T:  # noqa: C901
        """Builder for body of api requests.

        Args:
            manager (VeSync): Instance of VeSync.
            method (str): Type of request to build body for.

        Returns:
            dict: Body dictionary for api requests.

        Note:
            The body dictionary will be built based on the request's method.
            Known api are:
            - login
            - devicelist
            - devicedetail
            - devicestatus
            - energy_week
            - energy_month
            - energy_year
            - bypass
            - bypassV2
            - firmwareUpdateInfo
        """
        if (api == API_LOGIN):
            return cls.req_body_login()
        if (api == API_DEVICE_LIST):
            return cls.req_body_devices(manager)
        if api == API_DETAIL:
            return cls.req_body_device_detail(manager)
        if (api == API_STATUS):
            return cls.req_body_status(manager)
        if api == f'{API_ENERGY}_{ENERGY_WEEK}':
            return cls.req_body_energy_week(manager)
        if api == f'{API_ENERGY}_{ENERGY_MONTH}':
            return cls.req_body_energy_month(manager)
        if api == f'{API_ENERGY}_{ENERGY_YEAR}':
            return cls.req_body_energy_year(manager)
        if api == API_BYPASS_V1:
            return cls.req_body_bypass_v1(manager)
        if api == API_BYPASS_V2:
            return cls.req_body_bypass_v2(manager)
        if api == API_FIRMWARE:
            return cls.req_body_firmware(manager)

        logger.warning(f'pyvesync: building request-body for unknown method "{api}"!')
        body: REQUEST_T = cls.req_body_base(manager)
        body |= cls.req_body_auth(manager)
        body |= cls.req_body_details(api)

        return body

    @classmethod
    def req_body_login(cls, manager: VeSync) -> REQUEST_T:
        return {
            **cls.req_body_base(manager),
            **cls.req_body_details(API_LOGIN),
            'email': manager.username,
            'password': cls.hash_password(manager.password),
            'devToken': '',
            'userType': USER_TYPE,
        }
    
    @classmethod
    def req_body_status(cls, manager: VeSync, args: Optional[dict] = None) -> REQUEST_T:
        body: REQUEST_T = {
            **cls.req_body_base(manager),
            **cls.req_body_auth(manager)
        }
        if ((not args is None) 
            and (type(args) is dict)
            and (len(args))
        ):
            body |= args
        return body

    @classmethod
    def req_body_devices(cls, manager: VeSync, args: Optional[dict] = None) -> REQUEST_T:
        devices: REQUEST_T = {
            **cls.req_body_status(manager),
            **cls.req_body_details(API_DEVICE_LIST, args),
            'pageNo': '1',
            'pageSize': '100'
        }
        return devices

    @classmethod
    def req_body_device_detail(cls, manager: VeSync) -> REQUEST_T:
        return {
            **cls.req_body_status(manager),
            **cls.req_body_details(API_DETAIL),
            'mobileId': MOBILE_ID
        }

    @classmethod
    def req_body_energy(cls, manager: VeSync, period: str) -> REQUEST_T:
        return {
            **cls.req_body_status(manager),
            **cls.req_body_details(f'energy{period}'),
            'mobileId': MOBILE_ID
        }

    @classmethod
    def req_body_energy_week(cls, manager: VeSync) -> REQUEST_T:
        return cls.req_body_energy(manager, ENERGY_WEEK)

    @classmethod
    def req_body_energy_month(cls, manager: VeSync) -> REQUEST_T:
        return cls.req_body_energy(manager, ENERGY_MONTH)

    @classmethod
    def req_body_energy_year(cls, manager: VeSync) -> REQUEST_T:
        return cls.req_body_energy(manager, ENERGY_YEAR)

    @classmethod
    def req_body_bypass_v1(cls, manager: VeSync, args: Optional[dict] = None) -> REQUEST_T:
        return {
            **cls.req_body_base(manager),
            **cls.req_body_auth(manager),
            **cls.req_body_details(API_BYPASS_V1, args)
        }

    @classmethod
    def req_body_bypass_v2(cls, manager: VeSync, args: Optional[dict] = None) -> REQUEST_T:
        return {
            **cls.req_body_base(manager),
            **cls.req_body_auth(manager),
            **cls.req_body_details(API_BYPASS_V2, args),
            'deviceRegion': DEFAULT_REGION,
            'debugMode': False
        }

    @classmethod
    def req_body_firmware(cls, manager: VeSync, args: Optional[dict] = None) -> REQUEST_T:
        return {
            **cls.req_body_base(manager),
            **cls.req_body_auth(manager),
            **cls.req_body_details(API_FIRMWARE, args),
        }

    @staticmethod
    def calculate_hex(hex_string: str) -> float:
        """Credit for conversion to itsnotlupus/vesync_wsproxy."""
        hex_conv = hex_string.split(':')
        return (int(hex_conv[0], 16) + int(hex_conv[1], 16)) / 8192

    @staticmethod
    def hash_password(string: str) -> str:
        """Encode password."""
        return hashlib.md5(string.encode('utf-8')).hexdigest()  # noqa: S324

    should_redact = True

    @classmethod
    def redactor(cls, value: str) -> str:
        """Redact sensitive strings from debug output.

        This method searches for specific sensitive keys in the input string and replaces
        their values with '##_REDACTED_##'. The keys that are redacted include:

        - token
        - password
        - email
        - tk
        - accountId
        - authKey
        - uuid
        - cid

        Args:
            value (str): The input string potentially containing
                sensitive information.

        Returns:
            str: The redacted string with sensitive information replaced
                by '##_REDACTED_##'.
        """
        if cls.should_redact:
            value = re.sub(
                (
                    r"(?i)"
                    r'((?<=token":\s")|'
                    r'(?<=password":\s")|'
                    r'(?<=email":\s")|'
                    r'(?<=tk":\s")|'
                    r'(?<=accountId":\s")|'
                    r'(?<=authKey":\s")|'
                    r'(?<=uuid":\s")|'
                    r'(?<=cid":\s")|'
                    r"(?<=token\s)|"
                    r"(?<=account_id\s))"
                    r'[^"\s]+'
                ),
                "##_REDACTED_##",
                value,
            )
        return value

    @staticmethod
    def nested_code_check(response: dict) -> bool:
        """Return true if all code values are 0.

        Args:
            response (dict): API response.

        Returns:
            bool: True if all code values are 0, False otherwise.
        """
        if isinstance(response, dict):
            for key, value in response.items():
                if (key == 'code' and value != 0) or \
                        (isinstance(value, dict) and
                            not Helpers.nested_code_check(value)):
                    return False
        return True

    @staticmethod
    def call_api(api: str, method: str, headers: dict | None = None, json_object:  dict | None = None) -> tuple:
        """Make API calls by passing endpoint, header and body.

        api argument is appended to https://smartapi.vesync.com url

        Args:
            api (str): Endpoint to call with https://smartapi.vesync.com.
            method (str): HTTP method to use.
            json_object (dict): JSON object to send in body.
            headers (dict): Headers to send with request.

        Returns:
            dict: Response.
        """
        response = None

        try:
            logger.debug("=======call_api=============================")
            logger.debug("[%s] calling '%s' api", method, api)
            logger.debug("API call URL: \n  %s%s", API_BASE_URL, api)
            logger.debug("API call headers: \n  %s",
                         Helpers.redactor(json.dumps(headers, indent=2)))
            logger.debug("API call json: \n  %s",
                         Helpers.redactor(json.dumps(json_object, indent=2)))
            if method.lower() == 'get':
                r = requests.get(
                    API_BASE_URL + api, json=json_object, headers=headers,
                    timeout=API_TIMEOUT
                )
            elif method.lower() == 'post':
                r = requests.post(
                    API_BASE_URL + api, json=json_object, headers=headers,
                    timeout=API_TIMEOUT
                )
            elif method.lower() == 'put':
                r = requests.put(
                    API_BASE_URL + api, json=json_object, headers=headers,
                    timeout=API_TIMEOUT
                )
            else:
                raise NameError(f'Invalid method {method}')
        except requests.exceptions.RequestException as e:
            logger.debug(e)
        except Exception as e:
            logger.debug(e)
        else:
            if r.status_code == 200:
                if r.content:
                    response = r.json()
                    logger.debug("API response: \n\n  %s \n ",
                                 Helpers.redactor(json.dumps(response, indent=2)))
            else:
                logger.debug('Unable to fetch %s%s', API_BASE_URL, api)
        return response

    @staticmethod
    def post_device_managed_v1(manager, body):
        response = Helpers.call_api(
            api='/cloud/v1/deviceManaged/bypass',
            method='post',
            headers=Helpers.req_headers(manager),
            json_object=body
        )
        return response

    @staticmethod
    def post_device_managed_v2(body):
        response = Helpers.call_api(
            api='/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=Helpers.req_header_bypass(),
            json_object=body
        )
        return response

    @staticmethod
    def code_check(r: dict) -> bool:
        """Test if code == 0 for successful API call."""
        if r is None:
            logger.error('No response from API')
            return False
        return (isinstance(r, dict) and r.get('code') == 0)

    @staticmethod
    def build_details_dict(r: dict) -> dict:
        """Build details dictionary from API response.

        Args:
            r (dict): API response.

        Returns:
            dict: Details dictionary.

        Examples:
            >>> build_details_dict(r)
            {
                'active_time': 1234,
                'energy': 168,
                'night_light_status': 'on',
                'night_light_brightness': 50,
                'night_light_automode': 'on',
                'power': 1,
                'voltage': 120,
            }

        """
        return {
            'active_time': r.get('activeTime', 0),
            'energy': r.get('energy', 0),
            'night_light_status': r.get('nightLightStatus'),
            'night_light_brightness': r.get('nightLightBrightness'),
            'night_light_automode': r.get('nightLightAutomode'),
            'power': r.get('power', 0),
            'voltage': r.get('voltage', 0),
        }

    @staticmethod
    def build_energy_dict(r: dict) -> dict:
        """Build energy dictionary from API response.

        Note:
            For use with **Etekcity** outlets only

        Args:
            r (dict): API response.

        Returns:
            dict: Energy dictionary.
        """
        return {
            'energy_consumption_of_today': r.get(
                    'energyConsumptionOfToday', 0),
            'cost_per_kwh': r.get('costPerKWH', 0),
            'max_energy': r.get('maxEnergy', 0),
            'total_energy': r.get('totalEnergy', 0),
            'currency': r.get('currency', 0),
            'data': r.get('data', 0),
        }

    @staticmethod
    def build_config_dict(r: dict) -> dict:
        """Build configuration dictionary from API response.

        Contains firmware version, max power, threshold,
        power protection status, and energy saving status.

        Note:
            Energy and power stats only available for **Etekcity**
            outlets.

        Args:
            r (dict): API response.

        Returns:
            dict: Configuration dictionary.

        Examples:
            >>> build_config_dict(r)
            {
                'current_firmware_version': '1.2.3',
                'latest_firmware_version': '1.2.4',
                'max_power': 1000,
                'threshold': 500,
                'power_protection': 'on',
                'energy_saving_status': 'on',
            }

        """
        if r.get('threshold') is not None:
            threshold = r.get('threshold')
        else:
            threshold = r.get('threshHold')
        return {
            'current_firmware_version': r.get('currentFirmVersion'),
            'latest_firmware_version': r.get('latestFirmVersion'),
            'maxPower': r.get('maxPower'),
            'threshold': threshold,
            'power_protection': r.get('powerProtectionStatus'),
            'energy_saving_status': r.get('energySavingStatus'),
        }

    @staticmethod
    def named_tuple_to_str(named_tuple: NamedTuple) -> str:
        """Convert named tuple to string.

        Args:
            named_tuple (namedtuple): Named tuple to convert to string.

        Returns:
            str: String representation of named tuple.

        Examples:
            >>> named_tuple_to_str(HSV(100, 50, 75))
            'hue: 100, saturation: 50, value: 75, '
        """
        tuple_str = ''
        for key, val in named_tuple._asdict().items():
            tuple_str += f'{key}: {val}, '
        return tuple_str


class HSV(NamedTuple):
    """HSV color space named tuple.

    Used as an attribute in the `pyvesync.helpers.Color` dataclass.

    Attributes:
        hue (float): The hue component of the color, typically in the range [0, 360).
        saturation (float): The saturation component of the color,
            typically in the range [0, 1].
        value (float): The value (brightness) component of the color,
            typically in the range [0, 1].
    """

    hue: float
    saturation: float
    value: float


class RGB(NamedTuple):
    """RGB color space named tuple.

    Used as an attribute in the :obj:`pyvesync.helpers.Color` dataclass.

    Attributes:
        red (float): The red component of the RGB color.
        green (float): The green component of the RGB color.
        blue (float): The blue component of the RGB color.
    """

    red: float
    green: float
    blue: float


@dataclass
class Color:
    """Dataclass for color values.

    For HSV, pass hue as value in degrees 0-360, saturation and value as values
    between 0 and 100. For RGB, pass red, green and blue as values between 0 and 255. This
    dataclass provides validation and conversion methods for both HSV and RGB color spaces

    Notes:
        To instantiate pass kw arguments for colors with *either* **hue, saturation and
        value** *or* **red, green and blue**. RGB will take precedence if both are
        provided. Once instantiated, the named tuples `hsv` and `rgb` will be
        available as attributes.

    Args:
        red (int): Red value of RGB color, 0-255
        green (int): Green value of RGB color, 0-255
        blue (int): Blue value of RGB color, 0-255
        hue (int): Hue value of HSV color, 0-360
        saturation (int): Saturation value of HSV color, 0-100
        value (int): Value (brightness) value of HSV color, 0-100

    Attributes:
        hsv (namedtuple): hue (0-360), saturation (0-100), value (0-100)
            see [`HSV dataclass`][pyvesync.helpers.HSV]
        rgb (namedtuple): red (0-255), green (0-255), blue (0-255)
            see [`RGB dataclass`][pyvesync.helpers.RGB]
    """

    red: InitVar[NUMERIC] = field(default=None, repr=False, compare=False)
    green: InitVar[NUMERIC] = field(default=None, repr=False, compare=False)
    blue: InitVar[NUMERIC] = field(default=None, repr=False, compare=False)
    hue: InitVar[NUMERIC] = field(default=None, repr=False, compare=False)
    saturation: InitVar[NUMERIC] = field(default=None, repr=False,
                                         compare=False)
    value: InitVar[NUMERIC] = field(default=None, repr=False, compare=False)
    hsv: HSV = field(init=False)
    rgb: RGB = field(init=False)

    def __post_init__(self,
                      red: NUMERIC,
                      green: NUMERIC,
                      blue: NUMERIC,
                      hue: NUMERIC,
                      saturation: NUMERIC,
                      value: NUMERIC) -> None:
        """Check HSV or RGB Values and create named tuples."""
        if None not in [hue, saturation, value]:
            self.hsv = HSV(*self.valid_hsv(hue, saturation, value))  # type: ignore[arg-type] # noqa
            self.rgb = self.hsv_to_rgb(hue, saturation, value)  # type: ignore[arg-type]  # noqa
        elif None not in [red, green, blue]:
            self.rgb = RGB(*self.valid_rgb(red, green, blue))  # type: ignore[arg-type]
            self.hsv = self.rgb_to_hsv(red, green, blue)  # type: ignore[arg-type]
        else:
            logger.error('No color values provided')

    @staticmethod
    def _min_max(value: float | str, min_val: float,
                 max_val: float, default: float) -> float:
        """Check if value is within min and max values."""
        try:
            val = max(min_val, (min(max_val, round(float(value), 2))))
        except (ValueError, TypeError):
            val = default
        return val

    @classmethod
    def valid_hsv(cls, h: float | str,
                  s: float | str,
                  v: float | str) -> tuple:
        """Check if HSV values are valid."""
        valid_hue = float(cls._min_max(h, 0, 360, 360))
        valid_saturation = float(cls._min_max(s, 0, 100, 100))
        valid_value = float(cls._min_max(v, 0, 100, 100))
        return (
            valid_hue,
            valid_saturation,
            valid_value
        )

    @classmethod
    def valid_rgb(cls, r: float, g: float, b: float) -> list:
        """Check if RGB values are valid."""
        rgb = []
        for val in (r, g, b):
            valid_val = cls._min_max(val, 0, 255, 255)
            rgb.append(valid_val)
        return rgb

    @staticmethod
    def hsv_to_rgb(hue: float, saturation: float, value: float) -> RGB:
        """Convert HSV to RGB."""
        return RGB(
            *tuple(round(i * 255, 0) for i in colorsys.hsv_to_rgb(
                hue / 360,
                saturation / 100,
                value / 100
            ))
        )

    @staticmethod
    def rgb_to_hsv(red: float, green: float, blue: float) -> HSV:
        """Convert RGB to HSV."""
        hsv_tuple = colorsys.rgb_to_hsv(
                red / 255,
                green / 255,
                blue / 255
            )
        hsv_factors = [360, 100, 100]

        return HSV(
            float(round(hsv_tuple[0] * hsv_factors[0], 2)),
            float(round(hsv_tuple[1] * hsv_factors[1], 2)),
            float(round(hsv_tuple[2] * hsv_factors[2], 0)),
        )


@dataclass
class Timer:
    """Dataclass to hold state of timers.

    Note:
        This should be used by VeSync device instances to manage internal status,
        does not interact with the VeSync API.

    Args:
        timer_duration (int): Length of timer in seconds
        action (str): Action to perform when timer is done
        id (int): ID of timer, defaults to 1
        remaining (int): Time remaining on timer in seconds, defaults to None
        update_time (int): Last updated unix timestamp in seconds, defaults to None

    Attributes:
        update_time (str): Timestamp of last update
        status (str): Status of timer, one of 'active', 'paused', 'done'
        time_remaining (int): Time remaining on timer in seconds
        running (bool): True if timer is running
        paused (bool): True if timer is paused
        done (bool): True if timer is done
    """

    timer_duration: int
    action: str
    id: int = 1
    remaining: InitVar[int | None] = None
    _status: str = 'active'
    _remain: int = 0
    update_time: int | None = int(time.time())

    def __post_init__(self, remaining: int | None) -> None:
        """Set remaining time if provided."""
        if remaining is not None:
            self._remain = remaining
        else:
            self._remain = self.timer_duration

    @property
    def status(self) -> str:
        """Return status of timer."""
        return self._status

    @status.setter
    def status(self, status: str) -> None:
        """Set status of timer."""
        if status not in ['active', 'paused', 'done']:
            logger.error('Invalid status %s', status)
            raise ValueError
        self._internal_update()
        if status == 'done' or self._status == 'done':
            self.end()
            return
        if self.status == 'paused' and status == 'active':
            self.update_time = int(time.time())
        if self.status == 'active' and status == 'paused':
            self.update_time = None
        self._status = status

    @property
    def _seconds_since_check(self) -> int:
        """Return seconds since last update."""
        if self.update_time is None:
            return 0
        return int(time.time()) - self.update_time

    @property
    def time_remaining(self) -> int:
        """Return remaining seconds."""
        self._internal_update()
        return self._remain

    @time_remaining.setter
    def time_remaining(self, remaining: int) -> None:
        """Set time remaining in seconds."""
        if remaining <= 0:
            self.end()
            return
        self._internal_update()
        if self._status == 'done':
            self._remain = 0
            return
        self._remain = remaining

    def _internal_update(self) -> None:
        """Use time remaining update status."""
        if self._status == 'paused':
            self.update_time = None
            return
        if self._status == 'done' or (self._seconds_since_check > self._remain
                                      and self._status == 'active'):
            self._status = 'done'
            self.update_time = None
            self._remain = 0
        if self._status == 'active':
            self._remain = self._remain - self._seconds_since_check
            self.update_time = int(time.time())

    @property
    def running(self) -> bool:
        """Check if timer is active."""
        return (self.time_remaining > 0 and self.status == 'active')

    @property
    def paused(self) -> bool:
        """Check if timer is paused."""
        return bool(self.status == 'paused')

    @property
    def done(self) -> bool:
        """Check if timer is complete."""
        return bool(self.time_remaining <= 0 or self._status == 'done')

    def end(self) -> None:
        """Change status of timer to done."""
        self._status = 'done'
        self._remain = 0
        self.update_time = None

    def start(self) -> None:
        """Restart paused timer."""
        if self._status != 'paused':
            return
        self.update_time = int(time.time())
        self.status = 'active'

    def update(self, *, time_remaining: int | None = None,
               status: str | None = None) -> None:
        """Update timer.

        Accepts only KW args

        Parameters:
            time_remaining : int
                Time remaining on timer in seconds
            status : str
                Status of timer, can be active, paused, or done
        """
        if time_remaining is not None:
            self.time_remaining = time_remaining
        if status is not None:
            self.status = status

    def pause(self) -> None:
        """Pause timer. NOTE - this does not stop the timer via API only locally."""
        self._internal_update()
        if self.status == 'done':
            return
        self.status = 'paused'
        self.update_time = None
