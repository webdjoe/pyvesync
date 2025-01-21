"""Etekcity Outlets."""

import logging
import time
import json
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from pyvesync.helpers import Helpers
from pyvesync.vesyncbasedevice import VeSyncBaseDevice

logger = logging.getLogger(__name__)

outlet_config = {
    'wifi-switch-1.3': {
        'module': 'VeSyncOutlet7A'},
    'ESW03-USA': {
        'module': 'VeSyncOutlet10A'},
    'ESW01-EU': {
        'module': 'VeSyncOutlet10A'},
    'ESW15-USA': {
        'module': 'VeSyncOutlet15A'},
    'ESO15-TB': {
        'module': 'VeSyncOutdoorPlug'},
    'BSDOG01': {
        'module': 'VeSyncOutletBSDGO1'},
    'WYSMTOD16A': { # GreenSun outdoor Plug IP44 16A & Power-Metering
        'module': 'VeSyncOutletWYSMTOD16A'},
}

outlet_modules = {k: v['module'] for k, v in outlet_config.items()}

__all__ = list(outlet_modules.values()) + ['outlet_modules']


class VeSyncOutlet(VeSyncBaseDevice):
    """Base class for Etekcity Outlets."""

    __metaclass__ = ABCMeta

    def __init__(self, details, manager):
        """Initilize VeSync Outlet base class."""
        super().__init__(details, manager)

        self.details = {}
        self.energy = {}
        self.update_energy_ts = None
        self._energy_update_interval = manager.energy_update_interval

    @property
    def update_time_check(self) -> bool:
        """Test if energy update interval has been exceeded."""
        if self.update_energy_ts is None:
            return True

        if ((time.time() - self.update_energy_ts)
                > self._energy_update_interval):
            return True
        return False

    @abstractmethod
    def get_details(self) -> bool:
        """Build details dictionary."""

    @abstractmethod
    def get_weekly_energy(self) -> dict:
        """Build weekly energy history dictionary."""

    @abstractmethod
    def get_monthly_energy(self) -> dict:
        """Build Monthly Energy History Dictionary."""

    @abstractmethod
    def get_yearly_energy(self) -> dict:
        """Build Yearly Energy Dictionary."""

    @abstractmethod
    def get_config(self) -> dict:
        """Get configuration and firmware details."""

    def update(self) -> bool:
        """Get Device Energy and Status."""
        return self.get_details()

    def update_energy(self, bypass_check: bool = False) -> None:
        """Build weekly, monthly and yearly dictionaries."""
        if bypass_check or (not bypass_check and self.update_time_check):
            self.update_energy_ts = time.time()
            self.get_weekly_energy()
            if 'week' in self.energy:
                self.get_monthly_energy()
                self.get_yearly_energy()
            if not bypass_check:
                self.update_energy_ts = time.time()

    @property
    def active_time(self) -> int:
        """Return active time of a device in minutes."""
        return self.details.get('active_time', 0)

    @property
    def energy_today(self) -> float:
        """Return energy."""
        return self.details.get('energy', 0)

    @property
    def power(self) -> float:
        """Return current power in watts."""
        return float(self.details.get('power', 0))

    @property
    def voltage(self) -> float:
        """Return current voltage."""
        return float(self.details.get('voltage', 0))

    def current(self) -> float:
        i = float(self.details.get('current', 0))
        if (i == 0):
            if (self.voltage != 0):
                return self.power / self.voltage
        return i

    @property
    def monthly_energy_total(self) -> float:
        """Return total energy usage over the month."""
        return self.energy.get('month', {}).get('total_energy', 0)

    @property
    def weekly_energy_total(self) -> float:
        """Return total energy usage over the week."""
        return self.energy.get('week', {}).get('total_energy', 0)

    @property
    def yearly_energy_total(self) -> float:
        """Return total energy usage over the year."""
        return self.energy.get('year', {}).get('total_energy', 0)

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp = [
            ('Active Time : ', self.active_time, ' minutes'),
            ('Energy: ', self.energy_today, ' kWh'),
            ('Power: ', self.power, ' Watts'),
            ('Voltage: ', self.voltage, ' Volts'),
            ('Current: ', self.current, ' Volts'),
            ('Energy Week: ', self.weekly_energy_total, ' kWh'),
            ('Energy Month: ', self.monthly_energy_total, ' kWh'),
            ('Energy Year: ', self.yearly_energy_total, ' kWh'),
        ]
        for line in disp:
            print(f'{line[0]:.<30} {line[1]} {line[2]}')

    def displayJSON(self) -> None:
        """Return JSON details for outlet."""
        sup = super().displayJSON()
        sup_val = json.loads(sup)
        sup_val.update(
            {
                'Active Time': str(self.active_time),
                'Energy': str(self.energy_today),
                'Power': str(self.power),
                'Voltage': str(self.voltage),
                'Current': str(self.current),
                'Energy Week': str(self.weekly_energy_total),
                'Energy Month': str(self.monthly_energy_total),
                'Energy Year': str(self.yearly_energy_total),
            }
        )

        return json.dumps(sup_val, indent=4)

    @abstractmethod
    def turn(self, status) -> bool:
        """Get configuration and firmware details."""

    def turn_on(self) -> bool:
        """Turn outdoor outlet on and return True if successful."""
        return self.turn('on')

    def turn_off(self) -> bool:
        """Turn outdoor outlet off and return True if successful."""
        return self.turn('off')

    def get_body_v2(self) -> dict:
        body = Helpers.req_body(self.manager, ('bypassV2'))
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        return body


