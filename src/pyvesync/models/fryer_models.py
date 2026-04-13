"""Data models for VeSync air fryers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated

from mashumaro.exceptions import MissingField
from mashumaro.types import Discriminator

from pyvesync.models.base_models import RequestBaseModel, ResponseBaseModel
from pyvesync.models.bypass_models import (
    BypassV1Result,
    BypassV2InnerResult,
)


@dataclass
class Fryer158RequestModel(RequestBaseModel):
    """Request model for air fryer commands."""

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
    uuid: str
    pid: str = field(default_factory=str)
    jsonCmd: dict = field(default_factory=dict)
    # deviceId: str = field(default_factory=str)
    # configModel: str = field(default_factory=lambda: '')

    @classmethod
    def __post_deserialize__(cls, obj: Fryer158RequestModel) -> Fryer158RequestModel:  # type: ignore[reportIncompatibleMethodOverride]
        """Validate required fields after deserialization."""
        if not obj.pid:
            raise MissingField('pid', str, Fryer158RequestModel)
        if not obj.jsonCmd:
            raise MissingField('jsonCmd', dict, Fryer158RequestModel)
        return obj

    # def __post_serialize__(self, d: dict) -> dict:
    #     """Remove empty strings before serialization."""
    #     for attrs in ['deviceId', 'configModel']:
    #         d.pop(attrs, None)
    #     return d


@dataclass
class Fryer158Result(BypassV1Result):
    """Result model for air fryer details."""

    returnStatus: Fryer158CookingReturnStatus


@dataclass
class Fryer158CookingReturnStatus(ResponseBaseModel):
    """Result returnStatus model for air fryer status."""

    cookStatus: str
    currentTemp: int | None = None
    cookSetTemp: int | None = None
    mode: str | None = None
    cookSetTime: int | None = None
    cookLastTime: int | None = None
    tempUnit: str | None = None
    preheatLastTime: int | None = None
    preheatSetTime: int | None = None
    targetTemp: int | None = None
    customRecipe: str | None = None


@dataclass
class Fryer158CookRequest(RequestBaseModel):
    """Base request model for air fryer cooking commands."""

    cookMode: Annotated[Fryer158CookModeBase, Discriminator(include_subtypes=True)]


@dataclass
class Fryer158PreheatRequest(RequestBaseModel):
    """Base request model for air fryer preheat commands."""

    preheat: Annotated[Fryer158PreheatModeBase, Discriminator(include_subtypes=True)]


@dataclass
class Fryer158CookModeBase(RequestBaseModel):
    """Base model for air fryer cooking modes."""


@dataclass
class Fryer158CookModeFromPreheat(Fryer158CookModeBase):
    """Model for continuing a cooking mode."""

    cookStatus: str
    accountId: str
    mode: str


@dataclass
class Fryer158CookModeChange(Fryer158CookModeBase):
    """Model for stopping a cooking mode."""

    cookStatus: str


@dataclass
class Fryer158CookModeStart(Fryer158CookModeBase):
    """Model for starting a cooking mode."""

    cookStatus: str
    accountId: str
    mode: str
    tempUnit: str
    readyStart: bool
    cookSetTime: int
    cookSetTemp: int
    appointmentTs: int = 0
    customRecipe: str = 'Manual Cooking'
    recipeId: int = 1
    recipeType: int = 3


@dataclass
class Fryer158PreheatModeBase(RequestBaseModel):
    """Base model for air fryer preheat modes."""


@dataclass
class Fryer158PreheatModeChange(Fryer158PreheatModeBase):
    """Model for continuing a preheat mode."""

    preheatStatus: str


@dataclass
class Fryer158PreheatModeStart(Fryer158PreheatModeBase):
    """Model for starting a preheat mode."""

    preheatStatus: str
    accountId: str
    mode: str
    tempUnit: str
    readyStart: bool
    preheatSetTime: int
    targetTemp: int
    cookSetTime: int
    customRecipe: str = 'Manual'
    recipeId: int = 1
    recipeType: int = 3


@dataclass
class FryerTurboBlazeDetailResult(BypassV2InnerResult):
    """Result model for TurboBlaze air fryer details."""

    stepArray: list[FryerTurboBlazeStepItem]
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


@dataclass
class FryerTurboBlazeStepItem(ResponseBaseModel):
    """Data model for TurboBlaze air fryer cooking steps."""

    cookSetTime: int
    cookTemp: int
    mode: str
    cookLastTime: int
    shakeTime: int
    cookEndTime: int
    recipeName: str
    recipeId: int
    recipeType: int


@dataclass
class FryerTurboBlazeRequestData(RequestBaseModel):
    """Request model for TurboBlaze air fryer cooking commands."""

    accountId: str
    hasPreheat: int
    hasWarm: bool
    readyStart: bool
    recipeId: int
    recipeName: str
    recipeType: int
    tempUnit: str
    startAct: list[FryerTurboBlazeStartActItem]


@dataclass
class FryerTurboBlazeStartActItem(RequestBaseModel):
    """Data model for TurboBlaze air fryer startAct items."""

    cookSetTime: int
    cookTemp: int
    preheatTemp: int = 0
    shakeTime: int = 0


# Dual Air Fryer Models (CAF-TF101S)


@dataclass
class FryerDualChamberStatusItem(ResponseBaseModel):
    """Status item for a single chamber in dual air fryer status response."""

    cookStatus: str
    chamber: int
    cookSetTime: int = 0
    cookTemp: int = 0
    mode: str = ''
    currentRemainingTime: int = 0
    totalTimeRemaining: int = 0
    startTime: int = 0
    recipeType: int = 3
    recipeId: int = 0
    recipeName: str = ''
    upc: str = ''
    holdTime: int = 0


@dataclass
class FryerDualMultiStatusResult(BypassV2InnerResult):
    """Result model for dual air fryer getAirfryerMultiStatus response."""

    statusList: list[FryerDualChamberStatusItem]
    tempUnit: str = 'c'
    syncType: int = 0
    workChamber: int = 0


@dataclass
class FryerDualCookConfig(RequestBaseModel):
    """Cook configuration for a single chamber in startMultiCook request."""

    chamber: int
    cookSetTime: int
    cookTemp: int
    mode: str
    recipeId: int
    recipeName: str
    recipeType: int


@dataclass
class FryerDualStartCookData(RequestBaseModel):
    """Request data for dual air fryer startMultiCook command."""

    accountId: str
    cookConfigs: list[FryerDualCookConfig]
    readyStart: bool
    syncType: int
    tempUnit: str
    workChamber: int
