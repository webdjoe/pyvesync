"""Air Purifier Base Class."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from pyvesync.base_devices.vesyncbasedevice import DeviceState, VeSyncBaseDevice
from pyvesync.const import (
    AIRFRYER_PID_MAP,
    AirFryerCookStatus,
    AirFryerFeatures,
    AirFryerPresetRecipe,
    TemperatureUnits,
    TimeUnits,
)

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import AirFryerMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel


logger = logging.getLogger(__name__)


class FryerState(DeviceState):
    """State class for Air Fryer devices.

    Time units are in seconds by default. They are automatically converted
    from the API response.
    """

    __slots__ = (
        '_time_conv',
        'cook_last_time',
        'cook_mode',
        'cook_set_temp',
        'cook_set_time',
        'cook_status',
        'current_temp',
        'last_timestamp',
        'preheat_last_time',
        'preheat_set_time',
        'ready_start',
        'time_units',
    )

    def __init__(
        self,
        device: VeSyncFryer,
        details: ResponseDeviceDetailsModel,
        feature_map: AirFryerMap,
    ) -> None:
        """Initialize FryerState.

        Args:
            device (VeSyncFryer): The device object.
            details (ResponseDeviceDetailsModel): The device details.
            feature_map (AirFryerMap): The feature map for the device.

        """
        super().__init__(device, details, feature_map)
        self.device: VeSyncFryer = device
        self.features: list[str] = feature_map.features
        self.time_units: TimeUnits = feature_map.time_units
        self.ready_start: bool = False
        self.cook_status: str | None = None
        self.cook_mode: str | None = None
        self.current_temp: int | None = None
        self.cook_set_temp: int | None = None
        self.cook_set_time: int | None = None
        self.cook_last_time: int | None = None
        self.last_timestamp: int | None = None
        self.preheat_set_time: int | None = None
        self.preheat_last_time: int | None = None
        self._time_conv: float = (
            60 if feature_map.time_units == TimeUnits.MINUTES else 1
        )

    @property
    def is_in_preheat_mode(self) -> bool:
        """Return True if the fryer has preheat feature."""
        return self.cook_status in [
            AirFryerCookStatus.HEATING,
            AirFryerCookStatus.PREHEAT_STOP,
        ] or (
            self.cook_status == AirFryerCookStatus.PULL_OUT
            and self.preheat_set_time is not None
        )

    @property
    def is_in_cook_mode(self) -> bool:
        """Return True if the fryer is in cook mode."""
        return self.cook_status in [
            AirFryerCookStatus.COOKING,
            AirFryerCookStatus.COOK_STOP,
        ] or (
            self.cook_status == AirFryerCookStatus.PULL_OUT
            and self.cook_set_time is not None
        )

    @property
    def is_cooking(self) -> bool:
        """Return True if the fryer is currently cooking (not preheating)."""
        return self.cook_status == AirFryerCookStatus.COOKING

    @property
    def is_preheating(self) -> bool:
        """Return True if the fryer is currently preheating."""
        return self.cook_status == AirFryerCookStatus.HEATING

    @property
    def is_running(self) -> bool:
        """Return True if the fryer is running (cooking or preheating)."""
        return self.is_cooking or self.is_preheating

    @property
    def can_resume(self) -> bool:
        """Return True if the fryer can resume cooking."""
        return self.cook_status in [
            AirFryerCookStatus.PREHEAT_STOP,
            AirFryerCookStatus.COOK_STOP,
        ]

    @property
    def preheat_time_remaining(self) -> int | None:
        """Return the remaining preheat time in seconds."""
        if not self.is_in_preheat_mode:
            return None
        if self.cook_status in [
            AirFryerCookStatus.PREHEAT_STOP,
            AirFryerCookStatus.PULL_OUT,
        ]:
            return self.preheat_last_time
        if self.preheat_last_time is not None and self.last_timestamp is not None:
            return max(
                0,
                self.preheat_last_time
                - int((self.last_timestamp - time.time()) * self._time_conv),
            )
        return None

    @property
    def cook_time_remaining(self) -> int | None:
        """Return the remaining cook time in seconds."""
        if not self.is_in_cook_mode:
            return None
        if self.cook_status in [
            AirFryerCookStatus.PULL_OUT,
            AirFryerCookStatus.COOK_STOP,
        ]:
            return self.cook_last_time

        if self.cook_last_time is not None and self.last_timestamp is not None:
            return max(
                0,
                self.cook_last_time
                - int((self.last_timestamp - time.time()) * self._time_conv),
            )
        return None

    def _clear_preheat(self) -> None:
        """Clear preheat status."""
        self.preheat_set_time = None
        self.preheat_last_time = None

    def set_standby(self) -> None:
        """Set the fryer state to standby and clear all state attributes.

        This is to be called by device classes before updating the state from
        the API response to prevent stale data. The get_details API responses
        do not include all keys in every response depending on the status.
        """
        self.cook_status = AirFryerCookStatus.STANDBY
        self.current_temp = None
        self.cook_set_temp = None
        self.cook_set_time = None
        self.cook_last_time = None
        self.last_timestamp = None
        self._clear_preheat()

    def set_state(  # noqa: PLR0913, C901
        self,
        *,
        cook_status: str,
        cook_time: int | None = None,
        cook_last_time: int | None = None,
        cook_temp: int | None = None,
        temp_unit: str | None = None,
        cook_mode: str | None = None,
        preheat_time: int | None = None,
        preheat_last_time: int | None = None,
        current_temp: int | None = None,
    ) -> None:
        """Set the cook state parameters.

        Args:
            cook_status (str): The cooking status.
            cook_time (int | None): The cooking time in seconds.
            cook_last_time (int | None): The last cooking time in seconds.
            cook_temp (int | None): The cooking temperature.
            temp_unit (str | None): The temperature units (F or C).
            cook_mode (str | None): The cooking mode.
            preheat_time (int | None): The preheating time in seconds.
            preheat_last_time (int | None): The remaining preheat time in seconds.
            current_temp (int | None): The current temperature.
        """
        if cook_status == AirFryerCookStatus.STANDBY:
            self.set_standby()
            return

        self.preheat_set_time = preheat_time
        self.preheat_last_time = preheat_last_time

        if cook_status is not None:
            self.cook_status = AirFryerCookStatus(cook_status)
        if cook_time is not None:
            self.cook_set_time = cook_time
        if cook_temp is not None:
            self.cook_set_temp = cook_temp
        if cook_mode is not None:
            self.cook_mode = cook_mode
        if current_temp is not None:
            self.current_temp = current_temp
        if temp_unit is not None:
            self.device.temp_unit = TemperatureUnits.from_string(temp_unit)
        if preheat_time is not None:
            self.preheat_set_time = preheat_time
        if cook_last_time is not None:
            self.cook_last_time = cook_last_time
        if cook_status in [
            AirFryerCookStatus.COOKING,
            AirFryerCookStatus.HEATING,
        ]:
            self.last_timestamp = int(time.time())


class VeSyncFryer(VeSyncBaseDevice):
    """Base class for VeSync Air Fryer devices."""

    __slots__ = (
        '_temp_unit',
        'cook_modes',
        'default_preset',
        'max_temp_c',
        'max_temp_f',
        'min_temp_c',
        'min_temp_f',
        'state_chamber_1',
        'state_chamber_2',
        'sync_chambers',
        'temperature_interval',
        'time_units',
    )

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: AirFryerMap,
    ) -> None:
        """Initialize VeSyncFryer.

        Args:
            details (ResponseDeviceDetailsModel): The device details.
            manager (VeSync): The VeSync manager.
            feature_map (AirFryerMap): The feature map for the device.

        Note:
            This is a bare class as there is only one supported air fryer model.
        """
        super().__init__(details, manager, feature_map)
        self.cook_modes: dict[str, str] = feature_map.cook_modes
        self.pid: str | None = AIRFRYER_PID_MAP.get(details.deviceType, None)
        self.default_preset: AirFryerPresetRecipe = feature_map.default_preset
        self.state_chamber_1: FryerState = FryerState(self, details, feature_map)
        self.state_chamber_2: FryerState = FryerState(self, details, feature_map)
        self.sync_chambers: bool = False
        self.min_temp_f: int = feature_map.temperature_range_f[0]
        self.max_temp_f: int = feature_map.temperature_range_f[1]
        self.min_temp_c: int = feature_map.temperature_range_c[0]
        self.max_temp_c: int = feature_map.temperature_range_c[1]
        self.temperature_interval: int = feature_map.temperature_step_f
        self.time_units: TimeUnits = feature_map.time_units

        # attempt to set temp unit from country code before first update
        self._temp_unit: TemperatureUnits = TemperatureUnits.CELSIUS
        if self.manager.measure_unit and self.manager.measure_unit.lower() == 'imperial':
            self._temp_unit = TemperatureUnits.FAHRENHEIT

        # Use single state attribute if not dual chamber fryer for compatibility
        if AirFryerFeatures.DUAL_CHAMBER not in self.features:
            self.state = self.state_chamber_1

    @property
    def temp_unit(self) -> TemperatureUnits:
        """Return the temperature unit (F or C)."""
        return self._temp_unit

    @temp_unit.setter
    def temp_unit(self, value: TemperatureUnits) -> None:
        """Set the temperature unit.

        Args:
            value (TemperatureUnits): The temperature unit (F or C).
        """
        self._temp_unit = TemperatureUnits.from_string(value)

    def validate_temperature(self, temperature: int) -> bool:
        """Validate the temperature is within the allowed range.

        Args:
            temperature (int): The temperature to validate.

        Returns:
            bool: True if the temperature is valid, False otherwise.
        """
        if self.temp_unit == TemperatureUnits.FAHRENHEIT:
            return self.min_temp_f <= temperature <= self.max_temp_f
        return self.min_temp_c <= temperature <= self.max_temp_c

    def round_temperature(self, temperature: int) -> int:
        """Round the temperature to the nearest valid step.

        Args:
            temperature (int): The temperature to round.

        Returns:
            int: The rounded temperature.
        """
        if self.temp_unit == TemperatureUnits.FAHRENHEIT:
            step: float = self.temperature_interval
            return int(round(temperature / step) * step)
        step = self.temperature_interval * 5 / 9
        return int(round(temperature / step) * step)

    def convert_time(self, time_in_seconds: int) -> int:
        """Convert time in seconds to the device's time units.

        Args:
            time_in_seconds (int): The time in seconds.

        Returns:
            int: The time converted to the device's time units.
        """
        if self.time_units == TimeUnits.MINUTES:
            return int(time_in_seconds / 60)
        return time_in_seconds

    async def end(self, chamber: int = 1) -> bool:
        """End the current cooking or preheating session.

        Arguments:
            chamber (int): The chamber number to end for. Default is 1.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        del chamber
        logger.info('end not configured for this fryer.')
        return False

    async def stop(self, chamber: int = 1) -> bool:
        """Stop (Pause) the current cooking or preheating session.

        Arguments:
            chamber (int): The chamber number to stop for. Default is 1.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        del chamber
        logger.info('stop not supported by this fryer.')
        return False

    async def resume(self, chamber: int = 1) -> bool:
        """Resume a paused cooking or preheating session.

        Arguments:
            chamber (int): The chamber number to resume for. Default is 1.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        del chamber
        logger.info('resume not supported by this fryer.')
        return False

    async def set_mode(
        self,
        cook_time: int,
        cook_temp: int,
        *,
        preheat_time: int | None = None,
        chamber: int = 1,
    ) -> bool:
        """Set the cooking mode.

        Args:
            cook_time (int): The cooking time in seconds.
            cook_temp (int): The cooking temperature.
            preheat_time (int | None): The preheating time in seconds, if any.
            chamber (int): The chamber number to set cooking for. Default is 1.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        del cook_time, cook_temp, chamber, preheat_time
        logger.warning('set_mode method not implemented for base fryer class.')
        return False

    async def set_mode_from_recipe(
        self,
        recipe: AirFryerPresetRecipe,
    ) -> bool:
        """Set the cooking mode from a preset recipe.

        Args:
            recipe (AirFryerPresetRecipe): The preset recipe to use.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        del recipe
        logger.warning(
            'set_mode_from_recipe method not implemented for base fryer class.'
        )
        return False

    async def cook_from_preheat(self, chamber: int = 1) -> bool:
        """Start cooking after preheating, cookStatus must be preheatEnd.

        Args:
            chamber (int): The chamber number to start cooking for. Default is 1.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        del chamber
        if AirFryerFeatures.PREHEAT not in self.features:
            logger.info('Preheat feature not supported on this fryer.')
            return False
        logger.info('cook_from_preheat not configured for this fryer.')
        return False
