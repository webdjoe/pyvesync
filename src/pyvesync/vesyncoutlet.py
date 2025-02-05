"""Etekcity Outlets."""

import logging
import time
import json
import sys
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from .helpers import (
    Helpers, EDeviceFamily, 
    ENERGY_WEEK, ENERGY_MONTH, ENERGY_YEAR, PERIOD_2_DAYS,
    ERR_REQ_TIMEOUTS
)
from .vesyncbasedevice import VeSyncBaseDevice, STATUS_ON, STATUS_OFF, MODE_AUTO, MODE_MANUAL

logger = logging.getLogger(__name__)

module_outlet = sys.modules[__name__]

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
#    'WHOGPLUG': {
#        'module': 'VeSyncOutletWHOGPLUG'},
    'WYSMTOD16A': { # GreenSun outdoor Plug IP44 16A & Power-Metering
        'module': 'VeSyncOutletWYSMTOD16A'},
}

outlet_modules = {k: v['module'] for k, v in outlet_config.items()}

__all__ = list(outlet_modules.values()) + ['outlet_modules']

class   VeSyncOutlet(VeSyncBaseDevice):
    """Base class for Etekcity Outlets."""

    energy: dict = {}
    update_energy_ts: float = 0
    _energy_update_interval: float = 0
    energy_period: bool = True
    device_family = EDeviceFamily.OUTLET

    __metaclass__ = ABCMeta

    def __init__(self, details, manager, energy_period = True):
        """Initialize VeSync Outlet base class."""
        super().__init__(details, manager, EDeviceFamily.OUTLET)
        self.energy = {}
        self.update_energy_ts = None
        self._energy_update_interval = manager.energy_update_interval
        self.energy_period = energy_period

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
    def get_energy(self, period) -> dict:
        """Build energy history dictionary."""

    def get_weekly_energy(self) -> dict:
        """Build weekly energy history dictionary."""
        return self.get_energy(ENERGY_WEEK)

    def get_monthly_energy(self) -> dict:
        """Build Monthly Energy History Dictionary."""
        return self.get_energy(ENERGY_MONTH)

    def get_yearly_energy(self) -> dict:
        """Build Yearly Energy Dictionary."""
        return self.get_energy(ENERGY_YEAR)

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
            if not self.get_weekly_energy() is None:
                self.get_monthly_energy()
                self.get_yearly_energy()
            else:
                self.energy[ENERGY_MONTH] = {}
                self.energy[ENERGY_YEAR] = {}
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
        P = float(self.details.get('power', 0))
        return round(P, 3)

    @property
    def voltage(self) -> float:
        """Return current voltage."""
        U = float(self.details.get('voltage', 0))
        return round(U, 1)

    @property
    def current(self) -> float:
        I = float(self.details.get('current', 0))

        if (I == 0):
            if (self.voltage != 0):
                return self.power / self.voltage
        return round(I, 2)

    @property
    def monthly_energy_total(self) -> float:
        """Return total energy usage over the month."""
        return self.energy.get(ENERGY_MONTH, {}).get('total_energy', 0)

    @property
    def weekly_energy_total(self) -> float:
        """Return total energy usage over the week."""
        return self.energy.get(ENERGY_WEEK, {}).get('total_energy', 0)

    @property
    def yearly_energy_total(self) -> float:
        """Return total energy usage over the year."""
        return self.energy.get(ENERGY_YEAR, {}).get('total_energy', 0)

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp = [
            ('Active Time', str(self.active_time), 'min'),
            ('Energy', str(self.energy_today), 'kWh'),
            ('Power', str(self.power), 'W'),
            ('Voltage', str(self.voltage), 'V'),
            ('Current', str(self.current), 'A'),
            ('Energy Week', str(self.weekly_energy_total), 'kWh'),
            ('Energy Month', str(self.monthly_energy_total), 'kWh'),
            ('Energy Year', str(self.yearly_energy_total), 'kWh'),
        ]
        for line in disp:
            print(f"{line[0]+': ':.<30} {' '.join(line[1:])}")

    def displayJSON(self) -> dict:
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

    @property
    def has_energy_period(self) -> bool:
        return self.energy_period


