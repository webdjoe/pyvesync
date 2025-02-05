"""Etekcity/Valceno Smart Light Bulbs.

This module provides classes for the following Etekcity/Valceno smart lights:

    1. ESL100: Dimmable Bulb
    2. ESL100CW: Tunable White Bulb
    3. XYD0001: RGB Bulb
    4. ESL100MC: Multi-Color Bulb

Attributes:
    feature_dict (dict): Dictionary of bulb models and their supported features.
        Defines the class to use for each bulb model and the list of features
    bulb_modules (dict): Dictionary of bulb models as keys and their associated classes
        as string values.

Note:
    The bulb module is built from the `feature_dict` dictionary and used by the
    `pyvesync_bulb.factory` and tests to determine the class to instantiate for
    each bulb model. These classes should not be instantiated manually.

Examples:
    The following example shows the structure of the `feature_dict` dictionary:
    ```python

    feature_dict = {
        'ESL100MC': { # device_type attribute
            'module': 'VeSyncBulbESL100MC', # String name of the class to instantiate
            'features': ['dimmable', 'rgb_shift'], # List of supported features
            'color_model': 'rgb' # Color model used by the bulb (rgb, hsv, none)
        }
    }
    ```
"""
from __future__ import annotations
import logging
import json
import sys
from typing import Union, Optional, NamedTuple
from abc import ABCMeta, abstractmethod
from enum import Enum
from .helpers import Helpers, Color, EDeviceFamily, ERR_DEV_OFFLINE, ERR_REQ_TIMEOUTS
from .vesyncbasedevice import VeSyncBaseDevice, STATUS_ON, STATUS_OFF

logger = logging.getLogger(__name__)

module_bulb = sys.modules[__name__]

NUMERIC_T = Optional[Union[int, float, str]]

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

__all__: list = list(bulb_modules.values()) + ["bulb_modules", "VeSyncBulb"]


def pct_to_kelvin(pct: float, max_k: int = 6500, min_k: int = 2700) -> float:
    """Convert percent to kelvin."""
    return ((max_k - min_k) * pct / 100) + min_k

class ColorMode(str, Enum):
    NONE = ''
    WHITE = 'white'
    COLOR = 'color'
    HSV = 'hsv'

