"""Base classes for all VeSync bulbs."""
from __future__ import annotations
import dataclasses
import logging
from abc import abstractmethod
from typing import TYPE_CHECKING
import orjson
from deprecated import deprecated

from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseToggleDevice, DeviceState
from pyvesync.helper_utils.colors import HSV, RGB, Color
from pyvesync.helper_utils.helpers import Converters, Validators, NUMERIC_STRICT
from pyvesync.const import BulbFeatures

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.data_models.device_list_models import ResponseDeviceDetailsModel
    from pyvesync.device_map import BulbMap


logger = logging.getLogger(__name__)


class BulbState(DeviceState):
    """VeSync Bulb State Base."""

    __slots__ = (
        '_brightness',
        '_color',
        '_color_temp',
        'color_mode',
        'color_modes'
    )

    def __init__(self,
                 device: VeSyncBulb,
                 details: ResponseDeviceDetailsModel,
                 feature_map: BulbMap) -> None:
        """Initialize VeSync Bulb State Base."""
        super().__init__(device, details, feature_map)
        self.features = feature_map.features
        self.color_modes: list[str] = feature_map.color_modes
        self.device: VeSyncBulb = device
        self.color_mode: str | None = None
        self._brightness: int | None = None
        self._color_temp: int | None = None
        self._color: Color | None = None

    @property
    def color(self) -> Color | None:
        """Return color of bulb."""
        return self._color

    @color.setter
    def color(self, color: Color) -> None:
        """Set color of bulb."""
        self.color = color

    @property
    def hsv(self) -> HSV | None:
        """Return color of bulb as HSV."""
        if self._color is not None:
            return self._color.hsv
        return None

    @hsv.setter
    def hsv(
        self, hue: NUMERIC_STRICT, saturation: NUMERIC_STRICT, value: NUMERIC_STRICT
            ) -> None:
        """Set color property with HSV values."""
        self._color = Color.from_hsv(hue, saturation, value)

    @property
    def rgb(self) -> RGB | None:
        """Return color of bulb as RGB."""
        if self._color is not None:
            return self._color.rgb
        return None

    @rgb.setter
    def rgb(self, red: float, green: float, blue: float) -> None:
        """Set color property with RGB values."""
        self._color = Color.from_rgb(red, green, blue)

    @property
    def brightness(self) -> int | None:
        """Brightness of vesync bulb 0-100."""
        if not self.device.supports_brightness:
            logger.warning("Brightness not supported by this bulb")
            return None
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        if not self.device.supports_brightness:
            logger.warning("Brightness not supported by this bulb")
            return
        if Validators.validate_zero_to_hundred(value):
            self._brightness = value

    @property
    def color_temp(self) -> int | None:
        """White color temperature of bulb in percent (0-100)."""
        if not self.device.supports_color_temp:
            logger.warning("Color temperature not supported by this bulb")
            return None
        return self._color_temp

    @color_temp.setter
    def color_temp(self, value: int) -> None:
        if not self.device.supports_color_temp:
            logger.warning("Color temperature not supported by this bulb")
            return
        if Validators.validate_zero_to_hundred(value):
            self._color_temp = value
        else:
            logger.warning("Color temperature must be between 0 and 100")

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return white color temperature of bulb in Kelvin."""
        if not self.device.supports_color_temp:
            logger.warning("Color temperature not supported by this bulb")
            return None
        if self._color_temp is not None:
            return Converters.color_temp_pct_to_kelvin(self._color_temp)
        return None


class VeSyncBulb(VeSyncBaseToggleDevice):
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
            attributes - `hsv` & `rgb`. See [pyvesync.helpers.Color][].
    """

    __slots__ = ()

    # __metaclass__ = ABCMeta

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: BulbMap) -> None:
        """Initialize VeSync smart bulb base class."""
        super().__init__(details, manager, feature_map)
        self.state: BulbState = BulbState(self, details, feature_map)

    @property
    def supports_brightness(self) -> bool:
        """Return True if bulb supports brightness."""
        return BulbFeatures.DIMMABLE in self.features

    @property
    def supports_color_temp(self) -> bool:
        """Return True if bulb supports color temperature."""
        return BulbFeatures.COLOR_TEMP in self.features

    @property
    def supports_multicolor(self) -> bool:
        """Return True if bulb supports backlight."""
        return BulbFeatures.MULTICOLOR in self.features

    @property
    def color(self) -> Color | None:
        """Color Property for VeSync Bulb.

        See [pyvesync.helpers.Color][] for more information.

        Accepts the Color object when setting and returns the color object
        when getting. Wrapper for the `state.color` attribute.
        """
        return self.state.color

    @color.setter
    def color(self, color: Color) -> None:
        self.state.color = color

    @abstractmethod
    async def get_details(self) -> None:
        """Get vesync bulb details.

        This is a legacy function to update devices, **updates should be
        called by `update()`**

        Returns:
            None
        """

    async def set_hsv(self, hue: float, saturation: float, value: float) -> bool:  # noqa: ARG002
        """Set HSV if supported by bulb.

        Args:
            hue (NUMERIC_T): Hue 0-360
            saturation (NUMERIC_T): Saturation 0-100
            value (NUMERIC_T): Value 0-100

        Returns:
            bool: True if successful, False otherwise.

        Raises:
            NotImplementedError: If bulb supports multicolor but has not been subclassed.
        """
        if self.supports_multicolor:
            raise NotImplementedError
        return False

    async def set_rgb(self, red: float, green: float, blue: float) -> bool:  # noqa: ARG002
        """Set RGB if supported by bulb.

        Args:
            red (NUMERIC_T): Red 0-255
            green (NUMERIC_T): green 0-255
            blue (NUMERIC_T): blue 0-255

        Returns:
            bool: True if successful, False otherwise.

        Raises:
            NotImplementedError: If bulb supports multicolor but has not been subclassed.
        """
        if self.supports_multicolor:
            raise NotImplementedError
        return False

    async def update(self) -> None:
        """Update bulb details.

        Calls `get_details()` method to retrieve status from API and
        update the bulb attributes. `get_details()` is overriden by subclasses
        to hit the respective API endpoints.
        """
        await self.get_details()

    def display(self) -> None:
        """Return formatted bulb info to stdout."""
        super().display()
        if self.state.connection_status == 'online':
            disp = []  # initiate list
            if self.supports_brightness:
                disp.append(('Brightness: ', str(self.state.brightness), '%'))
            if self.supports_color_temp:
                disp.append(('White Temperature Pct: ',
                             str(self.state.color_temp), '%'))
                disp.append(('White Temperature Kelvin: ',
                             str(self.state.color_temp_kelvin), 'K'))
            if self.supports_multicolor and self.state.color is not None:
                disp.append(('ColorHSV: ', str(self.state.color.hsv), ''))
                disp.append(('ColorRGB: ', str(self.state.color.rgb), ''))
                disp.append(('ColorMode: ', str(self.state.color_mode), ''))
            if len(disp) > 0:
                for line in disp:
                    print(f'{line[0]:.<30} {line[1]} {line[2]}')

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
        sup_val = orjson.loads(sup)
        if self.state.connection_status == 'online':
            if self.supports_brightness:
                sup_val.update({'Brightness': str(self.state.brightness)})
            if self.supports_color_temp:
                sup_val.update(
                    {'WhiteTemperaturePct': str(self.state.color_temp)})
                sup_val.update(
                    {'WhiteTemperatureKelvin': str(self.state.color_temp_kelvin)})
            if self.supports_multicolor:
                if self.state.hsv is not None:
                    sup_val.update({'ColorHSV': orjson.dumps(
                        dataclasses.asdict(self.state.hsv)).decode()})
                if self.state.rgb is not None:
                    sup_val.update({'ColorRGB': orjson.dumps(
                        dataclasses.asdict(self.state.rgb)).decode()})
                sup_val.update({'ColorMode': str(self.state.color_mode)})
        return orjson.dumps(sup_val,
                            option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
                            ).decode()

    @property
    @deprecated("color_value_rgb is deprecated, use color.rgb instead")
    def color_value_rgb(self) -> RGB | None:
        """Legacy Method .... Depreciated."""
        if self.state.color is not None:
            return self.state.color.rgb
        return None

    @property
    @deprecated("color_value_hsv is deprecated, use color.rgb")
    def color_value_hsv(self) -> HSV | None:
        """Legacy Method .... Depreciated."""
        if self.state.color is not None:
            return self.state.color.hsv
        return None
