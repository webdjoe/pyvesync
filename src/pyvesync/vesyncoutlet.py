from abc import ABCMeta, abstractmethod
import logging

from pyvesync.vesyncbasedevice import VeSyncBaseDevice
import pyvesync.helpers as helpers

logger = logging.getLogger(__name__)


class VeSyncOutlet(VeSyncBaseDevice):
    __metaclass__ = ABCMeta

    def __init__(self, details, manager):
        super().__init__(details, manager)

        self.details = {}
        self.energy = {}
    
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
            self.device_status = r.get('deviceStatus')
            self.details['active_time'] = r.get('activeTime')
            self.details['energy'] = r.get('energy')
            self.details['power'] = r.get('power')
            self.details['voltage'] = r.get('voltage')
        else:
            logger.debug('Unable to get {0} details'.format(self.device_name))

    def get_weekly_energy(self):
        r, _ = helpers.call_api(
            '/v1/device/' + self.cid + '/energy/week',
            'get',
            headers=helpers.req_headers(self.manager)
        )

        if r is not None and helpers.check_response(r, '7a_energy'):
            self.energy['week'] = helpers.build_energy_dict(r)
        else:
            logger.error(
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
            logger.error(
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
            logger.error(
                'Unable to get {0} yearly data'.format(self.device_name))

    def update(self):
        self.get_details()

    def update_energy(self):
        self.get_weekly_energy()
        if 'week' in self.energy:
            self.get_monthly_energy()
            self.get_yearly_energy()

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
            return False

    def power(self):
        data = self.details.get('power', '0:0')

        return round(float(helpers.calculate_hex(data)), 2)

    def voltage(self):
        data = self.details.get('voltage', '0:0')

        return round(float(helpers.calculate_hex(data)), 2)


class VeSyncOutlet10A(VeSyncOutlet):
    def __init__(self, details, manager):
        super(VeSyncOutlet10A, self).__init__(details, manager)

    def get_body(self, type_):
        if type_ == 'detail':
            body = helpers.req_body('devicedetail')
        elif type_ == 'status':
            body = helpers.req_body('devicestatus')
        body['uuid'] = self.uuid

        return body

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
            self.device_status = r['deviceStatus']
            self.connection_status = r.get('connectionStatus')
            self.details = helpers.build_details_dict()
        else:
            logger.debug('Unable to get {0} details'.format(self.device_name))

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
            logger.error(
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
            logger.error(
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
            logger.error(
                'Unable to get {0} yearly data'.format(self.device_name)
            )

    def update(self):
        self.get_details()

    def update_energy(self):
        self.get_weekly_energy()
        if 'week' in self.energy:
            self.get_monthly_energy()
            self.get_yearly_energy()

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

        attr_list = (
            'deviceStatus', 'activeTime', 'energy', 'power', 'voltage',
            'nightLightStatus', 'nightLightAutomode', 'nightLightBrightness'
        )

        if (helpers.check_response(r, '15a_detail') and
                all(k in r for k in attr_list)):

            self.device_status = r.get('deviceStatus')
            self.connection_status = r.get('connectionStatus')
            self.details = helpers.build_details_dict()
        else:
            logger.debug('Unable to get {0} details'.format(self.device_name))

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
            logger.error(
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
            logger.error(
                'Unable to get {0} yearly data'.format(self.device_name)
            )

    def update(self):
        self.get_details()

    def update_energy(self):
        self.get_weekly_energy()
        if 'week' in self.energy:
            self.get_monthly_energy()
            self.get_yearly_energy()

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
            return False

    def turn_on_nightlight(self):
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
