"""Thermostat device classes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyvesync.base_devices.thermostat_base import VeSyncThermostat
from pyvesync.const import (
    ThermostatConst,
    ThermostatEcoTypes,
    ThermostatFanModes,
    ThermostatHoldStatus,
    ThermostatWorkModes,
)
from pyvesync.models.thermostat_models import (
    ResultThermostatDetails,
    ThermostatMinorDetails,
)
from pyvesync.utils.device_mixins import BypassV2Mixin, process_bypassv2_result
from pyvesync.utils.helpers import Helpers, Validators

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import ThermostatMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel

_LOGGER = logging.getLogger(__name__)


class VeSyncAuraThermostat(BypassV2Mixin, VeSyncThermostat):
    """VeSync Aura Thermostat."""

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: ThermostatMap,
    ) -> None:
        """Initialize VeSync Aura Thermostat."""
        super().__init__(details, manager, feature_map)

    def _process_details(self, details: ResultThermostatDetails) -> None:
        """Internal method to process thermostat details."""
        if ResultThermostatDetails.supportMode is not None:
            self.supported_work_modes = [
                ThermostatWorkModes(mode) for mode in ResultThermostatDetails.supportMode
            ]
        self.state.work_mode = ThermostatConst.WorkMode(details.workMode)
        self.state.work_status = ThermostatConst.WorkStatus(details.workStatus)
        self.state.fan_status = ThermostatConst.FanStatus(details.fanStatus)
        self.state.fan_mode = ThermostatConst.FanMode(details.fanMode)
        self.state.temperature_unit = details.tempUnit
        self.state.temperature = details.temperature
        self.state.humidity = details.humidity
        self.state.heat_to_temp = details.heatToTemp
        self.state.cool_to_temp = details.coolToTemp
        self.state.deadband = details.deadband
        self.state.lock_status = details.lockStatus
        self.state.schedule_or_hold = ThermostatConst.ScheduleOrHoldOption(
            details.scheduleOrHold
        )
        self.state.hold_end_time = details.holdEndTime
        self.state.hold_option = ThermostatConst.HoldOption(details.holdOption)
        self.state.eco_type = ThermostatConst.EcoType(details.ecoType)
        self.state.alert_status = details.alertStatus
        self.state.routine_running_id = details.routineRunningId
        self.state.routines = details.routines

    async def get_details(self) -> None:
        """Get the details of the thermostat."""
        r_dict = await self.call_bypassv2_api('getTsStatus')
        r_model = process_bypassv2_result(
            self, _LOGGER, 'get_details', r_dict, ResultThermostatDetails
        )
        if r_model is None:
            return
        self._process_details(r_model)

    async def get_configuration(self) -> None:
        """Get configuration or 'minor details'."""
        r_dict = await self.call_bypassv2_api('getTsMinorInfo')
        result = process_bypassv2_result(
            self, _LOGGER, 'get_configuration', r_dict, ThermostatMinorDetails
        )
        if result is None:
            return
        self.state.configuration = result

    async def _set_hold_status_api(
        self,
        key: str | None = None,
        temp: float | None = None,
        hold_status: ThermostatHoldStatus | None = None,
    ) -> bool:
        """Internal function to call the 'setHoldStatus' API."""
        if key is None and temp is None and hold_status is None:
            _LOGGER.debug('At least one of key, temp, or hold_status must be provided.')
            return False
        payload_data: dict[str, str | float] = {}
        if hold_status is not None and hold_status.value == ThermostatHoldStatus.CANCEL:
            payload_data = {'holdStatus': ThermostatHoldStatus.CANCEL}
        else:
            if key is None or temp is None:
                _LOGGER.debug('Either key or temp must be provided.')
                return False
            payload_data = {key: temp, 'holdStatus': ThermostatHoldStatus.SET.value}
        r_dict = await self.call_bypassv2_api('setHoldStatus', data=payload_data)
        result = Helpers.process_dev_response(_LOGGER, 'setHoldStatus', self, r_dict)
        return bool(result)

    async def set_temp_point(self, temperature: float) -> bool:
        return await self._set_hold_status_api('setTempPoint', temperature)

    async def cancel_hold(self) -> bool:
        """Cancel hold."""
        return await self._set_hold_status_api(hold_status=ThermostatHoldStatus.CANCEL)

    async def set_cool_to_temp(self, temperature: float) -> bool:
        """Set cool to temperature."""
        return await self._set_hold_status_api('coolToTemp', temperature)

    async def set_heat_to_temp(self, temperature: float) -> bool:
        """Set heat to temperature."""
        return await self._set_hold_status_api('heatToTemp', temperature)

    async def set_mode(self, mode: ThermostatWorkModes) -> bool:
        """Set thermostat mode."""
        if mode not in self.supported_work_modes:
            _LOGGER.debug('Invalid mode: %s', mode)
            return False
        payload_data = {'tsMode': mode}
        r_dict = await self.call_bypassv2_api('setTsMode', data=payload_data)
        result = Helpers.process_dev_response(_LOGGER, 'setTsMode', self, r_dict)
        return bool(result)

    async def set_fan_mode(self, mode: ThermostatFanModes) -> bool:
        """Set thermostat fan mode."""
        if mode not in self.fan_modes:
            _LOGGER.debug('Invalid fan mode: %s', mode)
            return False
        payload_data = {'fanMode': mode.value}
        r_dict = await self.call_bypassv2_api('setFanMode', data=payload_data)
        result = Helpers.process_dev_response(_LOGGER, 'setFanMode', self, r_dict)
        return bool(result)

    async def toggle_lock(self, toggle: bool, pin: int | str | None = None) -> bool:
        """Toggle thermostat lock status."""
        if toggle is True and pin is None:
            _LOGGER.debug('PIN required to lock the thermostat.')
            return False
        payload_data: dict[str, bool | str] = {'lockStatus': toggle}
        if toggle is True:
            pin_int = int(pin) if isinstance(pin, str) else pin
            if not Validators.validate_range(pin_int, 0, 9999):
                _LOGGER.debug('PIN must be between 0 and 9999.')
                return False
            payload_data['lockPinCode'] = f'{pin_int:0>4}'
        r_dict = await self.call_bypassv2_api('setLockStatus', data=payload_data)
        result = Helpers.process_dev_response(_LOGGER, 'toggle_lock_status', self, r_dict)
        return bool(result)

    async def set_eco_type(self, eco_type: ThermostatEcoTypes) -> bool:
        """Set thermostat eco type."""
        if eco_type not in self.eco_types:
            _LOGGER.debug('Invalid eco type: %s', eco_type)
            return False
        payload_data = {'ecoType': eco_type.value}
        r_dict = await self.call_bypassv2_api('setECOType', data=payload_data)
        result = Helpers.process_dev_response(_LOGGER, 'setEcoType', self, r_dict)
        return bool(result)