class VeSyncOutlet7A(VeSyncOutlet):
    """Etekcity 7A Round Outlet Class."""

    def __init__(self, details, manager):
        """Initilize Etekcity 7A round outlet class."""
        super().__init__(details, manager)
        self.det_keys = ['deviceStatus', 'activeTime', 'energy', 'power', 'voltage']
        self.energy_keys = ['energyConsumptionOfToday', 'maxEnergy', 'totalEnergy']

    def get_details(self) -> bool:
        """Get 7A outlet details."""
        r, _ = Helpers.call_api(
            f'/v1/device/{self.cid}/detail',
            'get',
            headers=Helpers.req_headers(self.manager),
        )

        if r is not None and all(x in r for x in self.det_keys):
            self.device_status = r.get('deviceStatus', self.device_status)
            self.details['active_time'] = r.get('activeTime', 0)
            self.details['energy'] = r.get('energy', 0)
            power = r.get('power', '0')
            self.details['power'] = self.parse_energy_detail(power)
            voltage = r.get('voltage', 0)
            self.details['voltage'] = self.parse_energy_detail(voltage)
            return True

        logger.error('Unable to get %s details', self.device_name)
        return False

    @staticmethod
    def parse_energy_detail(energy):
        """Parse energy details to be compatible with new and old firmware."""
        try:
            if isinstance(energy, str) and ':' in energy:
                power = round(float(Helpers.calculate_hex(energy)), 2)
            else:
                power = float(energy)
        except ValueError:
            logger.debug('Error parsing power response - %s', energy)
            power = 0
        return power

    def get_energy(self, period) -> dict:
        """Get 7A outlet energy for period info and buld weekly energy dict."""
        r, _ = Helpers.call_api(
            f'/v1/device/{self.cid}/energy/{period}',
            'get',
            headers=Helpers.req_headers(self.manager),
        )

        if r is not None and all(x in r for x in self.energy_keys):
            self.energy[period] = Helpers.build_energy_dict(r)
        else:
            self.energy[period] = None
            logger.error(f'Unable to get {self.device_name} {period}ly data!')
        return self.energy[period]

    def get_weekly_energy(self) -> dict:
        """Get 7A outlet weekly energy info and buld weekly energy dict."""
        return self.get_energy('week')

    def get_monthly_energy(self) -> dict:
        """Get 7A outlet monthly energy info and buld monthly energy dict."""
        return self.get_energy('month')

    def get_yearly_energy(self) -> dict:
        """Get 7A outlet yearly energy info and build yearly energy dict."""
        return self.get_energy('year')

    def turn(self, status) -> bool:
        _, status_code = Helpers.call_api(
            f'/v1/wifi-switch-1.3/{self.cid}/status/{status}',
            'put',
            headers=Helpers.req_headers(self.manager),
        )

        if status_code is not None and status_code == 200:
            self.device_status = status
            return True

        logger.error(f'Error turning {self.device_name} {status}!')
        return False


    def get_config(self) -> dict:
        """Get 7A outlet configuration info."""
        r, _ = Helpers.call_api(
            f'/v1/device/{self.cid}/configurations',
            'get',
            headers=Helpers.req_headers(self.manager),
        )

        if 'currentFirmVersion' in r:
            self.config = Helpers.build_config_dict(r)
        else:
            self.config = {}
            logger.error(f'Error getting configuration info for {self.device_name}!')
        return self.config


