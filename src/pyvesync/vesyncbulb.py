"""Etekcity/Valceno Smart Light Bulbs."""

import logging
import json
from typing import Union, Dict, Optional, NamedTuple
from abc import ABCMeta, abstractmethod
from pyvesync.helpers import Helpers as helpers, Color
from pyvesync.vesyncbasedevice import VeSyncBaseDevice


logger = logging.getLogger(__name__)

NUMERIC_T = Optional[Union[int, float, str]]

# Possible features - dimmable, color_temp, rgb_shift
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


bulb_modules: dict = {k: v['module'] for k, v in feature_dict.items()}

__all__: list = list(bulb_modules.values()) + ['bulb_modules']


def pct_to_kelvin(pct: float, max_k: int = 6500, min_k: int = 2700) -> float:
    """Convert percent to kelvin."""
    kelvin = ((max_k - min_k) * pct / 100) + min_k
    return kelvin


class VeSyncBulb(VeSyncBaseDevice):
    """Base class for VeSync Bulbs."""

    __metaclass__ = ABCMeta

    def __init__(self, details: Dict[str, Union[str, list]],
                 manager):
        """Initialize VeSync smart bulb base class."""
        super().__init__(details, manager)
        self._brightness = int(0)
        self._color_temp = int(0)
        self._color_value = float(0)
        self._color_hue = float(0)
        self._color_saturation = float(0)
        self._color_mode: str = ''   # possible: white, color, hsv
        self._color: Optional[Color] = None
        self.features: Optional[list] = feature_dict.get(
            self.device_type, {}).get('features')
        if self.features is None:
            logger.error("No configuration set for - %s", self.device_name)
            raise KeyError(f"No configuration set for {self.device_name}")
        self._rgb_values = {
            'red': 0,
            'green': 0,
            'blue': 0
        }
    # self.get_config()
    # self.current_firm_version = self.config.get('currentFirmVersion', None)
    # self.latest_firm_version = self.config.get('latestFirmVersion', None)
    # self.firmware_url = self.config.get('firmwareUrl', None)

    @property
    def brightness(self) -> int:
        """Return brightness of vesync bulb."""
        if self.dimmable_feature and self._brightness is not None:
            return self._brightness
        return 0

    @property
    def color_temp_kelvin(self) -> int:
        """Return white color temperature of bulb in Kelvin."""
        if self.color_temp_feature and self._color_temp is not None:
            return int(pct_to_kelvin(self._color_temp))
        return 0

    @property
    def color_temp_pct(self) -> int:
        """Return white color temperature of bulb in percent (0-100)."""
        if self.color_temp_feature and self._color_temp is not None:
            return int(self._color_temp)
        return 0

    @property
    def color_hue(self) -> float:
        """Return color hue of bulb. (from 0 to 360)."""
        if self.rgb_shift_feature and self._color is not None:
            return self._color.hsv.hue
        return 0

    @property
    def color_saturation(self) -> float:
        """Return color saturation of bulb in percent (0-100)."""
        if self.rgb_shift_feature and self._color is not None:
            return self._color.hsv.saturation
        return 0

    @property
    def color_value(self) -> float:
        """Return color value of bulb in percent (0-100)."""
        if self.rgb_shift_feature and self._color is not None:
            return self._color.hsv.value
        return 0

    @property
    def color(self) -> Optional[Color]:
        """Return color of bulb in the form of a dataclass with two attributes.

        self.color.hsv -> (NamedTuple) Hue: float 0-360,
            Saturation: float 0-100 and Value: float 0-100
        self.color.rgb -> (NamedTuple) Red: float 0-255,
            Green: float 0-255 and Blue: float 0-255
        """
        if self.rgb_shift_feature is True and self._color is not None:
            return self._color
        return None

    @color.setter
    def color(self, red: Optional[float] = None,
              green: Optional[float] = None,
              blue: Optional[float] = None,
              hue: Optional[float] = None,
              saturation: Optional[float] = None,
              value: Optional[float] = None) -> None:
        self._color = Color(red=red, green=green, blue=blue,
                            hue=hue, saturation=saturation, value=value)

    @property
    def color_hsv(self) -> Optional[NamedTuple]:
        """Return color of bulb in hsv."""
        if self.rgb_shift_feature is True and self._color is not None:
            return self._color.hsv
        return None

    @property
    def color_rgb(self) -> Optional[NamedTuple]:
        """Return color of bulb in rgb."""
        if self.rgb_shift_feature is True and self._color is not None:
            return self._color.rgb
        return None

    @property
    def color_mode(self) -> Optional[str]:
        """Return color mode of bulb."""  # { white, hsv }
        if self.rgb_shift_feature and self._color_mode is not None:
            return str(self._color_mode)
        return None

    @property
    def dimmable_feature(self) -> bool:
        """Return true if dimmable bulb."""
        if self.features is not None and 'dimmable' in self.features:
            return True
        return False

    @property
    def color_temp_feature(self) -> bool:
        """Return true if bulb supports white color temperature changes."""
        if self.features is not None and 'color_temp' in self.features:
            return True
        return False

    @property
    def rgb_shift_feature(self) -> bool:
        """Return True if bulb supports changing color (RGB)."""
        if self.features is not None and 'rgb_shift' in self.features:
            return True
        return False

    def _validate_rgb(self, red: NUMERIC_T = None,
                      green: NUMERIC_T = None,
                      blue: NUMERIC_T = None) -> Color:
        """Validate RGB values."""
        rgb_dict = {'red': red, 'green': green, 'blue': blue}
        for clr, val in rgb_dict.items():
            if val is None:
                rgb_dict[clr] = getattr(self._rgb_values, clr)
            else:
                rgb_dict[clr] = val
        return Color(red=rgb_dict['red'],
                     green=rgb_dict['green'],
                     blue=rgb_dict['blue'])

    def _validate_hsv(self, hue: Optional[NUMERIC_T] = None,
                      saturation: Optional[NUMERIC_T] = None,
                      value: Optional[NUMERIC_T] = None) -> Color:
        """Validate HSV Arguments."""
        hsv_dict = {'hue': hue, 'saturation': saturation, 'value': value}
        for clr, val in hsv_dict.items():
            if val is None:
                if self._color is not None:
                    hsv_dict[clr] = getattr(self._color.hsv, clr)

        if hue is not None:
            valid_hue = self._validate_any(hue, 1, 360, 360)
        else:
            if self._color is not None:
                valid_hue = self._color.hsv.hue
            else:
                logger.debug("No current hue value, setting to 0")
                valid_hue = 360
        hsv_dict['hue'] = valid_hue
        for itm, val in {'saturation': saturation, 'value': value}.items():
            if val is not None:
                valid_item = self._validate_any(val, 1, 100, 100)
            else:
                if self.color is not None:
                    valid_item = getattr(self.color.hsv, itm)
                else:
                    logger.debug("No current %s value, setting to 0", itm)
                    valid_item = 100
            hsv_dict[itm] = valid_item
        return Color(hue=hsv_dict['hue'], saturation=hsv_dict['saturation'],
                     value=hsv_dict['value'])

    def _validate_brightness(self, brightness: Union[int, float, str],
                             start: int = 0, stop: int = 100) -> int:
        """Validate brightness value."""
        try:
            brightness_update: int = max(start, (min(stop, int(
                                                round(float(brightness), 2)))))
        except (ValueError, TypeError):
            if self._brightness is not None:
                brightness_update = self.brightness
            else:
                brightness_update = 100
        return brightness_update

    def _validate_color_temp(self, temp: int, start: int = 0, stop: int = 100):
        """Validate color temperature."""
        try:
            temp_update = max(start, (min(stop, int(
                round(float(temp), 0)))))
        except (ValueError, TypeError):
            if self._color_temp is not None:
                temp_update = self._color_temp
            else:
                temp_update = 100
        return temp_update

    @staticmethod
    def _validate_any(value: Union[int, float, str],
                      start: Union[int, float] = 0,
                      stop: Union[int, float] = 100,
                      default: Union[int, float] = 100) -> float:
        """Validate any value."""
        try:
            value_update = max(float(start), (min(float(stop), round(float(value), 2))))
        except (ValueError, TypeError):
            value_update = default
        return value_update

    @abstractmethod
    def set_status(self) -> bool:
        """Set vesync bulb attributes(brightness, color_temp, etc)."""

    @abstractmethod
    def get_details(self) -> None:
        """Get vesync bulb details."""

    @abstractmethod
    def _interpret_apicall_result(self, response) -> None:
        """Update bulb status from any api call response."""

    @abstractmethod
    def toggle(self, status: str) -> bool:
        """Toggle vesync lightbulb."""

    @abstractmethod
    def get_config(self) -> None:
        """Call api to get configuration details and firmware."""
        pass

    def set_hsv(self, hue, saturation, value):
        """Set HSV if supported by bulb.

        Hue 0-360, Saturation 0-100, Value 0-100.
        """
        if self.rgb_shift_feature is False:
            logger.debug("HSV not supported by bulb")
            return False

    def set_rgb(self, red: Optional[float] = None,
                green: Optional[float] = None,
                blue: Optional[float] = None) -> bool:
        """Set RGB if supported by bulb. Red 0-255, Green 0-255, Blue 0-255."""
        if self.rgb_shift_feature is False:
            logger.debug("RGB not supported by bulb")
            return False
        return True

    def turn_on(self) -> bool:
        """Turn on vesync bulbs."""
        if self.toggle('on'):
            self.device_status = 'on'
            return True
        logger.warning('Error turning %s on', self.device_name)
        return False

    def turn_off(self) -> bool:
        """Turn off vesync bulbs."""
        if self.toggle('off'):
            self.device_status = 'off'
            return True
        logger.warning('Error turning %s off', self.device_name)
        return False

    def update(self) -> None:
        """Update bulb details."""
        self.get_details()

    def display(self) -> None:
        """Return formatted bulb info to stdout."""
        super().display()
        if self.connection_status == 'online':
            disp = []  # initiate list
            if self.dimmable_feature:
                disp.append(('Brightness: ', str(self.brightness), '%'))
            if self.color_temp_feature:
                disp.append(('White Temperature Pct: ',
                             str(self.color_temp_pct), '%'))
                disp.append(('White Temperature Kelvin: ',
                             str(self.color_temp_kelvin), 'K'))
            if self.rgb_shift_feature and self.color is not None:
                disp.append(('ColorHSV: ', helpers.named_tuple_to_str(
                    self.color.hsv), ''))
                disp.append(('ColorRGB: ', helpers.named_tuple_to_str(
                    self.color.rgb), ''))
                disp.append(('ColorMode: ', str(self.color_mode), ''))
            if len(disp) > 0:
                for line in disp:
                    print(f'{line[0]:.<30} {line[1]} {line[2]}')

    def displayJSON(self) -> str:
        """Return bulb device info in JSON format."""
        sup = super().displayJSON()
        sup_val = json.loads(sup)
        if self.connection_status == 'online':
            if self.dimmable_feature:
                sup_val.update({'Brightness': str(self.brightness)})
            if self.color_temp_feature:
                sup_val.update(
                    {'WhiteTemperaturePct': str(self.color_temp_pct)})
                sup_val.update(
                    {'WhiteTemperatureKelvin': str(self.color_temp_kelvin)})
            if self.rgb_shift_feature:
                if self.color_hsv is not None:
                    sup_val.update({'ColorHSV': json.dumps(
                        self.color_hsv._asdict())})
                if self.color_rgb is not None:
                    sup_val.update({'ColorRGB': json.dumps(
                        self.color_rgb._asdict())})
                sup_val.update({'ColorMode': str(self.color_mode)})
        return json.dumps(sup_val, indent=4)

    @property
    def color_value_rgb(self) -> Optional[NamedTuple]:
        """Legacy Method .... Depreciated."""
        if self._color is not None:
            return self._color.rgb
        return None

    @property
    def color_value_hsv(self) -> Optional[NamedTuple]:
        """Legacy Method .... Depreciated."""
        if self._color is not None:
            return self._color.hsv
        return None


