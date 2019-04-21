from abc import ABCMeta, abstractmethod, abstractproperty
import hashlib
import logging
import time
import requests
import re
from typing import Union

logger = logging.getLogger(__name__)


from .protocol import call_api, check_response, get_body, get_head
from .vesyncdevice import VesyncDeviceException, VeSyncDeviceFactory


DEFAULT_TZ = 'America/New_York'

"""Dict showing which device should get assigned to which dev class"""
DEVICE_MATRIX = {
    'outlets': {"wifi-switch-1.3": ['energy_history'],
                "ESW01-EU": ['energy_history'],
                "ESW15-USA": ['energy_history'],
                "ESW03-USA": ['energy_history']
                },
    'switches': ['ESWL01']
    }


class VeSyncDeviceFeatures(object):
    '''Get Device Classification and Supported Features'''
    def __init__(self, dev_type=None, dev_class=None):
        self.device_matrix = {
            'outlet': {"wifi-switch-1.3": 'energy_history',
                        "ESW01-EU": 'energy_history',
                        "ESW15-USA": 'energy_history',
                        "ESW03-USA": 'energy_history'
                        },
            'switch': {'ESWL01': None,
                       'ESWL03': None,
                       'ESWL02-D': 'dimmable'},
            'air_purifier': {'LV-PUR131S': None}
            }
        self.dev_type = dev_type
        self.dev_class = dev_class
        self.__dict__.update(**DEVICE_MATRIX)
    
    def device_class(self, dev_type):
        if dev_type in self.device_matrix['outlet'].keys():
            return 'outlet'
        if dev_type in self.device_matrix['switch'].keys():
            return 'switch'
        if dev_type in self.device_matrix['air_purifier'].keys():
            return 'purifier'
    
    def device_features(self, dev_type):
        device_found = False
        for item in self.device_matrix.keys():
            for device in item.keys():
                if dev_type == device:
                    device_found = True
                    return self.device_matrix[item][device]
        if not device_found:
            logger.error('Feature lookup failed for unknown device')



def hash_password(password: str) -> str:
    return hashlib.md5(password.encode('utf-8')).hexdigest()


def tz_check(time_zone: str) -> str:
    if len(time_zone) > 0:
        reg_test = r"[^a-zA-Z/_]"
        if bool(re.search(reg_test, time_zone)):
            logger.debug("Invalid Characters in time zone")
            return DEFAULT_TZ
        else:
            return time_zone


def login(username: str, password: str, time_zone: str = DEFAULT_TZ):
    user_check = isinstance(username, str) and len(username) > 0
    pass_check = isinstance(password, str) and len(password) > 0

    if user_check and pass_check:
        body = {}
        hash_pass = hash_password(password)
        body = get_body('login')
        body['email'] = username
        body['password'] = hash_pass

        response, _ = call_api('/cloud/v1/user/login', 
                               'post', json=body)
        if response and check_response(response, 'login'):
            tk = response['result']['token']
            account_id = response['result']['accountID']
            tz = tz_check(time_zone)
            return VeSync(tk, account_id, tz)


def add_auth(part: str, json: dict, vesync_inst: object) -> dict:
    if isinstance(json, dict):
        if part == "header":
            json['tk'] = vesync_inst.tk
            json['tz'] = vesync_inst.tz
            json['accountId'] = vesync_inst.actid
            return json
        elif part == 'body':
            json['token'] = vesync_inst.tk
            json['accountID'] = vesync_inst.account_id
            json['timeZone'] = vesync_inst.tz
            return json


class VeSync(object):
    def __init__(self,
                 token: str,
                 account_id: Union[str, int],
                 time_zone: str):
        self.tk = token
        self.account_id = account_id
        self.tz = time_zone
        self.in_process = False

    def get_devices(self) -> list:
        """Retrieves device list and pass device to VeSyncDeviceFactory"""
        devs = []
        self.in_process = True
        body = get_body('devicelist')
        body = add_auth('body', body, self)
        head = get_head()
        head = add_auth('header', head, self)

        resp, _ = call_api('/cloud/v1/deviceManaged/devices',
                           'post', headers=head, json=body)
        if resp and check_response(resp, 'get_devices'):
            if 'result' in resp and 'list' in resp['result']:
                for device in resp['result']['list']:
                    if 'deviceType' in device:
                        devs.append(VeSyncDeviceFactory(device, self))
