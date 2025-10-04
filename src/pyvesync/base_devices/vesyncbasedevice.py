"""Base class for all VeSync devices."""

from __future__ import annotations

import inspect
import logging
from abc import ABC, abstractmethod
from datetime import UTC
from datetime import datetime as dt
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import orjson

from pyvesync.const import ConnectionStatus, DeviceStatus

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import DeviceMapTemplate
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
    from pyvesync.utils.errors import ResponseInfo
    from pyvesync.utils.helpers import Timer


VS_TYPE = TypeVar('VS_TYPE', bound='VeSyncBaseDevice')
VS_STATE_T = TypeVar('VS_STATE_T', bound='DeviceState')


class VeSyncBaseDevice(ABC, Generic[VS_STATE_T]):
    """Properties shared across all VeSync devices.

    Abstract Base Class for all VeSync devices. The device class is used solely
    for operational methods and static device properties.

    Parameters:
        details (ResponseDeviceDetailsModel): Device details from API call.
        manager (VeSync): Manager object for API calls.
        feature_map (DeviceMapTemplate): Device configuration map, will be specific
            subclass of DeviceMapTemplate based on device type.

    Attributes:
        state (pyvesync.base_devices.vesyncbasedevice.DeviceState): Device state object
            Each device has a separate state base class in the base_devices module.
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
        latest_firm_version (str | None): Latest firmware version of device.
        device_region (str): Region of device. (US, EU, etc.)
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.

    Methods:
        set_timer: Set timer for device.
        get_timer: Get timer for device from API.
        clear_timer: Clear timer for device from API.
        set_state: Set device state attribute.
        get_state: Get device state attribute.
        update: Update device details.
        display: Print formatted static device info to stdout.
        to_json: Print JSON API string
        to_jsonb: JSON API bytes device details
        to_dict: Return device information as a dictionary.

    Note:
        Device states are found in the `state` attribute in a subclass of DeviceState
        based on the device type. The `DeviceState` subclass is located in device the
        base_devices module.

        The `last_response` attribute is used to store the last response and error
        information from the API call. See the `pyvesync.errors` module for more
        information.
    """

    __slots__ = (
        '__base_exclusions',
        '__weakref__',
        '_exclude_serialization',
        'cid',
        'config_module',
        'connection_type',
        'current_firm_version',
        'device_image',
        'device_name',
        'device_region',
        'device_type',
        'enabled',
        'features',
        'last_response',
        'latest_firm_version',
        'mac_id',
        'manager',
        'pid',
        'product_type',
        'request_keys',
        'state',
        'sub_device_no',
        'type',
        'uuid',
    )

    state: VS_STATE_T

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: DeviceMapTemplate,
    ) -> None:
        """Initialize VeSync device base class."""
        self._exclude_serialization: list[str] = []
        self.enabled: bool = True
        self.last_response: ResponseInfo | None = None
        self.manager = manager
        self.device_name: str = details.deviceName
        self.device_image: str | None = details.deviceImg
        self.cid: str = details.cid
        self.connection_type: str | None = details.connectionType
        self.device_type: str = details.deviceType
        self.type: str | None = details.type
        self.uuid: str | None = details.uuid
        self.config_module: str = details.configModule
        self.mac_id: str | None = details.macID
        self.current_firm_version = details.currentFirmVersion
        self.latest_firm_version: str | None = None
        self.device_region: str | None = details.deviceRegion
        self.pid: str | None = None
        self.sub_device_no: int | None = details.subDeviceNo
        # From feature_map
        self.product_type: str = feature_map.product_type
        self.features: list[str] = feature_map.features

    def __eq__(self, other: object) -> bool:
        """Use device CID and sub-device number to test equality."""
        if not isinstance(other, VeSyncBaseDevice):
            return NotImplemented
        return bool(other.cid == self.cid and other.sub_device_no == self.sub_device_no)

    def __hash__(self) -> int:
        """Use CID and sub-device number to make device hash."""
        return hash(self.cid + str(self.sub_device_no))

    def __str__(self) -> str:
        """Use device info for string representation of class."""
        return (
            f'Device Name: {self.device_name}, '
            f'Device Type: {self.device_type}, '
            f'SubDevice No.: {self.sub_device_no}'
        )

    def __repr__(self) -> str:
        """Representation of device details."""
        return (
            f'DevClass: {self.__class__.__name__}, '
            f'Product Type: {self.product_type}, '
            f'Name:{self.device_name}, '
            f'Device No: {self.sub_device_no}, '
            f'CID: {self.cid}'
        )

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self.state.device_status in [DeviceStatus.ON, DeviceStatus.RUNNING]

    @property
    def firmware_update(self) -> bool:
        """Return True if firmware update available.

        This is going to be updated.
        """
        return self.latest_firm_version != self.current_firm_version

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        """Set timer for device.

        This may not be implemented for all devices. Please open an issue
        if there is an error.

        Args:
            duration (int): Duration in seconds.
            action (str | None): Action to take when timer expires.

        Returns:
            bool: True if successful, False otherwise.
        """
        del duration
        del action
        logger.debug('Not implemented - set_timer')
        return False

    async def get_timer(self) -> Timer | None:
        """Get timer for device from API and set the `state.Timer` attribute.

        This may not be implemented for all devices. Please open an issue
        if there is an error.

        Note:
            This method may not be implemented for all devices. Please
            open an issue if there is an error.
        """
        logger.debug('Not implemented - get_timer')
        return None

    async def clear_timer(self) -> bool:
        """Clear timer for device from API.

        This may not be implemented for all devices. Please open an issue
        if there is an error.

        Returns:
            bool: True if successful, False otherwise.
        """
        logger.debug('Not implemented - clear_timer')
        return False

    def set_state(self, state_attr: str, stat_value: Any) -> None:  # noqa: ANN401
        """Set device state attribute."""
        setattr(self, state_attr, stat_value)

    def get_state(self, state_attr: str) -> Any:  # noqa: ANN401
        """Get device state attribute."""
        return getattr(self.state, state_attr)

    @abstractmethod
    async def get_details(self) -> None:
        """Get device details.

        This method is defined in each device class to contain
        the logic to pull the device state from the API and update
        the device's `state` attribute. The `update()` method should
        be called to update the device state.
        """

    async def update(self) -> None:
        """Update device details."""
        await self.get_details()

    def display(self, state: bool = True) -> None:
        """Print formatted static device info to stdout.

        Args:
            state (bool): If True, include state in display, defaults to True.

        Example:
        ```
        Device Name:..................Living Room Lamp
        Model:........................ESL100
        Subdevice No:.................0
        Type:.........................wifi
        CID:..........................1234567890abcdef
        ```
        """
        # noinspection SpellCheckingInspection
        display_list = [
            ('Device Name:', self.device_name),
            ('Product Type: ', self.product_type),
            ('Model: ', self.device_type),
            ('Subdevice No: ', str(self.sub_device_no)),
            ('Type: ', self.type),
            ('CID: ', self.cid),
            ('Config Module: ', self.config_module),
            ('Connection Type: ', self.connection_type),
            ('Features', self.features),
            ('Last Response: ', self.last_response),
        ]
        if self.uuid is not None:
            display_list.append(('UUID: ', self.uuid))

        for line in display_list:
            print(f'{line[0]:.<30} {line[1]}')  # noqa: T201
        if state:
            self.state.display()

    def to_json(self, state: bool = True, indent: bool = True) -> str:
        """Print JSON API string for device details.

        Args:
            state (bool): If True, include state in JSON output, defaults to True.
            indent (bool): If True, indent JSON output, defaults to True.

        Returns:
            str: JSON formatted string of device details.
        """
        return self.to_jsonb(state, indent).decode()

    def to_dict(self, state: bool = True) -> dict[str, Any]:
        """Return device information as a dictionary.

        Args:
            state (bool): If True, include state in dictionary, defaults to True.

        Returns:
            dict[str, Any]: Dictionary containing device information.
        """
        device_dict = {
            'device_name': self.device_name,
            'product_type': self.product_type,
            'model': self.device_type,
            'subdevice_no': str(self.sub_device_no),
            'type': self.type,
            'cid': self.cid,
            'features:': self.features,
            'config_module': self.config_module,
            'connection_type': self.connection_type,
            'last_response': self.last_response,
        }
        state_dict = self.state.to_dict() if state else {}
        return device_dict | state_dict

    def to_jsonb(self, state: bool = True, indent: bool = True) -> bytes:
        """JSON API bytes for device details.

        Args:
            state (bool): If True, include state in JSON output, defaults to True.
            indent (bool): If True, indent JSON output, defaults to True.

        Returns:
            bytes: JSON formatted bytes of device details.

        Example:
            This is an example without state.
            ```
            {
                "Device Name": "Living Room Lamp",
                "Model": "ESL100",
                "Subdevice No": "0",
                "Type": "wifi",
                "CID": "1234567890abcdef"
            }
            ```
        """
        return_dict = self.to_dict(state=state)
        if indent:
            return orjson.dumps(
                return_dict,
                option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS,
            )

        return orjson.dumps(return_dict, option=orjson.OPT_NON_STR_KEYS)


