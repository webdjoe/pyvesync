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
import orjson

from pyvesync.base_devices.switch_base_device import VeSyncSwitch
from pyvesync.data_models.base_models import DefaultValues
from pyvesync.helper_utils.colors import Color
from pyvesync.helper_utils.helpers import Helpers, Validators
from pyvesync.data_models.switch_models import (
    RequestSwitchStatus,
    RequestSwitchDetails,
    ResponseDimmerDetails,
    ResponseSwitchDetails,
    RequestDimmerBrightness,
    )

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.data_models.device_list_models import ResponseDeviceDetailsModel
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


class VeSyncWallSwitch(VeSyncSwitch):
    """Etekcity standard wall switch."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: SwitchMap) -> None:
        """Initilize Etekcity Wall Switch class."""
        super().__init__(details, manager, feature_map)
        self.request_keys = [
            'acceptLanguage',
            'accountID',
            'appVersion',
            'cid',
            'configModule',
            'phoneBrand',
            'phoneOS',
            'timeZone',
            'token',
            'traceId',
            'userCountryCode',
            'debugMode',
            'uuid',
        ]

    def _build_request_base(self, method: str) -> dict:
        """Build the request body for dimmer switch."""
        base_dict = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        base_dict.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        base_dict.update(Helpers.get_class_attributes(self, self.request_keys))
        base_dict['configModel'] = self.config_module
        base_dict['deviceId'] = self.cid
        base_dict['method'] = method
        return base_dict

    def _build_status_request(self, status: str) -> RequestSwitchStatus:
        """Build the data model to send a status request."""
        base_dict = self._build_request_base('deviceStatus')
        base_dict['status'] = status
        return RequestSwitchStatus.from_dict(base_dict)

    def _build_details_request(self) -> RequestSwitchDetails:
        """Build the data model to send a details request."""
        base_dict = self._build_request_base('deviceDetail')
        return RequestSwitchDetails.from_dict(base_dict)

    async def get_details(self) -> None:
        """Get switch device details."""
        # body = Helpers.req_body(self.manager, 'devicedetail')
        # body['uuid'] = self.uuid
        body = self._build_details_request()
        head = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/deviceDetail', 'post',
            headers=head, json_object=body.to_dict()
        )

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return
        resp_model = ResponseSwitchDetails.from_dict(r)
        result = resp_model.result

        self.state.device_status = result.deviceStatus
        self.state.active_time = result.activeTime
        self.state.connection_status = result.connectionStatus

    # async def get_config(self) -> None:
    #     """Get switch device configuration info."""
    #     body = Helpers.req_body(self.manager, 'devicedetail')
    #     body['method'] = 'configurations'
    #     body['uuid'] = self.uuid

    #     r_bytes, _ = await self.manager.async_call_api(
    #         '/inwallswitch/v1/device/configurations',
    #         'post',
    #         headers=Helpers.req_headers(self.manager),
    #         json_object=body,
    #     )

    #     r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
    #     if r is None:
    #         return

    #     self.config = Helpers.build_config_dict(r)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Toggle switch device."""
        if toggle is None:
            toggle = self.state.device_status != 'on'
        toggle_str = 'on' if toggle else 'off'
        # body = Helpers.req_body(self.manager, 'devicestatus')
        # body['status'] = 'on' if toggle else 'off'
        # body['uuid'] = self.uuid
        body = self._build_status_request(toggle_str)
        head = Helpers.req_headers(self.manager)

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/deviceStatus', 'post',
            headers=head, json_object=body.to_dict()
        )

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return False

        self.state.device_status = 'on' if toggle else 'off'
        self.state.connection_status = 'online'
        return True

    async def turn_off(self) -> bool:  # TO BE FIXED - combine with turn_on in toggle
        """Turn off switch device."""
        # body = Helpers.req_body(self.manager, 'devicestatus')
        # body['status'] = 'off'
        # body['uuid'] = self.uuid
        # head = Helpers.req_headers(self.manager)

        # r_bytes, _ = await self.manager.async_call_api(
        #     '/inwallswitch/v1/device/devicestatus', 'put',
        #     headers=head, json_object=body
        # )

        # r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        # if r is None:
        #     return False

        # self.device_status = 'off'
        # return True
        return await self.toggle_switch(False)

    async def turn_on(self) -> bool:
        """Turn on switch device."""
        # body = Helpers.req_body(self.manager, 'devicestatus')
        # body['status'] = 'on'
        # body['uuid'] = self.uuid
        # head = Helpers.req_headers(self.manager)

        # r_bytes, _ = await self.manager.async_call_api(
        #     '/inwallswitch/v1/device/devicestatus', 'put',
        #     headers=head, json_object=body
        # )

        # r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        # if r is None:
        #     return False

        # self.device_status = 'on'
        # return True
        return await self.toggle_switch(True)


