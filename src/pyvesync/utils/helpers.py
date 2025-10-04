"""Helper functions for VeSync API."""

from __future__ import annotations

import hashlib
import logging
import re
import time
from collections.abc import Iterator
from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

import orjson
from mashumaro.exceptions import InvalidFieldValue, MissingField, UnserializableField
from mashumaro.mixins.orjson import DataClassORJSONMixin
from typing_extensions import deprecated

from pyvesync.const import (
    APP_VERSION,
    BYPASS_HEADER_UA,
    DEFAULT_REGION,
    KELVIN_MAX,
    KELVIN_MIN,
    MOBILE_ID,
    PHONE_BRAND,
    PHONE_OS,
    USER_TYPE,
    ConnectionStatus,
)
from pyvesync.utils.errors import ErrorCodes, ErrorTypes, ResponseInfo
from pyvesync.utils.logs import LibraryLogger

if TYPE_CHECKING:
    from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseDevice
    from pyvesync.vesync import VeSync


T = TypeVar('T')
T_MODEL = TypeVar('T_MODEL', bound=DataClassORJSONMixin)

_LOGGER = logging.getLogger(__name__)

NUMERIC_OPT = float | str | None

NUMERIC_STRICT = float | str

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
    def validate_hsv(
        cls, hue: NUMERIC_OPT, saturation: NUMERIC_OPT, value: NUMERIC_OPT
    ) -> bool:
        """Validate HSV values."""
        return (
            cls.validate_range(hue, 0, 360)
            and cls.validate_zero_to_hundred(saturation)
            and cls.validate_zero_to_hundred(value)
        )

    @classmethod
    def validate_rgb(
        cls, red: NUMERIC_OPT, green: NUMERIC_OPT, blue: NUMERIC_OPT
    ) -> bool:
        """Validate RGB values."""
        return all(cls.validate_range(val, 0, 255) for val in (red, green, blue))


