"""Common base class for tests and Default values.

Routine Listings
----------------

FunctionResponses : defaultdict
    Defaultdict of the standard response tuple for device methods
Defaults: class
    Default values and methods for generating default values
"""
from typing import TypeVar, Any
from collections import defaultdict
from requests.structures import CaseInsensitiveDict
import pyvesync.const as const
from pyvesync.device_map import DeviceMapTemplate
from pyvesync.utils.colors import Color, RGB

T = TypeVar("T", bound=DeviceMapTemplate)

FunctionResponses: defaultdict = defaultdict(lambda: {"code": 0, "msg": None})

FunctionResponsesV1: defaultdict = defaultdict(
    lambda: {"traceId": TestDefaults.trace_id, "code": 0, "msg": None, "result": {}}
)

FunctionResponsesV2: defaultdict = defaultdict(
    lambda: {
        "traceId": TestDefaults.trace_id,
        "code": 0,
        "msg": None,
        "result": {"code": 0, "msg": None, "traceId": TestDefaults.trace_id, "result": {}},
    }
)

CALL_API_ARGS = ['url', 'method', 'data', 'headers']

ID_KEYS = ['CID', 'UUID', 'MACID']


def clean_name(name: str) -> str:
    """Clean the device name by removing unwanted characters."""
    return name.strip().lower().replace(" ", "_").replace("-", "_").replace(".", "_")


def build_base_response(
    code: int = 0, msg: str | None = None, merge_dict: dict | None = None
) -> dict:
    """Build the standard response response tuple."""
    resp_dict = {
        "code": code,
        "msg": msg,
        "stacktrace": None,
        "module": None,
        "traceId": TestDefaults.trace_id,
    }
    resp_dict |= merge_dict or {}
    return resp_dict


def build_bypass_v1_response(
    *,
    code: int = 0,
    msg: str | None = None,
    result_dict: dict | None = None,
    result_override: dict | None = None,
) -> dict:
    """Build the standard response response tuple.

    This function has kw-only arguments.

    Args:
        code (int): The response code.
        msg (str | None): The response message.
        result_dict (dict | None): The result dictionary.
        result_override (dict | None): dictionary to override the supplied result_dict.

    Returns:
        tuple[dict, int]: The response dictionary and status code.
    """
    resp_dict = {
        "code": code,
        "msg": msg,
        "stacktrace": None,
        "module": None,
        "traceId": TestDefaults.trace_id,
        "result": result_dict or {},
    }
    return resp_dict


def build_bypass_v2_response(
    *,
    code: int = 0,
    msg: str | None = None,
    inner_code: int = 0,
    inner_result: dict[str, Any] | None = None,
    inner_result_override: dict | None = None
) -> dict:
    """Build the standard response response tuple for BypassV2 endpoints.

    This function has kw-only arguments.

    Args:
        code(int): The response code.
        msg(str | None): The response message.
        inner_code(int): The inner response code.
        inner_result(dict | None): The inner response result.
        inner_result_override(dict | None): dictionary to override the supplied inner_result.

    Returns:
        tuple[dict, int]: The response dictionary and status code.
    """
    inner_result = inner_result or {}
    resp_dict = build_base_response(code, msg)
    if inner_result_override is not None:
        inner_result = inner_result | inner_result_override
    resp_dict['result'] = {
        "traceId": TestDefaults.trace_id,
        "code": inner_code,
        "result": inner_result,
    }
    return resp_dict


def get_device_map_from_setup_entry(module_list: list[T], setup_entry: str) -> T | None:
    """Get the device map from the setup entry.

    Args:
        module_list (list[T]): The list of device modules.
        setup_entry (str): The setup entry string.

    Returns:
        dict: The device map dictionary.
    """
    for module in module_list:
        if clean_name(module.setup_entry) == clean_name(setup_entry):
            return module
    return None


