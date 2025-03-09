"""Etekcity/Valceno Smart Light Bulbs.

This module provides classes for the following Etekcity/Valceno smart lights:

    1. ESL100: Dimmable Bulb
    2. ESL100CW: Tunable White Bulb
    3. XYD0001: RGB Bulb
    4. ESL100MC: Multi-Color Bulb

The `DeviceContainer` class is used to instantiate and store bulb device instances.
These classes inherit from the `VeSyncBulb` base class, which provides common methods
and attributes for all bulb devices.
"""

from __future__ import annotations
import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING
from deprecated import deprecated
from pyvesync.base_devices.bulb_base_device import VeSyncBulb
from pyvesync.const import DeviceStatus, ConnectionStatus
from pyvesync.data_models.base_models import DefaultValues
from pyvesync.helper_utils.helpers import Helpers, Validators
from pyvesync.helper_utils.colors import Color
from pyvesync.data_models import bulb_models


if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.data_models.device_list_models import ResponseDeviceDetailsModel
    from pyvesync.device_map import BulbMap

logger = logging.getLogger(__name__)

NUMERIC_OPT = int | float | str | None
NUMERIC_STRICT = float | int | str

# --8<-- [start:feature_dict]

feature_dict: dict = {
    'ESL100':
        {
            'module': 'VeSyncBulbESL100',
            'features': ['dimmable'],
            'color_model': 'none'
        },
    'ESL100CW':
        {
            'module': 'VeSyncBulbESL100CW',
            'features': ['dimmable', 'color_temp'],
            'color_model': 'none'
        },
    'XYD0001':
        {
            'module': 'VeSyncBulbValcenoA19MC',
            'features': ['dimmable', 'color_temp', 'rgb_shift'],
            'color_model': 'hsv'
        },
    'ESL100MC':
        {
            'module': 'VeSyncBulbESL100MC',
            'features': ['dimmable', 'rgb_shift'],
            'color_model': 'rgb'
        }
}

# --8<-- [end:feature_dict]

bulb_modules: dict = {k: v['module'] for k, v in feature_dict.items()}

__all__: list = [*bulb_modules.values(), "bulb_modules"]  # noqa: PLE0604


