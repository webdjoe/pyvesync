"""Base Device and State Class for VeSync Humidifiers."""
from __future__ import annotations
from abc import abstractmethod
import logging
from typing import TYPE_CHECKING
from typing_extensions import deprecated

from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseDevice, DeviceState
from pyvesync.const import (
    HumidifierFeatures,
    HumidifierModes,
    DeviceStatus,
    IntFlag,
    StrFlag
    )

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.data_models.device_list_models import ResponseDeviceDetailsModel
    from pyvesync.device_map import HumidifierMap
    from pyvesync.helper_utils.helpers import Timer


logger = logging.getLogger(__name__)


class HumidifierState(DeviceState):
    """State Class for VeSync Humidifiers."""

    __slots__ = (
        "auto_preference",
        "auto_stop_target_reached",
        "auto_target_humidity",
        "automatic_stop_config",
        "child_lock_status",
        "display_set_status",
        "display_status",
        "drying_mode_auto_switch",
        "drying_mode_level",
        "drying_mode_status",
        "drying_mode_time_remain",
        "filter_life_percent",
        "humidity",
        "humidity_high",
        "mist_level",
        "mist_virtual_level",
        "mode",
        "nightlight_brightness",
        "nightlight_status",
        "temperature",
        "timer",
        "warm_mist_enabled",
        "warm_mist_level",
        "water_lacks",
        "water_tank_lifted",
    )

    def __init__(self, device: VeSyncHumidifier, details: ResponseDeviceDetailsModel,
                 feature_map: HumidifierMap) -> None:
        """Initialize VeSync Humidifier State."""
        super().__init__(device, details, feature_map)
        self.auto_stop_target_reached: bool = False
        self.auto_target_humidity: int = IntFlag.NOT_SUPPORTED
        self.automatic_stop_config: bool = False
        self.display_set_status: str = DeviceStatus.UNKNOWN
        self.display_status: str = DeviceStatus.UNKNOWN
        self.humidity: int = IntFlag.NOT_SUPPORTED
        self.humidity_high: bool = False
        self.mist_level: int | None = None
        self.mist_virtual_level: int | None = None
        self.mode: str = HumidifierModes.UNKNOWN
        self.nightlight_brightness: int = IntFlag.NOT_SUPPORTED
        self.nightlight_status: str = StrFlag.NOT_SUPPORTED
        self.warm_mist_enabled: bool | None = None
        self.warm_mist_level: int = IntFlag.NOT_SUPPORTED
        self.water_lacks: bool = False
        self.water_tank_lifted: bool = False
        self.temperature: int = IntFlag.NOT_SUPPORTED
        self.timer: Timer | None = None
        # Superior 6000S States
        self.auto_preference: int = IntFlag.NOT_SUPPORTED
        self.filter_life_percent: int = IntFlag.NOT_SUPPORTED
        self.drying_mode_level: int = IntFlag.NOT_SUPPORTED
        self.drying_mode_auto_switch: str = StrFlag.NOT_SUPPORTED
        self.drying_mode_status: str = StrFlag.NOT_SUPPORTED
        self.drying_mode_time_remain: int = IntFlag.NOT_SUPPORTED

    @property
    def automatic_stop(self) -> bool:
        """Return the automatic stop status."""
        return self.automatic_stop_config

    @property
    @deprecated("Use auto_stop_target_reached instead.")
    def automatic_stop_target_reached(self) -> bool:
        """Deprecated function."""
        return self.auto_stop_target_reached

    @property
    def target_humidity(self) -> int:
        """Return the target humidity level."""
        return self.auto_target_humidity

    @property
    def auto_humidity(self) -> int:
        """Return the auto humidity level."""
        return self.auto_target_humidity

    @property
    def auto_enabled(self) -> bool:
        """Return True if auto mode is enabled."""
        return self.mode in [HumidifierModes.AUTO, self.mode, HumidifierModes.HUMIDITY]

    @property
    @deprecated("Use humidity property instead.")
    def humidity_level(self) -> int | None:
        """Deprecated function."""
        if self.humidity == IntFlag.NOT_SUPPORTED:
            return None
        return self.humidity

    @property
    def drying_mode_state(self) -> str | None:
        """Return the drying mode state."""
        if self.drying_mode_status == StrFlag.NOT_SUPPORTED:
            return None
        return self.drying_mode_status

    @property
    def drying_mode_seconds_remaining(self) -> int | None:
        """Return the drying mode seconds remaining."""
        if self.drying_mode_time_remain == IntFlag.NOT_SUPPORTED:
            return None
        return self.drying_mode_time_remain

    @property
    def drying_mode_enabled(self) -> bool | None:
        """Return True if drying mode is enabled."""
        if self.drying_mode_status == StrFlag.NOT_SUPPORTED:
            return None
        return self.drying_mode_status == DeviceStatus.ON


