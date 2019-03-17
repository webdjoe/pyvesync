from abc import ABCMeta, abstractmethod, abstractproperty
import hashlib
import logging
import time
import requests


logger = logging.getLogger(__name__)

API_BASE_URL = 'https://smartapi.vesync.com'
API_RATE_LIMIT = 30
API_TIMEOUT = 5

DEFAULT_TZ = 'America/New_York'

#Constants
APP_VERSION = '2.5.1'
PHONE_BRAND = 'SM N9005'
PHONE_OS = 'Android'
MOBILE_ID = '1234567890123456'
USER_TYPE = '1'

class VeSync(object):
    def __init__(self, username, password, time_zone):
        self.username = username
        self.password = password
        self.time_zone = time_zone
        self.tk = None
        self.account_id = None
        self.devices = None
        self.enabled = False
        self.update_interval = API_RATE_LIMIT
        self.last_update_ts = None
        self.in_process = False

    #I'm working on a regular expression test that's more robust but it's not ready yet
    if isinstance(time_zone, str) and len(time_zone) > 2:
        i = 0
        for a in time_zone:
            if (a.isSpace()) == True:
                i += 1
        if i == 0:
            self.time_zone = time_zone
        else:
            self.time_zone = DEFAULT_TZ

    else:
        self.time_zone = DEFAULT_TZ


    def call_api(self, api, method, json=None, headers=None):
        response = None
        status_code = None

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
                status_code = 200
                response = r.json()
        finally:
            return (response, status_code)

    def get_devices(self):
        """Return list of VeSync devices"""

        device_list = []

        if self.enabled:
            self.in_process = True

            body = self.get_body('devicelist')
            body['method'] = 'devices'

            response, _ = self.call_api('/cloud/v1/deviceManaged/devices', 'post', headers=self.get_headers(), json=body)

            if response and self.check_response(response, 'get_devices'):
                if response['result']:
                    for device in response['result']['list']:
                        if 'deviceType' in device:
                            if device['deviceType'] == 'wifi-switch-1.3':
                                device_list.append(VeSyncSwitch7A(device, self))
                            elif device['deviceType'] == 'ESW15-USA':
                                device_list.append(VeSyncSwitch15A(device, self))
                            elif device['deviceType'] == 'ESWL01':
                                device_list.append(VeSyncSwitchInWall(device, self))
                            elif device['deviceType'] == 'ESW01-EU':
                                device_list.append(VeSyncSwitchEU10A(device, self))
                        else:
                            logger.debug('no devices found')

            self.in_process = False

        return device_list

    def get_energy_dict_from_api(self, response):
        data = {}
        data['energy_consumption_of_today'] = response['energyConsumptionOfToday']
        data['cost_per_kwh'] = response['costPerKWH']
        data['max_energy'] = response['maxEnergy']
        data['total_energy'] = response['totalEnergy']
        data['currency'] = response['currency'] if 'currency' in response else ''
        data['data'] = response['data']

        return data

    def get_headers(self):
        header = {}
        header['accept-language'] = 'en'
        header['accountId'] = self.account_id
        header['appVersion'] = APP_VERSION
        header['content-type'] = 'application/json'
        header['tk'] = self.tk
        header['tz'] = self.time_zone
        return header

    def get_body(self, type_):
        bodybase = {}
        bodybase['timeZone'] = self.time_zone
        bodybase['acceptLanguage'] = 'en'

        bodyauth = {}
        bodyauth['accountID'] = self.account_id
        bodyauth['token'] = self.tk

        bodydetails = {}
        bodydetails['appVersion'] = APP_VERSION
        bodydetails['phoneBrand'] = PHONE_BRAND
        bodydetails['phoneOS'] = PHONE_OS
        bodydetails['traceId'] = str(int(time.time()))

        if type_ == 'login':
            login = dict(**bodybase, **bodydetails)
            login['devToken'] = ''
            login['userType'] = USER_TYPE
            login['method'] = 'login'
            return login
        elif type_ == 'devicelist':
            devlist = dict(**bodybase, **bodyauth, **bodydetails)
            devlist['method'] = 'devices'
            devlist['pageNo'] = '1'
            devlist['pageSize'] ='50'
            return devlist
        elif type_ ==  'devicedetail':
            devdetail = dict(**bodybase, **bodyauth, **bodydetails)
            return devdetail
        elif type_ == 'devicestatus':
            devstatus = dict(**bodybase, **bodyauth)
            return devstatus

    def login(self):
        """Return True if log in request succeeds"""

        try:
            jd = {'email': self.username, 'password': hashlib.md5(self.password.encode('utf-8')).hexdigest()}
            body = self.get_body('login')
            body.update(jd)
        except ValueError:
            logger.error("Unable to read username and password")

            return False
        else:
            response, _ = self.call_api('/cloud/v1/user/login', 'post', json=body)

            if response and self.check_response(response, 'login'):
                self.tk = response['result']['token']
                self.account_id = response['result']['accountID']
                self.enabled = True

                return True

            return False

    def update(self):
        """Fetch updated information about devices"""

        if self.last_update_ts == None or (time.time() - self.last_update_ts) > self.update_interval:

            if not self.in_process:
                updated_device_list = self.get_devices()

                [device.update() for device in updated_device_list]

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

    def check_response(resp, call):
        stand_resp = ['get_devices', 'login', '15a_detail', '15a_toggle', 
                     '15a_energy', 'walls_detail', 'walls_toggle', 
                     '10a_detail', '10a_toggle', '10a_energy', '15a_ntlight'
                     ]
        if call in stand_resp:
            if resp['code'] == 0
                return True
            else:
                return False
        elif call == '7a_detail':
            if 'deviceStatus' in resp:
                return True
            else:
                return False
        elif call == '7a_energy':
            if 'energyConsumptionOfToday' in resp:
                return True
            else:
                return False
        



