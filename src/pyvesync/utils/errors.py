"""Module holding VeSync API Error Codes and Response statuses.

Error codes are pulled from the VeSync app source code. If there are unknown errors
that are not found, please open an issue on GitHub.

Errors are integers divided by 1000 and then multiplied by 1000 to
get the base error code. It also tries to check if the absolute value matches
as well.

This is used by the `pyvesync.utils.helpers.Helpers.process_dev_response` method to
retrieve response code information and store in the `last_response` device instance.


The "check_device" key of the error dictionary is used to determine if the logger
should emit a warning to the user for critical device errors, such as a short
or voltage error.

The ResponseInfo class is used to define information regarding the error code or
indicate the request was successful. The ErrorTypes class is used to categorize the
error types. This is a WIP and subject to change. Should not be used for anything
other than the ErrorCodes error configuration.

Example:
    Example of the error dictionary structure:
    ```python
    pyvesync.errors.ErrorCodes.get_error_info("-11201022")
    ResponseInfo(
        name="PASSWORD_ERROR",
        error_type=ErrorTypes.AUTHENTICATION,
        msg="Invalid password"
        critical_error=False,
        operational_error=False,
        device_online=None
    )

    device.last_response
    # Returns the ResponseInfo object.
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from types import MappingProxyType

from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class ResponseInfo(DataClassORJSONMixin):
    """Class holding response information and error code definitions and lookup methods.

    Attributes:
        name (str): Name of the error
        error_type (ErrorTypes): Type of the error see `ErrorTypes`
        message (str): Message for the error
        critical_error (bool): A major error, such as a short or voltage error
        operational_error (bool): Device connected but API error
        device_online (bool | None): Device online status
        response_data (dict | None): Response data from API - populated by the
            process_dev_response method in the Helpers class and bypass mixin
            methods.
    """

    name: str
    error_type: str
    message: str
    critical_error: bool = False
    operational_error: bool = False  # Device connected but API error
    device_online: bool = True  # Defaults to connected
    response_data: dict | None = None  # Response data from API


class ErrorTypes(StrEnum):
    """Error types for API return codes.

    Attributes:
        SUCCESS: Successful request
        AUTHENTICATION: Authentication error
        RATE_LIMIT: Rate limiting error
        SERVER_ERROR: Server and connection error
        REQUEST_ERROR: Error in Request parameters or method
        DEVICE_ERROR: Device operational error, device
            connected but cannot perform requested action
        CONFIG_ERROR: Configuration error in user profie
        DEVICE_OFFLINE: Device is offline, not connected
        UNKNOWN_ERROR: Unknown error
        BAD_RESPONSE: Bad response from API
    """

    SUCCESS = 'success'
    AUTHENTICATION = 'auth_error'
    RATE_LIMIT = 'rate_limit_error'
    SERVER_ERROR = 'server_error'
    REQUEST_ERROR = 'request_error'
    DEVICE_ERROR = 'device_error'
    CONFIG_ERROR = 'config_error'
    DEVICE_OFFLINE = 'device_offline'
    UNKNOWN_ERROR = 'unknown_error'
    TOKEN_ERROR = 'token_error'
    BAD_RESPONSE = 'bad_response'
    CROSS_REGION = 'cross_region'


class ErrorCodes:
    """Class holding error code definitions and lookup methods.

    Taken from VeSync app source code. Values are `ErrorInfo` dataclasses.

    Attributes:
        errors (MappingProxyType[str, ErrorInfo]): Dictionary of error codes and
            their meanings.

    Example:
        Error codes are taken from VeSync app source code, if there are unknown errors
        that are not found, please open an issue on GitHub. The "critical_error" key of
        the error dictionary is used to determine if the logger should emit a warning.
        Used for device issues that are critical, such as a short or voltage error.

        Each error dictionary is structured as follows:
        ```
        ErrorInfo(
            name: str,
            error_type: ErrorType,
            message: str,
            critical_error: bool,
            operational_error: bool,
            device_online: bool
            )
        ```

        The `cls.critical_error(error_code)` method is used to determine if the error
        is a critical device error that should emit a warning.

        `cls.get_error_info(error_code)` method is used to return the error dictionary
        for a given error code.
    """

    errors: MappingProxyType[str, ResponseInfo] = MappingProxyType(
        {
            '-11260022': ResponseInfo(
                'CROSS_REGION_ERROR',
                ErrorTypes.CROSS_REGION,
                'Cross region error',
            ),
            '11': ResponseInfo(
                'DEVICE_OFFLINE',
                ErrorTypes.DEVICE_OFFLINE,
                'Device offline',
                device_online=False,
            ),
            '4041004': ResponseInfo(
                'DEVICE_OFFLINE',
                ErrorTypes.DEVICE_OFFLINE,
                'Device offline',
                device_online=False,
            ),
            '-11203000': ResponseInfo(
                'ACCOUNT_EXIST', ErrorTypes.AUTHENTICATION, 'Account already exists'
            ),
            '-11200000': ResponseInfo(
                'ACCOUNT_FORMAT_ERROR', ErrorTypes.CONFIG_ERROR, 'Account format error'
            ),
            '-11202000': ResponseInfo(
                'ACCOUNT_NOT_EXIST', ErrorTypes.AUTHENTICATION, 'Account does not exist'
            ),
            '-11300027': ResponseInfo(
                'AIRPURGE_OFFLINE',
                ErrorTypes.DEVICE_OFFLINE,
                'Device offline',
                device_online=False,
            ),
            '-16906000': ResponseInfo(
                'REQUEST_TOO_FREQUENT',
                ErrorTypes.RATE_LIMIT,
                'Request too frequent',
                operational_error=True,
            ),
            '-11902000': ResponseInfo(
                'AUTHKEY_NOT_EXIST', ErrorTypes.CONFIG_ERROR, 'Authkey does not exist'
            ),
            '-11900000': ResponseInfo(
                'AUTHKEY_PID_NOT_MATCH', ErrorTypes.DEVICE_ERROR, 'Authkey PID mismatch'
            ),
            '-11504000': ResponseInfo(
                'AWAY_MAX', ErrorTypes.CONFIG_ERROR, 'Away maximum reached'
            ),
            '11014000': ResponseInfo(
                'BYPASS_AIRPURIFIER_E2',
                ErrorTypes.DEVICE_ERROR,
                'Air Purifier E2 error',
                critical_error=True,
                device_online=True,
            ),
            '11802000': ResponseInfo(
                'BYPASS_AIRPURIFIER_MOTOR_ABNORMAL',
                ErrorTypes.DEVICE_ERROR,
                'Air Purifier motor error',
                critical_error=True,
                device_online=True,
            ),
            '11504000': ResponseInfo(
                'BYPASS_AWAY_MAX', ErrorTypes.CONFIG_ERROR, 'Away maximum reached'
            ),
            '11509000': ResponseInfo(
                'BYPASS_AWAY_NOT_EXIST',
                ErrorTypes.CONFIG_ERROR,
                'Away does not exist',
            ),
            '11908000': ResponseInfo(
                'BYPASS_COOK_TIMEOUT', ErrorTypes.DEVICE_ERROR, 'Cook timeout error'
            ),
            '11909000': ResponseInfo(
                'BYPASS_SMART_STOP',
                ErrorTypes.DEVICE_ERROR,
                'Smart stop error',
                device_online=True,
            ),
            '11910000': ResponseInfo(
                'BYPASS_LEFT_ZONE_COOKING',
                ErrorTypes.DEVICE_ERROR,
                'Left zone cooking error',
                device_online=True,
            ),
            '11911000': ResponseInfo(
                'BYPASS_RIGHT_ZONE_COOKING',
                ErrorTypes.DEVICE_ERROR,
                'Right zone cooking error',
                device_online=True,
            ),
            '11912000': ResponseInfo(
                'BYPASS_ALL_ZONE_COOKING',
                ErrorTypes.DEVICE_ERROR,
                'All zone cooking error',
                device_online=True,
            ),
            '11916000': ResponseInfo(
                'BYPASS_NTC_RIGHT_TOP_SHORT',
                ErrorTypes.DEVICE_ERROR,
                'Right top short error',
                critical_error=True,
                device_online=True,
            ),
            '11917000': ResponseInfo(
                'BYPASS_NTC_RIGHT_TOP_OPEN',
                ErrorTypes.DEVICE_ERROR,
                'Right top open error',
                critical_error=True,
                device_online=True,
            ),
            '11918000': ResponseInfo(
                'BYPASS_NTC_BOTTOM_SHORT',
                ErrorTypes.DEVICE_ERROR,
                'Bottom short error',
                critical_error=True,
                device_online=True,
            ),
            '11919000': ResponseInfo(
                'BYPASS_NTC_BOTTOM_OPEN',
                ErrorTypes.DEVICE_ERROR,
                'Bottom open error',
                critical_error=True,
                device_online=True,
            ),
            '11924000': ResponseInfo(
                'BYPASS_RIGHT_TEMP_FAULT',
                ErrorTypes.DEVICE_ERROR,
                'Right temperature fault',
                critical_error=True,
                device_online=True,
            ),
            '11925000': ResponseInfo(
                'BYPASS_ZONE_2_MOTOR_ABNORMAL',
                ErrorTypes.DEVICE_ERROR,
                'Zone 2 motor error',
                critical_error=True,
                device_online=True,
            ),
            '11021000': ResponseInfo(
                'BYPASS_DEVICE_END',
                ErrorTypes.DEVICE_ERROR,
                'Device end error',
                critical_error=True,
                device_online=True,
            ),
            '11012000': ResponseInfo(
                'BYPASS_DEVICE_RUNNING',
                ErrorTypes.DEVICE_ERROR,
                'Device running error',
                critical_error=True,
                device_online=True,
            ),
            '11020000': ResponseInfo(
                'BYPASS_DEVICE_STOP',
                ErrorTypes.DEVICE_ERROR,
                'Device stop error',
                device_online=True,
                critical_error=True,
            ),
            '11901000': ResponseInfo(
                'BYPASS_DOOR_OPEN',
                ErrorTypes.DEVICE_ERROR,
                'Door open error',
                critical_error=True,
                device_online=True,
            ),
            '11006000': ResponseInfo(
                'BYPASS_E1_OPEN',
                ErrorTypes.DEVICE_ERROR,
                'Open circuit error',
                critical_error=True,
                device_online=True,
            ),
            '11007000': ResponseInfo(
                'BYPASS_E2_SHORT',
                ErrorTypes.DEVICE_ERROR,
                'Short circuit error',
                device_online=True,
                critical_error=True,
            ),
            '11015000': ResponseInfo(
                'BYPASS_E3_WARM',
                ErrorTypes.DEVICE_ERROR,
                'Warm error',
                critical_error=True,
                device_online=True,
            ),
            '11018000': ResponseInfo(
                'BYPASS_SET_MIST_LEVEL',
                ErrorTypes.DEVICE_ERROR,
                'Cannot set mist level error',
                device_online=True,
            ),
            '11019000': ResponseInfo(
                'BYPASS_E6_VOLTAGE_LOW',
                ErrorTypes.DEVICE_ERROR,
                'Low voltage error',
                critical_error=True,
                device_online=True,
            ),
            '11013000': ResponseInfo(
                'BYPASS_E7_VOLTAGE',
                ErrorTypes.DEVICE_ERROR,
                'Voltage error',
                critical_error=True,
                device_online=True,
            ),
            '11607000': ResponseInfo(
                'BYPASS_HUMIDIFIER_ERROR_CONNECT_MSG',
                ErrorTypes.DEVICE_ERROR,
                'Humidifier connect message error',
            ),
            '11317000': ResponseInfo(
                'BYPASS_DIMMER_NCT',
                ErrorTypes.DEVICE_ERROR,
                'Dimmer NCT error',
                critical_error=True,
                device_online=True,
            ),
            '11608000': ResponseInfo(
                'BYPASS_HUMIDIFIER_ERROR_WATER_PUMP',
                ErrorTypes.DEVICE_ERROR,
                'Humidifier water pump error',
                critical_error=True,
                device_online=True,
            ),
            '11609000': ResponseInfo(
                'BYPASS_HUMIDIFIER_ERROR_FAN_MOTOR',
                ErrorTypes.DEVICE_ERROR,
                'Humidifier fan motor error',
                critical_error=True,
                device_online=True,
            ),
            '11601000': ResponseInfo(
                'BYPASS_HUMIDIFIER_ERROR_DRY_BURNING',
                ErrorTypes.DEVICE_ERROR,
                'Dry burning error',
                critical_error=True,
                device_online=True,
            ),
            '11602000': ResponseInfo(
                'BYPASS_HUMIDIFIER_ERROR_PTC',
                ErrorTypes.DEVICE_ERROR,
                'Humidifier PTC error',
                critical_error=True,
                device_online=True,
            ),
            '11603000': ResponseInfo(
                'BYPASS_HUMIDIFIER_ERROR_WARM_HIGH',
                ErrorTypes.DEVICE_ERROR,
                'Humidifier warm high error',
                critical_error=True,
                device_online=True,
            ),
            '11604000': ResponseInfo(
                'BYPASS_HUMIDIFIER_ERROR_WATER',
                ErrorTypes.DEVICE_ERROR,
                'Humidifier water error',
                critical_error=True,
                device_online=True,
            ),
            '11907000': ResponseInfo(
                'BYPASS_LOW_WATER',
                ErrorTypes.DEVICE_ERROR,
                'Low water error',
                device_online=True,
                critical_error=True,
            ),
            '11028000': ResponseInfo(
                'BYPASS_MOTOR_OPEN',
                ErrorTypes.DEVICE_ERROR,
                'Motor open error',
                device_online=True,
                critical_error=True,
            ),
            '11017000': ResponseInfo(
                'BYPASS_NOT_SUPPORTED', ErrorTypes.REQUEST_ERROR, 'Not supported error'
            ),
            '11905000': ResponseInfo(
                'BYPASS_NO_POT',
                ErrorTypes.DEVICE_ERROR,
                'No pot error',
                device_online=True,
                critical_error=True,
            ),
            '12001000': ResponseInfo(
                'BYPASS_LACK_FOOD',
                ErrorTypes.DEVICE_ERROR,
                'Lack of food error',
                device_online=True,
                critical_error=True,
            ),
            '12002000': ResponseInfo(
                'BYPASS_JAM_FOOD',
                ErrorTypes.DEVICE_ERROR,
                'Jam food error',
                device_online=True,
                critical_error=True,
            ),
            '12003000': ResponseInfo(
                'BYPASS_BLOCK_FOOD',
                ErrorTypes.DEVICE_ERROR,
                'Block food error',
                device_online=True,
                critical_error=True,
            ),
            '12004000': ResponseInfo(
                'BYPASS_PUMP_FAIL',
                ErrorTypes.DEVICE_ERROR,
                'Pump failure error',
                device_online=True,
                critical_error=True,
            ),
            '12005000': ResponseInfo(
                'BYPASS_CALI_FAIL',
                ErrorTypes.DEVICE_ERROR,
                'Calibration failure error',
                device_online=True,
                critical_error=True,
            ),
            '11611000': ResponseInfo(
                'BYPASS_FILTER_TRAY_ERROR',
                ErrorTypes.DEVICE_ERROR,
                'Filter tray error',
                critical_error=True,
                device_online=True,
            ),
            '11610000': ResponseInfo(
                'BYPASS_VALUE_ERROR',
                ErrorTypes.DEVICE_ERROR,
                'Value error',
                critical_error=True,
                device_online=True,
            ),
            '11022000': ResponseInfo(
                'BYPASS_CANNOT_SET_LEVEL',
                ErrorTypes.DEVICE_ERROR,
                'Cannot set level error',
                critical_error=False,
                device_online=True,
            ),
            '11023000': ResponseInfo(
                'BYPASS_NTC_BOTTOM_OPEN',
                ErrorTypes.DEVICE_ERROR,
                'NTC bottom open error',
                critical_error=True,
                device_online=True,
            ),
            '11024000': ResponseInfo(
                'BYPASS_NTC_BOTTOM_SHORT',
                ErrorTypes.DEVICE_ERROR,
                'NTC bottom short error',
                critical_error=True,
                device_online=True,
            ),
            '11026000': ResponseInfo(
                'BYPASS_NTC_TOP_OPEN',
                ErrorTypes.DEVICE_ERROR,
                'NTC top open error',
                critical_error=True,
                device_online=True,
            ),
            '11025000': ResponseInfo(
                'BYPASS_NTC_TOP_SHORT',
                ErrorTypes.DEVICE_ERROR,
                'NTC top short error',
                critical_error=True,
                device_online=True,
            ),
            '11027000': ResponseInfo(
                'BYPASS_OPEN_HEAT_PIPE_OR_OPEN_FUSE',
                ErrorTypes.DEVICE_ERROR,
                'Open heat pipe or fuse error',
                critical_error=True,
                device_online=True,
            ),
            '11906000': ResponseInfo(
                'BYPASS_OVER_HEATED',
                ErrorTypes.DEVICE_ERROR,
                'Overheated error',
                critical_error=True,
                device_online=True,
            ),
            '11000000': ResponseInfo(
                'BYPASS_PARAMETER_INVALID',
                ErrorTypes.REQUEST_ERROR,
                'Invalid bypass parameter',
            ),
            '11510000': ResponseInfo(
                'BYPASS_SCHEDULE_CONFLICT', ErrorTypes.CONFIG_ERROR, 'Schedule conflict'
            ),
            '11502000': ResponseInfo(
                'BYPASS_SCHEDULE_MAX',
                ErrorTypes.CONFIG_ERROR,
                'Maximum number of schedules reached',
            ),
            '11507000': ResponseInfo(
                'BYPASS_SCHEDULE_NOT_EXIST',
                ErrorTypes.CONFIG_ERROR,
                'Schedule does not exist',
            ),
            '11503000': ResponseInfo(
                'TIMER_MAX',
                ErrorTypes.CONFIG_ERROR,
                'Maximum number of timers reached',
            ),
            '11508000': ResponseInfo(
                'TIMER_NOT_EXIST',
                ErrorTypes.CONFIG_ERROR,
                'Timer does not exist',
            ),
            '11605000': ResponseInfo(
                'BYPASS_WATER_LOCK',
                ErrorTypes.DEVICE_ERROR,
                'Water lock error',
                critical_error=True,
                device_online=True,
            ),
            '11029000': ResponseInfo(
                'BYPASS_WIFI_ERROR', ErrorTypes.DEVICE_ERROR, 'WiFi error'
            ),
            '11902000': ResponseInfo(
                'BY_PASS_ERROR_COOKING_158',
                ErrorTypes.DEVICE_ERROR,
                'Error setting cook mode, air fryer is already cooking',
                device_online=True,
            ),
            '11035000': ResponseInfo(
                'BYPASS_MOTOR_ABNORMAL_ERROR',
                ErrorTypes.DEVICE_ERROR,
                'Motor abnormal error',
                critical_error=True,
                device_online=True,
            ),
            '11903000': ResponseInfo(
                'BY_PASS_ERROR_NOT_COOK_158',
                ErrorTypes.DEVICE_ERROR,
                'Error pausing, air fryer is not cooking',
                device_online=True,
            ),
            '-12001000': ResponseInfo(
                'CONFIGKEY_EXPIRED', ErrorTypes.CONFIG_ERROR, 'Configkey expired'
            ),
            '-12000000': ResponseInfo(
                'CONFIGKEY_NOT_EXIST',
                ErrorTypes.CONFIG_ERROR,
                'Configkey does not exist',
            ),
            '-11305000': ResponseInfo(
                'CONFIG_MODULE_NOT_EXIST',
                ErrorTypes.REQUEST_ERROR,
                'Config module does not exist',
            ),
            '-11100000': ResponseInfo(
                'DATABASE_FAILED', ErrorTypes.SERVER_ERROR, 'Database error'
            ),
            '-11101000': ResponseInfo(
                'DATABASE_FAILED_ERROR', ErrorTypes.SERVER_ERROR, 'Database error'
            ),
            '-11306000': ResponseInfo(
                'DEVICE_BOUND',
                ErrorTypes.CONFIG_ERROR,
                'Device already associated with another account',
            ),
            '-11301000': ResponseInfo(
                'DEVICE_NOT_EXIST',
                ErrorTypes.CONFIG_ERROR,
                'Device does not exist',
                device_online=False,
            ),
            '-11300000': ResponseInfo(
                'DEVICE_OFFLINE',
                ErrorTypes.DEVICE_OFFLINE,
                'Device offline',
                device_online=False,
            ),
            '-11302000': ResponseInfo(
                'DEVICE_TIMEOUT',
                ErrorTypes.DEVICE_ERROR,
                'Device timeout',
                device_online=False,
            ),
            '-11304000': ResponseInfo(
                'DEVICE_TIMEZONE_DIFF',
                ErrorTypes.CONFIG_ERROR,
                'Device timezone difference',
            ),
            '-11303000': ResponseInfo(
                'FIRMWARE_LATEST',
                ErrorTypes.CONFIG_ERROR,
                'No firmware update available',
            ),
            '-11102000': ResponseInfo(
                'INTERNAL_ERROR', ErrorTypes.SERVER_ERROR, 'Internal server error'
            ),
            '-11004000': ResponseInfo(
                'METHOD_NOT_FOUND', ErrorTypes.REQUEST_ERROR, 'Method not found'
            ),
            '-11107000': ResponseInfo(
                'MONGODB_ERROR', ErrorTypes.SERVER_ERROR, 'MongoDB error'
            ),
            '-11105000': ResponseInfo(
                'MYSQL_ERROR', ErrorTypes.SERVER_ERROR, 'MySQL error'
            ),
            '88888888': ResponseInfo(
                'NETWORK_DISABLE', ErrorTypes.SERVER_ERROR, 'Network disabled'
            ),
            '77777777': ResponseInfo(
                'NETWORK_TIMEOUT', ErrorTypes.SERVER_ERROR, 'Network timeout'
            ),
            '4031005': ResponseInfo(
                'NO_PERMISSION_7A', ErrorTypes.DEVICE_ERROR, 'No 7A Permissions'
            ),
            '-11201000': ResponseInfo(
                'PASSWORD_ERROR', ErrorTypes.AUTHENTICATION, 'Invalid password'
            ),
            '-11901000': ResponseInfo(
                'PID_NOT_EXIST', ErrorTypes.DEVICE_ERROR, 'PID does not exist'
            ),
            '-11106000': ResponseInfo(
                'REDIS_ERROR', ErrorTypes.SERVER_ERROR, 'Redis error'
            ),
            '-11003000': ResponseInfo(
                'REQUEST_HIGH', ErrorTypes.RATE_LIMIT, 'Rate limiting error'
            ),
            '-11005000': ResponseInfo(
                'RESOURCE_NOT_EXIST',
                ErrorTypes.REQUEST_ERROR,
                'No device with ID found',
                device_online=False,
            ),
            '-11108000': ResponseInfo('S3_ERROR', ErrorTypes.SERVER_ERROR, 'S3 error'),
            '-11502000': ResponseInfo(
                'SCHEDULE_MAX',
                ErrorTypes.CONFIG_ERROR,
                'Maximum number of schedules reached',
            ),
            '-11103000': ResponseInfo(
                'SERVER_BUSY', ErrorTypes.SERVER_ERROR, 'Server busy'
            ),
            '-11104000': ResponseInfo(
                'SERVER_TIMEOUT', ErrorTypes.SERVER_ERROR, 'Server timeout'
            ),
            '-11501000': ResponseInfo(
                'TIMER_CONFLICT', ErrorTypes.DEVICE_ERROR, 'Timer conflict'
            ),
            '-11503000': ResponseInfo(
                'TIMER_MAX', ErrorTypes.DEVICE_ERROR, 'Maximum number of timers reached'
            ),
            '-11500000': ResponseInfo(
                'TIMER_NOT_EXIST', ErrorTypes.DEVICE_ERROR, 'Timer does not exist'
            ),
            '-11001000': ResponseInfo(
                'TOKEN_EXPIRED', ErrorTypes.TOKEN_ERROR, 'Invalid token'
            ),
            '-999999999': ResponseInfo(
                'UNKNOWN', ErrorTypes.SERVER_ERROR, 'Unknown error'
            ),
            '-11307000': ResponseInfo(
                'UUID_NOT_EXIST',
                ErrorTypes.DEVICE_ERROR,
                'Device UUID not found',
                device_online=False,
            ),
            '12102000': ResponseInfo(
                'TEM_SENOR_ERROR',
                ErrorTypes.DEVICE_ERROR,
                'Temperature sensor error',
                critical_error=True,
                device_online=True,
            ),
            '12103000': ResponseInfo(
                'HUM_SENOR_ERROR',
                ErrorTypes.DEVICE_ERROR,
                'Humidity sensor error',
                critical_error=True,
                device_online=True,
            ),
            '12101000': ResponseInfo(
                'SENSOR_ERROR',
                ErrorTypes.DEVICE_ERROR,
                'Sensor error',
                critical_error=True,
                device_online=True,
            ),
            '11005000': ResponseInfo(
                'BYPASS_DEVICE_IS_OFF',
                ErrorTypes.DEVICE_ERROR,
                'Device is offDevice is off',
                critical_error=True,
                device_online=True,
            ),
        }
    )

    @classmethod
    def get_error_info(
        cls, error_code: str | int | None, msg: str | None = None
    ) -> ResponseInfo:
        """Return error dictionary for the given error code.

        Args:
            error_code (str | int): Error code to lookup.
            msg: (str | None): Optional message from API.

        Returns:
            dict: Error dictionary for the given error code.

        Example:
            ```python
            ErrorCodes.get_error_info("-11201022")
            ErrorInfo(
                "PASSWORD_ERROR", ErrorTypes.AUTHENTICATION, "Invalid password"
            )
            ```
        """
        try:
            if error_code is None:
                return ResponseInfo('UNKNOWN', ErrorTypes.UNKNOWN_ERROR, 'Unknown error')
            error_str = str(error_code)
            error_int = int(error_code)
            if error_str == '0':
                return ResponseInfo('SUCCESS', ErrorTypes.SUCCESS, 'Success')

            if error_str in cls.errors:
                error_info = cls.errors[error_str]
            else:
                error_code = int(error_int / 1000) * 1000
                error_object = cls.errors[str(error_code)]
                error_info = replace(error_object)

            if msg:
                error_info.message = f'{error_info.message} - {msg}'
        except (ValueError, TypeError, KeyError):
            return ResponseInfo('UNKNOWN', ErrorTypes.UNKNOWN_ERROR, 'Unknown error')
        return error_info

    @classmethod
    def is_critical(cls, error_code: str | int) -> bool:
        """Check if error code is a device error.

        Args:
            error_code (str | int): Error code to check.

        Returns:
            bool: True if error code is a device error, False otherwise.
        """
        error_info = cls.get_error_info(error_code)
        return bool(error_info.critical_error)


class VeSyncError(Exception):
    """Base exception for VeSync errors.

    These are raised based on API response codes and exceptions
    that may be raised by the different handlers.
    """


class VeSyncLoginError(VeSyncError):
    """Exception raised for login authentication errors."""

    def __init__(self, msg: str) -> None:
        """Initialize the exception with a message."""
        super().__init__(msg)


class VeSyncTokenError(VeSyncError):
    """Exception raised for VeSync API authentication errors."""

    def __init__(self, msg: str | None = None) -> None:
        """Initialize the exception with a message."""
        if msg is None or msg.strip() == '':
            msg = 'Re-authentication required'
        super().__init__(f'Token expired or invalid - {msg}')


class VeSyncServerError(VeSyncError):
    """Exception raised for VeSync API server errors."""

    def __init__(self, msg: str) -> None:
        """Initialize the exception with a message."""
        super().__init__(msg)


class VeSyncRateLimitError(VeSyncError):
    """Exception raised for VeSync API rate limit errors."""

    def __init__(self) -> None:
        """Initialize the exception with a message."""
        super().__init__('VeSync API rate limit exceeded')


class VeSyncAPIResponseError(VeSyncError):
    """Exception raised for malformed VeSync API responses."""

    def __init__(self, msg: None | str = None) -> None:
        """Initialize the exception with a message."""
        if msg is None:
            msg = 'Unexpected VeSync API response.'
        super().__init__(msg)


class VeSyncAPIStatusCodeError(VeSyncError):
    """Exception raised for malformed VeSync API responses."""

    def __init__(self, status_code: str | None = None) -> None:
        """Initialize the exception with a message."""
        message = 'VeSync API returned an unknown status code'
        if status_code is not None:
            message = f'VeSync API returned status code {status_code}'
        super().__init__(message)


def raise_api_errors(error_info: ResponseInfo) -> None:
    """Raise the appropriate exception for API error code.

    Called by `VeSync.async_call_api` method.

    Raises:
        VeSyncRateLimitError: Rate limit error
        VeSyncLoginError: Authentication error
        VeSyncTokenError: Token error
        VeSyncServerError: Server error
    """
    match error_info.error_type:
        case ErrorTypes.RATE_LIMIT:
            raise VeSyncRateLimitError
        case ErrorTypes.AUTHENTICATION:
            raise VeSyncLoginError(error_info.message)
        case ErrorTypes.SERVER_ERROR:
            msg = (
                f'{error_info.message} - '
                'Please report error to github.com/webdjoe/pyvesync/issues'
            )
            raise VeSyncServerError(msg)
