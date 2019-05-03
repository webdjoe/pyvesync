import time
from pyvesync.helpers import (API_BASE_URL, API_RATE_LIMIT, API_TIMEOUT,
                              DEFAULT_TZ, APP_VERSION, PHONE_BRAND,
                              PHONE_OS, MOBILE_ID, USER_TYPE)

SAMPLE_ACTID = '1234567'
SAMPLE_TOKEN = 'sample-token'
TRACE_ID = '1234567890123'


"""
Standard.default_header = standard header for most calls
Login.call_body = body of login call
Login.return_body = return of login call
-------------------------------------------------------
DeviceList.call_body = body of call to get device list
DeviceList.call_header = header of call to get device list
DeviceList.details_10eu = device list entry for 10A Europe outlet
DeviceList.details_10us = devlice list entry for 10A US outlet
DeviceList.details_7a = device list entry for 7A outlet
DeviceList.details_air = device list entry for air purifier
DeviceList.details_wallsw = device list entry for wall switch
DeviceList.all_dev_list = list of all device entries
DeviceList.outlet10aeu_list = device list return for only 10A eu outlet
DeviceList.outlet10aus_list = device list return for only 10A us outlet
DeviceList.outlet7a_list = device list return for only 7A outlet
DeviceList.outlet15a_list = device list return for only 15A outlet
DeviceList.wallswitch_list = device list return for only wall switch
DeviceList.airpur_list = device list return for just air purifier
---------------------------------------------------------
Details.outlet10a_return = Return for 10A outlet device details
Details.outlet15a_return = Return for 15A outlet device details
Details.outlet7a_return = Return for 7A outlet device details
Details.wallswitch_return = Return for wall switch device details
Details.airpur_return = Return for Air Purifier device details

"""


class Standard:

    @property
    @staticmethod
    def default_header():
        header = {
            'accept-language': 'en',
            'accountId': SAMPLE_ACTID,
            'appVersion': APP_VERSION,
            'content-type': 'application/json',
            'tk': SAMPLE_TOKEN,
            'tz': DEFAULT_TZ
        }
        return header

    @property
    @staticmethod
    def default_body():
        json = {
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
        return json


class Login:
    def __init__(self):
        self.api_url = '/cloud/v1/user/login'

    @staticmethod
    def call_body(email, password):
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

    @property
    @staticmethod
    def return_body():
        json = {
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
        }
        return json


class DeviceList:

    @property
    def details_7a(self):
        return {
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

    @property
    def details_15a(self):
        return {
                "deviceType": "ESW15-USA",
                "extension": None,
                "macID": None,
                "type": "wifi-switch",
                "deviceName": "Dryer",
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

    @property
    def details_wallsw(self):
        return {
                "deviceType": "ESWL01",
                "extension": None,
                "macID": None,
                "type": "Switches",
                "deviceName": "Name Wall Switch",
                "connectionType": "wifi",
                "uuid": "UUID",
                "speed": None,
                "deviceStatus": "off",
                "mode": None,
                "configModule": "InwallswitchUS",
                "currentFirmVersion": None,
                "connectionStatus": "online",
                "cid": "WALLSWITCH-CID"
                }

    @property
    def details_10aeu(self):
        return {
                "deviceType": "ESW01-EU",
                "extension": None,
                "macID": None,
                "type": "wifi-switch",
                "deviceName": "Name 10A EU Outlet",
                "connectionType": "wifi",
                "uuid": "UUID",
                "speed": None,
                "deviceStatus": "off",
                "mode": None,
                "configModule": "10AOutletEU",
                "currentFirmVersion": None,
                "connectionStatus": "offline",
                "cid": "10AEU-CID"
                }

    @property
    def details_10aus(self):
        return {
                "deviceType": "ESW03-USA",
                "extension": None,
                "macID": None,
                "type": "wifi-switch",
                "deviceName": "Name 10A US Outlet",
                "connectionType": "wifi",
                "uuid": "UUID",
                "speed": None,
                "deviceStatus": "off",
                "mode": None,
                "configModule": "10AOutletUSA",
                "currentFirmVersion": None,
                "connectionStatus": "offline",
                "cid": "10AUS-CID"
                }

    @property
    def details_air(self):
        return {
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

    @property
    def full_list(self):
        return [self.details_7a, self.details_10aeu,
                self.details_10aus, self.details_15a,
                self.details_air, self.details_wallsw]

    @property
    def call_header(self):
        return Standard.default_header

    @property
    def call_body(self):
        body = dict(Standard.default_body)
        body['method'] = 'devices'
        return body

    @property
    def all_dev_list(self):
        return ({'code': 0, 'result': {'list': self.full_list}}, 200)

    @property
    def outlet7a_list(self):
        return ({'code': 0, 'result': {'list': [self.details_7a]}}, 200)

    @property
    def outlet15a_list(self):
        return ({'code': 0, 'result': {'list': self.details_15a}}, 200)

    @property
    def outlet10aus_list(self):
        return ({'code': 0, 'result': {'list': self.details_10aus}}, 200)

    @property
    def outlet10aeu_list(self):
        return ({'code': 0, 'result': {'list': self.details_10aeu}}, 200)

    @property
    def wallswitch_list(self):
        return ({'code': 0, 'result': {'list': self.details_wallsw}}, 200)

    @property
    def airpur_list(self):
        return ({'code': 0, 'result': {'list': self.details_air}}, 200)


class Details:

    @property
    @staticmethod
    def outlet15A_details():
        return {
            "code": 0,
            "msg": None,
            "deviceStatus": "on",
            "connectionStatus": "online",
            "activeTime": 28,
            "energy": 0.0,
            "nightLightStatus": "on",
            "nightLightBrightness": 50,
            "nightLightAutomode": "manual",
            "power": "0.0",
            "voltage": "118.64"
        }

    @property
    @staticmethod
    def outlet7a_details():
        return {
            "deviceStatus": "off",
            "deviceImg": "",
            "activeTime": 0,
            "energy": 0,
            "power": "0:0",
            "voltage": "0:0"
        }

    @property
    @staticmethod
    def outlet10a_return():
        return {
            "code": 0,
            "msg": None,
            "deviceStatus": "on",
            "connectionStatus": "online",
            "activeTime": 0,
            "energy": 0.0,
            "nightLightStatus": None,
            "nightLightBrightness": None,
            "nightLightAutomode": None,
            "power": "0",
            "voltage": "0"
        }

    @property
    @staticmethod
    def wallswitch_return():
        return {
            "code": 0,
            "msg": None,
            "deviceStatus": "on",
            "connectionStatus": "online",
            "activeTime": 28,
            "power": "None",
            "voltage": "None"
        }


class status:

    status_body = {
                   "accountID": SAMPLE_ACTID,
                   "token": SAMPLE_TOKEN,
                   "uuid": "UUID",
                   "timeZone": DEFAULT_TZ
                   }

    @property
    @classmethod
    def off_body(cls):
        body = cls.status_body
        body['status'] = 'off'
        return body

    @property
    @classmethod
    def on_body(cls):
        body = cls.status_body
        body['status'] = 'on'
        return body

    @property
    @staticmethod
    def call_body():
        body = dict(Standard.default_body)
        body['method'] = 'deviceDetail'
        return body
