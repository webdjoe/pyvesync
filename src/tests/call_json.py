import copy
from typing import Any
import pyvesync.const as const
from defaults import TestDefaults
from pyvesync.device_map import DeviceMapTemplate
import call_json_switches
import call_json_outlets
import call_json_bulbs
import call_json_fans
import call_json_humidifiers
import call_json_purifiers


API_BASE_URL = const.API_BASE_URL
API_TIMEOUT = const.API_TIMEOUT
DEFAULT_TZ = const.DEFAULT_TZ
APP_VERSION = const.APP_VERSION
PHONE_BRAND = const.PHONE_BRAND
PHONE_OS = const.PHONE_OS
MOBILE_ID = const.MOBILE_ID
USER_TYPE = const.USER_TYPE

ALL_DEVICE_MAP_MODULES: list[DeviceMapTemplate] = [
    *call_json_bulbs.bulb_modules,
    *call_json_fans.fan_modules,
    *call_json_outlets.outlet_modules,
    *call_json_switches.switch_modules,
    *call_json_humidifiers.humidifier_modules,
    *call_json_purifiers.purifier_modules
]

ALL_DEVICE_MAP_DICT: dict[str, DeviceMapTemplate] = {
    module.setup_entry: module for module in ALL_DEVICE_MAP_MODULES
}
"""Contains dictionary of setup_entry: DeviceMapTemplate for all devices."""


"""
DEFAULT_BODY = Standard body for new device calls
DEFAULT_HEADER = standard header for most calls
DEFAULT_HEADER_BYPASS = standard header for most calls api V2
ENERGY_HISTORY = standard outlet energy history response
-------------------------------------------------------
login_call_body(email, pass) = body of login call
LOGIN_RET_BODY = return of login call
-------------------------------------------------------
get_devices_body() = body of call to get device list
LIST_CONF_10AEU = device list entry for 10A Europe outlet
LIST_CONF_10AUS = devlice list entry for 10A US outlet
LIST_CONF_7A = device list entry for 7A outlet
LIST_CONF_AIR = device list entry for air purifier
LIST_CONF_15A = device list entry for 15A outlet
LIST_CONF_WS = device list entry for wall switch
LIST_CONF_ESL100 = device list entry for bulb ESL100
LIST_CONF_OUTDOOR_1 = devlice list entry for outdoor outlet subDevice 1
LIST_CONF_OUTDOOR_2 = devlice list entry for outdoor outlet subDevice 2
DEVLIST_ALL = Return tuple for all devices
DEVLIST_10AEU = device list return for only 10A eu outlet
DEVLIST_10AUS = device list return for only 10A us outlet
DEVLIST_7A = device list return for only 7A outlet
DEVLIST_15A = device list return for only 15A outlet
DEVLIST_WS = device list return for only wall switch
DEVLIST_AIR = device list return for just air purifier
DEVLIST_ESL100 = device list return for just ESL100 bulb
DEVLIST_OUTDOOR_1 = device list return for outdoor outlet subDevice 1
DEVLIST_OUTDOOR_2 = device list return for outdoor outlet subDevice 2
---------------------------------------------------------
DETAILS_10A = Return for 10A outlet device details
DETAILS_15A = Return for 15A outlet device details
DETAILS_7A = Return for 7A outlet device details
DETAILS_WS = Return for wall switch device details
DETAILS_AIR = Return for Air Purifier device details
DETAILS_ESL100 = Return for ESL100 Bulb device details
DETAILS_OUTDOOR = return for 2 plug outdoor outlet

"""

BULBS = call_json_bulbs.BULBS
FANS = call_json_fans.FANS
OUTLETS = call_json_outlets.OUTLETS
SWITCHES = call_json_switches.SWITCHES


DEFAULT_HEADER = {
    'accept-language': 'en',
    'accountId': TestDefaults.account_id,
    'appVersion': APP_VERSION,
    'content-type': 'application/json',
    'tk': TestDefaults.token,
    'tz': DEFAULT_TZ,
}

DEFAULT_HEADER_BYPASS = {
    'Content-Type': 'application/json; charset=UTF-8',
    'User-Agent': 'okhttp/3.12.1'
}