class VeSyncDimmerSwitch(VeSyncSwitch):
    """Vesync Dimmer Switch Class with RGB Faceplate."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: SwitchMap) -> None:
        """Initilize dimmer switch class."""
        super().__init__(details, manager, feature_map)
        self.request_keys = [
            'acceptLanguage',
            'accountID',
            'appVersion',
            'cid',
            'configModule',
            'debugMode',
            'phoneBrand',
            'phoneOS',
            'timeZone',
            'token',
            'traceId',
            'userCountryCode',
            'uuid',
        ]

    def _build_request_base(self, method: str) -> dict:
        """Build the request body for dimmer switch."""
        base_dict = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        base_dict.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        base_dict.update(Helpers.get_class_attributes(self, self.request_keys))
        base_dict['configModel'] = self.config_module
        base_dict['deviceId'] = self.cid
        base_dict['method'] = method
        return base_dict

    def _build_status_request(self, status: str) -> RequestSwitchStatus:
        """Build the data model to send a status request."""
        base_dict = self._build_request_base('dimmerPowerSwitchCtl')
        base_dict['status'] = status
        return RequestSwitchStatus.from_dict(base_dict)

    def _build_details_request(self) -> RequestSwitchDetails:
        """Build the data model to send a details request."""
        base_dict = self._build_request_base('deviceDetail')
        return RequestSwitchDetails.from_dict(base_dict)

    def _build_rgb_request(
            self, status: str, color: Color | None) -> RequestSwitchStatus:
        """Build the data model to send an indicator light request."""
        base_dict = self._build_request_base('dimmerRgbValueCtl')
        base_dict['status'] = status
        if color is not None:
            base_dict['rgbValue'] = asdict(color.rgb)
            base_dict['status'] = 'on'
        return RequestSwitchStatus.from_dict(base_dict)

    def _build_brightness_request(self, brightness: int) -> RequestDimmerBrightness:
        """Build the data model to send a brightness request."""
        base_dict = self._build_request_base('dimmerBrightnessCtl')
        base_dict['brightness'] = str(brightness)
        return RequestDimmerBrightness.from_dict(base_dict)

    async def get_details(self) -> None:
        """Get dimmer switch details."""
        head = Helpers.req_header_bypass()
        body_model = self._build_details_request()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/deviceDetail', 'post',
            headers=head, json_object=body_model.to_dict()
        )

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        resp_model = ResponseDimmerDetails.from_dict(r)
        result = resp_model.result
        self.state.active_time = result.activeTime
        self.state.connection_status = result.connectionStatus
        self.state.brightness = result.brightness
        new_color = result.rgbStatus
        if isinstance(new_color, dict):
            self.state.backlight_color = Color.from_rgb(
                new_color['red'], new_color['green'], new_color['blue']
                )
        self.state.indicator_status = Helpers.string_status(result.indicatorlightStatus)
        self.state.device_status = Helpers.string_status(result.deviceStatus)

    @deprecated(
        reason="switch_toggle() deprecated, use toggle_switch(toggle: bool | None = None)"
    )
    async def switch_toggle(self, status: str) -> bool:
        """Toggle switch status."""
        return await self.toggle_switch(status == 'on')

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status == 'off'
        toggle_status = 'on' if toggle else 'off'
        # body = Helpers.req_body(self.manager, 'devicestatus')
        # body['status'] = toggle_status
        # body['uuid'] = self.uuid
        # head = Helpers.req_headers(self.manager)

        body = self._build_status_request(toggle_status)
        head = Helpers.req_header_bypass()
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/dimmerPowerSwitchCtl', 'post',
            headers=head, json_object=body.to_dict()
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
        toggle_status = 'on' if toggle else 'off'
        # body = Helpers.req_body(self.manager, 'devicestatus')
        # body['status'] = status
        # body['uuid'] = self.uuid
        # head = Helpers.req_headers(self.manager)
        body = self._build_status_request(toggle_status)
        head = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/dimmerIndicatorLightCtl',
            'post', headers=head, json_object=body.to_dict()
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
        status_str = 'on' if status else 'off'
        body = self._build_rgb_request(status_str, new_color)
        head = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            "/cloud/v1/deviceManaged/dimmerRgbValueCtl",
            "post",
            headers=head,
            json_object=body.to_dict()
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

        body = self._build_brightness_request(brightness)
        head = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/dimmerBrightnessCtl', 'post',
            headers=head, json_object=body.to_dict()
        )

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return False

        self.state.brightness = brightness
        self.state.device_status = 'on'
        self.state.connection_status = 'online'
        return True

    def displayJSON(self) -> str:
        """JSON API for dimmer switch."""
        sup_val = orjson.loads(super().displayJSON())
        if self.is_dimmable is True:  # pylint: disable=using-constant-test
            sup_val.update(
                {
                    'Indicator Light': str(self.state.active_time),
                    'Brightness': str(self.state.brightness),
                    'RGB Light': str(self.state.backlight_status),
                    'RGB Color': str(self.state.backlight_color.rgb.as_tuple()
                                     if self.state.backlight_color is not None else "None"
                                     )
                }
            )
        return orjson.dumps(
            sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
            ).decode()