class VeSyncBulbESL100MC(VeSyncBulb):
    """Etekcity ESL100 Multi Color Bulb."""

    def __init__(self, details: Dict[str, Union[str, list]], manager):
        """Instantiate ESL100MC Multicolor Bulb."""
        super().__init__(details, manager)
        self.details: dict = {}

    def get_details(self) -> None:
        """Get ESL100MC Details."""
        head = helpers.bypass_header()
        body = helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': 'getLightStatus',
            'source': 'APP',
            'data': {}
        }

        r, _ = helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        if not isinstance(r, dict) or not isinstance(r.get('result'), dict) \
                or r.get('code') != 0:
            logger.debug("Error in bulb response")
            return
        outer_result = r.get('result', {})
        inner_result = outer_result.get('result')

        if inner_result is None or outer_result.get('code') != 0:
            logger.debug("No status data in bulb response")
            return
        self._interpret_apicall_result(inner_result)
        return

    def _interpret_apicall_result(self, response: dict):
        """Build detail dictionary from response."""
        self._brightness = response.get('brightness', 0)
        self._color_mode = response.get('colorMode', '')
        self._color = Color(red=response.get('red', 0),
                            green=response.get('green', 0),
                            blue=response.get('blue', 0))
        return True

    def set_brightness(self, brightness: int) -> bool:
        """Set brightness of bulb."""
        return self.set_status(brightness=brightness)

    def set_rgb_color(self, red: float, green: float, blue: float) -> bool:
        """Set RGB Color of bulb."""
        return self.set_status(red=red, green=green, blue=blue)

    def set_rgb(self, red: Optional[float] = None,
                green: Optional[float] = None,
                blue: Optional[float] = None) -> bool:
        """Set RGB Color of bulb."""
        return self.set_status(red=red, green=green, blue=blue)

    def set_hsv(self, hue, saturation, value):
        """Set HSV Color of bulb."""
        rgb = Color(hue=hue, saturation=saturation, value=value).rgb
        return self.set_status(red=rgb.red, green=rgb.green, blue=rgb.blue)

    def enable_white_mode(self) -> bool:
        """Enable white mode on bulb."""
        return self.set_status(brightness=100)

    def set_status(self, brightness: Optional[NUMERIC_T] = None,
                   red: Optional[NUMERIC_T] = None,
                   green: Optional[NUMERIC_T] = None,
                   blue: Optional[NUMERIC_T] = None) -> bool:
        """Set status of VeSync ESL100MC."""
        brightness_update = 100
        if red is not None and green is not None and blue is not None:
            new_color = self._validate_rgb(red, green, blue)
            color_mode = 'color'
            if self.device_status == 'on' and new_color == self._color:
                logger.debug("New color is same as current color")
                return True
        else:
            logger.debug("RGB Values not provided")
            new_color = None
            if brightness is not None:
                brightness_update = int(self._validate_brightness(brightness))
                # Do nothing if brightness is passed and same as current
                if self.device_status == 'on' and brightness_update == self._brightness:
                    logger.debug('Brightness already set to %s', brightness)
                    return True
                color_mode = 'white'
            else:
                logger.debug("Brightness and RGB values are not set")
                return False

        head = helpers.bypass_header()
        body = helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': 'setLightStatus',
            'source': 'APP',
            'data': {
                'action': 'on',
                'speed': 0,
                'brightness': brightness_update,
                'red': 0 if new_color is None else int(new_color.rgb.red),
                'green': 0 if new_color is None else int(new_color.rgb.green),
                'blue': 0 if new_color is None else int(new_color.rgb.blue),
                'colorMode': 'color' if new_color is not None else 'white',
            }
        }

        r, _ = helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        if not isinstance(r, dict) or r.get('code') != 0:
            logger.debug("Error in setting bulb status")
            return False

        if color_mode == 'color' and new_color is not None:
            self._color_mode = 'color'
            self._color = Color(red=new_color.rgb.red,
                                green=new_color.rgb.green,
                                blue=new_color.rgb.blue)
        elif brightness is not None:
            self._brightness = int(brightness_update)
            self._color_mode = 'white'

        self.device_status = 'on'
        return True

    def toggle(self, status: str) -> bool:
        """Toggle bulb status."""
        if status == 'on':
            turn_on = True
        elif status == 'off':
            turn_on = False
        else:
            logger.debug("Status must be on or off")
            return False
        head = helpers.bypass_header()
        body = helpers.bypass_body_v2(self.manager)
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'source': 'APP',
            'method': 'setSwitch',
            'data': {
                'id': 0,
                'enabled': turn_on
            }
        }
        r, _ = helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )
        if not isinstance(r, dict) or r.get('code') != 0:
            logger.debug("Error in setting bulb status")
            return False
        if turn_on is True:
            self.device_status = 'on'
        else:
            self.device_status = 'off'
        return True


