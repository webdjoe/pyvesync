from abc import ABCMeta, abstractmethod, abstractproperty
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

    def calculate_hex(self, hex_string):
        """Convert Hex Strings to Values"""
        """ CREDIT FOR CONVERSION TO ITSNOTLUPUS/vesync_wsproxy  """
        hex_conv = hex_string.split(':')
        converted_hex = (int(hex_conv[0],16) + int(hex_conv[1],16))/8192  
        return converted_hex

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

    def get_devices(self):
        """Return list of VeSync devices"""

        device_list = []

        if self.enabled:
            self.in_process = True

            body = {}
            body['accountID'] = self.account_id
            body['token'] = self.tk

            response = self.call_api('/platform/v1/app/devices', 'post', headers=self.get_headers(), json=body)

            if response is not None and response:
                if 'devices' in response and response['devices']:
                    for device in response['devices']:
                        if 'deviceType' in device:
                            if device['deviceType'] == 'ESW15-USA':
                                device_list.append(VeSyncSwitch15A(device, self))
                            elif device['deviceType'] == 'wifi-switch-1.3':
                                device_list.append(VeSyncSwitch7A(device, self))
                        else:
                            logger.debug('no devices found')

            self.in_process = False

        return device_list

    def get_headers(self):
        return {'Content-Type': 'application/json'}

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


class VeSyncSwitchABC(object):
    __metaclass__ = ABCMeta

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
        self.current_firm_version = None
        self.mode = None
        self.speed = None

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
            self.connection_status = details['connectionStatus']
        except ValueError:
            logger.error("cannot set connection_status")

        try:
            self.connection_type = details['connectionType']
        except ValueError:
            logger.error("cannot set connection_type")

        try:
            self.device_type = details['deviceType']
        except ValueError:
            logger.error("cannot set device type")

        try:
            self.type = details['type']
        except ValueError:
            logger.error("cannot set type")

        try:
            self.uuid = details['uuid']
        except ValueError:
            logger.error("cannot set uuid")

        try:
            self.config_module = details['configModule']
        except ValueError:
            logger.error("cannot set config module")

        try:
            self.current_firm_version = details['currentFirmVersion']
        except ValueError:
            logger.error("cannot set current firm version")

        try:
            self.mode = details['mode']
        except ValueError:
            logger.error("cannot set mode")

        try:
            self.speed = details['speed']
        except ValueError:
            logger.error("cannot set speed")
    
    @abstractmethod
    def turn_on(self):
        pass

    @abstractmethod
    def turn_off(self):
        pass

    @abstractmethod
    def get_active_time(self):
        pass

    @abstractmethod
    def get_kwh_today(self):
        pass

    @abstractmethod
    def get_power(self):
        pass

    @abstractmethod
    def get_voltage(self):
        pass

    @abstractmethod
    def get_monthly_energy_total(self):
        pass

    @abstractmethod
    def get_weekly_energy_total(self):
        pass

    @abstractmethod
    def get_yearly_energy_total(self):
        pass

    @abstractmethod
    def get_week_daily_energy(self):
        pass

    @abstractmethod
    def update(self):
        pass