class LoginResponses:
    GET_TOKEN_RESPONSE_SUCCESS = {
        "traceId": TestDefaults.trace_id,
        "code": 0,
        "msg": None,
        "result": {
            "accountID": TestDefaults.account_id,
            "avatarIcon": "",
            "nickName": "",
            "mailConfirmation": True,
            "registerSourceDetail": None,
            "verifyEmail": TestDefaults.email,
            "bizToken": None,
            "mfaMethodList": None,
            "authorizeCode": TestDefaults.authorization_code,
            "userType": "1",
        },
    }

    LOGIN_RESPONSE_SUCCESS = {
        "traceId": TestDefaults.trace_id,
        "code": 0,
        "msg": "request success",
        "module": None,
        "stacktrace": None,
        "result": {
            "birthday": "",
            "gender": "",
            "acceptLanguage": "en",
            "measureUnit": "Imperial",
            "weightG": 0.0,
            "heightCm": 0.0,
            "weightTargetSt": 0.0,
            "heightUnit": "FT",
            "heightFt": 0.0,
            "weightTargetKg": 0.0,
            "weightTargetLb": 0.0,
            "weightUnit": "LB",
            "maximalHeartRate": 0,
            "targetBfr": 0.0,
            "displayFlag": [],
            "targetStatus": 0,
            "realWeightKg": 0.0,
            "realWeightLb": 0.0,
            "realWeightUnit": "lb",
            "heartRateZones": 0.0,
            "runStepLongCm": 0.0,
            "walkStepLongCm": 0.0,
            "stepTarget": 0.0,
            "sleepTargetMins": 0.0,
            "regionType": 1,
            "currentRegion": TestDefaults.region,
            "token": TestDefaults.token,
            "countryCode": TestDefaults.country_code,
            "accountID": TestDefaults.account_id,
            "bizToken": None,
        },
    }

    LOGIN_RESPONSE_CROSS_REGION = {
        "traceId": "TRACE_ID",
        "code": -11260022,
        "msg": "login trigger cross region error.",
        "module": None,
        "stacktrace": None,
        "result": {
            "birthday": None,
            "gender": None,
            "acceptLanguage": None,
            "measureUnit": None,
            "weightG": None,
            "heightCm": None,
            "weightTargetSt": None,
            "heightUnit": None,
            "heightFt": None,
            "weightTargetKg": None,
            "weightTargetLb": None,
            "weightUnit": None,
            "maximalHeartRate": None,
            "targetBfr": None,
            "displayFlag": None,
            "targetStatus": None,
            "realWeightKg": None,
            "realWeightLb": None,
            "realWeightUnit": None,
            "heartRateZones": None,
            "runStepLongCm": None,
            "walkStepLongCm": None,
            "stepTarget": None,
            "sleepTargetMins": None,
            "regionType": 1,
            "currentRegion": TestDefaults.region,
            "token": None,
            "countryCode": TestDefaults.country_code,
            "accountID": TestDefaults.account_id,
            "bizToken": TestDefaults.biz_token,
        },
    }


class LoginRequests:
    authentication_success = {
        "acceptLanguage": "en",
        "accountID": "",
        "clientInfo": const.PHONE_BRAND,
        "clientType": const.CLIENT_TYPE,
        "clientVersion": const.APP_VERSION,
        "debugMode": False,
        "method": "authByPWDOrOTM",
        "osInfo": const.PHONE_OS,
        "terminalId": TestDefaults.terminal_id,
        "timeZone": const.DEFAULT_TZ,
        "token": "",
        "traceId": TestDefaults.trace_id,
        "userCountryCode": TestDefaults.country_code,
        "sourceAppID": TestDefaults.app_id,
        "appID": TestDefaults.app_id,
        "authProtocolType": "generic",
        "email": TestDefaults.email,
        "password": TestDefaults.password,
    }

    login_success = {
        "acceptLanguage": "en",
        "accountID": "",
        "clientInfo": const.PHONE_BRAND,
        "clientType": const.CLIENT_TYPE,
        "clientVersion": const.APP_VERSION,
        "debugMode": False,
        "method": "loginByAuthorizeCode4Vesync",
        "osInfo": const.PHONE_OS,
        "terminalId": TestDefaults.terminal_id,
        "timeZone": const.DEFAULT_TZ,
        "token": "",
        "traceId": TestDefaults.trace_id,
        "userCountryCode": TestDefaults.country_code,
        "authorizeCode": TestDefaults.authorization_code,
        "emailSubscriptions": False,
    }

    login_cross_region = {
        "acceptLanguage": "en",
        "accountID": "",
        "clientInfo": const.PHONE_BRAND,
        "clientType": const.CLIENT_TYPE,
        "clientVersion": const.APP_VERSION,
        "debugMode": False,
        "method": "loginByAuthorizeCode4Vesync",
        "osInfo": const.PHONE_OS,
        "terminalId": "2124569cc4905328aac52b39669b1b15e",
        "timeZone": const.DEFAULT_TZ,
        "token": "",
        "traceId": TestDefaults.trace_id,
        "userCountryCode": TestDefaults.country_code,
        "bizToken": TestDefaults.biz_token,
        "emailSubscriptions": False,
        "regionChange": "lastRegion",
    }


