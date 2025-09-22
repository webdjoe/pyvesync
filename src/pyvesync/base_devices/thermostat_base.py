"""Base classes for thermostat devices."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyvesync.base_devices.vesyncbasedevice import DeviceState, VeSyncBaseDevice
from pyvesync.const import (
    ThermostatConst,
    ThermostatEcoTypes,
    ThermostatFanModes,
    ThermostatFanStatus,
    ThermostatHoldOptions,
    ThermostatScheduleOrHoldOptions,
    ThermostatWorkModes,
    ThermostatWorkStatusCodes,
)

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import ThermostatMap
    from pyvesync.models.thermostat_models import (
        ThermostatMinorDetails,
        ThermostatSimpleRoutine,
    )
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel


_LOGGER = logging.getLogger(__name__)


class ThermostatState(DeviceState):
    """VeSync Thermostat State.

    Args:
        device (VeSyncThermostat): The thermostat device.
        details (ResponseDeviceDetailsModel): The thermostat device details.
        feature_map (ThermostatMap): The thermostat feature map.
    """

    __slots__ = (
        'alert_status',
        'battery_level',
        'configuration',
        'cool_to_temp',
        'deadband',
        'device_config',
        'eco_type',
        'fan_mode',
        'fan_status',
        'filter_life',
        'heat_to_temp',
        'hold_end_time',
        'hold_option',
        'humidity',
        'lock_status',
        'mode',
        'routine_running_id',
        'routines',
        'schedule_or_hold',
        'temperature',
        'temperature_unit',
        'work_mode',
        'work_status',
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
        self.battery_level: int | None = None
        self.filter_life: int | None = None

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

    __slots__ = ('eco_types', 'fan_modes', 'hold_options', 'supported_work_modes')

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
        self.supported_work_modes = feature_map.modes
        self.eco_types = feature_map.eco_types
        self.hold_options = feature_map.hold_options

    async def set_mode(self, mode: ThermostatWorkModes) -> bool:
        """Set the thermostat mode."""
        del mode  # Unused
        _LOGGER.debug('set mode not implemented for %s', self.device_type)
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
        _LOGGER.debug('set fan mode not implemented for %s', self.device_type)
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

    async def get_configuration(self) -> None:
        """Retrieve configuration from API."""
        _LOGGER.debug('get configuration not implemented for %s', self.device_type)

    async def set_temp_point(self, temperature: float) -> bool:
        """Set the temperature point."""
        del temperature
        _LOGGER.debug('set temp point not implemented for %s', self.device_type)
        return False

    async def cancel_hold(self) -> bool:
        """Cancel the scheduled hold."""
        _LOGGER.debug('cancel hold not implemented for %s', self.device_type)
        return False

    async def set_cool_to_temp(self, temperature: float) -> bool:
        """Set the cool to temperature.

        Args:
            temperature (float): The cool to temperature.

        Returns:
            bool: True if successful, False otherwise.
        """
        del temperature
        _LOGGER.debug('set cool to temp not implemented for %s', self.device_type)
        return False

    async def set_heat_to_temp(self, temperature: float) -> bool:
        """Set the heat to temperature.

        Args:
            temperature (float): The heat to temperature.

        Returns:
            bool: True if successful, False otherwise.
        """
        del temperature
        _LOGGER.debug('set heat to temp not implemented for %s', self.device_type)
        return False

    async def toggle_lock(self, toggle: bool, pin: int | str | None = None) -> bool:
        """Toggle the thermostat lock status."""
        del toggle, pin
        _LOGGER.debug('toggle lock not implemented for %s', self.device_type)
        return False

    async def turn_on_lock(self, pin: int | str) -> bool:
        """Turn on the thermostat lock.

        Args:
            pin (int | str): The 4-digit PIN code.
        """
        return await self.toggle_lock(True, pin)

    async def turn_off_lock(self) -> bool:
        """Turn off the thermostat lock."""
        return await self.toggle_lock(False)

    async def set_eco_type(self, eco_type: ThermostatEcoTypes) -> bool:
        """Set thermostat eco type.

        Args:
            eco_type (ThermostatEcoTypes): The eco type to set, options are found in
                self.eco_types.

        Returns:
            bool: True if successful, False otherwise.
        """
        del eco_type
        if not self.eco_types:
            _LOGGER.debug('No eco types available for %s', self.device_type)
        else:
            _LOGGER.debug('set_eco_type not configured for %s', self.device_name)
        return False

    async def set_eco_first(self) -> bool:
        """Set eco first."""
        return await self.set_eco_type(ThermostatEcoTypes.ECO_FIRST)

    async def set_eco_second(self) -> bool:
        """Set eco second."""
        return await self.set_eco_type(ThermostatEcoTypes.ECO_SECOND)

    async def set_eco_comfort_first(self) -> bool:
        """Set eco comfort."""
        return await self.set_eco_type(ThermostatEcoTypes.COMFORT_FIRST)

    async def set_eco_comfort_second(self) -> bool:
        """Set eco comfort."""
        return await self.set_eco_type(ThermostatEcoTypes.COMFORT_SECOND)
