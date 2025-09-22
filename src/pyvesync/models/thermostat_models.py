"""Data models for VeSync thermostats."""

from __future__ import annotations

from dataclasses import dataclass, field

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from pyvesync.const import ThermostatConst
from pyvesync.models.bypass_models import BypassV2InnerResult


@dataclass
class ResultThermostatDetails(BypassV2InnerResult):
    """Result model for thermostat details."""

    supportMode: list[int]
    workMode: int
    workStatus: int
    fanMode: int
    fanStatus: int
    tempUnit: str
    temperature: float
    humidity: int
    heatToTemp: int
    coolToTemp: int
    lockStatus: bool
    scheduleOrHold: int
    holdEndTime: int
    holdOption: int
    deadband: int
    ecoType: int
    alertStatus: int
    routines: list[ThermostatSimpleRoutine]
    routineRunningId: int | None = None


@dataclass
class ThermostatSimpleRoutine(DataClassORJSONMixin):
    """Thermostat routine model."""

    name: str
    routineId: int


@dataclass
class ThermostatRoutine(DataClassORJSONMixin):
    """Model for full thermostat routine."""

    name: str
    routineId: int
    type: int
    heatToTemp: int
    coolToTemp: int
    heatFanMode: int
    coolFanMode: int
    usuallyMask: int
    sensorIds: list[str]


@dataclass
class ThermostatMinorDetails(DataClassORJSONMixin):
    """Model for thermostat minor details."""

    mcu_version: str = field(metadata=field_options(alias='mcuVersion'))
    hvac_capacity: int = field(metadata=field_options(alias='hvacCapcity'))
    timestamp: int = field(metadata=field_options(alias='timeStamp'))
    time_zone: int = field(metadata=field_options(alias='timeZone'))
    offset_in_sec: int = field(metadata=field_options(alias='offsetInSec'))
    time_fmt: int = field(metadata=field_options(alias='timeFmt'))
    date_fmt: int = field(metadata=field_options(alias='dateFmt'))
    fan_delay_time: int = field(metadata=field_options(alias='fanDelayTime'))
    fan_circulation_time: int = field(metadata=field_options(alias='fanCirTime'))
    hvac_protect_time: int = field(metadata=field_options(alias='hvacProtecTime'))
    hvac_min_on_time: int = field(metadata=field_options(alias='hvacMinOnTime'))
    aux_min_on_time: int = field(metadata=field_options(alias='auxMinOnTime'))
    screen_brightness: int = field(metadata=field_options(alias='screenBrightness'))
    standby_timeout: int = field(metadata=field_options(alias='standbyTimeOut'))
    aux_low_temperature: int = field(metadata=field_options(alias='auxLowBalanceTemp'))
    aux_high_temperature: int = field(metadata=field_options(alias='auxHighBalanceTemp'))
    keytone: bool = field(metadata=field_options(alias='keyTone'))
    smart_schedule_enabled: bool = field(
        metadata=field_options(alias='smartScheduleEnabled')
    )
    time_to_temp_enabled: bool = field(metadata=field_options(alias='timeToTempEnabled'))
    early_on_enabled: bool = field(metadata=field_options(alias='earlyOnEnabled'))
    reminder_list: list[ThermostatReminder] = field(
        metadata=field_options(alias='reminderList')
    )
    alarm_list: list[ThermostatAlarm] = field(metadata=field_options(alias='alarmList'))


@dataclass
class ThermostatReminder(DataClassORJSONMixin):
    """Model for thermostat reminder."""

    code: int
    enabled: bool
    frequency: int
    code_name: str | None = None
    last_maintenance_time: int | None = field(
        default=None, metadata=field_options(alias='lastMaintenTime')
    )

    @classmethod
    def __post_deserialize__(  # type: ignore[override]
        cls, obj: ThermostatReminder
    ) -> ThermostatReminder:
        """Post-deserialization processing."""
        if isinstance(obj.code, int):
            obj.code_name = ThermostatConst.ReminderCode(obj.code).name
        return obj


@dataclass
class ThermostatAlarm(DataClassORJSONMixin):
    """Model for thermostat alarm."""

    code: int
    enabled: bool
    code_name: str | None = None
    aux_runtime_limit: int | None = field(
        default=None, metadata=field_options(alias='auxRunTimeLimit')
    )

    @classmethod
    def __post_deserialize__(  # type: ignore[override]
        cls, obj: ThermostatAlarm
    ) -> ThermostatAlarm:
        """Post-deserialization processing."""
        if obj.code is not None:
            obj.code_name = ThermostatConst.AlarmCode(obj.code).name
        return obj
