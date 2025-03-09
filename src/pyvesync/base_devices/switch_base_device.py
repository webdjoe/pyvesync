"""Base classes for all VeSync switches."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from deprecated import deprecated

from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseToggleDevice, DeviceState

from pyvesync.helper_utils.helpers import Validators
from pyvesync.const import SwitchFeatures

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.data_models.device_list_models import ResponseDeviceDetailsModel
    from pyvesync.helper_utils.colors import HSV, RGB, Color
    from pyvesync.device_map import SwitchMap

logger = logging.getLogger(__name__)


class SwitchState(DeviceState):
    """VeSync Switch State Base."""

    __slots__ = (
        "_backlight_color",
        "_brightness",
        "backlight_status",
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
        self._backlight_color: Color | None = None
        self._brightness: int | None = None
        self.active_time: int = 0
        self.backlight_status: str = "off"
        self.indicator_status: str = "off"

    @property
    def backlight_rgb(self) -> RGB | None:
        """Get backlight RGB color."""
        if not self.device.supports_backlight_color:
            logger.warning("Backlight color not supported.")
        if self._backlight_color is not None:
            return self._backlight_color.rgb
        return None

    @property
    def backlight_hsv(self) -> HSV | None:
        """Get backlight HSV color."""
        if not self.device.supports_backlight_color:
            logger.warning("Backlight color not supported.")
        if self._backlight_color is not None:
            return self._backlight_color.hsv
        return None

    @property
    def backlight_color(self) -> Color | None:
        """Get backlight color."""
        if not self.device.supports_backlight_color:
            logger.warning("Backlight color not supported.")
        return self._backlight_color

    @backlight_color.setter
    def backlight_color(self, color: Color) -> None:
        """Set backlight color."""
        if not self.device.supports_backlight_color:
            logger.warning("Backlight color not supported.")
            return
        self._backlight_color = color

    @property
    def brightness(self) -> int | None:
        """Get brightness."""
        if not self.device.supports_dimmable:
            logger.warning("Dimming not supported.")
        return self._brightness

    @brightness.setter
    def brightness(self, brightness: int) -> None:
        if not self.device.supports_dimmable:
            logger.warning("Dimming not supported.")
            return
        if Validators.validate_zero_to_hundred(brightness):
            self._brightness = brightness
        else:
            raise ValueError("Brightness must be between 0 and 100.")


class VeSyncSwitch(VeSyncBaseToggleDevice):
    """Etekcity Switch Base Class.

    Abstract Base Class for Etekcity Switch Devices, inherting from
    pyvesync.vesyncbasedevice.VeSyncBaseDevice. Should not be instantiated directly,
    subclassed by VeSyncWallSwitch and VeSyncDimmerSwitch.

    Attributes:
        features (list): List of features supported by the switch device.
        details (dict): Dictionary of switch device details.
        state (SwitchState): Switch state object.
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