class VeSyncBaseToggleDevice(VeSyncBaseDevice, Generic[VS_STATE_T]):
    """Base class for VeSync devices that can be toggled on and off.

    Parameters:
        details (ResponseDeviceDetailsModel): Device details from API call.
        manager (VeSync): Manager object for API calls.
        feature_map (DeviceMapTemplate): Device configuration map, will be specific
            subclass of DeviceMapTemplate based on device type.

    Attributes:
        state (pyvesync.base_devices.vesyncbasedevice.DeviceState): Device state object
            Each device has a separate state base class in the base_devices module.
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

    Methods:
        set_timer: Set timer for device.
        get_timer: Get timer for device from API.
        clear_timer: Clear timer for device from API.
        set_state: Set device state attribute.
        get_state: Get device state attribute.
        update: Update device details.
        display: Print formatted static device info to stdout.
        to_json: Print JSON API string
        to_jsonb: JSON API bytes device details
        to_dict: Return device information as a dictionary.
        toggle_switch: Toggle device power on or off.
        turn_on: Turn device on.
        turn_off: Turn device off.

    Note:
        Device states are found in the `state` attribute in a subclass of DeviceState
        based on the device type. The `DeviceState` subclass is located in device the
        base_devices module.

        The `last_response` attribute is used to store the last response and error
        information from the API call. See the `pyvesync.errors` module for more
        information.
    """

    __slots__ = ()

    @abstractmethod
    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Toggle device power on or off.

        Args:
            toggle (bool | None): True to turn on, False to turn off, None to toggle.

        Returns:
            bool: True if successful, False otherwise.
        """

    async def turn_on(self) -> bool:
        """Turn device on."""
        return await self.toggle_switch(True)

    async def turn_off(self) -> bool:
        """Turn device off."""
        return await self.toggle_switch(False)


class DeviceState:
    """Base dataclass to hold device state.

    Args:
        device (VeSyncBaseDevice): Device object.
        details (ResponseDeviceDetailsModel): Device details from API call.
        feature_map (DeviceMapTemplate): Device configuration map, will be specific
            subclass of DeviceMapTemplate based on device type.

    Attributes:
        active_time (int): Active time of device, defaults to None.
        connection_status (str): Connection status of device.
        device (VeSyncBaseDevice): Device object.
        device_status (str): Device status.
        features (dict): Features of device.
        last_update_ts (int): Last update timestamp in UTC, defaults to None.

    Methods:
        update_ts: Update last update timestamp.
        to_dict: Dump state to JSON.
        to_json: Dump state to JSON string.
        to_jsonb: Dump state to JSON bytes.
        as_tuple: Convert state to tuple of (name, value) tuples.

    Note:
        This cannot be instantiated directly. It should be inherited by the state class
        of a specific product type.
    """

    __slots__ = (
        '__base_exclusions',
        '_exclude_serialization',
        'active_time',
        'connection_status',
        'device',
        'device_status',
        'features',
        'last_update_ts',
        'timer',
    )

    def __init__(
        self,
        device: VeSyncBaseDevice,
        details: ResponseDeviceDetailsModel,
        feature_map: DeviceMapTemplate,
    ) -> None:
        """Initialize device state."""
        self.__base_exclusions: list[str] = ['manager', 'device', 'state']
        self._exclude_serialization: list[str] = []
        self.device = device
        self.device_status: str = details.deviceStatus or DeviceStatus.UNKNOWN
        self.connection_status: str = details.connectionStatus or ConnectionStatus.UNKNOWN
        self.features = feature_map.features
        self.last_update_ts: int | None = None
        self.active_time: int | None = None
        self.timer: Timer | None = None

    def __str__(self) -> str:
        """Return device state as string."""
        return (
            f'{self.device.device_name}, {self.device.product_type}, '
            f'Device Status:{self.device_status}, '
            f'Connection Status: {self.connection_status}'
        )

    def __repr__(self) -> str:
        """Return device state as string."""
        return (
            f'{self.device.device_name}, Device Status:{self.device_status}, '
            f'Connection Status: {self.connection_status}'
        )

    def update_ts(self) -> None:
        """Update last update timestamp as UTC timestamp."""
        self.last_update_ts = int(dt.now(tz=UTC).timestamp())

    @staticmethod
    def __predicate(attr: Any) -> bool:  # noqa: ANN401
        """Check if attribute should be serialized."""
        return (
            callable(attr)
            or inspect.ismethod(attr)
            or inspect.isbuiltin(attr)
            or inspect.isfunction(attr)
            or inspect.isroutine(attr)
            or inspect.isclass(attr)
        )

    def _serialize(self) -> dict[str, Any]:
        """Get dictionary of state attributes."""
        state_dict: dict[str, Any] = {}
        for attr_name, attr_value in inspect.getmembers(
            self, lambda a: not self.__predicate(a)
        ):
            if attr_name.startswith('_') or attr_name in [
                *self.__base_exclusions,
                *self._exclude_serialization,
            ]:
                continue
            state_dict[attr_name] = attr_value
        return state_dict

    def to_json(self, indent: bool = False) -> str:
        """Dump state to JSON string.

        Args:
            indent (bool): If True, indent JSON output, defaults to False.

        Returns:
            str: JSON formatted string of device state.
        """
        return self.to_jsonb(indent=indent).decode()

    def to_jsonb(self, indent: bool = False) -> bytes:
        """Convert state to JSON bytes."""
        if indent:
            return orjson.dumps(
                self._serialize(), option=orjson.OPT_NON_STR_KEYS | orjson.OPT_INDENT_2
            )
        return orjson.dumps(self._serialize(), option=orjson.OPT_NON_STR_KEYS)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary."""
        return self._serialize()

    def as_tuple(self) -> tuple[tuple[str, Any], ...]:
        """Convert state to tuple of (name, value) tuples."""
        return tuple((k, v) for k, v in self._serialize().items())

    def display(self) -> None:
        """Print formatted state to stdout."""
        for name, val in self._serialize().items():
            print(f'{name:.<30} {val}')  # noqa: T201
