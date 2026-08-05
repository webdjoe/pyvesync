"""Data models for VeSync air fryers."""

from __future__ import annotations

from dataclasses import dataclass

from pyvesync.models.base_models import ResponseBaseModel
from pyvesync.models.bypass_models import BypassV2InnerResult


@dataclass
class ResultFryerDetails(ResponseBaseModel):
    """Result model for air fryer details."""

    returnStatus: FryerCookingReturnStatus | FryerBaseReturnStatus | None = None


@dataclass
class FryerCookingReturnStatus(ResponseBaseModel):
    """Result returnStatus model for air fryer status."""

    currentTemp: int
    cookSetTemp: int
    mode: str
    cookSetTime: int
    cookLastTime: int
    cookStatus: str
    tempUnit: str


@dataclass
class FryerBaseReturnStatus(ResponseBaseModel):
    """Result returnStatus model for air fryer status."""

    cookStatus: str


@dataclass
class FryerV2StepItem(ResponseBaseModel):
    """Cooking step returned by newer VeSync air fryers."""

    cookSetTime: int
    cookTemp: int
    mode: str
    cookLastTime: int
    shakeTime: int = 0
    cookEndTime: int = 0
    recipeName: str = ''
    recipeId: int = 0
    recipeType: int = 0


@dataclass
class FryerV2Details(BypassV2InnerResult):
    """Status returned by newer single-basket VeSync air fryers."""

    stepArray: list[FryerV2StepItem]
    cookMode: str
    tempUnit: str
    stepIndex: int
    cookStatus: str
    preheatSetTime: int
    preheatLastTime: int
    preheatEndTime: int
    preheatTemp: int
    startTime: int
    totalTimeRemaining: int
    currentTemp: int
    shakeStatus: int
