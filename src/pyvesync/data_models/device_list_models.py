"""Data models for device list request and response.

Use the naming convention `Response<API CALL>Model` to represent the outermost
response model. Inner keys and values should be represented by internal models
named `Internal<API CALL>`.

Attributes:
    RequestDeviceListModel: Model for the device list request.
    ResponseDeviceListModel: Model for the device list response.
"""
from __future__ import annotations
from typing import Any
from dataclasses import dataclass
from pyvesync.data_models.base_models import (
    RequestBaseModel,
    ResponseCodeModel,
    DefaultValues,
    ResponseBaseModel
  )


@dataclass
class RequestDeviceListModel(RequestBaseModel):
    """Model for the device list request."""
    token: str
    accountID: str
    timeZone: str = DefaultValues.timeZone
    method: str = 'devices'
    pageNo: int = 1
    pageSize: int = 100
    appVersion: str = DefaultValues.appVersion
    phoneBrand: str = DefaultValues.phoneBrand
    phoneOS: str = DefaultValues.phoneOS
    acceptLanguage: str = DefaultValues.acceptLanguage
    traceId: str = str(DefaultValues.traceId())


@dataclass
class ResponseDeviceListModel(ResponseCodeModel):
    """Device list response model.

    Inherits from `BaseResultModel`. The `BaseResultModel` class provides the
    defaults "code" and "msg" fields for the response.

    Attributes:
        result: InternalDeviceListResult
            The inner model for the 'result' field in the device list response.
        module: str | None
        stacktrace: str | None

    Notes:
        See the `DeviceListResultModel` and `DeviceListDeviceModel` classes for
        the inner model of the 'result' field.
    """
    module: str | None
    stacktrace: str | None
    result: InternalDeviceListResult


@dataclass
class InternalDeviceListResult(ResponseBaseModel):
    """Internal model for the 'result' field in device list response.

    Notes:
      Used by the `ResponseDeviceListModel` class to populate result field.
    """
    total: int
    pageSize: int
    pageNo: int
    list: list[ResponseDeviceDetailsModel]


@dataclass
class InternalDeviceListExtension(ResponseBaseModel):
    """Internal Optional 'extension' field in device list response.

    Used by the `InnerRespDeviceListDevModel` class to populate
    the extension field in the device list response.
    """
    airQuality: None | int
    airQualityLevel: None | int
    mode: None | str
    fanSpeedLevel: None | str