class VeSyncBulb(VeSyncBaseDevice):
    """Base class for VeSync Bulbs.

    Abstract base class to provide methods for controlling and
    getting details of VeSync bulbs. Inherits from
    [`VeSyncBaseDevice`][pyvesync.vesyncbasedevice.VeSyncBaseDevice]. This class
    should not be used directly for devices, but rather subclassed for each.

    Attributes:
        brightness (int): Brightness of bulb (0-100).
        color_temp_kelvin (int): White color temperature of bulb in Kelvin.
        color_temp_pct (int): White color temperature of bulb in percent (0-100).
        color_hue (float): Color hue of bulb (0-360).
        color_saturation (float): Color saturation of bulb in percent (0-100).
        color_value (float): Color value of bulb in percent (0-100).
        color (Color): Color of bulb in the form of a dataclass with two namedtuple
            attributes - `hsv` & `rgb`. See [pyvesync.Helpers.Color][].
    """

    __metaclass__ = ABCMeta

    _brightness: Optional[int] = 0
    _color_temp: Optional[int] = 0
    _color_value: float = 0
    _color_hue: float = 0
    _color_saturation: float = 0
    _color_mode: ColorMode.NONE
    _color: Optional[Color] = None
    features: list[str] = []
    _rgb_values: dict[str, int] = {
        'red': 0,
        'green': 0,
        'blue': 0
    }

    def __init__(self, details: dict[str, str | list], manager) -> None:
        """Initialize VeSync smart bulb base class."""
        super().__init__(details, manager, EDeviceFamily.BULB)
        self.features: list | None = feature_dict.get(
            self.device_type, {}).get('features')
        if self.features is None:
            logger.error("No configuration set for - %s", self.device_name)
            raise KeyError

    @property
    def brightness(self) -> int:
        """Return brightness of vesync bulb.

        Returns:
            int: Brightness of bulb (0-100).
        """
        if self.dimmable_feature and self._brightness is not None:
            return self._brightness
        return 0

    @property
    def color_temp_kelvin(self) -> int:
        """Return white color temperature of bulb in Kelvin.

        Converts the color temperature in percent to Kelvin using
        the `pct_to_kelvin` function.

        Returns:
            int: White color temperature of bulb in Kelvin (2700 - 6500).

        Notes:
            This returns 0 for bulbs that do not have color temperature support.
        """
        if self.color_temp_feature and self._color_temp is not None:
            return int(pct_to_kelvin(self._color_temp))
        return 0

    @property
    def color_temp_pct(self) -> int:
        """Return white color temperature of bulb in percent (0-100).

        Subclasses that use this method, should calculate the color temeprature
        in percent regardless of how the API returns the value.
        """
        if self.color_temp_feature and self._color_temp is not None:
            return int(self._color_temp)
        return 0

    @property
    def color_hue(self) -> float:
        """Return color hue (HSV colorspace) of bulb.

        Returns hue from the `color` attribute. (0-360)

        Returns:
            float: Color hue of bulb in HSV colorspace.

        Notes:
            This returns 0 for bulbs that do not have color support.
        """
        if self.rgb_shift_feature and self._color is not None:
            return self._color.hsv.hue
        return 0

    @property
    def color_saturation(self) -> float:
        """Return color saturation (HSV colorspace) of bulb in percent.

        Return saturation from the `color` attribute (0-100).

        Returns:
            float: Color saturation of bulb in percent (0-100).

        Notes:
            This returns 0 for bulbs that do not have color
        """
        if self.rgb_shift_feature and self._color is not None:
            return self._color.hsv.saturation
        return 0

    @property
    def color_value(self) -> float:
        """Return color value (HSV colorspace) of bulb in percent.

        Returns the color from from the `color` attribute (0-100).

        Returns:
            float: Color value of bulb in percent (0-100).

        Notes:
            This returns 0 for bulbs that do not have color support.
        """
        if self.rgb_shift_feature and self._color is not None:
            return self._color.hsv.value
        return 0

    @property
    # pylint: disable-next=differing-param-doc # DOCUMENTATION FOR SETTER
    def color(self) -> Color | None:
        # pylint: disable=differing-type-doc
        """Set color property based on rgb or hsv values.

        Pass either red, green, blue or hue, saturation, value.

        Args:
            red (float): Red value of RGB color, 0-255
            green (float): Green value of RGB color, 0-255
            blue (float): Blue value of RGB color, 0-255
            hue (float): Hue value of HSV color, 0-360
            saturation (float): Saturation value of HSV color, 0-100
            value (float): Value (brightness) value of HSV color 0-100

        Returns:
            Color: Color dataclass with hsv and rgb named tuple attributes.
        """
        if self.rgb_shift_feature is True and self._color is not None:
            return self._color
        return None

    @color.setter
    def color(self, red: float | None = None,
              green: float | None = None,
              blue: float | None = None,
              hue: float | None = None,
              saturation: float | None = None,
              value: float | None = None) -> None:
        """Set color property based on rgb or hsv values."""
        self._color = Color(red=red, green=green, blue=blue,
                            hue=hue, saturation=saturation, value=value)

    @property
    def color_hsv(self) -> NamedTuple | None:
        """Return color of bulb as [hsv named tuple][pyvesync.Helpers.HSV].

        Notes:
            Returns `None` for bulbs that do not have color support.
        """
        if self.rgb_shift_feature is True and self._color is not None:
            return self._color.hsv
        return None

    @property
    def color_rgb(self) -> NamedTuple | None:
        """Return color of bulb as [rgb named tuple][pyvesync.Helpers.RGB].

        Notes:
            Returns `None` for bulbs that do not have color support.
        """
        if self.rgb_shift_feature is True and self._color is not None:
            return self._color.rgb
        return None

    @property
    def color_mode(self) -> str | None:
        """Return color mode of bulb. Possible values are none, hsv or rgb.

        Notes:
            This is a read-only property. Color mode is defined in
            the [`feature_dict`][pyvesync.vesyncbulb.feature_dict].
        """
        if self.rgb_shift_feature and self._color_mode is not None:
            return str(self._color_mode)
        return None

    @property
    def dimmable_feature(self) -> bool:
        """Return true if dimmable bulb."""
        return (self.features is not None and 'dimmable' in self.features)

    @property
    def color_temp_feature(self) -> bool:
        """Checks if the device has the ability to change color temperature.

        Returns:
            bool: True if the device supports changing color temperature.
        """
        return (self.features is not None and 'color_temp' in self.features)

    @property
    def rgb_shift_feature(self) -> bool:
        """Checks if the device is multicolor.

        Returns:
            bool: True if the device supports changing color.
        """
        return (self.features is not None and 'rgb_shift' in self.features)

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

    def _validate_hsv(self, hue: NUMERIC_T = None,
                      saturation: NUMERIC_T = None,
                      value: NUMERIC_T = None) -> Color:
        """Validate HSV Arguments."""
        hsv_dict = {'hue': hue, 'saturation': saturation, 'value': value}
        for clr, val in hsv_dict.items():
            if val is None and self._color is not None:
                hsv_dict[clr] = getattr(self._color.hsv, clr)

        if hue is not None:
            valid_hue = self._validate_any(hue, 1, 360, 360)
        elif self._color is not None:
            valid_hue = self._color.hsv.hue
        else:
            logger.debug("No current hue value, setting to 0")
            valid_hue = 360
        hsv_dict['hue'] = valid_hue
        for itm, val in {'saturation': saturation, 'value': value}.items():
            if val is not None:
                valid_item = self._validate_any(val, 1, 100, 100)
            elif self.color is not None:
                valid_item = getattr(self.color.hsv, itm)
            else:
                logger.debug("No current %s value, setting to 0", itm)
                valid_item = 100
            hsv_dict[itm] = valid_item
        return Color(hue=hsv_dict['hue'], saturation=hsv_dict['saturation'],
                     value=hsv_dict['value'])

    def _validate_brightness(self, brightness: float | str,
                             start: int = 0, stop: int = 100) -> int:
        """Validate brightness value."""
        try:
            brightness_update: int = max(start, (min(stop, int(
                                                round(float(brightness), 2)))))
        except (ValueError, TypeError):
            brightness_update = self.brightness if self.brightness is not None else 100
        return brightness_update

    def _validate_color_temp(self, temp: int, start: int = 0, stop: int = 100) -> int:
        """Validate color temperature."""
        try:
            temp_update = max(start, (min(stop, int(
                round(float(temp), 0)))))
        except (ValueError, TypeError):
            temp_update = self._color_temp if self._color_temp is not None else 100
        return temp_update

    @staticmethod
    def _validate_any(value: NUMERIC_T,
                      start: NUMERIC_T = 0,
                      stop: NUMERIC_T = 100,
                      default: float = 100) -> float:
        """Validate any value."""
        try:
            value_update = max(float(start), (min(float(stop), round(float(value), 2))))  # type: ignore[arg-type]  # noqa
        except (ValueError, TypeError):
            value_update = default
        return value_update

    @abstractmethod
    def set_status(self) -> bool:
        """Set vesync bulb attributes(brightness, color_temp, etc).

        This is a helper function that is called by the direct `set_*` methods,
        such as `set_brightness`, `set_rgb`, `set_hsv`, etc.

        Returns:
            bool : True if successful, False otherwise.
        """

    @abstractmethod
    def get_details(self) -> None:
        """Get vesync bulb details.

        This is a legacy function to update devices, **updates should be
        called by `update()`**

        Returns:
            None
        """

    @abstractmethod
    def _interpret_apicall_result(self, response: dict) -> None:
        """Update bulb status from any api call response."""

    @abstractmethod
    def get_config(self) -> None:
        """Call api to get configuration details and firmware.

        Populates the `self.config` attribute with the response.

        Returns:
            None

        Note:
            The configuration attribute `self.config` is structured as follows:
            ```python
            {
                'current_firmware_version': '1.0.0',
                'latest_firmware_version': '1.0.0',
                'maxPower': '560',
                'threshold': '1000',
                'power_protection': 'on',
                'energy_saving_status': 'on'
            }
            ```
        """

    def set_hsv(self,
                hue: NUMERIC_T,
                saturation: NUMERIC_T,
                value: NUMERIC_T) -> bool | None:
        """Set HSV if supported by bulb.

        Args:
            hue (NUMERIC_T): Hue 0-360
            saturation (NUMERIC_T): Saturation 0-100
            value (NUMERIC_T): Value 0-100

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.rgb_shift_feature is False:
            logger.debug("HSV not supported by bulb")
            return False
        return bool(hue and saturation and value)

    def set_rgb(self, red: NUMERIC_T = None,
                green: NUMERIC_T = None,
                blue: NUMERIC_T = None) -> bool:
        """Set RGB if supported by bulb.

        Args:
            red (NUMERIC_T): Red 0-255
            green (NUMERIC_T): green 0-255
            blue (NUMERIC_T): blue 0-255

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.rgb_shift_feature is False:
            logger.debug("RGB not supported by bulb")
            return False
        return bool(red and green and blue)

    def update(self) -> None:
        """Update bulb details.

        Calls `get_details()` method to retrieve status from API and
        update the bulb attributes. `get_details()` is overriden by subclasses
        to hit the respective API endpoints.
        """
        self.get_details()

    def display(self) -> None:
        """Return formatted bulb info to stdout."""
        super().display()
        if self.connection_status == 'online':
            disp = []  # initiate list
            if self.dimmable_feature:
                disp.append(('Brightness', str(self.brightness), '%'))
            if self.color_temp_feature:
                disp.append(('White Temperature Pct', str(self.color_temp_pct), '%'))
                disp.append(('White Temperature Kelvin', str(self.color_temp_kelvin), 'K'))
            if self.rgb_shift_feature and self.color is not None:
                disp.append(('ColorHSV', Helpers.named_tuple_to_str(self.color.hsv), ''))
                disp.append(('ColorRGB', Helpers.named_tuple_to_str(self.color.rgb), ''))
                disp.append(('ColorMode', str(self.color_mode), ''))
            if len(disp) > 0:
                for line in disp:
                    print(f"{line[0]+': ':.<30} {' '.join(line[1:])}")

    def displayJSON(self) -> str:
        """Return bulb device info in JSON format.

        Returns:
            str: JSON formatted string of bulb details.

        Example:
            ```json
            {
                "deviceName": "Bulb",
                "deviceStatus": "on",
                "connectionStatus": "online",
                "Brightness": "100%",
                "WhiteTemperaturePct": "100%",
                "WhiteTemperatureKelvin": "6500K",
                "ColorHSV": "{"hue": 0, "saturation": 0, "value": 0}",
                "ColorRGB": "{"red": 0, "green": 0, "blue": 0}",
                "ColorMode": "hsv"
            }
            ```
        """
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
    def color_value_rgb(self) -> NamedTuple | None:
        """Legacy Method .... Depreciated."""
        if self._color is not None:
            return self._color.rgb
        return None

    @property
    def color_value_hsv(self) -> NamedTuple | None:
        """Legacy Method .... Depreciated."""
        if self._color is not None:
            return self._color.hsv
        return None

    def build_api_dict(self, method, data):
        return {
            **Helpers.req_body_bypass_v2(self.manager),
            'cid': self.cid,
            'configModule': self.config_module,
            'payload': {
                'method': method,
                'source': 'APP',
                'data': data
            }
        }

