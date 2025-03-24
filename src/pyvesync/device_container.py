"""Module to contain VeSync device instances.

`DeviceContainer` holds VeSync device instances in a singleton container
that inherits from a `MutableSet`. The `DeviceContainer` class is instantiated
in the `pyvesync.vesync.VeSync` class and is used to store and manage VeSync
device instances. Use the `add_new_devices(dev_list_response: ResponseDeviceListModel)`
method to add devices from the device list response model.
"""

from __future__ import annotations
import logging
from typing import TypeVar, TYPE_CHECKING
from collections.abc import Iterator, MutableSet, Sequence
from typing_extensions import Self
from pyvesync.models.vesync_models import ResponseDeviceListModel
from pyvesync.utils.errors import VeSyncAPIResponseError
from pyvesync.const import ProductTypes
from pyvesync.base_devices.outlet_base import VeSyncOutlet
from pyvesync.base_devices.switch_base import VeSyncSwitch
from pyvesync.base_devices.bulb_base import VeSyncBulb
from pyvesync.base_devices.purifier_base import VeSyncPurifier
from pyvesync.base_devices.fan_base import VeSyncFanBase
from pyvesync.base_devices.humidifier_base import VeSyncHumidifier
from pyvesync.models.vesync_models import (
    ResponseDeviceDetailsModel
    )
from pyvesync.device_map import get_device_config
from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseDevice

if TYPE_CHECKING:
    from pyvesync import VeSync


logger = logging.getLogger(__name__)

T = TypeVar('T')


class DeviceContainerBase(MutableSet[VeSyncBaseDevice]):
    """Base class for VeSync device containe.

    Inherits from `MutableSet` and is used to store VeSync device instances.
    This class enable singleton behavior and overrides all necessary abstract
    methods from `MutableSet`.
    """
    _instance: Self | None = None

    def __new__(cls: type[Self]) -> Self:
        """Make DeviceContainer a singleton."""
        if cls._instance is None:
            print('Creating the object')
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
            self, sequence: Sequence[VeSyncBaseDevice] | None = None,
            /,
            ) -> None:
        """Initialize the DeviceContainer class."""
        self._data: set[VeSyncBaseDevice] = set()
        if isinstance(sequence, Sequence):
            self._data.update(sequence)

    def __iter__(self) -> Iterator[VeSyncBaseDevice]:
        """Iterate over the container."""
        return iter(self._data)

    def __len__(self) -> int:
        """Return the length of the container."""
        return len(self._data)

    def add(self, value: VeSyncBaseDevice) -> None:
        """Add a device to the container."""
        if value in self._data:
            logger.debug("Device already exists")
            return
        self._data.add(value)

    def remove(self, value: VeSyncBaseDevice) -> None:
        """Remove a device from the container."""
        self._data.remove(value)

    def clear(self) -> None:
        """Clear the container."""
        self._data.clear()

    def __contains__(self, value: object) -> bool:
        """Check if a device is in the container."""
        return value in self._data


