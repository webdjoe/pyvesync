"""Base class for all VeSync devices."""
from __future__ import annotations
from abc import ABC, abstractmethod
import logging
import inspect
from datetime import datetime as dt
from zoneinfo import ZoneInfo
from typing import TYPE_CHECKING, Any
import warnings
import orjson

from pyvesync.utils.helpers import Helpers
from pyvesync.const import DeviceStatus, ConnectionStatus, IntFlag, StrFlag
from pyvesync.utils.logs import LibraryLogger
from pyvesync.models.base_models import DefaultValues, RequestBaseModel

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
    from pyvesync.device_map import DeviceMapTemplate
    from pyvesync.utils.errors import ResponseInfo


class VeSyncBaseDevice(ABC):
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
        device_region (str): Region of device. (US, EU, etc.)
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.

    Methods:
        is_on(): Return True if device is on.
        firmware_update(): Return True if firmware update available.
        display(): Print formatted device info to stdout.
        displayJSON(): JSON API for device details.

    Note:
        Device states are found in the `state` attribute in a subclass of DeviceState
        based on the device type. The `DeviceState` subclass is located in device the
        base_devices module.

        The `last_response` attribute is used to store the last response and error
        information from the API call. See the `pyvesync.errors` module for more
        information.

    """

    __slots__ = (
        "cid",
        "config_module",
        "connection_type",
        "current_firm_version",
        "device_image",
        "device_name",
        "device_region",
        "device_type",
        "enabled",
        "features",
        "last_response",
        "mac_id",
        "manager",
        "pid",
        "product_type",
        "request_keys",
        "state",
        "sub_device_no",
        "type",
        "uuid",
    )

    def __init__(self,
                 details: ResponseDeviceDetailsModel,
                 manager: VeSync,
                 feature_map: DeviceMapTemplate
                 ) -> None:
        """Initialize VeSync device base class.

        Args:
            details (ResponseDeviceDetailsModel): Device details from API call.
            manager (VeSync): Manager object for API calls.
            feature_map (DeviceMapTemplate): Device configuration map, will be specific
        """
        self.enabled: bool = True
        self.state: DeviceState = DeviceState(self, details, feature_map)
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
        self.device_region: str | None = details.deviceRegion
        self.pid: str | None = None
        self.sub_device_no = details.subDeviceNo
        # From feature_map
        self.product_type: str = feature_map.product_type
        self.features = feature_map.features

    def build_request_from_model(
        self,
        model: type[RequestBaseModel],
        request_keys: list[str],
        instances: list[object] | None = None,
        update_dict: dict[str, Any] | None = None,
    ) -> RequestBaseModel:
        """Pass a model in to build a request.

        The instances argument is a list of instances to build the request from.
        No need to pass the device or VeSync instance. It automatically gets the
        attributes from the device instance and VeSync instance.

        Args:
            model (SerializableType): Model to build request from.
            request_keys (dict[str, str]): Dictionary of keys and type to use for request.
            instances (list[object] | None): List of additional classes to get
                attributes for the request model.
            update_dict (dict[str, Any]): Optional dictionary to update dict.

        Returns:
            dict[str, Any] | None : Built dictionary of request from keys

        Note:
            Order of building the request is:
            1. DefaultValues class
            2. VeSync manager
            3. Device
            4. Other Instances
            5. Update dict
        """
        request_dict: dict[str, Any] = {}
        request_dict.update(Helpers.get_class_attributes(DefaultValues, request_keys))
        request_dict.update(Helpers.get_class_attributes(self.manager, request_keys))
        request_dict.update(Helpers.get_class_attributes(self, request_keys))
        if instances is not None and len(instances) > 0:
            for obj in instances:
                request_dict.update(Helpers.get_class_attributes(obj, request_keys))

        if update_dict is not None:
            request_dict.update(update_dict)
        return model.from_dict(request_dict)

    def __eq__(self, other: object) -> bool:
        """Use device CID and sub-device number to test equality."""
        if not isinstance(other, VeSyncBaseDevice):
            return NotImplemented
        return bool(other.cid == self.cid
                    and other.sub_device_no == self.sub_device_no)

    def __hash__(self) -> int:
        """Use CID and sub-device number to make device hash."""
        if isinstance(self.sub_device_no, int) and self.sub_device_no > 0:
            return hash(self.cid + str(self.sub_device_no))
        return hash(self.cid)

    def __str__(self) -> str:
        """Use device info for string representation of class."""
        return (
            f"Device Name: {self.device_name}, "
            f"Device Type: {self.device_type}, "
            f"SubDevice No.: {self.sub_device_no}"
        )

    def __repr__(self) -> str:
        """Representation of device details."""
        return (
            f"DevClass: {self.__class__.__name__}, "
            f"Product Type: {self.product_type}, "
            f"Name:{self.device_name}, "
            f"Device No: {self.sub_device_no}, "
            f"CID: {self.cid}"
        )

    def __getattr__(self, attr: str) -> object:
        """Return attribute from device state.

        This will be removed in the next release.
        """
        if hasattr(self.state, attr):
            warnings.warn(
                "Access device state through the self.state attribute. "
                "Access to state in the device class will be removed in future releases.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return getattr(self.state, attr)
        return object.__getattribute__(self, attr)

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self.state.device_status in [DeviceStatus.ON, DeviceStatus.RUNNING]

    @property
    def firmware_update(self) -> bool:
        """Return True if firmware update available.

        This is going to be updated.
        """
        return False

    async def get_pid(self) -> None:
        """Get managed device configuration."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['configModule'] = self.config_module
        body['region'] = self.device_region
        body['method'] = 'configInfo'
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/configInfo', 'post', json_object=body
            )
        if r_bytes is None or len(r_bytes) == 0:
            LibraryLogger.log_device_api_response_error(
                logger, self.device_name, self.device_type, 'get_pid', "Empty response"
            )
            return
        try:
            r = orjson.loads(r_bytes)
        except orjson.JSONDecodeError as err:
            LibraryLogger.log_device_api_response_error(
                logger, self.device_name, self.device_type, 'get_pid', err.msg
            )
            return
        if r.get('code') != 0:
            LibraryLogger.log_device_return_code(
                logger, 'get_pid', self.device_name, self.device_type,
                r.get('code'), r.get('msg', '')
                )
            return
        self.pid = r.get('result', {}).get('pid')

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
        the logic to pull the device state.
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
        ]
        if self.uuid is not None:
            display_list.append(('UUID: ', self.uuid))

        for line in display_list:
            print(f'{line[0]:.<30} {line[1]}')
        if state:
            self.state.display()

    def displayJSON(self, state: bool = True, indent: bool = True) -> str:  # pylint: disable=invalid-name
        """JSON API for device details.

        Args:
            state (bool): If True, include state in JSON output, defaults to True.
            indent (bool): If True, indent JSON output, defaults to True.

        Returns:
            str: JSON formatted string of device details.

        Example:
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
        device_dict = {
            "Device Name": self.device_name,
            "Model": self.device_type,
            "Subdevice No": str(self.sub_device_no),
            "Type": self.type,
            "CID": self.cid,
        }
        state_dict = self.state.to_dict() if state else {}
        if indent:
            return orjson.dumps(
                device_dict | state_dict,
                option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS,
            ).decode()

        return orjson.dumps(
            device_dict | state_dict, option=orjson.OPT_NON_STR_KEYS
        ).decode()


class VeSyncBaseToggleDevice(VeSyncBaseDevice):
    """Base class for VeSync devices that can be toggled on and off."""

    __slots__ = ()

    @abstractmethod
    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Toggle device power on or off."""

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
        active_time (int | None): Active time of device.
        connection_status (str): Connection status of device.
        device (VeSyncBaseDevice): Device object.
        device_status (str): Device status.
        features (dict): Features of device.
        last_update_ts (int | None): Last update timestamp of device.

    Methods:
        update_ts(): Update last update timestamp.
        dumps(): Dump state to JSON.

    Note:
        This is not meant to be used directly. It should be inherited by the state class
        of a specific product type.
    """

    __slots__ = (
        "active_time",
        "connection_status",
        "device",
        "device_status",
        "features",
        "last_update_ts",
    )

    def __init__(
        self,
        device: VeSyncBaseDevice,
        details: ResponseDeviceDetailsModel,
        feature_map: DeviceMapTemplate
            ) -> None:
        """Initialize device state."""
        self.device = device
        self.device_status: str = details.deviceStatus or DeviceStatus.UNKNOWN
        self.connection_status: str = details.connectionStatus or ConnectionStatus.UNKNOWN
        self.features = feature_map.features
        self.last_update_ts: int | None = None
        self.active_time: int | None = None

    def __str__(self) -> str:
        """Return device state as string."""
        return (f"{self.device.device_name}, {self.device.product_type}, "
                f"Device Status:{self.device_status}, "
                f"Connection Status: {self.connection_status}")

    def __repr__(self) -> str:
        """Return device state as string."""
        return (f"{self.device.device_name}, Device Status:{self.device_status}, "
                f"Connection Status: {self.connection_status}")

    def update_ts(self) -> None:
        """Update last update timestamp."""
        self.last_update_ts = int(dt.now(
            tz=ZoneInfo(self.device.manager.time_zone)).timestamp())

    @staticmethod
    def __predicate(attr: Any) -> bool:
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
                self, lambda a: not self.__predicate(a)):
            # if attr_name in ignored_attr or attr_name.startswith('_'):
            #     continue
            if attr_name.startswith("_") or attr_name in ['features', 'device']:
                continue
            if attr_value in [IntFlag.NOT_SUPPORTED, StrFlag.NOT_SUPPORTED]:
                continue
            state_dict[attr_name] = attr_value
        return state_dict

    def dumps(self, indent: bool = False) -> str:
        """Dump state to JSON string.

        Args:
            indent (bool): If True, indent JSON output, defaults to False.

        Returns:
            str: JSON formatted string of device state.
        """
        if indent:
            return orjson.dumps(
                self._serialize(), option=orjson.OPT_NON_STR_KEYS | orjson.OPT_INDENT_2
            ).decode()
        return orjson.dumps(self._serialize(), option=orjson.OPT_NON_STR_KEYS).decode()

    def to_json(self, indent: bool = False) -> bytes:
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

    def display(self, state: bool = True) -> None:
        """Print formatted state to stdout."""
        state_dict = self._serialize()
        for name, val in state_dict.items():
            print(f'{name:.<30} {val}')
        if state:
            self.device.state.display()
