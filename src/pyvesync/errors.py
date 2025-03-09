"""Module holding VeSync API Error Codes.

Error codes are pulled from the VeSync app source code. If there are unknown errors
that are not found, please open an issue on GitHub.

Errors are integers divided by 1000 and then multiplied by 1000 to
get the base error code.

The "check_device" key of the error dictionary is used to determine if the logger
should emit a warning to the user for critical device errors, such as a short
or voltage error.

Example:
    Example of the error dictionary structure:
    >>> pyvesync.errors.ErrorCodes.get_error_info("-11201022")
    ErrorInfo(
"PASSWORD_ERROR", ErrorTypes.AUTHENTICATION, "Invalid password"
)

Note:
    The ErrorTypes class is used to categorize the error types. This is a WIP
    and subject to change. Should not be used for anything other than the ErrorCodes
    error configuration.

"""

from dataclasses import dataclass
from types import MappingProxyType
from enum import Enum


@dataclass
class ErrorInfo:
    """Class holding error code definitions and lookup methods.

    Attributes:
        name (str): Name of the error
        error_type (ErrorTypes): Type of the error see `ErrorTypes`
        message (str): Message for the error
        check_device (bool): Whether to emit warning, optional
    """

    name: str
    error_type: "ErrorTypes"
    message: str
    critical_error: bool = False
    operational_error: bool = False  # Device connected but API error
    device_online: bool = True  # Defaults to not connected


