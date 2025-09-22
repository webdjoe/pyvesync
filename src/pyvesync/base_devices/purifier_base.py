"""Air Purifier Base Class."""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING

from typing_extensions import deprecated

from pyvesync.base_devices.vesyncbasedevice import DeviceState, VeSyncBaseToggleDevice
from pyvesync.const import (
    AirQualityLevel,
    DeviceStatus,
    NightlightModes,
    PurifierFeatures,
    PurifierModes,
)

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import PurifierMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel


logger = logging.getLogger(__name__)


class PurifierState(DeviceState):
    """Base state class for Purifiers.

    Attributes:
        active_time (int): Active time of device, defaults to None.
        connection_status (str): Connection status of device.
        device (VeSyncOutlet): Device object.
        device_status (str): Device status.
        features (dict): Features of device.
        last_update_ts (int): Last update timestamp of device, defaults to None.
        mode (str): Current mode of the purifier.
        fan_level (int): Current fan level of the purifier.
        fan_set_level (int): Set fan level of the purifier.
        filter_life (int): Filter life percentage of the purifier.
        auto_preference_type (str): Auto preference type of the purifier.
        auto_room_size (int): Auto room size of the purifier.
        air_quality_level (AirQualityLevel): Air quality level of the purifier.
        child_lock (bool): Child lock status of the purifier.
        display_status (str): Display status of the purifier.
        display_set_status (str): Display set status of the purifier.
        display_forever (bool): Display forever status of the purifier.
        timer (Timer): Timer object for the purifier.
        pm25 (int): PM2.5 value of the purifier.
        pm1 (int): PM1 value of the purifier.
        pm10 (int): PM10 value of the purifier.
        aq_percent (int): Air quality percentage of the purifier.
        light_detection_switch (str): Light detection switch status of the purifier.
        light_detection_status (str): Light detection status of the purifier.
        nightlight_status (str): Nightlight status of the purifier.
        fan_rotate_angle (int): Fan rotate angle of the purifier.
        temperature (int): Temperature value of the purifier.
        humidity (int): Humidity value of the purifier.
        voc (int): VOC value of the purifier.
        co2 (int): CO2 value of the purifier.
        nightlight_brightness (int): Nightlight brightness level of the purifier.

    Note:
        Not all attributes are supported by all models.
    """

    __slots__ = (
        '_air_quality_level',
        'aq_percent',
        'auto_preference_type',
        'auto_room_size',
        'child_lock',
        'co2',
        'display_forever',
        'display_set_status',
        'display_status',
        'fan_level',
        'fan_rotate_angle',
        'fan_set_level',
        'filter_life',
        'filter_open_state',
        'humidity',
        'light_detection_status',
        'light_detection_switch',
        'mode',
        'nightlight_brightness',
        'nightlight_status',
        'pm1',
        'pm10',
        'pm25',
        'temperature',
        'voc',
    )

    def __init__(
        self,
        device: VeSyncPurifier,
        details: ResponseDeviceDetailsModel,
        feature_map: PurifierMap,
    ) -> None:
        """Initialize Purifier State."""
        super().__init__(device, details, feature_map)
        self.mode: str = PurifierModes.UNKNOWN
        self.fan_level: int | None = None
        self.fan_set_level: int | None = None
        self.filter_life: int | None = None
        self.auto_preference_type: str | None = None
        self.auto_room_size: int | None = None
        self._air_quality_level: AirQualityLevel | None = None
        self.child_lock: bool = False
        self.filter_open_state: bool = False
        self.display_status: str | None = None
        self.display_set_status: str | None = None
        self.display_forever: bool = False
        self.humidity: int | None = None
        self.temperature: int | None = None
        # Attributes not supported by all purifiers
        self.pm25: int | None = None
        self.pm1: int | None = None
        self.pm10: int | None = None
        self.aq_percent: int | None = None
        self.voc: int | None = None
        self.co2: int | None = None
        self.light_detection_switch: str | None = None
        self.light_detection_status: str | None = None
        self.nightlight_brightness: int | None = None
        self.nightlight_status: str | None = None
        self.fan_rotate_angle: int | None = None

    @property
    def air_quality_level(self) -> int:
        """Return air quality level in integer from 1-4.

        Returns -1 if unknown.
        """
        if self._air_quality_level is None:
            return -1
        return int(self._air_quality_level)

    @air_quality_level.setter
    def air_quality_level(self, value: int | None) -> None:
        """Set air quality level."""
        if isinstance(value, int):
            self._air_quality_level = AirQualityLevel.from_int(value)

    def set_air_quality_level(self, value: int | str | None) -> None:
        """Set air quality level."""
        if isinstance(value, str):
            self._air_quality_level = AirQualityLevel.from_string(value)
        elif isinstance(value, int):
            self._air_quality_level = AirQualityLevel.from_int(value)

    @property
    def air_quality_string(self) -> str:
        """Return air quality level as string."""
        return str(self._air_quality_level)

    @property
    @deprecated('Use state.air_quality_level instead.')
    def air_quality(self) -> int | str | None:
        """Return air quality level."""
        return self.air_quality_level

    @property
    @deprecated('Use light_detection_switch instead.')
    def light_detection(self) -> bool:
        """Return light detection status."""
        return self.light_detection_switch == DeviceStatus.ON

    @property
    @deprecated('Use state.pm25 instead.')
    def air_quality_value(self) -> int | None:
        """Return air quality value."""
        return self.pm25

    @property
    @deprecated('Use PurifierState.fan_level instead.')
    def speed(self) -> int | None:
        """Return fan speed."""
        return self.fan_level

    @property
    @deprecated('Use PurifierState.nightlight_status instead.')
    def night_light(self) -> str | None:
        """Return night light status."""
        return self.nightlight_status

    @property
    @deprecated('Use display_status instead.')
    def display_state(self) -> str | None:
        """Return display status."""
        return self.display_status

    @property
    @deprecated('Use display_set_status instead.')
    def display_switch(self) -> str | None:
        """Return display switch status."""
        return self.display_set_status


