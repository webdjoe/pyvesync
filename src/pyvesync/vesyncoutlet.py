import logging
import time
from abc import ABCMeta, abstractmethod

from pyvesync.helpers import Helpers as helpers
from pyvesync.vesyncbasedevice import VeSyncBaseDevice

logger = logging.getLogger(__name__)


class VeSyncOutlet(VeSyncBaseDevice):
    __metaclass__ = ABCMeta

    def __init__(self, details, manager):
        super(VeSyncOutlet, self).__init__(details, manager)

        self.details = {}
        self.energy = {}
        self.update_energy_ts = None
        self._energy_update_interval = manager.energy_update_interval

    @property
    def update_time_check(self) -> bool:
        if self.update_energy_ts is None:
            return True
        else:
            if (time.time() - self.update_energy_ts) \
                    > self._energy_update_interval:
                return True
            else:
                return False

    @abstractmethod
    def turn_on(self):
        """Return True if device has beeeen turned on"""

    @abstractmethod
    def turn_off(self):
        """Return True if device has beeeen turned off"""

    @abstractmethod
    def get_details(self):
        """Build details dictionary"""

    @abstractmethod
    def get_weekly_energy(self):
        """Build weekly energy history dictionary"""

    @abstractmethod
    def get_monthly_energy(self):
        """Build Monthly Energy History Dictionary"""

    @abstractmethod
    def get_yearly_energy(self):
        """Build Yearly Energy Dictionary"""

    @abstractmethod
    def get_config(self):
        """Get configuration and firmware details"""

    def update(self):
        """Gets Device Energy and Status"""
        self.get_details()

    def update_energy(self, bypass_check: bool = False):
        """Builds weekly, monthly and yearly dictionaries"""
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
        """Return active time of a device in minutes"""
        return self.details.get('active_time', 0)

    @property
    def energy_today(self) -> float:
        """Return energy"""
        return self.details.get('energy', 0)

    @property
    def power(self) -> float:
        """Return current power in watts"""
        return float(self.details.get('power', 0))

    @property
    def voltage(self) -> float:
        """Return current voltage"""
        return float(self.details.get('voltage', 0))

    @property
    def monthly_energy_total(self) -> float:
        """Return total energy usage over the month"""
        return self.energy.get('month', {}).get('total_energy', 0)

    @property
    def weekly_energy_total(self) -> float:
        """Return total energy usage over the week"""
        return self.energy.get('week', {}).get('total_energy', 0)

    @property
    def yearly_energy_total(self) -> float:
        """Return total energy usage over the year"""
        return self.energy.get('year', {}).get('total_energy', 0)

    def display(self):
        super(VeSyncOutlet, self).display()
        disp1 = [("Active Time : ", self.active_time, ' minutes'),
                 ("Energy: ", self.energy_today, " kWh"),
                 ("Power: ", self.power, " Watts"),
                 ("Voltage: ", self.voltage, " Volts"),
                 ("Energy Week: ", self.weekly_energy_total, " kWh"),
                 ("Energy Month: ", self.monthly_energy_total, " kWh"),
                 ("Energy Year: ", self.yearly_energy_total, " kWh")]
        for line in disp1:
            print("{:.<15} {} {}".format(line[0], line[1], line[2]))


class VeSyncOutlet7A(VeSyncOutlet):
    def __init__(self, details, manager):
        super(VeSyncOutlet7A, self).__init__(details, manager)

    def get_details(self):
        r, _ = helpers.call_api(
            '/v1/device/' + self.cid + '/detail',
            'get',
            headers=helpers.req_headers(self.manager)
        )

        if r is not None and helpers.check_response(r, '7a_detail'):
            self.device_status = r.get('deviceStatus', self.device_status)
            self.details['active_time'] = r.get('activeTime', 0)
            self.details['energy'] = r.get('energy', 0)
            power = r.get('power', '0:0')
            power = round(float(helpers.calculate_hex(power)), 2)
            self.details['power'] = power
            voltage = r.get('voltage', '0:0')
            voltage = round(float(helpers.calculate_hex(voltage)), 2)
            self.details['voltage'] = voltage
        else:
            logger.debug('Unable to get {0} details'.format(
                self.device_name))

    def get_weekly_energy(self):
        r, _ = helpers.call_api(
            '/v1/device/' + self.cid + '/energy/week',
            'get',
            headers=helpers.req_headers(self.manager)
        )

        if r is not None and helpers.check_response(r, '7a_energy'):
            self.energy['week'] = helpers.build_energy_dict(r)
        else:
            logger.debug(
                'Unable to get {0} weekly data'.format(self.device_name))

    def get_monthly_energy(self):
        r, _ = helpers.call_api(
            '/v1/device/' + self.cid + '/energy/month',
            'get',
            headers=helpers.req_headers(self.manager)
        )

        if r is not None and helpers.check_response(r, '7a_energy'):
            self.energy['month'] = helpers.build_energy_dict(r)
        else:
            logger.warning(
                'Unable to get {0} monthly data'.format(self.device_name))

    def get_yearly_energy(self):
        r, _ = helpers.call_api(
            '/v1/device/' + self.cid + '/energy/year',
            'get',
            headers=helpers.req_headers(self.manager)
        )

        if r is not None and helpers.check_response(r, '7a_energy'):
            self.energy['year'] = helpers.build_energy_dict(r)
        else:
            logger.debug(
                'Unable to get {0} yearly data'.format(self.device_name))

    def turn_on(self):
        _, status_code = helpers.call_api(
            '/v1/wifi-switch-1.3/' + self.cid + '/status/on',
            'put',
            headers=helpers.req_headers(self.manager)
        )

        if status_code is not None and status_code == 200:
            self.device_status = 'on'

            return True
        else:
            logger.warning('Error turning {} on'.format(self.device_name))
            return False

    def turn_off(self):
        _, status_code = helpers.call_api(
            '/v1/wifi-switch-1.3/' + self.cid + '/status/off',
            'put',
            headers=helpers.req_headers(self.manager)
        )

        if status_code is not None and status_code == 200:
            self.device_status = 'off'

            return True
        else:
            logger.warning('Error turning {} off'.format(self.device_name))
            return False

    def get_config(self):
        r, _ = helpers.call_api(
            '/v1/device/' + self.cid + '/configurations',
            'get',
            headers=helpers.req_headers(self.manager)
        )

        if 'currentFirmVersion' in r:
            self.config = helpers.build_config_dict(r)


