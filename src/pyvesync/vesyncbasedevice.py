import logging
import collections
logger = logging.getLogger(__name__)


class VeSyncDeviceException(Exception):
    """Gets errors reported by devices"""
    pass


class VeSyncBaseDevice(object):
    """Properties shared across all VeSync devices"""
    def __init__(self, details, manager):
        self.manager = manager
        if 'cid' in details and details['cid'] is not None:
            self.device_name = details.get('deviceName', None)
            self.device_image = details.get('deviceImg', None)
            self.cid = details.get('cid', None)
            self.connection_status = details.get('connectionStatus', None)
            self.connection_type = details.get('connectionType', None)
            self.device_type = details.get('deviceType', None)
            self.type = details.get('type', None)
            self.uuid = details.get('uuid', None)
            self.config_module = details.get('configModule', None)
            self.mac_id = details.get('macID', None)
            self.mode = details.get('mode', None)
            self.speed = details.get('speed', None)
            self.extension = details.get('extension', None)
            self.current_firm_version = details.get('currentFirmVersion', None)
            self.sub_device_no = details.get('subDeviceNo', 0)
            self.config = {}
            if self.connection_status is not 'online':
                self.device_status = 'off'
            else:
                self.device_status = details.get('deviceStatus', None)

        else:
            logger.error('No cid found for ' + self.__class__.__name__)

    def __eq__(self, other):
        if other.cid == self.cid and other.sub_device_no == self.sub_device_no:
            return True
        else:
            return False

    def __hash__(self):
        if isinstance(self.sub_device_no, int) and self.sub_device_no > 0:
            return hash(self.cid + str(self.sub_device_no))
        else:
            return hash(self.cid)

    def __str__(self):
        return "Device Name: {}, Device Type: {},\
            SubDevice No.: {} Status: {}".format(
            self.device_name, self.device_type, self.sub_device_no,
            self.device_status)

    def __repr__(self):
        return "DevClass: {}, Name:{}, Device No: {}, DevStatus: {}, CID: {}"\
            .format(self.__class__.__name__, self.device_name,
                    self.sub_device_no, self.device_status, self.cid)

    @property
    def is_on(self) -> bool:
        """Returns whether device is on"""
        if self.device_status == 'on':
            return True
        return False

    @property
    def firmware_update(self) -> bool:
        """Return True if firmware update available"""
        cfv = self.config.get('current_firmware_version')
        lfv = self.config.get('latest_firmware_version')
        if cfv is not None and lfv is not None:
            if cfv != lfv:
                return True
            else:
                return False
        else:
            logger.warning(
                'Call device.get_config() to get firmware versions')

    def display(self):
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
        disp1 = collections.OrderedDict(disp)
        for k, v in disp1.items():
            print("{:.<15} {:<15}".format(k, v))
