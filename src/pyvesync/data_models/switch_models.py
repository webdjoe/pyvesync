"""Data models for VeSync switches."""
from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
import orjson
from mashumaro.config import BaseConfig
from pyvesync.data_models.base_models import (
    ResponseCodeModel,
    ResponseBaseModel,
    RequestBaseModel
    )

if TYPE_CHECKING:
    from pyvesync.helper_utils.colors import RGB


@dataclass
class ResponseDimmerDetails(ResponseCodeModel):
    """Dimmer Details Response Dict."""
    result: InternalDimmerDetailsResult


@dataclass
class ResponseSwitchDetails(ResponseCodeModel):
    """Dimmer Status Response Dict."""
    result: InternalSwitchResult


@dataclass
class InternalSwitchResult(ResponseBaseModel):
    """Dimmer Status Response Dict."""
    deviceStatus: str
    connectionStatus: str
    activeTime: int


@dataclass
class InternalDimmerDetailsResult(ResponseBaseModel):
    """Dimmer Details Result Dict."""
    devicename: str | None
    brightness: int | None
    indicatorlightStatus: str | None
    startMode: str | None
    rgbStatus: str | None
    rgbValue: RGB | None = None
    deviceStatus: str = "off"
    connectionStatus: str = "offline"
    activeTime: int = 0


@dataclass
class RequestSwitchBase(RequestBaseModel):
    """Base Dimmer Request Dict."""
    method: str
    acceptLanguage: str
    accountID: str
    appVersion: str
    cid: str
    configModule: str
    phoneBrand: str
    phoneOS: str
    timeZone: str
    token: str
    traceId: str
    userCountryCode: str
    uuid: str
    debugMode: bool
    deviceId: str
    configModel: str


@dataclass
class RequestDimmerBrightness(RequestSwitchBase):
    """Dimmer Status Request Dict."""
    brightness: str


@dataclass
class RequestSwitchStatus(RequestSwitchBase):
    """Dimmer Status Request Dict."""
    status: str
    rgbValue: dict | None = None

    class Config(BaseConfig):
        """Dimmer Indicator Control Config Dict."""
        omit_none = True
        orjson_options = orjson.OPT_NON_STR_KEYS


@dataclass
class RequestSwitchDetails(RequestSwitchBase):
    """Dimmer Details Request Dict."""


@dataclass
class RequestDimmerIndicatorCtl(RequestSwitchBase):
    """Dimmer Indicator Control Request Dict."""
    status: str
    rgbValue: dict | None = None

    class Config(BaseConfig):
        """Dimmer Indicator Control Config Dict."""
        omit_none = True
        orjson_options = orjson.OPT_NON_STR_KEYS
