"""Base classes for thermostat devices."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseDevice, DeviceState
from pyvesync.const import (
    ThermostatConst,
    ThermostatWorkModes,
    ThermostatFanModes,
    ThermostatHoldOptions,
    ThermostatScheduleOrHoldOptions,
    ThermostatEcoTypes,
    ThermostatWorkStatusCodes,
    ThermostatFanStatus,
    )

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
    from pyvesync.models.thermostat_models import (
        ThermostatMinorDetails,
        ThermostatSimpleRoutine,
    )
    from pyvesync.device_map import ThermostatMap


_LOGGER = logging.getLogger(__name__)


class ThermostatState(DeviceState):
    """VeSync Thermostat State.

    Args:
        device (VeSyncThermostat): The thermostat device.
        details (ResponseDeviceDetailsModel): The thermostat device details.
        feature_map (ThermostatMap): The thermostat feature map.
    """
    __slots__ = (
        "alert_status",
        "configuration",
        "cool_to_temp",
        "deadband",
        "device_config",
        "eco_type",
        "fan_mode",
        "fan_status",
        "heat_to_temp",
        "hold_end_time",
        "hold_option",
        "humidity",
        "lock_status",
        "mode",
        "routine_running_id",
        "routines",
        "schedule_or_hold",
        "temperature",
        "temperature_unit",
        "work_mode",
        "work_status",
    )

    def __init__(
        self,
        device: VeSyncThermostat,
        details: ResponseDeviceDetailsModel,
        feature_map: ThermostatMap,
    ) -> None:
        """Initialize VeSync Thermostat State."""
        super().__init__(device, details, feature_map)
        self.device: VeSyncThermostat = device
        self.configuration: ThermostatMinorDetails | None = None
        self.work_mode: ThermostatWorkModes | None = None
        self.work_status: ThermostatWorkStatusCodes | None = None
        self.fan_mode: ThermostatFanModes | None = None
        self.fan_status: ThermostatFanStatus | None = None
        self.temperature_unit: str | None = None
        self.temperature: float | None = None
        self.humidity: int | None = None
        self.heat_to_temp: int | None = None
        self.cool_to_temp: int | None = None
        self.lock_status: bool = False
        self.schedule_or_hold: ThermostatScheduleOrHoldOptions | None = None
        self.hold_end_time: int | None = None
        self.hold_option: ThermostatHoldOptions | None = None
        self.deadband: int | None = None
        self.eco_type: ThermostatEcoTypes | None = None
        self.alert_status: int | None = None
        self.routines: list[ThermostatSimpleRoutine] = []
        self.routine_running_id: int | None = None

    @property
    def is_running(self) -> bool:
        """Check if the thermostat is running."""
        return self.work_status != ThermostatWorkStatusCodes.OFF

    @property
    def is_heating(self) -> bool:
        """Check if the thermostat is heating."""
        return self.work_status == ThermostatWorkStatusCodes.HEATING

    @property
    def is_cooling(self) -> bool:
        """Check if the thermostat is cooling."""
        return self.work_status == ThermostatWorkStatusCodes.COOLING

    @property
    def is_fan_on(self) -> bool:
        """Check if the fan is on."""
        return self.fan_status == ThermostatFanStatus.ON


class VeSyncThermostat(VeSyncBaseDevice):
    """Base class for VeSync Thermostat devices.

    Args:
        details (ResponseDeviceDetailsModel): The thermostat device details.
        manager (VeSync): The VeSync manager instance.
        feature_map (ThermostatMap): The thermostat feature map.
    """

    __slots__ = ("eco_types", "fan_modes", "hold_options", "work_modes")

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: ThermostatMap,
    ) -> None:
        """Initialize VeSync Thermostat."""
        super().__init__(details, manager, feature_map)
        self.state: ThermostatState = ThermostatState(self, details, feature_map)
        self.fan_modes = feature_map.fan_modes
        self.work_modes = feature_map.modes
        self.eco_types = feature_map.eco_types
        self.hold_options = feature_map.hold_options

    async def set_mode(self, mode: ThermostatWorkModes) -> bool:
        """Set the thermostat mode."""
        del mode  # Unused
        _LOGGER.debug("set mode not implemented for %s", self.device_type)
        return False

    async def turn_off(self) -> bool:
        """Set mode to off."""
        return await self.set_mode(ThermostatWorkModes.OFF)

    async def set_mode_cool(self) -> bool:
        """Set mode to cool."""
        return await self.set_mode(ThermostatWorkModes.COOL)

    async def set_mode_heat(self) -> bool:
        """Set mode to heat."""
        return await self.set_mode(ThermostatWorkModes.HEAT)

    async def set_mode_auto(self) -> bool:
        """Set mode to auto."""
        return await self.set_mode(ThermostatWorkModes.AUTO)

    async def set_mode_smart_auto(self) -> bool:
        """Set mode to smart auto."""
        return await self.set_mode(ThermostatWorkModes.SMART_AUTO)

    async def set_mode_emergency_heat(self) -> bool:
        """Set mode to emergency heat."""
        return await self.set_mode(ThermostatWorkModes.EM_HEAT)

    async def set_fan_mode(self, mode: ThermostatFanModes) -> bool:
        """Set thermostat fan mode."""
        del mode
        _LOGGER.debug("set fan mode not implemented for %s", self.device_type)
        return False

    async def set_fan_ciruclate(self) -> bool:
        """Set fan circulate."""
        return await self.set_fan_mode(ThermostatConst.FanMode.CIRCULATE)

    async def set_fan_auto(self) -> bool:
        """Set fan auto."""
        return await self.set_fan_mode(ThermostatConst.FanMode.AUTO)

    async def set_fan_on(self) -> bool:
        """Set fan on."""
        return await self.set_fan_mode(ThermostatConst.FanMode.ON)
