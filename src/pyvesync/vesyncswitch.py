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

import logging
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING
import orjson

from pyvesync.helpers import Helpers
from pyvesync.vesyncbasedevice import VeSyncBaseDevice

if TYPE_CHECKING:
    from pyvesync import VeSync

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


class VeSyncSwitch(VeSyncBaseDevice):
    """Etekcity Switch Base Class.

    Abstract Base Class for Etekcity Switch Devices, inherting from
    pyvesync.vesyncbasedevice.VeSyncBaseDevice. Should not be instantiated directly,
    subclassed by VeSyncWallSwitch and VeSyncDimmerSwitch.

    Attributes:
        features (list): List of features supported by the switch device.
        details (dict): Dictionary of switch device details.
    """

    __metaclasss__ = ABCMeta

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initialize Switch Base Class."""
        super().__init__(details, manager)
        self.features = feature_dict.get(self.device_type, {}).get('features', [])
        if self.features is None:
            logger.error('% device configuration not set', self.device_name)
            raise KeyError(f'Device configuration not set {self.device_name}')
        self.details: dict = {}

    def is_dimmable(self) -> bool:
        """Return True if switch is dimmable."""
        return bool('dimmable' in self.features)

    @abstractmethod
    async def get_details(self) -> None:
        """Get Device Details."""

    @abstractmethod
    async def turn_on(self) -> bool:
        """Turn Switch On."""

    @abstractmethod
    async def turn_off(self) -> bool:
        """Turn switch off."""

    @abstractmethod
    async def get_config(self) -> None:
        """Get configuration and firmware deatils."""

    @property
    def active_time(self) -> int:
        """Get active time of switch."""
        return self.details.get('active_time', 0)

    async def update(self) -> None:
        """Update device details."""
        await self.get_details()


class VeSyncWallSwitch(VeSyncSwitch):
    """Etekcity standard wall switch class."""

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initialize standard etekcity wall switch class."""
        super().__init__(details, manager)

    async def get_details(self) -> None:
        """Get switch device details."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        head = Helpers.req_headers(self.manager)

        r_bytes, _ = await self.manager.call_api(
            '/inwallswitch/v1/device/devicedetail', 'post',
            headers=head, json_object=body
        )

        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        self.device_status = r.get('deviceStatus', self.device_status)
        self.details['active_time'] = r.get('activeTime', 0)
        self.connection_status = r.get(
            'connectionStatus', self.connection_status)

    async def get_config(self) -> None:
        """Get switch device configuration info."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/inwallswitch/v1/device/configurations',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )

        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        self.config = Helpers.build_config_dict(r)

    async def turn_off(self) -> bool:  # TO BE FIXED - combine with turn_on in toggle
        """Turn off switch device."""
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['status'] = 'off'
        body['uuid'] = self.uuid
        head = Helpers.req_headers(self.manager)

        r_bytes, _ = await self.manager.call_api(
            '/inwallswitch/v1/device/devicestatus', 'put',
            headers=head, json_object=body
        )

        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return False

        self.device_status = 'off'
        return True

    async def turn_on(self) -> bool:
        """Turn on switch device."""
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['status'] = 'on'
        body['uuid'] = self.uuid
        head = Helpers.req_headers(self.manager)

        r_bytes, _ = await self.manager.call_api(
            '/inwallswitch/v1/device/devicestatus', 'put',
            headers=head, json_object=body
        )

        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return False

        self.device_status = 'on'
        return True


