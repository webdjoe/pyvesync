"""Air Fryer Base Class."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pyvesync.base_devices.vesyncbasedevice import DeviceState, VeSyncBaseDevice
from pyvesync.const import (
    AIRFRYER_PID_MAP,
    COOK_STATUSES,
    PREHEAT_STATUSES,
    RESUMABLE_STATUSES,
    RUNNING_STATUSES,
    AirFryerChamber,
    AirFryerCookStatus,
    AirFryerFeatures,
    AirFryerModeConfig,
    AirFryerPresetRecipe,
    AirFryerTempLimits,
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

    Times are in SECONDS, whatever the device's API uses; ``set_state()``
    converts API values with the device's ``convert_time_for_state()``.
    Temperatures are in the device's ``temp_unit``.

    Args:
        device (VeSyncFryer): The device object.
        details (ResponseDeviceDetailsModel): The device details.
        feature_map (AirFryerMap): The feature map for the device.

    Attributes:
        active_time (int): Active time of device, defaults to None.
        connection_status (str): Connection status of device.
        device (VeSyncFryer): Device object.
        device_status (str): Device status.
        features (list[str]): ``AirFryerFeatures`` values from the device map.
        time_units (TimeUnits): The time unit of the device's API. State times
            are always in seconds.
        cook_status (AirFryerCookStatus | None): The current cooking status.
        cook_mode (str | None): The API mode string of the current cook (for
            example ``'AirFry'`` or ``'poultry'``), not an ``AirFryerCookModes``
            key.
        temp_unit (TemperatureUnits): Unit for all temperatures in this state
            (read-through to the device's ``temp_unit``).
        current_temp (int | None): The current temperature in ``temp_unit`` units.
        cook_set_temp (int | None): The set cooking temperature in ``temp_unit``
            units.
        cook_set_time (int | None): The set cooking time in seconds.
        cook_last_time (int | None): The remaining cooking time in seconds at
            the last update or command. ``cook_time_remaining`` counts it down.
        last_timestamp (datetime | None): When the remaining times were last
            refreshed. Set each time ``cook_status`` is set to cooking,
            heating or hold (each update while running), None after standby, a
            stop, or a ``HOLD`` poll while the other chamber is not cooking.
            Used to count the remaining times down.
        preheat_set_time (int | None): The set preheating time in seconds.
        preheat_last_time (int | None): The remaining preheating time in
            seconds at the last update or command. ``preheat_time_remaining``
            counts it down.
        total_last_time (int | None): Device-reported total remaining time
            (preheat plus cook) in seconds at the last update; None when the
            device does not report it (CS158) or after a local command until
            the next update.
        recipe (str | None): The recipe name the device reports. A local
            command sets it only on dual-chamber fryers.
        ready_start (bool): Not used by the library; always False.
        sync_chambers (bool): True only when the device reports the app's Sync
            mode (``syncType`` 2). Dual-chamber fryers only, always False
            otherwise: set by ``update()``, by a successful ``set_mode()`` /
            ``set_mode_from_recipe()`` (True only for ``BOTH``) and by
            ``end(BOTH)`` (False). The same on both chamber states.
        work_chamber (AirFryerChamber | None): Chamber the device reports as
            active (``workChamber``); None when idle or not reported, and
            always None on single-chamber fryers. Set by ``update()``; a
            successful ``WHOLE`` start sets it to ``WHOLE``, any other start
            clears a ``WHOLE`` value, and ending ``WHOLE`` or ``BOTH`` clears
            it. The same on both chamber states.

    Note:
        Device classes call ``set_state()`` with the API response or the sent
        request, ``set_standby()`` to clear the state, and the stop and
        resume helpers for local pause and resume. Setting a running
        ``cook_status`` (cooking, heating or hold) updates ``last_timestamp``. A
        failed or unreadable poll leaves the state unchanged.
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
        'total_last_time',
        'work_chamber',
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
        self.work_chamber: AirFryerChamber | None = None
        # Cooking state attributes
        self._cook_status: AirFryerCookStatus | None = None
        self.current_temp: int | None = None
        self.cook_mode: str | None = None
        self.cook_set_temp: int | None = None
        self.cook_set_time: int | None = None
        self.cook_last_time: int | None = None
        self.preheat_set_time: int | None = None
        self.preheat_last_time: int | None = None
        self.total_last_time: int | None = None
        self.last_timestamp: datetime | None = None
        self.recipe: str | None = None
        self.ready_start: bool = False

    @property
    def temp_unit(self) -> TemperatureUnits:
        """Return the unit for all temperatures in this state.

        This is the device-level unit; all state temperatures
        (``current_temp``, ``cook_set_temp``) are expressed in this unit.
        """
        return self.device.temp_unit

    @property
    def is_in_preheat_mode(self) -> bool:
        """Return True if the fryer is in preheat mode.

        A pulled-out basket counts as preheat only while preheat time remains.
        """
        return self.cook_status in PREHEAT_STATUSES or (
            self.cook_status == AirFryerCookStatus.PULL_OUT
            and bool(self.preheat_last_time)
        )

    @property
    def is_in_cook_mode(self) -> bool:
        """Return True if the fryer is in cook mode."""
        return self.cook_status in COOK_STATUSES or (
            self.cook_status == AirFryerCookStatus.PULL_OUT and not self.preheat_last_time
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
        """Return True if the status is paused (cook or preheat stop).

        Only the CS137/CS158 implements ``resume()``.
        """
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
            self.last_timestamp = datetime.now(tz=UTC)
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
                - int((datetime.now(UTC) - self.last_timestamp).total_seconds()),
            )
        return None

    @property
    def cook_time_remaining(self) -> int | None:
        """Return the remaining cook time in seconds.

        In ``HOLD`` (dual-chamber Sync cook), this is the wait before the
        chamber starts cooking. It counts down only while the other chamber
        cooks; with no ``last_timestamp`` it is the reported wait.
        """
        if not self.is_in_cook_mode:
            return None
        if self.cook_status in [
            AirFryerCookStatus.PULL_OUT,
            AirFryerCookStatus.COOK_STOP,
            AirFryerCookStatus.READY,
        ]:
            return self.cook_last_time
        if self.cook_status == AirFryerCookStatus.HOLD and self.last_timestamp is None:
            return self.cook_last_time

        if self.cook_last_time is not None and self.last_timestamp is not None:
            return max(
                0,
                self.cook_last_time
                - int((datetime.now(UTC) - self.last_timestamp).total_seconds()),
            )
        return None

    @property
    def total_time_remaining(self) -> int | None:
        """Return the time until the cook finishes, in seconds.

        This is the value the app's finish time uses. It comes from the
        device's ``totalTimeRemaining`` where reported (counting down while
        cooking, preheating, or in ``HOLD`` while the other chamber cooks),
        else remaining preheat plus cook time. None in standby, and on the
        CS158 during preheat after an ``update()`` (it reports no cook time
        then).
        """
        if self.cook_status in (None, AirFryerCookStatus.STANDBY):
            return None
        if self.total_last_time is not None:
            if self.cook_status in RUNNING_STATUSES and self.last_timestamp is not None:
                elapsed = int((datetime.now(UTC) - self.last_timestamp).total_seconds())
                return max(0, self.total_last_time - elapsed)
            return self.total_last_time
        if self.is_in_preheat_mode:
            preheat = self.preheat_time_remaining
            cook = self.cook_last_time
            return None if preheat is None or cook is None else preheat + cook
        return self.cook_time_remaining if self.is_in_cook_mode else None

    def _clear_preheat(self) -> None:
        """Clear preheat status."""
        self.preheat_set_time = None
        self.preheat_last_time = None

    def set_standby(self) -> None:
        """Set the fryer state to standby and clear the cook values.

        Clears the temperatures, times, recipe, preheat and
        ``last_timestamp``. ``cook_mode``, ``sync_chambers`` and
        ``work_chamber`` are kept.

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
        self.total_last_time = None
        self.recipe = None
        self._clear_preheat()

    def set_cook_stop_state(
        self,
        cook_set_time: int | None = None,
        cook_last_time: int | None = None,
        total_last_time: int | None = None,
    ) -> None:
        """Set the fryer state to cook stopped.

        Args:
            cook_set_time (int | None): The cooking time in seconds.
            cook_last_time (int | None): The remaining cook time in seconds,
                as reported by the API. None freezes the live remaining time.
            total_last_time (int | None): The device-reported total remaining
                time in seconds, or None when not reported.
        """
        if cook_last_time is None:
            # Read before the status changes, while it still counts down.
            cook_last_time = self.cook_time_remaining
        self._clear_preheat()
        self.cook_status = AirFryerCookStatus.COOK_STOP
        if cook_set_time is not None:
            self.cook_set_time = cook_set_time
        self.cook_last_time = cook_last_time
        self.total_last_time = total_last_time
        self.last_timestamp = None

    def set_preheat_stop_state(
        self,
        preheat_set_time: int | None = None,
        preheat_last_time: int | None = None,
        total_last_time: int | None = None,
    ) -> None:
        """Set the fryer state to preheat stopped.

        Args:
            preheat_set_time (int | None): The preheating time in seconds.
            preheat_last_time (int | None): The remaining preheat time in
                seconds, as reported by the API. None freezes the live
                remaining time.
            total_last_time (int | None): The device-reported total remaining
                time in seconds, or None when not reported.
        """
        if preheat_last_time is None:
            # Read before the status changes, while it still counts down.
            preheat_last_time = self.preheat_time_remaining
        self.cook_status = AirFryerCookStatus.PREHEAT_STOP
        if preheat_set_time is not None:
            self.preheat_set_time = preheat_set_time
        self.preheat_last_time = preheat_last_time
        self.total_last_time = total_last_time
        self.last_timestamp = None

    def set_preheat_resume_state(self, preheat_set_time: int | None = None) -> None:
        """Set the fryer state to preheat resumed.

        The remaining preheat time carries over: a paused preheat resumes
        from its frozen value and a running one keeps counting down.

        Args:
            preheat_set_time (int | None): The preheating time in seconds.
        """
        # Read before the status changes, which restamps last_timestamp.
        remaining = self.preheat_time_remaining
        total = self._carried_total()
        self.cook_status = AirFryerCookStatus.HEATING
        if preheat_set_time is not None:
            self.preheat_set_time = preheat_set_time
        self.preheat_last_time = remaining
        self.total_last_time = total

    def set_cook_resume_state(self) -> None:
        """Set the fryer state to cooking after a resume.

        The remaining cook time carries over: a paused cook resumes from its
        frozen value and a running one keeps counting down.
        """
        # Read before the status changes, which restamps last_timestamp.
        remaining = self.cook_time_remaining
        total = self._carried_total()
        self._clear_preheat()
        self.cook_status = AirFryerCookStatus.COOKING
        if remaining is not None:
            self.cook_last_time = remaining
        self.total_last_time = total

    def _carried_total(self) -> int | None:
        """Return the device-reported total to keep across a local resume."""
        if self.total_last_time is None:
            return None
        return self.total_time_remaining

    def set_state(  # noqa: PLR0913
        self,
        *,
        cook_status: AirFryerCookStatus,
        cook_time: int | None = None,
        cook_last_time: int | None = None,
        cook_temp: int | None = None,
        cook_mode: str | None = None,
        preheat_set_time: int | None = None,
        preheat_last_time: int | None = None,
        current_temp: int | None = None,
        recipe: str | None = None,
        total_last_time: int | None = None,
    ) -> None:
        """Set the cook state from an API response or after a command.

        Pass every value of the current cook state together. Time values are
        in device units and are converted to seconds. ``STANDBY`` and the stop
        statuses use the matching helpers. Otherwise a None ``cook_time``,
        ``cook_temp``, ``cook_mode``, ``current_temp`` or ``recipe`` keeps the
        stored value; a None ``cook_last_time`` keeps it except while heating
        (cleared); and a None ``preheat_set_time`` clears the preheat values
        unless the status is a preheat status.

        Args:
            cook_status (AirFryerCookStatus): The cooking status.
            cook_time (int | None): The cooking time in device units.
            cook_last_time (int | None): The remaining cooking time in device units.
            cook_temp (int | None): The cooking temperature in the device's
                ``temp_unit``.
            cook_mode (str | None): The cooking mode.
            preheat_set_time (int | None): The preheating time in device units.
            preheat_last_time (int | None): The remaining preheat time in device units.
            current_temp (int | None): The current temperature in the device's
                ``temp_unit``.
            recipe (str | None): The recipe name or cooking mode.
            total_last_time (int | None): The device-reported total remaining
                time in device units. None (not reported, or a local command)
                clears the stored total.
        """
        # Stop/standby states delegate to helpers and return early
        if cook_status == AirFryerCookStatus.STANDBY:
            self.set_standby()
            return

        if cook_status == AirFryerCookStatus.COOK_STOP:
            self.set_cook_stop_state(
                cook_set_time=self._to_seconds(cook_time),
                cook_last_time=self._to_seconds(cook_last_time),
                total_last_time=self._to_seconds(total_last_time),
            )
            self._apply_settings(cook_temp, cook_mode, current_temp, recipe)
            return

        if cook_status == AirFryerCookStatus.PREHEAT_STOP:
            self.set_preheat_stop_state(
                preheat_set_time=self._to_seconds(preheat_set_time),
                preheat_last_time=self._to_seconds(preheat_last_time),
                total_last_time=self._to_seconds(total_last_time),
            )
            self._apply_settings(cook_temp, cook_mode, current_temp, recipe)
            return

        # Set cook status (setter auto-updates last_timestamp for running statuses)
        self.cook_status = cook_status
        self.total_last_time = self._to_seconds(total_last_time)

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

        self._apply_settings(cook_temp, cook_mode, current_temp, recipe)

    def _to_seconds(self, value: int | None) -> int | None:
        """Convert an API time in device units to seconds, keeping None."""
        if value is None:
            return None
        return self.device.convert_time_for_state(value)

    def _apply_settings(
        self,
        cook_temp: int | None,
        cook_mode: str | None,
        current_temp: int | None,
        recipe: str | None,
    ) -> None:
        """Set the reported cook settings that are not None."""
        if cook_temp is not None:
            self.cook_set_temp = cook_temp
        if cook_mode is not None:
            self.cook_mode = cook_mode
        if current_temp is not None:
            self.current_temp = current_temp
        if recipe is not None:
            self.recipe = recipe


