"""VeSync API for controling air purifiers."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from typing_extensions import deprecated
import orjson

from pyvesync.base_devices.purifier_base import VeSyncPurifier
from pyvesync.utils.device_mixins import BypassV2Mixin
from pyvesync.utils.logs import LibraryLogger
from pyvesync.utils.helpers import Helpers, Timer
from pyvesync.models.base_models import DefaultValues
from pyvesync.const import (
    IntFlag,
    StrFlag,
    PurifierAutoPreference,
    DeviceStatus,
    ConnectionStatus,
    AirQualityLevel,
    PurifierModes
    )
from pyvesync.models.purifier_models import (
    PurifierCoreDetailsResult,
    PurifierGetTimerResult,
    PurifierModifyTimerResult,
    PurifierV2DetailsResult,
    PurifierV2EventTiming,
    PurifierV2TimerActionItems,
    PurifierV2TimerPayloadData,
    ResponsePurifierBase,
    RequestPurifier131,
    Purifier131Result,
    ResponsePurifier131Base,
    )

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
    from pyvesync.device_map import PurifierMap


logger = logging.getLogger(__name__)


class VeSyncAirBypass(BypassV2Mixin, VeSyncPurifier):
    """Initialize air purifier devices.

    Instantiated by VeSync manager object. Inherits from
    VeSyncBaseDevice class.

    Parameters:
        details (dict): Dictionary of device details
        manager (VeSync): Instantiated VeSync object used to make API calls
        feature_map (PurifierMap): Device map template

    Attributes:
        modes (list): List of available operation modes for device
        air_quality_feature (bool): True if device has air quality sensor
        details (dict): Dictionary of device details
        timer (Timer): Timer object for device, None if no timer exists. See
            [pyveysnc.helpers.Timer][`Timer`] class
        config (dict): Dictionary of device configuration

    Notes:
        The `details` attribute holds device information that is updated when
        the `update()` method is called. An example of the `details` attribute:
    ```python
    >>> json.dumps(self.details, indent=4)
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

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: PurifierMap) -> None:
        """Initialize VeSync Air Purifier Bypass Base Class."""
        super().__init__(details, manager, feature_map)
        # self.request_keys = [
        #     "acceptLanguage",
        #     "appVersion",
        #     "phoneBrand",
        #     "phoneOS",
        #     "accountId",
        #     "cid",
        #     "configModule",
        #     "debugMode"
        #     "traceId",
        #     "timeZone",
        #     "token",
        #     "userCountryCode",
        # ]

    # def _build_request(
    #         self, payload_method: str, data: dict | None = None, method: str = 'bypassV2'  # noqa: E501
    #         ) -> RequestPurifierStatus:
    #     """Build API request body for air purifier."""
    #     request_keys = [*self.request_keys, "devieId", "configModel"]
    #     body = Helpers.get_class_attributes(DefaultValues, request_keys)
    #     body.update(Helpers.get_class_attributes(self.manager, request_keys))
    #     body.update(Helpers.get_class_attributes(self, request_keys))
    #     body['method'] = method
    #     body['payload'] = {
    #         "method": payload_method,
    #         "source": "APP",
    #         "data": data or {}
    #     }
    #     return RequestPurifierStatus.from_dict(body)

    # def _build_timer_request(
    #         self, payload_method: str, data: dict | None = None) -> RequestPurifierTimer:  # noqa: E501
    #     """Build API request body for air purifier timer."""
    #     request_keys = [*self.request_keys, "deviceRegion"]
    #     body = Helpers.get_class_attributes(DefaultValues, request_keys)
    #     body.update(Helpers.get_class_attributes(self.manager, request_keys))
    #     body.update(Helpers.get_class_attributes(self, request_keys))
    #     body['method'] = 'bypassV2'
    #     body['payload'] = {
    #         "method": payload_method,
    #         "source": "APP",
    #         "data": data or {}
    #     }
    #     return RequestPurifierTimer.from_dict(body)

    def _set_purifier_state(self, result: PurifierCoreDetailsResult) -> None:
        """Populate PurifierState with details from API response.

        Populates `self.state` and instance variables with device details.

        Args:
            result (InnerPurifierResult): Data model for inner result in purifier
                details response.
        """
        self.state.device_status = DeviceStatus.ON if result.enabled else DeviceStatus.OFF
        self.state.filter_life = result.filter_life or 0
        self.state.mode = result.mode
        self.state.fan_level = result.level or 0
        self.state.display_status = DeviceStatus.ON if result.display \
            else DeviceStatus.OFF
        self.state.child_lock = result.child_lock or False
        config = result.configuration
        if config is not None:
            self.state.display_set_state = DeviceStatus.ON if config.display \
                else DeviceStatus.OFF
            self.state.display_forever = config.display_forever
            if config.auto_preference is not None:
                self.state.auto_preference_type = config.auto_preference.type
                self.state.auto_room_size = config.auto_preference.room_size
        if self.supports_air_quality is True:
            self.state.pm25 = result.air_quality_value
            self.state.set_air_quality_level(result.air_quality)
        if result.night_light != StrFlag.NOT_SUPPORTED:
            self.state.nightlight_status = DeviceStatus.ON if result.night_light \
                else DeviceStatus.OFF

    async def get_details(self) -> None:
        """Build Bypass Purifier details dictionary."""
        head = Helpers.bypass_header()
        body = self._build_request('getPurifierStatus')

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return
        try:
            resp_model = ResponsePurifierBase.from_dict(r)
            inner_result = resp_model.result.result
        except (TypeError, ValueError, LookupError, orjson.JSONDecodeError):
            if not isinstance(r.get('result', {}).get("result"), dict):
                LibraryLogger.log_device_api_response_error(
                    logger,
                    self.device_name,
                    self.device_type,
                    "get_details",
                    "Error parsing response"
                )
                return
        inner_result = resp_model.result.result
        if inner_result is not None and isinstance(
            inner_result, PurifierCoreDetailsResult
        ):
            self._set_purifier_state(inner_result)

    async def get_timer(self) -> Timer | None:
        """Retrieve running timer from purifier.

        Returns Timer object if timer is running, None if no timer is running.

        Returns:
            Timer | None : Timer object if timer is running, None if no timer is running

        Notes:
            Timer object tracks the time remaining based on the last update. Timer
            properties include `status`, `time_remaining`, `duration`, `action`,
            `paused` and `done`. The methods `start()`, `end()` and `pause()`
            are available but should be called through the purifier object
            to update through the API.

        See Also:
            [pyvesync.helpers.Time][`Timer`] : Timer object used to hold status of timer

        """
        body = self._build_request('getTimer')
        head = Helpers.bypass_header()
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "get_timer", self, r_bytes)
        if r is None:
            return None

        try:
            resp_model = ResponsePurifierBase.from_dict(r)
            inner_result = resp_model.result.result
            if isinstance(inner_result, PurifierGetTimerResult):
                timer_list = inner_result.timers
            else:
                raise TypeError
        except (TypeError, ValueError, LookupError, orjson.JSONDecodeError):
            LibraryLogger.log_device_api_response_error(
                logger,
                self.device_name,
                self.device_type,
                "get_timer",
                "Error Parsing timer response."
            )
            return None

        if not timer_list:
            logger.debug("No timer found for %s", self.device_name)
            return None
        timer = timer_list[0]
        if self.state.timer is None:
            self.state.timer = Timer(
                timer_duration=timer.total,
                action=timer.action,
                id=timer.id,
                remaining=timer.remain,
            )
        else:
            self.state.timer.update(time_remaining=timer.remain)
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        logger.debug('Timer found: %s', str(self.state.timer))
        return self.state.timer

    async def set_timer(self, timer_duration: int) -> bool:
        """Set timer for Purifier.

        Args:
            timer_duration (int): Duration of timer in seconds

        Returns:
            bool : True if timer is set, False if not

        """
        if self.state.device_status != DeviceStatus.ON:
            logger.debug("Can't set timer when device is off")
        # head, body = self.build_api_dict('addTimer')
        payload_data = {
            "action": "off",
            "total": timer_duration
        }
        body = self._build_request('addTimer', payload_data)
        head = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_timer", self, r_bytes)
        if r is None:
            return False

        resp_model = ResponsePurifierBase.from_dict(r)
        result = resp_model.result.result
        if result is not None and isinstance(result, PurifierModifyTimerResult):
            timer_id = result.id
            self.state.timer = Timer(
                timer_duration=timer_duration, action="off", id=timer_id)
            self.state.device_status = DeviceStatus.ON
            self.state.connection_status = ConnectionStatus.ONLINE
            return True
        logger.warning("Timer not set for %s", self.device_name)
        return False

    async def clear_timer(self) -> bool:
        """Clear timer.

        Returns True if no error is returned from API call.

        Returns:
            bool : True if timer is cleared, False if not
        """
        if self.state.timer is None:
            logger.debug('No timer to clear')
            return False
        payload_data = {
            "id": self.state.timer.id
        }
        body = self._build_request('delTimer', payload_data)
        head = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "clear_timer", self, r_bytes)
        if r is None:
            return False

        logger.debug("Timer cleared")
        self.state.timer = None
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_fan_speed(self, speed: None | int = None) -> bool:
        """Change fan speed based on levels in configuration dict.

        If no value is passed, the next speed in the list is selected.

        Args:
            speed (int, optional): Speed to set fan. Defaults to None.

        Returns:
            bool : True if speed is set, False if not
        """
        speeds: list = self.fan_levels
        current_speed = self.state.fan_level

        if speed is not None:
            if speed not in speeds:
                logger.debug(
                    "%s is invalid speed - valid speeds are %s", speed, str(speeds))
                return False
            new_speed = speed
        else:
            new_speed = speeds[(speeds.index(current_speed) + 1) % len(speeds)]

        data = {
            "id": 0,
            "level": new_speed,
            "type": "wind",
        }
        body = self._build_request('setLevel', data)
        head = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_fan_speed", self, r_bytes)
        if r is None:
            return False

        self.state.fan_level = new_speed
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def child_lock_on(self) -> bool:
        """Turn Bypass child lock on."""
        return await self.set_child_lock(True)

    async def child_lock_off(self) -> bool:
        """Turn Bypass child lock off.

        Returns:
            bool : True if child lock is turned off, False if not
        """
        return await self.set_child_lock(False)

    async def set_child_lock(self, mode: bool) -> bool:
        """Set Bypass child lock.

        Set child lock to on or off. Internal method used by `child_lock_on` and
        `child_lock_off`.

        Args:
            mode (bool): True to turn child lock on, False to turn off

        Returns:
            bool : True if child lock is set, False if not

        """
        if mode not in (True, False):
            logger.debug('Invalid mode passed to set_child_lock - %s', mode)
            return False

        data = {
            "child_lock": mode
        }

        body = self._build_request('setChildLock', data)
        headers = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_child_lock", self, r_bytes)
        if r is None:
            return False

        self.state.child_lock = mode
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def reset_filter(self) -> bool:
        """Reset filter to 100%.

        Returns:
            bool : True if filter is reset, False if not
        """
        # head, body = self.build_api_dict('resetFilter')
        body = self._build_request('resetFilter')
        head = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "reset_filter", self, r_bytes)
        return bool(r)

    @deprecated("Use set_mode(mode: str) instead.")
    async def mode_toggle(self, mode: str) -> bool:
        """Deprecated method for setting purifier mode."""
        return await self.set_mode(mode)

    async def set_mode(self, mode: str) -> bool:
        """Set purifier mode - sleep or manual.

        Set purifier mode based on devices available modes.

        Args:
            mode (str): Mode to set purifier. Based on device modes in attribute `modes`

        Returns:
            bool : True if mode is set, False if not

        """
        if mode.lower() not in self.modes:
            logger.debug('Invalid purifier mode used - %s',
                         mode)
            return False

        if mode.lower() == 'manual':
            return await self.set_fan_speed(self.state.fan_level or 1)

        data = {
            "mode": mode,
        }

        body = self._build_request('setPurifierMode', data)
        head = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "mode_toggle", self, r_bytes)
        if r is None:
            return False

        self.state.mode = mode
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Toggle purifier on/off.

        Helper method for `turn_on()` and `turn_off()` methods.

        Args:
            toggle (bool): True to turn on, False to turn off, None to toggle

        Returns:
            bool : True if purifier is toggled, False if not
        """
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        if not isinstance(toggle, bool):
            logger.debug('Invalid toggle value for purifier switch')
            return False
        data = {
            "enabled": toggle,
            "id": 0
        }

        body = self._build_request('setSwitch', data)
        head = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.ON if toggle else DeviceStatus.OFF
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_display(self, mode: bool) -> bool:
        """Toggle display on/off.

        Called by `turn_on_display()` and `turn_off_display()` methods.

        Args:
            mode (bool): True to turn display on, False to turn off

        Returns:
            bool : True if display is toggled, False if not
        """
        if not isinstance(mode, bool):
            logger.debug("Mode must be True or False")
            return False

        head = Helpers.bypass_header()
        data = {
            "state": mode
        }
        body = self._build_request('setDisplay', data)

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_display", self, r_bytes)
        if r is None:
            return False
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_nightlight_mode(self, mode: str) -> bool:
        """Set night light.

        Possible modes are on, off or dim.

        Args:
            mode (str): Mode to set night light

        Returns:
            bool : True if night light is set, False if not
        """
        if not self.supports_nightlight:
            logger.debug("Device does not support night light")
            return False
        if mode.lower() not in [self.nightlight_modes]:
            logger.warning('Invalid nightlight mode used (on, off or dim)- %s',
                           mode)
            return False

        headers = Helpers.bypass_header()
        body = self._build_request('setNightLight', {'night_light': mode.lower()})

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body,
        )
        r = Helpers.process_dev_response(logger, "set_night_light", self, r_bytes)
        if r is None:
            return False

        self.state.nightlight_status = mode
        return True

    @property
    @deprecated("Use self.state.air_quality instead.")
    def air_quality(self) -> int | None:
        """Get air quality value PM2.5 (ug/m3)."""
        return self.state.pm25

    @property
    @deprecated("Use self.state.fan_level instead.")
    def fan_level(self) -> int | None:
        """Get current fan level."""
        return self.state.fan_level

    @property
    def filter_life(self) -> int | None:
        """Get percentage of filter life remaining."""
        return self.state.filter_life

    @property
    @deprecated("Use self.state.display_status instead.")
    def display_state(self) -> bool:
        """Get display state.

        See [pyvesync.VeSyncAirBypass.display_status][`self.display_status`]
        """
        return self.state.display_status == DeviceStatus.ON

    @property
    @deprecated("Use self.state.display_status instead.")
    def screen_status(self) -> bool:
        """Get display status.

        Returns:
            bool : True if display is on, False if off
        """
        return self.state.display_status == DeviceStatus.ON

    @property
    @deprecated("Use self.state.child_lock instead.")
    def child_lock(self) -> bool:
        """Get child lock state.

        Returns:
            bool : True if child lock is enabled, False if not.
        """
        return self.state.child_lock

    @property
    @deprecated("Use self.state.nightlight_status instead.")
    def night_light(self) -> str:
        """Get night light state.

        Returns:
            str : Night light state (on, dim, off)
        """
        return self.state.nightlight_status

    def display(self) -> None:
        """Print formatted device info to stdout.

        Builds on the `display()` method from the `VeSyncBaseDevice` class.

        See Also:
            [pyvesync.VeSyncBaseDevice.display][`VeSyncBaseDevice.display`]
        """
        super().display()
        disp = [
            ('Mode: ', self.state.mode, ''),
            ('Filter Life: ', self.state.filter_life, 'percent'),
            ('Fan Level: ', self.state.fan_level, ''),
            ('Display: ', self.state.display_status, ''),
            ('Child Lock: ', self.state.child_lock, ''),
            ('Night Light: ', self.state.night_light, ''),
            ('Display Config: ', self.state.display_set_state, ''),
            ('Display_Forever Config: ',
             self.state.display_forever, '')
        ]
        if self.supports_air_quality:
            disp.extend([
                ('Air Quality Level: ',
                    self.state.air_quality, ''),
                ('Air Quality Value: ',
                    self.state.air_quality_value, 'ug/m3')
                ])
        for line in disp:
            print(f'{line[0]:.<30} {line[1]} {line[2]}')

    def displayJSON(self) -> str:
        """Return air purifier status and properties in JSON output.

        Returns:
            str : JSON formatted string of air purifier details
        """
        sup = super().displayJSON()
        sup_val = orjson.loads(sup)
        sup_val.update(
            {
                'Mode': self.state.mode,
                'Filter Life': str(self.state.filter_life),
                'Fan Level': str(self.state.fan_level),
                'Display': self.state.display_status,
                'Child Lock': self.state.child_lock,
                'Night Light': str(self.state.night_light),
                'Display Config': self.state.display_set_state,
                'Display_Forever Config': self.state.display_forever,
            }
        )
        if self.supports_air_quality is True:
            sup_val.update(
                {'Air Quality Level': str(self.state.air_quality)}
            )
            sup_val.update(
                {'Air Quality Value': str(self.state.air_quality_value)}
            )
        return orjson.dumps(
            sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode()


class VeSyncAirBaseV2(VeSyncAirBypass):
    """Levoit V2 Air Purifier Class.

    Inherits from VeSyncAirBypass and VeSyncBaseDevice class.

    Args:
        details (dict): Dictionary of device details
        manager (VeSync): Instantiated VeSync object

    Attributes:
        set_speed_level (int): Set speed level for device
        auto_prefences (list): List of auto preferences for device
        modes (list): List of available operation modes for device
        air_quality_feature (bool): True if device has air quality sensor
        details (dict): Dictionary of device details
        timer (Timer): Timer object for device, None if no timer exists. See
            [pyveysnc.helpers.Timer][`Timer`] class
        config (dict): Dictionary of device configuration

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
        # self.request_keys = [
        #     "acceptLanguage",
        #     "appVersion",
        #     "phoneBrand",
        #     "phoneOS",
        #     "accountId",
        #     "cid",
        #     "configModule",
        #     "debugMode",
        #     "traceId",
        #     "timeZone",
        #     "token",
        #     "userCountryCode",
        #     "deviceId",
        #     "configModel",
        # ]

    def _set_state(self, details: PurifierV2DetailsResult) -> None:
        """Set Purifier state from details response."""
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = DeviceStatus.from_int(details.powerSwitch)
        self.state.mode = details.workMode
        self.state.filter_life = details.filterLifePercent
        if details.fanSpeedLevel == 255:
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
        self.state.display_set_state = DeviceStatus.from_int(details.screenSwitch)
        self.state.display_status = DeviceStatus.from_int(details.screenState)
        auto_pref = details.autoPreference
        if auto_pref is not None:
            self.state.auto_preference_type = auto_pref.autoPreferenceType
            self.state.auto_room_size = auto_pref.roomSize

        self.state.pm1 = details.PM1
        self.state.pm10 = details.PM10
        self.state.aq_percent = details.AQPercent
        self.state.fan_rotate_angle = details.fanRotateAngle
        if details.filterOpenState != IntFlag.NOT_SUPPORTED:
            self.state.filter_open_state = bool(details.filterOpenState)
        if details.timerRemain > 0:
            self.state.timer = Timer(details.timerRemain, 'off')

    @property
    @deprecated("Use self.state.fan_set_level instead.")
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
        # head, body = self.build_api_dict('getPurifierStatus')
        headers = Helpers.bypass_header()
        body = self._build_request('getPurifierStatus')

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        r_model = ResponsePurifierBase.from_dict(r)
        result = r_model.result.result
        if result is None:
            LibraryLogger.log_device_api_response_error(
                logger,
                self.device_name,
                self.device_type,
                "get_details",
                "Error in response nested results"
            )
            return

        if isinstance(result, PurifierV2DetailsResult):
            self._set_state(result)
        else:
            LibraryLogger.log_device_api_response_error(
                logger,
                self.device_name,
                self.device_type,
                "get_details",
                "Error in response nested results"
            )

    @deprecated("Use toggle_light_detection(toggle) instead.")
    async def set_light_detection(self, toggle: bool) -> bool:
        """Set light detection feature."""
        return await self.toggle_light_detection(toggle)

    async def toggle_light_detection(self, toggle: bool) -> bool:
        """Enable/Disable Light Detection Feature."""
        if bool(self.state.light_detection_switch) == toggle:
            logger.debug(
                "Light Detection is already set to %s", self.state.light_detection_switch
                )
            return True

        payload_data = {
            "lightDetectionSwitch": int(toggle)
        }
        body = self._build_request('setLightDetection', payload_data)
        head = Helpers.bypass_header()
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_light_detection", self, r_bytes)
        if r is None:
            return False

        self.state.light_detection_switch = DeviceStatus.ON if toggle \
            else DeviceStatus.OFF
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def turn_on_light_detection(self) -> bool:
        """Turn on light detection feature."""
        return await self.toggle_light_detection(True)

    async def turn_off_light_detection(self) -> bool:
        """Turn off light detection feature."""
        return await self.toggle_light_detection(False)

    @deprecated("Use turn_on_light_detection() instead.")
    async def set_light_detection_on(self) -> bool:
        """Turn on light detection feature."""
        return await self.toggle_light_detection(True)

    @deprecated("Use turn_off_light_detection() instead.")
    async def set_light_detection_off(self) -> bool:
        """Turn off light detection feature."""
        return await self.toggle_light_detection(False)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Toggle purifier on/off."""
        if toggle is None:
            toggle = not bool(self.state.device_status)
        if not isinstance(toggle, bool):
            logger.debug('Invalid toggle value for purifier switch')
            return False
        if toggle == bool(self.state.device_status):
            logger.debug('Purifier is already %s', self.state.device_status)
            return True

        # head, body = self.build_api_dict('setSwitch')
        # power = int(toggle)
        payload_data = {
                'powerSwitch': int(toggle),
                'switchIdx': 0
            }
        body = self._build_request('setSwitch', payload_data)
        head = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_child_lock(self, mode: bool) -> bool:
        """Levoit 100S/200S set Child Lock.

        Parameters:
            mode (bool): True to turn child lock on, False to turn off

        Returns:
            bool : True if successful, False if not
        """
        if self.state.child_lock == mode:
            logger.debug('Child lock is already %s', mode)
            return True

        payload_data = {
            'childLockSwitch': int(mode)
        }
        body = self._build_request('setChildLock', payload_data)
        head = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_child_lock", self, r_bytes)
        if r is None:
            return False

        self.state.child_lock = mode
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_display(self, mode: bool) -> bool:
        """Levoit Vital 100S/200S Set Display on/off with True/False."""
        if bool(self.state.display_set_state) == mode:
            logger.debug('Display is already %s', mode)
            return True

        payload_data = {
            'screenSwitch': int(mode)
        }
        body = self._build_request('setDisplay', payload_data)
        headers = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_display", self, r_bytes)
        if r is None:
            return False

        self.state.display_set_state = DeviceStatus.from_bool(mode)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_timer(
        self, timer_duration: int, action: str = DeviceStatus.OFF
    ) -> bool:
        """Set timer for Levoit 100S.

        Only one timer can be set and only toggling power is supported by passing
        DeviceStatus.ON or DeviceStatus.OFF.

        Parameters:
            timer_duration (int):
                Timer duration in seconds.
            action (str | None):
                Action to perform, on or off, by default 'off'

        Returns:
            bool : True if successful, False if not
        """
        if action not in [DeviceStatus.ON, DeviceStatus.OFF]:
            logger.debug('Invalid action for timer')
            return False

        method = 'powerSwitch'

        # head, body = self.build_api_dict('addTimerV2')
        action_item = PurifierV2TimerActionItems(type=method, act=int(bool(action)))
        timing = PurifierV2EventTiming(clkSec=timer_duration)
        payload_data = PurifierV2TimerPayloadData(
            enabled=True, startAct=[action_item], tmgEvt=timing,
        )

        body = self._build_request('addTimerV2', payload_data.to_dict())
        headers = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_timer", self, r_bytes)
        if r is None:
            return False

        r_model = ResponsePurifierBase.from_dict(r)
        result = r_model.result.result
        if result is None or not isinstance(result, PurifierModifyTimerResult):
            LibraryLogger.log_device_api_response_error(
                logger,
                self.device_name,
                self.device_type,
                "set_timer",
                "Error in response nested results"
            )
            return False

        self.state.timer = Timer(timer_duration, action=action, id=result.id)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def clear_timer(self) -> bool:
        # head, body = self.build_api_dict('delTimerV2')
        # body['payload']['subDeviceNo'] = 0
        # body['payload']['data'] = {'id': 1, "subDeviceNo": 0}

        if self.state.timer is None:
            logger.warning("No timer found, run get_timer() to retreive timer.")
            return False
        paylod_data = {
            "id": self.state.timer.id,
            "subDeviceNo": 0
        }
        body = self._build_request('delTimerV2', paylod_data)
        headers = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "clear_timer", self, r_bytes)
        if r is None:
            return False

        self.state.timer = None
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_auto_preference(self, preference: str = PurifierAutoPreference.DEFAULT,
                                  room_size: int = 600) -> bool:
        """Set Levoit Vital 100S/200S auto mode.

        Parameters:
            preference (str | None | PurifierAutoPreference):
                Preference for auto mode, default 'default' (default, efficient, quiet)
            room_size (int | None):
                Room size in square feet, by default 600
        """
        if preference not in self.auto_preferences:
            logger.debug("%s is invalid preference -"
                         " valid preferences are default, efficient, quiet",
                         preference)
            return False
        # head, body = self.build_api_dict('setAutoPreference')
        # body['payload']['data'] = {
        #     'autoPreference': preference,
        #     'roomSize': room_size,
        # }
        payload_data = {
            "autoPreference": preference,
            "roomSize": room_size
        }
        body = self._build_request('setAutoPreference', payload_data)
        head = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_auto_preference", self, r_bytes)
        if r is None:
            return False

        self.state.auto_preference_type = preference
        self.state.auto_room_size = room_size
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_fan_speed(self, speed: None | int = None) -> bool:
        current_speed = self.state.fan_set_level or 0

        if speed is not None:
            if speed not in self.fan_levels:
                logger.debug("%s is invalid speed - valid speeds are %s",
                             speed, str(self.fan_levels))
                return False
            new_speed = speed
        elif current_speed in [self.fan_levels[-1], 0]:
            new_speed = self.fan_levels[0]
        else:
            current_index = self.fan_levels.index(current_speed)
            new_speed = self.fan_levels[current_index + 1]

        payload_data = {
            "levelIdx": 0,
            "manualSpeedLevel": new_speed,
            "levelType": "wind"
        }
        body = self._build_request('setLevel', payload_data)
        headers = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "change_fan_speed", self, r_bytes)
        if r is None:
            return False

        self.state.fan_set_level = new_speed
        self.state.mode = PurifierModes.MANUAL
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mode(self, mode: str) -> bool:
        if mode.lower() not in self.modes:
            logger.debug('Invalid purifier mode used - %s',
                         mode)
            return False

        # Call change_fan_speed if mode is set to manual
        if mode == PurifierModes.MANUAL:
            if self.state.fan_set_level is None or self.state.fan_level == 0:
                return await self.set_fan_speed(1)
            return await self.set_fan_speed(self.state.fan_set_level)

        payload_data = {
            "workMode": mode
        }
        body = self._build_request('setPurifierMode', payload_data)
        headers = Helpers.bypass_header()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "mode_toggle", self, r_bytes)
        if r is None:
            return False

        self.state.mode = mode
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = DeviceStatus.ON
        return True


class VeSyncAir131(VeSyncPurifier):
    """Levoit Air Purifier Class."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: PurifierMap) -> None:
        """Initilize air purifier class."""
        super().__init__(details, manager, feature_map)
        self.request_keys = [
            "acceptLanguage",
            "appVersion",
            "phoneBrand",
            "phoneOS",
            "accountId",
            "debugMode"
            "traceId",
            "timeZone",
            "token",
            "userCountryCode",
            "uuid"
        ]

    def _build_request(
        self, method: str, update_dict: dict | None = None
    ) -> RequestPurifier131:
        """Build API request body for air purifier timer."""
        body = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        body.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        body.update(Helpers.get_class_attributes(self, self.request_keys))
        body["method"] = method
        if update_dict is not None:
            body.update(update_dict)
        return RequestPurifier131.from_dict(body)

    def _set_state(self, details: Purifier131Result) -> None:
        """Set state from purifier API get_details() response."""
        self.state.device_status = details.deviceStatus
        self.state.connection_status = details.connectionStatus
        self.state.active_time = details.activeTime
        self.state.filter_life = details.filterLife.percent
        self.state.display_status = details.screenStatus
        self.state.display_set_state = details.screenStatus
        self.state.child_lock = bool(DeviceStatus(details.childLock))
        self.state.mode = details.mode
        self.state.fan_level = details.level or 0
        self.state.fan_set_level = details.levelNew
        self.state.air_quality_level = AirQualityLevel(details.airQuality).value

    async def get_details(self) -> None:
        # body = Helpers.req_body(self.manager, 'devicedetail')
        # body['uuid'] = self.uuid
        # head = Helpers.req_headers(self.manager)
        body = self._build_request('deviceDetail')
        headers = Helpers.req_headers(self.manager)

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/deviceDetail',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        r_model = ResponsePurifier131Base.from_dict(r)
        if r_model.result is not None:
            self._set_state(r_model.result)
        else:
            LibraryLogger.log_device_api_response_error(
                logger,
                self.device_name,
                self.device_type,
                "get_details",
                "Error in response nested results"
            )

    async def toggle_display(self, mode: bool) -> bool:
        update_dict = {
            "status": "on" if mode else "off"
        }
        body = self._build_request('airPurifierScreenCtl', update_dict=update_dict)
        headers = Helpers.req_headers(self.manager)

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/airPurifierScreenCtl', 'post',
            json_object=body.to_dict(), headers=headers
        )
        r = Helpers.process_dev_response(logger, "toggle_display", self, r_bytes)
        if r is None:
            return False

        self.state.display_set_state = DeviceStatus.from_bool(mode)
        self.state.display_status = DeviceStatus.from_bool(mode)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON

        update_dict = {
            "status": DeviceStatus.from_bool(toggle).value
        }
        body = self._build_request('airPurifierPowerSwitchCtl', update_dict=update_dict)
        headers = Helpers.req_header_bypass()
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/airPurifierPowerSwitchCtl', 'post',
            json_object=body.to_dict(), headers=headers
        )
        r = Helpers.process_dev_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_fan_speed(self, speed: int | None = None) -> bool:
        current_speed = self.state.fan_set_level or 0

        if speed is not None:
            if speed not in self.fan_levels:
                logger.debug("%s is invalid speed - valid speeds are %s",
                             speed, str(self.fan_levels))
                return False
            new_speed = speed
        elif current_speed in [self.fan_levels[-1], 0]:
            new_speed = self.fan_levels[0]
        else:
            current_index = self.fan_levels.index(current_speed)
            new_speed = self.fan_levels[current_index + 1]

        update_dict = {
            "level": new_speed
        }
        body = self._build_request('airPurifierSpeedCtl', update_dict=update_dict)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/airPurifierSpeedCtl', 'post',
            json_object=body, headers=headers
        )
        r = Helpers.process_dev_response(logger, "change_fan_speed", self, r_bytes)
        if r is None:
            return False

        self.state.fan_level = new_speed
        self.state.fan_set_level = new_speed
        self.state.connection_status = 'online'
        self.state.mode = PurifierModes.MANUAL
        return True

    async def set_mode(self, mode: str) -> bool:
        if mode not in self.modes:
            logger.debug('Invalid purifier mode used - %s', mode)
            return False

        update_dict = {
            "mode": mode
        }
        body = self._build_request('airPurifierModeCtl', update_dict=update_dict)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/airPurifierRunModeCtl', 'post',
            json_object=body.to_dict(), headers=headers
        )
        r = Helpers.process_dev_response(logger, "mode_toggle", self, r_bytes)
        if r is None:
            return False

        self.state.mode = mode
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def update(self) -> None:
        await self.get_details()

    # def display(self) -> None:
    #     """Return formatted device info to stdout."""
    #     super().display()
    #     disp = [
    #         ('Active Time : ', self.active_time, ' minutes'),
    #         ('Fan Level: ', self.fan_level, ''),
    #         ('Air Quality: ', self.air_quality, ''),
    #         ('Mode: ', self.mode, ''),
    #         ('Screen Status: ', self.screen_status, ''),
    #         ('Filter Life: ', orjson.dumps(
    #             self.filter_life, option=orjson.OPT_NON_STR_KEYS), ' percent')
    #         ]
    #     for line in disp:
    #         print(f'{line[0]:.<30} {line[1]} {line[2]}')

    # def displayJSON(self) -> str:
    #     """Return air purifier status and properties in JSON output."""
    #     sup = super().displayJSON()
    #     sup_val = orjson.loads(sup)
    #     sup_val.update(
    #         {
    #             'Active Time': str(self.active_time),
    #             'Fan Level': self.fan_level,
    #             'Air Quality': self.air_quality,
    #             'Mode': self.mode,
    #             'Screen Status': self.screen_status,
    #             'Filter Life': str(self.filter_life)
    #         }
    #     )
    #     return orjson.dumps(
    #         sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode()
