"""Classes for VeSync Switch Devices.

This module provides classes for VeSync Switch Devices:

    1. VeSyncSwitch: Abstract Base class for VeSync Switch Devices.
    2. VeSyncWallSwitch: Class for VeSync Wall Switch Devices ESWL01 and ESWL03.
    3. VeSyncDimmerSwitch: Class for VeSync Dimmer Switch Devices ESWD16.


Attributes:
    feature_dict (dict): Dictionary of switch models and their supported features.
        Defines the class to use for each switch model and the list of features
    switch_modules (dict): Dictionary of switch models as keys and their associated
        classes as string values.

Note:
    The switch device is built from the `feature_dict` dictionary and used by the
    `vesync.object_factory` during initial call to pyvesync.vesync.update() and
    determines the class to instantiate for each switch model. These classes should
    not be instantiated manually.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import TYPE_CHECKING

from typing_extensions import deprecated

from pyvesync.base_devices.switch_base import VeSyncSwitch
from pyvesync.const import ConnectionStatus, DeviceStatus
from pyvesync.models import switch_models
from pyvesync.models.bypass_models import RequestBypassV1, TimerModels
from pyvesync.utils.colors import Color
from pyvesync.utils.device_mixins import BypassV1Mixin, process_bypassv1_result
from pyvesync.utils.helpers import Helpers, Timer, Validators

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import SwitchMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel

_LOGGER = logging.getLogger(__name__)


class VeSyncWallSwitch(BypassV1Mixin, VeSyncSwitch):
    """Etekcity standard wall switch.

    Inherits from the BypassV1Mixin and VeSyncSwitch classes.
    """

    __slots__ = ()

    def __init__(
        self, details: ResponseDeviceDetailsModel, manager: VeSync, feature_map: SwitchMap
    ) -> None:
        """Initialize Etekcity Wall Switch class.

        Args:
            details (ResponseDeviceDetailsModel): The device details.
            manager (VeSync): The VeSync manager.
            feature_map (SwitchMap): The feature map for the device.
        """
        super().__init__(details, manager, feature_map)

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv1_api(
            RequestBypassV1, method='deviceDetail', endpoint='deviceDetail'
        )

        r = Helpers.process_dev_response(_LOGGER, 'get_details', self, r_dict)
        if r is None:
            return
        resp_model = Helpers.model_maker(
            _LOGGER, switch_models.ResponseSwitchDetails, 'get_details', r, self
        )
        if resp_model is None:
            return
        result = resp_model.result
        if not isinstance(result, switch_models.InternalSwitchResult):
            _LOGGER.warning('Invalid response model for switch details')
            return
        self.state.device_status = result.deviceStatus
        self.state.active_time = result.activeTime
        self.state.connection_status = result.connectionStatus

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Toggle switch device."""
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_str = DeviceStatus.from_bool(toggle)

        r_dict = await self.call_bypassv1_api(
            switch_models.RequestSwitchStatus,
            {'status': toggle_str, 'switchNo': 0},
            'deviceStatus',
            'deviceStatus',
        )

        r = Helpers.process_dev_response(_LOGGER, 'get_details', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def get_timer(self) -> None:
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1GetTimer, method='getTimers', endpoint='timer/getTimers'
        )
        if r_dict is None:
            return
        result_model = process_bypassv1_result(
            self, _LOGGER, 'get_timer', r_dict, TimerModels.ResultV1GetTimer
        )
        if result_model is None:
            return

        timers = result_model.timers
        if not isinstance(timers, list) or len(timers) == 0:
            _LOGGER.debug('No timers found')
            return
        if len(timers) > 1:
            _LOGGER.debug('More than one timer found, using first timer')
        timer = timers[0]
        if not isinstance(timer, TimerModels.TimerItemV1):
            _LOGGER.warning('Invalid timer model')
            return
        self.state.timer = Timer(
            int(timer.counterTimer),
            action=timer.action,
            id=int(timer.timerID),
        )

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        if action is None:
            action = (
                DeviceStatus.ON
                if self.state.device_status == DeviceStatus.OFF
                else DeviceStatus.OFF
            )
        if action not in [DeviceStatus.ON, DeviceStatus.OFF]:
            _LOGGER.warning('Invalid action for timer - on/off')
            return False
        update_dict = {
            'action': action,
            'counterTime': str(duration),
        }
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1SetTime,
            update_dict,
            method='addTimer',
            endpoint='timer/addTimer',
        )
        if r_dict is None:
            return False
        result_model = process_bypassv1_result(
            self, _LOGGER, 'set_timer', r_dict, TimerModels.ResultV1SetTimer
        )
        if result_model is None:
            return False
        self.state.timer = Timer(
            int(duration),
            action=action,
            id=int(result_model.timerID),
        )
        return True

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            _LOGGER.warning('No timer set, run get_timer() first.')
            return False
        update_dict = {
            'timerId': str(self.state.timer.id),
        }
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1ClearTimer,
            update_dict,
            method='deleteTimer',
            endpoint='timer/deleteTimer',
        )
        if r_dict is None:
            return False
        result = Helpers.process_dev_response(_LOGGER, 'clear_timer', self, r_dict)
        if result is None:
            return False
        self.state.timer = None
        return True


