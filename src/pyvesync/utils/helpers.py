"""Helper functions for VeSync API."""
from __future__ import annotations
from collections.abc import Iterator
import hashlib
import logging
import time
import re
from dataclasses import dataclass, InitVar
from typing import Any, Literal, NamedTuple, Union, TYPE_CHECKING, TypeVar
import orjson
from pyvesync.const import (
    APP_VERSION,
    BYPASS_HEADER_UA,
    DEFAULT_REGION,
    MOBILE_ID,
    PHONE_BRAND,
    PHONE_OS,
    USER_TYPE
    )
from pyvesync.utils.logs import LibraryLogger
from pyvesync.utils.errors import ErrorCodes

if TYPE_CHECKING:
    from pyvesync.vesync import VeSync
    from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseDevice

T = TypeVar('T')


_LOGGER = logging.getLogger(__name__)

API_BASE_URL = 'https://smartapi.vesync.com'
API_RATE_LIMIT = 30
NUMERIC_OPT = Union[float, str, None]

NUMERIC_STRICT = Union[float, str]

REQUEST_T = dict[str, Any]


class Validators:
    """Methods to validate input."""

    @staticmethod
    def validate_range(
        value: NUMERIC_OPT, minimum: NUMERIC_STRICT, maximum: NUMERIC_STRICT
    ) -> bool:
        """Validate number is within range."""
        if value is None:
            return False
        try:
            return float(minimum) <= float(value) <= float(maximum)
        except (ValueError, TypeError):
            return False

    @classmethod
    def validate_zero_to_hundred(cls, value: NUMERIC_OPT) -> bool:
        """Validate number is a percentage."""
        return Validators.validate_range(value, 0, 100)

    @classmethod
    def validate_hsv(cls, hue: NUMERIC_OPT, saturation: NUMERIC_OPT,
                     value: NUMERIC_OPT) -> bool:
        """Validate HSV values."""
        return (
            cls.validate_range(hue, 0, 360)
            and cls.validate_zero_to_hundred(saturation)
            and cls.validate_zero_to_hundred(value)
        )

    @classmethod
    def validate_rgb(cls, red: NUMERIC_OPT, green: NUMERIC_OPT,
                     blue: NUMERIC_OPT) -> bool:
        """Validate RGB values."""
        return all(
            cls.validate_range(val, 0, 255) for val in (red, green, blue)
        )