class VeSyncOutlet7A(VeSyncOutlet):
    """Etekcity 7A Round Outlet Class."""
    det_keys = ['deviceStatus', 'activeTime', 'energy', 'power', 'voltage']
    energy_keys = ['energyConsumptionOfToday', 'maxEnergy', 'totalEnergy']

    def __init__(self, details, manager):
        """Initialize Etekcity 7A round outlet class."""
        super().__init__(details, manager)

    def get_details(self) -> bool:
        """Get 7A outlet details."""
        r = Helpers.call_api(f'/v1/device/{self.cid}/detail',
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

        logger.error(f'Failed to get {self.device_name} details')
        return False

    @staticmethod
    def parse_energy_detail(energy) -> float:
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
        r = Helpers.call_api(f'/v1/device/{self.cid}/energy/{period}',
            'get',
            headers=Helpers.req_headers(self.manager),
        )

        if r is not None and all(x in r for x in self.energy_keys):
            self.energy[period] = Helpers.build_energy_dict(r)
        else:
            self.energy[period] = None
            logger.error(f'Unable to get {self.device_name} energy-data for {period}!')
        return self.energy[period]

    def turn(self, status) -> bool:
        """Turn 7A outlet on/off - return True if successful."""
        r = Helpers.call_api(f'/v1/wifi-switch-1.3/{self.cid}/status/{status}',
            'put',
            headers=Helpers.req_headers(self.manager),
        )

        if r is None:
            logger.error(f'Error turning {self.device_name} {status}!')
            return False
        self.device_status = status
        return True


    def get_config(self) -> dict:
        """Get 7A outlet configuration info."""
        r = Helpers.call_api(f'/v1/device/{self.cid}/configurations',
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

    def call_api(self, api, method, body):
        r = Helpers.call_api(f'/10a/v1/device/{api}',
            method=method,
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        return r

    def get_details(self) -> bool:
        """Get 10A outlet details."""
        body = Helpers.req_body_device_detail(self.manager)
        body['uuid'] = self.uuid

        r = self.call_api('devicedetail', 'post', body)

        if Helpers.code_check(r):
            self.device_status = r.get('deviceStatus', self.device_status)
            self.connection_status = r.get('connectionStatus',
                                           self.connection_status)
            self.details = Helpers.build_details_dict(r)
            return True

        logger.debug(f'Failed to get {self.device_name} details')
        return False

    def get_config(self) -> dict:
        """Get 10A outlet configuration info."""
        body = Helpers.req_body_device_detail(self.manager)
        body['uuid'] = self.uuid
        body['method'] = 'configurations'

        r = self.call_api('configurations', 'post', body)

        if Helpers.code_check(r):
            self.config = Helpers.build_config_dict(r)
        else:
            self.config = {}
            logger.debug(f'Error getting {self.device_name} config info!')
        return self.config

    def get_energy(self, period) -> dict:
        """Get 10A outlet energy for period info and populate energy dict."""
        body = Helpers.req_body_energy(self.manager, period)
        body['uuid'] = self.uuid

        r = self.call_api(f'energy{period}', 'post', body)

        if Helpers.code_check(r):
            self.energy[period] = Helpers.build_energy_dict(r)
        else:
            self.energy[period] = None
            logger.error(f'Unable to get {self.device_name} energy-data for {period}!')
        return self.energy[period]

    def turn(self, status) -> bool:
        """Turn 10A outlet on/off - return True if successful."""
        body = Helpers.req_body_status(self.manager)
        body['uuid'] = self.uuid
        body['status'] = status

        r = self.call_api('devicestatus', 'put', body)

        if Helpers.code_check(r):
            self.device_status = status
            return True
        logger.warning(f'Error turning {self.device_name} {status}!')
        return False


class VeSyncOutlet15A(VeSyncOutlet):
    """Class for Etekcity 15A Rectangular Outlets."""

    nightlight_status: str = None
    nightlight_brightness: float = 0

    def __init__(self, details, manager):
        """Initialize 15A rectangular outlets."""
        super().__init__(details, manager)
        self.nightlight_status = STATUS_OFF
        self.nightlight_brightness = 0

    def call_api(self, api, method, body):
        r = Helpers.call_api(f'/15a/v1/device/{api}',
            method=method,
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        return r
    def get_details(self) -> bool:
        """Get 15A outlet details."""
        body = Helpers.req_body_device_detail(self.manager)
        body['uuid'] = self.uuid

        r = self.call_api('devicedetail', 'post', body)

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

        logger.error(f'Failed to get {self.device_name} details')
        return False

    def get_config(self) -> dict:
        """Get 15A outlet configuration info."""
        body = Helpers.req_body_device_detail(self.manager)
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r = self.call_api('configurations', 'post', body)

        if Helpers.code_check(r):
            self.config = Helpers.build_config_dict(r)
        else:
            self.config = {}
            logger.debug(f'Unable to get {self.device_name} config info!')
        return self.config

    def get_energy(self, period) -> dict:
        """Get 15A outlet energy for period info and populate energy dict."""
        body = Helpers.req_body_energy(self.manager, period)
        body['uuid'] = self.uuid

        r = self.call_api(f'energy{period}', 'post', body)

        if Helpers.code_check(r):
            self.energy[period] = Helpers.build_energy_dict(r)
        else:
            self.energy[period] = None
            logger.error(f'Unable to get {self.device_name} energy-data for {period}!')
        return self.energy[period]

    def turn(self, status) -> bool:
        """Turn 15A outlet on/off - return True if successful."""
        body = Helpers.req_body_status(self.manager)
        body['uuid'] = self.uuid
        body['status'] = status

        r = self.call_api('devicestatus', 'put', body)

        if Helpers.code_check(r):
            self.device_status = status
            return True
        logger.warning(f'Error turning {self.device_name} {status}!')
        return False

    def turn_nightlight(self, mode) -> bool:
        body = Helpers.req_body_status(self.manager)
        body['uuid'] = self.uuid
        body['mode'] = mode
        r = self.call_api('nightlightstatus', 'put', body)

        if Helpers.code_check(r):
            return True
        logger.debug(f'Error turning {self.device_name} to {mode} nightlight!')
        return False

    def turn_on_nightlight(self) -> bool:
        """Turn on nightlight."""
        return self.turn_nightlight(MODE_AUTO)

    def turn_off_nightlight(self) -> bool:
        """Turn off Nightlight."""
        return self.turn_nightlight(MODE_MANUAL)


class VeSyncOutdoorPlug(VeSyncOutlet):
    """Class to hold Etekcity outdoor outlets."""

    def __init__(self, details, manager):
        """Initialize Etekcity Outdoor Plug class."""
        super().__init__(details, manager)

    def call_api(self, api, method, body):
        r = Helpers.call_api(f'/outdoorsocket15a/v1/device/{api}',
            method=method,
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        return r
    def get_details(self) -> bool:
        """Get details for outdoor outlet."""
        body = Helpers.req_body_device_detail(self.manager)
        body['uuid'] = self.uuid
        r = self.call_api('devicedetail', 'post', body)

        if Helpers.code_check(r):
            self.details = Helpers.build_details_dict(r)
            self.connection_status = r.get('connectionStatus')

            dev_no = self.sub_device_no
            sub_device_list = r.get('subDevices')
            if sub_device_list and dev_no <= len(sub_device_list):
                self.device_status = sub_device_list[(dev_no + -1)].get('subDeviceStatus')
                return True
        logger.debug(f'Failed to get {self.device_name} details!')
        return False

    def get_config(self) -> dict:
        """Get configuration info for outdoor outlet."""
        body = Helpers.req_body_device_detail(self.manager)
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r = self.call_api('configurations', 'post', body)

        if Helpers.code_check(r):
            self.config = Helpers.build_config_dict(r)
        else:
            self.config = {}
            logger.error(f'Error getting {self.device_name} config info!')
        return self.config

    def get_energy(self, period) -> dict:
        """Get outdoor outlet energy for period info and populate energy dict."""
        body = Helpers.req_body_energy(self.manager, period)
        body['uuid'] = self.uuid

        r = self.call_api(f'energy{period}', 'post', body)

        if Helpers.code_check(r):
            self.energy[period] = Helpers.build_energy_dict(r)
        else:
            self.energy[period] = None
            logger.error(f'Unable to get {self.device_name} energy-data for {period}!')
        return self.energy[period]

    def turn(self, status) -> bool:
        """Turn outdoor outlet on/off."""
        body = Helpers.req_body_status(self.manager)
        body['uuid'] = self.uuid
        body['status'] = status
        body['switchNo'] = self.sub_device_no

        r = self.call_api('devicestatus', 'put', body)

        if Helpers.code_check(r):
            self.device_status = status
            return True
        logger.warning(f'Error turning {self.device_name} {status}')
        return False


class VeSyncOutletV2(VeSyncOutlet):
    """VeSync bypassV2 smart plug."""

    def __init__(self, details, manager):
        """Initialize bypassV2 smart plug class."""
        super().__init__(details, manager, False)

    def get_body_v2(self) -> dict:
        body = {
            **Helpers.req_body_bypass_v2(self.manager),
            'cid': self.cid,
            'configModule': self.config_module
        }
        return body

    def get_response(self, body) -> dict:
        response = Helpers.post_device_managed_v2(body)

        if Helpers.code_check(response):
            code = response['result']
            if (code['code'] == 0):
                return code, None
            logger.error(f'Failed {self.device_name}::{body["payload"]["method"]} - wrong argument')
            return None, (code['code'], 'wrong argument')
        if response:
            err_code = response['code']
            err_msg  = response['msg']
            if (err_code not in ERR_REQ_TIMEOUTS):
                logger.error(f'Failed {self.device_name}::{body["payload"]["method"]} - {err_msg} ({err_code})')
            return None, (err_code, err_msg)
        self.connection_status = 'offline'
        return None, (-1, "offline")


class VeSyncOutletBSDGO1(VeSyncOutletV2):
    """VeSync BSDGO1 smart plug."""

    def __init__(self, details, manager):
        """Initialize bypassV2 smart plug class."""
        super().__init__(details, manager)

    def get_details(self) -> bool:
        """Get BSDGO1 device details."""
        body = self.get_body_v2()
        body['payload'] = {
            'method': 'getProperty',
            'source': 'APP',
            'data': {}
        }

        code, error = self.get_response(body)
        if (error is None):
            self.device_status = STATUS_ON if code.get('powerSwitch_1') == 1 else STATUS_OFF
            return True
        return False

    def turn(self, status: str) -> bool:
        """Set power state of BSDGO1 outlet."""
        body = self.get_body_v2()
        body['payload'] = {
            'data': {'powerSwitch_1': 1 if (status==STATUS_ON) else 0},
            'method': 'setProperty',
            'source': 'APP'
        }

        code, error = self.get_response(body)

        if error is None:
            self.device_status = status
            return True
        return False


class VeSyncOutletWHOGPLUG(VeSyncOutletV2):

    def __init__(self, details, manager):
        """Initialize bypassV2 smart plug class."""
        super().__init__(details, manager)

    def get_details(self) -> bool:
        """Get WHOGPLUG device details."""
        body = self.get_body_v2()
        body['payload'] = {
            'method': 'getProperty',
            'source': 'APP',
            'subDeviceNo': 0,
            'data': {}
        }

        code, error = self.get_response(body)
        if (error is None):
            self.device_status = STATUS_ON if code.get('poweenabled') else STATUS_OFF
            self.details['voltage'] = code.get('voltage', 0)
            self.details['current'] = code.get('current', 0)
            self.details['power'] = code.get('power', 0)
            self.details['energy'] = code.get('energy', 0)
            self.details['highestVoltage'] = code.get('highestVoltage', 0)
            self.details['voltagePtStatus'] = code.get('voltagePtStatus', False)
            return True
        return False

    def turn(self, status) -> bool:
        """Set power state of WHOGPLUG outlet."""
        body = self.get_body_v2()
        body['payload'] = {
            'method': 'setProperty',
            'source': 'APP',
            'subDeviceNo': 0,
            'data': {'powerSwitch_1': 1 if status==STATUS_ON else 0},
        }

        code, error = self.get_response(body)

        if error is None:
            self.device_status = status
            return True
        return False


class VeSyncOutletWYSMTOD16A(VeSyncOutletV2):

    def __init__(self, details, manager):
        """Initialize WHOGPLUG class."""
        super().__init__(details, manager)
        self.connection_status = 'online' # assume online -> workaround.

    """Class to hold GreenSun outdoor outlets."""
    PROPERTIES = (
        'powerSwitch_1',         # int:    device status
        'realTimeCurrent',       # double: actual current
        'realTimeVoltage',       # double: actual voltage
        'realTimePower',         # double: actual power
        'electricalEnergy',      # double: today's energy consumption
        'protectionStatus',      # string: protection status
        'currentUpperThreshold', # double
        'voltageUpperThreshold', # double
        'powerUpperThreshold',   # double
        'scheduleNum',           # int
        'powerSave',             # dict {'enable' -> int, 'triggerUpperThreshold': double}
        'powerProtection',       # dict {'enable' -> int, 'triggerType' -> string, 'upperThreshold' -> double}
        'inchings',              # list
        'aways',                 # list
    )
    UPDATE_PROPERTIES = ('powerSwitch_1', 'realTimeCurrent', 'realTimeVoltage', 'realTimePower', 'electricalEnergy')

    def get_details(self) -> bool:
        """Get details for this plug."""
        properties = self.get_properties(VeSyncOutletWYSMTOD16A.UPDATE_PROPERTIES)

        if (properties):
            self.device_status = STATUS_ON if properties.get('powerSwitch_1', False) else STATUS_OFF
            self.details['voltage'] = properties.get('realTimeVoltage', 0)
            self.details['current'] = properties.get('realTimeCurrent', 0)
            self.details['power']   = properties.get('realTimePower', 0)
            self.details['energy'] = properties.get('electricalEnergy', 0)
            self.connection_status = 'online'
            return True
        self.connection_status = 'offline'
        return False

    def get_energy(self, period) -> dict:
        today = datetime.today()
        from_day = today - timedelta(days=PERIOD_2_DAYS[period])
        till_day = today

        body = self.get_body_v2()
        body['subDeviceNo'] = 0 # required?
        body['payload'] = {
            'method': 'getEnergyHistory',
            'source': 'APP',
            'subDeviceNo': 0,
            'data': {
                'fromDay': from_day.timestamp(),
                'toDay'  : till_day.timestamp()
            }
        }
        code, error = self.get_response(body)

        if (error is None):
            self.energy[period] = Helpers.build_energy_dict(code['result'])
        else:
            self.energy[period] = None
        return self.energy[period]

    def turn(self, status) -> bool:
        """switch power for outdoor outlet."""
        body = self.get_body_v2()
        body['payload'] = {
            'method': 'setSwitch',
            'source': 'APP',
            'data': {
                'enabled': True if (status==STATUS_ON) else False,
                'id': 0,
            },
        }

        code, error = self.get_response(body)
        if (error is None):
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
        code, error = self.get_response(body)
        if (error is None):
            return code['result']
        return None


def factory(module: str, details: dict, manager) -> VeSyncOutlet:
    try:
        definition = outlet_modules[module]
        outlet = getattr(module_outlet, definition)
        return outlet(details, manager)
    except:
        return None
