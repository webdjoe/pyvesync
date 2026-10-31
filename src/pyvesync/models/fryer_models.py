"""Data models for VeSync air fryers."""

from __future__ import annotations

from dataclasses import dataclass, field

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
class AirFryerChamberStatus(ResponseBaseModel):
    """Status of one Turbo Tower Pro (CAF-DC111S) cooking chamber.

    Times are in seconds.
    """

    chamber: int
    cookStatus: str = 'standby'
    startTime: int = 0
    recipeType: int | None = None
    recipeId: int | None = None
    recipeName: str = ''
    upc: str = ''
    holdTime: int = 0
    cookSetTime: int = 0
    cookTemp: int = 0
    mode: str = ''
    currentRemainingTime: int = 0
    totalTimeRemaining: int = 0


@dataclass
class AirFryerMultiStatusResult(BypassV2InnerResult):
    """Result returned by getAirfryerMultiStatus."""

    statusList: list[AirFryerChamberStatus] = field(default_factory=list)
    tempUnit: str = 'c'
    syncType: int = 0
    workChamber: int = 0