class TestDefaults:
    """General defaults for API responses and requests.

    Attributes
    ----------
    token : str
        Default token for API requests
    active_time : str
        Default active time for API responses
    account_id : str
        Default account ID for API responses
    active_time : str
        Default active time for API responses
    color: Color (dataclass)
        Red=50, Green=100, Blue=225, Hue=223, Saturation=77.78, value=88.24
        Default Color dataclass
        contains red, green, blue, hue, saturation and value attributes

    Methods
    --------
    name(dev_type='NA')
        Default device name created from "dev_type-NAME"
    cid(dev_type='NA')
        Default device cid created from "dev_type-CID"
    uuid(dev_type='NA')
        Default device uuid created from "dev_type-UUID"
    macid(dev_type='NA')
        Default device macid created from "dev_type-MACID"
    """

    token = 'sample_tk'
    account_id = 'sample_id'
    trace_id = "TRACE_ID"
    terminal_id = "TERMINAL_ID"
    app_id = "APP_ID"
    email = 'EMAIL'
    password = 'PASSWORD'
    authorization_code = "AUTHORIZATION_CODE"
    biz_token = "BIZ_TOKEN"
    region = 'US'
    country_code = 'US'
    active_time = 1
    time_zone = const.DEFAULT_TZ
    color: Color = Color(RGB(50, 100, 225))
    brightness = 100
    color_temp = 100
    bool_toggle = True
    str_toggle = 'on'
    bin_toggle = 1
    level_int = 1
    country_code = 'US'

    @staticmethod
    def name(setup_entry: str = 'NA'):
        """Name of device with format f"{setup_entry}-NAME".

        Parameters
        ----------
        setup_entry : str
            Device type use to create default name

        Returns
        -------
        str
            Default name for device f"{setup_entry}-NAME"
        """
        return f'{setup_entry}-NAME'

    @staticmethod
    def cid(setup_entry='NA'):
        """CID for a device with format f"{setup_entry}-CID".

        Parameters
        ----------
        setup_entry : str
            Device type use to create default cid

        Returns
        -------
        str
            Default cid for device f"setup_entry-CID"
        """
        return f'{setup_entry}-CID'

    @staticmethod
    def uuid(setup_entry='NA'):
        """UUID for a device with format f"{setup_entry}-UUID".

        Parameters
        ----------
        setup_entry : str
            Device type use to create default UUID

        Returns
        -------
        str
            Default uuid for device f"{setup_entry}-UUID"
        """
        return f'{setup_entry}-UUID'

    @staticmethod
    def macid(setup_entry='NA'):
        """MACID for a device with format f"{setup_entry}-MACID".

        Parameters
        ----------
        setup_entry : str
            Device type use to create default macid

        Returns
        -------
        str
            Default macID for device f"{setup_entry}-MACID"
        """
        return f'{setup_entry}-MACID'

    @staticmethod
    def config_module(setup_entry='NA'):
        """Config module for a device with format f"{setup_entry}-CONFIG".

        Parameters
        ----------
        setup_entry : str
            Device type use to create default config module

        Returns
        -------
        str
            Default config module for device f"{setup_entry}-CONFIG_MODULE"
        """
        return f'{setup_entry}-CONFIG_MODULE'


API_DEFAULTS = CaseInsensitiveDict({
    'accountID': TestDefaults.account_id,
    'token': TestDefaults.token,
    'timeZone': const.DEFAULT_TZ,
    'acceptLanguage': 'en',
    'appVersion': const.APP_VERSION,
    'phoneBrand': const.PHONE_BRAND,
    'phoneOS': const.PHONE_OS,
    'userType': const.USER_TYPE,
    "tk": TestDefaults.token,
    "traceId": "TRACE_ID",
    'verifyEmail': 'EMAIL',
    'nickName': 'NICKNAME',
    'password': 'PASSWORD',
    'username': 'EMAIL',
    'email': 'EMAIL',
    'deviceName': 'NAME'

})
