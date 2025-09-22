"""Models for VeSync Bulb API responses and requests.

These models are used to serialize and deserialize the JSON responses from the
VeSync API. The models are used in the VeSync API class methods to provide
type hints and data validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self, TypedDict

from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.mixins.orjson import DataClassORJSONMixin

from pyvesync.models.base_models import ResponseBaseModel, ResponseCodeModel
from pyvesync.models.bypass_models import BypassV2InnerResult, RequestBypassV1


@dataclass
class JSONCMD(DataClassORJSONMixin):
    """Tunable Bulb JSON CMD dict."""

    light: None | JSONCMDLight = None
    getLightStatus: None | str = None

    class Config(BaseConfig):
        """Configure the JSONCMD model."""

        omit_none = True


@dataclass
class JSONCMDLight(DataClassORJSONMixin):
    """Light JSON CMD dict."""

    action: str
    brightness: int | None = None
    colorTempe: int | None = None

    class Config(BaseConfig):
        """Configure the JSONCMDLight model."""

        omit_none = True


@dataclass
class RequestESL100Detail(RequestBypassV1):
    """Request model for Etekcity bulb details."""


@dataclass
class RequestESL100Status(RequestBypassV1):
    """Request model for Etekcity bulb details."""

    status: str


@dataclass
class RequestESL100Brightness(RequestBypassV1):
    """Request model for Etekcity bulb details."""

    status: str
    brightNess: int


@dataclass
class RequestESL100CWBase(RequestBypassV1):
    """Request model for ESL100CW bulb."""

    jsonCmd: JSONCMD


@dataclass
class ResponseESL100Detail(ResponseCodeModel):
    """Response model for Etekcity bulb details."""

    traceId: str
    code: int
    msg: str | None
    result: ResponseESL100DetailResult


@dataclass
class ResponseESL100DetailResult(ResponseBaseModel):
    """ESL100 Dimmable Bulb Device Detail Response."""

    deviceName: str | None
    name: str | None
    brightness: int | None = field(metadata=field_options(alias='brightNess'))
    activeTime: int | None
    deviceStatus: str = 'off'
    connectionStatus: str = 'offline'

    @classmethod
    def __post_deserialize__(  # type: ignore[override]
        cls, obj: Self
    ) -> Self:
        """Set values depending on color or white mode."""
        if obj.brightness is None:
            obj.brightness = 0
        if obj.activeTime is None:
            obj.activeTime = 0
        return obj


@dataclass
class ResponseESL100CWDetail(ResponseCodeModel):
    """Response model for Etekcity bulb details."""

    result: ResponseESL100CWDetailResult


@dataclass
class ResponseESL100CWLight(ResponseBaseModel):
    """ESL100CW Tunable Bulb Device Detail Response."""

    brightness: int | None
    action: str = 'on'
    colorTempe: int = 0


@dataclass
class ResponseESL100CWDetailResult(ResponseBaseModel):
    """Result model for ESL100CW Tunable bulb details."""

    light: ResponseESL100CWLight


@dataclass
class ResponseESL100MCStatus(ResponseCodeModel):
    """Response model for Etekcity bulb status."""

    result: ResponseESL100MCOuterResult


@dataclass
class ResponseESL100MCOuterResult:
    """ESL100MC Multi-Color Bulb Status Response."""

    traceId: str
    code: int
    result: ResponseESL100MCResult


@dataclass
class ResponseESL100MCResult(BypassV2InnerResult):
    """ESL100MC Multi-Color Bulb Status Response."""

    colorMode: str
    action: str
    brightness: int = 0
    red: int = 0
    green: int = 0
    blue: int = 0


@dataclass
class ResponseValcenoStatus(ResponseCodeModel):
    """Response model for Valceno bulb status."""

    result: ResponseValcenoOuterResult


@dataclass
class ResponseValcenoOuterResult(ResponseBaseModel):
    """Valceno Bulb Status Response."""

    result: ResponseValcenoStatusResult
    traceId: str = ''
    code: int = 0


@dataclass
class ResponseValcenoStatusResult(ResponseBaseModel):
    """Valceno Bulb Status Result."""

    colorMode: str = ''
    colorTemp: int = 0
    brightness: int = 0
    hue: int = 0
    saturation: int = 0
    value: int = 0
    enabled: str = 'off'


class ValcenoStatusPayload(TypedDict):
    """Typed Dict for setting Valceno bulb status."""

    colorMode: str
    colorTemp: int | str
    brightness: int | str
    hue: int | str
    saturation: int | str
    value: int | str
    force: int