class VeSyncBulbESL100MC(VeSyncBulb):
    """Etekcity ESL100 Multi Color Bulb device instance.

    Inherits from [VeSyncBulb][pyvesync.vesyncbulb.VeSyncBulb]
    and [VeSyncBaseDevice][pyvesync.vesyncbasedevice.VeSyncBaseDevice].

    Attributes:
        device_status (str): Status of bulb, either 'on' or 'off'.
        connection_status (str): Connection status of bulb, either 'online' or 'offline'.
        details (dict): Dictionary of bulb state details.
        brightness (int): Brightness of bulb (0-100).
        color_temp_kelvin (int): White color temperature of bulb in Kelvin.
        color_temp_pct (int): White color temperature of bulb in percent (0-100).
        color_hue (float): Color hue of bulb (0-360).
        color_saturation (float): Color saturation of bulb in percent (0-100).
        color_value (float): Color value of bulb in percent (0-100).
        color (Color): Color of bulb in the form of a dataclass with
            two named tuple attributes - `hsv` & `rgb`. See [pyvesync.Helpers.Color][].

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
        See pyvesync.Helpers.Color for more information on the Color dataclass.
    """

    def __init__(self, details: dict[str, str | list], manager) -> None:
        """Instantiate ESL100MC Multicolor Bulb.

        Args:
            details (dict): Dictionary of bulb state details.
            manager (VeSync): Manager class used to make API calls.
        """
        super().__init__(details, manager)

    def get_details(self) -> None:
        body = self.build_api_dict('getLightStatus', {})
        r = Helpers.post_device_managed_v2(body)
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

    def _interpret_apicall_result(self, response: dict) -> None:
        """Build detail dictionary from response."""
        self._brightness = response.get('brightness', 0)
        self._color_mode = response.get('colorMode', '')
        self._color = Color(red=response.get('red', 0),
                            green=response.get('green', 0),
                            blue=response.get('blue', 0))

    def set_brightness(self, brightness: int) -> bool:
        """Set brightness of bulb.

        Calls the `set_status` method with the brightness value.

        Args:
            brightness (int): Brightness of bulb (0-100).

        Returns:
            bool: True if successful, False otherwise.
        """
        return self.set_status(brightness=brightness)

    def set_rgb_color(self, red: NUMERIC_T, green: NUMERIC_T, blue: NUMERIC_T) -> bool:
        """DEPRECIATED, USE `set_rgb()`."""
        return self.set_status(red=red, green=green, blue=blue)

    def set_rgb(self, red: NUMERIC_T = None,
                green: NUMERIC_T = None,
                blue: NUMERIC_T = None) -> bool:
        return self.set_status(red=red, green=green, blue=blue)

    def set_hsv(self,
                hue: NUMERIC_T,
                saturation: NUMERIC_T,
                value: NUMERIC_T) -> bool | None:
        rgb = Color(hue=hue, saturation=saturation, value=value).rgb
        return self.set_status(red=rgb.red, green=rgb.green, blue=rgb.blue)

    def enable_white_mode(self) -> bool:
        """Enable white mode on bulb.

        Returns:
            bool: True if successful, False otherwise.
        """
        return self.set_status(brightness=100)

    def set_status(self, brightness: NUMERIC_T = None,
                   red: NUMERIC_T = None,
                   green: NUMERIC_T = None,
                   blue: NUMERIC_T = None) -> bool:
        """Set color of VeSync ESL100MC.

        Brightness or RGB values must be provided. If RGB values are provided,
        brightness is ignored.

        Args:
            brightness (int): Brightness of bulb (0-100).
            red (int): Red value of RGB color, 0-255.
            green (int): Green value of RGB color, 0-255.
            blue (int): Blue value of RGB color, 0-255.

        Returns:
            bool: True if successful, False otherwise.
        """
        brightness_update = 100
        if red is not None and green is not None and blue is not None:
            new_color = self._validate_rgb(red, green, blue)
            color_mode = 'color'
            if self.device_status == STATUS_ON and new_color == self._color:
                logger.debug("New color is same as current color")
                return True
        else:
            logger.debug("RGB Values not provided")
            new_color = None
            if brightness is not None:
                brightness_update = int(self._validate_brightness(brightness))
                # Do nothing if brightness is passed and same as current
                if self.device_status == STATUS_ON and brightness_update == self._brightness:
                    logger.debug('Brightness already set to %s', brightness)
                    return True
                color_mode = 'white'
            else:
                logger.debug("Brightness and RGB values are not set")
                return False

        data = {
            'action': STATUS_ON,
            'speed': 0,
            'brightness': brightness_update,
            'red': 0 if new_color is None else int(new_color.rgb.red),
            'green': 0 if new_color is None else int(new_color.rgb.green),
            'blue': 0 if new_color is None else int(new_color.rgb.blue),
            'colorMode': 'color' if new_color is not None else 'white',
        }
        body = self.build_api_dict('setLightStatus', data)
        r = Helpers.post_device_managed_v2(body)
        if not isinstance(r, dict) or r.get('code') != 0:
            logger.debug("Error in setting bulb status")
            return False

        if color_mode == 'color' and new_color is not None:
            self._color_mode = ColorMode.COLOR
            self._color = Color(red=new_color.rgb.red,
                                green=new_color.rgb.green,
                                blue=new_color.rgb.blue)
        elif brightness is not None:
            self._color_mode = ColorMode.WHITE
            self._brightness = int(brightness_update)

        self.device_status = STATUS_ON
        return True

    def turn(self, status: str) -> bool:
        if (status in (STATUS_ON, STATUS_OFF)):
            turn_on = status == STATUS_ON
        else:
            logger.debug("Status must be on or off")
            return False
        body = self.build_api_dict('setSwitch', {'id': 0,'enabled': turn_on})
        r = Helpers.post_device_managed_v2(body)
        if not isinstance(r, dict) or r.get('code') != 0:
            logger.debug("Error in setting %s %s", self.device_name, status)
            return False
        self.device_status = status
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

    def __init__(self, details: dict, manager) -> None:
        """Initialize Etekcity ESL100 Dimmable Bulb.

        Args:
            details (dict): Dictionary of bulb state details.
            manager (VeSync): Manager class used to make API calls
        """
        super().__init__(details, manager)

    def call_api(self, api, method, body):
        r = Helpers.call_api(f'/SmartBulb/v1/device/{api}',
            method=method,
            headers=Helpers.req_headers(self.manager),
            json_object=body
        )
        return r

    def get_details(self) -> None:
        body = Helpers.req_body_device_detail(self.manager)
        body['uuid'] = self.uuid
        r = self.call_api('devicedetail', 'post', body)
        if Helpers.code_check(r):
            self.connection_status = r.get('connectionStatus')
            self.device_status = r.get('deviceStatus')
            if self.dimmable_feature:
                self._brightness = int(r.get('brightNess'))
        else:
            logger.debug('Error getting %s details', self.device_name)

    def get_config(self) -> None:
        body = Helpers.req_body_device_detail(self.manager)
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r = self.call_api('configurations', 'post', body)

        if Helpers.code_check(r):
            self.config = Helpers.build_config_dict(r)
        else:
            logger.debug('Error getting %s config info', self.device_name)

    def turn(self, status: str) -> bool:
        body = Helpers.req_body_status(self.manager)
        body['uuid'] = self.uuid
        body['status'] = status
        r = self.call_api('devicestatus', 'put', body)
        if Helpers.code_check(r):
            self.device_status = status
            return True
        return False

    def set_brightness(self, brightness: int) -> bool:
        """Set brightness of dimmable bulb.

        Args:
            brightness (int): Brightness of bulb (0-100).

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.dimmable_feature:
            logger.debug('%s is not dimmable', self.device_name)
            return False
        brightness_update = int(self._validate_brightness(brightness))
        if self.device_status == STATUS_ON and brightness_update == self._brightness:
            logger.debug("Device already in requested state")
            return True
        if self.device_status == STATUS_OFF:
            self.turn(STATUS_ON)
        body = Helpers.req_body_status(self.manager)
        body['uuid'] = self.uuid
        body['status'] = STATUS_ON
        body['brightNess'] = str(brightness_update)
        r = self.call_api('updateBrightness', 'put', body)

        if Helpers.code_check(r):
            self._brightness = brightness_update
            return True

        logger.debug('Error setting brightness for %s', self.device_name)
        return False


class VeSyncBulbESL100CW(VeSyncBulb):
    """VeSync Tunable and Dimmable White Bulb."""

    def __init__(self, details: dict, manager) -> None:
        """Initialize Etekcity Tunable white bulb."""
        super().__init__(details, manager)
    def get_details(self) -> None:
        body = {
            **Helpers.req_body_bypass_v1(self.manager),
            'cid': self.cid,
            'configModule': self.config_module,
            'jsonCmd': {'getLightStatus': 'get'}
        }
        r = Helpers.post_device_managed_v1(self.manager, body)
        if not isinstance(r, dict) or not Helpers.code_check(r):
            logger.debug('Error calling %s', self.device_name)
            return
        light_resp = r.get('result', {}).get('light')

        if light_resp is not None:
            self._interpret_apicall_result(light_resp)
        elif r.get('code') == ERR_DEV_OFFLINE:
            logger.debug('%s device offline', self.device_name)
            self.connection_status = 'offline'
            self.device_status = STATUS_OFF
        else:
            logger.debug(
                '%s - Unknown return code - %s with message %s',
                self.device_name,
                str(r.get('code', '')),
                str(r.get('msg', '')),
            )

    def _interpret_apicall_result(self, response: dict) -> None:
        self.connection_status = 'online'
        self.device_status = response.get('action', STATUS_OFF)
        self._brightness = response.get('brightness', 0)
        self._color_temp = response.get('colorTempe', 0)

    def get_config(self) -> None:
        body = Helpers.req_body_firmware(self.manager, {'uuid': self.uuid})

        r = self.call_api_v1('configurations', 'post', body)

        if Helpers.code_check(r):
            self.config = Helpers.build_config_dict(r)
        else:
            logger.debug('Error getting %s config info', self.device_name)

    def turn(self, status: str) -> bool:
        if status not in (STATUS_ON, STATUS_OFF):
            logger.debug('Invalid status %s', status)
            return False
        body = {
            **Helpers.req_body_bypass_v1(self.manager),
            'cid': self.cid,
            'configModule': self.config_module,
            'jsonCmd': {
                'light': {'action': status}
            }
        }
        r = Helpers.post_device_managed_v1(self.manager, body)
        if Helpers.code_check(r):
            self.device_status = status
            return True
        logger.debug('%s offline', self.device_name)
        self.device_status = STATUS_OFF
        self.connection_status = 'offline'
        return False

    def set_brightness(self, brightness: int) -> bool:
        """Set brightness of tunable bulb."""
        brightness_update = int(self._validate_brightness(brightness))
        if self.device_status == STATUS_ON and brightness_update == self._brightness:
            logger.debug("Device already in requested state")
            return True
        body = {
            **Helpers.req_body_bypass_v1(self.manager),
            'cid': self.cid,
            'configModule': self.config_module
        }
        light_dict: dict[str, NUMERIC_T] = {
            'brightness': brightness_update}
        if self.device_status == STATUS_OFF:
            light_dict['action'] = STATUS_ON
        body['jsonCmd'] = {'light': light_dict}
        r = Helpers.post_device_managed_v1(self.manager, body)

        if Helpers.code_check(r):
            self._brightness = brightness_update
            self.device_status = STATUS_ON
            self.connection_status = 'online'
            return True
        self.device_status = STATUS_OFF
        self.connection_status = 'offline'
        logger.debug('%s offline', self.device_name)

        return False

    def set_color_temp(self, color_temp: int) -> bool:
        """Set Color Temperature of Bulb in pct (1 - 100)."""
        color_temp_update = self._validate_color_temp(color_temp)
        if self.device_status == STATUS_ON and color_temp_update == self._color_temp:
            logger.debug("Device already in requested state")
            return True
        body = {
            **Helpers.req_body_bypass_v1(self.manager),
            'cid': self.cid,
            'jsonCmd': {
                'light': {'colorTempe': color_temp_update}
            }
        }
        if self.device_status == STATUS_OFF:
            body['jsonCmd']['light']['action'] = STATUS_ON
        r = Helpers.post_device_managed_v1(self.manager, body)

        if not Helpers.code_check(r):
            return False

        if r.get('code') == ERR_DEV_OFFLINE:
            logger.debug('%s device offline', self.device_name)
            self.connection_status = 'offline'
            self.device_status = STATUS_OFF
            return False
        if r.get('code') == 0:
            self.device_status = STATUS_ON
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

    def __init__(self, details: dict, manager) -> None:
        """Initialize Multicolor bulb."""
        super().__init__(details, manager)

    def get_details(self) -> None:
        body = self.build_api_dict('getLightStatusV2', {})
        r = Helpers.post_device_managed_v2(body)
        if not isinstance(r, dict) or not Helpers.code_check(r):
            logger.debug('Error calling %s', self.device_name)
            return
        self._interpret_apicall_result(r)

    def _interpret_apicall_result(self, response: dict) -> None:
        if response.get('result', {}).get('result') is not None:
            innerresult = response.get('result', {}).get('result')
            self.connection_status = 'online'
            self.device_status = innerresult.get('enabled', STATUS_OFF)
            if self.dimmable_feature:
                self._brightness = innerresult.get('brightness')
            if self.color_temp_feature:
                self._color_temp = innerresult.get('colorTemp')
            if self.rgb_shift_feature:
                color_mode = innerresult.get('colorMode')
                try:
                    self._color_mode = ColorMode(color_mode)
                except:
                    logger.warning("Unknown ColorMode '%s' - using 'color'!", color_mode)
                    self._color_mode = ColorMode.COLOR
                hue = float(round(innerresult.get('hue')/27.777777, 2))
                sat = float(innerresult.get('saturation')/100)
                val = float(innerresult.get('value'))
                self._color = Color(hue=hue, saturation=sat, value=val)
        elif (response.get('code') in ERR_REQ_TIMEOUTS):
            logger.debug('%s device request timeout', self.device_name)
            self.connection_status = 'offline'
            self.device_status = STATUS_OFF
        elif response.get('code') == ERR_DEV_OFFLINE:
            logger.debug('%s device offline', self.device_name)
            self.connection_status = 'offline'
            self.device_status = STATUS_OFF
        else:
            logger.debug(
                '%s - Unknown return code - %d with message %s',
                self.device_name,
                response.get('code'),
                response.get('msg'),
            )

    def get_config(self) -> None:
        body = {
            **Helpers.req_body(self.manager, 'configurations'),
            'uuid': self.uuid
        }
        r = self.call_api_v1('configurations', 'post', body)
        if Helpers.code_check(r):
            if r.get('result') is not None:
                result = r.get('result')
                self.__build_config_dict(result)
        else:
            logger.debug('Error getting %s config info', self.device_name)
            logger.debug('  return code - %d with message %s',
                         r.get('code'), r.get('msg'))

    def __build_config_dict(self, conf_dict: dict[str, str]) -> None:
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

    def turn(self, status: str) -> bool:
        if status == STATUS_OFF:
            status_bool = False
        elif status == STATUS_ON:
            status_bool = True
        else:
            logger.debug('Invalid status %s for turn - only on/off allowed',
                         status)
            return False
        if status == self.device_status:
            logger.debug("Device already in requested state")
            return True
        body = self.build_api_dict('setSwitch', {'id': 0,'enabled': status_bool})
        r = Helpers.post_device_managed_v2(body)
        if Helpers.code_check(r):
            self.device_status = status
            return True
        logger.debug('%s offline', self.device_name)
        self.device_status = STATUS_OFF
        self.connection_status = 'offline'
        return False

    def set_rgb(self, red: NUMERIC_T = None,
                green: NUMERIC_T = None,
                blue: NUMERIC_T = None) -> bool:
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
        arg_dict = {
            "hue": self._validate_any(hue, 0, 360, 360) if hue is not None else "",
            "saturation": self._validate_any(
                saturation, 0, 100, 100) if saturation is not None else "",
            "brightness": self._validate_any(
                value, 0, 100, 100) if value is not None else ""
            }

        # the api expects the hsv Value in the brightness parameter
        if self._color is not None:
            current_dict = {"hue": self.color_hue,
                            "saturation": self.color_saturation,
                            "brightness": self.color_value}
            filtered_arg_dict = {k: v for k, v in arg_dict.items() if v != ""}
            same_colors = all(current_dict.get(k) == v
                              for k, v in filtered_arg_dict.items())
            if self.device_status == STATUS_ON and same_colors:
                logger.debug("Device already in requested state")
                return True
        arg_dict = {
            "hue": int(round(arg_dict["hue"]*27.77778, 0)) if isinstance(
                arg_dict["hue"], float) else "",
            "saturation": int(round(arg_dict["saturation"]*100, 0)) if isinstance(
                arg_dict["saturation"], float) else "",
            "brightness": int(round(arg_dict["brightness"], 0)) if isinstance(
                arg_dict["brightness"], float) else ""
        }
        arg_dict['colorMode'] = 'hsv'
        return self._set_status_api(arg_dict)

    def enable_white_mode(self) -> bool:
        """Enable white color mode."""
        return self.set_status(color_mode='white')

    def set_status(self,  # noqa: C901
                   *,
                   brightness: NUMERIC_T = None,
                   color_temp: NUMERIC_T = None,
                   color_saturation: NUMERIC_T = None,
                   color_hue: NUMERIC_T = None,
                   color_mode: str | None = None,
                   color_value: NUMERIC_T = None
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
        arg_list = ['brightness', 'color_temp', 'color_saturation',
                    'color_hue', 'color_mode', 'color_value']
        turn_on = True
        for val in arg_list:
            if locals()[val] is not None:
                turn_on = False
        if turn_on:
            self.turn_on()

        # If any HSV color values are passed,
        # set HSV status & ignore other values
        # Set Color if hue, saturation or value is set
        if any(var is not None for var in [color_hue, color_saturation, color_value]):
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
            if self.device_status == 'on' and brightness_update == self._brightness:
                logger.debug('Brightness already set to %s', brightness)
                return True
            if all(locals().get(k) is None for k in force_list):
                request_dict['force'] = 0
            request_dict['brightness'] = int(brightness_update)
        else:
            brightness_update = None
        # Set White Temperature of Bulb in pct (1 - 100).
        if color_temp is not None and \
                self._validate_any(color_temp, 0, 100, 100):
            valid_color_temp = self._validate_any(color_temp, 0, 100, 100)
            request_dict['colorTemp'] = int(valid_color_temp)
            request_dict['colorMode'] = 'white'

        # Set Color Mode of Bulb (white / hsv).
        if color_mode is not None:
            possible_modes = {'white': 'white',
                              'color': 'hsv',
                              'hsv': 'hsv'}
            if not isinstance(color_mode, str) or \
                    color_mode.lower() not in possible_modes:
                logger.error('Error: invalid color_mode value')
                return False
            color_mode = color_mode.lower()
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
        body = self.build_api_dict('setLightStatusV2', data_dict_start)
        # Make API call
        r = Helpers.post_device_managed_v2(body)
        # Check result
        if Helpers.code_check(r):
            self._interpret_apicall_result(r)
            self.device_status = STATUS_ON
            return True
        self.device_status = STATUS_OFF
        self.connection_status = 'offline'
        logger.debug('%s offline', self.device_name)
        return False


def factory(module: str, details: dict, manager) -> VeSyncBulb:
    try:
        definition = bulb_modules[module]
        bulb = getattr(module_bulb, definition)
        return bulb(details, manager)
    except:
        return None