class VeSyncSwitch(object):
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

        self.details = {}
        self.energy = {}

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

    def set_config(self, device):
        self.device_name = device.device_name
        self.device_image = device.device_image
        self.device_status = device.device_status
        self.connection_status = device.connection_status
        self.connection_type = device.connection_type
        self.device_type = device.device_type
        self.type = device.type
        self.uuid = device.uuid
        self.config_module = device.config_module
        self.current_firm_version = device.current_firm_version
        self.mode = device.mode
        self.speed = device.speed

        self.details = device.details
        self.energy = device.energy

    @abstractmethod
    def update(self):
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
        return self.details.get('power')

    @abstractmethod
    def voltage(self):
        """Return current voltage"""
        return self.details.get('voltage')

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


class VeSyncSwitch7A(VeSyncSwitch):
    def __init__(self, details, manager):
        super(VeSyncSwitch7A, self).__init__(details, manager)

    def get_details(self):
        response, _ = self.manager.call_api('/v1/device/' + self.cid + '/detail', 'get', headers=self.manager.get_headers())

        if response is not None and self.manager.check_response(response, '7a_details'):
            self.device_status = response['deviceStatus']
            self.details['active_time'] = response['activeTime']
            self.details['energy'] = response['energy']
            self.details['power'] = response['power']
            self.details['voltage'] = response['voltage']
        else:
            logger.error('Unable to get {0} details'.format(self.device_name))

    def get_weekly_energy(self):
        response, _ = self.manager.call_api('/v1/device/' + self.cid + '/energy/week', 'get', headers=self.manager.get_headers())
        if response and self.manager.check_response(response, '7a_energy'):
            self.energy['week'] = self.manager.get_energy_dict_from_api(response)
        else:
            logger.error('Unable to get {0} weekly data'.format(self.device_name))

    def get_monthly_energy(self):
        response, _ = self.manager.call_api('/v1/device/' + self.cid + '/energy/month', 'get', headers=self.manager.get_headers())
        if response and self.manager.check_response(response, '7a_energy'):
            self.energy['month'] = self.manager.get_energy_dict_from_api(response)
        else:
            logger.error('Unable to get {0} monthly data'.format(self.device_name))

    def get_yearly_energy(self):
        response, _ = self.manager.call_api('/v1/device/' + self.cid + '/energy/year', 'get', headers=self.manager.get_headers())
        if response and self.manager.check_response(response, '7a_energy'):
            self.energy['year'] = self.manager.get_energy_dict_from_api(response)
        else:
            logger.error('Unable to get {0} yearly data'.format(self.device_name))

    def update(self):
        self.get_details()


    def update_energy(self):
        self.get_weekly_energy()
        if self.energy['weekly']: #only update monthly & yearly if weekly succeeds
            self.get_monthly_energy()
            self.get_yearly_energy()


    def turn_on(self):
        _, status_code = self.manager.call_api('/v1/wifi-switch-1.3/' + self.cid + '/status/on', 'put', headers=self.get_headers())

        if status_code is not None and status_code == 200:
            self.device_status = 'on'
            return True
        else:
            return False

    def turn_off(self):
        _, status_code = self.manager.call_api('/v1/wifi-switch-1.3/' + self.cid + '/status/off', 'put', headers=self.get_headers())

        if status_code is not None and status_code == 200:
            self.device_status = 'off'
            return True
        else:
            return False

    def power(self):
        if self.details.get('power'):
            return round(float(self.calculate_hex(self.details.get('power'))), 2)
        else:
            return None

    def voltage(self):
        if self.details.get('voltage'):
            return round(float(self.calculate_hex(self.details.get('voltage'))), 2)
        else:
            return None

    def calculate_hex(self, hex_string):
        """Credit for conversion to itsnotlupus/vesync_wsproxy"""
        hex_conv = hex_string.split(':')
        converted_hex = (int(hex_conv[0],16) + int(hex_conv[1],16))/8192

        return converted_hex


