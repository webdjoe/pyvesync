from abc import ABCMeta, abstractmethod, abstractproperty, ABC
import hashlib
import logging
import time
import requests
import re
from typing import Any

logger = logging.getLogger(__name__)

ALL_DEVTYPES = [
    'ESW15-USA',
    'ESW10-EU',
    'ESW03-USA',
    'wifi-switch-1.3',
    'ESWL01',
    'ESWL03',
]


class VesyncDeviceException(Exception):
    """Gets errors reported by devices"""
    pass


class VeSyncDeviceFactory(object):
    def __init__(self, device, manager):
        self.manager = manager
        self.device = device

    def device_init(self, device: dict, manager: any):
        device_obj = self.device_classification(device['devType'])
        if device_obj is not None:
            device_obj = device_obj(device, manager)
            return device_obj
        else:
            logger.debug("Device Class Could not be initialized")


    @staticmethod
    def device_classification(devtype: str) -> Any:
        if devtype in ALL_DEVTYPES:
            if devtype == 'ESW15-USA':
                return VeSyncSwitch15A
            elif devtype == 'wifi-switch-1.3':
                return VeSyncSwitch7A
            elif devtype in ['ESWL01', 'ESWL03']:
                return VeSyncInWallSwitch
            elif devtype in ['ESW03-USA', 'ESW10-EU']:
                return VeSyncSwitch10A
            else:
                logger.debug('Unknown device found - ' + devtype)
                return None


class VeSyncDevice(ABCMeta):
    def __init__(self, details, manager):
        self.manager = manager

        self.device_name = None
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
        self.current_firm_version = None
        self.mode = None
        self.speed = None

        self.details = {}
        self.energy = {}

        self.configure(details)

    def configure(self, details):
        try:
            self.device_name = details['deviceName']
        except (ValueError, KeyError):
            logger.error("cannot set device_name")

        try:
            self.device_image = details['deviceImg']
        except (ValueError, KeyError):
            logger.error("cannot set device_image")

        try:
            self.cid = details['cid']
        except (ValueError, KeyError):
            logger.error("cannot set cid")

        try:
            self.device_status = details['deviceStatus']
        except (ValueError, KeyError):
            logger.error("cannot set device_status")

        try:
            self.connection_status = details['connectionStatus']
        except (ValueError, KeyError):
            logger.error("cannot set connection_status")

        try:
            self.connection_type = details['connectionType']
        except (ValueError, KeyError):
            logger.error("cannot set connection_type")

        try:
            self.device_type = details['deviceType']
        except (ValueError, KeyError):
            logger.error("cannot set device type")

        try:
            self.type = details['type']
        except (ValueError, KeyError):
            logger.error("cannot set type")

        try:
            self.uuid = details['uuid']
        except (ValueError, KeyError):
            logger.error("cannot set uuid")

        try:
            self.config_module = details['configModule']
        except (ValueError, KeyError):
            logger.error("cannot set config module")

        try:
            self.current_firm_version = details['currentFirmVersion']
        except (ValueError, KeyError):
            logger.error("cannot set current firm version")

        try:
            self.mode = details['mode']
        except (ValueError, KeyError):
            logger.error("cannot set mode")

        try:
            self.speed = details['speed']
        except (ValueError, KeyError):
            logger.error("cannot set speed")

    @abstractmethod
    def update(self):
        """Gets Device Energy and Status"""
        raise NotImplementedError

    @abstractmethod
    def turn_on(self):
        """Return True if device has beeeen turned on"""
        raise NotImplementedError

    @abstractmethod
    def turn_off(self):
        """Return True if device has beeeen turned off"""
        raise NotImplementedError

    @abstractmethod
    def active_time(self):
        """Return active time of a device in minutes"""
        return self.details.get('active_time')

    @abstractmethod
    def energy_today(self):
        """Return energy"""
        return self.details.get('energy')

    @abstractmethod
    def power(self):
        """Return current power in watts"""
        return float(self.details.get('power', 0))

    @abstractmethod
    def voltage(self):
        """Return current voltage"""
        return float(self.details.get('voltage', 0))

    @abstractmethod
    def monthly_energy_total(self):
        """Return total energy usage over the month"""
        return self.energy.get('month', {}).get('total_energy')

    @abstractmethod
    def weekly_energy_total(self):
        """Return total energy usage over the week"""
        return self.energy.get('week', {}).get('total_energy')

    @abstractmethod
    def yearly_energy_total(self):
        """Return total energy usage over the year"""
        return self.energy.get('year', {}).get('total_energy')
