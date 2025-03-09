"""Data models for VeSync Humidifier devices."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Annotated

from mashumaro.config import BaseConfig
from mashumaro.types import Discriminator, Alias
import orjson

from pyvesync.data_models.base_models import (
    ResponseBaseModel,
    RequestBaseModel,
    ResponseCodeModel
    )
from pyvesync.const import IntFlag


@dataclass
class ResponseHumidifierBase(ResponseCodeModel):
    """Humidifier Base Response Dict."""
    result: OuterHumidifierResult

    class Config(BaseConfig):
        """Config for mashumaro serialization."""
        orjson_options = orjson.OPT_NON_STR_KEYS
        forbid_extra_keys = False


@dataclass
class OuterHumidifierResult(ResponseCodeModel):
    """Humidifier Result Dict."""
    result: InnerHumidifierBaseResult | None = None


@dataclass
class InnerHumidifierBaseResult:
    """Base class for inner humidifier results model."""

    class Config(BaseConfig):
        """Configure the results model to use subclass discriminator."""
        discriminator = Discriminator(include_subtypes=True)


# Inner Result models for individual devices inherit from InnerHumidifierBaseResult
# and are used to parse the response from the API.
# The correct subclass is determined by the mashumaro discriminator

@dataclass
class ClassicLVHumidResult(InnerHumidifierBaseResult):
    """Classic 200S Humidifier Result Model.

    Inherits from InnerHumidifierBaseResult.
    """
    enabled: bool
    mist_virtual_level: int
    mist_level: int
    mode: str
    water_lacks: bool = False
    humidity: int | None = None
    humidity_high: bool = False
    display: Annotated[bool, Alias("indicator_light_status")] = False
    automatic_stop_reach_target: bool = False
    water_tank_lifted: bool = False
    warm_enabled: bool = False
    warm_level: int = IntFlag.NOT_SUPPORTED
    night_light_brightness: int = IntFlag.NOT_SUPPORTED
    configuration: ClassicConfig | None = None


@dataclass
class ClassicConfig:
    """Classic 200S Humidifier Configuration Model."""
    auto_target_humidity: int = 0
    display: Annotated[bool, Alias("indicator_light_status")] = False
    automatic_stop: bool = False


@dataclass
class LV600SConfig:
    """LV 600S Humidifier Configuration Model."""
    auto_target_humidity: int = 0
    display: bool = False


@dataclass
class LV600SExtension:
    """LV 600S Humidifier Configuration Model."""
    timer_remain: int = 0
    schedule_count: int = 0


@dataclass
class LV600SHumidResult(InnerHumidifierBaseResult):
    """LV600S Humidifier Result Model.

    Inherits from InnerHumidifierBaseResult.
    """
    automatic_stop_reach_target: bool
    display: bool
    enabled: bool
    humidity: int
    humidity_high: bool
    mist_level: int
    mist_virtual_level: int
    mode: str

    water_lacks: bool
    water_tank_lifted: bool
    extension: LV600SExtension | None = None
    configuration: LV600SConfig | None = None


# Bypass V2 Humidifier Request Models

@dataclass
class RequestHumidifierStatus(RequestBaseModel):
    """Humidifier Status Request Dict."""
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
    payload: HumidifierRequestPayload


@dataclass
class HumidifierRequestPayload(RequestBaseModel):
    """Humidifier Payload Request Dict."""
    data: dict
    method: str
    source: str = "APP"


# Models for the VeSync Superior 6000S Humidifier

@dataclass
class Superior6000SResult(InnerHumidifierBaseResult):
    """Superior 6000S Humidifier Result Model.

    Inherits from InnerHumidifierBaseResult.
    """
    powerSwitch: int
    humidity: int
    targetHumidity: int
    virtualLevel: int
    mistLevel: int
    workMode: str
    waterLacksState: int
    waterTankLifted: int
    autoStopSwitch: int
    autoStopState: int
    screenSwitch: int
    screenState: int
    scheduleCount: int
    timerRemain: int
    errorCode: int
    autoPreference: int
    childLockSwitch: int
    filterLifePercent: int
    temperature: int
    dryingMode: Superior6000SDryingMode | None = None


@dataclass
class Superior6000SDryingMode(ResponseBaseModel):
    """Drying Mode Model for Superior 6000S Humidifier."""
    dryingLevel: int
    autoDryingSwitch: int
    dryingState: int
    dryingRemain: int


# Models for the Levoit 1000S Humidifier

@dataclass
class Levoit1000SResult(InnerHumidifierBaseResult):
    """Levoit 1000S Humidifier Result Model."""
    powerSwitch: int
    humidity: int
    targetHumidity: int
    virtualLevel: int
    mistLevel: int
    workMode: str
    waterLacksState: int
    waterTankLifted: int
    autoStopSwitch: int
    autoStopState: int
    screenSwitch: int
    screenState: int
    scheduleCount: int
    timerRemain: int
    errorCode: int
