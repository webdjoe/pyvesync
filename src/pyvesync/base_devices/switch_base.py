"""Base classes for all VeSync switches."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from typing_extensions import deprecated

from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseToggleDevice, DeviceState

from pyvesync.utils.colors import Color
from pyvesync.const import SwitchFeatures, StrFlag, IntFlag

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
    from pyvesync.utils.colors import HSV, RGB
    from pyvesync.device_map import SwitchMap

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
        "_backlight_color",
        "backlight_status",
        "brightness",
        "indicator_status",
    )

    def __init__(
        self,
        device: VeSyncSwitch,
        details: ResponseDeviceDetailsModel,
        feature_map: SwitchMap
            ) -> None:
        """Initialize VeSync Switch State."""
        super().__init__(device, details, feature_map)
        self.device: VeSyncSwitch = device
        self._backlight_color: Color | str = StrFlag.NOT_SUPPORTED
        self.brightness: int = IntFlag.NOT_SUPPORTED
        self.active_time: int = 0
        self.backlight_status: str = StrFlag.NOT_SUPPORTED
        self.indicator_status: str = StrFlag.NOT_SUPPORTED

    @property
    def backlight_rgb(self) -> RGB | None:
        """Get backlight RGB color."""
        if not self.device.supports_backlight_color:
            logger.warning("Backlight color not supported.")
        if isinstance(self._backlight_color, Color):
            return self._backlight_color.rgb
        return None

    @property
    def backlight_hsv(self) -> HSV | None:
        """Get backlight HSV color."""
        if not self.device.supports_backlight_color:
            logger.warning("Backlight color not supported.")
        if isinstance(self._backlight_color, Color):
            return self._backlight_color.hsv
        return None

    @property
    def backlight_color(self) -> Color | None:
        """Get backlight color."""
        if isinstance(self._backlight_color, Color):
            return self._backlight_color
        logger.warning("Backlight color not supported.")
        return None

    @backlight_color.setter
    def backlight_color(self, color: Color) -> None:
        """Set backlight color."""
        if not self.device.supports_backlight_color:
            logger.warning("Backlight color not supported.")
            return
        self._backlight_color = color


class VeSyncSwitch(VeSyncBaseToggleDevice):
    """Etekcity Switch Base Class.

    Abstract Base Class for Etekcity Switch Devices, inheriting from
    pyvesync.vesyncbasedevice.VeSyncBaseDevice. Should not be instantiated directly,
    subclassed by VeSyncWallSwitch and VeSyncDimmerSwitch.

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

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: SwitchMap) -> None:
        """Initialize Switch Base Class."""
        super().__init__(details, manager, feature_map)
        self.state: SwitchState = SwitchState(self, details, feature_map)

    @property
    @deprecated("Use `supports_dimmable` property instead.")
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
