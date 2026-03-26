"""Air Fryer Base Class."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pyvesync.base_devices.vesyncbasedevice import DeviceState, VeSyncBaseDevice
from pyvesync.const import (
    AIRFRYER_PID_MAP,
    COOK_STATUSES,
    PREHEAT_STATUSES,
    RESUMABLE_STATUSES,
    RUNNING_STATUSES,
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

    Each FryerState instance represents a single cooking chamber. For single
    chamber fryers, ``state`` is set to ``state_chamber_1``. For dual chamber
    fryers, ``state_chamber_1`` and ``state_chamber_2`` are used independently.

    Time units are in SECONDS. They are automatically converted from the API
    response via the device's ``convert_time_for_state`` method. The
    ``last_timestamp`` attribute is set when the fryer enters a running state
    (cooking or heating) and is used to calculate remaining time.

    Args:
        device (VeSyncFryer): The device object.
        details (ResponseDeviceDetailsModel): The device details.
        feature_map (AirFryerMap): The feature map for the device.

    Attributes:
        active_time (int): Active time of device, defaults to None.
        connection_status (str): Connection status of device.
        device (VeSyncFryer): Device object.
        device_status (str): Device status.
        features (dict): Features of device.
        time_units (TimeUnits): The time units used by the device.
        cook_status (AirFryerCookStatus | None): The current cooking status.
        cook_mode (str | None): The current cooking mode.
        current_temp (int | None): The current temperature of the fryer.
        cook_set_temp (int | None): The set cooking temperature.
        cook_set_time (int | None): The set cooking time in seconds.
        cook_last_time (int | None): The remaining cooking time in seconds.
        last_timestamp (datetime | None): The timestamp of the last status update.
        preheat_set_time (int | None): The set preheating time in seconds.
        preheat_last_time (int | None): The remaining preheating time in seconds.
        recipe (str | None): The current recipe or cooking mode.
        ready_start (bool): Whether the fryer is ready to start cooking.

    Note:
        Use convenience state methods like ``set_standby``, ``set_cook_stop_state``,
        ``set_preheat_stop_state``, and ``set_preheat_resume_state`` to set the
        state attributes when changing cooking states. The ``set_state`` method
        can be used to set all state attributes at once when updating from the API
        response. The ``last_timestamp`` attribute will be automatically updated
        when setting a running state (cooking or heating).
    """

    __slots__ = (
        '_cook_status',
        'cook_last_time',
        'cook_mode',
        'cook_set_temp',
        'cook_set_time',
        'current_temp',
        'last_timestamp',
        'preheat_last_time',
        'preheat_set_time',
        'ready_start',
        'recipe',
        'sync_chambers',
        'time_units',
    )

    def __init__(
        self,
        device: VeSyncFryer,
        details: ResponseDeviceDetailsModel,
        feature_map: AirFryerMap,
    ) -> None:
        """Initialize FryerState."""
        super().__init__(device, details, feature_map)
        self.device: VeSyncFryer = device
        self.features: list[str] = feature_map.features
        self.time_units: TimeUnits = feature_map.time_units
        self.sync_chambers: bool = False
        # Cooking state attributes
        self._cook_status: AirFryerCookStatus | None = None
        self.current_temp: int | None = None
        self.cook_mode: str | None = None
        self.cook_set_temp: int | None = None
        self.cook_set_time: int | None = None
        self.cook_last_time: int | None = None
        self.preheat_set_time: int | None = None
        self.preheat_last_time: int | None = None
        self.last_timestamp: datetime | None = None
        self.recipe: str | None = None
        self.ready_start: bool = False

    @property
    def is_in_preheat_mode(self) -> bool:
        """Return True if the fryer has preheat feature."""
        return self.cook_status in PREHEAT_STATUSES or (
            self.cook_status == AirFryerCookStatus.PULL_OUT
            and self.preheat_set_time is not None
        )

    @property
    def is_in_cook_mode(self) -> bool:
        """Return True if the fryer is in cook mode."""
        return self.cook_status in COOK_STATUSES or (
            self.cook_status == AirFryerCookStatus.PULL_OUT
            and self.preheat_last_time is None
        )

    @property
    def is_cooking(self) -> bool:
        """Return True if the fryer is currently running in cook mode."""
        return self.cook_status == AirFryerCookStatus.COOKING

    @property
    def is_preheating(self) -> bool:
        """Return True if the fryer is currently running in preheat mode."""
        return self.cook_status == AirFryerCookStatus.HEATING

    @property
    def is_running(self) -> bool:
        """Return True if the fryer is running (cooking or preheating)."""
        return self.is_cooking or self.is_preheating

    @property
    def can_resume(self) -> bool:
        """Return True if the fryer can resume cooking."""
        return self.cook_status in RESUMABLE_STATUSES

    @property
    def cook_status(self) -> AirFryerCookStatus | None:
        """Return the current cooking status."""
        return self._cook_status

    @cook_status.setter
    def cook_status(self, value: AirFryerCookStatus | None) -> None:
        """Set the current cooking status.

        Automatically updates ``last_timestamp`` when setting a running state.

        Args:
            value (AirFryerCookStatus | None): The cooking status to set.
        """
        if value in RUNNING_STATUSES:
            self.last_timestamp = datetime.now(tz=timezone.utc)
        self._cook_status = value

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
                - int((datetime.now(timezone.utc) - self.last_timestamp).total_seconds()),
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
                - int((datetime.now(timezone.utc) - self.last_timestamp).total_seconds()),
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
        self.recipe = None
        self._clear_preheat()

    def set_cook_stop_state(self, cook_set_time: int | None = None) -> None:
        """Set the fryer state to cook stopped.

        Args:
            cook_set_time (int | None): The cooking time in seconds.
        """
        self._clear_preheat()
        self.cook_status = AirFryerCookStatus.COOK_STOP
        if cook_set_time is not None:
            self.cook_set_time = cook_set_time
        self.cook_last_time = self.cook_time_remaining
        self.last_timestamp = None

    def set_preheat_stop_state(self, preheat_set_time: int | None = None) -> None:
        """Set the fryer state to preheat stopped."""
        self.cook_status = AirFryerCookStatus.PREHEAT_STOP
        if preheat_set_time is not None:
            self.preheat_set_time = self.device.convert_time_for_state(preheat_set_time)
        self.preheat_last_time = self.preheat_time_remaining
        self.last_timestamp = None

    def set_preheat_resume_state(self, preheat_set_time: int | None = None) -> None:
        """Set the fryer state to preheat resumed."""
        self.cook_status = AirFryerCookStatus.HEATING
        if preheat_set_time is not None:
            self.preheat_set_time = self.device.convert_time_for_state(preheat_set_time)
        self.preheat_last_time = self.preheat_time_remaining
        self.last_timestamp = datetime.now(timezone.utc)

    def set_cooking_state(
        self, *, recipe: str, cook_set_time: int, cook_temp: int, cook_mode: str
    ) -> None:
        """Set the fryer state to cooking.

        Args:
            recipe (str): The recipe name or cooking mode.
            cook_set_time (int): The cooking time in device units.
            cook_temp (int): The cooking temperature.
            cook_mode (str): The cooking mode.
        """
        self._clear_preheat()
        self.cook_status = AirFryerCookStatus.COOKING
        self.recipe = recipe
        self.cook_set_time = self.device.convert_time_for_state(cook_set_time)
        self.cook_last_time = self.cook_set_time
        self.cook_set_temp = cook_temp
        self.cook_mode = cook_mode

    def set_preheating_state(
        self,
        *,
        recipe: str,
        cook_temp: int,
        cook_mode: str,
        preheat_set_time: int | None = None,
    ) -> None:
        """Set the fryer state to preheating.

        Args:
            recipe (str): The recipe name or cooking mode.
            preheat_set_time (int | None): The preheating time in device units.
            cook_temp (int): The cooking temperature.
            cook_mode (str): The cooking mode.
        """
        self.cook_status = AirFryerCookStatus.HEATING
        self.preheat_set_time = self.device.convert_time_for_state(
            preheat_set_time or 300
        )
        self.preheat_last_time = self.preheat_set_time
        self.cook_set_temp = cook_temp
        self.cook_mode = cook_mode
        self.recipe = recipe

    def set_state(  # noqa: PLR0912, PLR0913, C901
        self,
        *,
        cook_status: AirFryerCookStatus,
        cook_time: int | None = None,
        cook_last_time: int | None = None,
        cook_temp: int | None = None,
        temp_unit: str | None = None,
        cook_mode: str | None = None,
        preheat_set_time: int | None = None,
        preheat_last_time: int | None = None,
        current_temp: int | None = None,
        recipe: str | None = None,
    ) -> None:
        """Set the cook state parameters from an API response or action.

        All parameters that are part of the current cook state must be passed.
        This should be primarily used when updating from the API response to
        ensure all state attributes are updated together. If updating state
        from a user action, use the specific state methods like ``set_standby``,
        ``set_cook_stop_state``, ``set_cooking_state``, etc.

        Time values are expected in device units and will be converted to
        seconds automatically.

        Args:
            cook_status (AirFryerCookStatus): The cooking status.
            cook_time (int | None): The cooking time in device units.
            cook_last_time (int | None): The remaining cooking time in device units.
            cook_temp (int | None): The cooking temperature.
            temp_unit (str | None): The temperature units (F or C).
            cook_mode (str | None): The cooking mode.
            preheat_set_time (int | None): The preheating time in device units.
            preheat_last_time (int | None): The remaining preheat time in device units.
            current_temp (int | None): The current temperature.
            recipe (str | None): The recipe name or cooking mode.
        """
        # Stop/standby states delegate to helpers and return early
        if cook_status == AirFryerCookStatus.STANDBY:
            self.set_standby()
            return

        if cook_status == AirFryerCookStatus.COOK_STOP:
            self.set_cook_stop_state(
                cook_set_time=self.device.convert_time_for_state(cook_time)
                if cook_time is not None
                else None
            )
            return

        if cook_status == AirFryerCookStatus.PREHEAT_STOP:
            self.set_preheat_stop_state(preheat_set_time=preheat_set_time)
            return

        # Set cook status (setter auto-updates last_timestamp for running statuses)
        self.cook_status = cook_status

        # Handle preheat attributes
        if preheat_set_time is not None:
            self.preheat_set_time = self.device.convert_time_for_state(preheat_set_time)
            self.preheat_last_time = (
                self.device.convert_time_for_state(preheat_last_time)
                if preheat_last_time is not None
                else self.preheat_set_time
            )
        elif cook_status not in PREHEAT_STATUSES:
            self._clear_preheat()

        # Handle cook time attributes
        if cook_time is not None:
            self.cook_set_time = self.device.convert_time_for_state(cook_time)
        if cook_last_time is not None:
            self.cook_last_time = self.device.convert_time_for_state(cook_last_time)
        elif cook_status == AirFryerCookStatus.HEATING:
            self.cook_last_time = None

        # Set remaining attributes
        if cook_temp is not None:
            self.cook_set_temp = cook_temp
        if cook_mode is not None:
            self.cook_mode = cook_mode
        if current_temp is not None:
            self.current_temp = current_temp
        if temp_unit is not None:
            self.device.temp_unit = TemperatureUnits.from_string(temp_unit)
        if recipe is not None:
            self.recipe = recipe


