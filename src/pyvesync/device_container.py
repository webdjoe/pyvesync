"""Module to contain VeSync device instances.

Attributes:
    DeviceContainerInstance (DeviceContainer): Singleton instance of the DeviceContainer
        class. This is imported by the `vesync` module.

Classes:
    DeviceContainer: Container for VeSync device instances.
        This class should not be instantiated directly. Use the `DeviceContainerInstance`
        instead.
    _DeviceContainerBase: Base class for VeSync device
        container. Inherits from `MutableSet`.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator, MutableSet, Sequence
from typing import TYPE_CHECKING, TypeVar

from pyvesync.base_devices.bulb_base import VeSyncBulb
from pyvesync.base_devices.fan_base import VeSyncFanBase
from pyvesync.base_devices.fryer_base import VeSyncFryer
from pyvesync.base_devices.humidifier_base import VeSyncHumidifier
from pyvesync.base_devices.outlet_base import VeSyncOutlet
from pyvesync.base_devices.purifier_base import VeSyncPurifier
from pyvesync.base_devices.switch_base import VeSyncSwitch
from pyvesync.base_devices.thermostat_base import VeSyncThermostat
from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseDevice
from pyvesync.const import ProductTypes
from pyvesync.device_map import get_device_config

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.models.vesync_models import (
        ResponseDeviceDetailsModel,
        ResponseDeviceListModel,
    )


logger = logging.getLogger(__name__)

T = TypeVar('T')


def _clean_string(string: str) -> str:
    """Clean a string by removing non alphanumeric characters and making lowercase."""
    return re.sub(r'[^a0zA-Z0-9]', '', string)


class _DeviceContainerBase(MutableSet[VeSyncBaseDevice]):
    """Base class for VeSync device container.

    Inherits from `MutableSet` and defines the core MutableSet methods.
    """

    __slots__ = ('__weakref__', '_data')

    def __init__(
        self,
        sequence: Sequence[VeSyncBaseDevice] | None = None,
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
            logger.debug('Device already exists')
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


class DeviceContainer(_DeviceContainerBase):
    """Container for VeSync device instances.

    /// admonition | Warning
    type: warning

    This class should not be instantiated directly. Use the `DeviceContainerInstance`
    instead.
    ///

    The `DeviceContainer` class is a container for VeSync device instances that
    inherits behavior from `MutableSet`. The container contains all VeSync devices
    and is used to store and manage device instances. The container is a singleton
    and is instantiated directly by the `DeviceContainerInstance` in the
    `device_container` module and imported as needed.

    Use the [`add_new_devices`][pyvesync.device_container.DeviceContainer.add_new_devices]
    class method to add devices from the device list model API response and
    `remove_stale_devices` to remove stale devices from the device list API response
    model. The device list response model is built in the
    [VeSync.get_devices()][pyvesync.vesync.VeSync.get_devices] method.

    Args:
        sequence (Sequence[VeSyncBaseDevice] | None): A sequence of device instances to
            initialize the container with. Typically this is not used directly,
            defaults to None.

    Attributes:
        _data (set[VeSyncBaseDevice]): The mutable set of devices in the container.
    """

    __slots__ = ()

    def __init__(
        self,
        sequence: Sequence[VeSyncBaseDevice] | None = None,
        /,
    ) -> None:
        """Initialize the DeviceContainer class."""
        super().__init__(sequence)

    def _build_device_instance(
        self, device: ResponseDeviceDetailsModel, manager: VeSync
    ) -> VeSyncBaseDevice | None:
        """Create a device from a single device model from the device list.

        Args:
            device (ResponseDeviceDetailsModel): The device details model from the
                device list response model.
            manager (VeSync): The VeSync instance to pass to the device instance

        Returns:
            VeSyncBaseDevice: The device instance created from the device list
                response model.

        Raises:
            VeSyncAPIResponseError: If the model is not an instance of
                `ResponseDeviceDetailsModel`.
        """
        device_features = get_device_config(device.deviceType)
        if device_features is None:
            logger.debug('Device type %s not found in device map', device.deviceType)
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
                device list response model.
            manager (VeSync): The VeSync instance to pass to the device instance

        Raises:
            VeSyncAPIResponseError: If the model is not an instance of
                `ResponseDeviceDetailsModel`.
        """
        device_obj = self._build_device_instance(device, manager)
        if device_obj is not None:
            self.add(device_obj)

    def device_exists(self, cid: str, sub_device_no: int | None = None) -> bool:
        """Check if a device with the given cid & sub_dev_no exists.

        Args:
            cid (str): The cid of the device to check.
            sub_device_no (int): The sub_device_no of the device to check, defaults to 0
                for most devices.

        Returns:
            bool: True if the device exists, False otherwise.
        """
        new_hash = hash(cid + str(sub_device_no))
        return any(new_hash == hash(dev) for dev in self._data)

    def get_by_name(self, name: str, fuzzy: bool = False) -> VeSyncBaseDevice | None:
        """Forgiving method to get a device by name.

        Args:
            name (str): The name of the device to get.
            fuzzy (bool): Use a fuzzy match to find the device. Defaults to False.

        Returns:
            VeSyncBaseDevice | None: The device instance if found, None otherwise.

        Note:
            Fuzzy matching removes all non-alphanumeric characters and makes the string
            lowercase. If there are multiple devices with the same name, the first one
            found will be returned (a set is unordered).
        """
        for device in self._data:
            if (fuzzy and _clean_string(device.device_name) == _clean_string(name)) or (
                device.device_name == name
            ):
                return device
        return None

    def remove_by_cid(self, cid: str) -> bool:
        """Remove a device by cid.

        Args:
            cid (str): The cid of the device to remove.

        Returns:
            bool : True if the device was removed, False otherwise.
        """
        device_found: VeSyncBaseDevice | None = None
        for device in self._data:
            if device.cid == cid:
                device_found = device
                break
        if device_found is not None:
            self.remove(device_found)
            return True
        return False

    def discard(self, value: VeSyncBaseDevice) -> None:
        """Discard a device from the container.

        Args:
            value (VeSyncBaseDevice): The device to discard.
        """
        return self._data.discard(value)

    def remove_stale_devices(self, device_list_result: ResponseDeviceListModel) -> None:
        """Remove devices that are not in the provided list.

        Args:
            device_list_result (ResponseDeviceListModel): The device list response model
                from the VeSync API. This is generated by the `VeSync.get_devices()`
                method.
        """
        device_list = device_list_result.result.list
        new_hashes = [
            hash(device.cid + str(device.subDeviceNo)) for device in device_list
        ]
        remove_cids = []
        for device in self._data:
            if hash(device) not in new_hashes:
                logger.debug('Removing stale device %s', device.device_name)
                remove_cids.append(device.cid)
        for cid in remove_cids:
            self.remove_by_cid(cid)

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
        return [
            device
            for device in self
            if isinstance(device, VeSyncOutlet)
            and device.product_type == ProductTypes.OUTLET
        ]

    @property
    def switches(self) -> list[VeSyncSwitch]:
        """Return a list of devices that are switches."""
        return [
            device
            for device in self
            if (
                isinstance(device, VeSyncSwitch)
                and device.product_type == ProductTypes.SWITCH
            )
        ]

    @property
    def bulbs(self) -> list[VeSyncBulb]:
        """Return a list of devices that are lights."""
        return [
            device
            for device in self
            if isinstance(device, VeSyncBulb)
            and (device.product_type == ProductTypes.BULB)
        ]

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
    def air_fryers(self) -> list[VeSyncFryer]:
        """Return a list of devices that are air fryers."""
        return [
            device
            for device in self
            if isinstance(device, VeSyncFryer)
            and device.product_type == ProductTypes.AIR_FRYER
        ]

    @property
    def thermostats(self) -> list[VeSyncThermostat]:
        """Return a list of devices that are thermostats."""
        return [
            device
            for device in self
            if isinstance(device, VeSyncThermostat)
            and device.product_type == ProductTypes.THERMOSTAT
        ]


DeviceContainerInstance = DeviceContainer()
"""Singleton instance of the DeviceContainer class.

This attribute should be imported by the `vesync` module and
not the `DeviceContainer` class directly.
"""