class VeSyncOutlet10A(VeSyncOutlet):
    """Etekcity 10A Round Outlets."""

    def __init__(self, details, manager):
        """Initialize 10A outlet class."""
        super().__init__(details, manager)

    def get_details(self) -> bool:
        """Get 10A outlet details."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid

        r, _ = Helpers.call_api(
            '/10a/v1/device/devicedetail',
            'post',
            body,
            Helpers.req_headers(self.manager),
        )

        if Helpers.code_check(r):
            self.device_status = r.get('deviceStatus', self.device_status)
            self.connection_status = r.get('connectionStatus', self.connection_status)
            self.details = Helpers.build_details_dict(r)
            return True
        
        logger.debug(f'Unable to get {self.device_name} details')
        return False

    def get_config(self) -> dict:
        """Get 10A outlet configuration info."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = Helpers.call_api(
            '/10a/v1/device/configurations',
            'post',
            body,
            Helpers.req_headers(self.manager),
        )

        if Helpers.code_check(r):
            self.config = Helpers.build_config_dict(r)
        else:
            self.config = {}
            logger.debug(f'Error getting {self.device_name} config info!')
        return self.config

    def get_energy(self, period) -> dict:
        """Get 10A outlet energy for period info and populate energy dict."""
        body = Helpers.req_body(self.manager, 'energy_week')
        body['uuid'] = self.uuid

        response, _ = Helpers.call_api(
            f'/10a/v1/device/energy{period}',
            'post',
            body,
            Helpers.req_headers(self.manager),
        )

        if Helpers.code_check(response):
            self.energy[period] = Helpers.build_energy_dict(response)
        else:
            self.energy[period] = {}
            logger.debug(f'Unable to get {self.device_name} {period}ly data')
            return self.energy[period]

    def get_weekly_energy(self) -> dict:
        """Get 10A outlet weekly energy info and populate energy dict."""
        return self.get_energy('week')

    def get_monthly_energy(self) -> dict:
        """Get 10A outlet monthly energy info and populate energy dict."""
        return self.get_energy('month')

    def get_yearly_energy(self) -> dict:
        """Get 10A outlet yearly energy info and populate energy dict."""
        return self.get_energy('year')

    def turn(self, status) -> bool:
        """Turn 10A outlet off - return True if successful."""
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = status

        response, _ = Helpers.call_api(
            '/10a/v1/device/devicestatus',
            'put',
            body,
            Helpers.req_headers(self.manager),
        )

        if Helpers.code_check(response):
            self.device_status = status
            return True
        logger.warning(f'Error turning {self.device_name} {status}!')
        return False


class VeSyncOutlet15A(VeSyncOutlet):
    """Class for Etekcity 15A Rectangular Outlets."""

    def __init__(self, details, manager):
        """Initialize 15A rectangular outlets."""
        super().__init__(details, manager)
        self.nightlight_status = 'off'
        self.nightlight_brightness = 0

    def get_details(self) -> bool:
        """Get 15A outlet details."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid

        r, _ = Helpers.call_api(
            '/15a/v1/device/devicedetail',
            'post',
            body,
            Helpers.req_headers(self.manager),
        )

        attr_list = (
            'deviceStatus',
            'activeTime',
            'energy',
            'power',
            'voltage',
            'nightLightStatus',
            'nightLightAutomode',
            'nightLightBrightness',
        )

        if Helpers.code_check(r) and all(k in r for k in attr_list):

            self.device_status = r.get('deviceStatus')
            self.connection_status = r.get('connectionStatus')
            self.nightlight_status = r.get('nightLightStatus')
            self.nightlight_brightness = r.get('nightLightBrightness')
            self.details = Helpers.build_details_dict(r)
            return True

        logger.error('Unable to get %s details', self.device_name)
        return False

    def get_config(self) -> dict:
        """Get 15A outlet configuration info."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = Helpers.call_api(
            '/15a/v1/device/configurations',
            'post',
            body,
            Helpers.req_headers(self.manager),
        )

        if Helpers.code_check(r):
            self.config = Helpers.build_config_dict(r)
        else:
            self.config = {}
            logger.debug(f'Unable to get {self.device_name} config info!')
        return self.config

    def get_energy(self, period) -> dict:
        """Get 15A outlet energy for period info and populate energy dict."""
        body = Helpers.req_body(self.manager, f'energy_{period}')
        body['uuid'] = self.uuid

        response, _ = Helpers.call_api(
            f'/15a/v1/device/energy{period}',
            'post',
            body,
            Helpers.req_headers(self.manager),
        )

        if Helpers.code_check(response):
            self.energy[period] = Helpers.build_energy_dict(response)
        else:
            self.energy[period] = {}
            logger.error('Unable to get %s {period}ly data', self.device_name)
        return self.energy[period]

    def get_weekly_energy(self) -> dict:
        """Get 15A outlet weekly energy info and populate energy dict."""
        return self.get_energy('week')

    def get_monthly_energy(self) -> dict:
        """Get 15A outlet monthly energy info and populate energy dict."""
        return self.get_energy('month')

    def get_yearly_energy(self) -> dict:
        """Get 15A outlet yearly energy info and populate energy dict."""
        return self.get_energy('year')

    def turn(self, status) -> bool:
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = status

        response, _ = Helpers.call_api(
            '/15a/v1/device/devicestatus',
            'put',
            body,
            Helpers.req_headers(self.manager),
        )

        if Helpers.code_check(response):
            self.device_status = status
            return True
        logger.warning(f'Error turning {self.device_name} {status}!')
        return False

    def toggle_nightlight(self, mode) -> bool:
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['mode'] = mode
        response, _ = Helpers.call_api(
            '/15a/v1/device/nightlightstatus',
            'put',
            body,
            Helpers.req_headers(self.manager),
        )

        if Helpers.code_check(response):
            return True
        logger.warning(f'Error turning {self.device_name} to {mode} nightlight!')
        return False

    def turn_on_nightlight(self) -> bool:
        """Turn on nightlight."""
        return self.toggle_nightlight('auto')


    def turn_off_nightlight(self) -> bool:
        """Turn Off Nightlight."""
        return self.toggle_nightlight('manual')


