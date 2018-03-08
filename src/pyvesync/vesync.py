import hashlib
import logging
import time
import requests


logger = logging.getLogger(__name__)

API_BASE_URL = 'https://smartapi.vesync.com'
API_RATE_LIMIT = 30


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

    def call_api(self, api, method, json=None, headers=None):
        response = None

        try:
            logger.info("[%s] calling '%s' api" % (method, api))
            if method == 'get':
                r = requests.get(API_BASE_URL + api, json=json, headers=headers)
            elif method == 'post':
                r = requests.post(API_BASE_URL + api, json=json, headers=headers)
            elif method == 'put':
                r = requests.put(API_BASE_URL + api, json=json, headers=headers)
        except Exception:
            logger.info("error")
            pass
        else:
            if r.status_code == 200:
                response = r.json()
        finally:
            return response

    def login(self):
        try:
            jd = {'account': self.username, 'password': hashlib.md5(self.password.encode('utf-8')).hexdigest()}
        except ValueError:
            logger.info("error getting username and password")
            return False
        else:
            try:
                response = self.call_api('/vold/user/login', 'post', json=jd)
            except Exception as e:
                logger.info("error logging in %s" % (e))
                pass
            else:
                if response is not None and 'tk' in response and 'accountID' in response:
                    self.tk = response['tk']
                    self.account_id = response['accountID']
                    self.enabled = True

                    return True

            return False

    def get_devices(self):
        device_list = []

        if self.enabled:
            self.in_process = True

            try:
                response = self.call_api('/vold/user/devices', 'get', headers=self.get_headers())
            except Exception as e:
                logger.info("received exception %s" % (e))
                pass
            else:
                for device in response:
                    if 'deviceType' in device and 'switch' in device['deviceType']:
                        device_list.append(VeSyncSwitch(device, self))
            finally:
                self.in_process = False

        return device_list

    def get_headers(self):
        return {'tk': self.tk, 'accountID': self.account_id}

    def turn_on(self, cid):
        try:
            response = self.call_api('/v1/wifi-switch-1.3/' + cid + '/status/on', 'put', headers=self.get_headers())
        except Exception as e:
            logger.info("error - %s" % (e))
            pass
        else:
            return True
        
        return False

    def turn_off(self, cid):
        try:
            response = self.call_api('/v1/wifi-switch-1.3/' + cid + '/status/off', 'put', headers=self.get_headers())
        except Exception as e:
            logger.info("error - %s" % (e))
            pass
        else:
            return True
        
        return False

    def update(self):
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

    def get_current(self, cid):
        return None

    def get_power(self, cid):
        return None

    def get_voltage(self, cid):
        return None


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

    def turn_on(self):
        if self.manager.turn_on(self.cid):
            self.device_status = "on"
        else:
            self.device_status = "off"

    def turn_off(self):
        if self.manager.turn_off(self.cid):
            self.device_status = "off"
        else:
            self.device_status = "off"

    def get_current(self):
        return self.manager.get_current(self.cid)

    def get_power(self):
        return self.manager.get_power(self.cid)

    def get_voltage(self):
        return self.manager.get_voltage(self.cid)

    def set_config(self, switch):
        self.device_name = switch.device_name
        self.device_image = switch.device_image
        self.device_status = switch.device_status
        self.connection_type = switch.connection_type
        self.connection_status = switch.connection_status
        self.device_type = switch.device_type
        self.model = switch.model

    def update(self):
        self.manager.update()
