"""VeSync API for controlling air purifiers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from typing_extensions import deprecated

from pyvesync.base_devices.purifier_base import VeSyncPurifier
from pyvesync.const import (
    DEFAULT_TIMER_ID,
    ConnectionStatus,
    DeviceStatus,
    NightlightModes,
    PurifierAutoCleanState,
    PurifierAutoModeTypes,
    PurifierAutoPreference,
    PurifierModes,
    PurifierScreenOnType,
)
from pyvesync.models.bypass_models import (
    ResultV2GetTimer,
    ResultV2GetTimerV2,
    ResultV2SetTimer,
)
from pyvesync.models.purifier_models import (
    InnerPurifierBaseResult,
    Purifier131Result,
    PurifierCoreDetailsResult,
    PurifierRH131Result,
    PurifierSproutResult,
    PurifierV2EventTiming,
    PurifierV2TimerActionItems,
    PurifierV2TimerPayloadData,
    PurifierVitalDetailsResult,
    PurifierVitalPetProResult,
    RequestPurifier131,
    RequestPurifier131Level,
    RequestPurifier131Mode,
)
from pyvesync.utils.device_mixins import (
    BypassV1Mixin,
    BypassV2Mixin,
    process_bypassv2_result,
)
from pyvesync.utils.helpers import Helpers, Timer

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import PurifierMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel


_LOGGER = logging.getLogger(__name__)


class VeSyncAirBypass(BypassV2Mixin, VeSyncPurifier):
    """Initialize air purifier devices.

    Instantiated by VeSync manager object. Inherits from
    VeSyncBaseDevice class. This is the primary class for most
    air purifiers, using the Bypass V2 API, except the original LV-PUR131S.

    Parameters:
        details (dict): Dictionary of device details
        manager (VeSync): Instantiated VeSync object used to make API calls
        feature_map (PurifierMap): Device map template

    Attributes:
        state (PurifierState): State of the device.
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
        device_region (str): Region of device. (US, EU, etc.)
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        modes (list[str]): List of modes supported by the device.
        fan_levels (list[int]): List of fan levels supported by the device.
        nightlight_modes (list[str]): List of nightlight modes supported by the device.
        auto_preferences (list[str]): List of auto preferences supported by the device.

    Notes:
        The `details` attribute holds device information that is updated when
        the `update()` method is called. An example of the `details` attribute:
    ```python
        json.dumps(self.details, indent=4)
        {
            'filter_life': 0,
            'mode': 'manual',
            'level': 0,
            'display': False,
            'child_lock': False,
            'night_light': 'off',
            'air_quality': 0 # air quality level
            'air_quality_value': 0, # PM2.5 value from device,
            'display_forever': False
        }
    ```
    """

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: PurifierMap,
    ) -> None:
        """Initialize VeSync Air Purifier Bypass Base Class."""
        super().__init__(details, manager, feature_map)

    def _set_purifier_state(self, result: PurifierCoreDetailsResult) -> None:
        """Populate PurifierState with details from API response.

        Populates `self.state` and instance variables with device details.

        Args:
            result (InnerPurifierResult): Data model for inner result in purifier
                details response.
        """
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = DeviceStatus.ON if result.enabled else DeviceStatus.OFF
        self.state.filter_life = result.filter_life or 0
        self.state.mode = result.mode
        self.state.fan_level = result.level or 0
        self.state.fan_set_level = result.levelNew or 0
        self.state.display_status = (
            DeviceStatus.ON if result.display else DeviceStatus.OFF
        )
        self.state.child_lock = result.child_lock or False
        config = result.configuration
        if config is not None:
            self.state.display_set_status = (
                DeviceStatus.ON if config.display else DeviceStatus.OFF
            )
            self.state.display_forever = config.display_forever
            if config.auto_preference is not None:
                self.state.auto_preference_type = config.auto_preference.type
                self.state.auto_room_size = config.auto_preference.room_size
        if self.supports_air_quality is True:
            self.state.pm25 = result.air_quality_value
            self.state.set_air_quality_level(result.air_quality)
        if result.night_light is not None:
            self.state.nightlight_status = DeviceStatus(result.night_light)

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv2_api('getPurifierStatus')
        resp_model = process_bypassv2_result(
            self, _LOGGER, 'get_details', r_dict, PurifierCoreDetailsResult
        )
        if resp_model is None:
            return
        self._set_purifier_state(resp_model)

    async def get_timer(self) -> Timer | None:
        r_bytes = await self.call_bypassv2_api('getTimer')
        resp_model = process_bypassv2_result(
            self, _LOGGER, 'get_timer', r_bytes, ResultV2GetTimer
        )
        if resp_model is None:
            return None
        timers = resp_model.timers
        if not timers:
            _LOGGER.debug('No timers found')
            self.state.timer = None
            return None
        timer = timers[0]
        self.state.timer = Timer(
            timer_duration=timer.total,
            action=timer.action,
            id=timer.id,
            remaining=timer.remain,
        )
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        _LOGGER.debug('Timer found: %s', str(self.state.timer))
        return self.state.timer

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        action = DeviceStatus.OFF  # No other actions available for this device
        if self.state.device_status != DeviceStatus.ON:
            _LOGGER.debug("Can't set timer when device is off")
        payload_data = {'action': str(action), 'total': duration}
        r_dict = await self.call_bypassv2_api('addTimer', payload_data)
        resp_model = process_bypassv2_result(
            self, _LOGGER, 'set_timer', r_dict, ResultV2SetTimer
        )
        if resp_model is None:
            return False
        self.state.timer = Timer(timer_duration=duration, action='off', id=resp_model.id)
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            _LOGGER.debug('No timer to clear, run `get_timer()` to get active timer')
            return False
        payload_data = {'id': self.state.timer.id}

        r_dict = await self.call_bypassv2_api('delTimer', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'clear_timer', self, r_dict)
        if r is None:
            return False

        _LOGGER.debug('Timer cleared')
        self.state.timer = None
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_auto_preference(self, preference: str, room_size: int = 800) -> bool:
        if self.state.device_status != DeviceStatus.ON:
            _LOGGER.debug("Can't set auto preference when device is off")
        payload_data = {'type': preference, 'room_size': room_size}
        r_dict = await self.call_bypassv2_api('setAutoPreference', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'set_auto_preference', self, r_dict)
        if r is None:
            return False
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.auto_preference_type = preference
        self.state.auto_room_size = room_size
        return True

    async def set_fan_speed(self, speed: None | int = None) -> bool:
        speeds: list = self.fan_levels
        current_speed = self.state.fan_level

        if speed is not None:
            if speed not in speeds:
                _LOGGER.warning(
                    '%s is invalid speed - valid speeds are %s', speed, str(speeds)
                )
                return False
            new_speed = speed
        else:
            new_speed = Helpers.bump_level(current_speed, self.fan_levels)

        data = {
            'id': 0,
            'level': new_speed,
            'type': 'wind',
        }
        r_dict = await self.call_bypassv2_api('setLevel', data)
        r = Helpers.process_dev_response(_LOGGER, 'set_fan_speed', self, r_dict)
        if r is None:
            return False

        self.state.fan_level = new_speed
        self.state.fan_set_level = new_speed
        self.state.mode = PurifierModes.MANUAL  # Set mode to manual to set fan speed
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_child_lock(self, toggle: bool | None = None) -> bool:
        """Toggle child lock.

        Set child lock to on or off. Internal method used by `turn_on_child_lock` and
        `turn_off_child_lock`.

        Args:
            toggle (bool): True to turn child lock on, False to turn off

        Returns:
            bool : True if child lock is set, False if not
        """
        if toggle is None:
            toggle = self.state.child_lock is False
        data = {'child_lock': toggle}

        r_dict = await self.call_bypassv2_api('setChildLock', data)
        r = Helpers.process_dev_response(_LOGGER, 'toggle_child_lock', self, r_dict)
        if r is None:
            return False

        self.state.child_lock = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def reset_filter(self) -> bool:
        """Reset filter to 100%.

        Returns:
            bool : True if filter is reset, False if not
        """
        r_dict = await self.call_bypassv2_api('resetFilter')
        r = Helpers.process_dev_response(_LOGGER, 'reset_filter', self, r_dict)
        return bool(r)

    @deprecated('Use set_mode(mode: str) instead.')
    async def mode_toggle(self, mode: str) -> bool:
        """Deprecated - Set purifier mode."""
        return await self.set_mode(mode)

    async def set_mode(self, mode: str) -> bool:
        if mode.lower() not in self.modes:
            _LOGGER.warning('Invalid purifier mode used - %s', mode)
            return False

        if mode.lower() == PurifierModes.MANUAL:
            return await self.set_fan_speed(self.state.fan_level or 1)

        data = {
            'mode': mode,
        }
        r_dict = await self.call_bypassv2_api('setPurifierMode', data)

        r = Helpers.process_dev_response(_LOGGER, 'set_mode', self, r_dict)
        if r is None:
            return False

        self.state.mode = mode
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON

        data = {'enabled': toggle, 'id': 0}
        r_dict = await self.call_bypassv2_api('setSwitch', data)
        r = Helpers.process_dev_response(_LOGGER, 'toggle_switch', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.ON if toggle else DeviceStatus.OFF
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_display(self, mode: bool) -> bool:
        data = {'state': mode}
        r_dict = await self.call_bypassv2_api('setDisplay', data)
        r = Helpers.process_dev_response(_LOGGER, 'set_display', self, r_dict)
        if r is None:
            return False
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.display_set_status = DeviceStatus.from_bool(mode)
        return True

    async def set_nightlight_mode(self, mode: str) -> bool:
        if not self.supports_nightlight:
            _LOGGER.debug('Device does not support night light')
            return False
        if mode.lower() not in self.nightlight_modes:
            _LOGGER.warning('Invalid nightlight mode used (on, off or dim)- %s', mode)
            return False

        r_dict = await self.call_bypassv2_api(
            'setNightLight', {'night_light': mode.lower()}
        )
        r = Helpers.process_dev_response(_LOGGER, 'set_night_light', self, r_dict)
        if r is None:
            return False
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.nightlight_status = NightlightModes(mode.lower())
        return True

    @property
    @deprecated('Use self.state.air_quality instead.')
    def air_quality(self) -> int | None:
        """Get air quality value PM2.5 (ug/m3)."""
        return self.state.pm25

    @property
    @deprecated('Use self.state.fan_level instead.')
    def fan_level(self) -> int | None:
        """Get current fan level."""
        return self.state.fan_level

    @property
    @deprecated('Use self.state.filter_life instead.')
    def filter_life(self) -> int | None:
        """Get percentage of filter life remaining."""
        return self.state.filter_life

    @property
    @deprecated('Use self.state.display_status instead.')
    def display_state(self) -> bool:
        """Get display state.

        See [self.state.display_status][`pyvesync.VeSyncAirBypass.state.display_status`]
        """
        return self.state.display_status == DeviceStatus.ON

    @property
    @deprecated('Use self.state.display_status instead.')
    def screen_status(self) -> bool:
        """Get display status.

        Returns:
            bool : True if display is on, False if off
        """
        return self.state.display_status == DeviceStatus.ON


class VeSyncAirBaseV2(VeSyncAirBypass):
    """Levoit V2 Air Purifier Class.

    Handles the Vital 100S/200S and Sprout Air Purifiers. The
    Sprout purifier has a separate class
    [VeSyncAirSprout][pyvesync.devices.vesyncpurifier.VeSyncAirSprout]
    that overrides the `_set_state` method. Inherits from VeSyncAirBypass
    and VeSyncBaseDevice class. For newer devices that use camel-case API calls.

    Args:
        details (dict): Dictionary of device details
        manager (VeSync): Instantiated VeSync object
        feature_map (PurifierMap): Device map template

    Attributes:
        state (PurifierState): State of the device.
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
        device_region (str): Region of device. (US, EU, etc.)
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        modes (list[str]): List of modes supported by the device.
        fan_levels (list[int]): List of fan levels supported by the device.
        nightlight_modes (list[str]): List of nightlight modes supported by the device.
        auto_preferences (list[str]): List of auto preferences supported by the device.
    """

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: PurifierMap,
    ) -> None:
        """Initialize the VeSync Base API V2 Air Purifier Class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, details: InnerPurifierBaseResult) -> None:
        """Set Purifier state from details response."""
        if not isinstance(details, PurifierVitalDetailsResult):
            _LOGGER.warning('Invalid details model passed to _set_state')
            return
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = DeviceStatus.from_int(details.powerSwitch)
        self.state.mode = details.workMode
        self.state.filter_life = details.filterLifePercent
        if details.fanSpeedLevel == 255:  # noqa: PLR2004
            self.state.fan_level = 0
        else:
            self.state.fan_level = details.fanSpeedLevel
        self.state.fan_set_level = details.manualSpeedLevel
        self.state.child_lock = bool(details.childLockSwitch)
        self.state.air_quality_level = details.AQLevel
        self.state.pm25 = details.PM25
        self.state.light_detection_switch = DeviceStatus.from_int(
            details.lightDetectionSwitch
        )
        self.state.light_detection_status = DeviceStatus.from_int(
            details.environmentLightState
        )
        self.state.display_set_status = DeviceStatus.from_int(details.screenSwitch)
        self.state.display_status = DeviceStatus.from_int(details.screenState)
        auto_pref = details.autoPreference
        if auto_pref is not None:
            self.state.auto_preference_type = auto_pref.autoPreferenceType
            self.state.auto_room_size = auto_pref.roomSize

        self.state.pm1 = details.PM1
        self.state.pm10 = details.PM10
        self.state.aq_percent = details.AQPercent
        self.state.fan_rotate_angle = details.fanRotateAngle
        if details.filterOpenState is not None:
            self.state.filter_open_state = bool(details.filterOpenState)
        if details.timerRemain > 0:
            self.state.timer = Timer(details.timerRemain, 'off')

    @property
    @deprecated('Use self.state.fan_set_level instead.')
    def set_speed_level(self) -> int | None:
        """Get set speed level."""
        return self.state.fan_set_level

    @property
    @deprecated("Use self.state.light_detection_switch, this returns 'on' or 'off")
    def light_detection(self) -> bool:
        """Return true if light detection feature is enabled."""
        return self.state.light_detection_switch == DeviceStatus.ON

    @property
    @deprecated("Use self.state.light_detection_status, this returns 'on' or 'off'")
    def light_detection_state(self) -> bool:
        """Return true if light is detected."""
        return self.state.light_detection_status == DeviceStatus.ON

    async def get_details(self) -> None:
        """Build API V2 Purifier details dictionary."""
        r_dict = await self.call_bypassv2_api('getPurifierStatus')
        r_model = process_bypassv2_result(
            self, _LOGGER, 'get_details', r_dict, PurifierVitalDetailsResult
        )
        if r_model is None:
            return

        self._set_state(r_model)

    @deprecated('Use toggle_light_detection(toggle) instead.')
    async def set_light_detection(self, toggle: bool) -> bool:
        """Set light detection feature."""
        return await self.toggle_light_detection(toggle)

    async def toggle_light_detection(self, toggle: bool | None = None) -> bool:
        """Enable/Disable Light Detection Feature."""
        if bool(self.state.light_detection_switch) == toggle:
            _LOGGER.debug(
                'Light detection is already %s', self.state.light_detection_switch
            )
            return True

        if toggle is None:
            toggle = not bool(self.state.light_detection_switch)
        payload_data = {'lightDetectionSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setLightDetection', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'set_light_detection', self, r_dict)
        if r is None:
            return False

        self.state.light_detection_switch = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = not bool(self.state.device_status)
        if toggle == bool(self.state.device_status):
            _LOGGER.debug('Purifier is already %s', self.state.device_status)
            return True

        payload_data = {'powerSwitch': int(toggle), 'switchIdx': 0}
        r_dict = await self.call_bypassv2_api('setSwitch', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'toggle_switch', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_child_lock(self, toggle: bool | None = None) -> bool:
        """Levoit 100S/200S set Child Lock.

        Parameters:
            toggle (bool): True to turn child lock on, False to turn off

        Returns:
            bool : True if successful, False if not
        """
        if toggle is None:
            toggle = not bool(self.state.child_lock)
        payload_data = {'childLockSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setChildLock', payload_data)

        r = Helpers.process_dev_response(_LOGGER, 'toggle_child_lock', self, r_dict)
        if r is None:
            return False

        self.state.child_lock = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_display(self, mode: bool) -> bool:
        if bool(self.state.display_set_status) == mode:
            _LOGGER.debug('Display is already %s', mode)
            return True

        payload_data = {'screenSwitch': int(mode)}
        r_dict = await self.call_bypassv2_api('setDisplay', payload_data)

        r = Helpers.process_dev_response(_LOGGER, 'set_display', self, r_dict)
        if r is None:
            return False

        self.state.display_set_status = DeviceStatus.from_bool(mode)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        action = DeviceStatus.OFF  # No other actions available for this device
        if action not in [DeviceStatus.ON, DeviceStatus.OFF]:
            _LOGGER.warning('Invalid action for timer')
            return False

        method = 'powerSwitch'
        action_int = 1 if action == DeviceStatus.ON else 0
        action_item = PurifierV2TimerActionItems(type=method, act=action_int)
        timing = PurifierV2EventTiming(clkSec=duration)
        payload_data = PurifierV2TimerPayloadData(
            enabled=True,
            startAct=[action_item],
            tmgEvt=timing,
        )

        r_dict = await self.call_bypassv2_api('addTimerV2', payload_data.to_dict())
        r = Helpers.process_dev_response(_LOGGER, 'set_timer', self, r_dict)
        if r is None:
            return False

        r_model = ResultV2SetTimer.from_dict(r)

        self.state.timer = Timer(duration, action=action, id=r_model.id)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            _LOGGER.warning('No timer found, run get_timer() to retrieve timer.')
            return False

        payload_data = {'id': self.state.timer.id, 'subDeviceNo': 0}
        r_dict = await self.call_bypassv2_api('delTimerV2', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'clear_timer', self, r_dict)
        if r is None:
            return False

        self.state.timer = None
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_auto_preference(
        self, preference: str = PurifierAutoPreference.DEFAULT, room_size: int = 600
    ) -> bool:
        """Set Levoit Vital 100S/200S auto mode.

        Parameters:
            preference (str | None | PurifierAutoPreference):
                Preference for auto mode, default 'default' (default, efficient, quiet)
            room_size (int | None):
                Room size in square feet, by default 600
        """
        if preference not in self.auto_preferences:
            _LOGGER.warning(
                '%s is invalid preference -'
                ' valid preferences are default, efficient, quiet',
                preference,
            )
            return False
        payload_data = {'autoPreference': preference, 'roomSize': room_size}
        r_dict = await self.call_bypassv2_api('setAutoPreference', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'set_auto_preference', self, r_dict)
        if r is None:
            return False

        self.state.auto_preference_type = preference
        self.state.auto_room_size = room_size
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_fan_speed(self, speed: None | int = None) -> bool:
        if speed is not None:
            if speed not in self.fan_levels:
                _LOGGER.warning(
                    '%s is invalid speed - valid speeds are %s',
                    speed,
                    str(self.fan_levels),
                )
                return False
            new_speed = speed
        elif self.state.fan_level is None:
            new_speed = self.fan_levels[0]
        else:
            new_speed = Helpers.bump_level(self.state.fan_level, self.fan_levels)

        payload_data = {'levelIdx': 0, 'manualSpeedLevel': new_speed, 'levelType': 'wind'}
        r_dict = await self.call_bypassv2_api('setLevel', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'set_fan_speed', self, r_dict)
        if r is None:
            return False

        self.state.fan_set_level = new_speed
        self.state.fan_level = new_speed
        self.state.mode = PurifierModes.MANUAL
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    def _resolve_mode(self, mode: str) -> str | None:
        """Return the entry of `self.modes` that matches `mode`, ignoring case.

        Mode values sent to the API must keep the spelling in `self.modes`.

        Args:
            mode (str): Requested mode.

        Returns:
            str | None: The matching mode from `self.modes`, or None.
        """
        mode_lower = mode.lower()
        return next((m for m in self.modes if m.lower() == mode_lower), None)

    async def set_mode(self, mode: str) -> bool:
        resolved_mode = self._resolve_mode(mode)
        if resolved_mode is None:
            _LOGGER.warning('Invalid purifier mode used - %s', mode)
            return False
        mode = resolved_mode

        # Call change_fan_speed if mode is set to manual
        if mode == PurifierModes.MANUAL:
            if self.state.fan_set_level is None or self.state.fan_level == 0:
                return await self.set_fan_speed(1)
            return await self.set_fan_speed(self.state.fan_set_level)

        payload_data = {'workMode': mode}
        r_dict = await self.call_bypassv2_api('setPurifierMode', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'mode_toggle', self, r_dict)
        if r is None:
            return False

        self.state.mode = mode
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = DeviceStatus.ON
        return True


class VeSyncAirSprout(VeSyncAirBaseV2):  # pylint: disable=too-many-ancestors
    """Class for the Sprout Air Purifier.

    Inherits from VeSyncAirBaseV2 class and overrides
    the _set_state method. See the
    [VeSyncAirBaseV2][pyvesync.devices.vesyncpurifier.VeSyncAirBaseV2]
    class for more information.

    Args:
        details (dict): Dictionary of device details
        manager (VeSync): Instantiated VeSync object
        feature_map (PurifierMap): Device map template

    Attributes:
        state (PurifierState): State of the device.
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
        device_region (str): Region of device. (US, EU, etc.)
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        modes (list[str]): List of modes supported by the device.
        fan_levels (list[int]): List of fan levels supported by the device.
        nightlight_modes (list[str]): List of nightlight modes supported by the device.
        auto_preferences (list[str]): List of auto preferences supported by the device.
    """

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: PurifierMap,
    ) -> None:
        """Initialize air purifier class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, details: InnerPurifierBaseResult) -> None:
        """Set Purifier state from details response."""
        if not isinstance(details, PurifierSproutResult):
            _LOGGER.warning('Invalid details model passed to _set_state')
            return
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = DeviceStatus.from_int(details.powerSwitch)
        self.state.mode = details.workMode
        if details.fanSpeedLevel == 255:  # noqa: PLR2004
            self.state.fan_level = 0
        else:
            self.state.fan_level = details.fanSpeedLevel
        self.state.fan_set_level = details.manualSpeedLevel
        self.state.child_lock = bool(details.childLockSwitch)
        self.state.air_quality_level = details.AQLevel
        self.state.pm25 = details.PM25
        self.state.pm1 = details.PM1
        self.state.pm10 = details.PM10
        self.state.aq_percent = details.AQI
        self.state.display_set_status = DeviceStatus.from_int(details.screenSwitch)
        self.state.display_status = DeviceStatus.from_int(details.screenState)
        auto_pref = details.autoPreference
        if auto_pref is not None:
            self.state.auto_preference_type = auto_pref.autoPreferenceType
            self.state.auto_room_size = auto_pref.roomSize
        self.state.humidity = details.humidity
        self.state.temperature = int((details.temperature or 0) / 10)
        self.state.pm1 = details.PM1
        self.state.pm10 = details.PM10
        self.state.pm25 = details.PM25
        self.state.voc = details.VOC
        self.state.co2 = details.CO2
        if details.nightlight is not None:
            self.state.nightlight_status = DeviceStatus.from_int(
                details.nightlight.nightLightSwitch
            )
            self.state.nightlight_brightness = details.nightlight.brightness

    async def get_details(self) -> None:
        """Build API V2 Purifier details dictionary."""
        r_dict = await self.call_bypassv2_api('getPurifierStatus')
        r_model = process_bypassv2_result(
            self, _LOGGER, 'get_details', r_dict, PurifierSproutResult
        )
        if r_model is None:
            return

        self._set_state(r_model)


class VeSyncAirVitalPetPro(VeSyncAirBaseV2):  # pylint: disable=too-many-ancestors
    """Class for the Levoit Vital Pet Pro Air Purifier (LAP-P501S).

    Inherits from the
    [VeSyncAirBaseV2][pyvesync.devices.vesyncpurifier.VeSyncAirBaseV2] class.
    Power, manual fan speed and work modes use the same API calls. Status
    parsing, display, child lock and timers use this device's own payloads,
    and it adds the button buzzer and pre-filter self-cleaning.

    The device's Auto mode is three work modes, listed in `auto_mode_types`:
    `odorShieldQuiet`, `odorShieldBalanced` and `odorShieldPerformance`. In
    any of them `state.mode` is `auto` and `state.auto_mode_type` holds the
    work mode. `set_auto_mode_type()` selects one, which also switches the
    purifier to Auto. `set_mode('auto')` and `set_auto_mode()` send the last
    known type, or `odorShieldBalanced` when none is known, as the VeSync
    app's Auto button does.

    In Auto and Sleep modes the device reports `fanSpeedLevel` values outside
    the manual levels 1-3; `state.fan_level` keeps the reported value.

    Display on and child lock re-send settings from the last status, so run
    `update()` before them. Light detection and filter reset are not
    supported: the device has no light sensor, and no app request to reset
    the filter has been captured.

    Args:
        details (ResponseDeviceDetailsModel): Device details from the API.
        manager (VeSync): Instantiated VeSync object.
        feature_map (PurifierMap): Device map template.

    Attributes:
        state (PurifierState): State of the device.
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
        device_region (str): Region of device. (US, EU, etc.)
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        modes (list[str]): List of modes supported by the device.
        fan_levels (list[int]): List of fan levels supported by the device.
        nightlight_modes (list[str]): List of nightlight modes supported by the device.
        auto_preferences (list[str]): List of auto preferences supported by the device.
        auto_mode_types (list[str]): Auto mode types supported by the device.
    """

    __slots__ = ()

    DEFAULT_AUTO_MODE_TYPE: ClassVar[str] = PurifierAutoModeTypes.ODOR_SHIELD_BALANCED
    """Auto mode type sent for `auto` when no type is known (VeSync app default)."""

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: PurifierMap,
    ) -> None:
        """Initialize the Vital Pet Pro air purifier class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, details: InnerPurifierBaseResult) -> None:
        """Set Purifier state from details response."""
        if not isinstance(details, PurifierVitalPetProResult):
            _LOGGER.warning('Invalid details model passed to _set_state')
            return
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = DeviceStatus.from_int(details.powerSwitch)
        self._set_mode_from_status(details.workMode)
        if details.fanSpeedLevel == 255:  # noqa: PLR2004
            self.state.fan_level = 0
        else:
            self.state.fan_level = details.fanSpeedLevel
        self.state.fan_set_level = details.manualSpeedLevel
        self.state.air_quality_level = details.AQLevel
        self.state.pm25 = details.PM25
        self.state.voc = details.VOC
        self.state.filter_life = details.filterLifePercent
        self.state.filter_remain_day = details.filterRemainDay
        if details.filterOpenState is not None:
            self.state.filter_open_state = bool(details.filterOpenState)
        self.state.display_set_status = DeviceStatus.from_int(details.screenSwitch)
        self.state.display_status = DeviceStatus.from_int(details.screenState)
        if details.screenPreference is not None:
            screen = details.screenPreference
            self.state.display_on_type = screen.screenOnType
            self.state.display_start_time = screen.screenStartTime
            self.state.display_end_time = screen.screenEndTime
        self.state.child_lock = bool(details.childLockSwitch)
        if details.childLockPreference is not None:
            pref = details.childLockPreference
            self.state.child_lock_auto_switch = pref.childLockAutoSwitch
            self.state.child_lock_auto_time = pref.childLockAutoSwitchTime
        if details.buzzerSwitch is not None:
            self.state.buzzer_status = DeviceStatus.from_int(details.buzzerSwitch)
        if details.autoCleanPreference is not None:
            clean = details.autoCleanPreference
            self.state.auto_clean_status = bool(clean.autoCleanState)
            self.state.auto_clean_remaining = clean.autoCleanRemainTime
            self.state.auto_clean_total = clean.autoCleanTotalTime
        self._set_timer_from_status(details.timerRemain)

    def _set_mode_from_status(self, work_mode: str) -> None:
        """Set `state.mode` and `state.auto_mode_type` from the `workMode`.

        An auto mode type is reported as mode `auto`. In other modes the
        last known auto mode type is kept, so `set_auto_mode()` can return
        to it (the VeSync app does the same).
        """
        if work_mode in self.auto_mode_types:
            self.state.mode = PurifierModes.AUTO
            self.state.auto_mode_type = work_mode
        else:
            self.state.mode = work_mode

    def _set_timer_from_status(self, timer_remain: int) -> None:
        """Update `state.timer` from the status `timerRemain` seconds."""
        if timer_remain <= 0:
            self.state.timer = None
            return
        current = self.state.timer
        if current is None:
            self.state.timer = Timer(timer_remain, DeviceStatus.OFF, id=DEFAULT_TIMER_ID)
        else:
            self.state.timer = Timer(
                current.timer_duration,
                current.action,
                id=current.id,
                remaining=timer_remain,
            )
        self.state.timer.update_ts()

    async def get_details(self) -> None:
        """Get the purifier status from the API and update state."""
        r_dict = await self.call_bypassv2_api('getPurifierStatus')
        r_model = process_bypassv2_result(
            self, _LOGGER, 'get_details', r_dict, PurifierVitalPetProResult
        )
        if r_model is None:
            return

        self._set_state(r_model)

    async def set_mode(self, mode: str) -> bool:
        """Set the purifier mode.

        `auto` is not a device work mode. It sends the last known auto mode
        type (`state.auto_mode_type`), or `odorShieldBalanced` when none is
        known, as the VeSync app's Auto button does.

        `manual` sends the last manual speed (`state.fan_set_level`), or level
        1 when none is known, as the VeSync app's Manual button does. The
        reported `fan_level` is not used: in Auto it can be 0 while running.

        Args:
            mode (str): Mode to set, one of `self.modes` (case-insensitive).

        Returns:
            bool: True if successful, False otherwise.
        """
        resolved_mode = self._resolve_mode(mode)
        if resolved_mode == PurifierModes.AUTO:
            auto_mode_type = self.state.auto_mode_type or self.DEFAULT_AUTO_MODE_TYPE
            return await self.set_auto_mode_type(auto_mode_type)
        if resolved_mode == PurifierModes.MANUAL:
            manual_level = self.state.fan_set_level or self.fan_levels[0]
            return await self.set_fan_speed(manual_level)
        return await super().set_mode(mode)

    async def set_auto_mode_type(self, auto_mode_type: str) -> bool:
        """Set the auto mode type and switch the purifier to auto mode.

        Args:
            auto_mode_type (str): One of `self.auto_mode_types`
                (`PurifierAutoModeTypes`), case-insensitive.

        Returns:
            bool: True if successful, False otherwise.
        """
        type_lower = auto_mode_type.lower()
        resolved_type = next(
            (t for t in self.auto_mode_types if t.lower() == type_lower), None
        )
        if resolved_type is None:
            _LOGGER.warning(
                '%s is not a valid auto mode type - valid types are %s',
                auto_mode_type,
                self.auto_mode_types,
            )
            return False

        payload_data = {'workMode': resolved_type}
        r_dict = await self.call_bypassv2_api('setPurifierMode', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'set_auto_mode_type', self, r_dict)
        if r is None:
            return False

        self.state.mode = PurifierModes.AUTO
        self.state.auto_mode_type = resolved_type
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_display(self, mode: bool) -> bool:
        """Turn the display on or off.

        Turning the display on re-sends the display on-mode from the last
        status, with the daily window when the display is scheduled, as the
        VeSync app does. This keeps a display schedule. Run `update()` first.

        Args:
            mode (bool): True to turn the display on, False to turn it off.

        Returns:
            bool: True if successful, False otherwise.
        """
        if bool(self.state.display_set_status) == mode:
            _LOGGER.debug('Display is already %s', mode)
            return True

        payload_data: dict[str, int]
        if not mode:
            payload_data = {'screenSwitch': int(DeviceStatus.OFF)}
        elif self.state.display_on_type is None:
            _LOGGER.warning('Display settings unknown, run update() first')
            return False
        elif self.state.display_on_type == PurifierScreenOnType.SCHEDULED:
            start_time = self.state.display_start_time
            end_time = self.state.display_end_time
            if start_time is None or end_time is None:
                _LOGGER.warning('Display schedule unknown, run update() first')
                return False
            payload_data = {
                'screenEndTime': end_time,
                'screenOnType': int(PurifierScreenOnType.SCHEDULED),
                'screenStartTime': start_time,
                'screenSwitch': int(DeviceStatus.ON),
            }
        else:
            payload_data = {
                'screenOnType': self.state.display_on_type,
                'screenSwitch': int(DeviceStatus.ON),
            }
        r_dict = await self.call_bypassv2_api('setDisplay', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'toggle_display', self, r_dict)
        if r is None:
            return False

        self.state.display_set_status = DeviceStatus.from_bool(mode)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_child_lock(self, toggle: bool | None = None) -> bool:
        """Set the child lock (control lock).

        The device expects the auto child lock settings with every request,
        so they are re-sent from the last status. Run `update()` first.

        Args:
            toggle (bool | None): True to lock, False to unlock. If None,
                toggle the current state.

        Returns:
            bool: True if successful, False otherwise.
        """
        if (
            self.state.child_lock_auto_switch is None
            or self.state.child_lock_auto_time is None
        ):
            _LOGGER.warning('Child lock settings unknown, run update() first')
            return False
        if toggle is None:
            toggle = not bool(self.state.child_lock)
        payload_data = {
            'childLockAutoSwitch': self.state.child_lock_auto_switch,
            'childLockAutoSwitchTime': self.state.child_lock_auto_time,
            'childLockSwitch': int(toggle),
        }
        r_dict = await self.call_bypassv2_api('setChildLock', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'toggle_child_lock', self, r_dict)
        if r is None:
            return False

        self.state.child_lock = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_buzzer(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.buzzer_status != DeviceStatus.ON
        payload_data = {'buzzerSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setBuzzer', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'toggle_buzzer', self, r_dict)
        if r is None:
            return False

        self.state.buzzer_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_auto_clean(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = not bool(self.state.auto_clean_status)
        clean_state = (
            PurifierAutoCleanState.START if toggle else PurifierAutoCleanState.STOP
        )
        payload_data = {'autoCleanState': int(clean_state)}
        r_dict = await self.call_bypassv2_api('setAutoClean', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'toggle_auto_clean', self, r_dict)
        if r is None:
            return False

        self.state.auto_clean_status = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_light_detection(self, toggle: bool | None = None) -> bool:
        """Not supported: the Vital Pet Pro has no light detection.

        Its only air sensors are PM2.5 and TVOC, and the VeSync app has no
        light detection control for it.

        Returns:
            bool: Always False.
        """
        del toggle
        _LOGGER.debug('Light detection not supported for this device.')
        return False

    async def reset_filter(self) -> bool:
        """Not supported: no app request to reset the filter has been captured.

        Reset the Check Filter Indicator on the purifier instead, by holding
        the Auto Mode button for 3 seconds.

        Returns:
            bool: Always False.
        """
        _LOGGER.debug('Filter life reset not supported for this device.')
        return False

    async def get_timer(self) -> Timer | None:
        r_dict = await self.call_bypassv2_api('getTimerV2', {})
        r_model = process_bypassv2_result(
            self, _LOGGER, 'get_timer', r_dict, ResultV2GetTimerV2
        )
        if r_model is None:
            return None
        if not r_model.timers:
            _LOGGER.debug('No timers found')
            self.state.timer = None
            return None
        timer = r_model.timers[0]
        action: str = DeviceStatus.OFF
        if timer.startAct:
            action = DeviceStatus.from_int(timer.startAct[0].act)
        self.state.timer = Timer(timer.total, action, id=timer.id, remaining=timer.remain)
        self.state.timer.update_ts()
        self.state.connection_status = ConnectionStatus.ONLINE
        return self.state.timer

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        """Set a timer that turns the purifier off.

        The request is sent without checking for a running timer, and the timer
        is stored with id `DEFAULT_TIMER_ID`. A new timer replaces the running
        one.

        Args:
            duration (int): Timer length in seconds.
            action (str | None): Only 'off' (the default) is supported.

        Returns:
            bool: True if successful, False otherwise.
        """
        if action is not None and action != DeviceStatus.OFF:
            _LOGGER.warning('Only an "off" timer is supported for this device')
            return False
        payload_data = {
            'startAct': [{'type': 'powerSwitch', 'num': 0, 'act': int(DeviceStatus.OFF)}],
            'total': duration,
        }
        r_dict = await self.call_bypassv2_api('addTimerV2', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'set_timer', self, r_dict)
        if r is None:
            return False

        self.state.timer = Timer(duration, DeviceStatus.OFF, id=DEFAULT_TIMER_ID)
        self.state.timer.update_ts()
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def clear_timer(self) -> bool:
        """Cancel the running timer.

        `delTimerV2` is sent with id `DEFAULT_TIMER_ID`, without reading the
        timer list or checking `state.timer` first. Every captured timer id on
        this model is 1.

        Returns:
            bool: True if successful, False on error.
        """
        payload_data = {'id': DEFAULT_TIMER_ID}
        r_dict = await self.call_bypassv2_api('delTimerV2', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'clear_timer', self, r_dict)
        if r is None:
            return False

        self.state.timer = None
        self.state.connection_status = ConnectionStatus.ONLINE
        return True


class VeSyncAir131(BypassV1Mixin, VeSyncPurifier):
    """Levoit Air Purifier Class.

    Class for LV-PUR131S, using BypassV1 API.

    Attributes:
        state (PurifierState): State of the device.
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
        device_region (str): Region of device. (US, EU, etc.)
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        modes (list[str]): List of modes supported by the device.
        fan_levels (list[int]): List of fan levels supported by the device.
        nightlight_modes (list[str]): List of nightlight modes supported by the device.
        auto_preferences (list[str]): List of auto preferences supported by the device.
    """

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: PurifierMap,
    ) -> None:
        """Initialize air purifier class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, details: Purifier131Result) -> None:
        """Set state from purifier API get_details() response."""
        self.state.device_status = details.deviceStatus
        self.state.connection_status = details.connectionStatus
        self.state.active_time = details.activeTime
        if details.filterLife is not None:
            self.state.filter_life = details.filterLife.percent
        self.state.display_status = DeviceStatus(details.screenStatus)
        self.state.display_set_status = details.screenStatus
        self.state.mode = details.mode
        self.state.fan_level = details.level or 0
        self.state.fan_set_level = details.level or 0
        self.state.set_air_quality_level(details.airQuality)

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv1_api(
            RequestPurifier131, method='deviceDetail', endpoint='deviceDetail'
        )
        r = Helpers.process_dev_response(_LOGGER, 'get_details', self, r_dict)
        if r is None:
            return

        r_model = Purifier131Result.from_dict(r.get('result', {}))
        self._set_state(r_model)

    async def toggle_display(self, mode: bool) -> bool:
        update_dict = {'status': 'on' if mode else 'off'}
        r_dict = await self.call_bypassv1_api(
            RequestPurifier131,
            method='airPurifierScreenCtl',
            endpoint='airPurifierScreenCtl',
            update_dict=update_dict,
        )
        r = Helpers.process_dev_response(_LOGGER, 'toggle_display', self, r_dict)
        if r is None:
            return False

        self.state.display_set_status = DeviceStatus.from_bool(mode)
        self.state.display_status = DeviceStatus.from_bool(mode)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON

        update_dict = {'status': DeviceStatus.from_bool(toggle).value}
        r_dict = await self.call_bypassv1_api(
            RequestPurifier131,
            method='airPurifierPowerSwitchCtl',
            endpoint='airPurifierPowerSwitchCtl',
            update_dict=update_dict,
        )
        r = Helpers.process_dev_response(_LOGGER, 'toggle_switch', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_fan_speed(self, speed: int | None = None) -> bool:
        current_speed = self.state.fan_set_level or 0

        if speed is not None:
            if speed not in self.fan_levels:
                _LOGGER.warning(
                    '%s is invalid speed - valid speeds are %s',
                    speed,
                    str(self.fan_levels),
                )
                return False
            new_speed = speed
        else:
            new_speed = Helpers.bump_level(current_speed, self.fan_levels)

        update_dict = {'level': new_speed}
        r_dict = await self.call_bypassv1_api(
            RequestPurifier131Level,
            method='airPurifierSpeedCtl',
            endpoint='airPurifierSpeedCtl',
            update_dict=update_dict,
        )
        r = Helpers.process_dev_response(_LOGGER, 'set_fan_speed', self, r_dict)
        if r is None:
            return False

        self.state.fan_level = new_speed
        self.state.fan_set_level = new_speed
        self.state.connection_status = 'online'
        self.state.mode = PurifierModes.MANUAL
        return True

    async def set_mode(self, mode: str) -> bool:
        if mode not in self.modes:
            _LOGGER.warning('Invalid purifier mode used - %s', mode)
            return False

        if mode == PurifierModes.MANUAL:
            set_level = (
                1 if self.state.fan_set_level in [0, None] else self.state.fan_set_level
            )
            return await self.set_fan_speed(set_level)

        update_dict = {'mode': mode}
        r_dict = await self.call_bypassv1_api(
            RequestPurifier131Mode,
            method='airPurifierRunModeCtl',
            endpoint='airPurifierRunModeCtl',
            update_dict=update_dict,
        )
        r = Helpers.process_dev_response(_LOGGER, 'mode_toggle', self, r_dict)
        if r is None:
            return False

        self.state.mode = mode
        self.state.connection_status = ConnectionStatus.ONLINE
        return True


class VeSyncAirRH131(BypassV2Mixin, VeSyncPurifier):
    """Levoit Air Purifier Class.

    Class for LV-PUR131S, using BypassV1 API.

    Attributes:
        state (PurifierState): State of the device.
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
        device_region (str): Region of device. (US, EU, etc.)
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        modes (list[str]): List of modes supported by the device.
        fan_levels (list[int]): List of fan levels supported by the device.
        nightlight_modes (list[str]): List of nightlight modes supported by the device.
        auto_preferences (list[str]): List of auto preferences supported by the device.
    """

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: PurifierMap,
    ) -> None:
        """Initialize air purifier class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, details: PurifierRH131Result) -> None:
        """Set state from purifier API get_details() response."""
        self.state.device_status = DeviceStatus.from_bool(details.enabled)
        self.state.connection_status = ConnectionStatus.ONLINE
        if details.filter_life is not None:
            self.state.filter_life = details.filter_life
        self.state.display_status = DeviceStatus.from_bool(details.display)
        self.state.display_set_status = DeviceStatus.from_bool(details.display)
        self.state.mode = details.mode
        self.state.fan_level = details.level or 0
        self.state.fan_set_level = details.level or 0
        self.state.set_air_quality_level(details.air_quality or 0)
        self.state.child_lock = details.child_lock

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv2_api('getPurifierStatus')
        r_model = process_bypassv2_result(
            self, _LOGGER, 'get_details', r_dict, PurifierRH131Result
        )
        if r_model is None:
            return

        self._set_state(r_model)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON

        payload_data = {'enabled': toggle, 'id': 0}
        r_dict = await self.call_bypassv2_api('setSwitch', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'toggle_switch', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_display(self, mode: bool) -> bool:
        update_dict = {'state': mode}
        r_dict = await self.call_bypassv2_api('setDisplay', update_dict)
        r = Helpers.process_dev_response(_LOGGER, 'toggle_display', self, r_dict)
        if r is None:
            return False

        self.state.display_set_status = DeviceStatus.from_bool(mode)
        self.state.display_status = DeviceStatus.from_bool(mode)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mode(self, mode: str) -> bool:
        if mode not in self.modes:
            _LOGGER.warning('Invalid purifier mode used - %s', mode)
            return False

        payload_data = {'mode': mode}
        r_dict = await self.call_bypassv2_api('setPurifierMode', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'set_mode', self, r_dict)
        if r is None:
            return False

        self.state.mode = mode
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_fan_speed(self, speed: int | None = None) -> bool:
        if speed is not None:
            if speed not in self.fan_levels:
                _LOGGER.warning(
                    '%s is invalid speed - valid speeds are %s',
                    speed,
                    str(self.fan_levels),
                )
                return False
            new_speed = speed
        else:
            new_speed = Helpers.bump_level(self.state.fan_level or 0, self.fan_levels)

        payload_data = {'level': new_speed, 'id': 0, 'type': 'wind'}

        r_dict = await self.call_bypassv2_api('setLevel', payload_data)

        r = Helpers.process_dev_response(_LOGGER, 'set_fan_speed', self, r_dict)
        if r is None:
            return False

        self.state.fan_level = new_speed
        self.state.fan_set_level = new_speed
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.mode = PurifierModes.MANUAL
        return True

    async def toggle_child_lock(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = not bool(self.state.child_lock)
        payload_data = {'child_lock': toggle}
        r_dict = await self.call_bypassv2_api('setChildLock', payload_data)

        r = Helpers.process_dev_response(_LOGGER, 'toggle_child_lock', self, r_dict)
        if r is None:
            return False

        self.state.child_lock = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True
