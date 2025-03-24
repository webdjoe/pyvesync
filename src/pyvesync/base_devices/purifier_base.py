"""Air Purifier Base Class."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from abc import abstractmethod

from deprecated import deprecated

from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseToggleDevice, DeviceState
from pyvesync.const import (
    AirQualityLevel,
    PurifierFeatures,
    PurifierModes,
    DeviceStatus,
    NightlightModes,
    PurifierAutoPreference,
    IntFlag,
    StrFlag,
    )

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
    from pyvesync.device_map import PurifierMap
    from pyvesync.utils.helpers import Timer


logger = logging.getLogger(__name__)


class PurifierState(DeviceState):
    """Base state class for Purifiers."""

    __slots__ = (
        "_air_quality_level",
        "aq_percent",
        "auto_preference_type",
        "auto_room_size",
        "child_lock",
        "display_forever",
        "display_set_state",
        "display_status",
        "fan_level",
        "fan_rotate_angle",
        "fan_set_level",
        "filter_life",
        "filter_open_state",
        "light_detection_status",
        "light_detection_switch",
        "mode",
        "nightlight_status",
        "pm1",
        "pm10",
        "pm25",
        "timer",
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
        self.auto_preference_type: str | None = PurifierAutoPreference.UNKNOWN
        self.auto_room_size: int | None = None
        self._air_quality_level: AirQualityLevel = AirQualityLevel.UNKNOWN
        self.child_lock: bool = False
        self.filter_open_state: bool = False
        self.display_status: str = DeviceStatus.UNKNOWN
        self.display_set_state: str = DeviceStatus.UNKNOWN
        self.display_forever: bool = False
        self.timer: Timer | None = None
        # Attributes not supported by all purifiers
        # When update is first called, devices that support these attributes will
        # update them from NOT_SUPPORTED, whether to None or another value.
        self.pm25: int | None = IntFlag.NOT_SUPPORTED
        self.pm1: int | None = IntFlag.NOT_SUPPORTED
        self.pm10: int | None = IntFlag.NOT_SUPPORTED
        self.aq_percent: int | None = IntFlag.NOT_SUPPORTED
        self.light_detection_switch: str = StrFlag.NOT_SUPPORTED
        self.light_detection_status: str = StrFlag.NOT_SUPPORTED
        self.nightlight_status: str = StrFlag.NOT_SUPPORTED
        self.fan_rotate_angle: int | None = IntFlag.NOT_SUPPORTED

    @property
    def air_quality_level(self) -> int:
        """Return air quality level in integer from 1-4.

        Returns -1 if unknown.
        """
        return self._air_quality_level.value

    @air_quality_level.setter
    def air_quality_level(self, value: int | None) -> None:
        """Set air quality level."""
        if isinstance(value, str):
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
    @deprecated("Use state.air_quality_level instead.")
    def air_quality(self) -> int | str | None:
        """Return air quality level."""
        return self.air_quality_level

    @property
    @deprecated("Use light_detection_switch instead.")
    def light_detection(self) -> bool:
        """Return light detection status."""
        return self.light_detection_switch == DeviceStatus.ON

    @property
    @deprecated("Use state.pm25 instead.")
    def air_quality_value(self) -> int | None:
        """Return air quality value."""
        return self.pm25

    @property
    @deprecated("Use PurifierState.fan_level instead.")
    def speed(self) -> int | None:
        """Return fan speed."""
        return self.fan_level

    @property
    @deprecated("Use PurifierState.nightlight_status instead.")
    def night_light(self) -> str:
        """Return night light status."""
        return self.nightlight_status

    @property
    @deprecated("Use display_status instead.")
    def display_state(self) -> str:
        """Return display status."""
        return self.display_status

    @property
    @deprecated("Use display_set_state instead.")
    def display_switch(self) -> str:
        """Return display switch status."""
        return self.display_set_state


class VeSyncPurifier(VeSyncBaseToggleDevice):
    """Base device for vesync air purifiers."""

    __slots__ = (
        "auto_preferences",
        "fan_levels",
        "modes",
        "nightlight_modes"
    )

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
        self.nightlight_modes = feature_map.nightlight_modes
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
        """Set Nightlight Mode."""
        del mode
        raise NotImplementedError

    async def set_nightlight_dim(self) -> bool:
        """Set Nightlight Dim."""
        return await self.set_nightlight_mode(NightlightModes.DIM)

    async def turn_on_nightlight(self) -> bool:
        """Turn on Nightlight."""
        return await self.set_nightlight_mode(NightlightModes.ON)

    async def turn_off_nightlight(self) -> bool:
        """Turn off Nightlight."""
        return await self.set_nightlight_mode(NightlightModes.OFF)

    @abstractmethod
    async def set_mode(self, mode: str) -> bool:
        """Set Purifier Mode."""

    @abstractmethod
    async def set_fan_speed(self, speed: int | None = None) -> bool:
        """Set Purifier Fan Speed."""

    async def set_auto_mode(self) -> bool:
        """Set Purifier to Auto Mode."""
        if PurifierModes.AUTO in self.modes:
            return await self.set_mode(PurifierModes.AUTO)
        logger.error("Auto mode not supported for this device.")
        return False

    async def set_sleep_mode(self) -> bool:
        """Set Purifier to Sleep Mode."""
        if PurifierModes.SLEEP in self.modes:
            return await self.set_mode(PurifierModes.SLEEP)
        logger.error("Sleep mode not supported for this device.")
        return False

    async def set_manual_mode(self) -> bool:
        """Set Purifier to Manual Mode."""
        if PurifierModes.MANUAL in self.modes:
            return await self.set_mode(PurifierModes.MANUAL)
        logger.error("Manual mode not supported for this device.")
        return False

    async def set_turbo_mode(self) -> bool:
        """Set Purifier to Turbo Mode."""
        if PurifierModes.TURBO in self.modes:
            return await self.set_mode(PurifierModes.TURBO)
        logger.error("Turbo mode not supported for this device.")
        return False

    async def set_pet_mode(self) -> bool:
        """Set Purifier to Pet Mode."""
        if PurifierModes.PET in self.modes:
            return await self.set_mode(PurifierModes.PET)
        logger.error("Pet mode not supported for this device.")
        return False

    @deprecated("Use set_auto_mode instead.")
    async def auto_mode(self) -> bool:
        """Set Purifier to Auto Mode."""
        return await self.set_auto_mode()

    @deprecated("Use set_sleep_mode instead.")
    async def sleep_mode(self) -> bool:
        """Set Purifier to Sleep Mode."""
        return await self.set_sleep_mode()

    @deprecated("Use set_manual_mode instead.")
    async def manual_mode(self) -> bool:
        """Set Purifier to Manual Mode."""
        return await self.set_manual_mode()

    @deprecated("Use set_turbo_mode instead.")
    async def turbo_mode(self) -> bool:
        """Set Purifier to Turbo Mode."""
        return await self.set_turbo_mode()

    @deprecated("Use set_pet_mode instead.")
    async def pet_mode(self) -> bool:
        """Set Purifier to Pet Mode."""
        return await self.set_pet_mode()

    @deprecated("Use set_nightlight_mode instead.")
    async def nightlight_mode(self, mode: str) -> bool:
        """Set Nightlight Mode."""
        return await self.set_nightlight_mode(mode)

    @deprecated("Use `set_fan_speed()` instead.")
    async def change_fan_speed(self, speed: int | None = None) -> bool:
        """Deprecated method for changing fan speed."""
        return await self.set_fan_speed(speed)

    @deprecated("Use `set_mode(mode: str)` instead.")
    async def change_mode(self, mode: str) -> bool:
        """Deprecated method for changing purifier mode."""
        return await self.set_mode(mode)
