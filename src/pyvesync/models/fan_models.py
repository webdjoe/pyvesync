"""Data models for VeSync Fans.

These models inherit from `ResponseBaseModel` and `RequestBaseModel` from the
`base_models` module.
"""
from __future__ import annotations
from dataclasses import dataclass
from mashumaro.mixins.orjson import DataClassORJSONMixin

from pyvesync.const import IntFlag
from pyvesync.models.bypass_models import (
    RequestBypassV2,
    BypassV2RequestPayload,
    ResponseBypassV2,
    BypassV2OuterResult,
    BypassV2InnerResult,
)


@dataclass
class ResponseFanBase(ResponseBypassV2):
    """Fan Base Response Dict."""


@dataclass
class OuterBypassV2Result(BypassV2OuterResult):
    """Fan Result Dict."""
    result: BypassV2InnerResult | None = None


@dataclass
class TowerFanResult(BypassV2InnerResult):
    """Vital 100S/200S and Everest Fan Result Model."""
    powerSwitch: int
    filterLifePercent: int
    workMode: str
    manualSpeedLevel: int
    fanSpeedLevel: int
    screenState: int
    screenSwitch: int
    oscillationSwitch: int
    oscillationState: int
    muteSwitch: int
    muteState: int
    timerRemain: int
    temperature: int
    humidity: int
    thermalComfort: int
    errorCode: int
    scheduleCount: int
    displayingType: int = IntFlag.NOT_SUPPORTED
    sleepPreference: FanSleepPreferences | None = None


@dataclass
class FanSleepPreferences(DataClassORJSONMixin):
    """Fan Sleep Preferences."""
    sleepPreferenceType: int
    oscillationSwitch: int
    fallAsleepRemain: int
    autoChangeFanLevelSwitch: int


# Fan Request Models


@dataclass
class RequestFanStatus(RequestBypassV2):
    """Fan Status Request Dict."""
    payload: RequestFanPayload


@dataclass
class RequestFanPayload(BypassV2RequestPayload):
    """Fan Payload Request Dict."""
