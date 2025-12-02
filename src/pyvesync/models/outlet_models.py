"""Data models for VeSync outlets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, TypeVar

from mashumaro.config import BaseConfig
from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.types import Alias

from pyvesync.models.base_models import (
    RequestBaseModel,
    ResponseBaseModel,
    ResponseCodeModel,
)
from pyvesync.models.bypass_models import (
    BypassV1Result,
    BypassV2InnerResult,
    RequestBypassV1,
)

T = TypeVar('T', bound='RequestWHOGYearlyEnergy')


@dataclass
class Response7AOutlet(ResponseBaseModel):
    """Response model for 7A outlet."""

    activeTime: int
    energy: float
    deviceStatus: str
    power: float | str
    voltage: float | str


@dataclass
class ResponseEnergyHistory(ResponseCodeModel):
    """Response model for energy history."""

    result: ResponseEnergyResult


@dataclass
class ResponseEnergyResult(BypassV2InnerResult):
    """Response model for energy result."""

    energyInfos: list[EnergyInfo]
    energyConsumptionOfToday: float | None = None
    costPerKWH: float | None = None
    maxEnergy: float | None = None
    totalEnergy: float | None = None


@dataclass
class EnergyInfo:
    """Energy Info list items."""

    timestamp: int
    energyKWH: Annotated[float, Alias('energy')]
    money: float | None = None

    class Config(BaseConfig):
        """Allow deserialization not by alias."""

        allow_deserialization_not_by_alias = True


@dataclass
class Response10ADetails(DataClassORJSONMixin):
    """Response model for Etekcity outlet details."""

    code: int
    msg: str | None
    deviceStatus: str
    connectionStatus: str
    activeTime: int
    power: float
    voltage: float
    energy: float | None = None
    nightLightStatus: str | None = None
    nightLightAutoMode: str | None = None
    nightLightBrightness: int | None = None


@dataclass
class RequestESW03Status(RequestBypassV1):
    """Request model for Etekcity 10A outlet status."""

    status: str


@dataclass
class ResponseESW03Details(BypassV1Result):
    """Response model for Etekcity 10A outlet details."""

    activeTime: int
    deviceStatus: str
    connectionStatus: str
    power: float | None = None
    voltage: float | None = None
    energy: float | None = None


@dataclass
class ResponseOldEnergy(ResponseCodeModel):
    """Response model for old energy history."""

    energyConsumptionOfToday: float
    costPerKWH: float
    maxEnergy: float
    totalEnergy: float
    data: list[float]


@dataclass
class Response15ADetails(ResponseCodeModel):
    """Response for 15A Outlets."""

    result: Response15AOutletResult


@dataclass
class Response15AOutletResult(ResponseBaseModel):
    """Response model for 15A outlet."""

    deviceStatus: str
    connectionStatus: str
    activeTime: int
    power: float
    voltage: float
    energy: float | None = None
    nightLightStatus: str | None = None
    nightLightAutoMode: str | None = None
    nightLightBrightness: int | None = None


@dataclass
class Request15ADetails(RequestBypassV1):
    """Request data model for 15A outlet Details."""


@dataclass
class RequestOutdoorStatus(RequestBypassV1):
    """Request model for outlet status."""

    status: str
    switchNo: str


@dataclass
class RequestEnergyHistory(RequestBaseModel):
    """Request model for energy history."""

    acceptLanguage: str
    appVersion: str
    accountID: str
    method: str
    phoneBrand: str
    phoneOS: str
    timeZone: str
    token: str
    traceId: str
    userCountryCode: str
    debugMode: bool
    homeTimeZone: str
    uuid: str


@dataclass
class Request15AStatus(RequestBypassV1):
    """Request data model for 15A outlet.

    Inherits from RequestBypassV1.
    """

    status: str


@dataclass
class Request15ANightlight(RequestBypassV1):
    """Nightlight request data model for 15A Outlets.

    Inherits from RequestBypassV1.
    """

    mode: str


@dataclass
class ResponseOutdoorDetails(ResponseCodeModel):
    """Response model for outdoor outlet."""

    result: ResponseOutdoorOutletResult


@dataclass
class ResponseOutdoorOutletResult(ResponseBaseModel):
    """Response model for outdoor outlet."""

    deviceStatus: str
    connectionStatus: str
    activeTime: int
    power: float
    voltage: float
    energy: float
    subDevices: list[ResponseOutdoorSubDevices]


@dataclass
class ResponseOutdoorSubDevices(ResponseBaseModel):
    """Response model for outdoor energy."""

    subDeviceNo: int
    defaultName: str
    subDeviceName: str
    subDeviceStatus: str


@dataclass
class ResponseBSDGO1Details(ResponseCodeModel):
    """Response model for BSDGO1 outlet."""

    result: ResponseBSDGO1OutletResult


@dataclass
class ResponseWHOGResult(BypassV2InnerResult):
    """Response model for WHOG outlet."""

    enabled: bool
    voltage: float | None = None
    power: float | None = None
    energy: float | None = None
    current: float | None = None
    highestVoltage: float | None = None
    voltagePtStatus: bool | None = None


@dataclass
class ResponseBSDGO1OutletResult(BypassV2InnerResult):
    """Response model for BSDGO1 outlet."""

    powerSwitch_1: int
    realTimeVoltage: float | None = None
    realTimePower: float | None = None
    electricalEnergy: float | None = None
    voltageUpperThreshold: float | None = None
    protectionStatus: str | None = None
    currentUpperThreshold: float | None = None


@dataclass
class Timer7AItem(ResponseBaseModel):
    """Timer item for 7A outlet."""

    timerID: str
    counterTimer: int
    action: str
    timerStatus: str


@dataclass
class ResultESW10Details(ResponseBaseModel):
    """Response model for ESW10 outlet."""

    enabled: bool


@dataclass
class RequestWHOGYearlyEnergy(RequestBypassV1):
    """Request model for WHOG yearly energy history."""

    subDeviceNo: int = 0

    def __post_serialize__(self: RequestWHOGYearlyEnergy, d: dict) -> dict:
        """Remove unneeded keys after serialization."""
        d.pop('uuid', None)
        return d
