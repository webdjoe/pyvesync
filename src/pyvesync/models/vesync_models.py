"""Models for general VeSync API requests and responses.

Dataclasses should follow the naming convention of Request/Response + <API Name> + Model.
Internal models should be named starting with IntResp/IntReq<API Name>Model.

Note:
    All models should inherit `ResponseBaseModel` or `RequestBaseModel`. Use
    `pyvesync.models.base_models.DefaultValues` to set default values. There
    should be no repeating keys set in the child models.

"""
from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
from typing import Any

from pyvesync.models.base_models import (
    ResponseCodeModel,
    ResponseBaseModel,
    RequestBaseModel,
    DefaultValues,
    )


@dataclass
class RequestLoginModel(RequestBaseModel):
    """Request model for login."""
    # Arguments to set
    email: str
    method: str
    password: str
    # default values
    acceptLanguage: str = DefaultValues.acceptLanguage
    appVersion: str = DefaultValues.appVersion
    timeZone: str = DefaultValues.timeZone
    phoneBrand: str = DefaultValues.phoneBrand
    phoneOS: str = DefaultValues.phoneOS
    traceId: str = field(default_factory=DefaultValues.traceId)
    # Non-default constants
    userType: str = '1'
    devToken: str = ''

    def __post_init__(self) -> None:
        """Set the method field."""
        self.password = self.hash_password(self.password)

    @staticmethod
    def hash_password(string: str) -> str:
        """Encode password."""
        return hashlib.md5(string.encode('utf-8')).hexdigest()  # noqa: S324


@dataclass
class IntRespLoginResultModel(ResponseBaseModel):
    """Model for the 'result' field in login response containing token and account ID.

    This class is inherited by the `ResponseLoginModel` class.
    """
    accountID: str
    acceptLanguage: str
    countryCode: str
    token: str


@dataclass
class ResponseLoginModel(ResponseCodeModel):
    """Model for the login response.

    Inherits from `BaseResultModel`. The `BaseResultModel` class provides the
    defaults "code" and "msg" fields for the response.

    Attributes:
        result: ResponseLoginResultModel
            The inner model for the 'result' field in the login response.

    Examples:
        ```python
        a = {
            "code": 0,
            "msg": "success",
            "stacktrace": null,
            "module": null,
            "traceId": "123456",
            "result": {
                "accountID": "123456",
                "acceptLanguage": "en",
                "countryCode": "US",
                }
        }
        b = ResponseLoginModel.from_dict(a)
        account_id = b.result.accountId
        token = b.result.token
        ```
    """
    result: IntRespLoginResultModel
    stacktrace: str | None
    module: str | None


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
class RequestPID(RequestBaseModel):
    """Model for the PID request."""
    method: str
    appVersion: str
    phoneBrand: str
    phoneOS: str
    traceId: str
    token: str
    accountID: str
    mobileID: str
    configModule: str
    region: str
