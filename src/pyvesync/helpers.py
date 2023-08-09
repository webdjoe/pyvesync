"""Helper functions for VeSync API."""

import hashlib
import logging
import time
import json
import colorsys
from dataclasses import dataclass, field, InitVar
from typing import NamedTuple, Optional, Union
import re
import requests


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

NUMERIC = Optional[Union[int, float, str]]


class Helpers:
    """VeSync Helper Functions."""

    @staticmethod
    def req_headers(manager) -> dict:
        """Build header for api requests."""
        headers = {
            'accept-language': 'en',
            'accountId': manager.account_id,
            'appVersion': APP_VERSION,
            'content-type': 'application/json',
            'tk': manager.token,
            'tz': manager.time_zone,
        }
        return headers

    @staticmethod
    def req_header_bypass() -> dict:
        """Build header for api requests on 'bypass' endpoint."""
        return {
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': 'okhttp/3.12.1',
            }

    @staticmethod
    def req_body_base(manager) -> dict:
        """Return universal keys for body of api requests."""
        return {'timeZone': manager.time_zone, 'acceptLanguage': 'en'}

    @staticmethod
    def req_body_auth(manager) -> dict:
        """Keys for authenticating api requests."""
        return {'accountID': manager.account_id, 'token': manager.token}

    @staticmethod
    def req_body_details() -> dict:
        """Detail keys for api requests."""
        return {
            'appVersion': APP_VERSION,
            'phoneBrand': PHONE_BRAND,
            'phoneOS': PHONE_OS,
            'traceId': str(int(time.time())),
        }

    @classmethod
    def req_body(cls, manager, type_) -> dict:
        """Builder for body of api requests."""
        body = {}

        if type_ == 'login':
            body = {**cls.req_body_base(manager),
                    **cls.req_body_details()}
            body['email'] = manager.username
            body['password'] = cls.hash_password(manager.password)
            body['devToken'] = ''
            body['userType'] = USER_TYPE
            body['method'] = 'login'
        elif type_ == 'devicedetail':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details(),
            }
            body['method'] = 'devicedetail'
            body['mobileId'] = MOBILE_ID
        elif type_ == 'devicelist':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details(),
            }
            body['method'] = 'devices'
            body['pageNo'] = '1'
            body['pageSize'] = '100'
        elif type_ == 'devicestatus':
            body = {**cls.req_body_base(manager),
                    **cls.req_body_auth(manager)}
        elif type_ == 'energy_week':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details(),
            }
            body['method'] = 'energyweek'
            body['mobileId'] = MOBILE_ID
        elif type_ == 'energy_month':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details(),
            }
            body['method'] = 'energymonth'
            body['mobileId'] = MOBILE_ID
        elif type_ == 'energy_year':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details(),
            }
            body['method'] = 'energyyear'
            body['mobileId'] = MOBILE_ID
        elif type_ == 'bypass':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details(),
            }
            body['method'] = 'bypass'
        elif type_ == 'bypassV2':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details(),
            }
            body['deviceRegion'] = DEFAULT_REGION
            body['method'] = 'bypassV2'
        elif type_ == 'bypass_config':
            body = {
                **cls.req_body_base(manager),
                **cls.req_body_auth(manager),
                **cls.req_body_details(),
            }
            body['method'] = 'firmwareUpdateInfo'

        return body

    @staticmethod
    def calculate_hex(hex_string) -> float:
        """Credit for conversion to itsnotlupus/vesync_wsproxy."""
        hex_conv = hex_string.split(':')
        converted_hex = (int(hex_conv[0], 16) + int(hex_conv[1], 16)) / 8192

        return converted_hex

    @staticmethod
    def hash_password(string) -> str:
        """Encode password."""
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    shouldredact = True

    @classmethod
    def redactor(cls, stringvalue: str) -> str:
        """Redact sensitive strings from debug output."""
        if cls.shouldredact:
            stringvalue = re.sub(r''.join((
                                          '(?i)',
                                          '((?<=token": ")|',
                                          '(?<=password": ")|',
                                          '(?<=email": ")|',
                                          '(?<=tk": ")|',
                                          '(?<=accountId": ")|',
                                          '(?<=authKey": ")|',
                                          '(?<=uuid": ")|',
                                          '(?<=cid": "))',
                                          '[^"]+')
                                          ),
                                 '##_REDACTED_##', stringvalue)
        return stringvalue

    @staticmethod
    def nested_code_check(response: dict) -> bool:
        """Return true if all code values are 0."""
        if isinstance(response, dict):
            for key, value in response.items():
                if key == 'code':
                    if value != 0:
                        return False
                elif isinstance(value, dict):
                    if not Helpers.nested_code_check(value):
                        return False
        return True

    @staticmethod
    def call_api(api: str, method: str, json_object:  Optional[dict] = None,
                 headers: Optional[dict] = None) -> tuple:
        """Make API calls by passing endpoint, header and body."""
        response = None
        status_code = None

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
        except requests.exceptions.RequestException as e:
            logger.debug(e)
        except Exception as e:  # pylint: disable=broad-except
            logger.debug(e)
        else:
            if r.status_code == 200:
                status_code = 200
                if r.content:
                    response = r.json()
                    logger.debug("API response: \n\n  %s \n ",
                                 Helpers.redactor(json.dumps(response, indent=2)))
            else:
                logger.debug('Unable to fetch %s%s', API_BASE_URL, api)
        return response, status_code

    @staticmethod
    def code_check(r: dict) -> bool:
        """Test if code == 0 for successful API call."""
        if r is None:
            logger.error('No response from API')
            return False
        if isinstance(r, dict) and r.get('code') == 0:
            return True
        return False

    @staticmethod
    def build_details_dict(r: dict) -> dict:
        """Build details dictionary from API response."""
        return {
            'active_time': r.get('activeTime', 0),
            'energy': r.get('energy', 0),
            'night_light_status': r.get('nightLightStatus', None),
            'night_light_brightness': r.get('nightLightBrightness', None),
            'night_light_automode': r.get('nightLightAutomode', None),
            'power': r.get('power', 0),
            'voltage': r.get('voltage', 0),
        }

    @staticmethod
    def build_energy_dict(r: dict) -> dict:
        """Build energy dictionary from API response."""
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
        """Build configuration dictionary from API response."""
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

    @classmethod
    def bypass_body_v2(cls, manager):
        """Build body dict for bypass calls."""
        bdy = {}
        bdy.update(
            **cls.req_body(manager, "bypass")
        )
        bdy['method'] = 'bypassV2'
        bdy['debugMode'] = False
        bdy['deviceRegion'] = DEFAULT_REGION
        return bdy

    @staticmethod
    def bypass_header():
        """Build bypass header dict."""
        return {
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': 'okhttp/3.12.1',
        }

    @staticmethod
    def named_tuple_to_str(named_tuple: NamedTuple) -> str:
        """Convert named tuple to string."""
        tuple_str = ''
        for key, val in named_tuple._asdict().items():
            tuple_str += f'{key}: {val}, '
        return tuple_str


