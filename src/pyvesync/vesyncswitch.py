"""Classes for VeSync Switch Devices."""

import logging
import json
from abc import ABCMeta, abstractmethod
from typing import Dict, Union, Optional

from pyvesync.helpers import Helpers as helpers
from pyvesync.vesyncbasedevice import VeSyncBaseDevice

logger = logging.getLogger(__name__)

feature_dict: Dict[str, Dict[str, Union[list, str]]] = {
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

switch_modules: dict = {k: v['module']
                        for k, v in feature_dict.items()}

__all__: list = list(switch_modules.values()) + ['switch_modules']


class VeSyncSwitch(VeSyncBaseDevice):
    """Etekcity Switch Base Class."""

    __metaclasss__ = ABCMeta

    def __init__(self, details, manager):
        """Initialize Switch Base Class."""
        super().__init__(details, manager)
        self.features = feature_dict.get(self.device_type, {}).get('features')
        if self.features is None:
            logger.error('% device configuration not set', self.device_name)
            raise KeyError(f'Device configuration not set {self.device_name}')
        self.details = {}

    def is_dimmable(self) -> bool:
        """Return True if switch is dimmable."""
        return bool('dimmable' in self.features)

    @abstractmethod
    def get_details(self) -> None:
        """Get Device Details."""

    @abstractmethod
    def turn_on(self) -> bool:
        """Turn Switch On."""

    @abstractmethod
    def turn_off(self) -> bool:
        """Turn switch off."""

    @abstractmethod
    def get_config(self) -> None:
        """Get configuration and firmware deatils."""

    @property
    def active_time(self) -> int:
        """Get active time of switch."""
        return self.details.get('active_time', 0)

    def update(self) -> None:
        """Update device details."""
        self.get_details()


class VeSyncWallSwitch(VeSyncSwitch):
    """Etekcity standard wall switch class."""

    def __init__(self, details, manager):
        """Initialize standard etekcity wall switch class."""
        super().__init__(details, manager)

    def get_details(self) -> None:
        """Get switch device details."""
        body = helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/inwallswitch/v1/device/devicedetail', 'post',
            headers=head, json_object=body
        )

        if r is not None and helpers.code_check(r):
            self.device_status = r.get('deviceStatus', self.device_status)
            self.details['active_time'] = r.get('activeTime', 0)
            self.connection_status = r.get(
                'connectionStatus', self.connection_status)
        else:
            logger.debug('Error getting %s details', self.device_name)

    def get_config(self) -> None:
        """Get switch device configuration info."""
        body = helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/inwallswitch/v1/device/configurations',
            'post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )

        if helpers.code_check(r):
            self.config = helpers.build_config_dict(r)
        else:
            logger.warning('Unable to get %s config info',
                           self.device_name)

    def turn_off(self) -> bool:
        """Turn off switch device."""
        body = helpers.req_body(self.manager, 'devicestatus')
        body['status'] = 'off'
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/inwallswitch/v1/device/devicestatus', 'put',
            headers=head, json_object=body
        )

        if r is not None and helpers.code_check(r):
            self.device_status = 'off'
            return True
        logger.warning('Error turning %s off', self.device_name)
        return False

    def turn_on(self) -> bool:
        """Turn on switch device."""
        body = helpers.req_body(self.manager, 'devicestatus')
        body['status'] = 'on'
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/inwallswitch/v1/device/devicestatus', 'put',
            headers=head, json_object=body
        )

        if r is not None and helpers.code_check(r):
            self.device_status = 'on'
            return True
        logger.warning('Error turning %s on', self.device_name)
        return False


