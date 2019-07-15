import time
import pyvesync.helpers as helpers

API_BASE_URL = helpers.API_BASE_URL
API_RATE_LIMIT = helpers.API_RATE_LIMIT
API_TIMEOUT = helpers.API_TIMEOUT
DEFAULT_TZ = helpers.DEFAULT_TZ
APP_VERSION = helpers.APP_VERSION
PHONE_BRAND = helpers.PHONE_BRAND
PHONE_OS = helpers.PHONE_OS
MOBILE_ID = helpers.MOBILE_ID
USER_TYPE = helpers.USER_TYPE

SAMPLE_ACTID = 'sample_id'
SAMPLE_TOKEN = 'sample_tk'
TRACE_ID = str(int(time.time()))
"""
DEFAULT_BODY = Standard body for new device calls
DEFAULT_HEADER = standard header for most calls
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

DEFAULT_HEADER = {
    'accept-language': 'en',
    'accountId': SAMPLE_ACTID,
    'appVersion': APP_VERSION,
    'content-type': 'application/json',
    'tk': SAMPLE_TOKEN,
    'tz': DEFAULT_TZ
}

DEFAULT_BODY = {
    "acceptLanguage": "en",
    "accountID": SAMPLE_ACTID,
    "appVersion": APP_VERSION,
    "pageNo": 1,
    "pageSize": 50,
    "phoneBrand": PHONE_BRAND,
    "phoneOS": PHONE_OS,
    "timeZone": DEFAULT_TZ,
    "token": SAMPLE_TOKEN,
    "traceId": TRACE_ID
}

ENERGY_HISTORY = ({
    "code": 0,
    "energyConsumptionOfToday": 1,
    "costPerKWH": 1,
    "maxEnergy": 1,
    "totalEnergy": 1,
    "data": [
        1,
        1,
    ]
}, 200)

LOGIN_RET_BODY = ({
    "traceId": TRACE_ID,
    "msg": "",
    "result": {
        "accountID": SAMPLE_ACTID,
        "avatarIcon": "",
        "acceptLanguage": "en",
        "gdprStatus": True,
        "nickName": "nick",
        "userType": "1",
        "token": SAMPLE_TOKEN
    },
    "code": 0
}, 200)


def login_call_body(email, password):
    json = {
        "acceptLanguage": "en",
        "appVersion": APP_VERSION,
        "devToken": "",
        "email": email,
        "method": "login",
        "password": password,
        "phoneBrand": PHONE_BRAND,
        "phoneOS": PHONE_OS,
        "timeZone": DEFAULT_TZ,
        "traceId": TRACE_ID,
        "userType": "1"
    }
    return json


LIST_CONF_7A = {
    "deviceType": "wifi-switch-1.3",
    "extension": None,
    "macID": None,
    "type": "wifi-switch",
    "deviceName": "Name 7A Outlet",
    "connectionType": "wifi",
    "uuid": None,
    "speed": None,
    "deviceStatus": "on",
    "mode": None,
    "configModule": "7AOutlet",
    "currentFirmVersion": "1.95",
    "connectionStatus": "online",
    "cid": "7A-CID"
}

LIST_CONF_15A = {
    "deviceType": "ESW15-USA",
    "extension": None,
    "macID": None,
    "type": "wifi-switch",
    "deviceName": "Name 15A Outlet",
    "connectionType": "wifi",
    "uuid": "UUID",
    "speed": None,
    "deviceStatus": "on",
    "mode": None,
    "configModule": "15AOutletNightlight",
    "currentFirmVersion": None,
    "connectionStatus": "online",
    "cid": "15A-CID"
}

LIST_CONF_WS = {
    "deviceType": "ESWL01",
    "extension": None,
    "macID": None,
    "type": "Switches",
    "deviceName": "Name Wall Switch",
    "connectionType": "wifi",
    "uuid": "UUID",
    "speed": None,
    "deviceStatus": "on",
    "mode": None,
    "configModule": "InwallswitchUS",
    "currentFirmVersion": None,
    "connectionStatus": "online",
    "cid": "WS-CID"
}

LIST_CONF_10AEU = {
    "deviceType": "ESW01-EU",
    "extension": None,
    "macID": None,
    "type": "wifi-switch",
    "deviceName": "Name 10A Outlet",
    "connectionType": "wifi",
    "uuid": "UUID",
    "speed": None,
    "deviceStatus": "on",
    "mode": None,
    "configModule": "10AOutletEU",
    "currentFirmVersion": None,
    "connectionStatus": "online",
    "cid": "10A-CID"
}

LIST_CONF_10AUS = {
    "deviceType": "ESW03-USA",
    "extension": None,
    "macID": None,
    "type": "wifi-switch",
    "deviceName": "Name 10A Outlet",
    "connectionType": "wifi",
    "uuid": "UUID",
    "speed": None,
    "deviceStatus": "on",
    "mode": None,
    "configModule": "10AOutletUSA",
    "currentFirmVersion": None,
    "connectionStatus": "online",
    "cid": "10A-CID"
}

LIST_CONF_OUTDOOR_1 = {
    "deviceRegion": "US",
    "deviceName": "Outdoor Socket B",
    "cid": "OUTDOOR-CID",
    "deviceStatus": "on",
    "connectionStatus": "online",
    "connectionType": "wifi",
    "deviceType": "ESO15-TB",
    "type": "wifi-switch",
    "uuid": "UUID",
    "configModule": "OutdoorSocket15A",
    "macID": None,
    "mode": None,
    "speed": None,
    "extension": None,
    "currentFirmVersion": None,
    "subDeviceNo": 1
}

LIST_CONF_OUTDOOR_2 = {
    "deviceRegion": "US",
    "deviceName": "Outdoor Socket B",
    "cid": "OUTDOOR-CID",
    "deviceStatus": "on",
    "connectionStatus": "online",
    "connectionType": "wifi",
    "deviceType": "ESO15-TB",
    "type": "wifi-switch",
    "uuid": "UUID",
    "configModule": "OutdoorSocket15A",
    "macID": None,
    "mode": None,
    "speed": None,
    "extension": None,
    "currentFirmVersion": None,
    "subDeviceNo": 2
}

LIST_CONF_ESL100 = {
    "deviceRegion": "US",
    "deviceName": "Etekcity Soft White Bulb",
    "cid": "ESL100-CID",
    "deviceStatus": "on",
    "connectionStatus": "online",
    "connectionType": "wifi",
    "deviceType": "ESL100",
    "type": "Wifi-light",
    "uuid": "UUID",
    "configModule": "WifiSmartBulb",
    "macID": None,
    "mode": None,
    "speed": None,
    "extension": None,
    "currentFirmVersion": None,
    "subDeviceNo": None
}

LIST_CONF_AIR = {
    "deviceName": "Name Air Purifier",
    "cid": "AIRPUR-CID",
    "deviceStatus": "on",
    "connectionStatus": "online",
    "connectionType": "wifi",
    "deviceType": "LV-PUR131S",
    "type": "wifi-air",
    "uuid": "UUID",
    "configModule": "AirPurifier131",
    "macID": None,
    "mode": "manual",
    "speed": "low",
    "extension": None,
    "currentFirmVersion": None
}

FULL_DEV_LIST = [
    LIST_CONF_10AEU, LIST_CONF_10AUS, LIST_CONF_15A, LIST_CONF_7A,
    LIST_CONF_AIR, LIST_CONF_WS, LIST_CONF_ESL100, LIST_CONF_OUTDOOR_1,
    LIST_CONF_OUTDOOR_2
]


def get_devices_body():
    body = DEFAULT_BODY
    body['method'] = 'devices'
    return (body, 200)


DEVLIST_ALL = ({'code': 0, 'result': {'list': FULL_DEV_LIST}}, 200)

DEVLIST_7A = ({'code': 0, 'result': {'list': [LIST_CONF_7A]}}, 200)

DEVLIST_15A = ({'code': 0, 'result': {'list': [LIST_CONF_15A]}}, 200)

DEVLIST_10AEU = ({'code': 0, 'result': {'list': [LIST_CONF_10AEU]}}, 200)

DEVLIST_10AUS = ({'code': 0, 'result': {'list': [LIST_CONF_10AUS]}}, 200)

DEVLIST_WS = ({'code': 0, 'result': {'list': [LIST_CONF_WS]}}, 200)

DEVLIST_AIR = ({'code': 0, 'result': {'list': [LIST_CONF_AIR]}}, 200)

DEVLIST_ESL100 = ({'code': 0, 'result': {'list': [LIST_CONF_ESL100]}}, 200)

DEVLIST_OUTDOOR = ({
    'code': 0,
    'result': {
        'list': [LIST_CONF_OUTDOOR_1, LIST_CONF_OUTDOOR_2]
    }
}, 200)


def get_details_body():
    body = DEFAULT_BODY
    body['method'] = 'deviceDetail'
    return (body, 200)


DETAILS_15A = ({
    "code": 0,
    "msg": None,
    "deviceStatus": "on",
    "connectionStatus": "online",
    "activeTime": 1,
    "energy": 1,
    "nightLightStatus": "on",
    "nightLightBrightness": 50,
    "nightLightAutomode": "manual",
    "power": "1",
    "voltage": "1"
}, 200)

DETAILS_7A = ({
    "deviceStatus": "on",
    "deviceImg": "",
    "activeTime": 1,
    "energy": 1,
    "power": "1000:1000",
    "voltage": "1000:1000"
}, 200)

DETAILS_WS = ({
    "code": 0,
    "msg": None,
    "deviceStatus": "on",
    "connectionStatus": "online",
    "activeTime": 1,
    "power": "None",
    "voltage": "None"
}, 200)

DETAILS_10A = ({
    "code": 0,
    "msg": None,
    "deviceStatus": "on",
    "connectionStatus": "online",
    "activeTime": 1,
    "energy": 1,
    "nightLightStatus": None,
    "nightLightBrightness": None,
    "nightLightAutomode": None,
    "power": "1",
    "voltage": "1"
}, 200)

DETAILS_OUTDOOR = ({
    "code": 0,
    "msg": None,
    "connectionStatus": "online",
    "activeTime": 1,
    "energy": 1,
    "power": "1",
    "voltage": "1",
    "deviceStatus": "on",
    "deviceName": "Etekcity Outdoor Plug",
    "subDevices": [{
        "subDeviceNo": 1,
        "defaultName": "Socket A",
        "subDeviceName": "Outdoor Socket A",
        "subDeviceStatus": "on",
    }, {
        "subDeviceNo": 2,
        "defaultName": "Socket B",
        "subDeviceName": "Outdoor Socket B",
        "subDeviceStatus": "on",
    }]
}, 200)

DETAILS_ESL100 = ({
    "code": 0,
    "msg": None,
    "deviceStatus": "on",
    "connectionStatus": "online",
    "name": "Etekcity Soft White Bulb",
    "brightNess": "1",
    "timer": None,
    "away": None,
    "schedule": None,
    "ownerShip": "1",
    "scheduleCount": 0
}, 200)

DETAILS_AIR = ({
    "code": 0,
    "msg": None,
    "deviceStatus": "on",
    "connectionStatus": "online",
    "activeTime": 1,
    "deviceImg": None,
    "deviceName": "XXXXXXX",
    "filterLife": {
        "change": False,
        "useHour": None,
        "percent": 100
    },
    "airQuality": "excellent",
    "screenStatus": "on",
    "mode": "manual",
    "level": 1,
    "schedule": None,
    "timer": None,
    "scheduleCount": 0
}, 200)

DETAILS_BADCODE = ({
    "code": 1,
    "deviceImg": "",
    "activeTime": 1,
    "energy": 1,
    "power": "1",
    "voltage": "1"
}, 200)

STATUS_BODY = {
    "accountID": SAMPLE_ACTID,
    "token": SAMPLE_TOKEN,
    "uuid": "UUID",
    "timeZone": DEFAULT_TZ
}


def off_body():
    body = STATUS_BODY
    body['status'] = 'off'
    return (body, 200)


def on_body(cls):
    body = STATUS_BODY
    body['status'] = 'on'
    return (body, 200)