class VeSyncDimmerSwitch(VeSyncSwitch):
    """Vesync Dimmer Switch Class with RGB Faceplate."""

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initilize dimmer switch class."""
        super().__init__(details, manager)
        self._brightness = 0
        self._rgb_value = {'red': 0, 'blue': 0, 'green': 0}
        self._rgb_status = 'unknown'
        self._indicator_light = 'unknown'

    async def get_details(self) -> None:
        """Get dimmer switch details."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        head = Helpers.req_headers(self.manager)

        r_bytes, _ = await self.manager.call_api(
            '/dimmer/v1/device/devicedetail', 'post',
            headers=head, json_object=body
        )

        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        self.device_status = r.get('deviceStatus', self.device_status)
        self.details['active_time'] = r.get('activeTime', 0)
        self.connection_status = r.get(
            'connectionStatus', self.connection_status)
        self._brightness = r.get('brightness')
        self._rgb_status = r.get('rgbStatus')
        self._rgb_value = r.get('rgbValue')
        self._indicator_light = r.get('indicatorlightStatus')

    @property
    def brightness(self) -> float:
        """Return brightness in percent."""
        return self._brightness

    @property
    def indicator_light_status(self) -> str:
        """Faceplate brightness light status."""
        return self._indicator_light

    @property
    def rgb_light_status(self) -> str:
        """RGB Faceplate light status."""
        return self._rgb_status

    @property
    def rgb_light_value(self) -> dict:
        """RGB Light Values."""
        return self._rgb_value

    async def switch_toggle(self, status: str) -> bool:
        """Toggle switch status."""
        if status not in ['on', 'off']:
            logger.debug('Invalid status passed to wall switch')
            return False
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['status'] = status
        body['uuid'] = self.uuid
        head = Helpers.req_headers(self.manager)

        r_bytes, _ = await self.manager.call_api(
            '/dimmer/v1/device/devicestatus', 'put',
            headers=head, json_object=body
        )

        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return False

        self.device_status = status
        return True

    async def turn_on(self) -> bool:
        """Turn switch on."""
        return await self.switch_toggle('on')

    async def turn_off(self) -> bool:
        """Turn switch off."""
        return await self.switch_toggle('off')

    async def indicator_light_toggle(self, status: str) -> bool:
        """Toggle indicator light."""
        if status not in ['on', 'off']:
            logger.debug('Invalid status for wall switch')
            return False
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['status'] = status
        body['uuid'] = self.uuid
        head = Helpers.req_headers(self.manager)

        r_bytes, _ = await self.manager.call_api(
            '/dimmer/v1/device/indicatorlightstatus',
            'put', headers=head, json_object=body
        )

        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return False

        self.device_status = status
        return True

    async def indicator_light_on(self) -> bool:
        """Turn Indicator light on."""
        return await self.indicator_light_toggle('on')

    async def indicator_light_off(self) -> bool:
        """Turn indicator light off."""
        return await self.indicator_light_toggle('off')

    async def rgb_color_status(
        self,
        status: str,
        red: int | None = None,
        blue: int | None = None,
        green: int | None = None,
    ) -> bool:
        """Set faceplate RGB color."""
        body = Helpers.req_body(self.manager, "devicestatus")
        body["status"] = status
        body["uuid"] = self.uuid
        head = Helpers.req_headers(self.manager)
        if red is not None and blue is not None and green is not None:
            body["rgbValue"] = {"red": red, "blue": blue, "green": green}

        r_bytes, _ = await self.manager.call_api(
            "/dimmer/v1/device/devicergbstatus", "put", headers=head, json_object=body
        )

        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return False

        self._rgb_status = status
        if (
            body.get("rgbValue") is not None
            and red is not None
            and blue is not None
            and green is not None
        ):
            self._rgb_value = {"red": red, "blue": blue, "green": green}
        return True

    async def rgb_color_off(self) -> bool:
        """Turn RGB Color Off."""
        return await self.rgb_color_status('off')

    async def rgb_color_on(self) -> bool:
        """Turn RGB Color Off."""
        return await self.rgb_color_status('on')

    async def rgb_color_set(self, red: int, green: int, blue: int) -> bool:
        """Set RGB color of faceplate."""
        try:
            red = int(red)
            green = int(green)
            blue = int(blue)
        except ValueError:
            return False
        if isinstance(red, int) and isinstance(
                green, int) and isinstance(blue, int):
            for color in [red, green, blue]:
                if color < 0 or color > 255:
                    logger.warning('Invalid RGB value')
                    return False

            return bool(await self.rgb_color_status('on', red, green, blue))
        return False

    async def set_brightness(self, brightness: int) -> bool:
        """Set brightness of dimmer - 1 - 100."""
        if isinstance(brightness, int) and (
                brightness > 0 or brightness <= 100):

            body = Helpers.req_body(self.manager, 'devicestatus')
            body['brightness'] = brightness
            body['uuid'] = self.uuid
            head = Helpers.req_headers(self.manager)

            r_bytes, _ = await self.manager.call_api(
                '/dimmer/v1/device/updatebrightness', 'put',
                headers=head, json_object=body
            )

            r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
            if r is None:
                return False

            self._brightness = brightness
            return True
        logger.warning('Invalid brightness')
        return False

    def displayJSON(self) -> str:
        """JSON API for dimmer switch."""
        sup_val = orjson.loads(super().displayJSON())
        if self.is_dimmable is True:  # pylint: disable=using-constant-test
            sup_val.update(
                {
                    'Indicator Light': str(self.active_time),
                    'Brightness': str(self._brightness),
                    'RGB Light': str(self._rgb_status),
                }
            )
        return orjson.dumps(
            sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
            ).decode()

    async def get_config(self) -> None:
        """Get dimmable switch device configuration info."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/dimmer/v1/device/configurations',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )

        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        self.config = Helpers.build_config_dict(r)
