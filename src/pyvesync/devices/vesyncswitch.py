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
from dataclasses import asdict
import logging
# from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING
from deprecated import deprecated

from pyvesync.base_devices.switch_base import VeSyncSwitch
from pyvesync.utils.colors import Color
from pyvesync.utils.helpers import Helpers, Validators
from pyvesync.utils.device_mixins import BypassV1Mixin
from pyvesync.const import ConnectionStatus, DeviceStatus
from pyvesync.models.bypass_models import RequestBypassV1
from pyvesync.models.switch_models import (
    ResponseSwitchDetails,
    InternalDimmerDetailsResult,
    InternalSwitchResult,
    RequestDimmerBrightness,
    RequestSwitchStatus,
    RequestDimmerDetails,
    RequestDimmerStatus,
    DimmerRGB,
    )

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
    from pyvesync.device_map import SwitchMap

logger = logging.getLogger(__name__)

# --8<-- [start:feature_dict]

feature_dict: dict[str, dict[str, list | str]] = {
    'ESWL01': {
        'module': 'VeSyncWallSwitch',
        'features': []
    },
    'ESWD16': {
        'module': 'VeSyncDimmerSwitch',
        'features': ['dimmable']
    },
    'ESWL03': {
        'module': 'VeSyncWallSwitch',
        'features': []
    }
}

# --8<-- [end:feature_dict]

switch_modules: dict = {k: v['module']
                        for k, v in feature_dict.items()}

__all__: list = [*switch_modules.values(), 'switch_modules']  # noqa: PLE0604


