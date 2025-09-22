"""Data models for VeSync air fryers."""

from __future__ import annotations

from dataclasses import dataclass

from pyvesync.models.base_models import ResponseBaseModel


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