class Converters:
    """Helper functions to convert units."""

    @staticmethod
    def color_temp_kelvin_to_pct(kelvin: int) -> int:
        """Convert Kelvin to percentage."""
        return int((kelvin - KELVIN_MIN) / (KELVIN_MAX - KELVIN_MIN) * 100)

    @staticmethod
    def color_temp_pct_to_kelvin(pct: int) -> int:
        """Convert percentage to Kelvin."""
        return int(KELVIN_MIN + ((pct / 100) * (KELVIN_MAX - KELVIN_MIN)))

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
    def model_maker(
        logger: logging.Logger,
        model: type[T_MODEL],
        method_name: str,
        data: dict[str, Any],
        device: VeSyncBaseDevice | None = None,
    ) -> T_MODEL | None:
        """Create a model instance from a dictionary.

        This method catches common errors that occur when parsing the
        API response and returns None if the data is invalid. Enable debug
        or verbose logging to see more information.


        Args:
            logger (logging.Logger): Logger instance.
            model (type[T_MODEL]): Model class to create an instance of.
            method_name (str): Name of the method used in API call.
            device (VeSyncBaseDevice): Instance of VeSyncBaseDevice.
            data (dict[str, Any] | None): Dictionary to create the model from.

        Returns:
            T_MODEL: Instance of the model class.
        """
        try:
            model_instance = model.from_dict(data)
        except (MissingField, UnserializableField, InvalidFieldValue) as err:
            LibraryLogger.log_mashumaro_response_error(
                logger,
                method_name,
                data,
                err,
                device,
            )
            return None
        return model_instance

    @staticmethod
    def bump_level(level: T | None, levels: list[T]) -> T:
        """Increment level by one returning to first level if at last.

        Args:
            level (T | None): Current level.
            levels (list[T]): List of levels.
        """
        if level in levels:
            idx = levels.index(level)
            if idx < len(levels) - 1:
                return levels[idx + 1]
        return levels[0]

    @staticmethod
    def try_json_loads(data: str | bytes | None) -> dict | None:
        """Try to load JSON data.

        Gracefully handle errors and return None if loading fails.

        Args:
            data (str | bytes | None): JSON data to load.

        Returns:
            dict | None: Parsed JSON data or None if loading fails.
        """
        if data is None:
            return None
        try:
            return orjson.loads(data)
        except (orjson.JSONDecodeError, TypeError):
            return None

    @classmethod
    def process_dev_response(  # noqa: C901,PLR0912
        cls,
        logger: logging.Logger,
        method_name: str,
        device: VeSyncBaseDevice,
        r_dict: dict | None,
    ) -> dict | None:
        """Process JSON response from Bytes.

        Parses bytes and checks for errors common to all JSON
        responses, included checking the "code" key for non-zero
        values. Outputs error to passed logger with formatted string
        if an error is found. This also saves the response code information
        to the `device.last_response` attribute.

        Args:
            logger (logging.Logger): Logger instance.
            method_name (str): Method used in API call.
            r_dict (dict | None): JSON response from API.
            device (VeSyncBaseDevice): Instance of VeSyncBaseDevice.

        Returns:
            dict | None: Parsed JSON response or None if there was an error.
        """
        device.state.update_ts()
        if r_dict is None:
            logger.error('No response from API for %s', method_name)
            device.last_response = ResponseInfo(
                name='INVALID_RESPONSE',
                error_type=ErrorTypes.BAD_RESPONSE,
                message=f'No response from API for {method_name}',
            )
            return None

        error_code = (
            r_dict.get('error', {}).get('code')
            if 'error' in r_dict
            else r_dict.get('code')
        )

        new_msg = None
        # Get error codes from nested dictionaries.
        if error_code == 0:
            internal_codes = cls._get_internal_codes(r_dict)
            for code_tuple in internal_codes:
                if code_tuple[0] != 0:
                    error_code = code_tuple[0]
                    new_msg = code_tuple[1]
                    break

        if isinstance(error_code, int):
            error_int = error_code
        elif isinstance(error_code, str):
            try:
                error_int = int(error_code)
            except ValueError:
                error_int = -999999999
        else:
            error_int = -999999999
        error_info = ErrorCodes.get_error_info(error_int)
        if new_msg is not None:
            if error_info.error_type == ErrorTypes.UNKNOWN_ERROR:
                error_info.message = new_msg
            else:
                error_info.message = f'{error_info.message} - {new_msg}'
        if error_info.device_online is False:
            device.state.connection_status = ConnectionStatus.OFFLINE
        LibraryLogger.log_device_return_code(
            logger,
            method_name,
            device.device_name,
            device.device_type,
            error_int,
            f'{error_info.error_type} - {error_info.name} {error_info.message}',
        )
        device.last_response = error_info
        if error_int != 0:
            return None
        return r_dict

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
                return attr() if callable(attr) else attr  # type: ignore[no-any-return]
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
    def req_legacy_headers(manager: VeSync) -> dict[str, str]:
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
    def _req_body_base(manager: VeSync) -> dict[str, str]:
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
    def _req_body_auth(manager: VeSync) -> REQUEST_T:
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
    @deprecated('This is a legacy function and will be removed in a future release.')
    def _req_body_details() -> REQUEST_T:
        """Detail keys for api requests.

        This method is deprecated, use `get_class_attributes` instead.

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
    @deprecated('This is a legacy function and will be removed in a future release.')
    def req_body(cls, manager: VeSync, type_: str) -> REQUEST_T:  # noqa: C901
        """Builder for body of api requests.

        This method is deprecated, use `get_class_attributes` instead.

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
        body: REQUEST_T = cls._req_body_base(manager)

        if type_ == 'login':
            body |= cls._req_body_details()
            # pylint: disable=protected-access
            body |= {
                'email': manager.auth._username,  # noqa: SLF001
                'password': cls.hash_password(
                    manager.auth._password  # noqa: SLF001
                ),
                'devToken': '',
                'userType': USER_TYPE,
                'method': 'login',
            }
            return body

        body |= cls._req_body_auth(manager)

        if type_ == 'devicestatus':
            return body

        body |= cls._req_body_details()

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
        """Credit for conversion to itsnotlupus/vesync_wsproxy.

        Hex conversion for legacy outlet power and voltage.
        """
        hex_conv = hex_string.split(':')
        return (int(hex_conv[0], 16) + int(hex_conv[1], 16)) / 8192

    @staticmethod
    def hash_password(string: str) -> str:
        """Encode password."""
        return hashlib.md5(string.encode('utf-8')).hexdigest()  # noqa: S324

    @staticmethod
    def _get_internal_codes(response: dict) -> list[tuple[int, str | None]]:
        """Get all error codes from nested dictionary.

        Args:
            response (dict): API response.

        Returns:
            list[int]: List of error codes.
        """
        error_keys = ['error', 'code', 'device_error_code', 'errorCode']

        def extract_all_error_codes(
            key: str, var: dict
        ) -> Iterator[tuple[int, str | None]]:
            """Find all error code keys in nested dictionary."""
            if hasattr(var, 'items'):
                for k, v in var.items():
                    if k == key and int(v) != 0:
                        msg = var.get('msg') or var.get('result', {}).get('msg')
                        yield v, msg
                    if isinstance(v, dict):
                        yield from extract_all_error_codes(key, v)
                    elif isinstance(v, list):
                        for item in v:
                            yield from extract_all_error_codes(key, item)

        errors = []
        for error_key in error_keys:
            errors.extend(list(extract_all_error_codes(error_key, response)))
        return errors


