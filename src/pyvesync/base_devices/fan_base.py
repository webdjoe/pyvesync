"""Fan Devices Base Class (NOT purifiers or humidifiers)."""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING

from typing_extensions import deprecated

from pyvesync.base_devices.vesyncbasedevice import DeviceState, VeSyncBaseToggleDevice
from pyvesync.const import FanFeatures, FanModes

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import FanMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel


logger = logging.getLogger(__name__)


class FanState(DeviceState):
    """Base state class for Purifiers.

    Not all attributes are supported by all devices.


    Attributes:
        display_set_status (str): Display set status.
        display_status (str): Display status.
        displaying_type (str): Displaying type.
        fan_level (int): Fan level.
        fan_set_level (int): Fan set level.
        humidity (int): Humidity level.
        mode (str): Mode of device.
        mute_set_status (str): Mute set status.
        mute_status (str): Mute status.
        oscillation_set_status (str): Oscillation set status.
        oscillation_status (str): Oscillation status.
        sleep_change_fan_level (str): Sleep change fan level.
        sleep_fallasleep_remain (str): Sleep fall asleep remain.
        sleep_oscillation_switch (str): Sleep oscillation switch.
        sleep_preference_type (str): Sleep preference type.
        temperature (int): Temperature.
        thermal_comfort (int): Thermal comfort.
        timer (Timer): Timer object.
    """

    __slots__ = (
        'display_set_status',
        'display_status',
        'displaying_type',
        'fan_level',
        'fan_set_level',
        'humidity',
        'mode',
        'mute_set_status',
        'mute_status',
        'oscillation_set_status',
        'oscillation_status',
        'sleep_change_fan_level',
        'sleep_fallasleep_remain',
        'sleep_oscillation_switch',
        'sleep_preference_type',
        'temperature',
        'thermal_comfort',
    )

    def __init__(
        self,
        device: VeSyncFanBase,
        details: ResponseDeviceDetailsModel,
        feature_map: FanMap,
    ) -> None:
        """Initialize Purifier State.

        Args:
            device (VeSyncFanBase): Device object.
            details (ResponseDeviceDetailsModel): Device details.
            feature_map (FanMap): Feature map.
        """
        super().__init__(device, details, feature_map)
        self.mode: str = FanModes.UNKNOWN
        self.fan_level: int | None = None
        self.fan_set_level: int | None = None
        self.humidity: int | None = None
        self.temperature: int | None = None
        self.thermal_comfort: int | None = None
        self.sleep_preference_type: str | None = None
        self.sleep_fallasleep_remain: str | None = None
        self.sleep_oscillation_switch: str | None = None
        self.sleep_change_fan_level: str | None = None
        self.mute_status: str | None = None
        self.mute_set_status: str | None = None
        self.oscillation_status: str | None = None
        self.oscillation_set_status: str | None = None
        self.display_status: str | None = None
        self.display_set_status: str | None = None
        self.displaying_type: str | None = None