class VeSyncOutlet10A(VeSyncOutlet):
    def __init__(self, details, manager):
        super(VeSyncOutlet10A, self).__init__(details, manager)

    def get_details(self):
        body = helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/10a/v1/device/devicedetail',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(r, '10a_detail'):
            self.device_status = r.get('deviceStatus', self.device_status)
            self.connection_status = r.get('connectionStatus',
                                           self.connection_status)
            self.details = helpers.build_details_dict(r)
        else:
            logger.debug('Unable to get {0} details'.format(self.device_name))

    def get_config(self):
        body = helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/10a/v1/device/configurations',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(r, 'config'):
            self.config = helpers.build_config_dict(r)

    def get_weekly_energy(self):
        body = helpers.req_body(self.manager, 'energy_week')
        body['uuid'] = self.uuid

        response, _ = helpers.call_api(
            '/10a/v1/device/energyweek',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(response, '10a_energy'):
            self.energy['week'] = helpers.build_energy_dict(response)
        else:
            logger.debug(
                'Unable to get {0} weekly data'.format(self.device_name)
            )

    def get_monthly_energy(self):
        body = helpers.req_body(self.manager, 'energy_month')
        body['uuid'] = self.uuid

        response, _ = helpers.call_api(
            '/10a/v1/device/energymonth',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(response, '10a_energy'):
            self.energy['month'] = helpers.build_energy_dict(response)
        else:
            logger.debug(
                'Unable to get {0} monthly data'.format(self.device_name)
            )

    def get_yearly_energy(self):
        body = helpers.req_body(self.manager, 'energy_year')
        body['uuid'] = self.uuid

        response, _ = helpers.call_api(
            '/10a/v1/device/energyyear',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(response, '10a_energy'):
            self.energy['year'] = helpers.build_energy_dict(response)
        else:
            logger.debug(
                'Unable to get {0} yearly data'.format(self.device_name)
            )

    def turn_on(self):
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = 'on'

        response, _ = helpers.call_api(
            '/10a/v1/device/devicestatus',
            'put',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(response, '10a_toggle'):
            self.device_status = 'on'
            return True
        else:
            logger.warning('Error turning {} on'.format(self.device_name))
            return False

    def turn_off(self):
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = 'off'

        response, _ = helpers.call_api(
            '/10a/v1/device/devicestatus',
            'put',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(response, '10a_toggle'):
            self.device_status = 'off'
            return True
        else:
            logger.warning('Error turning {} off'.format(self.device_name))
            return False


class VeSyncOutlet15A(VeSyncOutlet):
    def __init__(self, details, manager):
        super(VeSyncOutlet15A, self).__init__(details, manager)

    def get_details(self):
        body = helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/15a/v1/device/devicedetail',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        attr_list = ('deviceStatus', 'activeTime', 'energy', 'power',
                     'voltage', 'nightLightStatus', 'nightLightAutomode',
                     'nightLightBrightness')

        if (helpers.check_response(r, '15a_detail')
                and all(k in r for k in attr_list)):

            self.device_status = r.get('deviceStatus')
            self.connection_status = r.get('connectionStatus')
            self.details = helpers.build_details_dict(r)
        else:
            logger.debug(
                'Unable to get {0} details'.format(self.device_name)
            )

    def get_config(self):
        body = helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/15a/v1/device/configurations',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(r, 'config'):
            self.config = helpers.build_config_dict(r)

    def get_weekly_energy(self):
        body = helpers.req_body(self.manager, 'energy_week')
        body['uuid'] = self.uuid

        response, _ = helpers.call_api(
            '/15a/v1/device/energyweek',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(response, '15a_energy'):
            self.energy['week'] = helpers.build_energy_dict(response)
        else:
            logger.debug(
                'Unable to get {0} weekly data'.format(self.device_name)
            )

    def get_monthly_energy(self):
        body = helpers.req_body(self.manager, 'energy_month')
        body['uuid'] = self.uuid

        response, _ = helpers.call_api(
            '/15a/v1/device/energymonth',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(response, '15a_energy'):
            self.energy['month'] = helpers.build_energy_dict(response)
        else:
            logger.debug(
                'Unable to get {0} monthly data'.format(self.device_name)
            )

    def get_yearly_energy(self):
        body = helpers.req_body(self.manager, 'energy_year')
        body['uuid'] = self.uuid

        response, _ = helpers.call_api(
            '/15a/v1/device/energyyear',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(response, '15a_energy'):
            self.energy['year'] = helpers.build_energy_dict(response)
        else:
            logger.debug(
                'Unable to get {0} yearly data'.format(self.device_name)
            )

    def turn_on(self):
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = 'on'

        response, _ = helpers.call_api(
            '/15a/v1/device/devicestatus',
            'put',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(response, '15a_toggle'):
            self.device_status = 'on'
            return True
        else:
            logger.warning('Error turning {} on'.format(self.device_name))
            return False

    def turn_off(self):
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = 'off'

        response, _ = helpers.call_api(
            '/15a/v1/device/devicestatus',
            'put',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(response, '15a_toggle'):
            self.device_status = 'off'
            return True
        else:
            logger.warning('Error turning {} off'.format(self.device_name))
            return False

    def turn_on_nightlight(self):
        """Turn on nightlight"""
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['mode'] = 'auto'

        response, _ = helpers.call_api(
            '/15a/v1/device/nightlightstatus',
            'put',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        return helpers.check_response(response, '15a_ntlight')

    def turn_off_nightlight(self):
        """Turn Off Nightlight"""
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['mode'] = 'manual'

        response, _ = helpers.call_api(
            '/15a/v1/device/nightlightstatus',
            'put',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        return helpers.check_response(response, '15a_ntlight')


class VeSyncOutdoorPlug(VeSyncOutlet):
    """Class to hold VeSync outdoor outlets."""
    def __init__(self, details, manager):
        super(VeSyncOutdoorPlug, self).__init__(details, manager)

    def get_details(self):
        body = helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        r, _ = helpers.call_api(
            '/outdoorsocket15a/v1/device/devicedetail',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body)

        if helpers.check_response(r, 'outdoor_detail'):
            self.details = helpers.build_details_dict(r)
            self.connection_status = r.get('connectionStatus')

            dev_no = self.sub_device_no
            sub_device_list = r.get('subDevices')
            if sub_device_list and dev_no <= len(sub_device_list):
                self.device_status = sub_device_list[(dev_no + -1)].get(
                    'subDeviceStatus')
        else:
            logger.debug('Unable to get {} details'.format(self.device_name))

    def get_config(self):
        body = helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r, _ = helpers.call_api(
            '/outdoorsocket15a/v1/device/configurations',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(r, 'config'):
            self.config = helpers.build_config_dict(r)

    def get_weekly_energy(self):
        body = helpers.req_body(self.manager, 'energy_week')
        body['uuid'] = self.uuid

        response, _ = helpers.call_api(
            '/outdoorsocket15a/v1/device/energyweek',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
            )

        if helpers.check_response(response, 'outdoor_energy'):
            self.energy['week'] = helpers.build_energy_dict(response)
        else:
            logger.debug(
                'Unable to get {} weekly data'.format(self.device_name)
            )

    def get_monthly_energy(self):
        body = helpers.req_body(self.manager, 'energy_month')
        body['uuid'] = self.uuid

        response, _ = helpers.call_api(
            '/outdoorsocket15a/v1/device/energymonth',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
            )

        if helpers.check_response(response, 'outdoor_energy'):
            self.energy['month'] = helpers.build_energy_dict(response)
        else:
            logger.debug(
                'Unable to get {} monthly data'.format(self.device_name)
            )

    def get_yearly_energy(self):
        body = helpers.req_body(self.manager, 'energy_year')
        body['uuid'] = self.uuid

        response, _ = helpers.call_api(
            '/outdoorsocket15a/v1/device/energyyear',
            'post',
            headers=helpers.req_headers(self.manager),
            json=body
            )

        if helpers.check_response(response, '10a_energy'):
            self.energy['year'] = helpers.build_energy_dict(response)
        else:
            logger.debug(
                'Unable to get {0} yearly data'.format(self.device_name)
            )

    def toggle(self, status):
        """Toggle power for outdoor outlet"""
        body = helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = status
        body['switchNo'] = self.sub_device_no

        response, _ = helpers.call_api(
            '/outdoorsocket15a/v1/device/devicestatus',
            'put',
            headers=helpers.req_headers(self.manager),
            json=body
        )

        if helpers.check_response(response, 'outdoor_toggle'):
            self.device_status = status
            return True
        else:
            logger.warning(
                'Error turning {} {}'.format(self.device_name, status))
            return False

    def turn_on(self):
        if self.toggle('on'):
            return True
        else:
            return False

    def turn_off(self):
        if self.toggle('off'):
            return True
        else:
            return False