class VeSyncWallSwitch(BypassV1Mixin, VeSyncSwitch):
    """Etekcity standard wall switch.

    Inherits from the BypassV1Mixin and VeSyncSwitch classes.
    """

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: SwitchMap) -> None:
        """Initialize Etekcity Wall Switch class.

        Args:
            details (ResponseDeviceDetailsModel): The device details.
            manager (VeSync): The VeSync manager.
            feature_map (SwitchMap): The feature map for the device.
        """
        super().__init__(details, manager, feature_map)

    async def get_details(self) -> None:
        r_bytes = await self.call_bypassv1_api(
            RequestBypassV1, method='deviceDetail', endpoint='deviceDetail'
            )

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return
        resp_model = ResponseSwitchDetails.from_dict(r)
        result = resp_model.result
        if not isinstance(result, InternalSwitchResult):
            logger.warning("Invalid response model for switch details")
            return
        self.state.device_status = result.deviceStatus
        self.state.active_time = result.activeTime
        self.state.connection_status = result.connectionStatus

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Toggle switch device."""
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_str = DeviceStatus.from_bool(toggle)

        r_bytes = await self.call_bypassv1_api(
            RequestSwitchStatus,
            {"status": toggle_str, "switchNo": 0},
            'deviceStatus',
            'deviceStatus'
            )

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return False

        self.state.device_status = 'on' if toggle else 'off'
        self.state.connection_status = 'online'
        return True


class VeSyncDimmerSwitch(BypassV1Mixin, VeSyncSwitch):
    """Vesync Dimmer Switch Class with RGB Faceplate.

    Inherits from the BypassV1Mixin and VeSyncSwitch classes.
    """

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: SwitchMap) -> None:
        """Initialize dimmer switch class.

        Args:
            details (ResponseDeviceDetailsModel): The device details.
            manager (VeSync): The VeSync manager.
            feature_map (SwitchMap): The feature map for the device.
        """
        super().__init__(details, manager, feature_map)

    async def get_details(self) -> None:
        r_bytes = await self.call_bypassv1_api(
            RequestDimmerDetails, method='deviceDetail', endpoint='deviceDetail'
            )

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        resp_model = ResponseSwitchDetails.from_dict(r)
        result = resp_model.result
        if not isinstance(result, InternalDimmerDetailsResult):
            logger.warning("Invalid response model for dimmer details")
            return
        self.state.active_time = result.activeTime
        self.state.connection_status = result.connectionStatus
        self.state.brightness = result.brightness
        self.state.backlight_status = result.rgbStatus
        new_color = result.rgbValue
        if isinstance(new_color, DimmerRGB):
            self.state.backlight_color = Color.from_rgb(
                new_color.red, new_color.green, new_color.blue
                )
        self.state.indicator_status = result.indicatorlightStatus
        self.state.device_status = result.deviceStatus

    @deprecated(
        reason="switch_toggle() deprecated, use toggle_switch(toggle: bool | None = None)"
    )
    async def switch_toggle(self, status: str) -> bool:
        """Toggle switch status."""
        return await self.toggle_switch(status == 'on')

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status == 'off'
        toggle_status = DeviceStatus.from_bool(toggle)

        r_bytes = await self.call_bypassv1_api(
            RequestDimmerStatus,
            {"status": toggle_status},
            'dimmerPowerSwitchCtl',
            'dimmerPowerSwitchCtl'
            )

        r = Helpers.process_dev_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        self.state.device_status = toggle_status
        return True

    async def indicator_light_toggle(self, toggle: bool | None = None) -> bool:
        """Toggle indicator light."""
        if toggle is None:
            toggle = self.state.indicator_status == 'off'
        toggle_status = DeviceStatus.from_bool(toggle)

        r_bytes = await self.call_bypassv1_api(
            RequestDimmerStatus,
            {"status": toggle_status},
            'dimmerIndicatorLightCtl',
            'dimmerIndicatorLightCtl'
            )

        r = Helpers.process_dev_response(logger, "indicator_light_toggle", self, r_bytes)
        if r is None:
            return False

        self.state.indicator_status = toggle_status
        return True

    async def turn_indicator_light_on(self) -> bool:
        """Turn Indicator light on."""
        return await self.indicator_light_toggle(True)

    async def turn_indicator_light_off(self) -> bool:
        """Turn indicator light off."""
        return await self.indicator_light_toggle(False)

    async def set_backlight_status(
        self,
        status: bool,
        red: int | None = None,
        blue: int | None = None,
        green: int | None = None,
    ) -> bool:
        """Set faceplate RGB color."""
        if red is not None and blue is not None and green is not None:
            new_color = Color.from_rgb(red, green, blue)
        else:
            new_color = None
        status_str = DeviceStatus.from_bool(status)

        update_dict: dict[str, str | dict] = {"status": status_str.value}
        if new_color is not None:
            update_dict['rgbValue'] = asdict(new_color.rgb)
        r_bytes = await self.call_bypassv1_api(
            RequestDimmerStatus,
            update_dict,
            'dimmerRgbValueCtl',
            'dimmerRgbValueCtl'
            )

        r = Helpers.process_dev_response(logger, "set_rgb_backlight", self, r_bytes)
        if r is None:
            return False

        self.state.backlight_status = status_str
        if new_color is not None:
            self.state.backlight_color = new_color
        self.state.backlight_status = status_str
        self.state.device_status = 'on'
        self.state.connection_status = 'online'
        return True

    async def turn_rgb_backlight_off(self) -> bool:
        """Turn RGB Color Off."""
        return await self.set_backlight_status(False)

    async def turn_rgb_backlight_on(self) -> bool:
        """Turn RGB Color Off."""
        return await self.set_backlight_status(True)

    async def set_backlight_color(self, red: int, green: int, blue: int) -> bool:
        """Set RGB color of faceplate."""
        new_color = Color.from_rgb(red, green, blue)
        if new_color is None:
            logger.warning("Invalid RGB values")
            return False
        return await self.set_backlight_status(True, red, blue, green)

    async def set_brightness(self, brightness: int) -> bool:
        """Set brightness of dimmer - 1 - 100."""
        if not Validators.validate_zero_to_hundred(brightness):
            logger.warning("Invalid brightness - must be between 0 and 100")
            return False

        r_bytes = await self.call_bypassv1_api(
            RequestDimmerBrightness,
            {"brightness": brightness},
            'dimmerBrightnessCtl',
            'dimmerBrightnessCtl'
            )

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return False

        self.state.brightness = brightness
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True