class VeSyncSwitch15A(VeSyncSwitch):
    def __init__(self, details, manager):
        super(VeSyncSwitch15A, self).__init__(details, manager)

    def get_body(self, type_):
        if type_ == 'details':
            body = self.manager.get_body('devicedetail')
        if type_ == 'status':
            body = self.manager.get_body('devicestatus')
        body['uuid'] = self.uuid
        return body

    def get_details(self):
        body = self.get_body('details')
        body['method'] = 'devicedetail'
        body['mobileId'] = str(MOBILE_ID)
        response, _ = self.manager.call_api('/15a/v1/device/devicedetail', 'post', headers=self.manager.get_headers(), json=body)
        attr_list = ('deviceStatus', 'activeTime', 'energy', 'power', 'voltage', 'nightLightStatus', 'nightLightAutomode', 'nightLightBrightness')
        if self.manager.check_response(response, '15a_detail') and all(k in response for k in attr_list):
            self.device_status = response['deviceStatus']
            self.details['active_time'] = response['activeTime']
            self.details['energy'] = response['energy']
            self.details['night_light_status'] = response['nightLightStatus']
            self.details['night_light_brightness'] = response['nightLightBrightness']
            self.details['night_light_automode'] = response['nightLightAutomode']
            self.details['power'] = response['power']
            self.details['voltage'] = response['voltage']
        else:
            logger.error('Unable to get {0} details'.format(self.device_name))

    def get_weekly_energy(self):
        body = self.get_body('details')
        body['method'] = 'energyweek'

        response, _ = self.manager.call_api('/15a/v1/device/energyweek', 'post', headers=self.manager.get_headers(), json=body)
        if self.manager.check_response(response, '15a_energy'):
            self.energy['week'] = self.manager.get_energy_dict_from_api(response)
        else:
            logger.error('Unable to get {0} weekly data'.format(self.device_name))
            return

    def get_monthly_energy(self):
        body = self.get_body('details')
        body['method'] = 'energymonth'
        response, _ = self.manager.call_api('/15a/v1/device/energymonth', 'post', headers=self.manager.get_headers(), json=body)
        if self.manager.check_response(response, '15a_energy'):
            self.energy['month'] = self.manager.get_energy_dict_from_api(response)
        else:
            logger.error('Unable to get {0} monthly data'.format(self.device_name))

    def get_yearly_energy(self):
        body = self.get_body('details')
        body['method'] = 'energyyear'
        response, _ = self.manager.call_api('/15a/v1/device/energyyear', 'post', headers=self.manager.get_headers(), json=body)
        if self.manager.check_response(response, '15a_energy'):
            self.energy['year'] = self.manager.get_energy_dict_from_api(response)
        else:
            logger.error('Unable to get {0} yearly data'.format(self.device_name))


    def update(self):
        self.get_details()

    def update_energy(self):
        self.get_weekly_energy()
        if 'weekly' in self.energy:
            self.get_monthly_energy()
            self.get_yearly_energy()


    def turn_on(self):
        body = self.get_body('status')
        body['status'] = 'on'

        response, _ = self.manager.call_api('/15a/v1/device/devicestatus', 'put', headers=self.manager.get_headers(), json=body)

        if self.manager.check_response(response, '15a_toggle'):
            self.device_status = 'on'
            return True
        else:
            return False

    def turn_off(self):
        body = self.get_body('status')
        body['status'] = 'off'

        response, _ = self.manager.call_api('/15a/v1/device/devicestatus', 'put', headers=self.manager.get_headers(), json=body)

        if self.manager.check_response(response, '15a_toggle'):
            self.device_status = 'off'
            return True
        else:
            return False

    def turn_on_nightlight(self):
        body = self.get_body('status')
        body['mode'] = 'auto'

        response, _ = self.manager.call_api('/15a/v1/device/nightlightstatus', 'put', headers=self.manager.get_headers(), json=body)

        return self.manager.check_response(response, '15a_ntlight')

    def turn_off_nightlight(self):
        body = self.get_body('status')
        body['mode'] = 'manual'

        response, _ = self.manager.call_api('/15a/v1/device/nightlightstatus', 'put', headers=self.manager.get_headers(), json=body)

        return self.manager.check_response(response, '15a_ntlight')


