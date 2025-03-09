"""Data models for VeSync Fans."""
from __future__ import annotations
from dataclasses import dataclass
import orjson
from mashumaro.types import Discriminator
from mashumaro.config import BaseConfig
from pyvesync.const import IntFlag
from mashumaro.mixins.orjson import DataClassORJSONMixin
from pyvesync.data_models.base_models import (
    RequestBaseModel,
    ResponseCodeModel,
    )


@dataclass
class ResponseFanBase(ResponseCodeModel):
    """Fan Base Response Dict."""
    result: OuterBypassV2Result

    class Config(BaseConfig):
        """Config for mashumaro serialization."""
        orjson_options = orjson.OPT_NON_STR_KEYS
        forbid_extra_keys = False


@dataclass
class OuterBypassV2Result(DataClassORJSONMixin):
    """Fan Result Dict."""
    traceId: str
    code: int
    result: InnerFanBaseResult | None = None


# Inner Fan Result Models for Core and Everest/Vital Fans
# Correct subclass is determined by mashumaro's discriminator

@dataclass
class InnerFanBaseResult(DataClassORJSONMixin):
    """Base class for inner purifier results model."""

    class Config(BaseConfig):
        """Configure the results model to use subclass discriminator."""
        discriminator = Discriminator(include_subtypes=True)


@dataclass
class TowerFanResult(InnerFanBaseResult):
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
class RequestFanStatus(RequestBaseModel):
    """Fan Status Request Dict."""
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
    payload: RequestFanPayload


@dataclass
class RequestFanPayload(RequestBaseModel):
    """Fan Payload Request Dict."""
    data: dict
    method: str
    source: str = "APP"