class VeSyncDimmerSwitch(BypassV1Mixin, VeSyncSwitch):
    """Vesync Dimmer Switch Class with RGB Faceplate.

    Inherits from the BypassV1Mixin and VeSyncSwitch classes.
    """

    __slots__ = ()

    def __init__(
        self, details: ResponseDeviceDetailsModel, manager: VeSync, feature_map: SwitchMap
    ) -> None:
        """Initialize dimmer switch class.

        Args:
            details (ResponseDeviceDetailsModel): The device details.
            manager (VeSync): The VeSync manager.
            feature_map (SwitchMap): The feature map for the device.
        """
        super().__init__(details, manager, feature_map)

    async def get_details(self) -> None:
        r_bytes = await self.call_bypassv1_api(
            switch_models.RequestDimmerDetails,
            method='deviceDetail',
            endpoint='deviceDetail',
        )

        r = Helpers.process_dev_response(_LOGGER, 'get_details', self, r_bytes)
        if r is None:
            return

        resp_model = Helpers.model_maker(
            _LOGGER, switch_models.ResponseSwitchDetails, 'set_timer', r, self
        )
        if resp_model is None:
            return
        result = resp_model.result
        if not isinstance(result, switch_models.InternalDimmerDetailsResult):
            _LOGGER.warning('Invalid response model for dimmer details')
            return
        self.state.active_time = result.activeTime
        self.state.connection_status = result.connectionStatus
        self.state.brightness = result.brightness
        self.state.backlight_status = result.rgbStatus
        new_color = result.rgbValue
        if isinstance(new_color, switch_models.DimmerRGB):
            self.state.backlight_color = Color.from_rgb(
                new_color.red, new_color.green, new_color.blue
            )
        self.state.indicator_status = result.indicatorlightStatus
        self.state.device_status = result.deviceStatus

    @deprecated('switch_toggle() deprecated, use toggle_switch(toggle: bool | None)')
    async def switch_toggle(self, status: str) -> bool:
        """Toggle switch status."""
        return await self.toggle_switch(status == DeviceStatus.ON)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status == 'off'
        toggle_status = DeviceStatus.from_bool(toggle)

        r_bytes = await self.call_bypassv1_api(
            switch_models.RequestDimmerStatus,
            {'status': toggle_status},
            'dimmerPowerSwitchCtl',
            'dimmerPowerSwitchCtl',
        )

        r = Helpers.process_dev_response(_LOGGER, 'toggle_switch', self, r_bytes)
        if r is None:
            return False

        self.state.device_status = toggle_status
        return True

    async def toggle_indicator_light(self, toggle: bool | None = None) -> bool:
        """Toggle indicator light."""
        if toggle is None:
            toggle = self.state.indicator_status == 'off'
        toggle_status = DeviceStatus.from_bool(toggle)

        r_bytes = await self.call_bypassv1_api(
            switch_models.RequestDimmerStatus,
            {'status': toggle_status},
            'dimmerIndicatorLightCtl',
            'dimmerIndicatorLightCtl',
        )

        r = Helpers.process_dev_response(_LOGGER, 'toggle_indicator_light', self, r_bytes)
        if r is None:
            return False

        self.state.indicator_status = toggle_status
        return True

    async def set_backlight_status(
        self,
        status: bool,
        red: int | None = None,
        green: int | None = None,
        blue: int | None = None,
    ) -> bool:
        if red is not None and blue is not None and green is not None:
            new_color = Color.from_rgb(red, green, blue)
        else:
            new_color = None
        status_str = DeviceStatus.from_bool(status)

        update_dict: dict[str, str | dict] = {'status': status_str.value}
        if new_color is not None:
            update_dict['rgbValue'] = asdict(new_color.rgb)
        r_bytes = await self.call_bypassv1_api(
            switch_models.RequestDimmerStatus,
            update_dict,
            'dimmerRgbValueCtl',
            'dimmerRgbValueCtl',
        )

        r = Helpers.process_dev_response(_LOGGER, 'set_rgb_backlight', self, r_bytes)
        if r is None:
            return False

        self.state.backlight_status = status_str
        if new_color is not None:
            self.state.backlight_color = new_color
        self.state.backlight_status = status_str
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_brightness(self, brightness: int) -> bool:
        """Set brightness of dimmer - 1 - 100."""
        if not Validators.validate_zero_to_hundred(brightness):
            _LOGGER.warning('Invalid brightness - must be between 0 and 100')
            return False

        r_bytes = await self.call_bypassv1_api(
            switch_models.RequestDimmerBrightness,
            {'brightness': brightness},
            'dimmerBrightnessCtl',
            'dimmerBrightnessCtl',
        )

        r = Helpers.process_dev_response(_LOGGER, 'get_details', self, r_bytes)
        if r is None:
            return False

        self.state.brightness = brightness
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def get_timer(self) -> None:
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1GetTimer, method='getTimers', endpoint='timer/getTimers'
        )
        result_model = process_bypassv1_result(
            self, _LOGGER, 'get_timer', r_dict, TimerModels.ResultV1GetTimer
        )
        if result_model is None:
            return
        timers = result_model.timers
        if not isinstance(timers, list) or len(timers) == 0:
            _LOGGER.info('No timers found')
            return
        if len(timers) > 1:
            _LOGGER.debug('More than one timer found, using first timer')
        timer = timers[0]
        if not isinstance(timer, TimerModels.TimeItemV1):
            _LOGGER.warning('Invalid timer model')
            return
        self.state.timer = Timer(
            int(timer.counterTime),
            action=timer.action,
            id=int(timer.timerID),
        )

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        if action is None:
            action = (
                DeviceStatus.ON
                if self.state.device_status == DeviceStatus.OFF
                else DeviceStatus.OFF
            )
        if action not in [DeviceStatus.ON, DeviceStatus.OFF]:
            _LOGGER.warning('Invalid action for timer - on/off')
            return False
        update_dict = {'action': action, 'counterTime': str(duration), 'status': '1'}
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1SetTime,
            update_dict,
            method='addTimer',
            endpoint='timer/addTimer',
        )
        result_model = process_bypassv1_result(
            self, _LOGGER, 'set_timer', r_dict, TimerModels.ResultV1SetTimer
        )
        if result_model is None:
            return False
        self.state.timer = Timer(
            int(duration),
            action=action,
            id=int(result_model.timerID),
        )
        return True

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            _LOGGER.debug('No timer set, run get_timer() first.')
            return False
        update_dict = {'timerId': str(self.state.timer.id), 'status': '1'}
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1ClearTimer,
            update_dict,
            method='deleteTimer',
            endpoint='timer/deleteTimer',
        )
        result = Helpers.process_dev_response(_LOGGER, 'clear_timer', self, r_dict)
        if result is None:
            return False
        self.state.timer = None
        return True
