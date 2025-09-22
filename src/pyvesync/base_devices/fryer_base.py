"""Air Purifier Base Class."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyvesync.base_devices.vesyncbasedevice import DeviceState, VeSyncBaseDevice

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import AirFryerMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel


logger = logging.getLogger(__name__)


class FryerState(DeviceState):
    """State class for Air Fryer devices.

    Note: This class is a placeholder for future functionality and does not currently
    implement any specific features or attributes.
    """

    __slots__ = ()

    def __init__(
        self,
        device: VeSyncFryer,
        details: ResponseDeviceDetailsModel,
        feature_map: AirFryerMap,
    ) -> None:
        """Initialize FryerState.

        Args:
            device (VeSyncFryer): The device object.
            details (ResponseDeviceDetailsModel): The device details.
            feature_map (AirFryerMap): The feature map for the device.

        """
        super().__init__(device, details, feature_map)
        self.device: VeSyncFryer = device
        self.features: list[str] = feature_map.features


class VeSyncFryer(VeSyncBaseDevice):
    """Base class for VeSync Air Fryer devices."""

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: AirFryerMap,
    ) -> None:
        """Initialize VeSyncFryer.

        Args:
            details (ResponseDeviceDetailsModel): The device details.
            manager (VeSync): The VeSync manager.
            feature_map (AirFryerMap): The feature map for the device.

        Note:
            This is a bare class as there is only one supported air fryer model.
        """
        super().__init__(details, manager, feature_map)