class VeSyncDimmerSwitch(VeSyncSwitch):
    """Vesync Dimmer Switch Class with RGB Faceplate."""

    def __init__(self, details, manager):
        """Initilize dimmer switch class."""
        super().__init__(details, manager)
        self._brightness = 0
        self._rgb_value = {'red': 0, 'blue': 0, 'green': 0}
        self._rgb_status = 'unknown'
        self._indicator_light = 'unknown'

    def get_details(self) -> None:
        """Get dimmer switch details."""
        body = helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/dimmer/v1/device/devicedetail', 'post',
            headers=head, json_object=body
        )

        if r is not None and helpers.code_check(r):
            self.device_status = r.get('deviceStatus', self.device_status)
            self.details['active_time'] = r.get('activeTime', 0)
            self.connection_status = r.get(
                'connectionStatus', self.connection_status)
            self._brightness = r.get('brightness')
            self._rgb_status = r.get('rgbStatus')
            self._rgb_value = r.get('rgbValue')
            self._indicator_light = r.get('indicatorlightStatus')
        else:
            logger.debug('Error getting %s details', self.device_name)

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

    def switch_toggle(self, status: str) -> bool:
        """Toggle switch status."""
        if status not in ['on', 'off']:
            logger.debug('Invalid status passed to wall switch')
            return False
        body = helpers.req_body(self.manager, 'devicestatus')
        body['status'] = status
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/dimmer/v1/device/devicestatus', 'put',
            headers=head, json_object=body
        )

        if r is not None and helpers.code_check(r):
            self.device_status = status
            return True

        logger.warning('Error turning %s %s',
                       self.device_name, status)
        return False

    def turn_on(self) -> bool:
        """Turn switch on."""
        return self.switch_toggle('on')

    def turn_off(self) -> bool:
        """Turn switch off."""
        return self.switch_toggle('off')

    def indicator_light_toggle(self, status: str) -> bool:
        """Toggle indicator light."""
        if status not in ['on', 'off']:
            logger.debug('Invalid status for wall switch')
            return False
        body = helpers.req_body(self.manager, 'devicestatus')
        body['status'] = status
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)

        r, _ = helpers.call_api(
            '/dimmer/v1/device/indicatorlightstatus',
            'put', headers=head, json_object=body
        )

        if r is not None and helpers.code_check(r):
            self.device_status = status
            return True

        logger.warning('Error turning %s indicator light %s',
                       self.device_name, status)
        return False

    def indicator_light_on(self) -> bool:
        """Turn Indicator light on."""
        return self.indicator_light_toggle('on')

    def indicator_light_off(self) -> bool:
        """Turn indicator light off."""
        return self.indicator_light_toggle('off')

    def rgb_color_status(self, status: str,
                         red: Optional[int] = None,
                         blue: Optional[int] = None,
                         green: Optional[int] = None) -> bool:
        """Set faceplate RGB color."""
        body = helpers.req_body(self.manager, 'devicestatus')
        body['status'] = status
        body['uuid'] = self.uuid
        head = helpers.req_headers(self.manager)
        if red is not None and blue is not None and green is not None:
            body['rgbValue'] = {'red': red, 'blue': blue, 'green': green}

        r, _ = helpers.call_api(
            '/dimmer/v1/device/devicergbstatus', 'put',
            headers=head, json_object=body
        )

        if r is not None and helpers.code_check(r):
            self._rgb_status = status
            if body.get('rgbValue') is not None:
                self._rgb_value = {'red': red, 'blue': blue, 'green': green}
            return True
        logger.warning('Error turning %s off', self.device_name)
        return False

    def rgb_color_off(self) -> bool:
        """Turn RGB Color Off."""
        return self.rgb_color_status('off')

    def rgb_color_on(self) -> bool:
        """Turn RGB Color Off."""
        return self.rgb_color_status('on')

    def rgb_color_set(self, red: int, green: int, blue: int) -> bool:
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

            return bool(self.rgb_color_status('on', red, green, blue))
        return False

    def set_brightness(self, brightness: int) -> bool:
        """Set brightness of dimmer - 1 - 100."""
        if isinstance(brightness, int) and (
                brightness > 0 or brightness <= 100):

            body = helpers.req_body(self.manager, 'devicestatus')
            body['brightness'] = brightness
            body['uuid'] = self.uuid
            head = helpers.req_headers(self.manager)

            r, _ = helpers.call_api(
                '/dimmer/v1/device/updatebrightness', 'put',
                headers=head, json_object=body
            )

            if r is not None and helpers.code_check(r):
                self._brightness = brightness
                return True
            logger.warning('Error setting %s brightness', self.device_name)
        else:
            logger.warning('Invalid brightness')
        return False

    def displayJSON(self) -> str:
        """JSON API for dimmer switch."""
        sup_val = json.loads(super().displayJSON())
        if self.is_dimmable is True:  # pylint: disable=using-constant-test
            sup_val.update(
                {
                    'Indicator Light': str(self.active_time),
                    'Brightness': str(self._brightness),
                    'RGB Light': str(self._rgb_status),
                }
            )
        return json.dumps(sup_val, indent=4)

    def get_config(self) -> None:
        """Get dimmable switch device configuration info."""
        body = helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/dimmer/v1/device/configurations',
            'post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )

        if helpers.code_check(r):
            self.config = helpers.build_config_dict(r)
        else:
            logger.warning('Unable to get %s config info', self.device_name)
