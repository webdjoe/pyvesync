"""Models for general VeSync API requests and responses.

Dataclasses should follow the naming convention of Request/Response + <API Name> + Model.
Internal models should be named starting with IntResp/IntReq<API Name>Model.

Note:
    All models should inherit `ResponseBaseModel` or `RequestBaseModel`. Use
    `pyvesync.models.base_models.DefaultValues` to set default values. There
    should be no repeating keys set in the child models.

"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from pyvesync.models.base_models import (
    DefaultValues,
    RequestBaseModel,
    ResponseBaseModel,
    ResponseCodeModel,
)


@dataclass
class RequestGetTokenModel(RequestBaseModel):
    """Request model for requesting auth token (used for login)."""

    # Arguments to set
    email: str
    method: str
    password: str
    # default values
    acceptLanguage: str = DefaultValues.acceptLanguage
    accountID: str = ''
    authProtocolType: str = 'generic'
    clientInfo: str = DefaultValues.phoneBrand
    clientType: str = DefaultValues.clientType
    clientVersion: str = f'VeSync {DefaultValues.appVersion}'
    debugMode: bool = False
    osInfo: str = DefaultValues.phoneOS
    terminalId: str = DefaultValues.terminalId
    timeZone: str = DefaultValues.timeZone
    token: str = ''
    userCountryCode: str = DefaultValues.userCountryCode
    appID: str = DefaultValues.appId
    sourceAppID: str = DefaultValues.appId
    traceId: str = field(default_factory=DefaultValues.newTraceId)

    def __post_init__(self) -> None:
        """Hash the password field."""
        self.password = self.hash_password(self.password)

    @staticmethod
    def hash_password(string: str) -> str:
        """Encode password."""
        return hashlib.md5(string.encode('utf-8')).hexdigest()  # noqa: S324


@dataclass
class RespGetTokenResultModel(ResponseBaseModel):
    """Model for the 'result' field in auth response with authorizeCode and account ID.

    This class is referenced by the `ResponseAuthModel` class.
    """

    accountID: str
    authorizeCode: str


@dataclass
class RequestLoginTokenModel(RequestBaseModel):
    """Request model for login."""

    # Arguments to set
    method: str
    authorizeCode: str | None
    # default values
    acceptLanguage: str = DefaultValues.acceptLanguage
    accountID: str = ''
    clientInfo: str = DefaultValues.phoneBrand
    clientType: str = DefaultValues.clientType
    clientVersion: str = f'VeSync {DefaultValues.appVersion}'
    debugMode: bool = False
    emailSubscriptions: bool = False
    osInfo: str = DefaultValues.phoneOS
    terminalId: str = DefaultValues.terminalId
    timeZone: str = DefaultValues.timeZone
    token: str = ''
    bizToken: str | None = None
    regionChange: str | None = None
    userCountryCode: str = DefaultValues.userCountryCode
    traceId: str = field(default_factory=DefaultValues.newTraceId)

    def __post_serialize__(self, d: dict[Any, Any]) -> dict[Any, Any]:
        """Remove null keys."""
        if d['regionChange'] is None:
            d.pop('regionChange')
        if d['authorizeCode'] is None:
            d.pop('authorizeCode')
        if d['bizToken'] is None:
            d.pop('bizToken')
        return d


@dataclass
class RespLoginTokenResultModel(ResponseBaseModel):
    """Model for the 'result' field in login response containing token and account ID.

    This class is referenced by the `ResponseLoginModel` class.
    """

    accountID: str
    acceptLanguage: str
    countryCode: str
    token: str
    bizToken: str = ''
    currentRegion: str = ''


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
                "token": "abcdef1234567890"
            }
        }
        b = ResponseLoginModel.from_dict(a)
        account_id = b.result.accountId
        token = b.result.token
        ```
    """

    result: RespLoginTokenResultModel | RespGetTokenResultModel


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
            d['deviceStatus'] = 'on' if device_prop['powerSwitch'] == 1 else 'off'
        if device_prop.get('connectionStatus') is not None:
            d['connectionStatus'] = device_prop['connectionStatus']
        if device_prop.get('wifiMac') is not None:
            d['macID'] = device_prop['wifiMac']
    d.pop('deviceProp', None)
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
    cid: str
    connectionType: str
    deviceType: str
    type: str
    configModule: str
    uuid: str | None = None
    macID: str = ''
    mode: str = ''
    deviceImg: str = ''
    speed: str | None = None
    currentFirmVersion: str | None = None
    subDeviceType: str | None = None
    subDeviceList: str | None = None
    extension: InternalDeviceListExtension | None = None
    subDeviceNo: int | None = None
    deviceStatus: str = 'off'
    connectionStatus: str = 'offline'
    productType: str | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Perform device_list pre-deserialization processes.

        This performs the following:
            - Flattens the `deviceProp` field into `deviceStatus`, `connectionStatus`
                and `macID`
            - Sets `cid` to `uuid` or `macID` if null
        """
        super().__pre_deserialize__(d)
        d = _flatten_device_prop(d)
        if d.get('cid') is None:
            d['cid'] = d.get('uuid') if d.get('uuid') is not None else d.get('macID')
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


@dataclass
class RequestFirmwareModel(RequestBaseModel):
    """Model for the firmware request."""

    accountID: str
    timeZone: str
    token: str
    userCountryCode: str
    cidList: list[str]
    acceptLanguage: str = DefaultValues.acceptLanguage
    traceId: str = field(default_factory=DefaultValues.traceId)
    appVersion: str = DefaultValues.appVersion
    phoneBrand: str = DefaultValues.phoneBrand
    phoneOS: str = DefaultValues.phoneOS
    method: str = 'getFirmwareUpdateInfoList'
    debugMode: bool = False


@dataclass
class ResponseFirmwareModel(ResponseCodeModel):
    """Model for the firmware response."""

    result: FirmwareResultModel


@dataclass
class FirmwareUpdateInfoModel(ResponseBaseModel):
    """Firmware update information model."""

    currentVersion: str
    latestVersion: str
    releaseNotes: str
    pluginName: str
    isMainFw: bool


@dataclass
class FirmwareDeviceItemModel(ResponseBaseModel):
    """Model for the firmware device item in the firmware response."""

    deviceCid: str
    deviceName: str
    code: int
    msg: str | None
    firmUpdateInfos: list[FirmwareUpdateInfoModel]


@dataclass
class FirmwareResultModel(ResponseBaseModel):
    """Model for the firmware response result."""

    cidFwInfoList: list[FirmwareDeviceItemModel]


@dataclass
class RequestDeviceConfiguration(RequestBaseModel):
    """Model for the device configuration request."""

    accountID: str
    token: str
    acceptLanguage: str = DefaultValues.acceptLanguage
    appVersion: str = f'VeSync {DefaultValues.appVersion}'
    debugMode: bool = False
    method: str = 'getAppConfigurationV2'
    phoneBrand: str = DefaultValues.phoneBrand
    phoneOS: str = DefaultValues.phoneOS
    timeZone: str = DefaultValues.timeZone
    traceId: str = field(default_factory=DefaultValues.traceId)
    userCountryCode: str = DefaultValues.userCountryCode
    categories: list[dict[str, str | bool]] = field(
        default_factory=lambda: [
            {
                'category': 'SupportedModelsV3',
                'language': 'en',
                'testMode': False,
                'version': '',
            }
        ]
    )
    recall: bool = False


@dataclass
class ResponseDeviceConfiguration(ResponseCodeModel):
    """Model for the device configuration response.

    Inherits from `BaseResultModel`. The `BaseResultModel` class provides the
    defaults "code" and "msg" fields for the response.

    Attributes:
        result: dict
            The inner model for the 'result' field in the device configuration response.
    """

    result: dict[str, Any]


@dataclass
class ResultDeviceConfiguration(ResponseBaseModel):
    """Model for the device configuration result field.

    This class is referenced by the `ResponseDeviceConfiguration` class.
    """

    configList: list[DeviceConfigurationConfigListItem]


@dataclass
class DeviceConfigurationConfigListItem(ResponseBaseModel):
    """Model for each item in the configList field of the device configuration result.

    This class is referenced by the `ResultDeviceConfiguration` class.
    """

    category: str
    items: list[dict[str, Any]]


@dataclass
class DeviceConfigItem(ResponseBaseModel):
    """Model for each item in the configList field of the device configuration result.

    This class is referenced by the `DeviceConfigurationConfigListItem` class.
    """

    itemKey: str
    itemValue: list[dict[str, Any]]


@dataclass
class DeviceConfigItemValue(ResponseBaseModel):
    """Model for each item in the configList field of the device configuration result.

    This class is referenced by the `DeviceConfigItem` class.
    """

    productLineList: list
