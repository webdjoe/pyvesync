import hashlib
import logging
import time
import requests


logger = logging.getLogger(__name__)

API_BASE_URL = 'https://smartapi.vesync.com'
API_RATE_LIMIT = 30
API_TIMEOUT = 5


class VeSync(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.tk = None
        self.account_id = None
        self.devices = None
        self.enabled = False

        self.update_interval = API_RATE_LIMIT
        self.last_update_ts = None
        self.in_process = False

    def calculate_watts(self, kwh, minutes):
        """Return current watt usage of a device"""

        try:
            watts = (kwh * 60 * 1000) / minutes
        except ZeroDivisionError:
            return None
        except Exception as e:
            logger.error('Unable to calculate watts')
            return None
        else:
            return watts

    def call_api(self, api, method, json=None, headers=None):
        response = None

        try:
            logger.debug("[%s] calling '%s' api" % (method, api))
            if method == 'get':
                r = requests.get(API_BASE_URL + api, json=json, headers=headers, timeout=API_TIMEOUT)
            elif method == 'post':
                r = requests.post(API_BASE_URL + api, json=json, headers=headers, timeout=API_TIMEOUT)
            elif method == 'put':
                r = requests.put(API_BASE_URL + api, json=json, headers=headers, timeout=API_TIMEOUT)
        except requests.exceptions.RequestException as e:
            logger.error(e)
        except Exception as e:
            logger.error(e)
        else:
            if r.status_code == 200:
                response = r.json()
        finally:
            return response

    def get_active_time(self, cid):
        """Return active time of a device in minutes"""

        response = self.call_api('/v1/device/' + cid + '/detail', 'get', headers=self.get_headers())

        if response is not None and response:
            if 'activeTime' in response and response['activeTime'] is not None:
                if response['activeTime'] >= 0:
                    return response['activeTime']

        return 0

    def get_devices(self):
        """Return list of VeSync devices"""

        device_list = []

        if self.enabled:
            self.in_process = True

            response = self.call_api('/vold/user/devices', 'get', headers=self.get_headers())

            if response is not None and response:
                for device in response:
                    if 'deviceType' in device and 'switch' in device['deviceType']:
                        device_list.append(VeSyncSwitch(device, self))

            self.in_process = False

        return device_list

    def get_headers(self):
        return {'tk': self.tk, 'accountID': self.account_id}

    def get_kwh_today(self, cid):
        """Return total kWh for current date of a device"""

        response = self.call_api('/v1/device/' + cid + '/energy/week', 'get', headers=self.get_headers())

        if response is not None and response:
            if 'energyConsumptionOfToday' in response and response['energyConsumptionOfToday']:
                return response['energyConsumptionOfToday']
        
        return None

    def get_power(self, cid):
        """Return current power in watts of a device"""

        response = self.call_api('/v1/device/' + cid + '/detail', 'get', headers=self.get_headers())

        if response is not None and response:
            if 'energy' in response and response['energy']:
                if 'activeTime' in response and response['activeTime'] is not None:
                    watts = self.calculate_watts(response['energy'], response['activeTime'])

                    if watts is not None and watts > 0:
                        return watts
        
        return 0

    def login(self):
        """Return True if log in request succeeds"""

        try:
            jd = {'account': self.username, 'password': hashlib.md5(self.password.encode('utf-8')).hexdigest()}
        except ValueError:
            logger.error("Unable to read username and password")

            return False
        else:
            response = self.call_api('/vold/user/login', 'post', json=jd)

            if response is not None and response and 'tk' in response and 'accountID' in response:
                self.tk = response['tk']
                self.account_id = response['accountID']
                self.enabled = True

                return True

            return False

    def turn_off(self, cid):
        """Return True if device has beeeen turned off"""

        response = self.call_api('/v1/wifi-switch-1.3/' + cid + '/status/off', 'put', headers=self.get_headers())

        if response is not None and response:
            return True
        else:
            return False

    def turn_on(self, cid):
        """Return True if device has beeeen turned on"""
        
        response = self.call_api('/v1/wifi-switch-1.3/' + cid + '/status/on', 'put', headers=self.get_headers())

        if response is not None and response:
            return True
        else:
            return False

    def update(self):
        """Fetch updated information about devices"""

        if self.last_update_ts == None or (time.time() - self.last_update_ts) > self.update_interval:
            
            if not self.in_process:
                updated_device_list = self.get_devices()

                if updated_device_list is not None and updated_device_list:
                    for new_device in updated_device_list:
                        
                        if self.devices is not None and self.devices:  # Check if device is already known
                            was_found = False

                            for device in self.devices:
                                if device.cid == new_device.cid:
                                    device.set_config(new_device)

                                    was_found = True
                                    break

                            if not was_found:
                                self.devices.append(new_device)
                        else:
                            self.devices = []
                            self.devices.append(new_device)  

                    self.last_update_ts = time.time()


class VeSyncSwitch(object):
    def __init__(self, details, manager):
        self.manager = manager

        self.device_name = None
        self.device_image = None
        self.cid = None
        self.device_status = None
        self.connection_type = None
        self.connection_status = None
        self.device_type = None
        self.model = None

        self.configure(details)

    def configure(self, details):
        try:
            self.device_name = details['deviceName']
        except ValueError:
            logger.error("cannot set device_name")

        try:
            self.device_image = details['deviceImg']
        except ValueError:
            logger.error("cannot set device_image")

        try:
            self.cid = details['cid']
        except ValueError:
            logger.error("cannot set cid")

        try:
            self.device_status = details['deviceStatus']
        except ValueError:
            logger.error("cannot set device_status")

        try:
            self.connection_type = details['connectionType']
        except ValueError:
            logger.error("cannot set connection_type")

        try:
            self.connection_status = details['connectionStatus']
        except ValueError:
            logger.error("cannot set connection_status")

        try:
            self.device_type = details['deviceType']
        except ValueError:
            logger.error("Unable to set value for device type")

        try:
            self.model = details['model']
        except ValueError:
            logger.error("Unable to set switch value for model")

    def get_active_time(self):
        return self.manager.get_active_time(self.cid)

    def get_kwh_today(self):
        return self.manager.get_kwh_today(self.cid)

    def get_power(self):
        return self.manager.get_power(self.cid)

    def set_config(self, switch):
        self.device_name = switch.device_name
        self.device_image = switch.device_image
        self.device_status = switch.device_status
        self.connection_type = switch.connection_type
        self.connection_status = switch.connection_status
        self.device_type = switch.device_type
        self.model = switch.model

    def turn_off(self):
        if self.manager.turn_off(self.cid):
            self.device_status = "off"

    def turn_on(self):
        if self.manager.turn_on(self.cid):
            self.device_status = "on"

    def update(self):
        self.manager.update()