def BYPASS_V1_BODY(cid: str, config_module: str, json_cmd: dict):
    return {
        "traceId": TestDefaults.trace_id,
        "method": "bypass",
        "token": TestDefaults.token,
        "accountID": TestDefaults.account_id,
        "timeZone": DEFAULT_TZ,
        "acceptLanguage": "en",
        "appVersion": APP_VERSION,
        "phoneBrand": PHONE_BRAND,
        "phoneOS": PHONE_OS,
        "cid": cid,
        "configModule": config_module,
        "jsonCmd": json_cmd
    }


def login_call_body(email, password):
    json_object = {
        'acceptLanguage': 'en',
        'appVersion': APP_VERSION,
        'devToken': '',
        'email': email,
        'method': 'login',
        'password': password,
        'phoneBrand': PHONE_BRAND,
        'phoneOS': PHONE_OS,
        'timeZone': DEFAULT_TZ,
        'traceId': TestDefaults.trace_id,
        'userType': '1',
    }
    return json_object


def device_list_item(device_map: DeviceMapTemplate) -> dict:
    """Create a device list item from a device map.

    Parameters
    ----------
    device_map : DeviceMapTemplate
        Device map to create device list item from

    Returns
    -------
    dict
        Device list item dictionary
    """
    return {
        "deviceType": device_map.dev_types[0],
        "isOwner": True,
        "deviceName": TestDefaults.name(device_map.setup_entry),
        "deviceImg": "",
        "cid": TestDefaults.cid(device_map.setup_entry),
        "uuid": TestDefaults.uuid(device_map.setup_entry),
        "macID": TestDefaults.macid(device_map.setup_entry),
        "connectionType": "wifi",
        "type": device_map.product_type,
        "configModule": TestDefaults.config_module(device_map.setup_entry),
        "mode": None,
        "speed": None,
        "currentFirmVersion": None,
        "speed": None,
        "subDeviceNo": None,
        "extension": None,
        "deviceProps": None,
        "deviceStatus": const.DeviceStatus.ON,
        "connectionStatus": const.ConnectionStatus.ONLINE,
        "product_type": device_map.product_type
    }