class VeSyncFryer(VeSyncBaseDevice[FryerState]):
    """Base class for VeSync Air Fryer devices.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The VeSync manager.
        feature_map (AirFryerMap): The feature map for the device.

    Attributes:
        state (FryerState): The same object as ``state_chamber_1``.
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
        pid (str | None): Product ID from ``AIRFRYER_PID_MAP``, by config
            module; None for fryers not in it.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (list[str]): ``AirFryerFeatures`` values from the device map.
        status_map (MappingProxyType): Mapping of API status strings to
            AirFryerCookStatus enums.
        cook_modes (dict[str, AirFryerModeConfig]): The fryer's presets from the
            device map, keyed by ``AirFryerCookModes``. Look one up with
            ``get_cook_mode()``, or get it as a recipe with
            ``get_mode_recipe()``.
        default_preset (AirFryerPresetRecipe): This fryer's own copy of the
            preset whose mode, recipe ID, name and type ``set_mode()`` sends
            when ``cook_mode`` is None or the default mode; ``set_mode()``
            replaces its time, temperature and unit with the caller's. Its
            own time and temperature are the
            library's ``AirFryerPresets`` values and apply only when it is
            passed to ``set_mode_from_recipe()``. They can differ from the
            app's defaults, which ``get_mode_recipe()`` gives (for example
            TF101S Air Fry: ``default_preset`` 400 F / 600 s,
            ``get_mode_recipe()`` 200 C / 1200 s).
        min_temp_f (int): Lowest Fahrenheit temperature over all cook modes.
        max_temp_f (int): Highest Fahrenheit temperature over all cook modes.
        min_temp_c (int): Lowest Celsius temperature over all cook modes.
        max_temp_c (int): Highest Celsius temperature over all cook modes.
        min_temp (int): Lowest temperature over all cook modes, in the current
            unit. A mode can have a narrower range; ``temp_limits()`` gives
            the range ``set_mode()`` accepts.
        max_temp (int): Highest temperature over all cook modes, in the
            current unit (see ``min_temp``).
        state_chamber_1 (FryerState): The state object for chamber 1.
        state_chamber_2 (FryerState): The state object for chamber 2. It exists
            on every fryer, but only dual-chamber fryers update it.
        is_dual_chamber (bool): True if the fryer has two chambers.
        supported_chambers (tuple[AirFryerChamber, ...]): Chambers this fryer
            accepts, derived from ``features``. Every ``chamber`` argument is
            checked against it before a request is sent.
        sync_chambers (bool): Read-only. True only for the app's Sync mode
            (``syncType`` 2, both chambers finish together); Match (1) and
            Off (0) report False. Dual-chamber fryers only, always False
            otherwise: set by ``update()``, by a successful ``set_mode()`` /
            ``set_mode_from_recipe()`` (True only for ``BOTH``) and by
            ``end(BOTH)`` (False). Read from ``state_chamber_1``.
        work_chamber (AirFryerChamber | None): Read-only. Chamber the device
            reports as active (``workChamber``); None when idle or not
            reported, and always None on single-chamber fryers. Set by
            ``update()``; a successful ``WHOLE`` start sets it to ``WHOLE``,
            any other start clears a ``WHOLE`` value, and ending ``WHOLE`` or
            ``BOTH`` clears it. Read from ``state_chamber_1``.
        temp_unit (TemperatureUnits): The device's current temperature unit
            (seeded from the device map, updated from the API on update()).
        temperature_step (int): The default mode's temperature step in the
            current unit.
        temperature_interval (int): Deprecated alias of ``temperature_step``.
        time_units (TimeUnits): The time unit of the device's API (seconds or
            minutes). Every public time is in seconds.
    """

    __slots__ = (
        '_temp_unit',
        'cook_modes',
        'default_preset',
        'state_chamber_1',
        'state_chamber_2',
        'status_map',
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
        self.cook_modes: dict[str, AirFryerModeConfig] = feature_map.cook_modes
        self.pid: str | None = AIRFRYER_PID_MAP.get(details.configModule, None)
        # Copy, so changing one fryer's preset does not change the others.
        self.default_preset: AirFryerPresetRecipe = replace(feature_map.default_preset)
        self.state_chamber_1: FryerState = FryerState(self, details, feature_map)
        self.state_chamber_2: FryerState = FryerState(self, details, feature_map)
        self.time_units: TimeUnits = feature_map.time_units
        self.status_map = feature_map.status_map

        # Device map declares the model's unit; get_details() updates it
        # from the API response if the device reports a different unit.
        self._temp_unit: TemperatureUnits = feature_map.temp_unit

        # Set state to primary chamber (chamber 1) for base class compatibility
        self.state: FryerState = self.state_chamber_1

    @property
    def temp_unit(self) -> TemperatureUnits:
        """Return the temperature unit (F or C)."""
        return self._temp_unit

    @temp_unit.setter
    def temp_unit(self, value: TemperatureUnits | str) -> None:
        """Set the temperature unit.

        A value that does not start with 'c' or 'f' is logged as a warning
        and the current unit is kept.

        Args:
            value (TemperatureUnits | str): The temperature unit
                ('f'/'c'/'fahrenheit'/'celsius' or a TemperatureUnits member).
        """
        try:
            self._temp_unit = TemperatureUnits.from_string(value)
        except ValueError:
            logger.warning(
                'Invalid temperature unit %s for %s, keeping %s',
                value,
                self.device_name,
                self._temp_unit.label,
            )

    @property
    def sync_chambers(self) -> bool:
        """Return True if the chambers are in the app's Sync mode (read-only).

        Set by ``update()`` and by local commands on dual-chamber fryers; see
        the class attributes.
        """
        return self.state_chamber_1.sync_chambers

    @property
    def work_chamber(self) -> AirFryerChamber | None:
        """Return the chamber the device last reported as active (read-only)."""
        return self.state_chamber_1.work_chamber

    @property
    def supported_chambers(self) -> tuple[AirFryerChamber, ...]:
        """Return the chambers this fryer accepts, in enum order.

        Every fryer supports ``CHAMBER_1``. ``DUAL_CHAMBER`` adds ``CHAMBER_2``
        and ``BOTH``; ``WHOLE_CHAMBER`` adds ``WHOLE``.
        """
        chambers = {AirFryerChamber.CHAMBER_1}
        if AirFryerFeatures.DUAL_CHAMBER in self.features:
            chambers.update((AirFryerChamber.CHAMBER_2, AirFryerChamber.BOTH))
        if AirFryerFeatures.WHOLE_CHAMBER in self.features:
            chambers.add(AirFryerChamber.WHOLE)
        return tuple(sorted(chambers))

    @property
    def is_dual_chamber(self) -> bool:
        """Return True if the fryer has two chambers."""
        return AirFryerFeatures.DUAL_CHAMBER in self.features

    def _validate_chamber(self, chamber: AirFryerChamber | int) -> AirFryerChamber | None:
        """Return the chamber as an enum member if this fryer supports it.

        Args:
            chamber (AirFryerChamber | int): The requested chamber.

        Returns:
            AirFryerChamber | None: The enum member, or None (after a debug
            log) when the value is invalid or not supported. Never raises.
        """
        try:
            member = AirFryerChamber(chamber)
        except ValueError:
            logger.debug('Invalid chamber %s for %s', chamber, self.device_name)
            return None
        if member not in self.supported_chambers:
            logger.debug('Chamber %s not supported by %s', member.name, self.device_name)
            return None
        return member

    def get_chamber_state(self, chamber: AirFryerChamber | int) -> FryerState | None:
        """Return the state object for a chamber.

        ``CHAMBER_1`` and ``WHOLE`` map to ``state_chamber_1``, ``CHAMBER_2``
        to ``state_chamber_2``.

        Args:
            chamber (AirFryerChamber | int): The chamber.

        Returns:
            FryerState | None: The chamber's state, or None (after a debug
            log) for ``BOTH``, which has two states (read ``state_chamber_1``
            and ``state_chamber_2``), or for a chamber the fryer does not
            support or an invalid value. Never raises.
        """
        member = self._validate_chamber(chamber)
        if member is None:
            return None
        if member == AirFryerChamber.BOTH:
            logger.debug(
                'Chamber BOTH has two states on %s; read state_chamber_1 and '
                'state_chamber_2',
                self.device_name,
            )
            return None
        return self._chamber_state(member)

    def _chamber_state(self, member: AirFryerChamber) -> FryerState:
        """Return the state for a validated single chamber (not ``BOTH``)."""
        if member == AirFryerChamber.CHAMBER_2:
            return self.state_chamber_2
        return self.state_chamber_1

    def get_cook_mode(self, cook_mode: str | None = None) -> AirFryerModeConfig | None:
        """Return the preset for a cook mode.

        Args:
            cook_mode (str | None): An ``AirFryerCookModes`` key (``'steak'``)
                or the API mode string (``'poultry'``, ``'AirFry'``). None gives
                the default mode, the one the default preset sends.

        Returns:
            AirFryerModeConfig | None: The preset, or None if the fryer has no
            such mode.
        """
        if cook_mode is None:
            cook_mode = self.default_preset.cook_mode
        elif cook_mode in self.cook_modes:
            return self.cook_modes[cook_mode]
        for mode in self.cook_modes.values():
            if mode.api_mode == cook_mode:
                return mode
        return None

    def get_mode_recipe(
        self, cook_mode: str | None = None
    ) -> AirFryerPresetRecipe | None:
        """Return a cook mode's preset as a recipe in the current unit.

        Pass the result to ``set_mode_from_recipe()``. Change its time or
        temperature with ``dataclasses.replace`` first if needed. These are
        the app's defaults for the mode, which can differ from
        ``default_preset``.

        Args:
            cook_mode (str | None): As for ``get_cook_mode()``.

        Returns:
            AirFryerPresetRecipe | None: The recipe at the mode's default time
            and temperature, or None if the fryer has no such mode.
        """
        mode = self.get_cook_mode(cook_mode)
        if mode is None:
            return None
        return mode.to_recipe(self.temp_unit)

    def _recipe_for_set_mode(
        self,
        cook_time: int,
        cook_temp: int,
        cook_mode: str | None,
        preheat_time: int | None,
        temp_unit: TemperatureUnits | None = None,
    ) -> AirFryerPresetRecipe | None:
        """Build the recipe ``set_mode()`` sends.

        The default mode copies ``default_preset``; any other mode uses its own
        preset ID and name. The caller's time, temperature and unit are set on
        the copy.

        Args:
            cook_time (int): Cooking time in seconds.
            cook_temp (int): Cooking temperature in ``temp_unit``.
            cook_mode (str | None): As for ``get_cook_mode()``.
            preheat_time (int | None): Preheating time in seconds, if any.
            temp_unit (TemperatureUnits | None): Unit of ``cook_temp``; None
                means the device's current ``temp_unit``.

        Returns:
            AirFryerPresetRecipe | None: The recipe, or None if the fryer has
            no such mode.
        """
        config = self.get_cook_mode(cook_mode)
        if config is None:
            logger.warning(
                '%s does not support cook mode %s', self.device_name, cook_mode
            )
            return None
        if config.api_mode == self.default_preset.cook_mode:
            recipe = replace(self.default_preset)
        else:
            recipe = config.to_recipe(self.temp_unit)
        recipe.cook_time = cook_time
        recipe.target_temp = cook_temp
        recipe.temp_unit = (temp_unit or self.temp_unit).code
        if preheat_time is not None:
            recipe.preheat_time = preheat_time
        return recipe

    def _resolve_temp_unit(
        self, temp_unit: TemperatureUnits | str | None
    ) -> TemperatureUnits | None:
        """Return the unit a ``set_mode()`` temperature is given in.

        Args:
            temp_unit (TemperatureUnits | str | None): The caller's unit. None
                means the device's current ``temp_unit``.

        Returns:
            TemperatureUnits | None: The unit, or None (after a warning) if it
            is not a valid unit.
        """
        if temp_unit is None:
            return self.temp_unit
        try:
            return TemperatureUnits.from_string(temp_unit)
        except ValueError:
            logger.warning(
                'Invalid temperature unit %s for %s', temp_unit, self.device_name
            )
            return None

    @property
    def _default_mode_config(self) -> AirFryerModeConfig:
        """Return the default mode's preset (always mapped, see the map tests)."""
        mode = self.get_cook_mode()
        if mode is None:
            msg = f'No cook mode matches the default preset of {self.device_name}'
            raise ValueError(msg)
        return mode

    @property
    def min_temp_f(self) -> int:
        """Return the lowest Fahrenheit temperature over all cook modes."""
        return min(m.temp_f.min_temp for m in self.cook_modes.values())

    @property
    def max_temp_f(self) -> int:
        """Return the highest Fahrenheit temperature over all cook modes."""
        return max(m.temp_f.max_temp for m in self.cook_modes.values())

    @property
    def min_temp_c(self) -> int:
        """Return the lowest Celsius temperature over all cook modes."""
        return min(m.temp_c.min_temp for m in self.cook_modes.values())

    @property
    def max_temp_c(self) -> int:
        """Return the highest Celsius temperature over all cook modes."""
        return max(m.temp_c.max_temp for m in self.cook_modes.values())

    @property
    def temperature_step(self) -> int:
        """Return the default mode's temperature step in the current unit."""
        return self._default_mode_config.limits(self.temp_unit).step

    @property
    def temperature_interval(self) -> int:
        """Return the default mode's temperature step in the current unit.

        Deprecated:
            Use ``temperature_step`` instead.
        """
        return self.temperature_step

    @property
    def min_temp(self) -> int:
        """Return the lowest temperature over all cook modes, in the current unit.

        A mode can have a narrower range; ``temp_limits()`` gives the range
        ``set_mode()`` accepts.
        """
        if self.temp_unit == TemperatureUnits.FAHRENHEIT:
            return self.min_temp_f
        return self.min_temp_c

    @property
    def max_temp(self) -> int:
        """Return the highest temperature over all cook modes, in the current unit.

        A mode can have a narrower range; ``temp_limits()`` gives the range
        ``set_mode()`` accepts.
        """
        if self.temp_unit == TemperatureUnits.FAHRENHEIT:
            return self.max_temp_f
        return self.max_temp_c

    def temp_limits(self, cook_mode: str | None = None) -> AirFryerTempLimits:
        """Return a cook mode's temperature limits in the current unit.

        Args:
            cook_mode (str | None): As for ``get_cook_mode()``. None, or a mode
                the fryer does not have, gives the default mode's limits.

        Returns:
            AirFryerTempLimits: The mode's minimum, maximum and step.
        """
        mode = self.get_cook_mode(cook_mode)
        if mode is None:
            logger.debug(
                'Cook mode %s not in the cook modes of %s; using the default '
                "mode's temperature limits",
                cook_mode,
                self.device_name,
            )
            mode = self._default_mode_config
        return mode.limits(self.temp_unit)

    def validate_temperature(
        self, temperature: int, cook_mode: str | None = None
    ) -> bool:
        """Validate the temperature is within the cook mode's range.

        Checks the range only; off-step values are handled by rounding (see
        ``round_temperature()`` and ``prepare_temperature()``).

        Args:
            temperature (int): The temperature in the device's ``temp_unit``.
            cook_mode (str | None): Cook mode whose limits apply, as for
                ``temp_limits()``.

        Returns:
            bool: True if the temperature is valid, False otherwise.
        """
        limits = self.temp_limits(cook_mode)
        return limits.min_temp <= temperature <= limits.max_temp

    def round_temperature(self, temperature: int, cook_mode: str | None = None) -> int:
        """Round the temperature to the nearest step of the cook mode.

        Uses Python's ``round()``, so a value exactly halfway between two
        steps goes to the even multiple (385 to 380 with a 10 degree step).

        Args:
            temperature (int): The temperature in the device's ``temp_unit``.
            cook_mode (str | None): Cook mode whose step applies, as for
                ``temp_limits()``.

        Returns:
            int: The temperature rounded to the mode's step in the current
            unit.
        """
        step = self.temp_limits(cook_mode).step
        return round(temperature / step) * step

    def prepare_temperature(
        self, temperature: int, cook_mode: str | None = None
    ) -> int | None:
        """Round a requested temperature to the mode's step, then validate.

        Args:
            temperature (int): Requested temperature in the device's
                ``temp_unit``.
            cook_mode (str | None): Cook mode whose limits apply, as for
                ``temp_limits()``.

        Returns:
            int | None: The rounded temperature, or None (after a warning) if
            the rounded value is outside the mode's range for the current
            unit.
        """
        rounded = self.round_temperature(temperature, cook_mode)
        if not self.validate_temperature(rounded, cook_mode):
            limits = self.temp_limits(cook_mode)
            mode = self.get_cook_mode(cook_mode) or self._default_mode_config
            logger.warning(
                'Cook temperature %s%s is outside the %s range %s-%s for %s',
                temperature,
                self.temp_unit.code.upper(),
                mode.api_mode,
                limits.min_temp,
                limits.max_temp,
                self.device_name,
            )
            return None
        return rounded

    def prepare_recipe_temperature(self, recipe: AirFryerPresetRecipe) -> int | None:
        """Convert a recipe's temperature to the device unit, round and validate.

        Args:
            recipe (AirFryerPresetRecipe): The recipe, whose ``target_temp`` is
                in ``recipe.temp_unit``.

        Returns:
            int | None: The temperature in the device's ``temp_unit``, rounded
            to the mode's step, or None (after a warning) if it is outside the
            range of the recipe's ``cook_mode`` (of the default mode when the
            fryer has no such mode), or if the temperature or
            ``recipe.temp_unit`` is not valid.
        """
        try:
            temperature = float(recipe.target_temp)
            recipe_unit = TemperatureUnits.from_string(recipe.temp_unit)
        except (TypeError, ValueError):
            logger.warning(
                'Invalid recipe temperature %s %s for %s',
                recipe.target_temp,
                recipe.temp_unit,
                self.device_name,
            )
            return None
        if recipe_unit != self.temp_unit:
            if self.temp_unit == TemperatureUnits.CELSIUS:
                temperature = TemperatureUnits.to_celsius(temperature, recipe_unit)
            else:
                temperature = TemperatureUnits.to_fahrenheit(temperature, recipe_unit)
        return self.prepare_temperature(round(temperature), recipe.cook_mode)

    def convert_time_for_api(self, time_in_seconds: int) -> int:
        """Convert time in seconds to the device's time units.

        Minutes are truncated (``int(seconds / 60)``), so under 60 seconds
        gives 0.

        Args:
            time_in_seconds (int): The time in seconds.

        Returns:
            int: The time converted to the device's time units.
        """
        if self.time_units == TimeUnits.MINUTES:
            return int(time_in_seconds / 60)
        return int(time_in_seconds)

    def _recipe_times(
        self, recipe: AirFryerPresetRecipe
    ) -> tuple[int, int | None] | None:
        """Return a recipe's cook and preheat times as whole seconds.

        The cook time must be at least one API time unit (1 second, or
        60 seconds on minute-based fryers). On fryers with the ``PREHEAT``
        feature the preheat time, if given, must be 0 or at least one unit.
        Other fryers drop it with a debug log.

        Args:
            recipe (AirFryerPresetRecipe): The recipe to check.

        Returns:
            tuple[int, int | None] | None: The cook and preheat times (preheat
            None when not given or not supported), or None (after a warning)
            if either is not valid.
        """
        minimum = self.convert_time_for_state(1)
        try:
            cook_time = int(recipe.cook_time)
        except (TypeError, ValueError):
            cook_time = 0
        if cook_time < minimum:
            logger.warning(
                'Cook time %s is not a number of seconds of at least %s for %s',
                recipe.cook_time,
                minimum,
                self.device_name,
            )
            return None
        if recipe.preheat_time is None:
            return cook_time, None
        if AirFryerFeatures.PREHEAT not in self.features:
            logger.debug('Preheat not supported for %s, ignoring', self.device_name)
            return cook_time, None
        try:
            preheat_time = int(recipe.preheat_time)
        except (TypeError, ValueError):
            preheat_time = -1
        if preheat_time < 0 or 0 < preheat_time < minimum:
            logger.warning(
                'Preheat time %s is not 0 or at least %s seconds for %s',
                recipe.preheat_time,
                minimum,
                self.device_name,
            )
            return None
        return cook_time, preheat_time

    def _prepare_recipe(
        self, recipe: AirFryerPresetRecipe
    ) -> AirFryerPresetRecipe | None:
        """Check a recipe and return a copy ready to send.

        The recipe's ``cook_mode`` must be one of the fryer's cook modes and
        its times must pass ``_recipe_times()``. Its temperature is converted
        to the device unit, rounded and checked (``prepare_recipe_temperature``).

        Args:
            recipe (AirFryerPresetRecipe): The caller's recipe, not changed.

        Returns:
            AirFryerPresetRecipe | None: A copy with the mode's API string,
            whole-second times and the temperature in the device unit, or None
            (after a warning) if a check fails.
        """
        mode = self.get_cook_mode(recipe.cook_mode)
        if mode is None:
            logger.warning(
                '%s does not support cook mode %s', self.device_name, recipe.cook_mode
            )
            return None
        times = self._recipe_times(recipe)
        if times is None:
            return None
        target_temp = self.prepare_recipe_temperature(recipe)
        if target_temp is None:
            return None
        return replace(
            recipe,
            cook_mode=mode.api_mode,
            cook_time=times[0],
            preheat_time=times[1],
            target_temp=target_temp,
            temp_unit=self.temp_unit.code,
        )

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

    async def end(
        self, chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1
    ) -> bool:
        """End the current cooking or preheating session.

        On success the chamber state is set to standby. On the CS137/CS158
        the command depends on the last known state, and it returns False
        without a request when that state is neither cooking nor preheating.
        On the CAF-TF101S/TF102S, ``CHAMBER_1`` during a whole-basket cook
        (``work_chamber`` ``WHOLE``) ends the whole basket.

        Arguments:
            chamber (AirFryerChamber | int): The chamber to end for. Default
                is ``CHAMBER_1``. An unsupported chamber returns False without
                a request.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        del chamber
        logger.info('end not configured for this fryer.')
        return False

    async def stop(
        self, chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1
    ) -> bool:
        """Stop (Pause) the current cooking or preheating session.

        Supported by the CS137/CS158 (``VeSyncAirFryer158``) and dual fryers
        with the ``RESUMABLE`` feature (CAF-DC111S-AEU); other fryers return
        False without a request. The command is always sent:
        the preheat stop when the last known state is a preheat phase,
        otherwise the cook stop. Every successful command sets the state to
        the phase it sent, so the next command picks the matching one.

        Arguments:
            chamber (AirFryerChamber | int): The chamber to stop for. Default
                is ``CHAMBER_1``.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        del chamber
        logger.info('stop not supported by this fryer.')
        return False

    async def resume(
        self, chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1
    ) -> bool:
        """Resume a paused cooking or preheating session.

        Supported by the CS137/CS158 (``VeSyncAirFryer158``) and dual fryers
        with the ``RESUMABLE`` feature (CAF-DC111S-AEU); other fryers return
        False without a request. The command is always sent:
        the preheat resume when the last known state is a preheat phase,
        otherwise the cook resume. The remaining time carries over, so a
        resume while running does not restart the countdown.

        Arguments:
            chamber (AirFryerChamber | int): The chamber to resume for. Default
                is ``CHAMBER_1``.

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
        temp_unit: TemperatureUnits | str | None = None,
        preheat_time: int | None = None,
        cook_mode: str | None = None,
        chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1,
    ) -> bool:
        """Start a cook with the given time and temperature.

        ``cook_temp`` is converted to the device unit if needed, rounded to
        the cook mode's step (see ``round_temperature()``) and checked against
        that mode's limits (see ``temp_limits()``). Out of range logs a
        warning and returns False without a request. On success the chamber
        state is set locally from the request; call ``update()`` for the
        device's reported state.

        Args:
            cook_time (int): The cooking time in seconds, at least 1 (60 on
                the CS137/CS158, whose API uses minutes and truncates to whole
                minutes). A shorter time returns False without a request.
                There is no upper limit: the app's per-mode time ranges are
                not checked.
            cook_temp (int): The cooking temperature, in ``temp_unit``.
            temp_unit (TemperatureUnits | str | None): The unit of
                ``cook_temp``; defaults to the device's current ``temp_unit``.
                An unrecognised unit string returns False without a request.
            preheat_time (int | None): The preheating time in seconds, if any.
                Used only on fryers with the ``PREHEAT`` feature: dropped on
                the CAF-P583S and ignored on the dual-chamber fryers. On fryers
                with preheat it must be 0 or at least one API time unit (60
                seconds on the CS137/CS158); otherwise False without a
                request.
            cook_mode (str | None): Cook mode to use, an ``AirFryerCookModes``
                key or the API mode string (see ``get_cook_mode()``). Its
                recipe ID, name and type are sent. None uses the default
                preset. A mode the fryer does not have returns False without a
                request.
            chamber (AirFryerChamber | int): The chamber to cook in. Default is
                ``CHAMBER_1``. A chamber not in ``supported_chambers`` returns
                False without a request.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        del cook_time, cook_temp, chamber, preheat_time, cook_mode, temp_unit
        logger.warning('set_mode method not implemented for base fryer class.')
        return False

    async def set_mode_from_recipe(
        self,
        recipe: AirFryerPresetRecipe,
        *,
        chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1,
    ) -> bool:
        """Start a cook from a recipe.

        ``recipe.cook_mode`` must be one of the fryer's cook modes (see
        ``get_cook_mode()``); its API mode string is sent.
        ``recipe.target_temp`` is converted from ``recipe.temp_unit`` to the
        device unit, rounded to the mode's step and checked against its
        limits. The times are checked as in ``set_mode()``. A failed check
        (including an invalid ``recipe.temp_unit``) logs a warning and returns
        False without a request. The recipe passed in is not changed.

        Args:
            recipe (AirFryerPresetRecipe): The preset recipe to use. Its recipe
                ID, name and type are sent as given.
            chamber (AirFryerChamber | int): The chamber to cook in. Default is
                ``CHAMBER_1``. A chamber not in ``supported_chambers`` returns
                False without a request.

        Returns:
            bool: True if the command was successful, False otherwise.

        Note:
            Get a fryer's preset with ``get_mode_recipe()`` and change it with
            ``dataclasses.replace``. See
            [AirFryerPresetRecipe][pyvesync.const.AirFryerPresetRecipe].
        """
        del recipe, chamber
        logger.warning(
            'set_mode_from_recipe method not implemented for base fryer class.'
        )
        return False

    async def cook_from_preheat(
        self, chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1
    ) -> bool:
        """Start cooking after the preheat has finished.

        Only the CS137/CS158 (``VeSyncAirFryer158``) supports this; other
        fryers return False without a request. The last known
        ``cook_status`` must be ``PREHEAT_END``, so call ``update()`` after
        the preheat finishes; otherwise it returns False without a request.

        Args:
            chamber (AirFryerChamber | int): The chamber to start cooking for.
                Default is ``CHAMBER_1``.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        del chamber
        if AirFryerFeatures.PREHEAT not in self.features:
            logger.info('Preheat feature not supported on this fryer.')
            return False
        logger.info('cook_from_preheat not configured for this fryer.')
        return False
