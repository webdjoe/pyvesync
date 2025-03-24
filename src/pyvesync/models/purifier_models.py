"""Data models for VeSync Purifiers.

These models inherit from `ResponseBaseModel` and `RequestBaseModel` from the
`base_models` module.

The `InnerPurifierBaseResult` class is used as a base class for the inner purifier
result models for all models and the mashumaro discriminator determines the correct
subclass when deserializing.
"""
from __future__ import annotations
from dataclasses import dataclass
import orjson
from mashumaro.types import Discriminator
from mashumaro.config import BaseConfig
from mashumaro.mixins.orjson import DataClassORJSONMixin
from pyvesync.const import IntFlag, StrFlag
from pyvesync.models.base_models import (
    ResponseBaseModel,
    RequestBaseModel,
    ResponseCodeModel,
    )


@dataclass
class ResponsePurifierBase(ResponseCodeModel):
    """Purifier Base Response Dict."""
    result: OuterBypassResult

    class Config(BaseConfig):
        """Config for mashumaro serialization."""
        orjson_options = orjson.OPT_NON_STR_KEYS
        forbid_extra_keys = False


@dataclass
class OuterBypassResult:
    """Purifier Result Dict."""
    traceId: str
    code: int
    result: InnerPurifierBaseResult | None = None


# Inner Purifier Result Models for Core and Everest/Vital Purifiers
# Correct subclass is determined by mashumaro's discriminator

@dataclass
class InnerPurifierBaseResult(DataClassORJSONMixin):
    """Base class for inner purifier results model."""

    class Config(BaseConfig):
        """Configure the results model to use subclass discriminator."""
        discriminator = Discriminator(include_subtypes=True)


@dataclass
class PurifierV2DetailsResult(InnerPurifierBaseResult):
    """Vital 100S/200S and Everest Purifier Result Model."""
    powerSwitch: int
    filterLifePercent: int
    workMode: str
    manualSpeedLevel: int
    fanSpeedLevel: int
    AQLevel: int
    PM25: int
    screenState: int
    childLockSwitch: int
    screenSwitch: int
    lightDetectionSwitch: int
    environmentLightState: int
    scheduleCount: int
    timerRemain: int
    efficientModeTimeRemain: int
    errorCode: int
    autoPreference: VitalAutoPreferences | None = None
    fanRotateAngle: int | None = IntFlag.NOT_SUPPORTED
    filterOpenState: int | None = IntFlag.NOT_SUPPORTED
    PM1: int | None = IntFlag.NOT_SUPPORTED
    PM10: int | None = IntFlag.NOT_SUPPORTED
    AQPercent: int | None = IntFlag.NOT_SUPPORTED


@dataclass
class VitalAutoPreferences:
    """Vital 100S/200S Auto Preferences."""
    autoPreferenceType: str
    roomSize: int


@dataclass
class PurifierCoreDetailsResult(InnerPurifierBaseResult):
    """Purifier inner Result Dict."""
    enabled: bool
    filter_life: int
    mode: str
    level: int
    device_error_code: int
    air_quality: int | None = None
    display: bool | None = None
    child_lock: bool | None = None
    configuration: PurifierCoreDetailsConfig | None = None
    extension: dict | None = None
    air_quality_value: int | None = None
    night_light: str | None = StrFlag.NOT_SUPPORTED
    fan_rotate: str | None = StrFlag.NOT_SUPPORTED


# Purifier Timer Models


@dataclass
class PurifierModifyTimerResult(InnerPurifierBaseResult):
    """Purifier inner Add Timer Result Dict."""
    id: int


@dataclass
class PurifierGetTimerResult(InnerPurifierBaseResult):
    """Purifier inner Timer Result Dict."""
    timers: list[ResponsePurifierTimerItems]


@dataclass
class ResponsePurifierTimerItems(ResponseBaseModel):
    """Purifier Timer Items Response Dict."""
    id: int
    remain: int
    total: int
    action: str


@dataclass
class RequestPurifierTimer(RequestBaseModel):
    """Purifier Status Request Dict."""
    acceptLanguage: str
    accountID: str
    appVersion: str
    cid: str
    configModule: str
    debugMode: bool
    deviceRegion: str
    method: str
    phoneBrand: str
    phoneOS: str
    traceId: str
    timeZone: str
    token: str
    userCountryCode: str
    payload: RequestPurifierPayload


@dataclass
class PurifierV2TimerPayloadData(RequestBaseModel):
    """Purifier Timer Payload Data Request Dict."""
    enabled: bool
    startAct: list[PurifierV2TimerActionItems]
    tmgEvt: PurifierV2EventTiming
    type: int = 0
    subDeviceNo: int = 0
    repeat: int = 0


@dataclass
class PurifierV2TimerActionItems(RequestBaseModel):
    """Purifier Timer Action Items Request Dict."""
    type: str
    act: int
    num: int = 0


@dataclass
class PurifierV2EventTiming(RequestBaseModel):
    """Purifier Event Timing Request Dict."""
    clkSec: int

# Purifier Request Models


@dataclass
class RequestPurifierStatus(RequestBaseModel):
    """Purifier Status Request Dict."""
    acceptLanguage: str
    accountID: str
    appVersion: str
    cid: str
    configModule: str
    debugMode: bool
    method: str
    phoneBrand: str
    phoneOS: str
    traceId: str
    timeZone: str
    token: str
    userCountryCode: str
    deviceId: str
    configModel: str
    payload: RequestPurifierPayload


@dataclass
class RequestPurifierPayload(RequestBaseModel):
    """Purifier Payload Request Dict."""
    data: dict
    method: str
    source: str = "APP"


# Internal Purifier Details Models

@dataclass
class PurifierCoreDetailsConfig(ResponseBaseModel):
    """Config dict in Core purifier details response."""
    display: bool
    display_forever: bool
    auto_preference: None | PurifierCoreAutoConfig


@dataclass
class PurifierCoreAutoConfig(ResponseBaseModel):
    """Auto configuration Core dict in purifier details response."""
    type: str
    room_size: int


@dataclass
class PurifierDetailsExtension(ResponseBaseModel):
    """Extension dict in purifier details response for Core 200/300/400."""
    schedule_count: int
    timer_remain: int


# LV - PUR131S Purifier Models

@dataclass
class ResponsePurifier131Base(ResponseCodeModel):
    """Purifier 131 Base Response Dict."""
    result: Purifier131Result | None = None

    class Config(BaseConfig):
        """Config for mashumaro serialization."""
        orjson_options = orjson.OPT_NON_STR_KEYS
        forbid_extra_keys = False


@dataclass
class RequestPurifier131(RequestBaseModel):
    """Purifier 131 Request Dict."""
    acceptLanguage: str
    accountID: str
    appVersion: str
    debugMode: bool
    method: str
    phoneBrand: str
    phoneOS: str
    timeZone: str
    token: str
    traceId: str
    userCountryCode: str
    uuid: str
    status: str | None = None

    class Config(BaseConfig):
        """Configure omit None value keys."""
        omit_none = True
        orjson_options = orjson.OPT_NON_STR_KEYS
        forbid_extra_keys = True


@dataclass
class Purifier131Result(ResponseBaseModel):
    """Purifier 131 Details Response Dict."""
    screenStatus: str
    filterLife: Purifier131Filter
    activeTime: int
    levelNew: int
    level: int | None
    mode: str
    airQuality: str
    deviceName: str
    childLock: str
    deviceStatus: str
    connectionStatus: str


@dataclass
class Purifier131Filter(ResponseBaseModel):
    """Filter details model for LV PUR131."""
    change: bool
    useHour: int
    percent: int
