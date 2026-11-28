"""Data models for VeSync Purifiers.

These models inherit from `ResponseBaseModel` and `RequestBaseModel` from the
`base_models` module.

The `InnerPurifierBaseResult` class is used as a base class for the inner purifier
result models for all models and the mashumaro discriminator determines the correct
subclass when deserializing.
"""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro.config import BaseConfig
from mashumaro.types import Discriminator

from pyvesync.models.base_models import (
    RequestBaseModel,
    ResponseBaseModel,
)
from pyvesync.models.bypass_models import (
    BypassV1Result,
    BypassV2InnerResult,
    RequestBypassV1,
)


@dataclass
class InnerPurifierBaseResult(BypassV2InnerResult):
    """Base class for inner purifier results model."""

    class Config(BaseConfig):  # type: ignore[override]
        """Configure the results model to use subclass discriminator."""

        discriminator = Discriminator(include_subtypes=True)


@dataclass
class PurifierVitalDetailsResult(InnerPurifierBaseResult):
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
    autoPreference: V2AutoPreferences | None = None
    fanRotateAngle: int | None = None
    filterOpenState: int | None = None
    PM1: int | None = None
    PM10: int | None = None
    AQPercent: int | None = None


@dataclass
class V2AutoPreferences:
    """Vital 100S/200S Auto Preferences."""

    autoPreferenceType: str
    roomSize: int


@dataclass
class PurifierSproutResult(InnerPurifierBaseResult):
    """Sprout Purifier Result Model."""

    powerSwitch: int
    workMode: str
    manualSpeedLevel: int | None
    fanSpeedLevel: int | None
    PM1: int | None
    PM25: int | None
    PM10: int | None
    screenState: int
    childLockSwitch: int
    screenSwitch: int
    scheduleCount: int
    timerRemain: int
    humidity: int | None
    AQI: int | None
    AQLevel: int | None
    temperature: int | None
    VOC: int | None
    CO2: int | None
    errorCode: int
    nightlight: PurifierNightlight | None = None
    autoPreference: V2AutoPreferences | None = None


@dataclass
class PurifierVitalPetProResult(InnerPurifierBaseResult):
    """Vital Pet (LAP-P201S) and Vital Pet Pro (LAP-P501S) status result model.

    The `getPurifierStatus` result. The Vital Pet reports no
    `autoCleanPreference`.

    `odorLevel`, `resetFilterDate`, `cumulativeCleanAir` and `totalCleanAir`
    are parsed but not used: their meaning or unit is not known.
    """

    powerSwitch: int
    workMode: str
    manualSpeedLevel: int
    fanSpeedLevel: int
    AQLevel: int
    PM25: int
    filterLifePercent: int
    screenState: int
    screenSwitch: int
    childLockSwitch: int
    scheduleCount: int
    timerRemain: int
    errorCode: int
    VOC: int | None = None
    buzzerSwitch: int | None = None  # VeSync app Mute switch: 1 = muted, 0 = beep on
    filterRemainDay: int | None = None
    filterOpenState: int | None = None
    screenPreference: PurifierScreenPreference | None = None
    childLockPreference: PurifierChildLockPreference | None = None
    autoCleanPreference: PurifierAutoCleanPreference | None = None
    errorCodes: list[int] | None = None
    odorLevel: int | None = None
    resetFilterDate: int | None = None
    cumulativeCleanAir: int | None = None
    totalCleanAir: int | None = None


@dataclass
class PurifierElevaAutoPreference(ResponseBaseModel):
    """Auto preference in the Core 300S MaxAQ status response.

    Separate from `V2AutoPreferences` because the device reports no `roomSize`.
    """

    autoPreferenceType: str


@dataclass
class PurifierQuietPeriod(ResponseBaseModel):
    """Quiet Period in the Core 300S MaxAQ status response.

    `modeIdx` is `PurifierQuietPeriodMode`. The times are the Customized
    window, in seconds since midnight.
    """

    quietPeriodSwitch: int
    modeIdx: int
    startTime: int | None = None
    endTime: int | None = None


@dataclass
class PurifierElevaResult(InnerPurifierBaseResult):
    """Core 300S MaxAQ / Eleva 300X (LAP-C341S) status result model.

    The `getPurifierStatus` result. The required fields are in both the US
    capture and the EU status (issue #545). The EU unit reports no `group`,
    so the Health Protect fields are optional.

    `carbonFilterResetDate`, `preFilterLastCleanDate`, `curFilterCert`,
    `authenticatedTsInSec`, `resetFilterDate`, `totalCleanAir`,
    `dataScheduleRules`, `sensorInfos`, `supportTrendType` and `buzzerSwitch`
    are not modelled; they are ignored because `forbid_extra_keys` is False.
    """

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
    timerRemain: int
    scheduleCount: int
    errorCode: int
    filterRemainDay: int | None = None
    carbonFilterLifePercent: int | None = None
    preFilterLifePercent: int | None = None
    PM1: int | None = None
    PM10: int | None = None
    AQI: int | None = None
    aqiLightMode: int | None = None
    group: int | None = None
    standbyGuardSwitch: int | None = None
    manualGuardSwitch: int | None = None
    sleepGuardSwitch: int | None = None
    autoPreference: PurifierElevaAutoPreference | None = None
    quietPeriod: PurifierQuietPeriod | None = None
    errorCodes: list[int] | None = None


