from abc import ABC, ABCMeta


class VeSyncDeviceException(Exception):
    """Gets errors reported by devices"""
    pass


class VeSyncBaseDevice(object):
    """Properties shared across all VeSync devices"""
    def __init__(self, details, manager):
        self.manager = manager

        self.device_name = None
        self.device_image = None
        self.cid = None
        self.device_status = None
        self.connection_status = None
        self.connection_type = None
        self.device_type = None
        self.type = None
        self.uuid = None
        self.config_module = None
        self.mac_id = None
        self.mode = None
        self.speed = None
        self.extension = None
        self.current_firm_version = None

        self.configure(details)

    def configure(self, details):
        self.device_name = details.get('deviceName', None)
        self.device_image = details.get('deviceImg', None)
        self.cid = details.get('cid', None)
        self.device_status = details.get('deviceStatus', None)
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

        if self.device_type is not None:
            return True

    def is_on(self) -> str:
        """Returns whether device is on"""
        return self.device_status
