"""Base class for all VeSync devices."""
from __future__ import annotations
from abc import ABC, abstractmethod
import logging
from datetime import datetime as dt
from zoneinfo import ZoneInfo
from typing import TYPE_CHECKING, Any
import warnings  # noqa: F401  # pylint: disable=unused-import
from mashumaro.types import SerializableType
import orjson

from pyvesync.helper_utils.helpers import Helpers
from pyvesync.const import DeviceStatus, ConnectionStatus, IntFlag, StrFlag
from pyvesync.helper_utils.logs import LibraryLogger

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.data_models.device_list_models import ResponseDeviceDetailsModel
    from pyvesync.device_map import DeviceMapTemplate
    from pyvesync.helper_utils.errors import ResponseInfo


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
        "speed",
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
        """Initialize VeSync device base class."""
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
        self.pid = None
        self.sub_device_no = details.subDeviceNo
        # From feature_map
        self.product_type: str = feature_map.product_type
        self.features = feature_map.features

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

    #
    # def __getattr__(self, attr: str) -> object:
    #     """Return attribute from device state."""
    #     if hasattr(self.state, attr):
    #         warnings.warn(
    #             "Access device state through the self.state attribute. "
    #             "Access to state in the device class will be removed in future releases.",  # noqa: E501
    #             category=DeprecationWarning,
    #             stacklevel=2,
    #         )
    #         return getattr(self.state, attr)
    #     return object.__getattribute__(self, attr)

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
        """Get device details."""

    async def update(self) -> None:
        """Update device details."""
        await self.get_details()

    def display(self) -> None:
        """Print formatted static device info to stdout.

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
        disp = [
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
            disp.append(('UUID: ', self.uuid))

        for line in disp:
            print(f'{line[0]:.<30} {line[1]}')

    def displayJSON(self) -> str:  # pylint: disable=invalid-name
        """JSON API for device details.

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
        return orjson.dumps(
            {
                'Device Name': self.device_name,
                'Model': self.device_type,
                'Subdevice No': str(self.sub_device_no),
                'Type': self.type,
                'CID': self.cid,
            },
            option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode()


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


class DeviceState(SerializableType):
    """Base dataclass to hold device state."""

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
        return (f"{self.device.device_name}, Device Status:{self.device_status}, "
                f"Connection Status: {self.connection_status}")

    def __repr__(self) -> str:
        """Return device state as string."""
        return (f"{self.device.device_name}, Device Status:{self.device_status}, "
                f"Connection Status: {self.connection_status}")

    def update_ts(self) -> None:
        """Update last update timestamp."""
        self.last_update_ts = int(dt.now(
            tz=ZoneInfo(self.device.manager.time_zone)).timestamp())

    def _serialize(self) -> bytes:
        """Dump state to JSON."""
        state_dict = {}
        for attr in self.__slots__:
            if attr == 'device':
                continue
            if getattr(self, attr) in [IntFlag.NOT_SUPPORTED, StrFlag.NOT_SUPPORTED]:
                continue
            state_dict[attr] = getattr(self, attr)
        return orjson.dumps(state_dict, option=orjson.OPT_NON_STR_KEYS)

    def dumps(self) -> str:
        """Dump state to JSON."""
        return self._serialize().decode()

    def display(self) -> None:
        """Print formatted state to stdout."""
        state_list = []
        for attr in self.__slots__:
            if attr == 'device':
                continue
            if getattr(self, attr) in [IntFlag.NOT_SUPPORTED, StrFlag.NOT_SUPPORTED]:
                continue
            state_list.append((attr, getattr(self, attr)))
        for line in state_list:
            print(f'{line[0]:.<30} {line[1]}')