@dataclass
class PurifierScreenPreference(ResponseBaseModel):
    """Display preference in the Vital Pet and Vital Pet Pro status response."""

    screenOnType: int
    screenStartTime: int | None = None
    screenEndTime: int | None = None


@dataclass
class PurifierChildLockPreference(ResponseBaseModel):
    """Auto child lock preference in the Vital Pet and Vital Pet Pro status response."""

    childLockAutoSwitch: int
    childLockAutoSwitchTime: int


@dataclass
class PurifierAutoCleanPreference(ResponseBaseModel):
    """Self-cleaning state in the Vital Pet Pro status response.

    `autoCleanState` is 1 while a run is active and 0 when idle; the
    times are in seconds.
    """

    autoCleanState: int
    autoCleanRemainTime: int | None = None
    autoCleanTotalTime: int | None = None
    previousCleanTime: int | None = None


@dataclass
class PurifierNightlight(ResponseBaseModel):
    """Purifier Nightlight Response Dict."""

    nightLightSwitch: bool
    brightness: int
    colorTemperature: int


@dataclass
class PurifierCoreDetailsResult(InnerPurifierBaseResult):
    """Purifier inner Result Dict."""

    enabled: bool
    filter_life: int
    mode: str
    level: int
    device_error_code: int
    levelNew: int | None = None
    air_quality: int | None = None
    display: bool | None = None
    child_lock: bool | None = None
    configuration: PurifierCoreDetailsConfig | None = None
    extension: dict | None = None
    air_quality_value: int | None = None
    night_light: str | None = None
    fan_rotate: str | None = None


# Purifier Timer Models


@dataclass
class PurifierModifyTimerResult(InnerPurifierBaseResult):
    """Purifier inner Add Timer Result Dict."""

    id: int


@dataclass
class PurifierGetTimerResult(InnerPurifierBaseResult):
    """Purifier inner Timer Result Dict."""

    timers: list[ResponsePurifierTimerItems] | None


@dataclass
class ResponsePurifierTimerItems(ResponseBaseModel):
    """Purifier Timer Items Response Dict."""

    id: int
    remain: int
    total: int
    action: str


@dataclass
class PurifierV2TimerPayloadData(RequestBaseModel):
    """Purifier Timer Payload Data Request Dict."""

    enabled: bool
    startAct: list[PurifierV2TimerActionItems]
    tmgEvt: PurifierV2EventTiming | None = None
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


# Internal Purifier Details Models


@dataclass
class PurifierCoreDetailsConfig(ResponseBaseModel):
    """Config dict in Core purifier details response."""

    display: bool
    display_forever: bool
    auto_preference: None | PurifierCoreAutoConfig = None


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
class RequestPurifier131(RequestBypassV1):
    """Purifier 131 Request Dict."""

    status: str | None = None


@dataclass
class RequestPurifier131Mode(RequestBypassV1):
    """Purifier 131 Request Dict."""

    mode: str


@dataclass
class RequestPurifier131Level(RequestBypassV1):
    """Purifier 131 Request Dict."""

    level: int


@dataclass
class Purifier131Result(BypassV1Result):
    """Purifier 131 Details Response Dict."""

    screenStatus: str
    activeTime: int
    levelNew: int
    level: int | None
    mode: str
    airQuality: str
    deviceName: str
    deviceStatus: str
    connectionStatus: str
    filterLife: Purifier131Filter | None = None


@dataclass
class Purifier131Filter(ResponseBaseModel):
    """Filter details model for LV PUR131."""

    change: bool
    useHour: int
    percent: int


@dataclass
class PurifierRH131Result(BypassV2InnerResult):
    """Purifier RH131 Details Response Dict."""

    enabled: bool
    filter_life: int
    mode: str
    level: int
    air_quality: int
    display: bool
    child_lock: bool
    buzzer: bool
    configuration: dict
    extension: PurifierRH131DetailsExtension | None = None


@dataclass
class PurifierRH131DetailsExtension(ResponseBaseModel):
    """Extension dict in RH131 purifier details response."""

    schedule_count: int
    timer_remain: int