class DeviceContainer(DeviceContainerBase):
    """Container for VeSync device instances.

    The `DeviceContainer` class is a container for VeSync device instances that
    inherits behavior from `MutableSet`. The container contains all VeSync devices
    and is used to store and manage device instances. The container is a singleton
    and is instantiated in the `pyvesync.vesync.VeSync` class. This should not be
    manually instantiated.

    Use the `DeviceContainer.add_new_devices(device_list_model)` class method to
    add devices from the device list model API response and `remove_stale_devices`
    to remove stale devices from the device list API response model.
    The device list response model is built in the `pyvesync.vesync.VeSync.get_devices`
    method.

    Attributes:
        _instance ('DeviceContainer' | None): Singleton instance of the
            DeviceContainer class

    Notes:
        The :obj:`DeviceContainer.add(device: VeSyncBaseDevice)` method accepts a valid
        VeSync device instance and adds it to the container. To add devices from a model,
        use the classmethod :obj:`DeviceContainer.add_device_from_model()` to add a
        single device. The model must be :obj:`ResponseDeviceDetailsModel`.

        The :obj:`DeviceContainer.remove_by_cid(cid: str)` method accepts a device CID and
        removes the device from the container. The `cid_exists(cid: str)` method accepts a
        device CID and returns a boolean indicating if the device exists in the container.

        Example usage:
        ```python
        container = DeviceContainer()
        container.add_device_from_model(device)
        ```
    """
    def __init__(
            self, sequence: Sequence[VeSyncBaseDevice] | None = None,
            /,
            ) -> None:
        """Initialize the DeviceContainer class."""
        super().__init__(sequence)

    def _build_device_instance(self,
                               device: ResponseDeviceDetailsModel,
                               manager: VeSync) -> VeSyncBaseDevice | None:
        """Create a device from the device list response model.

        Args:
            device (ResponseDeviceDetailsModel): The device details model from the
                device list response model. This is a single device model from the device
                list response.
            manager (VeSync): The VeSync instance to pass to the device instance

        Returns:
            VeSyncBaseDevice: The device instance created from the device list
                response model.

        Raises:
            VeSyncAPIResponseError: If the model is not an instance of
                `ResponseDeviceDetailsModel`.
        """
        if not isinstance(device, ResponseDeviceDetailsModel):
            raise VeSyncAPIResponseError(
                f"Expected ResponseDeviceDetailsModel, got {type(device)}"
            )
        device_features = get_device_config(device.deviceType)
        if device_features is None:
            logger.debug("Device type %s not found in device map", device.deviceType)
            return None
        dev_class = device_features.class_name
        dev_module = device_features.module
        device.productType = device_features.product_type
        # Import via string to avoid circular imports
        cls = getattr(dev_module, dev_class)
        return cls(device, manager, device_features)

    def add_device_from_model(
        self, device: ResponseDeviceDetailsModel, manager: VeSync
    ) -> None:
        """Add a single device from the device list response model.

        Args:
            device (ResponseDeviceDetailsModel): The device details model from the
                device list response model. This is a single device model from the device
                list response.
            manager (VeSync): The VeSync instance to pass to the device instance

        Raises:
            VeSyncAPIResponseError: If the model is not an instance of
                `ResponseDeviceDetailsModel`.
        """
        device_obj = self._build_device_instance(device, manager)
        if device_obj is not None:
            self.add(device_obj)

    def device_exists(self, cid: str, sub_device_no: int) -> bool:
        """Check if a device with the given cid & sub_dev_no exists."""
        new_hash = hash(cid + str(sub_device_no))
        return any(new_hash == hash(dev) for dev in self._data)

    def get_by_name(self, name: str) -> VeSyncBaseDevice | None:
        """Forgiving method to get a device by cid."""
        for device in self._data:
            if device.device_name.lower() == name.lower():
                return device
        return None

    def remove_by_cid(self, cid: str) -> None:
        """Remove a device by cid."""
        for device in self._data:
            if device.cid == cid:
                self.remove(device)
                return

    def discard(self, value: VeSyncBaseDevice) -> None:
        """Discard a device from the container."""
        return self._data.discard(value)

    def remove_stale_devices(
        self, device_list_result: ResponseDeviceListModel
    ) -> None:
        """Remove devices that are not in the provided list.

        Args:
            device_list_result (ResponseDeviceListModel): The device list response model
                from the VeSync API. This is generated by the `VeSync.get_devices()`
                method.
        """
        device_list = device_list_result.result.list
        new_hashes = [hash(device.cid+str(device.subDeviceNo)) for device in device_list]
        for device in self._data:
            if hash(device) not in new_hashes:
                logger.debug("Removing stale device %s", device.device_name)
                self.remove(device)

    def add_new_devices(
        self, device_list_result: ResponseDeviceListModel, manager: VeSync
    ) -> None:
        """Add new devices to the container.

        Args:
            device_list_result (ResponseDeviceListModel): The device list response model
                from the VeSync API. This is generated by the `VeSync.get_devices()`
                method.
            manager (VeSync): The VeSync instance to pass to the device instance
        """
        device_list = device_list_result.result.list
        for device in device_list:
            if self.device_exists(device.cid, device.subDeviceNo) not in self._data:
                self.add_device_from_model(device, manager)

    @property
    def outlets(self) -> list[VeSyncOutlet]:
        """Return a list of devices that are outlets."""
        return [device for device in self if isinstance(device, VeSyncOutlet)
                and device.product_type == ProductTypes.OUTLET]

    @property
    def switches(self) -> list[VeSyncSwitch]:
        """Return a list of devices that are switches."""
        return [device for device in self
                if (isinstance(
                    device, VeSyncSwitch) and device.product_type == ProductTypes.SWITCH)]

    @property
    def bulbs(self) -> list[VeSyncBulb]:
        """Return a list of devices that are lights."""
        return [device for device in self if isinstance(device, VeSyncBulb)
                and (device.product_type == ProductTypes.BULB)]

    @property
    def air_purifiers(self) -> list[VeSyncPurifier]:
        """Return a list of devices that are air purifiers."""
        return [
            device
            for device in self
            if isinstance(device, VeSyncPurifier)
            and device.product_type == ProductTypes.PURIFIER
        ]

    @property
    def fans(self) -> list[VeSyncFanBase]:
        """Return a list of devices that are fans."""
        return [
            device
            for device in self
            if isinstance(device, VeSyncFanBase)
            and device.product_type == ProductTypes.FAN
        ]

    @property
    def humidifiers(self) -> list[VeSyncHumidifier]:
        """Return a list of devices that are humidifiers."""
        return [
            device
            for device in self
            if isinstance(device, VeSyncHumidifier)
            and device.product_type == ProductTypes.HUMIDIFIER
        ]

    @property
    def air_fryers(self) -> list[VeSyncBaseDevice]:
        """Return a list of devices that are air fryers."""
        return [device for device in self
                if device.product_type == ProductTypes.AIR_FRYER]
