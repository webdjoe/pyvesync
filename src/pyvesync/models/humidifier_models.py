"""Data models for VeSync Humidifier devices.

These models inherit from `ResponseBaseModel` and `RequestBaseModel` from the
`base_models` module.

The `InnerHumidifierBaseResult` class is used as a base class for the inner humidifier
result models. The correct subclass is determined by the mashumaro discriminator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from mashumaro.config import BaseConfig
from mashumaro.types import Alias

from pyvesync.models.base_models import (
    ResponseBaseModel,
    ResponseCodeModel,
)


@dataclass
class ResponseHumidifierBase(ResponseCodeModel):
    """Humidifier Base Response Dict."""

    result: OuterHumidifierResult


@dataclass
class OuterHumidifierResult(ResponseBaseModel):
    """Humidifier Result Dict."""

    code: int
    result: InnerHumidifierBaseResult


@dataclass
class InnerHumidifierBaseResult(ResponseBaseModel):
    """Base class for inner humidifier results model.

    All inner results models inherit from this class and are
    correctly subclassed by the mashumaro discriminator.
    """

    class Config(BaseConfig):  # type: ignore[override]
        """Configure the results model to use subclass discriminator."""

        allow_deserialization_not_by_alias = True


class BypassV2InnerErrorResult(InnerHumidifierBaseResult):
    """Inner Error Result Model."""

    msg: str


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
    display: Annotated[bool, Alias('indicator_light_switch')]
    water_lacks: bool
    humidity: int | None = None
    humidity_high: bool = False
    automatic_stop_reach_target: bool = False
    water_tank_lifted: bool = False
    warm_enabled: bool = False
    warm_level: int | None = None
    night_light_brightness: int | None = None
    configuration: ClassicConfig | None = None


@dataclass
class ClassicConfig(ResponseBaseModel):
    """Classic 200S Humidifier Configuration Model."""

    auto_target_humidity: int = 0
    display: Annotated[bool, Alias('indicator_light_switch')] = False
    automatic_stop: bool = False

    class Config(BaseConfig):  # type: ignore[override]
        """Configure the results model to use subclass discriminator."""

        allow_deserialization_not_by_alias = True
        forbid_extra_keys = False


@dataclass
class LV600SConfig(ResponseBaseModel):
    """LV 600S Humidifier Configuration Model."""

    auto_target_humidity: int = 0
    display: bool = False


@dataclass
class LV600SExtension(ResponseBaseModel):
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
    dryingMode: DryingModeModel | None = None


@dataclass
class DryingModeModel(ResponseBaseModel):
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
    nightLight: Levoit1000SNightLight | None = None


@dataclass
class Levoit1000SNightLight(ResponseBaseModel):
    """Night Light Model for Levoit 1000S Humidifier."""

    nightLightSwitch: int
    brightness: int


@dataclass
class SproutHumidifierResult(InnerHumidifierBaseResult):
    """Sprout Humidifier Result Model."""

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
    autoModePreference: int
    autoPreference: int
    waterShortageDryingSwitch: int
    childLockSwitch: int
    filterLifePercent: int
    hepaFilterLifePercent: int
    temperature: int
    lampSwitch: int
    lampType: int
    dumpedState: int
    roomSize: int
    supportLampAct: int
    lastDryingCompletedTime: int
    afterDryLastHumidityTime: int
    sensorContent: SproutSensorcontent | None = None
    breathingLamp: SproutBreathinglamp | None = None
    guardingInfo: SproutGuardinginfo | None = None
    dryingMode: DryingModeModel | None = None
    nightLight: SproutNightlight | None = None


@dataclass
class SproutSensorcontent(ResponseBaseModel):
    """Sprout Humidifier Sensor Content Model."""

    selfSensorMac: str
    selfSenorBattery: int
    selfSensorStatus: str


@dataclass
class SproutNightlight(ResponseBaseModel):
    """Sprout Humidifier Night Light Model."""

    nightLightSwitch: int
    brightness: int
    colorTemperature: int


@dataclass
class SproutBreathinglamp(ResponseBaseModel):
    """Sprout Humidifier Breathing Lamp Model."""

    breathingLampSwitch: int
    colorTemperature: int
    timeInterval: int
    brightnessStart: int
    brightnessEnd: int


@dataclass
class SproutGuardinginfo(ResponseBaseModel):
    """Sprout Humidifier Guarding Info Model."""

    guarding: int
    remainTS: int


@dataclass
class LV600SResult(InnerHumidifierBaseResult):
    """LV600S (LUH-A603S) Humidifier Result Model.

    Uses the newer API format with powerSwitch, workMode, etc.
    Includes warm mist support via warmPower and warmLevel.
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
    totalWorkTime: int = 0
    warmPower: bool = False
    warmLevel: int = 0
