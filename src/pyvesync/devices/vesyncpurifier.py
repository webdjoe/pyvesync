"""VeSync API for controlling air purifiers."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, ClassVar

from typing_extensions import deprecated

from pyvesync.base_devices.purifier_base import VeSyncPurifier
from pyvesync.const import (
    ConnectionStatus,
    DeviceStatus,
    NightlightModes,
    PurifierAutoPreference,
    PurifierAutoProfiles,
    PurifierIndicatorRingLevels,
    PurifierModes,
    PurifierQuietPeriodModes,
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
    RequestPurifier131,
    RequestPurifier131Level,
    RequestPurifier131Mode,
)
from pyvesync.utils.device_mixins import (
    BypassV1Mixin,
    BypassV2Mixin,
    countdown_timer_from_result,
    countdown_timer_payload,
    process_bypassv2_result,
)
from pyvesync.utils.helpers import Helpers, Timer

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import PurifierMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel


_LOGGER = logging.getLogger(__name__)

SECONDS_PER_DAY = 86400


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
        self.state.aqi = details.AQI
        self.state.voc = details.VOC
        self.state.no2 = details.NO2
        self.state.carbon_filter_life = details.carbonFilterLifePercent
        self.state.pre_filter_life = details.preFilterLifePercent
        self.state.filter_remain_days = details.filterRemainDay
        self.state.total_clean_air = details.totalCleanAir
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
        if bool(self.state.light_detection_status):
            _LOGGER.error('Cannot set display when light detection is enabled')
            return False

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

    async def set_mode(self, mode: str) -> bool:
        if mode.lower() not in self.modes:
            _LOGGER.warning('Invalid purifier mode used - %s', mode)
            return False

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


class VeSyncAirEleva(VeSyncAirBaseV2):  # pylint: disable=too-many-ancestors
    """Levoit Eleva Air Purifier Class.

    The `getPurifierStatus` response of the Eleva 500X is a cloud snapshot that
    can lag the device by several minutes, while the `deviceProp` field of the
    device list is current. `get_details` overlays `deviceProp` on the snapshot
    for power, mode, fan level, auto profile and air quality values.

    Settings that are only in the snapshot (child lock, display, light
    detection, Quiet Period, indicator ring and timer) are held at their new
    value after a successful command, until the snapshot reports it or
    `PENDING_HOLD_SECONDS` pass.

    Timers use the countdown format of `addTimerV2` (`startAct` and `total`).

    Note:
        The Eleva 500X rejects the `setAutoPreference` request used by other V2
        purifiers, so the auto preference is read-only (the map lists no
        `auto_preferences`).

    Args:
        details (ResponseDeviceDetailsModel): Device details from device list.
        manager (VeSync): Instantiated VeSync object.
        feature_map (PurifierMap): Device map template.
    """

    __slots__ = ('_pending_state',)

    PENDING_HOLD_SECONDS = 300
    AUTO_PROFILES: ClassVar[dict[int, str]] = {
        1: PurifierAutoProfiles.DAILY_COMFORT,
        2: PurifierAutoProfiles.FOCUSED_CARE,
        3: PurifierAutoProfiles.ADVANCED_CARE,
    }
    QUIET_PERIOD_MODES: ClassVar[dict[int, str]] = {
        0: PurifierQuietPeriodModes.LIGHT_CONTROL,
        1: PurifierQuietPeriodModes.SCHEDULE,
    }
    INDICATOR_RING_LEVELS: ClassVar[dict[int, str]] = {
        1: PurifierIndicatorRingLevels.BRIGHT,
        2: PurifierIndicatorRingLevels.DIM,
    }
    QUIET_PERIOD_MODE_IDS: ClassVar[dict[str, int]] = {
        v: k for k, v in QUIET_PERIOD_MODES.items()
    }
    INDICATOR_RING_MODES: ClassVar[dict[str, int]] = {
        v: k for k, v in INDICATOR_RING_LEVELS.items()
    }

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: PurifierMap,
    ) -> None:
        """Initialize the VeSync Eleva Air Purifier Class."""
        super().__init__(details, manager, feature_map)
        self._pending_state: dict[str, tuple[Any, float]] = {}

    def _hold_state(self, attr: str) -> None:
        """Hold the current value of a state attribute set by a command."""
        self._pending_state[attr] = (getattr(self.state, attr), time.monotonic())

    @staticmethod
    def _pending_matches(attr: str, held: object, current: object) -> bool:
        """Return True when the snapshot reports the held value.

        Timers match on presence only, because the remaining time keeps changing.
        """
        if attr == 'timer':
            return (held is None) == (current is None)
        return held == current

    def _apply_pending_state(self) -> None:
        """Keep held values until the snapshot reports them or the hold expires."""
        now = time.monotonic()
        for attr, (value, set_at) in list(self._pending_state.items()):
            if self._pending_matches(attr, value, getattr(self.state, attr)) or (
                now - set_at > self.PENDING_HOLD_SECONDS
            ):
                del self._pending_state[attr]
            else:
                setattr(self.state, attr, value)

    def _set_state(self, details: InnerPurifierBaseResult) -> None:
        """Set state from the snapshot, including the Eleva settings."""
        running_timer = self.state.timer
        super()._set_state(details)
        if not isinstance(details, PurifierVitalDetailsResult):
            return
        if details.timerRemain <= 0:
            self.state.timer = None
        elif running_timer is not None and running_timer.running:
            # The local countdown is more accurate than the snapshot.
            self.state.timer = running_timer
        if details.group is not None:
            self.state.auto_profile = self.AUTO_PROFILES.get(details.group)
        if details.manualGuardSwitch is not None:
            self.state.dynamic_manual = bool(details.manualGuardSwitch)
        if details.sleepGuardSwitch is not None:
            self.state.dynamic_sleep = bool(details.sleepGuardSwitch)
        if details.standbyGuardSwitch is not None:
            self.state.adaptive_start = bool(details.standbyGuardSwitch)
        if details.aqiLightMode is not None:
            self.state.indicator_ring = self.INDICATOR_RING_LEVELS.get(
                details.aqiLightMode
            )
        quiet = details.quietPeriod
        if quiet is not None:
            self.state.quiet_period_switch = DeviceStatus.from_int(
                quiet.quietPeriodSwitch
            )
            self.state.quiet_period_mode = self.QUIET_PERIOD_MODES.get(quiet.modeIdx)
            self.state.quiet_period_start = quiet.startTime
            self.state.quiet_period_end = quiet.endTime

    def _set_device_prop_state(self, prop: dict) -> None:
        """Overlay current values from `deviceProp` on the device state."""
        if prop.get('powerSwitch') is not None:
            self.state.device_status = DeviceStatus.from_int(prop['powerSwitch'])
        if prop.get('workMode') is not None:
            self.state.mode = prop['workMode']
        if prop.get('fanSpeedLevel') is not None:
            fan_level = prop['fanSpeedLevel']
            self.state.fan_level = 0 if fan_level == 255 else fan_level  # noqa: PLR2004
        if prop.get('manualSpeedLevel') is not None:
            self.state.fan_set_level = prop['manualSpeedLevel']
        if prop.get('AQLevel') is not None:
            self.state.air_quality_level = prop['AQLevel']
        if prop.get('healthProtectMode') is not None:
            self.state.auto_profile = self.AUTO_PROFILES.get(prop['healthProtectMode'])
        for key, attr in (
            ('PM1', 'pm1'),
            ('PM25', 'pm25'),
            ('PM10', 'pm10'),
            ('AQI', 'aqi'),
            ('VOC', 'voc'),
            ('NO2', 'no2'),
        ):
            if prop.get(key) is not None:
                setattr(self.state, attr, prop[key])

    async def get_details(self) -> None:
        """Get the status snapshot, then overlay current `deviceProp` values.

        `deviceProp` is read from the device list (`VeSync.get_device_props`)
        before `getPurifierStatus`. Devices updated together share one device
        list request, so a poll costs one device list request in total plus
        one status request per Eleva device. If the device list request
        fails, the snapshot is used unchanged.
        """
        prop = (await self.manager.get_device_props()).get(self.cid)
        await super().get_details()
        if self.state.connection_status != ConnectionStatus.ONLINE:
            return
        if prop is not None:
            self._set_device_prop_state(prop)
        self._apply_pending_state()

    async def toggle_child_lock(self, toggle: bool | None = None) -> bool:
        """Set child lock and hold the new value until the snapshot reports it."""
        if not await super().toggle_child_lock(toggle):
            return False
        self._hold_state('child_lock')
        return True

    async def toggle_display(self, mode: bool) -> bool:
        """Set display and hold the new value until the snapshot reports it."""
        if not await super().toggle_display(mode):
            return False
        self._hold_state('display_set_status')
        return True

    async def toggle_light_detection(self, toggle: bool | None = None) -> bool:
        """Set light detection and hold the new value until the snapshot reports it."""
        if not await super().toggle_light_detection(toggle):
            return False
        self._hold_state('light_detection_switch')
        return True

    async def set_quiet_period(
        self,
        enabled: bool | None = None,
        mode: str | None = None,
        start: int | None = None,
        end: int | None = None,
    ) -> bool:
        """Set the Quiet Period.

        Values left as None keep their current setting.

        Args:
            enabled (bool | None): Turn the Quiet Period on or off.
            mode (str | None): 'light_control' or 'schedule'
                (see `PurifierQuietPeriodModes`).
            start (int | None): Start time in seconds after midnight.
            end (int | None): End time in seconds after midnight.

        Returns:
            bool: True if successful, False if not.
        """
        if enabled is None:
            enabled = bool(self.state.quiet_period_switch)
        mode = mode or self.state.quiet_period_mode
        start = self.state.quiet_period_start if start is None else start
        end = self.state.quiet_period_end if end is None else end
        if mode not in self.QUIET_PERIOD_MODE_IDS or start is None or end is None:
            _LOGGER.warning(
                'Quiet Period mode and times are unknown, run update() or pass them'
            )
            return False
        mode_idx = self.QUIET_PERIOD_MODE_IDS[mode]
        if not (0 <= start < SECONDS_PER_DAY and 0 <= end < SECONDS_PER_DAY):
            _LOGGER.warning('Quiet Period times must be seconds after midnight')
            return False
        payload_data = {
            'quietPeriodSwitch': int(enabled),
            'modeIdx': mode_idx,
            'startTime': start,
            'endTime': end,
        }
        r_dict = await self.call_bypassv2_api('setQuietPeriod', payload_data)
        r = Helpers.process_dev_response(_LOGGER, 'set_quiet_period', self, r_dict)
        if r is None:
            return False
        self.state.quiet_period_switch = DeviceStatus.from_bool(enabled)
        self.state.quiet_period_mode = self.QUIET_PERIOD_MODES[mode_idx]
        self.state.quiet_period_start = start
        self.state.quiet_period_end = end
        for attr in (
            'quiet_period_switch',
            'quiet_period_mode',
            'quiet_period_start',
            'quiet_period_end',
        ):
            self._hold_state(attr)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_indicator_ring(self, level: str) -> bool:
        """Set the air quality indicator ring to 'bright' or 'dim'.

        Args:
            level (str): Ring level, see `PurifierIndicatorRingLevels`.

        Returns:
            bool: True if successful, False if not.
        """
        mode = self.INDICATOR_RING_MODES.get(level)
        if mode is None:
            _LOGGER.warning('Invalid indicator ring level - %s', level)
            return False
        r_dict = await self.call_bypassv2_api('setAqiLight', {'mode': mode})
        r = Helpers.process_dev_response(_LOGGER, 'set_indicator_ring', self, r_dict)
        if r is None:
            return False
        self.state.indicator_ring = self.INDICATOR_RING_LEVELS[mode]
        self._hold_state('indicator_ring')
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def _get_timer_result(self) -> ResultV2GetTimerV2 | None:
        """Return the `getTimerV2` result, or None if the request failed."""
        r_dict = await self.call_bypassv2_api('getTimerV2', {})
        return process_bypassv2_result(
            self, _LOGGER, 'get_timer', r_dict, ResultV2GetTimerV2
        )

    async def get_timer(self) -> Timer | None:
        """Get the active countdown timer from `getTimerV2`."""
        result_model = await self._get_timer_result()
        if result_model is None:
            return None
        self.state.timer = countdown_timer_from_result(result_model)
        if self.state.timer is None:
            _LOGGER.debug('No timer found for %s', self.device_name)
        return self.state.timer

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        """Set a countdown timer that turns the purifier on or off.

        Args:
            duration (int): Timer length in seconds.
            action (str | None): 'off' (default) or 'on' when the timer ends.

        Returns:
            bool: True if successful, False if not.
        """
        if action is None:
            action = DeviceStatus.OFF
        if action not in [DeviceStatus.ON, DeviceStatus.OFF]:
            _LOGGER.warning('Invalid action for timer - %s', action)
            return False
        payload_data = countdown_timer_payload(duration, action)
        r_dict = await self.call_bypassv2_api('addTimerV2', payload_data)
        result_model = process_bypassv2_result(
            self, _LOGGER, 'set_timer', r_dict, ResultV2SetTimer
        )
        if result_model is None:
            return False
        self.state.timer = Timer(
            timer_duration=duration,
            action=action,
            id=result_model.id,
            remaining=duration,
        )
        self._hold_state('timer')
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def clear_timer(self) -> bool:
        """Clear the active countdown timer.

        The timer ID is read from `getTimerV2` first, because the status
        snapshot only reports the remaining time. If the device has no timer,
        nothing is sent and the call succeeds.

        Returns:
            bool: True if the timer was cleared or no timer was set, False if
                the `getTimerV2` or `delTimerV2` request failed.
        """
        result_model = await self._get_timer_result()
        if result_model is None:
            return False
        timer = countdown_timer_from_result(result_model)
        if timer is None:
            _LOGGER.debug('No timer to clear for %s', self.device_name)
        else:
            r_dict = await self.call_bypassv2_api('delTimerV2', {'id': timer.id})
            r = Helpers.process_dev_response(_LOGGER, 'clear_timer', self, r_dict)
            if r is None:
                return False
        self.state.timer = None
        self._hold_state('timer')
        self.state.connection_status = ConnectionStatus.ONLINE
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
