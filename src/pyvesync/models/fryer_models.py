"""Data models for VeSync air fryers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated

from mashumaro.types import Discriminator

from pyvesync.models.base_models import RequestBaseModel, ResponseBaseModel
from pyvesync.models.bypass_models import BypassV1Result, RequestBypassV1


@dataclass
class Fryer158RequestModel(RequestBypassV1):
    """Request model for air fryer commands."""

    pid: str  # type: ignore[misc]  # bug in mypy invalid argument ordering
    jsonCmd: dict  # type: ignore[misc]  # bug in mypy invalid argument ordering
    deviceId: str = field(default_factory=str)
    configModel: str = field(default_factory=lambda: '')

    def __post_serialize__(self, d: dict) -> dict:
        """Remove empty strings before serialization."""
        for attrs in ['deviceId', 'configModel']:
            d.pop(attrs, None)
        return d


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


# a = {
#     'cookMode': {
#         'accountId': '1221391',
#         'appointmentTs': 0,
#         'cookSetTemp': 350,
#         'cookSetTime': 15,
#         'cookStatus': 'cooking',
#         'customRecipe': 'Manual Cooking',
#         'mode': 'custom',
#         'readyStart': True,
#         'recipeId': 1,
#         'recipeType': 3,
#         'tempUnit': 'fahrenheit',
#     },
#     'preheat': {
#         'customRecipe': 'Manual',
#         'readyStart': False,
#         'cookSetTime': 15,
#         'tempUnit': 'fahrenheit',
#         'mode': 'custom',
#         'accountId': '1221391',
#         'targetTemp': 350,
#         'preheatSetTime': 4,
#         'preheatStatus': 'heating',
#         'recipeId': 1,
#         'recipeType': 3,
#     },
#     'cookMode': {
#         'accountId': '1221391',
#         'cookSetTemp': 400,
#         'recipeId': 1,
#         'mode': 'custom',
#         'readyStart': False,
#         'appointmentTs': 0,
#         'cookStatus': 'cooking',
#         'customRecipe': 'Manual',
#         'cookSetTime': 15,
#         'tempUnit': 'fahrenheit',
#         'recipeType': 3,
#     },
# }