class VeSyncOutdoorPlug(VeSyncOutlet):
    """Class to hold Etekcity outdoor outlets."""

    def __init__(self, details, manager):
        """Initialize Etekcity Outdoor Plug class."""
        super().__init__(details, manager)

    def get_details(self) -> bool:
        """Get details for outdoor outlet."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        r, _ = Helpers.call_api(
            '/outdoorsocket15a/v1/device/devicedetail',
            'post',
            body,
            Helpers.req_headers(self.manager),
        )

        if Helpers.code_check(r):
            self.details = Helpers.build_details_dict(r)
            self.connection_status = r.get('connectionStatus')

            dev_no = self.sub_device_no
            sub_device_list = r.get('subDevices')
            if sub_device_list and dev_no <= len(sub_device_list):
                self.device_status = sub_device_list[(dev_no + -1)].get('subDeviceStatus')
                return True
        logger.debug(f'Unable to get {self.device_name} details!')
        return False

    def get_config(self) -> dict:
        """Get configuration info for outdoor outlet."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = Helpers.call_api(
            '/outdoorsocket15a/v1/device/configurations',
            'post',
            body,
            Helpers.req_headers(self.manager),
        )

        if Helpers.code_check(r):
            self.config = Helpers.build_config_dict(r)
        else:
            self.config = {}
            logger.error(f'Error getting {self.device_name} config info!')
        return self.config

    def get_energy(self, period):
        body = Helpers.req_body(self.manager, f'energy_{period}')
        body['uuid'] = self.uuid

        response, _ = Helpers.call_api(
            f'/outdoorsocket15a/v1/device/energy{period}',
            'post',
            body,
            Helpers.req_headers(self.manager),
        )

        if Helpers.code_check(response):
            self.energy[period] = Helpers.build_energy_dict(response)
        else:
            self.energy[period] = {}
            logger.error(f'Unable to get {self.device_name} {period}ly data!')
        return self.energy[period]

    def get_weekly_energy(self) -> dict:
        """Get outdoor outlet weekly energy info and populate energy dict."""
        return self.get_energy('week')

    def get_monthly_energy(self) -> dict:
        """Get outdoor outlet monthly energy info and populate energy dict."""
        return self.get_energy('month')

    def get_yearly_energy(self) -> dict:
        """Get outdoor outlet yearly energy info and populate energy dict."""
        return self.get_energy('year')

    def turn(self, status) -> bool:
        """Toggle power for outdoor outlet."""
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = status
        body['switchNo'] = self.sub_device_no

        response, _ = Helpers.call_api(
            '/outdoorsocket15a/v1/device/devicestatus',
            'put',
            body,
            Helpers.req_headers(self.manager),
        )

        if Helpers.code_check(response):
            self.device_status = status
            return True
        logger.warning(f'Error turning {self.device_name} {status}')
        return False