@dataclass(repr=False)
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
        _update_time (int): Last updated unix timestamp in seconds, defaults to None

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
    _status: str = field(default='active', init=False, repr=False)
    _remain: int = field(default=0, init=False, repr=False)
    _update_time: int = int(time.time())

    def __post_init__(self, remaining: int | None) -> None:
        """Set remaining time if provided."""
        if remaining is not None:
            self._remain = remaining
        else:
            self._remain = self.timer_duration

    def __repr__(self) -> str:
        """Return string representation of the Timer object.

        Returns:
            str: String representation of the Timer object.
        """
        return (
            f'Timer(id={self.id}, duration={self.timer_duration}, '
            f'status={self.status}, remaining={self.time_remaining})'
        )

    def update_ts(self) -> None:
        """Update timestamp."""
        self._update_time = int(time.time())

    @property
    def status(self) -> str:
        """Return status of timer."""
        if self._status in ('paused', 'done'):
            return self._status
        if self.time_remaining <= 0:
            self._status = 'done'
            return 'done'
        return 'active'

    @property
    def time_remaining(self) -> int:
        """Return remaining seconds."""
        if self._status == 'paused':
            return self._remain
        if self._status == 'done':
            return 0

        # 'active' state - compute how much time has ticked away
        elapsed = time.time() - self._update_time
        current_remaining = self._remain - elapsed

        # If we've run out of time, mark it done
        if current_remaining <= 0:
            return 0
        return int(current_remaining)

    @property
    def running(self) -> bool:
        """Check if timer is active."""
        return self.time_remaining > 0 and self.status == 'active'

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

    def start(self) -> None:
        """Restart paused timer."""
        if self._status != 'paused':
            return
        self._update_time = int(time.time())
        self._status = 'active'

    def pause(self) -> None:
        """Pauses the timer if it's active.

        Performs the following steps:
            - Calculate the up-to-date remaining time,
            - Update internal counters,
            - Set _status to 'paused'.
        """
        if self._status == 'active':
            # Update the time_remaining based on elapsed
            current_remaining = self.time_remaining
            if current_remaining <= 0:
                self._status = 'done'
                self._remain = 0
            else:
                self._status = 'paused'
                self._remain = current_remaining
            self._update_time = int(time.time())