class VeSyncPurifier(VeSyncBaseToggleDevice):
    """Base device for vesync air purifiers.

    Args:
        details (ResponseDeviceDetailsModel): Device details from API.
        manager (VeSync): VeSync manager instance.
        feature_map (PurifierMap): Feature map for the device.

    Attributes:
        state (PurifierState): State of the device.
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
        modes (list[str]): List of modes supported by the device.
        fan_levels (list[int]): List of fan levels supported by the device.
        nightlight_modes (list[str]): List of nightlight modes supported by the device.
        auto_preferences (list[str]): List of auto preferences supported by the device.
    """

    __slots__ = ('auto_preferences', 'fan_levels', 'modes', 'nightlight_modes')

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: PurifierMap,
    ) -> None:
        """Initialize VeSync Purifier Base Class."""
        super().__init__(details, manager, feature_map)
        self.features: list[str] = feature_map.features
        self.state: PurifierState = PurifierState(self, details, feature_map)
        self.modes: list[str] = feature_map.modes
        self.fan_levels: list[int] = feature_map.fan_levels
        self.nightlight_modes: list[str] = feature_map.nightlight_modes
        self.auto_preferences: list[str] = feature_map.auto_preferences

    @property
    def supports_air_quality(self) -> bool:
        """Return True if device supports air quality."""
        return PurifierFeatures.AIR_QUALITY in self.features

    @property
    def supports_fan_rotate(self) -> bool:
        """Return True if device supports fan rotation."""
        return PurifierFeatures.VENT_ANGLE in self.features

    @property
    def supports_nightlight(self) -> bool:
        """Return True if device supports nightlight."""
        return PurifierFeatures.NIGHTLIGHT in self.features

    @property
    def supports_light_detection(self) -> bool:
        """Returns True if device supports light detection."""
        return PurifierFeatures.LIGHT_DETECT in self.features

    async def toggle_display(self, mode: bool) -> bool:
        """Set Display Mode."""
        del mode
        raise NotImplementedError

    async def turn_on_display(self) -> bool:
        """Turn on Display."""
        return await self.toggle_display(True)

    async def turn_off_display(self) -> bool:
        """Turn off Display."""
        return await self.toggle_display(False)

    async def set_nightlight_mode(self, mode: str) -> bool:
        """Set Nightlight Mode.

        Modes are defined in the `device.nightlight_modes` attribute.

        Args:
            mode (str): Nightlight mode to set.

        Returns:
            bool: True if successful, False otherwise.
        """
        del mode
        return False

    async def set_nightlight_dim(self) -> bool:
        """Set Nightlight Dim."""
        return await self.set_nightlight_mode(NightlightModes.DIM)

    async def turn_on_nightlight(self) -> bool:
        """Turn on Nightlight."""
        return await self.set_nightlight_mode(NightlightModes.ON)

    async def turn_off_nightlight(self) -> bool:
        """Turn off Nightlight."""
        return await self.set_nightlight_mode(NightlightModes.OFF)

    async def toggle_child_lock(self, toggle: bool | None = None) -> bool:
        """Toggle Child Lock (Display Lock).

        Args:
            toggle (bool | None): Toggle child lock. If None, toggle state.
        """
        del toggle
        logger.debug('Child lock not configured for this device.')
        return False

    async def turn_on_child_lock(self) -> bool:
        """Set child lock (display lock) to ON."""
        return await self.toggle_child_lock(True)

    async def turn_off_child_lock(self) -> bool:
        """Set child lock (display lock) to OFF."""
        return await self.toggle_child_lock(False)

    @abstractmethod
    async def set_mode(self, mode: str) -> bool:
        """Set Purifier Mode.

        Allowed modes are found in the `device.modes` attribute.

        Args:
            mode (str): Mode to set.

        Returns:
            bool: True if successful, False otherwise.
        """

    @abstractmethod
    async def set_fan_speed(self, speed: int | None = None) -> bool:
        """Set Purifier Fan Speed.

        Args:
            speed (int | None): Fan speed to set. If None, use default speed.

        Returns:
            bool: True if successful, False otherwise.
        """

    async def set_auto_mode(self) -> bool:
        """Set Purifier to Auto Mode."""
        if PurifierModes.AUTO in self.modes:
            return await self.set_mode(PurifierModes.AUTO)
        logger.error('Auto mode not supported for this device.')
        return False

    async def set_sleep_mode(self) -> bool:
        """Set Purifier to Sleep Mode."""
        if PurifierModes.SLEEP in self.modes:
            return await self.set_mode(PurifierModes.SLEEP)
        logger.error('Sleep mode not supported for this device.')
        return False

    async def set_manual_mode(self) -> bool:
        """Set Purifier to Manual Mode."""
        if PurifierModes.MANUAL in self.modes:
            return await self.set_mode(PurifierModes.MANUAL)
        logger.error('Manual mode not supported for this device.')
        return False

    async def set_turbo_mode(self) -> bool:
        """Set Purifier to Turbo Mode."""
        if PurifierModes.TURBO in self.modes:
            return await self.set_mode(PurifierModes.TURBO)
        logger.error('Turbo mode not supported for this device.')
        return False

    async def set_pet_mode(self) -> bool:
        """Set Purifier to Pet Mode."""
        if PurifierModes.PET in self.modes:
            return await self.set_mode(PurifierModes.PET)
        logger.error('Pet mode not supported for this device.')
        return False

    async def set_auto_preference(self, preference: str, room_size: int = 800) -> bool:
        """Set auto preference.

        Args:
            preference (str): Auto preference to set, available preference is
                found in `self.auto_preferences`.
            room_size (int): Room size to set, defaults to 800ft2.

        Returns:
            bool: True if successful, False otherwise.
        """
        del preference, room_size
        logger.debug('Auto preference not configured for this device.')
        return False

    async def toggle_light_detection(self, toggle: bool | None = None) -> bool:
        """Set Light Detection Mode.

        Args:
            toggle (bool | None): Toggle light detection. If None, toggle state.

        Returns:
            bool: True if successful, False otherwise.
        """
        del toggle
        if not self.supports_light_detection:
            logger.debug('Light detection not supported for this device.')
        else:
            logger.debug('Light detection not configured for this device.')
        return False

    async def turn_on_light_detection(self) -> bool:
        """Turn on Light Detection."""
        return await self.toggle_light_detection(True)

    async def turn_off_light_detection(self) -> bool:
        """Turn off Light Detection."""
        return await self.toggle_light_detection(False)

    async def reset_filter(self) -> bool:
        """Reset filter life."""
        logger.debug('Filter life reset not configured for this device.')
        return False

    @deprecated('Use set_auto_mode instead.')
    async def auto_mode(self) -> bool:
        """Set Purifier to Auto Mode."""
        return await self.set_auto_mode()

    @deprecated('Use set_sleep_mode instead.')
    async def sleep_mode(self) -> bool:
        """Set Purifier to Sleep Mode."""
        return await self.set_sleep_mode()

    @deprecated('Use set_manual_mode instead.')
    async def manual_mode(self) -> bool:
        """Set Purifier to Manual Mode."""
        return await self.set_manual_mode()

    @deprecated('Use set_turbo_mode instead.')
    async def turbo_mode(self) -> bool:
        """Set Purifier to Turbo Mode."""
        return await self.set_turbo_mode()

    @deprecated('Use set_pet_mode instead.')
    async def pet_mode(self) -> bool:
        """Set Purifier to Pet Mode."""
        return await self.set_pet_mode()

    @deprecated('Use set_nightlight_mode instead.')
    async def nightlight_mode(self, mode: str) -> bool:
        """Set Nightlight Mode."""
        return await self.set_nightlight_mode(mode)

    @deprecated('Use `set_fan_speed()` instead.')
    async def change_fan_speed(self, speed: int | None = None) -> bool:
        """Deprecated - Set fan speed."""
        return await self.set_fan_speed(speed)

    @deprecated('Use `set_mode(mode: str)` instead.')
    async def change_mode(self, mode: str) -> bool:
        """Deprecated - Set purifier mode."""
        return await self.set_mode(mode)

    @deprecated('Use `toggle_child_lock()` instead.')
    async def set_child_lock(self, toggle: bool) -> bool:
        """Set child lock (display lock).

        This has been deprecated in favor of `toggle_child_lock()`.
        """
        return await self.toggle_child_lock(toggle)

    @deprecated('Use `turn_on_child_lock()` instead.')
    async def child_lock_on(self) -> bool:
        """Turn on child lock (display lock).

        This has been deprecated, use `turn_on_child_lock()` instead.
        """
        return await self.toggle_child_lock(True)

    @deprecated('Use `turn_off_child_lock()` instead.')
    async def child_lock_off(self) -> bool:
        """Turn off child lock (display lock).

        This has been deprecated, use `turn_off_child_lock()` instead.
        """
        return await self.toggle_child_lock(False)

    @property
    @deprecated('Use self.state.child_lock instead.')
    def child_lock(self) -> bool:
        """Get child lock state.

        Returns:
            bool : True if child lock is enabled, False if not.
        """
        return self.state.child_lock

    @property
    @deprecated('Use self.state.nightlight_status instead.')
    def night_light(self) -> str | None:
        """Get night light state.

        Returns:
            str : Night light state (on, dim, off)
        """
        return self.state.nightlight_status

    @deprecated('Use turn_on_light_detection() instead.')
    async def set_light_detection_on(self) -> bool:
        """Turn on light detection feature."""
        return await self.toggle_light_detection(True)

    @deprecated('Use turn_off_light_detection() instead.')
    async def set_light_detection_off(self) -> bool:
        """Turn off light detection feature."""
        return await self.toggle_light_detection(False)
