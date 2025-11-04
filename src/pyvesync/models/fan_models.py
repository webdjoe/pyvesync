"""Data models for VeSync Fans.

These models inherit from `ResponseBaseModel` and `RequestBaseModel` from the
`base_models` module.
"""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro.mixins.orjson import DataClassORJSONMixin

from pyvesync.models.bypass_models import (
    BypassV2InnerResult,
)


@dataclass
class TowerFanResult(BypassV2InnerResult):
    """Tower Fan Result Model."""

    powerSwitch: int
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
    errorCode: int
    scheduleCount: int
    displayingType: int | None = None
    sleepPreference: FanTowerSleepPreferences | None = None


@dataclass
class FanSleepPreferences(DataClassORJSONMixin):
    """Fan Sleep Preferences."""


@dataclass
class FanTowerSleepPreferences(FanSleepPreferences):
    """Fan Sleep Preferences."""

    sleepPreferenceType: str
    oscillationSwitch: int
    fallAsleepRemain: int
    autoChangeFanLevelSwitch: int


@dataclass
class FanPedestalSleepPreferences(FanSleepPreferences):
    """Fan Sleep Preferences."""

    sleepPreferenceType: str
    oscillationState: int
    fallAsleepRemain: int
    initFanSpeedLevel: int


@dataclass
class PedestalFanResult(BypassV2InnerResult):
    """Pedestal Fan Result Model."""

    powerSwitch: int
    workMode: str
    fanSpeedLevel: int
    temperature: int
    muteSwitch: int
    muteState: int
    screenState: int
    screenSwitch: int
    horizontalOscillationState: int
    verticalOscillationState: int
    childLock: int
    errorCode: int
    oscillationCoordinate: OscillationCoordinatesModel | None = None
    oscillationRange: OscillationRangeModel | None = None
    sleepPreference: FanPedestalSleepPreferences | None = None


@dataclass
class OscillationCoordinatesModel(DataClassORJSONMixin):
    """Oscillation Coordinates Model."""

    yaw: int
    pitch: int


@dataclass
class OscillationRangeModel(DataClassORJSONMixin):
    """Oscillation Range Model."""

    left: int
    right: int
    top: int
    bottom: int
