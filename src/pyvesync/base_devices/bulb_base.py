"""Base classes for all VeSync bulbs."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from typing_extensions import deprecated

from pyvesync.base_devices.vesyncbasedevice import DeviceState, VeSyncBaseToggleDevice
from pyvesync.const import BulbFeatures
from pyvesync.utils.colors import HSV, RGB, Color
from pyvesync.utils.helpers import Converters, Validators

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import BulbMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel


logger = logging.getLogger(__name__)


class BulbState(DeviceState):
    """VeSync Bulb State Base.

    Base class to hold all state attributes for bulb devices. Inherits from
    [`DeviceState`][pyvesync.base_devices.vesyncbasedevice.DeviceState]. This
    class should not be used directly for devices, but rather subclassed for each
    bulb type.

    Args:
        device (VeSyncBulb): VeSync Bulb device.
        details (ResponseDeviceDetailsModel): Device details from API.
        feature_map (BulbMap): Feature map for bulb.

    Attributes:
        _exclude_serialization (list[str]): List of attributes to exclude from
            serialization.
        active_time (int): Active time of device, defaults to None.
        connection_status (str): Connection status of device.
        device (VeSyncBaseDevice): Device object.
        device_status (str): Device status.
        features (dict): Features of device.
        last_update_ts (int): Last update timestamp of device, defaults to None.
        brightness (int): Brightness of bulb (0-100).
        color_temp (int): White color temperature of bulb in percent (0-100).
        color_temp_kelvin (int): White color temperature of bulb in Kelvin.
        color (Color): Color of bulb in the form of a dataclass with two namedtuple
            attributes - `hsv` & `rgb`. See
            [utils.colors.Colors][pyvesync.utils.colors.Color].
        color_mode (str): Color mode of bulb.
        color_modes (list[str]): List of color modes supported by bulb.

    Methods:
        update_ts: Update last update timestamp.
        to_dict: Dump state to JSON.
        to_json: Dump state to JSON string.
        to_jsonb: Dump state to JSON bytes.
        as_tuple: Convert state to tuple of (name, value) tuples.

    See Also:
        - [`VeSyncBulb`][pyvesync.base_devices.bulb_base.VeSyncBulb]
        - [`ResponseDeviceDetailsModel`][
            pyvesync.models.device_list_models.ResponseDeviceDetailsModel]
        - [`BulbMap`][pyvesync.device_map.BulbMap]
    """

    __slots__ = ('_brightness', '_color', '_color_temp', 'color_mode', 'color_modes')

    def __init__(
        self,
        device: VeSyncBulb,
        details: ResponseDeviceDetailsModel,
        feature_map: BulbMap,
    ) -> None:
        """Initialize VeSync Bulb State Base."""
        super().__init__(device, details, feature_map)
        self._exclude_serialization: list[str] = ['rgb', 'hsv']
        self.features: list[str] = feature_map.features
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
    def color(self, color: Color | None) -> None:
        """Set color of bulb."""
        self._color = color

    @property
    def hsv(self) -> HSV | None:
        """Return color of bulb as HSV."""
        if self._color is not None:
            return self._color.hsv
        return None

    @hsv.setter
    def hsv(self, hsv_object: HSV | None) -> None:
        """Set color property with HSV values."""
        if hsv_object is None:
            self._color = None
            return
        self._color = Color(hsv_object)

    @property
    def rgb(self) -> RGB | None:
        """Return color of bulb as RGB."""
        if self._color is not None:
            return self._color.rgb
        return None

    @rgb.setter
    def rgb(self, rgb_object: RGB | None) -> None:
        """Set color property with RGB values."""
        if rgb_object is None:
            self._color = None
            return
        self._color = Color(rgb_object)

    @property
    def brightness(self) -> int | None:
        """Brightness of vesync bulb 0-100."""
        if not self.device.supports_brightness:
            logger.warning('Brightness not supported by this bulb')
            return None
        return self._brightness

    @brightness.setter
    def brightness(self, value: int | None) -> None:
        if not self.device.supports_brightness:
            logger.warning('Brightness not supported by this bulb')
            return
        if Validators.validate_zero_to_hundred(value):
            self._brightness = value
        else:
            self._brightness = None

    @property
    def color_temp(self) -> int | None:
        """White color temperature of bulb in percent (0-100)."""
        if not self.device.supports_color_temp:
            logger.warning('Color temperature not supported by this bulb')
            return None
        return self._color_temp

    @color_temp.setter
    def color_temp(self, value: int) -> None:
        if not self.device.supports_color_temp:
            logger.warning('Color temperature not supported by this bulb')
            return
        if Validators.validate_zero_to_hundred(value):
            self._color_temp = value
        else:
            logger.warning('Color temperature must be between 0 and 100')

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return white color temperature of bulb in Kelvin."""
        if not self.device.supports_color_temp:
            logger.warning('Color temperature not supported by this bulb')
            return None
        if self._color_temp is not None:
            return Converters.color_temp_pct_to_kelvin(self._color_temp)
        return None