@dataclass
class ResponseDeviceDetailsModel(ResponseBaseModel):
    """Internal response model for each device in device list response.

    Populates the 'list' field in the `InternalDeviceListResult`.

    Certain Devices have device status information in the `deviceProp` or `extension`
    fields. This model flattens those fields into the `deviceStatus` and
    `connectionStatus` fields before deserialization.
    """
    deviceRegion: str
    isOwner: bool
    deviceName: str
    deviceImg: str
    cid: str
    connectionType: str
    deviceType: str
    type: str
    uuid: str | None
    configModule: str
    macID: str
    mode: str
    speed: str | None
    currentFirmVersion: str
    subDeviceType: str | None
    subDeviceList: None | str
    extension: None | InternalDeviceListExtension
    subDeviceNo: int = 0
    deviceStatus: str = "off"
    connectionStatus: str = "offline"
    productType: str | None = None
    # deviceProp: InitVar[None | InternalDevicePropModel] = None

    # def __post_init__(self, deviceProp: None | IntRespDevicePropModel) -> None:
    #     """Set productType based on deviceType."""
    #     if deviceProp is not None:
    #         if deviceProp.powerSwitch == 1:
    #             self.deviceStatus = "on"
    #         elif deviceProp.powerSwitch == 0:
    #             self.deviceStatus = "off"
    #         if isinstance(deviceProp.connectionStatus, str) and \
    #                 self.connectionStatus != deviceProp.connectionStatus:
    #             self.connectionStatus = deviceProp.connectionStatus

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Perform device_list pre-deserialization processes.

        This performs the following:
            - Flattens the deviceProp field into deviceStatus and connectionStatus fields
            - Sets subDeviceNo to 0 if not present
            - Sets cid to uuid or macID if null
        """
        super().__pre_deserialize__(d)
        d = _flatten_device_prop(d)
        if d.get('subDeviceNo') is None:
            d['subDeviceNo'] = 0
        if d.get('cid') is None:
            d['cid'] = d.get('uuid') if d.get('uuid') is not None else d.get("macID")
        return d


def _flatten_device_prop(d: dict[str, Any]) -> dict[str, Any]:
    """Flatten deviceProp field in device list response."""
    if isinstance(d.get('deviceProp'), dict):
        device_prop = d['deviceProp']
        if device_prop.get('powerSwitch') is not None:
            d['deviceStatus'] = "on" if device_prop['powerSwitch'] == 1 else "off"
        if device_prop.get('connectionStatus') is not None:
            d['connectionStatus'] = device_prop['connectionStatus']
        if device_prop.get('wifiMac') is not None:
            d['macID'] = device_prop['wifiMac']
    del d['deviceProp']
    return d

# test_response = {
#   "traceId": "1739761422",
#   "code": 0,
#   "msg": "request success",
#   "module": None,
#   "stacktrace": None,
#   "result": {
#     "total": 10,
#     "pageSize": 100,
#     "pageNo": 1,
#     "list": [
#       {
#         "deviceRegion": "US",
#         "isOwner": True,
#         "authKey": None,
#         "deviceName": "Purifier",
#         "deviceImg": "https://image.vesync.com/defaultImages/deviceDefaultImages/wifibtonboardingnotify_airpurifier_core400s_us_240.png",
#         "cid": "vsaq9d94b2e44768a7a856b8e8b2132d",
#         "deviceStatus": "on",
#         "connectionStatus": "online",
#         "connectionType": "WiFi+BTOnboarding+BTNotify",
#         "deviceType": "Core400S",
#         "type": "wifi-air",
#         "uuid": "603ef340-8934-4e2b-98f1-85c6455d2e48",
#         "configModule": "WiFiBTOnboardingNotify_AirPurifier_Core400S_US",
#         "macID": "c4:5b:be:0a:d5:36",
#         "mode": None,
#         "speed": None,
#         "currentFirmVersion": None,
#         "subDeviceNo": None,
#         "subDeviceType": None,
#         "deviceFirstSetupTime": "Dec 17, 2021 6:07:08 PM",
#         "subDeviceList": None,
#         "extension": {
#           "airQuality": -1,
#           "airQualityLevel": 1,
#           "mode": "manual",
#           "fanSpeedLevel": "3"
#         },
#         "deviceProp": None
#       },
#       {
#         "deviceRegion": "US",
#         "isOwner": True,
#         "authKey": None,
#         "deviceName": "Etekcity Cool-to-Warm White Light Bulb",
#         "deviceImg": "https://image.vesync.com/defaultImages/deviceDefaultImages/wifi_bulb_whitelightbulb_us_240.png",
#         "cid": "0LgR5MkK-g8p2ymnFoicuXyPTEu_0LyM",
#         "deviceStatus": "off",
#         "connectionStatus": "offline",
#         "connectionType": "wifi",
#         "deviceType": "ESL100CW",
#         "type": "Wifi-light",
#         "uuid": "9998189e-a1bf-47fc-961d-44c1e6163715",
#         "configModule": "WiFi_Bulb_WhiteLightBulb_US",
#         "macID": None,
#         "mode": None,
#         "speed": None,
#         "currentFirmVersion": None,
#         "subDeviceNo": None,
#         "subDeviceType": None,
#         "deviceFirstSetupTime": "Aug 30, 2019 1:09:19 AM",
#         "subDeviceList": None,
#         "extension": None,
#         "deviceProp": None
#       },
#       {
#         "deviceRegion": "US",
#         "isOwner": True,
#         "authKey": None,
#         "deviceName": "Etekcity Dimmer Switch",
#         "deviceImg": "https://image.vesync.com/defaultImages/deviceDefaultImages/wifiwalldimmer_240.png",
#         "cid": "0Li2r7eeNQVnS60NlqRQrFVtRLGUQoqV",
#         "deviceStatus": "on",
#         "connectionStatus": "offline",
#         "connectionType": "wifi",
#         "deviceType": "ESWD16",
#         "type": "Switches",
#         "uuid": "9b052462-cc2f-4eb3-b675-bc4aa405e0b8",
#         "configModule": "WifiWallDimmer",
#         "macID": None,
#         "mode": None,
#         "speed": None,
#         "currentFirmVersion": None,
#         "subDeviceNo": None,
#         "subDeviceType": None,
#         "deviceFirstSetupTime": "Aug 20, 2019 3:43:07 PM",
#         "subDeviceList": None,
#         "extension": None,
#         "deviceProp": None
#       },
#       {
#         "deviceRegion": "US",
#         "isOwner": True,
#         "authKey": None,
#         "deviceName": "Etekcity Light Switch",
#         "deviceImg": "https://image.vesync.com/defaultImages/ESWL01_Series/icon_light_switch_80.png",
#         "cid": "0LQbzC3sLn65ZKUOMKENWJO7RqrgOCB1",
#         "deviceStatus": "off",
#         "connectionStatus": "offline",
#         "connectionType": "wifi",
#         "deviceType": "ESWL01",
#         "type": "Switches",
#         "uuid": "ca93665f-0eee-437b-8642-1f7dba34efd8",
#         "configModule": "InwallswitchUS",
#         "macID": None,
#         "mode": None,
#         "speed": None,
#         "currentFirmVersion": None,
#         "subDeviceNo": None,
#         "subDeviceType": None,
#         "deviceFirstSetupTime": "Jul 13, 2019 6:17:16 PM",
#         "subDeviceList": None,
#         "extension": None,
#         "deviceProp": None
#       },
#       {
#         "deviceRegion": "US",
#         "isOwner": True,
#         "authKey": None,
#         "deviceName": "Socket A",
#         "deviceImg": "https://image.vesync.com/defaultImages/ESO15_TB_Series/socket_a.png",
#         "cid": "0LbuVl3GWymimvcDPdamHAo_t7ROqRX1",
#         "deviceStatus": "off",
#         "connectionStatus": "offline",
#         "connectionType": "wifi",
#         "deviceType": "ESO15-TB",
#         "type": "wifi-switch",
#         "uuid": "75889f2a-707a-45c8-b142-6ba2975c7361",
#         "configModule": "OutdoorSocket15A",
#         "macID": None,
#         "mode": None,
#         "speed": None,
#         "currentFirmVersion": None,
#         "subDeviceNo": 1,
#         "subDeviceType": None,
#         "deviceFirstSetupTime": "Jul 8, 2019 12:58:50 AM",
#         "subDeviceList": None,
#         "extension": None,
#         "deviceProp": None
#       },
#       {
#         "deviceRegion": "US",
#         "isOwner": True,
#         "authKey": None,
#         "deviceName": "Socket B",
#         "deviceImg": "https://image.vesync.com/defaultImages/ESO15_TB_Series/socket_b.png",
#         "cid": "0LbuVl3GWymimvcDPdamHAo_t7ROqRX1",
#         "deviceStatus": "off",
#         "connectionStatus": "offline",
#         "connectionType": "wifi",
#         "deviceType": "ESO15-TB",
#         "type": "wifi-switch",
#         "uuid": "75889f2a-707a-45c8-b142-6ba2975c7361",
#         "configModule": "OutdoorSocket15A",
#         "macID": None,
#         "mode": None,
#         "speed": None,
#         "currentFirmVersion": None,
#         "subDeviceNo": 2,
#         "subDeviceType": None,
#         "deviceFirstSetupTime": "Jul 8, 2019 12:58:50 AM",
#         "subDeviceList": None,
#         "extension": None,
#         "deviceProp": None
#       },
#       {
#         "deviceRegion": "US",
#         "isOwner": True,
#         "authKey": None,
#         "deviceName": "Etekcity Soft White Bulb",
#         "deviceImg": "https://image.vesync.com/defaultImages/deviceDefaultImages/wifismartbulb_240.png",
#         "cid": "0LbQt4VYZaJgc86rd_2H8BtgXUhUql-1",
#         "deviceStatus": "off",
#         "connectionStatus": "offline",
#         "connectionType": "wifi",
#         "deviceType": "ESL100",
#         "type": "Wifi-light",
#         "uuid": "dd2a8317-0b1e-4a90-beb4-9d53bef4c4b7",
#         "configModule": "WifiSmartBulb",
#         "macID": None,
#         "mode": None,
#         "speed": None,
#         "currentFirmVersion": None,
#         "subDeviceNo": None,
#         "subDeviceType": None,
#         "deviceFirstSetupTime": "Jun 26, 2019 12:54:17 AM",
#         "subDeviceList": None,
#         "extension": None,
#         "deviceProp": None
#       },
#       {
#         "deviceRegion": "US",
#         "isOwner": True,
#         "authKey": None,
#         "deviceName": "Etekcity WiFi Outlet US/CA",
#         "deviceImg": "https://image.vesync.com/defaultImages/deviceDefaultImages/7aoutlet_240.png",
#         "cid": "dfabc02a-f511-42e0-b631-419b6269db5f",
#         "deviceStatus": "on",
#         "connectionStatus": "offline",
#         "connectionType": "wifi",
#         "deviceType": "wifi-switch-1.3",
#         "type": "wifi-switch",
#         "uuid": "dfabc02a-f511-42e0-b631-419b6269db5f",
#         "configModule": "7AOutlet",
#         "macID": "62:01:94:63:0C:43",
#         "mode": None,
#         "speed": None,
#         "currentFirmVersion": "2.125",
#         "subDeviceNo": None,
#         "subDeviceType": None,
#         "deviceFirstSetupTime": "May 14, 2019 3:30:09 AM",
#         "subDeviceList": None,
#         "extension": None,
#         "deviceProp": None
#       },
#       {
#         "deviceRegion": "US",
#         "isOwner": True,
#         "authKey": None,
#         "deviceName": "Round",
#         "deviceImg": "https://image.vesync.com/defaultImages/ESW01_USA_Series/icon_7a_wifi_outlet_160.png",
#         "cid": "3738f48d-f141-44d7-b08e-1ecc4fdeec63",
#         "deviceStatus": "off",
#         "connectionStatus": "online",
#         "connectionType": "wifi",
#         "deviceType": "wifi-switch-1.3",
#         "type": "wifi-switch",
#         "uuid": "3738f48d-f141-44d7-b08e-1ecc4fdeec63",
#         "configModule": "7AOutlet",
#         "macID": "2C:3A:E8:3E:29:4D",
#         "mode": None,
#         "speed": None,
#         "currentFirmVersion": "2.125",
#         "subDeviceNo": None,
#         "subDeviceType": None,
#         "deviceFirstSetupTime": "May 14, 2019 3:27:51 AM",
#         "subDeviceList": None,
#         "extension": None,
#         "deviceProp": None
#       },
#       {
#         "deviceRegion": "US",
#         "isOwner": True,
#         "authKey": None,
#         "deviceName": "Etekcity 15A WiFi Outlet US/CA",
#         "deviceImg": "https://image.vesync.com/defaultImages/deviceDefaultImages/15aoutletnightlight_240.png",
#         "cid": "0LRVzQGOo9GEasixjWgZKFfHPXlSST41",
#         "deviceStatus": "off",
#         "connectionStatus": "online",
#         "connectionType": "wifi",
#         "deviceType": "ESW15-USA",
#         "type": "wifi-switch",
#         "uuid": "c607c25f-e9ef-4a40-935f-03b73f61a1ee",
#         "configModule": "15AOutletNightlight",
#         "macID": None,
#         "mode": None,
#         "speed": None,
#         "currentFirmVersion": None,
#         "subDeviceNo": None,
#         "subDeviceType": None,
#         "deviceFirstSetupTime": "Feb 27, 2019 10:24:10 AM",
#         "subDeviceList": None,
#         "extension": None,
#         "deviceProp": None
#       }
#     ]
#   }
# }

# device_response_model = ResponseDeviceListModel.from_dict(test_response)
# device_response_dict = device_response_model.to_dict()
# print(device_response_model.to_json())
# print(device_response_dict)