class ErrorTypes(Enum):
    """Error types for API return codes.

    Attributes:
        AUTHENTICATION: Authentication error
        RATE_LIMIT: Rate limiting error
        SERVER_ERROR: Server and connection error
        REQUEST_ERROR: Error in Request parameters or method
        DEVICE_ERROR: Device operational error, device
            connected but cannot perform requested action
        CONFIG_ERROR: Configuration error in user profie
        DEVICE_OFFLINE: Device is offline, not connected
        UNKNOWN_ERROR: Unknown error
    """

    SUCCESS = "success"
    AUTHENTICATION = "auth_error"
    RATE_LIMIT = "rate_limit_error"
    SERVER_ERROR = "server_error"
    REQUEST_ERROR = "request_error"
    DEVICE_ERROR = "device_error"
    CONFIG_ERROR = "config_error"
    DEVICE_OFFLINE = "device_offline"
    UNKNOWN_ERROR = "unknown_error"


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
        ErrorInfo(name: str, error_type: ErrorType, message: str, critical_error: bool)
        ```

        The `cls.critical_error(error_code)` method is used to determine if the error
        is a critical device error that should emit a warning.

        `cls.get_error_info(error_code)` method is used to return the error dictionary
        for a given error code.
    """

    errors: MappingProxyType[str, ErrorInfo] = MappingProxyType(
        {
            "11": ErrorInfo(
                "DEVICE_OFFLINE",
                ErrorTypes.DEVICE_OFFLINE,
                "Device offline",
                device_online=False,
            ),
            "4041004": ErrorInfo(
                "DEVICE_OFFLINE",
                ErrorTypes.DEVICE_OFFLINE,
                "Device offline",
                device_online=False,
            ),
            "-11203000": ErrorInfo(
                "ACCOUNT_EXIST", ErrorTypes.AUTHENTICATION, "Account already exists"
            ),
            "-11200000": ErrorInfo(
                "ACCOUNT_FORMAT_ERROR", ErrorTypes.CONFIG_ERROR, "Account format error"
            ),
            "-11202000": ErrorInfo(
                "ACCOUNT_NOT_EXIST", ErrorTypes.AUTHENTICATION, "Account does not exist"
            ),
            "-11300027": ErrorInfo(
                "AIRPURGE_OFFLINE",
                ErrorTypes.DEVICE_OFFLINE,
                "Device offline",
                device_online=False,
            ),
            "-11902000": ErrorInfo(
                "AUTHKEY_NOT_EXIST", ErrorTypes.CONFIG_ERROR, "Authkey does not exist"
            ),
            "-11900000": ErrorInfo(
                "AUTHKEY_PID_NOT_MATCH", ErrorTypes.DEVICE_ERROR, "Authkey PID mismatch"
            ),
            "-11504000": ErrorInfo(
                "AWAY_MAX", ErrorTypes.CONFIG_ERROR, "Away maximum reached"
            ),
            "11014000": ErrorInfo(
                "BYPASS_AIRPURIFIER_E2",
                ErrorTypes.DEVICE_ERROR,
                "Air Purifier E2 error",
                True,
            ),
            "11802000": ErrorInfo(
                "BYPASS_AIRPURIFIER_MOTOR_ABNORMAL",
                ErrorTypes.DEVICE_ERROR,
                "Air Purifier motor error",
                True,
            ),
            "11504000": ErrorInfo(
                "BYPASS_AWAY_MAX", ErrorTypes.CONFIG_ERROR, "Away maximum reached"
            ),
            "11509000": ErrorInfo(
                "BYPASS_AWAY_NOT_EXIST", ErrorTypes.CONFIG_ERROR, "Away does not exist"
            ),
            "11908000": ErrorInfo(
                "BYPASS_COOK_TIMEOUT", ErrorTypes.DEVICE_ERROR, "Cook timeout error"
            ),
            "11021000": ErrorInfo(
                "BYPASS_DEVICE_END", ErrorTypes.DEVICE_ERROR, "Device end error", True
            ),
            "11012000": ErrorInfo(
                "BYPASS_DEVICE_RUNNING",
                ErrorTypes.DEVICE_ERROR,
                "Device running error",
                True,
            ),
            "11020000": ErrorInfo(
                "BYPASS_DEVICE_STOP", ErrorTypes.DEVICE_ERROR, "Device stop error", True
            ),
            "11901000": ErrorInfo(
                "BYPASS_DOOR_OPEN", ErrorTypes.DEVICE_ERROR, "Door open error", True
            ),
            "11006000": ErrorInfo(
                "BYPASS_E1_OPEN", ErrorTypes.DEVICE_ERROR, "Open circuit error", True
            ),
            "11007000": ErrorInfo(
                "BYPASS_E2_SHORT", ErrorTypes.DEVICE_ERROR, "Short circuit error", True
            ),
            "11015000": ErrorInfo(
                "BYPASS_E3_WARM", ErrorTypes.DEVICE_ERROR, "Warm error", True
            ),
            "11019000": ErrorInfo(
                "BYPASS_E6_VOLTAGE_LOW",
                ErrorTypes.DEVICE_ERROR,
                "Low voltage error",
                True,
            ),
            "11013000": ErrorInfo(
                "BYPASS_E7_VOLTAGE", ErrorTypes.DEVICE_ERROR, "Voltage error", True
            ),
            "11607000": ErrorInfo(
                "BYPASS_HUMIDIFIER_ERROR_CONNECT_MSG",
                ErrorTypes.DEVICE_ERROR,
                "Humidifier connect message error",
            ),
            "11601000": ErrorInfo(
                "BYPASS_HUMIDIFIER_ERROR_DRY_BURNING",
                ErrorTypes.DEVICE_ERROR,
                "Dry burning error",
                True,
            ),
            "11602000": ErrorInfo(
                "BYPASS_HUMIDIFIER_ERROR_PTC",
                ErrorTypes.DEVICE_ERROR,
                "Humidifier PTC error",
                True,
            ),
            "11603000": ErrorInfo(
                "BYPASS_HUMIDIFIER_ERROR_WARM_HIGH",
                ErrorTypes.DEVICE_ERROR,
                "Humidifier warm high error",
                True,
            ),
            "11604000": ErrorInfo(
                "BYPASS_HUMIDIFIER_ERROR_WATER",
                ErrorTypes.DEVICE_ERROR,
                "Humidifier water error",
                True,
            ),
            "11907000": ErrorInfo(
                "BYPASS_LOW_WATER", ErrorTypes.DEVICE_ERROR, "Low water error", True
            ),
            "11028000": ErrorInfo(
                "BYPASS_MOTOR_OPEN", ErrorTypes.DEVICE_ERROR, "Motor open error", True
            ),
            "11017000": ErrorInfo(
                "BYPASS_NOT_SUPPORTED", ErrorTypes.REQUEST_ERROR, "Not supported error"
            ),
            "11905000": ErrorInfo(
                "BYPASS_NO_POT", ErrorTypes.DEVICE_ERROR, "No pot error", True
            ),
            "11023000": ErrorInfo(
                "BYPASS_NTC_BOTTOM_OPEN",
                ErrorTypes.DEVICE_ERROR,
                "NTC bottom open error",
                True,
            ),
            "11024000": ErrorInfo(
                "BYPASS_NTC_BOTTOM_SHORT",
                ErrorTypes.DEVICE_ERROR,
                "NTC bottom short error",
                True,
            ),
            "11026000": ErrorInfo(
                "BYPASS_NTC_TOP_OPEN",
                ErrorTypes.DEVICE_ERROR,
                "NTC top open error",
                True,
            ),
            "11025000": ErrorInfo(
                "BYPASS_NTC_TOP_SHORT",
                ErrorTypes.DEVICE_ERROR,
                "NTC top short error",
                True,
            ),
            "11027000": ErrorInfo(
                "BYPASS_OPEN_HEAT_PIPE_OR_OPEN_FUSE",
                ErrorTypes.DEVICE_ERROR,
                "Open heat pipe or fuse error",
                True,
            ),
            "11906000": ErrorInfo(
                "BYPASS_OVER_HEATED", ErrorTypes.DEVICE_ERROR, "Overheated error", True
            ),
            "11000000": ErrorInfo(
                "BYPASS_PARAMETER_INVALID",
                ErrorTypes.REQUEST_ERROR,
                "Invalid bypass parameter",
            ),
            "11510000": ErrorInfo(
                "BYPASS_SCHEDULE_CONFLICT", ErrorTypes.CONFIG_ERROR, "Schedule conflict"
            ),
            "11502000": ErrorInfo(
                "BYPASS_SCHEDULE_MAX",
                ErrorTypes.CONFIG_ERROR,
                "Maximum number of schedules reached",
            ),
            "11507000": ErrorInfo(
                "BYPASS_SCHEDULE_NOT_EXIST",
                ErrorTypes.CONFIG_ERROR,
                "Schedule does not exist",
            ),
            "11503000": ErrorInfo(
                "BYPASS_TIMER_MAX",
                ErrorTypes.CONFIG_ERROR,
                "Maximum number of timers reached",
            ),
            "11508000": ErrorInfo(
                "BYPASS_TIMER_NOT_EXIST",
                ErrorTypes.CONFIG_ERROR,
                "Timer does not exist",
            ),
            "11605000": ErrorInfo(
                "BYPASS_WATER_LOCK", ErrorTypes.DEVICE_ERROR, "Water lock error", True
            ),
            "11029000": ErrorInfo(
                "BYPASS_WIFI_ERROR", ErrorTypes.DEVICE_ERROR, "WiFi error"
            ),
            "11902000": ErrorInfo(
                "BY_PASS_ERROR_COOKING_158",
                ErrorTypes.DEVICE_ERROR,
                "Error setting cook mode, air fryer is already cooking",
                True,
            ),
            "11903000": ErrorInfo(
                "BY_PASS_ERROR_NOT_COOK_158",
                ErrorTypes.DEVICE_ERROR,
                "Error pausing, air fryer is not cooking",
                True,
            ),
            "-12001000": ErrorInfo(
                "CONFIGKEY_EXPIRED", ErrorTypes.CONFIG_ERROR, "Configkey expired"
            ),
            "-12000000": ErrorInfo(
                "CONFIGKEY_NOT_EXIST",
                ErrorTypes.CONFIG_ERROR,
                "Configkey does not exist",
            ),
            "-11305000": ErrorInfo(
                "CONFIG_MODULE_NOT_EXIST",
                ErrorTypes.CONFIG_ERROR,
                "Config module does not exist",
            ),
            "-11100000": ErrorInfo(
                "DATABASE_FAILED", ErrorTypes.SERVER_ERROR, "Database error"
            ),
            "-11101000": ErrorInfo(
                "DATABASE_FAILED_ERROR", ErrorTypes.SERVER_ERROR, "Database error"
            ),
            "-11306000": ErrorInfo(
                "DEVICE_BOUND",
                ErrorTypes.CONFIG_ERROR,
                "Device already associated with another account",
            ),
            "-11301000": ErrorInfo(
                "DEVICE_NOT_EXIST",
                ErrorTypes.CONFIG_ERROR,
                "Device does not exist",
                device_online=False,
            ),
            "-11300000": ErrorInfo(
                "DEVICE_OFFLINE",
                ErrorTypes.DEVICE_OFFLINE,
                "Device offline",
                device_online=False,
            ),
            "-11302000": ErrorInfo(
                "DEVICE_TIMEOUT",
                ErrorTypes.DEVICE_ERROR,
                "Device timeout",
                device_online=False,
            ),
            "-11304000": ErrorInfo(
                "DEVICE_TIMEZONE_DIFF",
                ErrorTypes.CONFIG_ERROR,
                "Device timezone difference",
            ),
            "-11303000": ErrorInfo(
                "FIRMWARE_LATEST",
                ErrorTypes.CONFIG_ERROR,
                "No firmware update available",
            ),
            "-11102000": ErrorInfo(
                "INTERNAL_ERROR", ErrorTypes.SERVER_ERROR, "Internal server error"
            ),
            "-11004000": ErrorInfo(
                "METHOD_NOT_FOUND", ErrorTypes.REQUEST_ERROR, "Method not found"
            ),
            "-11107000": ErrorInfo(
                "MONGODB_ERROR", ErrorTypes.SERVER_ERROR, "MongoDB error"
            ),
            "-11105000": ErrorInfo("MYSQL_ERROR", ErrorTypes.SERVER_ERROR, "MySQL error"),
            "88888888": ErrorInfo(
                "NETWORK_DISABLE", ErrorTypes.SERVER_ERROR, "Network disabled"
            ),
            "77777777": ErrorInfo(
                "NETWORK_TIMEOUT", ErrorTypes.SERVER_ERROR, "Network timeout"
            ),
            "4031005": ErrorInfo(
                "NO_PERMISSION_7A", ErrorTypes.DEVICE_ERROR, "No 7A Permissions"
            ),
            "-11201000": ErrorInfo(
                "PASSWORD_ERROR", ErrorTypes.AUTHENTICATION, "Invalid password"
            ),
            "-11901000": ErrorInfo(
                "PID_NOT_EXIST", ErrorTypes.DEVICE_ERROR, "PID does not exist"
            ),
            "-11106000": ErrorInfo("REDIS_ERROR", ErrorTypes.SERVER_ERROR, "Redis error"),
            "-11003000": ErrorInfo(
                "REQUEST_HIGH", ErrorTypes.RATE_LIMIT, "Rate limiting error"
            ),
            "-11005000": ErrorInfo(
                "RESOURCE_NOT_EXIST",
                ErrorTypes.REQUEST_ERROR,
                "No device with ID found",
                device_online=False,
            ),
            "-11108000": ErrorInfo("S3_ERROR", ErrorTypes.SERVER_ERROR, "S3 error"),
            "-11502000": ErrorInfo(
                "SCHEDULE_MAX",
                ErrorTypes.CONFIG_ERROR,
                "Maximum number of schedules reached",
            ),
            "-11103000": ErrorInfo("SERVER_BUSY", ErrorTypes.SERVER_ERROR, "Server busy"),
            "-11104000": ErrorInfo(
                "SERVER_TIMEOUT", ErrorTypes.SERVER_ERROR, "Server timeout"
            ),
            "-11501000": ErrorInfo(
                "TIMER_CONFLICT", ErrorTypes.DEVICE_ERROR, "Timer conflict"
            ),
            "-11503000": ErrorInfo(
                "TIMER_MAX", ErrorTypes.DEVICE_ERROR, "Maximum number of timers reached"
            ),
            "-11500000": ErrorInfo(
                "TIMER_NOT_EXIST", ErrorTypes.DEVICE_ERROR, "Timer does not exist"
            ),
            "-11001000": ErrorInfo(
                "TOKEN_EXPIRED", ErrorTypes.AUTHENTICATION, "Invalid token"
            ),
            "-999999999": ErrorInfo("UNKNOWN", ErrorTypes.SERVER_ERROR, "Unknown error"),
            "-11307000": ErrorInfo(
                "UUID_NOT_EXIST",
                ErrorTypes.DEVICE_ERROR,
                "Device UUID not found",
                device_online=False,
            ),
        }
    )

    @classmethod
    def get_error_info(cls, error_code: str | int | None) -> ErrorInfo:
        """Return error dictionary for the given error code.

        Args:
            error_code (str | int): Error code to lookup.

        Returns:
            dict: Error dictionary for the given error code.

        Example:
            >>> ErrorCodes.get_error_info("-11201022")
            ErrorInfo(
                "PASSWORD_ERROR", ErrorTypes.AUTHENTICATION, "Invalid password"
            )
        """
        try:
            if isinstance(error_code, str):
                error_str = error_code
            elif isinstance(error_code, int):
                error_str = str(error_code)
            else:
                return ErrorInfo("UNKNOWN", ErrorTypes.UNKNOWN_ERROR, "Unknown error")
            if error_str == "0":
                return ErrorInfo("SUCCESS", ErrorTypes.SUCCESS, "Success")
            if error_str in cls.errors:
                return cls.errors[error_str]
            error_int = int(error_str)
            error_code = int(error_int / 1000) * 1000
            return cls.errors[error_str]
        except (ValueError, TypeError, KeyError):
            return ErrorInfo("UNKNOWN", ErrorTypes.UNKNOWN_ERROR, "Unknown error")

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
