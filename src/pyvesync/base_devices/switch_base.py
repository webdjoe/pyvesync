"""Base classes for all VeSync switches."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from typing_extensions import deprecated

from pyvesync.base_devices.vesyncbasedevice import DeviceState, VeSyncBaseToggleDevice
from pyvesync.const import SwitchFeatures
from pyvesync.utils.colors import Color

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import SwitchMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
    from pyvesync.utils.colors import HSV, RGB

logger = logging.getLogger(__name__)


class SwitchState(DeviceState):
    """VeSync Switch State Base.

    Args:
        device (VeSyncSwitch): The switch device.
        details (ResponseDeviceDetailsModel): The switch device details.
        feature_map (SwitchMap): The switch feature map.

    Attributes:
        _exclude_serialization (list[str]): List of attributes to exclude from
            serialization.
        active_time (int): Active time of device, defaults to None.
        connection_status (str): Connection status of device.
        device (VeSyncBaseDevice): Device object.
        device_status (str): Device status.
        features (dict): Features of device.
        last_update_ts (int): Last update timestamp of device, defaults to None.
        backlight_color (Color): The backlight color of the switch.
        brightness (int): The brightness level of the switch.
        backlight_status (str): The status of the backlight.
        indicator_status (str): The status of the indicator light.
    """

    __slots__ = (
        '_backlight_color',
        'backlight_status',
        'brightness',
        'indicator_status',
    )

    def __init__(
        self,
        device: VeSyncSwitch,
        details: ResponseDeviceDetailsModel,
        feature_map: SwitchMap,
    ) -> None:
        """Initialize VeSync Switch State."""
        super().__init__(device, details, feature_map)
        self.device: VeSyncSwitch = device
        self._backlight_color: Color | None = None
        self.brightness: int | None = None
        self.active_time: int | None = 0
        self.backlight_status: str | None = None
        self.indicator_status: str | None = None

    @property
    def backlight_rgb(self) -> RGB | None:
        """Get backlight RGB color."""
        if not self.device.supports_backlight_color:
            logger.warning('Backlight color not supported.')
        if isinstance(self._backlight_color, Color):
            return self._backlight_color.rgb
        return None

    @property
    def backlight_hsv(self) -> HSV | None:
        """Get backlight HSV color."""
        if not self.device.supports_backlight_color:
            logger.warning('Backlight color not supported.')
        if isinstance(self._backlight_color, Color):
            return self._backlight_color.hsv
        return None

    @property
    def backlight_color(self) -> Color | None:
        """Get backlight color."""
        if isinstance(self._backlight_color, Color):
            return self._backlight_color
        logger.warning('Backlight color not supported.')
        return None

    @backlight_color.setter
    def backlight_color(self, color: Color | None) -> None:
        """Set backlight color."""
        if not self.device.supports_backlight_color:
            logger.warning('Backlight color not supported.')
            return
        self._backlight_color = color


class VeSyncSwitch(VeSyncBaseToggleDevice):
    """Etekcity Switch Base Class.

    Abstract Base Class for Etekcity Switch Devices, inheriting from
    pyvesync.base_devices.vesyncbasedevice.VeSyncBaseDevice. Should not be
    instantiated directly, subclassed by VeSyncWallSwitch and VeSyncDimmerSwitch.

    Attributes:
        state (SwitchState): Switch state object.
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
        self, details: ResponseDeviceDetailsModel, manager: VeSync, feature_map: SwitchMap
    ) -> None:
        """Initialize Switch Base Class."""
        super().__init__(details, manager, feature_map)
        self.state: SwitchState = SwitchState(self, details, feature_map)

    @property
    @deprecated('Use `supports_dimmable` property instead.')
    def is_dimmable(self) -> bool:
        """Return True if switch is dimmable."""
        return bool(SwitchFeatures.DIMMABLE in self.features)

    @property
    def supports_backlight_color(self) -> bool:
        """Return True if switch supports backlight."""
        return bool(SwitchFeatures.BACKLIGHT_RGB in self.features)

    @property
    def supports_indicator_light(self) -> bool:
        """Return True if switch supports indicator."""
        return bool(SwitchFeatures.INDICATOR_LIGHT in self.features)

    @property
    def supports_backlight(self) -> bool:
        """Return True if switch supports backlight."""
        return bool(SwitchFeatures.BACKLIGHT in self.features)

    @property
    def supports_dimmable(self) -> bool:
        """Return True if switch is dimmable."""
        return bool(SwitchFeatures.DIMMABLE in self.features)

    async def toggle_indicator_light(self, toggle: bool | None = None) -> bool:
        """Toggle indicator light on or off.

        Args:
            toggle (bool): True to turn on, False to turn off. If None, toggles the state

        Returns:
            bool: True if successful, False otherwise.
        """
        del toggle
        if self.supports_indicator_light:
            logger.debug('toggle_indicator_light not configured for %s', self.device_name)
        else:
            logger.debug('toggle_indicator_light not supported for %s', self.device_name)
        return False

    async def turn_on_indicator_light(self) -> bool:
        """Turn on indicator light if supported."""
        return await self.toggle_indicator_light(True)

    async def turn_off_indicator_light(self) -> bool:
        """Turn off indicator light if supported."""
        return await self.toggle_indicator_light(False)

    async def set_backlight_status(
        self,
        status: bool,
        red: int | None = None,
        green: int | None = None,
        blue: int | None = None,
    ) -> bool:
        """Set the backlight status and optionally its color if supported by the device.

        Args:
            status (bool): Backlight status (True for ON, False for OFF).
            red (int | None): RGB green value (0-255), defaults to None.
            green (int | None): RGB green value (0-255), defaults to None.
            blue (int | None): RGB blue value (0-255), defaults to None.

        Returns:
            bool: True if successful, False otherwise.

        """
        del status, red, green, blue
        if self.supports_backlight:
            logger.debug('set_backlight_status not configured for %s', self.device_name)
        else:
            logger.debug('set_backlight_status not supported for %s', self.device_name)
        return False

    async def turn_on_rgb_backlight(self) -> bool:
        """Turn on backlight if supported."""
        return await self.set_backlight_status(True)

    async def turn_off_rgb_backlight(self) -> bool:
        """Turn off backlight if supported."""
        return await self.set_backlight_status(False)

    @deprecated('Use `turn_on_rgb_backlight()` instead.')
    async def turn_rgb_backlight_on(self) -> bool:
        """Turn on RGB backlight if supported."""
        return await self.set_backlight_status(True)

    @deprecated('Use `turn_off_rgb_backlight()` instead.')
    async def turn_rgb_backlight_off(self) -> bool:
        """Turn off RGB backlight if supported."""
        return await self.set_backlight_status(False)

    async def set_backlight_color(self, red: int, green: int, blue: int) -> bool:
        """Set the color of the backlight using RGB.

        Args:
            red (int): Red value (0-255).
            green (int): Green value (0-255).
            blue (int): Blue value (0-255).

        Returns:
            bool: True if successful, False otherwise.
        """
        return await self.set_backlight_status(True, red=red, green=green, blue=blue)

    async def set_brightness(self, brightness: int) -> bool:
        """Set the brightness of the switch if supported.

        Args:
            brightness (int): Brightness value (0-100).

        Returns:
            bool: True if successful, False otherwise.
        """
        del brightness
        if self.supports_dimmable:
            logger.debug('set_brightness not configured for %s', self.device_name)
        else:
            logger.debug('set_brightness not supported for %s', self.device_name)
        return False

    @deprecated('Use `turn_on_indicator_light` instead.')
    async def turn_indicator_light_on(self) -> bool:
        """Deprecated - use turn_on_indicator_light."""
        return await self.toggle_indicator_light(True)

    @deprecated('Use `turn_off_indicator_light` instead.')
    async def turn_indicator_light_off(self) -> bool:
        """Deprecated - use turn_off_indicator_light."""
        return await self.toggle_indicator_light(False)