class VeSyncBulbESL100MC(VeSyncBulb):
    """Etekcity ESL100 Multi Color Bulb device instance.

    Inherits from [VeSyncBulb][pyvesync.vesyncbulb.VeSyncBulb]
    and [VeSyncBaseDevice][pyvesync.vesyncbasedevice.VeSyncBaseDevice].

    The state of the bulb is stored in the `state` attribute, which is an instance of
    [BulbState][pyvesync.helpers.BulbState]. The `state` attribute contains all settable
    states for the bulb.

    Attributes:
        state (BulbState): State of the bulb, contains all settable states.
        device_status (str): Status of bulb, either 'on' or 'off'.
        connection_status (str): Connection status of bulb, either 'online' or 'offline'.
        details (dict): Dictionary of bulb state details.

    Notes:
        The details dictionary contains the device information retreived by the
        `update()` method:
        ```python
        details = {
            'brightness': 50,
            'colorMode': 'rgb',
            'color' : Color(red=0, green=0, blue=0)
        }
        ```
        See pyvesync.helpers.Color for more information on the Color dataclass.
    """

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: BulbMap) -> None:
        """Instantiate ESL100MC Multicolor Bulb.

        Args:
            details (dict): Dictionary of bulb state details.
            manager (VeSync): Manager class used to make API calls.
            feature_map (BulbMap): Device configuration map.
        """
        super().__init__(details, manager, feature_map)
        self.request_keys = [
            'acceptLanguage',
            'accountID',
            'appVersion',
            'cid',
            'configModule',
            'debugMode',
            'deviceRegion',
            'phoneBrand',
            'phoneOS',
            'timeZone',
            'token',
            'traceId',
        ]

    def _build_request(self, payload: dict) -> dict:
        """Generate base request body for ESL100MC."""
        default_dict = Helpers.get_class_attributes(
            DefaultValues, self.request_keys)
        default_dict.update(
            Helpers.get_class_attributes(self, self.request_keys))
        default_dict.update(
            Helpers.get_class_attributes(self.manager, self.request_keys))
        default_dict['method'] = 'bypassV2'
        payload |= {"source": "APP"}
        default_dict['payload'] = payload
        return default_dict

    async def get_details(self) -> None:
        head = Helpers.bypass_header()
        payload = {
            'method': 'getLightStatus',
            'source': 'APP',
            'data': {}
        }
        body = self._build_request(payload)

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        status = bulb_models.ResponseESL100MCStatus.from_dict(r)
        self._interpret_apicall_result(status)
        return

    def _interpret_apicall_result(
            self, response: bulb_models.ResponseESL100MCStatus) -> None:
        """Build detail dictionary from response."""
        result = response.result.result
        self.state.brightness = result.brightness
        self.state.color_mode = result.colorMode
        self.set_state("color", Color.from_rgb(
            red=result.red,
            green=result.green,
            blue=result.blue
        ))

    async def set_brightness(self, brightness: int) -> bool:
        """Set brightness of bulb.

        Calls the `set_status` method with the brightness value.

        Args:
            brightness (int): Brightness of bulb (0-100).

        Returns:
            bool: True if successful, False otherwise.
        """
        return await self.set_status(brightness=brightness)

    async def set_rgb(self,
                      red: float,
                      green: float,
                      blue: float) -> bool:
        """Set color of bulb using Red, Green and Blue values.

        Args:
            red (float): red value 0-255
            green (float): green value 0-255
            blue (float): blue value 0-255

        Returns:
            bool: True if successful, False otherwise.
        """
        return await self.set_status(red=red, green=green, blue=blue)

    async def set_hsv(self, hue: float, saturation: float, value: float) -> bool:
        """Set color of bulb using HSV values.

        Args:
            hue (float): hue value 0-360
            saturation (float): saturation value 0-100
            value (float): value (brightness) value 0-100

        Returns:
            bool: True if successful, False otherwise.
        """
        hsv = Color.from_hsv(hue=hue, saturation=saturation, value=value)
        if hsv is not None:
            return await self.set_status(
                red=hsv.rgb.red,
                green=hsv.rgb.green,
                blue=hsv.rgb.blue
                )
        logger.debug("Invalid HSV values")
        return False

    async def enable_white_mode(self) -> bool:
        """Enable white mode on bulb.

        Returns:
            bool: True if successful, False otherwise.
        """
        return await self.set_status(brightness=100)

    async def set_status(self, brightness: NUMERIC_OPT = None,
                         red: NUMERIC_OPT = None,
                         green: NUMERIC_OPT = None,
                         blue: NUMERIC_OPT = None) -> bool:
        """Set color of VeSync ESL100MC.

        Brightness or RGB values must be provided. If RGB values are provided,
        brightness is ignored.

        Args:
            brightness (float): Brightness of bulb (0-100).
            red (float): Red value of RGB color, 0-255.
            green (float): Green value of RGB color, 0-255.
            blue (float): Blue value of RGB color, 0-255.

        Returns:
            bool: True if successful, False otherwise.
        """
        brightness_update = 100
        if red is not None and green is not None and blue is not None:
            new_color = Color.from_rgb(red, green, blue)
            color_mode = 'color'
            if self.state.device_status == DeviceStatus.ON \
                    and new_color == self.state.color:
                logger.debug("New color is same as current color")
                return True
        else:
            logger.debug("RGB Values not provided")
            new_color = None
            if brightness is not None:
                if Validators.validate_zero_to_hundred(brightness):
                    brightness_update = int(brightness)
                else:
                    logger.debug("Invalid brightness value")
                    return False
                if self.state.device_status == DeviceStatus.ON \
                        and brightness_update == self.state.brightness:
                    logger.debug('Brightness already set to %s', brightness)
                    return True
                color_mode = 'white'
            else:
                logger.debug("Brightness and RGB values are not set")
                return False

        head = Helpers.bypass_header()
        # body = Helpers.bypass_body_v2(self.manager)
        # body['cid'] = self.cid
        # body['configModule'] = self.config_module

        payload = {
            'method': 'setLightStatus',
            'source': 'APP',
            'data': {
                'action': DeviceStatus.ON,
                'speed': 0,
                'brightness': brightness_update,
                'red': 0 if new_color is None else int(new_color.rgb.red),
                'green': 0 if new_color is None else int(new_color.rgb.green),
                'blue': 0 if new_color is None else int(new_color.rgb.blue),
                'colorMode': 'color' if new_color is not None else 'white',
            }
        }
        body = self._build_request(payload)

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        r = Helpers.process_dev_response(logger, "set_status", self, r_bytes)
        if r is None:
            return False

        if color_mode == 'color' and new_color is not None:
            self.state.color_mode = 'color'
            self.state.color = new_color
        elif brightness is not None:
            self.state.brightness = int(brightness_update)
            self.state.color_mode = 'white'

        self.state.device_status = DeviceStatus.ON
        return True

    @deprecated(
        "toggle() is deprecated, use toggle_switch(toggle: bool | None = None) instead"
        )
    async def toggle(self, status: str) -> bool:
        """Toggle switch of VeSync ESL100MC."""
        status_bool = status == DeviceStatus.ON
        return await self.toggle_switch(status_bool)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        head = Helpers.bypass_header()
        # body = Helpers.bypass_body_v2(self.manager)
        # body['cid'] = self.cid
        # body['configModule'] = self.config_module
        if toggle is None:
            toggle = self.state.device_status == DeviceStatus.OFF
        payload = {
            'source': 'APP',
            'method': 'setSwitch',
            'data': {
                'id': 0,
                'enabled': toggle
            }
        }
        body = self._build_request(payload)

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        r = Helpers.process_dev_response(logger, "toggle", self, r_bytes)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.ON if toggle else DeviceStatus.OFF
        return True