class VeSyncOutletBSDGO1(VeSyncOutlet):
    """VeSync BSDGO1 smart plug."""

    def __init__(self, details, manager):
        """Initialize BSDGO1 smart plug class."""
        super().__init__(details, manager)

    def get_details(self) -> bool:
        """Get BSDGO1 device details."""
        body = self.get_body_v2()
        body['payload'] = {
            'method': 'getProperty',
            'source': 'APP',
            'data': {}
        }

        data, error = self._get_response(body)
        if data:
            self.device_status = 'on' if data.get('powerSwitch_1') == 1 else 'off'
            return True
        return False

    def turn(self, status) -> bool:
        """Set power state of BSDGO1 outlet."""
        body = self.get_body_v2()
        body['payload'] = {
            'data': {'powerSwitch_1': 1 if status=='on' else 0},
            'method': 'setProperty',
            'source': 'APP'
        }

        data, error = self._get_response(body)

        if error is None:
            self.device_status = status
            return True
        logger.warning(f'Error turning {self.device_name} {status}')
        return False


class VeSyncOutletWYSMTOD16A(VeSyncOutlet):
    """Class to hold GreenSun outdoor outlets."""
    PROPERTIES = (
        'powerSwitch_1',         # int
        'realTimeCurrent',       # double
        'realTimeVoltage',       # double
        'realTimePower',         # double
        'electricalEnergy',      # double
        'protectionStatus',      # string
        'voltageUpperThreshold', # double
        'currentUpperThreshold', # double
        'powerUpperThreshold',   # double
        'scheduleNum',           # int
        'powerSave',             # dict {'enable' -> int, 'triggerUpperThreshold': double}
        'powerProtection',       # dict {'enable' -> int, 'triggerType' -> string, 'upperThreshold' -> double}
        'inchings',              # list
        'aways',                 # list
    )
    def __init__(self, details, manager):
        """Initialize GreenSun's WYSMTOD16A plug class."""
        super().__init__(details, manager)

    def _get_response(self, body, rel_path = '/cloud/v2/deviceManaged/bypassV2') -> dict:
        response, _ = Helpers.call_api(
            rel_path,
            'post',
            body,
            Helpers.req_headers(self.manager),
        )
        if Helpers.code_check(response):
            code = response['result']
            if (code['code'] == 0):
                return code.get('result', {}), None
            logger.error(f'Calling {self.device_name}::{body["payload"]["method"]} - wrong argument')
            return None, (code['code'], 'wrong argument')

        err_code = response['code']
        err_msg  = response['msg']
        if (err_code != -11300030):
            logger.error(f'Calling {self.device_name}::{body["payload"]["method"]} - E_{(err_code & 0xFFFFFFFF):08X}: {err_msg}')
        return None, (err_code, err_msg)

    def get_details(self) -> bool:
        """Get details for this plug."""
        properties =['powerSwitch_1', 'realTimeVoltage', 'realTimePower', 'realTimeCurrent']
        data = self.get_properties(properties)

        if (data):
            self.device_status = 'on' if data.get('powerSwitch_1', False) else 'off'
            self.details['voltage'] = data.get('realTimeVoltage', 0)
            self.details['power']   = data.get('realTimePower', 0)
            self.details['current'] = data.get('realTimeCurrent', 0)
            return True
        self.device_status = 'offline'
        return False

    def get_energy(self, days):
        till_day = datetime.today()
        from_day = till_day - timedelta(days=days)
        body = self.get_body_v2()
        body['payload'] = {
            'method': 'getEnergyHistory',
            'source': 'APP',
            'data': {
                'fromDay': int(from_day.timestamp()),
                'toDay'  : int(till_day.timestamp()),
#                'id'       : 0,
            }
        }
        data, error = self._get_response(body)

        PERIODS = {7: 'week', 30: 'month', 365: 'year'}
        period = PERIODS.get(days, days)
        self.energy[period] = {}
        if (data):
            self.energy[period] = Helpers.build_energy_dict(data)
        return self.energy[period]

    def get_weekly_energy(self) -> dict:
        """Get outdoor outlet weekly energy info and populate energy dict."""
        return self.get_energy(7)

    def get_monthly_energy(self) -> dict:
        """Get outdoor outlet monthly energy info and populate energy dict."""
        return self.get_energy(30)

    def get_yearly_energy(self) -> dict:
        """Get outdoor outlet yearly energy info and populate energy dict."""
        return self.get_energy(365)

    def turn(self, status) -> bool:
        """switch power for outdoor outlet."""
        body = self.get_body_v2()
        body['payload'] = {
            'method': 'setSwitch',
            'source': 'APP',
            'data': {
                'enabled': True if (status=='on') else False,
                'id': 0,
            },
        }

        data, error = self._get_response(body)
        if (data):
            self.device_status = status
            return True
        return False

    def get_properties(self, properties):
        """ Returns the value of one of the properties """
        body = self.get_body_v2()
        body['payload'] = {
            'method': 'getProperty',
            'source': 'APP',
            'data': { 'properties': properties },
        }
        data, error = self._get_response(body)
        if (data):
            return data
        return None
