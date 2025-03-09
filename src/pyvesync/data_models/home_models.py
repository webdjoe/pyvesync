"""Home and Rooms request and response models.

Dataclasses should follow the naming convention of Request/Response + <API Name> + Model.
Internal models should be named starting with IntResp/IntReq<API Name>Model.

Attributes:
    ResponseLoginResultModel: Model for the 'result' field in login response.
    ResponseLoginModel: Model for the login response.
    RequestLoginModel: Model for the login request.

Notes:
    All models should inherit `ResponseBaseModel` or `RequestBaseModel`. Use
    `pyvesync.data_models.base_models.DefaultValues` to set default values.

"""
from __future__ import annotations
from dataclasses import dataclass, field

from pyvesync.data_models.base_models import (
    ResponseCodeModel,
    ResponseBaseModel,
    RequestBaseModel,
    DefaultValues,
    )


@dataclass
class RequestHomeModel(RequestBaseModel):
    """Request model for home data.

    Inherits from `RequestVeSyncInstanceMixin` to populate fields from the
    VeSync instance. The `VeSync` instance is passed as a
    keyword argument `RequestHomeModel(manager=instance)`.
    """
    # Arguments set by Manager Instance by passing kw_argument manager
    # these fields should be set to init=False
    accountID: str = field(init=False)
    token: str = field(init=False)
    userCountryCode: str = field(init=False)
    # Non-default constants
    method: str = 'getHomeList'
    # default values
    acceptLanguage: str = DefaultValues.acceptLanguage
    appVersion: str = DefaultValues.appVersion
    timeZone: str = DefaultValues.timeZone
    phoneBrand: str = DefaultValues.phoneBrand
    phoneOS: str = DefaultValues.phoneOS
    traceId: str = field(default_factory=DefaultValues.traceId)
    debugMode: bool = DefaultValues.debugMode


@dataclass
class ResponseHomeModel(ResponseBaseModel):
    """Model for the home data response.

    Inherits from `ResponseBaseModel`. The `ResponseBaseModel` class provides the
    `code` and `msg` fields. The `ResponseHomeModel` class provides the `result`
    field containing the home data.

    Attributes:
        result: dict: The home data.
    """
    result: IntResponseHomeResultModel


@dataclass
class RequestHomeInfoModel(RequestBaseModel):
    """Request model for home room information.

    Inherits from `RequestVeSyncInstanceMixin` to populate fields from the
    VeSync instance. The `VeSync` instance is passed as a
    keyword argument `RequestHomeModel(manager=instance)`.
    """
    # argument to pass in as positional or keyword argument homeId
    homeId: str
    # Arguments set by Manager Instance by passing kw_argument manager
    # these fields should be set to init=False
    accountID: str = field(init=False)
    token: str = field(init=False)
    userCountryCode: str = field(init=False)
    # Non-default constants
    method: str = 'getHomeDetail'
    # default values
    acceptLanguage: str = DefaultValues.acceptLanguage
    appVersion: str = DefaultValues.appVersion
    timeZone: str = DefaultValues.timeZone
    phoneBrand: str = DefaultValues.phoneBrand
    phoneOS: str = DefaultValues.phoneOS
    traceId: str = field(default_factory=DefaultValues.traceId)
    debugMode: bool = DefaultValues.debugMode


@dataclass
class ResponseHomeInfoModel(ResponseCodeModel):
    """Model for the home room information response.

    Inherits from `ResponseCodeModel`. The `ResponseCodeModel` class provides the
    `traceId`, `code`, and `msg` fields. The `ResponseHomeInfoModel` class provides
    the `result` field containing the home room data.

    Attributes:
        result: dict: The home room data.
    """
    result: IntResponseHomeInfoResultModel


@dataclass
class IntResponseHomeInfoResultModel:
    """Internal model for the 'result' field in home room response."""
    roomInfoList: list[IntResponseHomeListModel]


@dataclass
class IntResponseRoomListModel:
    """Internal model for the 'roomList' field in home response."""
    roomID: str
    roomName: str
    deviceList: list[IntResponseRoomDeviceListModel]
    plantComformHumidityRangeLower: int | None = None
    plantComformHumidityRangeHigher: int | None = None
    # group_list = []  # TODO: Create group model


@dataclass
class IntResponseRoomDeviceListModel:
    """Internal model for the device list in room response."""
    logicalDeviceType: int
    virDeviceType: int
    cid: str
    uuid: str
    subDeviceNo: int
    deviceName: str
    configModule: str
    deviceRegion: str
    deviceType: str
    type: str
    connectionType: str
    currentFirmwareVersion: str
    deviceStatus: str
    connectionStatus: str
    mode: str | None = None
    subDeviceType: str | None = None
    macid: str | None = None


@dataclass
class IntResponseHomeResultModel:
    """Internal model for the 'result' field in home response."""
    homeList: list[IntResponseHomeListModel]


@dataclass
class IntResponseHomeListModel:
    """Internal model for the 'homeList' field in home response result."""
    homeID: str
    homeName: str
