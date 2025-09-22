"""Request Models for Bypass V2 Endpoints.

API calls to bypassV2 endpoints have similar request structures. These models are used
to serialize and deserialize the JSON requests for the bypassV2 endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import orjson
from mashumaro import pass_through
from mashumaro.config import BaseConfig
from mashumaro.mixins.orjson import DataClassORJSONMixin

from pyvesync.models.base_models import (
    BaseModelConfig,
    RequestBaseModel,
    ResponseBaseModel,
    ResponseCodeModel,
)


@dataclass
class RequestBypassV2(RequestBaseModel):
    """Bypass V2 Status Request Dict.

    This is the bypassV2 request model for API calls
    that use the `configModel` and `deviceId` fields.
    """

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
    payload: BypassV2RequestPayload


@dataclass
class BypassV2RequestPayload(RequestBaseModel):
    """Generic Bypass V2 Payload Request model."""

    data: dict
    method: str
    source: str = 'APP'


@dataclass
class RequestBypassV1(RequestBaseModel):
    """Bypass V1 Status Request Dict.

    This is the bypassV1 request model for API calls
    that use the `configModel` and `deviceId` fields.
    """

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
    uuid: str
    deviceId: str
    configModel: str

    class Config(BaseConfig):  # type: ignore[override]
        """Configure omit None value keys."""

        omit_none = True
        orjson_options = orjson.OPT_NON_STR_KEYS
        forbid_extra_keys = True


@dataclass
class ResponseBypassV1(ResponseCodeModel):
    """Bypass V1 Response Dict."""

    result: BypassV1Result | None = field(
        default=None,
        metadata={
            'serialize': pass_through,
            'deserialize': pass_through,
        },
    )


@dataclass
class BypassV1Result(DataClassORJSONMixin):
    """Bypass V1 Response Dict."""


@dataclass
class ResponseBypassV2(ResponseCodeModel):
    """Bypass V2 Response Dict.

    This is the bypassV2 response model for API calls
    that use the `configModel` and `deviceId` fields.
    """

    result: BypassV2OuterResult | None = None


@dataclass
class BypassV2InnerResult(DataClassORJSONMixin):
    """Inner Bypass V2 Result Data Model."""

    class Config(BaseModelConfig):
        """Configure the Outer Result model."""

        allow_deserialization_not_by_alias = True


@dataclass
class BypassV2OuterResult(DataClassORJSONMixin):
    """Bypass V2 Outer Result Data Model."""

    code: int
    result: BypassV2InnerResult | None = field(
        default=None,
        metadata={
            'serialize': pass_through,
            'deserialize': pass_through,
        },
    )

    class Config(BaseModelConfig):
        """Configure the Outer Result model."""

        allow_deserialization_not_by_alias = True


@dataclass
class BypassV2ResultError(DataClassORJSONMixin):
    """Bypass V2 Result Error Data Model."""

    msg: str


@dataclass
class ResultV2GetTimer(BypassV2InnerResult):
    """Inner result for Bypass V2 GetTimer method."""

    timers: list[TimerItemV2] | None = None


@dataclass
class ResultV2SetTimer(BypassV2InnerResult):
    """Result for Bypass V2 SetTimer method."""

    id: int


# Bypass V1 Timer Models


@dataclass
class TimeItemV1(ResponseBaseModel):
    """Data model for Bypass V1 Timers."""

    timerID: str
    counterTime: str
    action: str
    status: str
    resetTime: str
    uuid: str


@dataclass
class TimerItemV1(ResponseBaseModel):
    """Data model for Bypass V1 Timers."""

    timerID: str
    counterTimer: str
    action: str
    status: str
    resetTime: str


@dataclass
class TimerItemV2(ResponseBaseModel):
    """Data model for Bypass V2 Timers."""

    id: int
    remain: int
    action: str
    total: int


@dataclass
class ResultV1SetTimer(BypassV1Result):
    """Result model for setting Bypass V1 API timer."""

    timerID: str
    conflictTimerIds: list[str] | None = None


@dataclass
class RequestV1ClearTimer(RequestBypassV1):
    """Request model for clearing Bypass V1 API outlet timer."""

    timerId: str
    status: str | None = None


@dataclass
class ResultV1GetTimerList(BypassV1Result):
    """Get timers result for v1 API."""

    timers: list[TimeItemV1] | list[TimerItemV1] | TimerItemV1 | None = None


@dataclass
class RequestV1SetTime(RequestBypassV1):
    """Request model for setting timer with counterTime."""

    counterTime: str
    action: str
    status: str | None = None
    switchNo: int | None = None


@dataclass
class RequestV1GetTimer(RequestBypassV1):
    """Request model for getting timers from v1 API."""

    switchNo: str | None = None


@dataclass
class RequestV1SetTimer(RequestBypassV1):
    """Request model for timer with counterTimer key.

    Attributes:
        counterTimer (str): The timer value in seconds.
        action (str): The action to perform (e.g., "on", "off").
        switchNo (int | None): The switch number for the timer.
    """

    counterTimer: str
    action: str
    switchNo: int | None = None


class TimerModels:
    """Class holding all common timer models.

    Attributes:
        ResultV2GetTimer (ResultV2GetTimer): Result model for Bypass V2 GetTimer method.
        ResultV2SetTimer (ResultV2SetTimer): Result model for Bypass V2 SetTimer method.
        ResultV1SetTimer (ResultV1SetTimer): Result model V1 API for setting timer.
        ResultV1GetTimer (ResultV1GetTimerList): Get timers result for v1 API.
        TimeItemV1 (TimeItemV1): Data model for Bypass V1 Timers.
        TimerItemV1 (TimerItemV1): Data model for Bypass V1 Timers.
        TimerItemV2 (TimerItemV2): Data model for Bypass V2 Timers.
        RequestV1ClearTimer (RequestV1ClearTimer): Model for deleting timer.
        RequestV1SetTimer (RequestV1SetTimer): Model for timer with counterTimer key.
        RequestV1GetTimer (RequestV1GetTimer): Model for getting timers from v1 API.
        RequestV1SetTime (RequestV1SetTime): Model for setting timer with counterTime key.
    """

    ResultV2GetTimer = ResultV2GetTimer
    ResultV2SetTimer = ResultV2SetTimer
    ResultV1SetTimer = ResultV1SetTimer
    ResultV1GetTimer = ResultV1GetTimerList
    TimeItemV1 = TimeItemV1
    TimerItemV1 = TimerItemV1
    TimerItemV2 = TimerItemV2
    RequestV1ClearTimer = RequestV1ClearTimer
    RequestV1SetTimer = RequestV1SetTimer
    RequestV1GetTimer = RequestV1GetTimer
    RequestV1SetTime = RequestV1SetTime