class VeSyncBulbESL100(VeSyncBulb):
    """Object to hold VeSync ESL100 light bulb."""

    def __init__(self, details: dict, manager) -> None:
        """Initialize Etekcity ESL100 Dimmable Bulb."""
        super().__init__(details, manager)
        self.details: dict = {}

    def get_details(self) -> None:
        """Get details of dimmable bulb."""
        body = helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        r, _ = helpers.call_api(
            '/SmartBulb/v1/device/devicedetail',
            'post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )
        if helpers.code_check(r):
            self.connection_status = r.get('connectionStatus')
            self.device_status = r.get('deviceStatus')
            if self.dimmable_feature:
                self._brightness = int(r.get('brightNess'))
        else:
            logger.debug('Error getting %s details', self.device_name)

    def get_config(self) -> None:
        """Get configuration of dimmable bulb."""
        body = helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/SmartBulb/v1/device/configurations',
            'post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )

        if helpers.code_check(r):
            self.config = helpers.build_config_dict(r)
        else:
            logger.debug('Error getting %s config info', self.device_name)

    def toggle(self, status) -> bool:
        """Toggle dimmable bulb."""
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = status
        r, _ = helpers.call_api(
            '/SmartBulb/v1/device/devicestatus',
            'put',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )
        if helpers.code_check(r):
            self.device_status = status
            return True
        return False

    def set_brightness(self, brightness: int) -> bool:
        """Set brightness of dimmable bulb."""
        if not self.dimmable_feature:
            logger.debug('%s is not dimmable', self.device_name)
            return False
        brightness_update = int(self._validate_brightness(brightness))
        if self.device_status == 'on' and brightness_update == self._brightness:
            logger.debug("Device already in requested state")
            return True
        if self.device_status == 'off':
            self.toggle('on')
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = 'on'
        body['brightNess'] = str(brightness_update)
        r, _ = helpers.call_api(
            '/SmartBulb/v1/device/updateBrightness',
            'put',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )

        if helpers.code_check(r):
            self._brightness = brightness_update
            return True

        logger.debug('Error setting brightness for %s', self.device_name)
        return False


class VeSyncBulbESL100CW(VeSyncBulb):
    """VeSync Tunable and Dimmable White Bulb."""

    def __init__(self, details, manager):
        """Initialize Etekcity Tunable white bulb."""
        super().__init__(details, manager)

    def get_details(self) -> None:
        """Get details of tunable bulb."""
        body = helpers.req_body(self.manager, 'bypass')
        body['cid'] = self.cid
        body['jsonCmd'] = {'getLightStatus': 'get'}
        body['configModule'] = self.config_module
        r, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/bypass',
            'post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )
        if not isinstance(r, dict) or not helpers.code_check(r):
            logger.debug('Error calling %s', self.device_name)
            return
        light_resp = r.get('result', {}).get('light')

        if light_resp is not None:
            self._interpret_apicall_result(light_resp)
        elif r.get('code') == -11300027:
            logger.debug('%s device offline', self.device_name)
            self.connection_status = 'offline'
            self.device_status = 'off'
        else:
            logger.debug(
                '%s - Unknown return code - %s with message %s',
                self.device_name,
                str(r.get('code', '')),
                str(r.get('msg', '')),
            )

    def _interpret_apicall_result(self, response) -> None:
        self.connection_status = 'online'
        self.device_status = response.get('action', 'off')
        self._brightness = response.get('brightness', 0)
        self._color_temp = response.get('colorTempe', 0)

    def get_config(self) -> None:
        """Get configuration and firmware info of tunable bulb."""
        body = helpers.req_body(self.manager, 'bypass_config')
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/configurations',
            'post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )

        if helpers.code_check(r):
            self.config = helpers.build_config_dict(r)
        else:
            logger.debug('Error getting %s config info', self.device_name)

    def toggle(self, status) -> bool:
        """Toggle tunable bulb."""
        if status not in ('on', 'off'):
            logger.debug('Invalid status %s', status)
            return False
        body = helpers.req_body(self.manager, 'bypass')
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['jsonCmd'] = {'light': {'action': status}}
        r, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/bypass',
            'post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )
        if helpers.code_check(r):
            self.device_status = status
            return True
        logger.debug('%s offline', self.device_name)
        self.device_status = 'off'
        self.connection_status = 'offline'
        return False

    def set_brightness(self, brightness: int) -> bool:
        """Set brightness of tunable bulb."""
        brightness_update = int(self._validate_brightness(brightness))
        if self.device_status == 'on' and brightness_update == self._brightness:
            logger.debug("Device already in requested state")
            return True
        body = helpers.req_body(self.manager, 'bypass')
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        light_dict: Dict[str, NUMERIC_T] = {
            'brightness': brightness_update}
        if self.device_status == 'off':
            light_dict['action'] = 'on'
        body['jsonCmd'] = {'light': light_dict}
        r, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/bypass',
            'post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )

        if helpers.code_check(r):
            self._brightness = brightness_update
            self.device_status = 'on'
            self.connection_status = 'online'
            return True
        self.device_status = 'off'
        self.connection_status = 'offline'
        logger.debug('%s offline', self.device_name)

        return False

    def set_color_temp(self, color_temp: int) -> bool:
        """Set Color Temperature of Bulb in pct (1 - 100)."""
        color_temp_update = self._validate_color_temp(color_temp)
        if self.device_status == 'on' and color_temp_update == self._color_temp:
            logger.debug("Device already in requested state")
            return True
        body = helpers.req_body(self.manager, 'bypass')
        body['cid'] = self.cid
        body['jsonCmd'] = {'light': {}}
        body['jsonCmd']['light']['colorTempe'] = color_temp_update
        if self.device_status == 'off':
            body['jsonCmd']['light']['action'] = 'on'
        r, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/bypass',
            'post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )

        if not helpers.code_check(r):
            return False

        if r.get('code') == -11300027:
            logger.debug('%s device offline', self.device_name)
            self.connection_status = 'offline'
            self.device_status = 'off'
            return False
        if r.get('code') == 0:
            self.device_status = 'on'
            self._color_temp = color_temp
            return True
        logger.debug(
            '%s - Unknown return code - %d with message %s',
            self.device_name,
            r.get('code'),
            r.get('msg'),
        )
        return False


class VeSyncBulbValcenoA19MC(VeSyncBulb):
    """VeSync Multicolor Bulb."""

    def __init__(self, details, manager):
        """Initialize Multicolor bulb."""
        super().__init__(details, manager)

    def get_details(self) -> None:
        """Get details of multicolor bulb."""
        body = helpers.req_body(self.manager, 'bypassV2')
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': 'getLightStatusV2',
            'source': 'APP',
            'data': {},
        }
        r, _ = helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            'post',
            headers=helpers.req_header_bypass(),
            json_object=body,
        )
        if not isinstance(r, dict) or not helpers.code_check(r):
            logger.debug('Error calling %s', self.device_name)
            return
        self._interpret_apicall_result(r)

    def _interpret_apicall_result(self, response) -> None:
        if response.get('result', {}).get('result') is not None:
            innerresult = response.get('result', {}).get('result')
            self.connection_status = 'online'
            self.device_status = innerresult.get('enabled', 'off')
            if self.dimmable_feature:
                self._brightness = innerresult.get('brightness')
            if self.color_temp_feature:
                self._color_temp = innerresult.get('colorTemp')
            if self.rgb_shift_feature:
                self._color_mode = innerresult.get('colorMode')
                hue = float(round(innerresult.get('hue')/27.777777, 2))
                sat = float(innerresult.get('saturation')/100)
                val = float(innerresult.get('value'))
                self._color = Color(hue=hue, saturation=sat, value=val)
        elif (response.get('code') == -11300030 or
              response.get('code') == -11302030):
            logger.debug('%s device request timeout', self.device_name)
            self.connection_status = 'offline'
            self.device_status = 'off'
        elif response.get('code') == -11300027:
            logger.debug('%s device offline', self.device_name)
            self.connection_status = 'offline'
            self.device_status = 'off'
        else:
            logger.debug(
                '%s - Unknown return code - %d with message %s',
                self.device_name,
                response.get('code'),
                response.get('msg'),
            )

    def get_config(self) -> None:
        """Get configuration and firmware info of multicolor bulb."""
        body = helpers.req_body(self.manager, 'bypass')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid
        r, _ = helpers.call_api(
            '/cloud/v1/deviceManaged/configurations',
            'post',
            headers=helpers.req_header_bypass(),
            json_object=body,
        )
        if helpers.code_check(r):
            if r.get('result') is not None:
                result = r.get('result')
                self.__build_config_dict(result)
        else:
            logger.debug('Error getting %s config info', self.device_name)
            logger.debug('  return code - %d with message %s',
                         r.get('code'), r.get('msg'))

    def __build_config_dict(self, conf_dict: Dict[str, str]) -> None:
        """Build configuration dict for Multicolor bulb."""
        self.config['currentFirmVersion'] = (
            conf_dict.get('currentFirmVersion', ''))
        self.config['latestFirmVersion'] = (
            conf_dict.get('latestFirmVersion', ''))
        self.config['firmwareUrl'] = (
            conf_dict.get('firmwareUrl', ''))
        self.config['allowNotify'] = (
            conf_dict.get('allowNotify', ''))
        self.config['deviceImg'] = (
            conf_dict.get('deviceImg', ''))
        self.config['defaultDeviceImg'] = (
            conf_dict.get('defaultDeviceImg', ''))
        self.config['ownerShip'] = (
            conf_dict.get('ownerShip', False))

    def toggle(self, status: str) -> bool:
        """Toggle multicolor bulb."""
        body = helpers.req_body(self.manager, 'bypassV2')
        if status == 'off':
            status_bool = False
        elif status == 'on':
            status_bool = True
        else:
            logger.debug('Invalid status %s for toggle - only on/off allowed',
                         status)
            return False
        if status == self.device_status:
            logger.debug("Device already in requested state")
            return True
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': 'setSwitch',
            'source': 'APP',
            'data': {
                'id': 0,
                'enabled': status_bool,
                }
            }
        r, _ = helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            'post',
            headers=helpers.req_header_bypass(),
            json_object=body)
        if helpers.code_check(r):
            self.device_status = status
            return True
        logger.debug('%s offline', self.device_name)
        self.device_status = 'off'
        self.connection_status = 'offline'
        return False

    def set_rgb(self, red: NUMERIC_T = None,
                green: NUMERIC_T = None,
                blue: NUMERIC_T = None) -> bool:
        """Set RGB - red, green & blue 0-255."""
        new_color = Color(red=red, green=green, blue=blue).hsv
        return self.set_hsv(hue=new_color.hue,
                            saturation=new_color.saturation,
                            value=new_color.value)

    def set_brightness(self, brightness: int) -> bool:
        """Set brightness of multicolor bulb."""
        return self.set_status(brightness=brightness)

    def set_color_temp(self, color_temp: int) -> bool:
        """Set White Temperature of Bulb in pct (0 - 100)."""
        return self.set_status(color_temp=color_temp)

    def set_color_hue(self, color_hue: float) -> bool:
        """Set Color Hue of Bulb (0 - 360)."""
        return self.set_status(color_hue=color_hue)

    def set_color_saturation(self, color_saturation: float) -> bool:
        """Set Color Saturation of Bulb in pct (1 - 100)."""
        return self.set_status(color_saturation=color_saturation)

    def set_color_value(self, color_value: float) -> bool:
        """Set Value of multicolor bulb in pct (1 - 100)."""
        # Equivalent to brightness level, when in color mode.
        return self.set_status(color_value=color_value)

    def set_color_mode(self, color_mode: str) -> bool:
        """Set Color Mode of Bulb (white / hsv)."""
        return self.set_status(color_mode=color_mode)

    def set_hsv(self, hue: NUMERIC_T = None,
                saturation: NUMERIC_T = None,
                value: NUMERIC_T = None) -> bool:
        """Set HSV Values."""
        arg_dict = {"hue": hue, "saturation": saturation, "value": value}
        if hue is not None:
            hue_update: NUMERIC_T = self._validate_any(hue, 0, 360, 360)
        else:
            hue_update = ""
        if saturation is not None:
            sat_update: NUMERIC_T = self._validate_any(saturation, 0, 100, 100)
        else:
            sat_update = ""
        if value is not None:
            value_update: NUMERIC_T = self._validate_any(value, 0, 100, 100)
        else:
            value_update = ""
        arg_dict = {
            "hue": hue_update,
            "saturation": sat_update,
            "brightness": value_update
        }
        # the api expects the hsv Value in the brightness parameter

        if self._color is not None:
            current_dict = {"hue": self.color_hue,
                            "saturation": self.color_saturation,
                            "brightness": self.color_value}
            same_colors = True
            for key, val in arg_dict.items():
                if val != "":
                    if val != current_dict[key]:
                        same_colors = False
            if self.device_status == 'on' and same_colors:
                logger.debug("Device already in requested state")
                return True
        for key, val in arg_dict.items():
            if key == 'hue' and isinstance(val, float):
                arg_dict[key] = int(round(val*27.77778, 0))
            if key == "saturation" and isinstance(val, float):
                arg_dict[key] = int(round(val*100, 0))
            if key == "brightness" and isinstance(val, float):
                arg_dict[key] = int(round(val, 0))
        arg_dict['colorMode'] = 'hsv'
        return self._set_status_api(arg_dict)

    def enable_white_mode(self) -> bool:
        """Enable white color mode."""
        return self.set_status(color_mode='white')

    def set_status(self,
                   brightness: NUMERIC_T = None,
                   color_temp: NUMERIC_T = None,
                   color_saturation: NUMERIC_T = None,
                   color_hue: NUMERIC_T = None,
                   color_mode: Optional[str] = None,
                   color_value: NUMERIC_T = None
                   ) -> bool:
        """Set multicolor bulb parameters.

        No arguments turns bulb on.

        Parameters
        ----------
        brightness : int, optional
            brightness between 0 and 100, by default None
        color_temp : int, optional
            color temperature between 0 and 100, by default None
        color_mode : str, optional
            color mode hsv or white, by default None
        color_hue : float, optional
            color hue between 0 and 360, by default None
        color_saturation : float, optional
            color saturation between 0 and 100, by default None
        color_value : float, optional
            color value between 0 and 100, by default None

        Returns
        -------
        bool
            True if call was successful, False otherwise
        """
        arg_list = ['brightness', 'color_temp', 'color_saturation',
                    'color_hue', 'color_mode', 'color_value']
        toggle_on = True
        for val in arg_list:
            if locals()[val] is not None:
                toggle_on = False
        if toggle_on:
            self.turn_on()

        # If any HSV color values are passed,
        # set HSV status & ignore other values
        # Set Color if hue, saturation or value is set
        if color_hue is not None or color_value is not None or \
                color_saturation is not None:
            return self.set_hsv(color_hue, color_saturation, color_value)

        # initiate variables
        request_dict = {
            "force": 1,
            "colorMode": '',
            "brightness": '',
            "colorTemp": '',
            "hue": "",
            "saturation": "",
            "value": ""
        }

        force_list = ['colorTemp', 'saturation', 'hue', 'colorMode', 'value']
        if brightness is not None:
            brightness_update = self._validate_brightness(brightness)

            if all(locals().get(k) is None for k in force_list):

                # Do nothing if brightness is passed and same as current
                if self.device_status == 'on' and brightness_update == self._brightness:
                    logger.debug('Brightness already set to %s', brightness)
                    return True
                request_dict['force'] = 0
            request_dict['brightness'] = int(brightness_update)
        else:
            brightness_update = None
        # Set White Temperature of Bulb in pct (1 - 100).
        if color_temp is not None:
            valid_color_temp = self._validate_any(color_temp, 0, 100, 100)
            if valid_color_temp is not None:
                request_dict['colorTemp'] = int(valid_color_temp)
                request_dict['colorMode'] = 'white'

        # """Set Color Mode of Bulb (white / hsv)."""
        if color_mode is not None:
            if not isinstance(color_mode, str):
                logger.error('Error: color_mode should be a string value')
                return False
            color_mode = color_mode.lower()
            possible_modes = {'white': 'white',
                              'color': 'hsv',
                              'hsv': 'hsv'}
            if color_mode not in possible_modes:
                logger.error(
                    'Color mode specified is not acceptable '
                    '(Try: "white"/"color"/"hsv")')
                return False
            request_dict['colorMode'] = possible_modes[color_mode]
        if self._set_status_api(request_dict) and \
                brightness_update is not None:
            self._brightness = brightness_update
            return True
        return False

    def _set_status_api(self, data_dict: dict) -> bool:
        """Call api to set status - INTERNAL."""
        data_dict_start = {
            "force": 1,
            "brightness": '',
            "colorTemp": "",
            "colorMode": "",
            "hue": "",
            "saturation": "",
            "value": ""
        }
        data_dict_start.update(data_dict)
        body = helpers.req_body(self.manager, 'bypassV2')
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': 'setLightStatusV2',
            'source': 'APP',
            'data': data_dict_start
        }
        # Make API call
        r, _ = helpers.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            'post',
            headers=helpers.req_header_bypass(),
            json_object=body,
        )
        # Check result
        if helpers.code_check(r):
            self._interpret_apicall_result(r)
            self.device_status = 'on'
            return True
        self.device_status = 'off'
        self.connection_status = 'offline'
        logger.debug('%s offline', self.device_name)
        return False
