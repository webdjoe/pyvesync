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
    sleepPreference: FanSleepPreferences | None = None


@dataclass
class FanSleepPreferences(DataClassORJSONMixin):
    """Fan Sleep Preferences."""

    sleepPreferenceType: str
    oscillationSwitch: int
    fallAsleepRemain: int
    autoChangeFanLevelSwitch: int
