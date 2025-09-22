"""Data models for VeSync switches.

These models inherit from `ResponseBaseModel` and `RequestBaseModel` from the
`base_models` module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import orjson
from mashumaro.config import BaseConfig

from pyvesync.models.base_models import ResponseBaseModel, ResponseCodeModel
from pyvesync.models.bypass_models import RequestBypassV1


@dataclass
class ResponseSwitchDetails(ResponseCodeModel):
    """Dimmer and Wall Switch Details Response Dict."""

    result: InternalDimmerDetailsResult | InternalSwitchResult | None = None


@dataclass
class InternalSwitchResult(ResponseBaseModel):
    """Dimmer Status Response Dict."""

    deviceStatus: str
    connectionStatus: str
    activeTime: int


@dataclass
class InternalDimmerDetailsResult(ResponseBaseModel):
    """Dimmer Details Result Dict."""

    devicename: str
    brightness: int
    indicatorlightStatus: str
    rgbStatus: str
    rgbValue: DimmerRGB
    deviceStatus: str
    connectionStatus: str
    activeTime: int = 0
    timer: Any | None = None
    schedule: Any | None = None
    deviceImg: str | None = None


@dataclass
class DimmerRGB:
    """Dimmer RGB Color Dict."""

    red: int
    green: int
    blue: int


@dataclass
class RequestSwitchBase(RequestBypassV1):
    """Base Dimmer Request Dict.

    Inherits from RequestBypassV1 to include the common fields for all requests.
    """


@dataclass
class RequestDimmerBrightness(RequestBypassV1):
    """Dimmer Status Request Dict."""

    brightness: str


@dataclass
class RequestDimmerDetails(RequestBypassV1):
    """Dimmer Details Request Dict."""


@dataclass
class RequestSwitchStatus(RequestBypassV1):
    """Dimmer Details Request Dict."""

    status: str
    switchNo: int


@dataclass
class RequestDimmerStatus(RequestBypassV1):
    """Dimmer Status Request Dict."""

    status: str
    rgbValue: dict | None = None

    class Config(BaseConfig):  # type: ignore[override]
        """Dimmer Indicator Control Config Dict."""

        omit_none = True
        omit_default = True
        orjson_options = orjson.OPT_NON_STR_KEYS