class VeSyncBulbESL100(VeSyncBulb):
    """Object to hold VeSync ESL100 light bulb.

    This bulb only has the dimmable feature. Inherits from pyvesync.vesyncbulb.VeSyncBulb
    and pyvesync.vesyncbasedevice.VeSyncBaseDevice.

    Attributes:
        details (dict): Dictionary of bulb state details.
        brightness (int): Brightness of bulb (0-100).
        device_status (str): Status of bulb (on/off).
        connection_status (str): Connection status of bulb (online/offline).
    """

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: BulbMap) -> None:
        """Initialize Etekcity ESL100 Dimmable Bulb.

        Args:
            details (dict): Dictionary of bulb state details.
            manager (VeSync): Manager class used to make API calls
            feature_map (DeviceMapTemplate): Device configuration map.
        """
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
            'uuid',
            'userCountryCode'
        ]

    def _build_request(self, method_dict: dict) -> dict:
        """Generate base request body for ESL100."""
        default_dict = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        default_dict.update(Helpers.get_class_attributes(self, self.request_keys))
        default_dict.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        default_dict['configModel'] = self.config_module
        default_dict['deviceId'] = self.cid
        default_dict |= method_dict

        return default_dict

    async def get_details(self) -> None:
        # body = Helpers.req_body(self.manager, 'devicedetail')
        # body['uuid'] = self.uuid
        method_dict = {
            "method": "deviceDetail",
        }
        body = self._build_request(method_dict)

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/deviceDetail',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=body,
        )

        # r_bytes, _ = await self.manager.async_call_api(
        #     '/SmartBulb/v1/device/devicedetail',
        #     'post',
        #     headers=Helpers.req_headers(self.manager),
        #     json_object=body,
        # )

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        model = bulb_models.ResponseESL100DeviceDetail.from_dict(r)
        self.state.brightness = model.result.brightness
        self.state.device_status = model.result.deviceStatus
        self.state.connection_status = model.result.connectionStatus

    @deprecated(
        "toggle() is deprecated, use toggle_switch(toggle: bool | None = None) instead"
        )
    async def toggle(self, status: str) -> bool:
        """Toggle switch of ESL100 bulb."""
        status_bool = status != DeviceStatus.ON
        return await self.toggle_switch(status_bool)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        status = DeviceStatus.ON if toggle else DeviceStatus.OFF
        # body = Helpers.req_body(self.manager, 'devicestatus')
        # body['uuid'] = self.uuid
        # body['status'] = status
        # r_bytes, _ = await self.manager.async_call_api(
        #     '/SmartBulb/v1/device/devicestatus',
        #     'put',
        #     headers=Helpers.req_headers(self.manager),
        #     json_object=body,
        # )
        method_dict = {
            "method": "smartBulbPowerSwitchCtl",
            "status": status,
        }
        body = self._build_request(method_dict)
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/smartBulbPowerSwitchCtl',
            'post',
            headers=Helpers.bypass_header(),
            json_object=body,
        )

        r = Helpers.process_dev_response(logger, "toggle", self, r_bytes)
        if r is None:
            return False

        self.state.device_status = status
        return True

    @deprecated("Use set_brightness() instead")
    async def set_status(self, brightness: int) -> bool:
        """Set brightness of dimmable bulb.

        Args:
            brightness (int): Brightness of bulb (0-100).

        Returns:
            bool: True if successful, False otherwise.
        """
        return await self.set_brightness(brightness=brightness)

    async def set_brightness(self, brightness: int) -> bool:
        """Set brightness.

        Args:
            brightness (int): brightness between 1 and 100

        Returns:
            bool: True if successful, False if not
        """
        if not self.supports_brightness:
            logger.warning('%s is not dimmable', self.device_name)
            return False
        if not Validators.validate_zero_to_hundred(brightness):
            logger.debug("Invalid brightness value")
            return False
        brightness_update = brightness
        if self.state.device_status == DeviceStatus.ON \
                and brightness_update == self.supports_brightness:
            logger.debug("Device already in requested state")
            return True

        method_dict = {
            "method": "smartBulbBrightnessCtl",
            "brightNess": str(brightness_update),
            "status": "on",
        }
        body = self._build_request(method_dict)
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/smartBulbBrightnessCtl',
            'put',
            headers=Helpers.bypass_header(),
            json_object=body,
        )

        r = Helpers.process_dev_response(logger, "set_brightness", self, r_bytes)
        if r is None:
            return False

        self.state.brightness = brightness_update
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True