class DeviceList:
    list_response_base: dict[str, Any] = {
        'code': 0,
        'msg': 'Success',
        'result': {
            'pageNo': 1,
            'pageSize': 100,
            'total': 0,
            'list': [],
        }
    }
    device_list_base: dict[str, Any] = {
        'extension': None,
        'isOwner': True,
        'authKey': None,
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'connectionType': 'wifi',
        'mode': None,
        'speed': None,
        'deviceProps': None,
        'configModule': 'ConfigModule',
        'deviceRegion': TestDefaults.country_code,

    }

    bulbs = dict.fromkeys(call_json_bulbs.BULBS, "wifi-light")
    outlets = dict.fromkeys(call_json_outlets.OUTLETS, "wifi-switch")
    fans = dict.fromkeys(call_json_fans.FANS, "wifi-air")
    switches = dict.fromkeys(call_json_switches.SWITCHES, "Switches")
    # purifiers = dict.fromkeys(call_json_purifiers.)

    @classmethod
    def device_list_item(cls, module: DeviceMapTemplate):
        model_types = {**cls.bulbs, **cls.outlets, **cls.fans, **cls.switches}

        device_dict = cls.device_list_base
        model_dict = device_dict.copy()
        # model_dict['deviceType'] = setup_entry
        model_dict['deviceName'] = TestDefaults.name(module.setup_entry)
        model_dict['type'] = model_types.get(module.setup_entry)
        model_dict['cid'] = TestDefaults.cid(module.setup_entry)
        model_dict['uuid'] = TestDefaults.uuid(module.setup_entry)
        model_dict['macID'] = TestDefaults.macid(module.setup_entry)
        model_dict['deviceType'] = module.dev_types[0]
        if module.setup_entry == 'ESO15-TB':
            model_dict['subDeviceNo'] = 1
        return model_dict

    @classmethod
    def device_list_response(
        cls,
        setup_entrys: list[str] | str | None = None,
    ):
        """Class method that returns the api get_devices response

        Args:
            setup_entrys (list, str optional): List or string of setup_entry(s)
                to return. Defaults to None.
        """
        if setup_entrys is None:
            entry_list = ALL_DEVICE_MAP_DICT
        elif isinstance(setup_entrys, str):
            entry_list = {
                k: v for k, v in ALL_DEVICE_MAP_DICT.items() if k == setup_entrys
            }
        elif isinstance(setup_entrys, list):
            entry_list = {
                k: v for k, v in ALL_DEVICE_MAP_DICT.items() if k in setup_entrys
            }
        response_base = copy.deepcopy(cls.list_response_base)

        response_base['result']['list'] = []
        response_base['result']['total'] = 0
        for module in entry_list.values():
            response_base['result']['list'].append(cls.device_list_item(module))
            response_base['result']['total'] += 1
        return response_base

    LIST_CONF_7A = {
        'deviceType': 'wifi-switch-1.3',
        'extension': None,
        'macID': None,
        'type': 'wifi-switch',
        'deviceName': 'Name 7A Outlet',
        'connectionType': 'wifi',
        'uuid': None,
        'speed': None,
        'deviceStatus': 'on',
        'mode': None,
        'configModule': '7AOutlet',
        'currentFirmVersion': '1.95',
        'connectionStatus': 'online',
        'cid': '7A-CID',
    }

    LIST_CONF_15A = {
        'deviceType': 'ESW15-USA',
        'extension': None,
        'macID': None,
        'type': 'wifi-switch',
        'deviceName': 'Name 15A Outlet',
        'connectionType': 'wifi',
        'uuid': 'UUID',
        'speed': None,
        'deviceStatus': 'on',
        'mode': None,
        'configModule': '15AOutletNightlight',
        'currentFirmVersion': None,
        'connectionStatus': 'online',
        'cid': '15A-CID',
    }

    LIST_CONF_WS = {
        'deviceType': 'ESWL01',
        'extension': None,
        'macID': None,
        'type': 'Switches',
        'deviceName': 'Name Wall Switch',
        'connectionType': 'wifi',
        'uuid': 'UUID',
        'speed': None,
        'deviceStatus': 'on',
        'mode': None,
        'configModule': 'InwallswitchUS',
        'currentFirmVersion': None,
        'connectionStatus': 'online',
        'cid': 'WS-CID',
    }

    LIST_CONF_10AEU = {
        'deviceType': 'ESW01-EU',
        'extension': None,
        'macID': None,
        'type': 'wifi-switch',
        'deviceName': 'Name 10A Outlet',
        'connectionType': 'wifi',
        'uuid': 'UUID',
        'speed': None,
        'deviceStatus': 'on',
        'mode': None,
        'configModule': '10AOutletEU',
        'currentFirmVersion': None,
        'connectionStatus': 'online',
        'cid': '10A-CID',
    }

    LIST_CONF_10AUS = {
        'deviceType': 'ESW03-USA',
        'extension': None,
        'macID': None,
        'type': 'wifi-switch',
        'deviceName': 'Name 10A Outlet',
        'connectionType': 'wifi',
        'uuid': 'UUID',
        'speed': None,
        'deviceStatus': 'on',
        'mode': None,
        'configModule': '10AOutletUSA',
        'currentFirmVersion': None,
        'connectionStatus': 'online',
        'cid': '10A-CID',
    }

    LIST_CONF_OUTDOOR_1 = {
        'deviceRegion': 'US',
        'deviceName': 'Outdoor Socket B',
        'cid': 'OUTDOOR-CID',
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'connectionType': 'wifi',
        'deviceType': 'ESO15-TB',
        'type': 'wifi-switch',
        'uuid': 'UUID',
        'configModule': 'OutdoorSocket15A',
        'macID': None,
        'mode': None,
        'speed': None,
        'extension': None,
        'currentFirmVersion': None,
        'subDeviceNo': 1,
    }

    LIST_CONF_OUTDOOR_2 = {
        'deviceRegion': 'US',
        'deviceName': 'Outdoor Socket B',
        'cid': 'OUTDOOR-CID',
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'connectionType': 'wifi',
        'deviceType': 'ESO15-TB',
        'type': 'wifi-switch',
        'uuid': 'UUID',
        'configModule': 'OutdoorSocket15A',
        'macID': None,
        'mode': None,
        'speed': None,
        'extension': None,
        'currentFirmVersion': None,
        'subDeviceNo': 2,
    }

    LIST_CONF_ESL100 = {
        'deviceRegion': 'US',
        'deviceName': 'Etekcity Soft White Bulb',
        'cid': 'ESL100-CID',
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'connectionType': 'wifi',
        'deviceType': 'ESL100',
        'type': 'Wifi-light',
        'uuid': 'UUID',
        'configModule': 'WifiSmartBulb',
        'macID': None,
        'mode': None,
        'speed': None,
        'extension': None,
        'currentFirmVersion': None,
        'subDeviceNo': None,
    }

    LIST_CONF_ESL100CW = {
        'deviceRegion': 'US',
        'deviceName': 'ESL100CW NAME',
        'cid': 'ESL100CW-CID',
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'connectionType': 'wifi',
        'deviceType': 'ESL100CW',
        'type': 'Wifi-light',
        'uuid': 'ESL100CW-UUID',
        'configModule': 'WifiSmartBulb',
        'macID': None,
        'mode': None,
        'speed': None,
        'extension': None,
        'currentFirmVersion': None,
        'subDeviceNo': None,
    }

    LIST_CONF_AIR = {
        'deviceName': 'Name Air Purifier',
        'cid': 'AIRPUR-CID',
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'connectionType': 'wifi',
        'deviceType': 'LV-PUR131S',
        'type': 'wifi-air',
        'uuid': 'UUID',
        'configModule': 'AirPurifier131',
        'macID': None,
        'mode': 'manual',
        'speed': 'low',
        'extension': None,
        'currentFirmVersion': None,
    }

    LIST_CONF_DUAL200S = {
        'deviceRegion': 'EU',
        'isOwner': True,
        'authKey': None,
        'deviceName': '200S NAME',
        'cid': 'CID-200S',
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'connectionType': 'WiFi+BTOnboarding+BTNotify',
        'deviceType': 'LUH-D301S-WEU',
        'type': 'wifi-air',
        'uuid': 'UUID-200S',
        'configModule': 'WFON_AHM_LUH-D301S-WEU_EU',
        'macID': None,
        'mode': None,
        'speed': None,
        'extension': None,
        'currentFirmVersion': None,
        'subDeviceNo': None,
        'subDeviceType': None,
    }

    LIST_CONF_DIMMER = {
        "deviceRegion": "US",
        "deviceName": "Etekcity Dimmer Switch",
        "cid": "DIM-CID",
        "deviceStatus": "on",
        "connectionStatus": "online",
        "connectionType": "wifi",
        "deviceType": "ESWD16",
        "type": "Switches",
        "uuid": "DIM-UUID",
        "configModule": "WifiWallDimmer"
    }

    LIST_CONF_600S = {
        'deviceRegion': 'US',
        'deviceName': 'Bedroom Humidifier',
        'deviceImg': '',
        'cid': 'CID-600S',
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'connectionType': 'WiFi+BTOnboarding+BTNotify',
        'deviceType': 'LUH-A602S-WUS',
        'type': 'wifi-air',
        'uuid': 'UUID-600S',
        'configModule': 'WFON_AHM_LUH-A602S-WUS_US',
        'macID': None,
        'subDeviceNo': None,
        'subDeviceType': None,
        'deviceProp': None
    }

    LIST_CONF_ESL100MC = {
        "cid": "CID-ESL100MC",
        "uuid": "UUID-ESL100MC",
        "macID": None,
        "subDeviceNo": 0,
        "subDeviceType": None,
        "deviceName": "ESL100MC NAME",
        "configModule": "WiFi_Bulb_MulticolorBulb_US",
        "type": "Wifi-light",
        "deviceType": "ESL100MC",
        "deviceStatus": "on",
        "connectionType": "wifi",
        "currentFirmVersion": "1.0.12",
        "connectionStatus": "online",
        "speed": None,
        "extension": None,
        "deviceProp": None
    }

    LIST_CONF_LV131S = {
        'deviceName': 'LV131S NAME',
        'cid': 'CID-LV131S',
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'connectionType': 'wifi',
        'deviceType': 'LV-PUR131S',
        'type': 'wifi-air',
        'uuid': 'UUID-LV131S',
        'configModule': 'AirPurifier131',
        'macID': None,
        'mode': 'auto',
        'speed': None,
        'extension': None,
        'currentFirmVersion': None,
        'subDeviceNo': None,
        'subDeviceType': None
    }

    LIST_CONF_VALCENO = {
        "deviceName": "VALCENO NAME",
        "cid": "CID-VALCENO",
        "deviceStatus": "on",
        "connectionStatus": "online",
        "connectionType": "WiFi+BTOnboarding+BTNotify",
        "deviceType": "XYD0001",
        "type": "Wifi-light",
        "uuid": "UUID-VALCENO",
        "configModule": "VC_WFON_BLB_A19-MC_US",
        "macID": None,
        "subDeviceNo": None,
        "subDeviceType": None
    }

    API_URL = '/cloud/v1/deviceManaged/devices'

    METHOD = 'POST'

    FULL_DEV_LIST = [
        LIST_CONF_10AEU,
        LIST_CONF_10AUS,
        LIST_CONF_15A,
        LIST_CONF_7A,
        LIST_CONF_AIR,
        LIST_CONF_WS,
        LIST_CONF_ESL100,
        LIST_CONF_OUTDOOR_1,
        LIST_CONF_OUTDOOR_2,
        LIST_CONF_DIMMER,
        LIST_CONF_600S,
        LIST_CONF_LV131S,
        LIST_CONF_DUAL200S,
        LIST_CONF_ESL100CW,
        LIST_CONF_ESL100MC,
        LIST_CONF_VALCENO

    ]

    @classmethod
    def DEVICE_LIST_RETURN(cls, dev_conf: dict) -> tuple:
        """Test the fan."""
        return (
            {
                'code': 0,
                'result':
                    {
                        'list': [dev_conf]
                    }
            },
            200
        )

    FAN_TEST = ({'code': 0, 'result': {'list': [LIST_CONF_600S, LIST_CONF_LV131S,
                                                LIST_CONF_DUAL200S]}}, 200)

    DEVLIST_ALL = ({'code': 0, 'result': {'list': FULL_DEV_LIST}}, 200)

    DEVLIST_7A = ({'code': 0, 'result': {'list': [LIST_CONF_7A]}}, 200)

    DEVLIST_15A = ({'code': 0, 'result': {'list': [LIST_CONF_15A]}}, 200)

    DEVLIST_10AEU = ({'code': 0, 'result': {'list': [LIST_CONF_10AEU]}}, 200)

    DEVLIST_10AUS = ({'code': 0, 'result': {'list': [LIST_CONF_10AUS]}}, 200)

    DEVLIST_WS = ({'code': 0, 'result': {'list': [LIST_CONF_WS]}}, 200)

    DEVLIST_DIMMER = ({'code': 0, 'result': {'list': [LIST_CONF_DIMMER]}}, 200)

    DEVLIST_AIR = ({'code': 0, 'result': {'list': [LIST_CONF_AIR]}}, 200)

    DEVLIST_ESL100 = ({'code': 0, 'result': {'list': [LIST_CONF_ESL100]}}, 200)

    DEVLIST_DUAL200S = ({'code': 0, 'result': {'list': [LIST_CONF_DUAL200S]}}, 200)

    DEVLIST_OUTDOOR = (
        {'code': 0, 'result': {'list': [LIST_CONF_OUTDOOR_1, LIST_CONF_OUTDOOR_2]}},
        200,
    )


