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
class AirFryerChamberStatus(ResponseBaseModel):
    """Status of one CAF-DC111S-AEU cooking chamber."""

    cookStatus: str
    startTime: int
    recipeType: int
    recipeId: int
    recipeName: str
    upc: str
    holdTime: int
    cookSetTime: int
    cookTemp: int
    mode: str
    currentRemainingTime: int
    totalTimeRemaining: int
    chamber: int


@dataclass
class AirFryerMultiStatusResult(BypassV2InnerResult):
    """Result returned by getAirfryerMultiStatus."""

    statusList: list[AirFryerChamberStatus]
    tempUnit: str
    syncType: int
    workChamber: int