class VeSyncSwitch7A(VeSyncSwitchABC):
    def __init__(self, details, manager):
        super(VeSyncSwitch7A, self).__init__(details, manager)

    def get_headers(self):
        return {'tk': self.manager.tk, 'accountID': self.manager.account_id}
    
    def turn_on(self):
        """Return True if device has beeeen turned on"""
        
        response = self.manager.call_api('/v1/wifi-switch-1.3/' + self.cid + '/status/on', 'put', headers=self.get_headers())

        if response is not None and response:
            return True
        else:
            return False
    
    def turn_off(self):
        """Return True if device has beeeen turned on"""
        
        response = self.manager.call_api('/v1/wifi-switch-1.3/' + self.cid + '/status/off', 'put', headers=self.get_headers())

        if response is not None and response:
            return True
        else:
            return False

    def get_active_time(self):
        """Return active time of a device in minutes"""

        response = self.manager.call_api('/v1/device/' + self.cid + '/detail', 'get', headers=self.get_headers())

        if response is not None and response:
            if 'activeTime' in response and response['activeTime'] is not None:
                if response['activeTime'] >= 0:
                    return response['activeTime']

        return 0

    def get_kwh_today(self):
        """Return total kWh for current date of a device"""

        response = self.manager.call_api('/v1/device/' + self.cid + '/energy/week', 'get', headers=self.get_headers())

        if response is not None and response:
            if 'energyConsumptionOfToday' in response and response['energyConsumptionOfToday']:
                return response['energyConsumptionOfToday']
        
        return None

    def get_power(self):
        """Return current power in watts of a device"""

        response = self.manager.call_api('/v1/device/' + self.cid + '/detail', 'get', headers=self.get_headers())

        if response is not None and response:
            if 'power' in response and response['power']:
                watts = self.manager.calculate_hex(response['power'])
                if watts is not None and watts > 0:
                    return watts
        
        return 0
    
    def get_voltage(self):
        """ Return Current Voltage """

        response = self.manager.call_api('/v1/device/' + self.cid + '/detail', 'get', headers=self.get_headers())

        if response is not None and response:
            if 'voltage' in response and response['voltage']:
                voltage = self.manager.calculate_hex(response['voltage'])
                if voltage is not None and voltage > 0:
                    return voltage
        return 0

    def get_weekly_energy_total(self):
        """Returns the total weekly energy usage  """
        response = self.manager.call_api('/v1/device/' + self.cid + '/energy/week', 'get', headers=self.get_headers())

        if response is not None and response:
            if 'totalEnergy' in response and response['totalEnergy']:
                return response['totalEnergy']
        
        return 1
    
    def get_monthly_energy_total(self):
        """Returns total energy usage over the month"""
        response = self.manager.call_api('/v1/device/' + self.cid + '/energy/month', 'get', headers=self.get_headers())

        if response is not None and response:
            if 'totalEnergy' in response and response['totalEnergy']:
                return response['totalEnergy']
        
        return 0
    
    def get_yearly_energy_total(self):
        """Returns total energy usage over the year"""
        response = self.manager.call_api('/v1/device/' + self.cid + '/energy/year', 'get', headers=self.get_headers())

        if response is not None and response:
            if 'totalEnergy' in response and response['totalEnergy']:
                return response['totalEnergy']
        
        return 0
    
    def get_week_daily_energy(self):
        """Returns daily energy usage over the week"""
        response = self.manager.call_api('/v1/device/' + self.cid + '/energy/week', 'get', headers=self.get_headers())
        if response is not None and response:
            if 'data' in response and response['data']:
                return response['data']

        return 0


class VeSyncSwitch15A(VeSyncSwitchABC):
    def __init__(self, details, manager):
        super(VeSyncSwitch15A, self).__init__(details, manager)
        self.mobile_id = '1234567890123456'

    def get_body(self):
        body = {}
        body['accountID'] = self.manager.account_id
        body['token'] = self.manager.tk
        body['uuid'] = self.uuid

        return body

    def get_headers(self):
        return {'Content-Type': 'application/json'}
    
    def turn_on(self):
        """Return True if device has beeeen turned on"""

        body = self.get_body()
        body['status'] = 'on'

        response = self.manager.call_api('/15a/v1/device/devicestatus', 'put', headers=self.get_headers(), json=body)

        if response is not None and response:
            return True
        else:
            return False
    
    def turn_off(self):
        """Return True if device has beeeen turned on"""

        body = self.get_body()
        body['status'] = 'off'
        
        response = self.manager.call_api('/15a/v1/device/devicestatus', 'put', headers=self.get_headers(), json=body)

        if response is not None and response:
            return True
        else:
            return False

    def get_active_time(self):
        """Return active time of a device in minutes"""

        body = self.get_body()
        body['mobileID'] = self.mobile_id

        response = self.manager.call_api('/15a/v1/device/devicedetail', 'post', headers=self.get_headers(), json=body)

        if response is not None and response:
            if 'activeTime' in response and response['activeTime'] is not None:
                if response['activeTime'] >= 0:
                    return response['activeTime']

        return 0

    def get_kwh_today(self):
        print('todo')

    def get_power(self):
        print('todo')
    
    def get_voltage(self):
        print('todo')

    def get_monthly_energy_total(self):
        print('todo')

    def get_weekly_energy_total(self):
        print('todo')

    def get_yearly_energy_total(self):
        print('todo')
    
    def get_week_daily_energy(self):
        print('todo')
