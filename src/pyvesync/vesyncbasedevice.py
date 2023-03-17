"""Base class for all VeSync devices."""

import logging
import json
from typing import Optional, Union
from pyvesync.helpers import Helpers as helper
logger = logging.getLogger(__name__)


class VeSyncBaseDevice:
    """Properties shared across all VeSync devices."""

    def __init__(self, details: dict, manager):
        """Initialize VeSync device base class."""
        self.manager = manager
        if 'cid' in details and details['cid'] is not None:
            self.device_name: str = details.get('deviceName', None)
            self.device_image: Optional[str] = details.get('deviceImg', None)
            self.cid: str = details.get('cid', None)
            self.connection_status: str = details.get('connectionStatus', None)
            self.connection_type: Optional[str] = details.get(
                'connectionType', None)
            self.device_type: str = details.get('deviceType', None)
            self.type: str = details.get('type', None)
            self.uuid: Optional[str] = details.get('uuid', None)
            self.config_module: str = details.get(
                'configModule', None)
            self.mac_id: Optional[str] = details.get('macID', None)
            self.mode: Optional[str] = details.get('mode', None)
            self.speed: Union[str, int, None] = details.get('speed', None)
            self.extension = details.get('extension', None)
            self.current_firm_version = details.get(
                    'currentFirmVersion', None)
            self.device_region: Optional[str] = details.get('deviceRegion', None)
            self.pid = None
            self.sub_device_no = details.get('subDeviceNo', 0)
            self.config: dict = {}
            if isinstance(details.get('extension'), dict):
                ext = details['extension']
                self.speed = ext.get('fanSpeedLevel')
                self.mode = ext.get('mode')
            if self.connection_status != 'online':
                self.device_status = 'off'
            else:
                self.device_status = details.get('deviceStatus', None)

        else:
            logger.error('No cid found for %s', self.__class__.__name__)

    def __eq__(self, other):
        """Use device CID and subdevice number to test equality."""
        return bool(other.cid == self.cid
                    and other.sub_device_no == self.sub_device_no)

    def __hash__(self):
        """Use CID and sub-device number to make device hash."""
        if isinstance(self.sub_device_no, int) and self.sub_device_no > 0:
            return hash(self.cid + str(self.sub_device_no))
        return hash(self.cid)

    def __str__(self):
        """Use device info for string represtation of class."""
        return f'Device Name: {self.device_name}, \
                 Device Type: {self.device_type},\
                 SubDevice No.: {self.sub_device_no},\
                 Status: {self.device_status}'

    def __repr__(self):
        """Representation of device details."""
        return f'DevClass: {self.__class__.__name__},\
                Name:{self.device_name}, Device No: {self.sub_device_no},\
                DevStatus: {self.device_status}, CID: {self.cid}'

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        if self.device_status == 'on':
            return True
        return False

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
        """Print formatted device info to stdout."""
        disp = [
            ('Device Name:', self.device_name),
            ('Model: ', self.device_type),
            ('Subdevice No: ', str(self.sub_device_no)),
            ('Status: ', self.device_status),
            ('Online: ', self.connection_status),
            ('Type: ', self.type),
            ('CID: ', self.cid),
        ]
        if self.uuid is not None:
            disp.append(('UUID: ', self.uuid))

        for line in disp:
            print(f'{line[0]:.<30} {line[1]}')

    def displayJSON(self) -> str:  # pylint: disable=invalid-name
        """JSON API for device details."""
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
