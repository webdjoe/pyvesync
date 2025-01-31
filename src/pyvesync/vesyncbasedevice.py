"""Base class for all VeSync devices."""
from __future__ import annotations
import logging
import json
from typing import TYPE_CHECKING
from pyvesync.helpers import Helpers as helper  # noqa: N813

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pyvesync import VeSync

STATUS_ON = 'on'
STATUS_OFF = 'off'
MODE_ADVANCED_SLEEP = 'advancedSleep'
MODE_AUTO = 'auto'
MODE_DIM = 'dim'
MODE_HUMIDITY = 'humidity'
MODE_MANUAL = 'manual'
MODE_NORMAL = 'normal'
MODE_PET = 'pet'
MODE_SLEEP = 'sleep'
MODE_TURBO = 'turbo'

class VeSyncBaseDevice:
    """Properties shared across all VeSync devices.

    Base class for all VeSync devices.

    Parameters:
        details (dict): Device details from API call.
        manager (VeSync): Manager object for API calls.

    Attributes:
        device_name (str): Name of device.
        device_image (str): URL for device image.
        cid (str): Device ID.
        connection_status (str): Connection status of device.
        connection_type (str): Connection type of device.
        device_type (str): Type of device.
        type (str): Type of device.
        uuid (str): UUID of device, not always present.
        config_module (str): Configuration module of device.
        mac_id (str): MAC ID of device.
        mode (str): Mode of device.
        speed (Union[str, int]): Speed of device.
        extension (dict): Extension of device, not used.
        current_firm_version (str): Current firmware version of device.
        device_region (str): Region of device. (US, EU, etc.)
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        config (dict): Configuration of device, including firmware version
        device_status (str): Status of device, on or off.

    Methods:
        is_on(): Return True if device is on.
        firmware_update(): Return True if firmware update available.
        display(): Print formatted device info to stdout.
        displayJSON(): JSON API for device details.
    """

    def __init__(self, details: dict, manager: VeSync) -> None:
        """Initialize VeSync device base class."""
        self.manager = manager
        if 'cid' in details and details['cid'] is not None:
            self.device_name: str = details['deviceName']
            self.device_image: str | None = details.get('deviceImg')
            self.cid: str = details['cid']
            self.connection_status: str = details['connectionStatus']
            self.connection_type: str | None = details.get(
                'connectionType')
            self.device_type: str = details['deviceType']
            self.type: str | None = details.get('type')
            self.uuid: str | None = details.get('uuid')
            self.config_module: str = details['configModule']
            self.mac_id: str | None = details.get('macID')
            self.mode: str | None = details.get('mode')
            self.speed: int | None = details.get('speed') if details.get(
                'speed') != '' else None
            self.extension = details.get('extension')
            self.current_firm_version = details.get(
                    'currentFirmVersion')
            self.device_region: str | None = details.get('deviceRegion')
            self.pid = None
            self.sub_device_no = details.get('subDeviceNo', 0)
            self.config: dict = {}
            if isinstance(details.get('extension'), dict):
                ext = details['extension']
                self.speed = ext.get('fanSpeedLevel')
                self.mode = ext.get('mode')
            if self.connection_status != 'online':
                self.device_status: str | None = STATUS_OFF
            else:
                self.device_status = details.get('deviceStatus')

        else:
            logger.error('No cid found for %s', self.__class__.__name__)

    def __eq__(self, other: object) -> bool:
        """Use device CID and subdevice number to test equality."""
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
        """Use device info for string represtation of class."""
        return f'Device Name: {self.device_name}, ' + \
               f'Device Type: {self.device_type}, ' + \
               f'SubDevice No.: {self.sub_device_no}, ' + \
               f'Status: {self.device_status}'

    def __repr__(self) -> str:
        """Representation of device details."""
        return f'DevClass: {self.__class__.__name__}, ' + \
               f'Name:{self.device_name}, ' + \
               f'Device No: {self.sub_device_no}, ' + \
               f'DevStatus: {self.device_status}, ' + \
               f'CID: {self.cid}'

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return (self.device_status == STATUS_ON)

    @property
    def firmware_update(self) -> bool:
        """Return True if firmware update available."""
        cfv = self.config.get('current_firmware_version')
        lfv = self.config.get('latest_firmware_version')
        if cfv is not None and lfv is not None:
            if cfv != lfv:
                return True
        else:
            logger.debug('Call device.get_config() to get firmware versions')
        return False

    def get_pid(self) -> None:
        """Get managed device configuration."""
        body = helper.req_body(self.manager, 'devicedetail')
        body['configModule'] = self.config_module
        body['region'] = self.device_region
        body['method'] = 'configInfo'
        r, _ = helper.call_api('/cloud/v1/deviceManaged/configInfo',
                               'post',
                               json_object=body)
        if not isinstance(r, dict) or r.get('code') != 0 or r.get('result') is None:
            logger.error('Error getting config info for %s', self.device_name)
            return
        self.pid = r.get('result', {}).get('pid')

    def display(self) -> None:
        """Print formatted device info to stdout.

        Example:
        ```
        Device Name:..................Living Room Lamp
        Model:........................ESL100
        Subdevice No:.................0
        Status:.......................on
        Online:.......................online
        Type:.........................wifi
        CID:..........................1234567890abcdef
        ```
        """
        disp = [
            ('Device Name', self.device_name),
            ('Model', self.device_type),
            ('Subdevice No', str(self.sub_device_no)),
            ('Status', self.device_status),
            ('Connection', self.connection_status),
            ('Type', self.type),
            ('CID', self.cid),
        ]
        if self.uuid is not None:
            disp.append(('UUID', self.uuid))

        for line in disp:
            print(f"{line[0]+': ':.<30} {line[1]}")

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
            "Status": "on",
            "Online": "online",
            "Type": "wifi",
            "CID": "1234567890abcdef"
        }
        ```
        """
        return json.dumps(
            {
                'Device Name': self.device_name,
                'Model': self.device_type,
                'Subdevice No': str(self.sub_device_no),
                'Status': self.device_status,
                'Online': self.connection_status,
                'Type': self.type,
                'CID': self.cid,
            },
            indent=4)