class Converters:
    """Helper functions to convert units."""

    @staticmethod
    def color_temp_kelvin_to_pct(kelvin: int) -> int:
        """Convert Kelvin to percentage."""
        return int((kelvin - 2700) / 153)

    @staticmethod
    def color_temp_pct_to_kelvin(pct: int) -> int:
        """Convert percentage to Kelvin."""
        return int(pct * 153 + 2700)

    @staticmethod
    def temperature_kelvin_to_celsius(kelvin: int) -> float:
        """Convert Kelvin to Celsius."""
        return kelvin - 273.15

    @staticmethod
    def temperature_celsius_to_kelvin(celsius: float) -> int:
        """Convert Celsius to Kelvin."""
        return int(celsius + 273.15)

    @staticmethod
    def temperature_fahrenheit_to_celsius(fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius."""
        return (fahrenheit - 32) * 5.0 / 9.0

    @staticmethod
    def temperature_celsius_to_fahrenheit(celsius: float) -> float:
        """Convert Celsius to Fahrenheit."""
        return celsius * 9.0 / 5.0 + 32


class Helpers:
    """VeSync Helper Functions."""

    @staticmethod
    def bump_level(level: T | None, levels: list[T]) -> T:
        """Increment level by one if not at max level."""
        if level in levels:
            idx = levels.index(level)
            if idx < len(levels) - 1:
                return levels[idx + 1]
        return levels[0]

    @staticmethod
    def try_json_loads(data: str | bytes | None) -> dict | None:
        """Try to load JSON data."""
        if data is None:
            return None
        try:
            return orjson.loads(data)
        except (orjson.JSONDecodeError, TypeError):
            return None

    @staticmethod
    def bool_to_string_status(status: bool | None | str) -> Literal['on', 'off']:
        """Get string status from boolean or string."""
        if isinstance(status, bool):
            return 'on' if status else 'off'
        return 'on' if status == 'on' else 'off'

    @staticmethod
    def get_class_attributes(target_class: object, keys: list[str]) -> dict[str, Any]:
        """Find matching attributes, static methods, and class methods from list of keys.

        This function is case insensitive and will remove underscores from the keys before
        comparing them to the class attributes. The provided keys will be returned in the
        same format if found

        Args:
            target_class (object): Class to search for attributes
            keys (list[str]): List of keys to search for

        Returns:
            dict[str, Any]: Dictionary of keys and their values from the class
        """
        alias_map = {
            'userCountryCode': 'countrycode',
            'deviceId': 'cid',
            'homeTimeZone': 'timezone',
            'configModel': 'configmodule',
            'region': 'countrycode',
        }

        def normalize_name(name: str) -> str:
            """Normalize a string by removing underscores and making it lowercase."""
            return re.sub(r'_', '', name).lower()

        def get_value(attr_name: str) -> str | float | None:
            """Get value from attribute."""
            attr = getattr(target_class, attr_name)
            try:
                return attr() if callable(attr) else attr
            except TypeError:
                return None
        result = {}
        normalized_keys = {normalize_name(key): key for key in keys}
        normalized_aliases = [normalize_name(key) for key in alias_map.values()]

        for attr_name in dir(target_class):
            normalized_attr = normalize_name(attr_name)
            if normalized_attr in normalized_keys:
                attr_val = get_value(attr_name)
                if attr_val is not None:
                    result[normalized_keys[normalized_attr]] = attr_val
            if normalized_attr in normalized_aliases:
                attr_val = get_value(attr_name)
                if attr_val is not None:
                    key_index = normalized_aliases.index(normalized_attr)
                    key_val = list(alias_map.keys())[key_index]
                    if key_val in keys:
                        result[key_val] = attr_val

        return result

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
            'accountId': manager.account_id,  # type: ignore[dict-item]
            'appVersion': APP_VERSION,
            'content-type': 'application/json',
            'tk': manager.token,  # type: ignore[dict-item]
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
        return {'timeZone': manager.time_zone, 'acceptLanguage': 'en'}

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
        return {'accountID': manager.account_id, 'token': manager.token}

    @staticmethod
    def req_body_details() -> REQUEST_T:
        """Detail keys for api requests.

        Returns:
            dict: Detail keys for api requests.

        Examples:
            >>> req_body_details()
            {
                'appVersion': APP_VERSION,
                'phoneBrand': PHONE_BRAND,
                'phoneOS': PHONE_OS,
                'traceId': str(int(time.time())),
            }
        """
        return {
            'appVersion': APP_VERSION,
            'phoneBrand': PHONE_BRAND,
            'phoneOS': PHONE_OS,
            'traceId': str(int(time.time())),
        }

    @classmethod
    def req_body(cls, manager: VeSync, type_: str) -> REQUEST_T:  # noqa: C901
        """Builder for body of api requests.

        Args:
            manager (VeSyncManager): Instance of VeSyncManager.
            type_ (str): Type of request to build body for.

        Returns:
            dict: Body dictionary for api requests.

        Note:
            The body dictionary will be built based on the type of request.
            The type of requests include:
            - login
            - devicestatus
            - devicelist
            - devicedetail
            - energy_week
            - energy_month
            - energy_year
            - bypass
            - bypassV2
            - bypass_config
        """
        body: REQUEST_T = cls.req_body_base(manager)

        if type_ == 'login':
            body |= cls.req_body_details()
            body |= {
                'email': manager.username,
                'password': cls.hash_password(manager.password),
                'devToken': '',
                'userType': USER_TYPE,
                'method': 'login'
            }
            return body

        body |= cls.req_body_auth(manager)

        if type_ == 'devicestatus':
            return body

        body |= cls.req_body_details()

        if type_ == 'devicelist':
            body['method'] = 'devices'
            body['pageNo'] = '1'
            body['pageSize'] = '100'

        elif type_ == 'devicedetail':
            body['method'] = 'devicedetail'
            body['mobileId'] = MOBILE_ID

        elif type_ == 'energy_week':
            body['method'] = 'energyweek'
            body['mobileId'] = MOBILE_ID

        elif type_ == 'energy_month':
            body['method'] = 'energymonth'
            body['mobileId'] = MOBILE_ID

        elif type_ == 'energy_year':
            body['method'] = 'energyyear'
            body['mobileId'] = MOBILE_ID

        elif type_ == 'bypass':
            body['method'] = 'bypass'

        elif type_ == 'bypassV2':
            body['deviceRegion'] = DEFAULT_REGION
            body['method'] = 'bypassV2'

        elif type_ == 'bypass_config':
            body['method'] = 'firmwareUpdateInfo'

        return body

    @staticmethod
    def calculate_hex(hex_string: str) -> float:
        """Credit for conversion to itsnotlupus/vesync_wsproxy."""
        hex_conv = hex_string.split(':')
        return (int(hex_conv[0], 16) + int(hex_conv[1], 16)) / 8192

    @staticmethod
    def hash_password(string: str) -> str:
        """Encode password."""
        return hashlib.md5(string.encode('utf-8')).hexdigest()  # noqa: S324

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
    def _get_internal_codes(response: dict) -> list[int]:
        """Get all error codes from nested dictionary.

        Args:
            response (dict): API response.

        Returns:
            list[int]: List of error codes.
        """
        error_keys = ['error', 'code', 'device_error_code', 'errorCode']

        def extract_all_error_codes(key: str, var: dict) -> Iterator[int]:
            """Find all error code keys in nested dictionary."""
            if hasattr(var, 'items'):
                for k, v in var.items():
                    if k == key and int(v) != 0:
                        yield v
                    if isinstance(v, dict):
                        yield from extract_all_error_codes(key, v)
                    elif isinstance(v, list):
                        for item in v:
                            yield from extract_all_error_codes(key, item)
        errors = []
        for error_key in error_keys:
            errors.extend(list(extract_all_error_codes(error_key, response)))
        return errors

    @classmethod
    def process_dev_response(
        cls,
        logger: logging.Logger,
        method_name: str,
        device: VeSyncBaseDevice,
        r_bytes: bytes | None,
    ) -> dict | None:
        """Process JSON response from Bytes.

        Parses bytes and checks for errors common to all JSON
        responses, included checking the "code" key for non-zero
        values. Outputs error to passed logger with formated string
        if an error is found.

        Args:
            logger (logging.Logger): Logger instance.
            method_name (str): Method used in API call.
            r_bytes (bytes | None): JSON response from API.
            device (VeSyncBaseDevice): Instance of VeSyncBaseDevice.

        Returns:
            dict | None: Parsed JSON response or None if there was an error.
        """
        device.state.update_ts()
        if r_bytes is None or len(r_bytes) == 0:
            LibraryLogger.log_device_api_response_error(
                logger,
                device.device_name,
                device.device_type,
                method_name,
                "Response empty",
            )
            return None

        try:
            r = orjson.loads(r_bytes)
        except (ValueError, orjson.JSONDecodeError):
            LibraryLogger.log_device_api_response_error(
                logger,
                device.device_name,
                device.device_type,
                method_name,
                "Error decoding JSON response",
            )
            return None

        error_code = r.get('error', {}).get('code') if 'error' in r else r.get('code')

        # Get error codes from nested dictionaries.
        if error_code == 0:
            internal_codes = cls._get_internal_codes(r)
            if internal_codes:
                error_code = internal_codes[0]

        try:
            error_int = int(error_code)
        except TypeError:
            error_int = -999999999
        error_info = ErrorCodes.get_error_info(error_int)
        if error_info.critical_error is True:
            logger.warning("%s critical error - %s",
                           device.device_name, error_info.message)
        if error_info.device_online is False:
            device.state.device_status = "off"
            device.state.connection_status = "offline"
        LibraryLogger.log_device_return_code(
            logger, method_name, device.device_name, device.device_type,
            error_code,
            f"{error_info.error_type} - {error_info.name} {error_info.message}"
            )
        device.last_response = error_info
        if error_int != 0:
            return None
        return r

    @staticmethod
    def code_check(r: dict | None) -> bool:
        """Test if code == 0 for successful API call."""
        if r is None:
            _LOGGER.error('No response from API')
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

    @classmethod
    def bypass_body_v2(cls, manager: VeSync) -> dict:
        """Build body dict for second version of bypass api calls.

        Args:
            manager (VeSyncManager): Instance of VeSyncManager.

        Returns:
            dict: Body dictionary for bypass api calls.

        Examples:
            >>> bypass_body_v2(manager)
            {
                'timeZone': manager.time_zone,
                'acceptLanguage': 'en',
                'accountID': manager.account_id,
                'token': manager.token,
                'appVersion': APP_VERSION,
                'phoneBrand': PHONE_BRAND,
                'phoneOS': PHONE_OS,
                'traceId': str(int(time.time())),
                'method': 'bypassV2',
                'debugMode': False,
                'deviceRegion': DEFAULT_REGION,
            }

        """
        bdy: dict[str, str | bool] = {}
        bdy.update(
            **cls.req_body(manager, "bypass")
        )
        bdy['method'] = 'bypassV2'
        bdy['debugMode'] = False
        bdy['deviceRegion'] = DEFAULT_REGION
        return bdy

    @staticmethod
    def bypass_header() -> dict:
        """Build bypass header dict.

        Returns:
            dict: Header dictionary for bypass api calls.

        Examples:
            >>> bypass_header()
            {
                'Content-Type': 'application/json; charset=UTF-8',
                'User-Agent': BYPASS_HEADER_UA,
            }

        """
        return {
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': 'okhttp/3.12.1',
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
            _LOGGER.error('Invalid status %s', status)
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
