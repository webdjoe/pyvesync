"""Air Purifier Base Class."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from abc import abstractmethod
from typing_extensions import deprecated

from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseToggleDevice, DeviceState
from pyvesync.const import (
    FanModes,
    DeviceStatus,
    FanSleepPreference,
    StrFlag,
    )

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.data_models.device_list_models import ResponseDeviceDetailsModel
    from pyvesync.device_map import FanMap
    from pyvesync.helper_utils.helpers import Timer


logger = logging.getLogger(__name__)


class FanState(DeviceState):
    """Base state class for Purifiers."""

    __slots__ = (
        "display_set_state",
        "display_status",
        "displaying_type",
        "fan_level",
        "fan_set_level",
        "humidity",
        "mode",
        "mute_set_state",
        "mute_status",
        "oscillation_set_state",
        "oscillation_status",
        "sleep_change_fan_level",
        "sleep_fallasleep_remain",
        "sleep_oscillation_switch",
        "sleep_preference_type",
        "temperature",
        "thermal_comfort",
        "timer",
    )

    def __init__(
        self,
        device: VeSyncFanBase,
        details: ResponseDeviceDetailsModel,
        feature_map: FanMap,
    ) -> None:
        """Initialize Purifier State."""
        super().__init__(device, details, feature_map)
        self.mode: str = FanModes.UNKNOWN
        self.fan_level: int | None = None
        self.fan_set_level: int | None = None
        self.humidity: int | None = None
        self.temperature: int | None = None
        self.thermal_comfort: int | None = None
        self.sleep_preference_type: str | None = FanSleepPreference.UNKNOWN
        self.sleep_fallasleep_remain: str | None = DeviceStatus.UNKNOWN
        self.sleep_oscillation_switch: str | None = DeviceStatus.UNKNOWN
        self.sleep_change_fan_level: str | None = DeviceStatus.UNKNOWN
        self.mute_status: str = DeviceStatus.UNKNOWN
        self.mute_set_state: str = DeviceStatus.UNKNOWN
        self.oscillation_status: str = DeviceStatus.UNKNOWN
        self.oscillation_set_state: str = DeviceStatus.UNKNOWN
        self.display_status: str = DeviceStatus.UNKNOWN
        self.display_set_state: str = DeviceStatus.UNKNOWN
        self.displaying_type: str = StrFlag.NOT_SUPPORTED
        self.timer: Timer | None = None


class VeSyncFanBase(VeSyncBaseToggleDevice):
    """Base device for vesync air purifiers."""

    __slots__ = (
        "fan_levels",
        "modes",
        "sleep_preferences",
    )

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: FanMap,
    ) -> None:
        """Initialize VeSync Purifier Base Class."""
        super().__init__(details, manager, feature_map)
        self.features: list[str] = feature_map.features
        self.state: FanState = FanState(self, details, feature_map)
        self.modes: list[str] = feature_map.modes
        self.fan_levels: list[int] = feature_map.fan_levels
        self.sleep_preferences: list[str] = feature_map.sleep_preferences

    async def toggle_display(self, toggle: bool) -> bool:
        """Toggle Display on/off.

        Args:
            toggle (bool): Display state.

        Returns:
            bool: Success of request.
        """
        del toggle
        return False

    async def turn_on_display(self) -> bool:
        """Turn on Display.

        Returns:
            bool: Success of request
        """
        return await self.toggle_display(True)

    async def turn_off_display(self) -> bool:
        """Turn off Display.

        Returns:
            bool: Success of request
        """
        return await self.toggle_display(False)

    @abstractmethod
    async def set_mode(self, mode: str) -> bool:
        """Set Purifier Mode.

        Returns:
            bool: Success of request.
        """

    @abstractmethod
    async def set_fan_speed(self, speed: int | None = None) -> bool:
        """Set Purifier Fan Speed.

        Args:
            speed (int, optional): Fan speed level according to device specs.

        Returns:
            bool: Success of request.
        """

    async def set_auto_mode(self) -> bool:
        """Set Purifier to Auto Mode.

        Returns:
            bool: Success of request.

        Note:
            This method is not supported by all devices, will return
            false with warning debug message if not supported.
        """
        if FanModes.AUTO in self.modes:
            return await self.set_mode(FanModes.AUTO)
        logger.warning("Auto mode not supported for this device.")
        return False

    async def set_advanced_sleep_mode(self) -> bool:
        """Set Purifier to Advanced Sleep Mode.

        Returns:
            bool: Success of request.

        Note:
            This method is not supported by all devices, will return
            false with warning debug message if not supported.
        """
        if FanModes.ADVANCED_SLEEP in self.modes:
            return await self.set_mode(FanModes.ADVANCED_SLEEP)
        logger.warning("Advanced Sleep mode not supported for this device.")
        return False

    async def set_sleep_mode(self) -> bool:
        """Set Purifier to Sleep Mode.

        This is also referred to as Advanced Sleep Mode on some devices.

        Returns:
            bool: Success of request.

        Note:
            This method is not supported by all devices, will return
            false with warning debug message if not supported.
        """
        if FanModes.ADVANCED_SLEEP in self.modes:
            return await self.set_mode(FanModes.ADVANCED_SLEEP)
        logger.warning("Sleep mode not supported for this device.")
        return False

    async def set_manual_mode(self) -> bool:
        """Set Purifier to Manual Mode - Normal Mode.

        Returns:
            bool: Success of request.

        Note:
            This method is not supported by all devices, will return
            false with warning debug message if not supported.
        """
        if FanModes.NORMAL in self.modes:
            return await self.set_mode(FanModes.NORMAL)
        logger.warning("Manual mode not supported for this device.")
        return False

    async def set_normal_mode(self) -> bool:
        """Set Purifier to Normal Mode.

        Returns:
            bool: Success of request.

        Note:
            This method is not supported by all devices, will return
            false with warning debug message if not supported.
        """
        if FanModes.NORMAL in self.modes:
            return await self.set_mode(FanModes.NORMAL)
        logger.warning("Normal mode not supported for this device.")
        return False

    async def set_turbo_mode(self) -> bool:
        """Set Purifier to Turbo Mode.

        Returns:
            bool: Success of request.

        Note:
            This method is not supported by all devices, will return
            false with warning debug message if not supported.
        """
        if FanModes.TURBO in self.modes:
            return await self.set_mode(FanModes.TURBO)
        logger.warning("Turbo mode not supported for this device.")
        return False

    @deprecated("Use `set_normal_mode` method instead")
    async def normal_mode(self) -> bool:
        """Set mode to normal."""
        return await self.set_normal_mode()

    @deprecated("Use `set_manual_mode` method instead")
    async def manual_mode(self) -> bool:
        """Adapter to set mode to normal."""
        return await self.set_normal_mode()

    @deprecated("Use `set_advanced_sleep_mode` method instead")
    async def advanced_sleep_mode(self) -> bool:
        """Set advanced sleep mode."""
        return await self.set_mode('advancedSleep')

    @deprecated("Use `set_sleep_mode` method instead")
    async def sleep_mode(self) -> bool:
        """Adapter to set advanced sleep mode."""
        return await self.set_advanced_sleep_mode()

    @deprecated("Use `set_mode` method instead")
    async def mode_toggle(self, mode: str) -> bool:
        """Set mode to specified mode."""
        return await self.set_mode(mode)