class VeSyncBulbESL100CW(VeSyncBulb):
    """VeSync Tunable and Dimmable White Bulb."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: BulbMap) -> None:
        """Initialize Etekcity Tunable white bulb."""
        super().__init__(details, manager, feature_map)
        self.request_keys = [
            "acceptLanguage",
            "accountID",
            "appVersion",
            "cid",
            "configModule",
            "debugMode",
            "phoneBrand",
            "phoneOS",
            "timeZone",
            "token",
            "traceId",
            "userCountryCode",
            "uuid",
        ]

    def _build_request(self, json_cmd: dict) -> dict:
        """Generate base request body for ESL100CW."""
        default_dict = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        default_dict.update(Helpers.get_class_attributes(self, self.request_keys))
        default_dict.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        default_dict['method'] = 'bypass'
        default_dict['deviceId'] = self.cid
        default_dict['configModel'] = self.config_module
        return default_dict | json_cmd

    async def get_details(self) -> None:
        body = self._build_request({"jsonCmd": {"getLightStatus": "get"}})
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/bypass',
            'post',
            headers=Helpers.bypass_header(),
            json_object=body,
        )

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        light_resp = bulb_models.ResponseESL100CWDeviceDetail.from_dict(r)
        self._interpret_apicall_result(light_resp)

    def _interpret_apicall_result(
            self, response: bulb_models.ResponseESL100CWDeviceDetail) -> None:
        self.state.connection_status = ConnectionStatus.ONLINE
        result = response.result.light
        self.state.device_status = result.action
        self.state.brightness = result.brightness
        self.state.color_temp = result.colorTempe

    @deprecated(
        "toggle() is deprecated, use toggle_switch(toggle: bool | None = None) instead"
        )
    async def toggle(self, status: str) -> bool:
        status_bool = status == DeviceStatus.ON
        return await self.toggle_switch(status_bool)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status == DeviceStatus.OFF
        status = DeviceStatus.ON if toggle else DeviceStatus.OFF
        body = self._build_request({"jsonCmd": {"light": {"action": status}}})
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/bypass',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=body,
        )

        r = Helpers.process_dev_response(logger, "toggle", self, r_bytes)
        if r is None:
            logger.debug('%s offline', self.device_name)
            return False
        self.state.device_status = status
        return True

    async def set_brightness(self, brightness: int) -> bool:
        """Set brightness of tunable bulb."""
        return await self.set_status(brightness=brightness)

    async def set_status(self, /, brightness: int | None = None,
                         color_temp: int | None = None) -> bool:
        """Set status of tunable bulb."""
        if brightness is not None:
            if Validators.validate_zero_to_hundred(brightness):
                brightness_update = int(brightness)
            else:
                logger.debug("Invalid brightness value")
                return False
        elif self.state.brightness is not None:
            brightness_update = self.state.brightness
        else:
            brightness_update = 100
        if color_temp is not None:
            if Validators.validate_zero_to_hundred(color_temp):
                color_temp_update = color_temp
            else:
                logger.debug("Invalid color temperature value")
                return False
        elif self.state.color_temp is not None:
            color_temp_update = self.state.color_temp
        else:
            color_temp_update = 100
        if self.state.device_status == DeviceStatus.ON \
                and brightness_update == self.state.brightness \
                and color_temp_update == self.state.color_temp:
            logger.debug("Device already in requested state")
            return True
        light_dict: dict[str, NUMERIC_OPT | str] = {
            'colorTempe': color_temp_update,
            'brightness': brightness_update,
            'action': DeviceStatus.ON}
        body = self._build_request({'jsonCmd': {'light': light_dict}})
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/bypass',
            'post',
            headers=Helpers.bypass_header(),
            json_object=body,
        )

        r = Helpers.process_dev_response(logger, "set_brightness", self, r_bytes)
        if r is None:
            return False

        self.state.brightness = brightness_update
        self.state.color_temp = color_temp_update
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_color_temp(self, color_temp: int) -> bool:
        """Set Color Temperature of Bulb in pct (1 - 100)."""
        return await self.set_status(color_temp=color_temp)


class VeSyncBulbValcenoA19MC(VeSyncBulb):
    """VeSync Multicolor Bulb."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: BulbMap) -> None:
        """Initialize Multicolor bulb."""
        super().__init__(details, manager, feature_map)
        self.request_keys = [
            'acceptLanguage',
            'accountID',
            'appVersion',
            'cid',
            'configModule',
            'deviceRegion',
            'debugMode',
            'phoneBrand',
            'phoneOS',
            'timeZone',
            'token',
            'traceId',
        ]

    def _payload_base(self) -> bulb_models.ValcenoStatusPayload:
        """The payload dict for set status request.

        Avoid duplicating code and ensure that the payload dict is
        reset to its default state before each request.
        """
        payload_dict: bulb_models.ValcenoStatusPayload = {
            "force": 1,
            "brightness": '',
            "colorTemp": "",
            "colorMode": "",
            "hue": "",
            "saturation": "",
            "value": ""
        }
        return payload_dict

    def _build_request(self, payload: dict) -> dict:
        """Build request for Valceno Smart Bulb.

        The request is built from the keys in `self.request_keys` and the
        `payload` dict. The payload is then added to the request body.

        Args:
            method (str): The method to use for the request.
            payload (dict): The data to use for the payload.

        Returns:
            dict: The request body.

        Note:
            The `payload` argument is the value of request_body['payload'].
            The request structure is:
            ```json
            {
                "acceptLanguage": "en",
                "accountID": "1234567890",
                "appVersion": "1.0.0",
                "cid": "1234567890",
                "configModule": "default",
                "deviceRegion": "US",
                "debugMode": False,
                "phoneBrand": "Apple",
                "phoneOS": "iOS",
                "timeZone": "New_York",
                "token": "",
                "traceId": "",
                "payload": {
                    "method": "getLightStatusV2",
                    "source": "APP",
                    "data": {}
                }
            }
            ```
        """
        default_dict = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        default_dict.update(Helpers.get_class_attributes(self, self.request_keys))
        default_dict.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        default_dict['method'] = 'bypassV2'
        default_dict['payload'] = payload
        return default_dict

    async def _call_valceno_api(
            self, payload_method: str, payload_data: Mapping) -> bytes | None:
        """Make API call to Valceno Smart Bulb.

        Args:
            payload_method (str): The method to use for the request.
            payload_data (dict): The payload to use for the request.

        Returns:
            tuple[bytes, Any]: The response from the API call.

        Note:
            The request is built by the `_build_request` method and the payload is
            added to the request body.
            The payload structure is:
            ```json
            {
                "method": "getLightStatusV2",
                "source": "APP",
                "data": {}
                }
        """
        payload = {
            'method': payload_method,
            'source': 'APP',
            'data': payload_data
        }
        request_body = self._build_request(payload)
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=request_body,
        )
        resp = Helpers.process_dev_response(logger, payload_method, self, r_bytes)
        if resp is None:
            return None
        return r_bytes

    async def get_details(self) -> None:
        r_bytes = await self._call_valceno_api('getLightStatusV2', {})

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        status = bulb_models.ResponseValcenoStatus.from_dict(r)
        self._interpret_apicall_result(status)

    def _interpret_apicall_result(
            self, response: bulb_models.ResponseValcenoStatus) -> None:
        """Process API response with device status.

        Assigns the values to the state attributes of the device.

        Args:
            response (bulb_models.ResponseValcenoStatus): The response from the API call.
        """
        result = response.result.result
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = result.enabled
        self.state.brightness = result.brightness
        self.state.color_temp = result.colorTemp
        self.state.color_mode = result.colorMode
        hue = float(round(result.hue/250*9, 2))
        sat = float(result.saturation/100)
        val = float(result.value)
        self.state.color = Color.from_hsv(hue=hue, saturation=sat, value=val)

    @deprecated(
        "toggle() is deprecated, use toggle_switch(toggle: bool | None = None) instead"
        )
    async def toggle(self, status: str) -> bool:
        status_bool = status == DeviceStatus.ON
        return await self.toggle_switch(status_bool)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Toggle switch of VeSync Valceno A19MC."""
        if toggle is None:
            toggle = self.state.device_status == DeviceStatus.OFF

        if toggle == self.state.device_status:
            logger.debug("Device already in requested state")
            return True

        payload_data = {
                'id': 0,
                'enabled': toggle,
                }
        method = 'setSwitch'

        r_bytes = await self._call_valceno_api(method, payload_data)

        r = Helpers.process_dev_response(logger, "toggle", self, r_bytes)
        if r is None:
            self.state.connection_status = ConnectionStatus.OFFLINE
            self.state.device_status = DeviceStatus.OFF
            return False
        self.state.device_status = DeviceStatus.ON if toggle else DeviceStatus.OFF
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_rgb(self, red: float, green: float, blue: float) -> bool:
        """Set color of bulb using Red, Green and Blue values.

        All values must be provided.

        Args:
            red (float): red value 0-255
            green (float): green value 0-255
            blue (float): blue value 0-255

        Returns:
            bool: True if successful, False otherwise.
        """
        new_color = Color.from_rgb(red=red, green=green, blue=blue)
        if new_color is None:
            logger.debug("Invalid RGB values")
            return False

        return await self.set_hsv(
            hue=new_color.hsv.hue,
            saturation=new_color.hsv.saturation,
            value=new_color.hsv.value
        )

    async def set_brightness(self, brightness: int) -> bool:
        """Set brightness of multicolor bulb."""
        return await self.set_status(brightness=brightness)

    async def set_color_temp(self, color_temp: int) -> bool:
        """Set White Temperature of Bulb in pct (0 - 100)."""
        return await self.set_status(color_temp=color_temp)

    async def set_color_hue(self, color_hue: float) -> bool:
        """Set Color Hue of Bulb (0 - 360)."""
        return await self.set_status(color_hue=color_hue)

    async def set_color_saturation(self, color_saturation: float) -> bool:
        """Set Color Saturation of Bulb in pct (1 - 100)."""
        return await self.set_status(color_saturation=color_saturation)

    async def set_color_value(self, color_value: float) -> bool:
        """Set Value of multicolor bulb in pct (1 - 100)."""
        # Equivalent to brightness level, when in color mode.
        return await self.set_status(color_value=color_value)

    async def set_color_mode(self, color_mode: str) -> bool:
        """Set Color Mode of Bulb (white / hsv)."""
        return await self.set_status(color_mode=color_mode)

    async def set_hsv(self, hue: float,
                      saturation: float,
                      value: float) -> bool:
        new_color = Color.from_hsv(hue=hue, saturation=saturation, value=value)
        if new_color is None:
            logger.warning("Invalid HSV values")
            return False

        # the api expects the hsv Value in the brightness parameter
        payload_data = self._build_status_payload(
            hue=hue,
            saturation=saturation,
            value=value,
        )
        if payload_data is None:
            return False
        resp = await self._call_valceno_api("setLightStatusV2", payload_data)
        if resp is None:
            return False

        r_dict = Helpers.process_dev_response(logger, "set_hsv", self, resp)
        if r_dict is None:
            return False

        status = bulb_models.ResponseValcenoStatus.from_dict(r_dict)
        self._interpret_apicall_result(status)
        return True

    async def enable_white_mode(self) -> bool:
        """Enable white color mode."""
        return await self.set_status(color_mode='white')

    async def set_status(
        self,
        *,
        brightness: float | None = None,
        color_temp: float | None = None,
        color_hue: float | None = None,
        color_saturation: float | None = None,
        color_value: float | None = None,
        color_mode: str | None = None,
    ) -> bool:
        """Set multicolor bulb parameters.

        No arguments turns bulb on. **Kwargs only**

        Args:
            brightness (int, optional): brightness between 0 and 100
            color_temp (int, optional): color temperature between 0 and 100
            color_mode (int, optional): color mode hsv or white
            color_hue (float, optional): color hue between 0 and 360
            color_saturation (float, optional): color saturation between 0 and 100
            color_value (int, optional): color value between 0 and 100

        Returns:
            bool : True if call was successful, False otherwise
        """
        if self.state.device_status != DeviceStatus.ON:
            await self.turn_on()

        payload_data = self._build_status_payload(
            brightness=brightness,
            color_temp=color_temp,
            hue=color_hue,
            saturation=color_saturation,
            value=color_value,
            color_mode=color_mode
        )
        if payload_data == self._payload_base():
            logger.debug("No state change.")
            return False
        if payload_data is None:
            logger.debug("Invalid payload data")
            return False

        r_bytes = await self._call_valceno_api('setLightStatus', payload_data)
        if r_bytes is None:
            return False

        r_dict = Helpers.process_dev_response(logger, "set_status", self, r_bytes)
        if r_dict is None:
            return False

        r_model = bulb_models.ResponseValcenoStatus.from_dict(r_dict)
        self._interpret_apicall_result(r_model)
        return True

    def _build_color_payload(self, color_hue: float | None = None,
                             color_saturation: float | None = None,
                             color_value: float | None = None
                             ) -> bulb_models.ValcenoStatusPayload | None:
        """Create color payload for Valceno Bulbs.

        This is called by `_build_status_payload` if any of the HSV values are set.
        This should not be called directly.

        Args:
            color_hue (float, optional): Color hue of bulb (0-360).
            color_saturation (float, optional): Color saturation of bulb (0-100).
            color_value (float, optional): Color value of bulb (0-100).
        """
        payload_dict = self._payload_base()
        if color_hue is not None:
            if Validators.validate_range(color_hue, 0, 360):
                set_hue = int(color_hue * 250 / 9)
                payload_dict['hue'] = set_hue
            else:
                logger.debug("Invalid hue value %s", color_hue)
        if color_saturation is not None:
            if Validators.validate_range(color_saturation, 0, 100):
                set_sat = int(color_saturation * 100)
                payload_dict['saturation'] = set_sat
            else:
                logger.debug("Invalid saturation value %s", color_saturation)
        if color_value is not None:
            if Validators.validate_range(color_saturation, 0, 100):
                payload_dict['value'] = int(color_value)
            else:
                logger.debug("Invalid color value %s", color_value)

        # Test if any HSV values are set
        c_string = (f"{payload_dict['hue']}{payload_dict['saturation']}"
                    f"{payload_dict['value']}")
        if not c_string:
            logger.debug("Invalid HSV values")
            return None
        payload_dict['colorMode'] = 'hsv'
        payload_dict['force'] = 1
        return payload_dict

    def _build_status_payload(self,
                              brightness: float | None = None,
                              color_temp: float | None = None,
                              hue: float | None = None,
                              saturation: float | None = None,
                              value: float | None = None,
                              color_mode: str | None = None
                              ) -> bulb_models.ValcenoStatusPayload | None:
        """Create status payload data for Valceno Bulbs.

        If color_mode is set, hue, saturation and/or value must be set as well.
        If color_mode is not set, brightness and/or color_temp must be set.

        This builds the `request_body['payload']['data']` dict for api calls that
        set teh status of the bulb.

        Args:
            brightness (float, optional): Brightness of bulb (0-100).
            color_temp (float, optional): Color temperature of bulb (0-100).
            hue (float, optional): Color hue of bulb (0-360).
            saturation (float, optional): Color saturation of bulb (0-100).
            value (float, optional): Color value of bulb (0-100).
            color_mode (str, optional): Color mode of bulb ('white', 'hsv', 'color').

        Returns:
            dict | None: Payload dictionary to be sent to the API.
        """
        payload_dict = self._payload_base()
        if any(itm is not None for itm in [hue, saturation, value]):
            color_dict = self._build_color_payload(
                color_hue=hue, color_saturation=saturation, color_value=value
            )
            if color_dict is not None:
                return color_dict
            # Return None if HSV values are same as current state
            if self._check_color_state(hue=hue, saturation=saturation, value=value):
                return None
        elif color_mode in ['color', 'hsv', 'rgb']:
            logger.debug("HSV values must be provided when setting color mode.")
        else:
            if color_mode is not None:
                # if color_mode not in ['white', 'hsv']
                pass
            if color_temp is not None and Validators.validate_zero_to_hundred(color_temp):
                payload_dict['colorTemp'] = int(color_temp)
                payload_dict['colorMode'] = 'white'
            if brightness is not None and Validators.validate_zero_to_hundred(brightness):
                payload_dict['brightness'] = int(brightness)
        force_keys = ["colorTemp", "saturation", "hue", "colorMode", "value"]
        for key in force_keys:
            if payload_dict.get(key) != "":
                payload_dict["force"] = 1
        return payload_dict

    def _check_color_state(self, hue: float | None = None,
                           saturation: float | None = None,
                           value: float | None = None
                           ) -> bool:
        """Check if color state is already set.

        Returns True if color is already set, False otherwise.

        Args:
            hue (float, optional): Color hue.
            saturation (float, optional): Color saturation.
            value (float, optional): Color value.
        """
        if self.state.color is not None:
            set_hue = hue or self.state.color.hsv.hue
            set_saturation = saturation or self.state.color.hsv.saturation
            set_value = value or self.state.color.hsv.value
            set_color = Color.from_hsv(
                hue=set_hue, saturation=set_saturation, value=set_value
            )
            if self.state.device_status == DeviceStatus.ON \
                    and set_color == self.state.color:
                logger.debug("Device already set to requested color")
                return True
        return False
