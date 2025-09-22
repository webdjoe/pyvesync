"""Data models for VeSync outlets."""

from __future__ import annotations

from dataclasses import dataclass

from mashumaro.mixins.orjson import DataClassORJSONMixin

from pyvesync.models.base_models import (
    RequestBaseModel,
    ResponseBaseModel,
    ResponseCodeModel,
)
from pyvesync.models.bypass_models import (
    RequestBypassV1,
)


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
class ResponseEnergyResult(ResponseBaseModel):
    """Response model for energy result."""

    energyConsumptionOfToday: float
    costPerKWH: float
    maxEnergy: float
    totalEnergy: float
    energyInfos: list[EnergyInfo]


@dataclass
class EnergyInfo:
    """Energy Info list items."""

    timestamp: int
    energyKWH: float
    money: float


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
class ResponseBSDGO1OutletResult(ResponseBaseModel):
    """Response model for BSDGO1 outlet."""

    powerSwitch_1: int
    active_time: int
    connectionStatus: str
    code: int


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