class DeviceDetails:
    """Responses for get_details() method for all devices.

    class attributes:
    outlets : dict
        Dictionary of outlet responses for each device type.
    switches : dict
        Dictionary of switch responses for each device type.
    bulbs : dict
        Dictionary of bulb responses for each device type.
    fans : dict
        Dictionary of humidifier & air pur responses for each device type.
    all_devices : dict
        Dictionary of all device responses for each device type.

    Example
    -------
    outlets = {'ESW01-EU': {'switches': [{'outlet': 0, 'switch': 'on'}]}}
    """

    outlets = call_json_outlets.DETAILS_RESPONSES
    switches = call_json_switches.DETAILS_RESPONSES
    fans = call_json_fans.DETAILS_RESPONSES
    bulbs = call_json_bulbs.DETAILS_RESPONSES
    all_devices = {
        'outlets': outlets,
        'switches': switches,
        'fans': fans,
        'bulbs': bulbs
        }


DETAILS_BADCODE = {
    "code": 1000,
    "deviceImg": "",
    "activeTime": 1,
    "energy": 1,
    "power": "1",
    "voltage": "1",
}


STATUS_BODY = {
    'accountID': TestDefaults.account_id,
    'token': TestDefaults.token,
    'uuid': 'UUID',
    'timeZone': DEFAULT_TZ,
}


def off_body():
    body = STATUS_BODY
    body['status'] = 'off'
    return body, 200


def on_body():
    body = STATUS_BODY
    body['status'] = 'on'
    return body, 200