class VeSyncSwitchInWall(VeSyncSwitch):
    def __init__(self, details, manager):
        super(VeSyncSwitchInWall, self).__init__(details, manager)

    def get_details(self):
        body = self.manager.get_body('devicedetail')
        body['uuid'] = self.uuid
        body['mobileID'] = MOBILE_ID

        response, _ = self.manager.call_api('/inwallswitch/v1/device/devicedetail', 'post', headers=self.manager.get_headers(), json=body)

        if self.manager.check_response(response, 'walls_detail'):
            self.device_status = response['deviceStatus']
            self.details['active_time'] = response['activeTime']
            self.details['connection_status'] = response['connectionStatus']
            self.details['power'] = response['power']
            self.details['voltage'] = response['voltage']
        else:
            logger.error('Unable to get {0} details'.format(self.device_name))

    def update(self):
        self.get_details()

    def turn_on(self):
        body = self.manager.get_body('devicestatus')
        body['status'] = 'on'
        body['uuid'] = self.uuid

        response, _ = self.manager.call_api('/inwallswitch/v1/device/devicestatus', 'put', headers=self.manager.get_headers(), json=body)

        if self.manager.check_response(response, 'walls_toggle'):
            self.device_status = 'on'
            return True
        else:
            return False

    def turn_off(self):
        body = self.manager.get_body('devicestatus')
        body['status'] = 'off'
        body['uuid'] = self.uuid

        response, _ = self.manager.call_api('/inwallswitch/v1/device/devicestatus', 'put', headers=self.manager.get_headers(), json=body)

        if self.manager.check_response(response, 'walls_toggle'):
            self.device_status = 'off'
            return True
        else:
            return False


class VeSyncSwitchEU10A(VeSyncSwitch):
    def __init__(self, details, manager):
        super(VeSyncSwitchEU10A, self).__init__(details, manager)

    def get_body(self, type_):
        if type_ == 'detail':
            body = self.manager.get_body('devicestatus')
        elif type_ == 'status':
            body = self.manager.get_body('status')
        body['uuid'] = self.uuid
        return body

    def get_details(self):
        body = self.get_body('detail')
        body['mobileID'] = str(MOBILE_ID)
        body['method'] = 'devicedetail'

        response, _ = self.manager.call_api('/10a/v1/device/devicedetail', 'post', headers=self.manager.get_headers(), json=body)

        if self.manager.check_response(response, '10a_detail'):
            self.device_status = response['deviceStatus']
            self.details['active_time'] = response['activeTime']
            self.details['energy'] = response['energy']
            self.details['night_light_status'] = response['nightLightStatus']
            self.details['night_light_brightness'] = response['nightLightBrightness']
            self.details['night_light_automode'] = response['nightLightAutomode']
            self.details['power'] = response['power']
            self.details['voltage'] = response['voltage']
        else:
            logger.error('Unable to get {0} details'.format(self.device_name))

    def get_weekly_energy(self):
        body = self.get_body('detail')
        body['method'] = 'energyweek'

        response, _ = self.manager.call_api('/10a/v1/device/energyweek', 'post', headers=self.manager.get_headers(), json=body)
        if self.manager.check_response(response, '10a_energy'):
            self.energy['week'] = self.manager.get_energy_dict_from_api(response)
        else:
            logger.error('Unable to get {0} weekly data'.format(self.device_name))

    def get_monthly_energy(self):
        body = self.get_body('detail')
        body['method'] = 'energymonth'


        response, _ = self.manager.call_api('/10a/v1/device/energymonth', 'post', headers=self.manager.get_headers(), json=body)
        if self.manager.check_response(repsonse, '10a_energy'):
            self.energy['month'] = self.manager.get_energy_dict_from_api(response)
        else:
            logger.error('Unable to get {0} monthly data'.format(self.device_name))

    def get_yearly_energy(self):
        body = self.get_body('detail')
        body['method'] = 'energyyear'

        response, _ = self.manager.call_api('/10a/v1/device/energyyear', 'post', headers=self.manager.get_headers(), json=body)
        if self.manager.check_response(response, '10a_energy'):
            self.energy['year'] = self.manager.get_energy_dict_from_api(response)
        else:
            logger.error('Unable to get {0} yearly data'.format(self.device_name))

    def update(self):
        self.get_details()

    def update_energy(self):
        self.get_weekly_energy()
        if 'weekly' in self.energy:
            self.get_monthly_energy()
            self.get_yearly_energy()

    def turn_on(self):
        body = self.get_body('status')
        body['status'] = 'on'

        response, _ = self.manager.call_api('/10a/v1/device/devicestatus', 'put', headers=self.manager.get_headers(), json=body)

        if self.manager.check_response(response, '10a_toggle'):
            self.device_status = 'on'
            return True
        else:
            return False

    def turn_off(self):
        body = self.get_body('status')
        body['status'] = 'off'

        response, _ = self.manager.call_api('/10a/v1/device/devicestatus', 'put', headers=self.manager.get_headers(), json=body)

        if self.manager.check_response(response, '10a_toggle'):
            self.device_status = 'off'
            return True
        else:
            return False