class HSV(NamedTuple):
    """HSV color space."""

    hue: float
    saturation: float
    value: float


class RGB(NamedTuple):
    """RGB color space."""

    red: float
    green: float
    blue: float


@dataclass
class Color:
    """Dataclass for color values.

    For HSV, pass hue as value in degrees 0-360, saturation and value as values
    between 0 and 100.

    For RGB, pass red, green and blue as values between 0 and 255.

    To instantiate pass kw arguments for colors hue, saturation and value or
    red, green and blue.

    Instance attributes are:
    hsv (nameduple) : hue (0-360), saturation (0-100), value (0-100)

    rgb (namedtuple) : red (0-255), green (0-255), blue

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

    def __post_init__(self, red, green, blue, hue, saturation, value):
        """Check HSV or RGB Values and create named tuples."""
        if any(x is not None for x in [hue, saturation, value]):
            self.hsv = HSV(*self.valid_hsv(hue, saturation, value))
            self.rgb = self.hsv_to_rgb(hue, saturation, value)
        elif any(x is not None for x in [red, green, blue]):
            self.rgb = RGB(*self.valid_rgb(red, green, blue))
            self.hsv = self.rgb_to_hsv(red, green, blue)
        else:
            logger.error('No color values provided')

    @staticmethod
    def min_max(value: Union[int, float, str], min_val: float,
                max_val: float, default: float) -> float:
        """Check if value is within min and max values."""
        try:
            val = max(min_val, (min(max_val, round(float(value), 2))))
        except (ValueError, TypeError):
            val = default
        return val

    @classmethod
    def valid_hsv(cls, h: Union[int, float, str],
                  s: Union[int, float, str],
                  v: Union[int, float, str]) -> tuple:
        """Check if HSV values are valid."""
        valid_hue = float(cls.min_max(h, 0, 360, 360))
        valid_saturation = float(cls.min_max(s, 0, 100, 100))
        valid_value = float(cls.min_max(v, 0, 100, 100))
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
            valid_val = cls.min_max(val, 0, 255, 255)
            rgb.append(valid_val)
        return rgb

    @staticmethod
    def hsv_to_rgb(hue, saturation, value) -> RGB:
        """Convert HSV to RGB."""
        return RGB(
            *tuple(round(i * 255, 0) for i in colorsys.hsv_to_rgb(
                hue / 360,
                saturation / 100,
                value / 100
            ))
        )

    @staticmethod
    def rgb_to_hsv(red, green, blue) -> HSV:
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
    """Dataclass for timers.

    Parameters
    ----------
    timer_duration : int
        Length of timer in seconds
    action : str
        Action to perform when timer is done
    id: int
        ID of timer, defaults to 1

    Attributes
    ----------
    update_time : int
        Timestamp of last update

    Properties
    ----------
    status : str
        Status of timer, one of 'active', 'paused', 'done'
    time_remaining : int
        Time remaining on timer in seconds
    running : bool
        True if timer is running
    paused : bool
        True if timer is paused
    done : bool
        True if timer is done

    Methods
    -------
    start()
        Restarts paused timer
    end()
        Ends timer
    pause()
        Pauses timer
    update(time_remaining: Optional[int] = None, status: Optional[str] = None)
        Updates timer with new time remaining and/or status
    """

    timer_duration: int
    action: str
    id: int = 1
    remaining: InitVar[Optional[int]] = None
    _status: str = 'active'
    _remain: int = 0
    update_time: Optional[int] = int(time.time())

    def __post_init__(self, remaining) -> None:
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
            raise ValueError(f'Invalid status {status}')
        self._internal_update()
        if status == 'done' or self._status == 'done':
            return self.end()
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
            return self.end()
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
        if self.time_remaining > 0 and self.status == 'active':
            return True
        return False

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

    def update(self, *, time_remaining: Optional[int] = None,
               status: Optional[str] = None) -> None:
        """Update timer.

        Accepts only KW args

        Parameters
        ----------
        time_remaining : int
            Time remaining on timer in seconds
        status : str
            Status of timer, can be active, paused, or done

        Returns
        -------
        None
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