class VeSyncBulb(VeSyncBaseToggleDevice[BulbState]):
    """Base class for VeSync Bulbs.

    Abstract base class to provide methods for controlling and
    getting details of VeSync bulbs. Inherits from
    [`VeSyncBaseDevice`][pyvesync.base_devices.vesyncbasedevice.VeSyncBaseDevice]. This
    class should not be used directly for devices, but rather subclassed for each bulb.

    Args:
        details (ResponseDeviceDetailsModel): Device details from API.
        manager (VeSync): VeSync API manager.
        feature_map (BulbMap): Feature map for bulb.

    Attributes:
        state (BulbState): Device state object
            Each device has a separate state base class in the base_devices module.
        last_response (ResponseInfo): Last response from API call.
        manager (VeSync): Manager object for API calls.
        device_name (str): Name of device.
        device_image (str): URL for device image.
        cid (str): Device ID.
        connection_type (str): Connection type of device.
        device_type (str): Type of device.
        type (str): Type of device.
        uuid (str): UUID of device, not always present.
        config_module (str): Configuration module of device.
        mac_id (str): MAC ID of device.
        current_firm_version (str): Current firmware version of device.
        device_region (str): Region of device. (US, EU, etc.)
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
    """

    __slots__ = ()

    def __init__(
        self, details: ResponseDeviceDetailsModel, manager: VeSync, feature_map: BulbMap
    ) -> None:
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

    async def set_hsv(self, hue: float, saturation: float, value: float) -> bool:
        """Set HSV if supported by bulb.

        Args:
            hue (float): Hue 0-360
            saturation (float): Saturation 0-100
            value (float): Value 0-100

        Returns:
            bool: True if successful, False otherwise.
        """
        del hue, saturation, value
        if not self.supports_multicolor:
            logger.debug('Color mode is not supported on this bulb.')
        else:
            logger.debug('set_hsv not configured for %s bulb', self.device_type)
        return False

    async def set_rgb(self, red: float, green: float, blue: float) -> bool:
        """Set RGB if supported by bulb.

        Args:
            red (float): Red 0-255
            green (float): green 0-255
            blue (float): blue 0-255

        Returns:
            bool: True if successful, False otherwise.
        """
        del red, green, blue
        if not self.supports_multicolor:
            logger.debug('Color mode is not supported on this bulb.')
        else:
            logger.debug('set_rgb not configured for %s bulb', self.device_type)
        return False

    async def set_brightness(self, brightness: int) -> bool:
        """Set brightness if supported by bulb.

        Args:
            brightness (NUMERIC_T): Brightness 0-100

        Returns:
            bool: True if successful, False otherwise.
        """
        del brightness
        logger.warning('Brightness not supported/configured by this bulb')
        return False

    async def set_color_temp(self, color_temp: int) -> bool:
        """Set color temperature if supported by bulb.

        Args:
            color_temp (int): Color temperature 0-100

        Returns:
            bool: True if successful, False otherwise.
        """
        del color_temp
        if self.supports_color_temp:
            logger.debug('Color temperature is not configured on this bulb.')
        else:
            logger.debug('Color temperature not supported by this bulb')
        return False

    async def set_white_mode(self) -> bool:
        """Set white mode if supported by bulb.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.supports_multicolor:
            logger.debug('White mode is not configured on this bulb.')
        else:
            logger.warning('White mode not supported by this bulb')
        return False

    async def set_color_mode(self, color_mode: str) -> bool:
        """Set color mode if supported by bulb.

        Args:
            color_mode (str): Color mode to set.

        Returns:
            bool: True if successful, False otherwise.
        """
        del color_mode
        if self.supports_multicolor:
            logger.debug('Color mode is not configured on this bulb.')
        else:
            logger.warning('Color mode not supported by this bulb')
        return False

    @deprecated('Use `set_white_mode` instead.')
    async def enable_white_mode(self) -> bool:
        """Enable white mode if supported by bulb."""
        return await self.set_white_mode()