class VeSyncFanBase(VeSyncBaseToggleDevice):
    """Base device for VeSync tower fans.

    Inherits from
    [VeSyncBaseToggleDevice][pyvesync.base_devices.vesyncbasedevice.VeSyncBaseToggleDevice]
    and [VeSyncBaseDevice][pyvesync.base_devices.vesyncbasedevice.VeSyncBaseDevice].

    Attributes:
        fan_levels (list[int]): Fan levels supported by device.
        modes (list[str]): Modes supported by device.
        sleep_preferences (list[str]): Sleep preferences supported by device.
    """

    __slots__ = (
        'fan_levels',
        'modes',
        'sleep_preferences',
    )

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: FanMap,
    ) -> None:
        """Initialize VeSync Tower Fan Base Class.

        Args:
            details (ResponseDeviceDetailsModel): Device details.
            manager (VeSync): Manager.
            feature_map (FanMap): Feature map.

        See Also:
            See [device_map][pyvesync.device_map] for configured features and modes.
        """
        super().__init__(details, manager, feature_map)
        self.features: list[str] = feature_map.features
        self.state: FanState = FanState(self, details, feature_map)
        self.modes: list[str] = feature_map.modes
        self.fan_levels: list[int] = feature_map.fan_levels
        self.sleep_preferences: list[str] = feature_map.sleep_preferences

    @property
    def supports_oscillation(self) -> bool:
        """Return True if device supports oscillation."""
        return FanFeatures.OSCILLATION in self.features

    @property
    def supports_mute(self) -> bool:
        """Return True if device supports mute."""
        return FanFeatures.SOUND in self.features

    @property
    def supports_displaying_type(self) -> bool:
        """Return True if device supports displaying type."""
        return FanFeatures.DISPLAYING_TYPE in self.features

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

        Args:
            mode (str): Mode to set, varies by device type.

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
        logger.warning('Auto mode not supported for this device.')
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
        logger.warning('Advanced Sleep mode not supported for this device.')
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
        logger.warning('Sleep mode not supported for this device.')
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
        logger.warning('Manual mode not supported for this device.')
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
        logger.warning('Normal mode not supported for this device.')
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
        logger.warning('Turbo mode not supported for this device.')
        return False

    async def toggle_oscillation(self, toggle: bool) -> bool:
        """Toggle Oscillation on/off.

        Args:
            toggle (bool): Oscillation state.

        Returns:
            bool: true if success.
        """
        del toggle
        if self.supports_oscillation:
            logger.debug('Oscillation not configured for this device.')
        else:
            logger.debug('Oscillation not supported for this device.')
        return False

    async def turn_on_oscillation(self) -> bool:
        """Set toggle_oscillation to on."""
        return await self.toggle_oscillation(True)

    async def turn_off_oscillation(self) -> bool:
        """Set toggle_oscillation to off."""
        return await self.toggle_oscillation(False)

    async def toggle_mute(self, toggle: bool) -> bool:
        """Toggle mute on/off.

        Parameters:
            toggle : bool
                True to turn mute on, False to turn off

        Returns:
            bool : True if successful, False if not
        """
        del toggle
        if self.supports_mute:
            logger.debug('Mute not configured for this device.')
        else:
            logger.debug('Mute not supported for this device.')
        return False

    async def turn_on_mute(self) -> bool:
        """Set toggle_mute to on."""
        return await self.toggle_mute(True)

    async def turn_off_mute(self) -> bool:
        """Set toggle_mute to off."""
        return await self.toggle_mute(False)

    async def toggle_displaying_type(self, toggle: bool) -> bool:
        """Toggle displaying type on/off.

        This functionality is unknown but was in the API calls.

        Args:
            toggle (bool): Displaying type state.

        Returns:
            bool: true if success.
        """
        del toggle
        if self.supports_displaying_type:
            logger.debug('Displaying type not configured for this device.')
        else:
            logger.debug('Displaying type not supported for this device.')
        return False

    @deprecated('Use `set_normal_mode` method instead')
    async def normal_mode(self) -> bool:
        """Set mode to normal."""
        return await self.set_normal_mode()

    @deprecated('Use `set_manual_mode` method instead')
    async def manual_mode(self) -> bool:
        """Adapter to set mode to normal."""
        return await self.set_normal_mode()

    @deprecated('Use `set_advanced_sleep_mode` method instead')
    async def advanced_sleep_mode(self) -> bool:
        """Set advanced sleep mode."""
        return await self.set_mode('advancedSleep')

    @deprecated('Use `set_sleep_mode` method instead')
    async def sleep_mode(self) -> bool:
        """Adapter to set advanced sleep mode."""
        return await self.set_advanced_sleep_mode()

    @deprecated('Use `set_mode` method instead')
    async def mode_toggle(self, mode: str) -> bool:
        """Set mode to specified mode."""
        return await self.set_mode(mode)