class VeSyncFryer(VeSyncBaseDevice):
    """Base class for VeSync Air Fryer devices.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The VeSync manager.
        feature_map (AirFryerMap): The feature map for the device.

    Attributes:
        state (FryerState): Device state object. For single chamber fryers,
            this is set to ``state_chamber_1``.
        last_response (ResponseInfo): Last response from API call.
        manager (VeSync): Manager object for API calls.
        device_name (str): Name of device.
        device_image (str): URL for device image.
        cid (str): Device ID.
        connection_type (str): Connection type of device.
        device_type (str): Type of device.
        type (str): Type of device.
        uuid (str): UUID of device, not always present.
        config_module (str): Configuration module of device.
        mac_id (str): MAC ID of device.
        current_firm_version (str): Current firmware version of device.
        latest_firm_version (str | None): Latest firmware version of device.
        device_region (str): Region of device. (US, EU, etc.)
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        status_map (MappingProxyType): Mapping of API status strings to
            AirFryerCookStatus enums.
        cook_modes (dict[str, str]): The available cooking modes and their API values.
        default_preset (AirFryerPresetRecipe): The default preset recipe for the fryer.
        min_temp_f (int): The minimum temperature in Fahrenheit.
        max_temp_f (int): The maximum temperature in Fahrenheit.
        min_temp_c (int): The minimum temperature in Celsius.
        max_temp_c (int): The maximum temperature in Celsius.
        state_chamber_1 (FryerState): The state object for chamber 1.
        state_chamber_2 (FryerState): The state object for chamber 2 (if dual chamber).
        sync_chambers (bool): Whether the chambers are synced for cooking.
        temperature_interval (int): The available temperature step interval.
        time_units (TimeUnits): The time units used by the device (seconds or minutes).
    """

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
        'status_map',
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
        """Initialize VeSyncFryer."""
        super().__init__(details, manager, feature_map)
        self.cook_modes: dict[str, str] = feature_map.cook_modes
        self.pid: str | None = AIRFRYER_PID_MAP.get(details.configModule, None)
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
        self.status_map = feature_map.status_map

        # attempt to set temp unit from country code before first update
        self._temp_unit: TemperatureUnits = TemperatureUnits.CELSIUS
        if self.manager.country_code == 'US':
            self._temp_unit = TemperatureUnits.FAHRENHEIT

        # Set state to primary chamber (chamber 1) for base class compatibility
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

    def convert_time_for_api(self, time_in_seconds: int) -> int:
        """Convert time in seconds to the device's time units.

        Args:
            time_in_seconds (int): The time in seconds.

        Returns:
            int: The time converted to the device's time units.
        """
        if self.time_units == TimeUnits.MINUTES:
            return int(time_in_seconds / 60)
        return time_in_seconds

    def convert_time_for_state(self, time_in_device_units: int) -> int:
        """Convert time in device's time units to seconds.

        Args:
            time_in_device_units (int): The time in device's time units.

        Returns:
            int: The time converted to seconds.
        """
        if self.time_units == TimeUnits.MINUTES:
            return time_in_device_units * 60
        return time_in_device_units

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

        Note:
            See [AirFryerPresetRecipe][pyvesync.const.AirFryerPresetRecipe] for
            more details on how to create a preset recipe.
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