class VeSyncHumidifier(VeSyncBaseDevice):
    """VeSyncHumdifier Base Class."""

    __slots__ = (
        "mist_levels",
        "mist_modes",
        "target_minmax",
        "warm_mist_levels",
    )

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: HumidifierMap) -> None:
        """Initialize VeSync Humidifier Class."""
        super().__init__(details, manager, feature_map)
        self.state: HumidifierState = HumidifierState(self, details, feature_map)
        self.mist_modes = feature_map.mist_modes
        self.mist_levels = feature_map.mist_levels
        self.features = feature_map.features
        self.warm_mist_levels = feature_map.warm_mist_levels
        self.target_minmax = feature_map.target_minmax

    @property
    def supports_warm_mist(self) -> bool:
        """Return True if the humidifier supports warm mist."""
        return HumidifierFeatures.WARM_MIST in self.features

    @property
    def supports_nightlight(self) -> bool:
        """Return True if the humidifier supports nightlight."""
        return HumidifierFeatures.NIGHTLIGHT in self.features

    async def toggle_automatic_stop(self, toggle: bool | None = None) -> bool:
        """Toggle automatic stop."""
        del toggle
        logger.warning("Automatic stop is not supported or configured for this device.")
        return False

    async def toggle_display(self, toggle: bool) -> bool:
        """Toggle the display on/off."""
        del toggle
        logger.warning("Display is not supported or configured for this device.")
        return False

    @abstractmethod
    async def set_mode(self, mode: str) -> bool:
        """Set Humidifier Mode.

        Args:
            mode (str): Humidifier mode.

        Returns:
            bool: Success of request.

        Note:
            Modes for device are defined in `self.mist_modes`.
        """

    @abstractmethod
    async def set_mist_level(self, level: int) -> bool:
        """Set Mist Level for Humidifier.

        Args:
            level (int): Mist level.

        Returns:
            bool: Success of request.

        Note:
            Mist levels are defined in `self.mist_levels`.
        """

    async def turn_on_display(self) -> bool:
        """Turn on the display."""
        return await self.toggle_display(True)

    async def turn_off_display(self) -> bool:
        """Turn off the display."""
        return await self.toggle_display(False)

    async def turn_on_automatic_stop(self) -> bool:
        """Turn on automatic stop."""
        return await self.toggle_automatic_stop(True)

    async def turn_off_automatic_stop(self) -> bool:
        """Turn off automatic stop."""
        return await self.toggle_automatic_stop(False)

    async def set_auto_mode(self) -> bool:
        """Set Humidifier to Auto Mode."""
        if HumidifierModes.AUTO in self.mist_modes:
            return await self.set_mode(HumidifierModes.AUTO)
        logger.debug("Auto mode not supported for this device.")
        return await self.set_mode(HumidifierModes.AUTO)

    async def set_manual_mode(self) -> bool:
        """Set Humidifier to Manual Mode."""
        if HumidifierModes.MANUAL in self.mist_modes:
            return await self.set_mode(HumidifierModes.MANUAL)
        logger.debug("Manual mode not supported for this device.")
        return await self.set_mode(HumidifierModes.MANUAL)

    async def set_sleep_mode(self) -> bool:
        """Set Humidifier to Sleep Mode."""
        if HumidifierModes.SLEEP in self.mist_modes:
            return await self.set_mode(HumidifierModes.SLEEP)
        logger.debug("Sleep mode not supported for this device.")
        return await self.set_mode(HumidifierModes.SLEEP)

    # async def set_humidity_mode(self) -> bool:
    #     """Set Humidifier to Humidity Mode."""
    #     if HumidifierModes.HUMIDITY in self.mist_modes:
    #         return await self.set_mode(HumidifierModes.HUMIDITY)
    #     logger.debug("Humidity mode not supported for this device.")
    #     return await self.set_mode(HumidifierModes.HUMIDITY)
