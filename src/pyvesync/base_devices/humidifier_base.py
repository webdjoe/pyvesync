"""Base Device and State Class for VeSync Humidifiers."""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING

from typing_extensions import deprecated

from pyvesync.base_devices.vesyncbasedevice import DeviceState, VeSyncBaseToggleDevice
from pyvesync.const import DeviceStatus, HumidifierFeatures, HumidifierModes

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import HumidifierMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel


logger = logging.getLogger(__name__)


class HumidifierState(DeviceState):
    """State Class for VeSync Humidifiers.

    This is the state class for all vesync humidifiers. If there are
    new features or state attributes.

    Attributes:
        auto_preference (int): Auto preference level.
        auto_stop_target_reached (bool): Automatic stop target reached.
        auto_target_humidity (int): Target humidity level.
        automatic_stop_config (bool): Automatic stop configuration.
        display_set_status (str): Display set status.
        display_status (str): Display status.
        drying_mode_auto_switch (str): Drying mode auto switch status.
        drying_mode_level (int): Drying mode level.
        drying_mode_status (str): Drying mode status.
        drying_mode_time_remain (int): Drying mode time remaining.
        filter_life_percent (int): Filter life percentage.
        humidity (int): Current humidity level.
        humidity_high (bool): High humidity status.
        mist_level (int): Mist level.
        mist_virtual_level (int): Mist virtual level.
        mode (str): Current mode.
        nightlight_brightness (int): Nightlight brightness level.
        nightlight_status (str): Nightlight status.
        temperature (int): Current temperature.
        warm_mist_enabled (bool): Warm mist enabled status.
        warm_mist_level (int): Warm mist level.
        water_lacks (bool): Water lacks status.
        water_tank_lifted (bool): Water tank lifted status.
    """

    __slots__ = (
        'auto_preference',
        'auto_stop_target_reached',
        'auto_target_humidity',
        'automatic_stop_config',
        'display_set_status',
        'display_status',
        'drying_mode_auto_switch',
        'drying_mode_level',
        'drying_mode_status',
        'drying_mode_time_remain',
        'filter_life_percent',
        'humidity',
        'humidity_high',
        'mist_level',
        'mist_virtual_level',
        'mode',
        'nightlight_brightness',
        'nightlight_status',
        'temperature',
        'warm_mist_enabled',
        'warm_mist_level',
        'water_lacks',
        'water_tank_lifted',
    )

    def __init__(
        self,
        device: VeSyncHumidifier,
        details: ResponseDeviceDetailsModel,
        feature_map: HumidifierMap,
    ) -> None:
        """Initialize VeSync Humidifier State.

        This state class is used to store the current state of the humidifier.

        Args:
            device (VeSyncHumidifier): The device object.
            details (ResponseDeviceDetailsModel): The device details.
            feature_map (HumidifierMap): The feature map for the device.
        """
        super().__init__(device, details, feature_map)
        self.auto_stop_target_reached: bool = False
        self.auto_target_humidity: int | None = None
        self.automatic_stop_config: bool = False
        self.display_set_status: str = DeviceStatus.UNKNOWN
        self.display_status: str = DeviceStatus.UNKNOWN
        self.humidity: int | None = None
        self.humidity_high: bool = False
        self.mist_level: int | None = None
        self.mist_virtual_level: int | None = None
        self.mode: str | None = None
        self.nightlight_brightness: int | None = None
        self.nightlight_status: str | None = None
        self.warm_mist_enabled: bool | None = None
        self.warm_mist_level: int | None = None
        self.water_lacks: bool = False
        self.water_tank_lifted: bool = False
        self.temperature: int | None = None
        # Superior 6000S States
        self.auto_preference: int | None = None
        self.filter_life_percent: int | None = None
        self.drying_mode_level: int | None = None
        self.drying_mode_auto_switch: str | None = None
        self.drying_mode_status: str | None = None
        self.drying_mode_time_remain: int | None = None

    @property
    def automatic_stop(self) -> bool:
        """Return the automatic stop status.

        Returns:
            bool: True if automatic stop is enabled, False otherwise.
        """
        return self.automatic_stop_config

    @property
    @deprecated('Use auto_stop_target_reached instead.')
    def automatic_stop_target_reached(self) -> bool:
        """Deprecated function.

        Returns:
            bool: True if automatic stop target is reached, False otherwise.
        """
        return self.auto_stop_target_reached

    @property
    def target_humidity(self) -> int | None:
        """Return the target humidity level.

        Returns:
            int: Target humidity level.
        """
        return self.auto_target_humidity

    @property
    def auto_humidity(self) -> int | None:
        """Return the auto humidity level.

        Returns:
            int: Auto humidity level.
        """
        return self.auto_target_humidity

    @property
    def auto_enabled(self) -> bool:
        """Return True if auto mode is enabled."""
        return self.mode in [HumidifierModes.AUTO, self.mode, HumidifierModes.HUMIDITY]

    @property
    @deprecated('Use humidity property instead.')
    def humidity_level(self) -> int | None:
        """Deprecated function.

        Returns:
            int | None: Humidity level.
        """
        return self.humidity

    @property
    def drying_mode_state(self) -> str | None:
        """Return the drying mode state.

        Returns:
            str | None: Drying mode state.
        """
        return self.drying_mode_status

    @property
    def drying_mode_seconds_remaining(self) -> int | None:
        """Return the drying mode seconds remaining.

        Return:
            int | None: Drying mode seconds remaining.
        """
        return self.drying_mode_time_remain

    @property
    def drying_mode_enabled(self) -> bool:
        """Return True if drying mode is enabled.

        Returns:
            bool | None: True if drying mode is enabled, False otherwise.
        """
        return self.drying_mode_status == DeviceStatus.ON


