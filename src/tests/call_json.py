import copy
import pyvesync.helpers as helpers
from pyvesync.vesync import APP_VERSION, PHONE_BRAND, PHONE_OS

from utils import Defaults
import call_json_switches
import call_json_outlets
import call_json_bulbs
import call_json_fans

DEFAULT_TZ = helpers.DEFAULT_TZ
MOBILE_ID = helpers.MOBILE_ID
USER_TYPE = helpers.USER_TYPE


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
    'accountId': Defaults.account_id,
    'appVersion': APP_VERSION,
    'content-type': 'application/json',
    'tk': Defaults.token,
    'tz': DEFAULT_TZ,
}

DEFAULT_HEADER_BYPASS = {
    'Content-Type': 'application/json; charset=UTF-8',
    'User-Agent': 'okhttp/3.12.1'
}


def BYPASS_V1_BODY(cid: str, config_module: str, json_cmd: dict):
    return {
        "traceId": Defaults.trace_id,
        "method": "bypass",
        "token": Defaults.token,
        "accountID": Defaults.account_id,
        "timeZone": DEFAULT_TZ,
        "acceptLanguage": "en",
        "appVersion": APP_VERSION,
        "phoneBrand": PHONE_BRAND,
        "phoneOS": PHONE_OS,
        "cid": cid,
        "configModule": config_module,
        "jsonCmd": json_cmd
    }


DEFAULT_BODY = {
    'acceptLanguage': 'en',
    'accountID': Defaults.account_id,
    'appVersion': APP_VERSION,
    'pageNo': 1,
    'pageSize': 100,
    'phoneBrand': PHONE_BRAND,
    'phoneOS': PHONE_OS,
    'timeZone': DEFAULT_TZ,
    'token': Defaults.token,
    'traceId': Defaults.trace_id,
}


LOGIN_RET_BODY = {
    'traceId': Defaults.trace_id,
    'msg': '',
    'result': {
        'accountID': Defaults.account_id,
        'avatarIcon': '',
        'acceptLanguage': 'en',
        'gdprStatus': True,
        'nickName': 'nick',
        'userType': '1',
        'token': Defaults.token,
    },
    'code': 0,
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
        'traceId': Defaults.trace_id,
        'userType': '1',
    }
    return json_object


class DeviceList:
    list_response_base = {
        'code': 0,
        'msg': 'Success',
        'result': {
            'pageNo': 1,
            'pageSize': 100,
            'total': 0,
            'list': [],
        }
    }
    device_list_base = {
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
    }

    bulbs = dict.fromkeys(call_json_bulbs.BULBS, "wifi-light")
    outlets = dict.fromkeys(call_json_outlets.OUTLETS, "wifi-switch")
    fans = dict.fromkeys(call_json_fans.FANS, "wifi-air")
    switches = dict.fromkeys(call_json_switches.SWITCHES, "Switches")

    @classmethod
    def device_list_item(cls, model, sub_device_no=0):
        model_types = {**cls.bulbs, **cls.outlets, **cls.fans, **cls.switches}

        device_dict = cls.device_list_base
        model_dict = device_dict.copy()
        model_dict['deviceType'] = model
        model_dict['deviceName'] = Defaults.name(model)
        model_dict['type'] = model_types.get(model)
        model_dict['cid'] = Defaults.cid(model)
        model_dict['uuid'] = Defaults.uuid(model)
        model_dict['macID'] = Defaults.macid(model)
        if model == 'ESO15-TB':
            model_dict['subDeviceNo'] = 1
        return model_dict

    @classmethod
    def device_list_response(cls, device_types=None, _types=None):
        """Class method that returns the api get_devices response

        Args:
            _types (list, str, optional): Can be one or list of types of devices.
                Defaults to None. can be bulb, fans, switches, outlets in list or string
            device_types (list, str optional): List or string of device_type(s)
                to return. Defaults to None.

        """

        response_base = copy.deepcopy(cls.list_response_base)
        if _types is not None:
            if isinstance(_types, list):
                full_model_list = {}
                for _type in _types:
                    device_types = full_model_list.update(cls.__dict__[_type])
            else:
                full_model_list = cls.__dict__[_types]
        else:
            full_model_list = {**cls.bulbs, **cls.outlets, **cls.fans, **cls.switches}
        if device_types is not None:
            if isinstance(device_types, list):
                full_model_list = {k: v for k, v in full_model_list.items()
                                   if k in device_types}
            else:
                full_model_list = {k: v for k, v in full_model_list.items()
                                   if k == device_types}
        for model in full_model_list:
            response_base['result']['list'].append(cls.device_list_item(model))
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
        'deviceName': 'Name 10A Outlet/EU',
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
        'deviceName': 'Name 10A Outlet/US',
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
        'deviceName': 'Outdoor Socket A',
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
        return {
                'code': 0,
                'result':
                    {
                        'list': [dev_conf]
                    }
            }

    FAN_TEST = {'code': 0, 'result': {'list': [LIST_CONF_600S, LIST_CONF_LV131S,
                                                LIST_CONF_DUAL200S]}}

    DEVLIST_ALL = {'code': 0, 'result': {'list': FULL_DEV_LIST}}

    DEVLIST_7A = {'code': 0, 'result': {'list': [LIST_CONF_7A]}}

    DEVLIST_15A = {'code': 0, 'result': {'list': [LIST_CONF_15A]}}

    DEVLIST_10AEU = {'code': 0, 'result': {'list': [LIST_CONF_10AEU]}}

    DEVLIST_10AUS = {'code': 0, 'result': {'list': [LIST_CONF_10AUS]}}

    DEVLIST_WS = {'code': 0, 'result': {'list': [LIST_CONF_WS]}}

    DEVLIST_DIMMER = {'code': 0, 'result': {'list': [LIST_CONF_DIMMER]}}

    DEVLIST_AIR = {'code': 0, 'result': {'list': [LIST_CONF_AIR]}}

    DEVLIST_ESL100 = {'code': 0, 'result': {'list': [LIST_CONF_ESL100]}}

    DEVLIST_DUAL200S = {'code': 0, 'result': {'list': [LIST_CONF_DUAL200S]}}

    DEVLIST_OUTDOOR = {'code': 0, 'msg': 'request success', 'result': {'list': [LIST_CONF_OUTDOOR_1, LIST_CONF_OUTDOOR_2]}}


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


def get_devices_body():
    """Build device body dictionary."""
    body = DEFAULT_BODY
    body['method'] = 'devices'
    return body


def get_details_body():
    body = DEFAULT_BODY
    body['method'] = 'deviceDetail'
    return body


DETAILS_BADCODE = {
    'code': 1,
    'msg' : 'FAILED',
    'deviceImg': '',
    'activeTime': 1,
    'energy': 1,
    'power': '1',
    'voltage': '1',
}

STATUS_BODY = {
    'accountID': Defaults.account_id,
    'token': Defaults.token,
    'uuid': 'UUID',
    'timeZone': DEFAULT_TZ,
}


def off_body():
    body = STATUS_BODY
    body['status'] = 'off'
    return body


def on_body():
    body = STATUS_BODY
    body['status'] = 'on'
    return body