class VeSyncHumidifier(VeSyncBaseToggleDevice):
    """VeSyncHumdifier Base Class.

    This is the base device to be inherited by all Humidifier devices.
    This class only holds the device configuration and static attributes.
    The state attribute holds the current state.

    Attributes:
        state (HumidifierState): The state of the humidifier.
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
        mist_levels (list): List of mist levels.
        mist_modes (list): List of mist modes.
        target_minmax (tuple): Tuple of target min and max values.
        warm_mist_levels (list): List of warm mist levels.

    """

    __slots__ = (
        'mist_levels',
        'mist_modes',
        'target_minmax',
        'warm_mist_levels',
    )

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: HumidifierMap,
    ) -> None:
        """Initialize VeSync Humidifier Class.

        Args:
            details (ResponseDeviceDetailsModel): The device details.
            manager (VeSync): The VeSync manager.
            feature_map (HumidifierMap): The feature map for the device.
        """
        super().__init__(details, manager, feature_map)
        self.state: HumidifierState = HumidifierState(self, details, feature_map)
        self.mist_modes: dict[str, str] = feature_map.mist_modes
        self.mist_levels: list[str | int] = feature_map.mist_levels
        self.features: list[str] = feature_map.features
        self.warm_mist_levels: list[int | str] = feature_map.warm_mist_levels
        self.target_minmax: tuple[int, int] = feature_map.target_minmax

    @property
    def supports_warm_mist(self) -> bool:
        """Return True if the humidifier supports warm mist.

        Returns:
            bool: True if warm mist is supported, False otherwise.
        """
        return HumidifierFeatures.WARM_MIST in self.features

    @property
    def supports_nightlight(self) -> bool:
        """Return True if the humidifier supports nightlight.

        Returns:
            bool: True if nightlight is supported, False otherwise.
        """
        return HumidifierFeatures.NIGHTLIGHT in self.features

    @property
    def supports_nightlight_brightness(self) -> bool:
        """Return True if the humidifier supports nightlight brightness."""
        return HumidifierFeatures.NIGHTLIGHT_BRIGHTNESS in self.features

    @property
    def supports_drying_mode(self) -> bool:
        """Return True if the humidifier supports drying mode."""
        return HumidifierFeatures.DRYING_MODE in self.features

    async def toggle_automatic_stop(self, toggle: bool | None = None) -> bool:
        """Toggle automatic stop.

        Args:
            toggle (bool | None): True to enable automatic stop, False to disable.

        Returns:
            bool: Success of request.
        """
        del toggle
        logger.warning('Automatic stop is not supported or configured for this device.')
        return False

    async def toggle_display(self, toggle: bool) -> bool:
        """Toggle the display on/off.

        Args:
            toggle (bool): True to turn on the display, False to turn off.

        Returns:
            bool: Success of request.
        """
        del toggle
        logger.warning('Display is not supported or configured for this device.')
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
        """Turn on the display.

        Returns:
            bool: Success of request.
        """
        return await self.toggle_display(True)

    async def turn_off_display(self) -> bool:
        """Turn off the display.

        Returns:
            bool: Success of request.
        """
        return await self.toggle_display(False)

    async def turn_on_automatic_stop(self) -> bool:
        """Turn on automatic stop.

        Returns:
            bool: Success of request.
        """
        return await self.toggle_automatic_stop(True)

    async def turn_off_automatic_stop(self) -> bool:
        """Turn off automatic stop.

        Returns:
            bool: Success of request.
        """
        return await self.toggle_automatic_stop(False)

    async def set_auto_mode(self) -> bool:
        """Set Humidifier to Auto Mode.

        Returns:
            bool: Success of request.
        """
        if HumidifierModes.AUTO in self.mist_modes:
            return await self.set_mode(HumidifierModes.AUTO)
        logger.debug('Auto mode not supported for this device.')
        return await self.set_mode(HumidifierModes.AUTO)

    async def set_manual_mode(self) -> bool:
        """Set Humidifier to Manual Mode.

        Returns:
            bool: Success of request.
        """
        if HumidifierModes.MANUAL in self.mist_modes:
            return await self.set_mode(HumidifierModes.MANUAL)
        logger.debug('Manual mode not supported for this device.')
        return await self.set_mode(HumidifierModes.MANUAL)

    async def set_sleep_mode(self) -> bool:
        """Set Humidifier to Sleep Mode.

        Returns:
            bool: Success of request.
        """
        if HumidifierModes.SLEEP in self.mist_modes:
            return await self.set_mode(HumidifierModes.SLEEP)
        logger.debug('Sleep mode not supported for this device.')
        return await self.set_mode(HumidifierModes.SLEEP)

    async def set_humidity(self, humidity: int) -> bool:
        """Set Humidifier Target Humidity.

        Args:
            humidity (int): Target humidity level.

        Returns:
            bool: Success of request.
        """
        del humidity
        logger.debug('Target humidity is not supported or configured for this device.')
        return False

    async def set_nightlight_brightness(self, brightness: int) -> bool:
        """Set Humidifier night light brightness.

        Args:
            brightness (int): Target night light brightness.

        Returns:
            bool: Success of request.
        """
        del brightness
        if not self.supports_nightlight_brightness:
            logger.debug('Nightlight brightness is not supported for this device.')
            return False
        logger.debug('Nightlight brightness has not been configured.')
        return False

    async def set_warm_level(self, warm_level: int) -> bool:
        """Set Humidifier Warm Level.

        Args:
            warm_level (int): Target warm level.

        Returns:
            bool: Success of request.
        """
        del warm_level
        if self.supports_warm_mist:
            logger.debug('Warm level has not been configured.')
            return False
        logger.debug('Warm level is not supported for this device.')
        return False

    async def toggle_drying_mode(self, toggle: bool | None = None) -> bool:
        """enable/disable drying filters after turning off."""
        del toggle
        if self.supports_drying_mode:
            logger.debug('Drying mode is not configured for this device.')
            return False
        logger.debug('Drying mode is not supported for this device.')
        return False
