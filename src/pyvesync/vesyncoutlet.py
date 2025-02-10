"""Etekcity Outlets."""

import logging
import time
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING
import orjson

from pyvesync.helpers import Helpers
from pyvesync.vesyncbasedevice import VeSyncBaseDevice

if TYPE_CHECKING:
    from pyvesync import VeSync

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
}

outlet_modules = {k: v['module'] for k, v in outlet_config.items()}

__all__ = [*outlet_modules.values(), 'outlet_modules']  # noqa: PLE0604


class VeSyncOutlet(VeSyncBaseDevice):
    """Base class for Etekcity Outlets."""

    __metaclass__ = ABCMeta

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initilize VeSync Outlet base class."""
        super().__init__(details, manager)

        self.details: dict = {}
        self.energy: dict = {}
        self.update_energy_ts: None | int = None
        self._energy_update_interval = manager.energy_update_interval

    @property
    def update_time_check(self) -> bool:
        """Test if energy update interval has been exceeded."""
        if self.update_energy_ts is None:
            return True
        return ((time.time() - self.update_energy_ts)
                > self._energy_update_interval)

    @abstractmethod
    async def turn_on(self) -> bool:
        """Return True if device has beeeen turned on."""

    @abstractmethod
    async def turn_off(self) -> bool:
        """Return True if device has beeeen turned off."""

    @abstractmethod
    async def get_details(self) -> None:
        """Build details dictionary."""

    @abstractmethod
    async def get_weekly_energy(self) -> None:
        """Build weekly energy history dictionary."""

    @abstractmethod
    async def get_monthly_energy(self) -> None:
        """Build Monthly Energy History Dictionary."""

    @abstractmethod
    async def get_yearly_energy(self) -> None:
        """Build Yearly Energy Dictionary."""

    @abstractmethod
    async def get_config(self) -> None:
        """Get configuration and firmware details."""

    async def update(self) -> None:
        """Get Device Energy and Status."""
        await self.get_details()

    async def update_energy(self, bypass_check: bool = False) -> None:
        """Build weekly, monthly and yearly dictionaries."""
        if bypass_check or (not bypass_check and self.update_time_check):
            self.update_energy_ts = int(time.time())
            await self.get_weekly_energy()
            if 'week' in self.energy:
                self.get_monthly_energy()
                self.get_yearly_energy()
            if not bypass_check:
                self.update_energy_ts = int(time.time())

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
            ('Energy Week: ', self.weekly_energy_total, ' kWh'),
            ('Energy Month: ', self.monthly_energy_total, ' kWh'),
            ('Energy Year: ', self.yearly_energy_total, ' kWh'),
        ]
        for line in disp:
            print(f'{line[0]:.<30} {line[1]} {line[2]}')

    def displayJSON(self) -> str:
        """Return JSON details for outlet."""
        sup = super().displayJSON()
        sup_val = orjson.loads(sup)
        sup_val.update(
            {
                'Active Time': str(self.active_time),
                'Energy': str(self.energy_today),
                'Power': str(self.power),
                'Voltage': str(self.voltage),
                'Energy Week': str(self.weekly_energy_total),
                'Energy Month': str(self.monthly_energy_total),
                'Energy Year': str(self.yearly_energy_total),
            }
        )

        return orjson.dumps(
            sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
            ).decode()


class VeSyncOutlet7A(VeSyncOutlet):
    """Etekcity 7A Round Outlet Class."""

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initilize Etekcity 7A round outlet class."""
        super().__init__(details, manager)
        self.det_keys = ['deviceStatus', 'activeTime',
                         'energy', 'power', 'voltage']
        self.energy_keys = ['energyConsumptionOfToday',
                            'maxEnergy', 'totalEnergy']

    async def get_details(self) -> None:
        """Get 7A outlet details."""
        r_bytes, _ = await self.manager.call_api(
            '/v1/device/' + self.cid + '/detail',
            'get',
            headers=Helpers.req_headers(self.manager),
        )

        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        self.device_status = r.get('deviceStatus', self.device_status)
        self.details['active_time'] = r.get('activeTime', 0)
        self.details['energy'] = r.get('energy', 0)
        power = r.get('power', '0')
        self.details['power'] = self.parse_energy_detail(power)
        voltage = r.get('voltage', 0)
        self.details['voltage'] = self.parse_energy_detail(voltage)

    @staticmethod
    def parse_energy_detail(energy: str | float) -> float:
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

    async def get_weekly_energy(self) -> None:
        """Get 7A outlet weekly energy info and buld weekly energy dict."""
        r_bytes, _ = await self.manager.call_api(
            '/v1/device/' + self.cid + '/energy/week',
            'get',
            headers=Helpers.req_headers(self.manager),
        )

        r = Helpers.process_api_response(
            logger, "get_weekly_energy", self, r_bytes
            )
        if r is None:
            return

        self.energy['week'] = Helpers.build_energy_dict(r)

    async def get_monthly_energy(self) -> None:
        """Get 7A outlet monthly energy info and buld monthly energy dict."""
        r_bytes, _ = await self.manager.call_api(
            '/v1/device/' + self.cid + '/energy/month',
            'get',
            headers=Helpers.req_headers(self.manager),
        )
        r = Helpers.process_api_response(
            logger, "get_monthly_energy", self, r_bytes
        )
        if r is None:
            return

        self.energy['month'] = Helpers.build_energy_dict(r)

    async def get_yearly_energy(self) -> None:
        """Get 7A outlet yearly energy info and build yearly energy dict."""
        r_bytes, _ = await self.manager.call_api(
            '/v1/device/' + self.cid + '/energy/year',
            'get',
            headers=Helpers.req_headers(self.manager),
        )
        r = Helpers.process_api_response(
            logger, "get_yearly_energy", self, r_bytes
        )
        if r is None:
            return

        self.energy['year'] = Helpers.build_energy_dict(r)

    async def turn_on(self) -> bool:
        """Turn 7A outlet on - return True if successful."""
        _, status_code = await self.manager.call_api(
            '/v1/wifi-switch-1.3/' + self.cid + '/status/on',
            'put',
            headers=Helpers.req_headers(self.manager),
        )
        if status_code is not None and status_code == 200:
            self.device_status = 'on'
            return True
        logger.warning('Error turning %s on', self.device_name)
        return False

    async def turn_off(self) -> bool:
        """Turn 7A outlet off - return True if successful."""
        _, status_code = await self.manager.call_api(
            '/v1/wifi-switch-1.3/' + self.cid + '/status/off',
            'put',
            headers=Helpers.req_headers(self.manager),
        )

        if status_code is not None and status_code == 200:
            self.device_status = 'off'

            return True
        logger.warning('Error turning %s off', self.device_name)
        return False

    async def get_config(self) -> None:
        """Get 7A outlet configuration info."""
        r_bytes, _ = await self.manager.call_api(
            '/v1/device/' + self.cid + '/configurations',
            'get',
            headers=Helpers.req_headers(self.manager),
        )

        r = Helpers.process_api_response(logger, "get_config", self, r_bytes)
        if r is None:
            return

        if 'currentFirmVersion' in r:
            self.config = Helpers.build_config_dict(r)
        else:
            logger.debug('Error getting configuration info for %s',
                         self.device_name)


class VeSyncOutlet10A(VeSyncOutlet):
    """Etekcity 10A Round Outlets."""

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initialize 10A outlet class."""
        super().__init__(details, manager)

    async def get_details(self) -> None:
        """Get 10A outlet details."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/10a/v1/device/devicedetail',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        self.device_status = r.get('deviceStatus', self.device_status)
        self.connection_status = r.get('connectionStatus', self.connection_status)
        self.details = Helpers.build_details_dict(r)

    async def get_config(self) -> None:
        """Get 10A outlet configuration info."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/10a/v1/device/configurations',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_config", self, r_bytes)
        if r is None:
            return

        self.config = Helpers.build_config_dict(r)

    async def get_weekly_energy(self) -> None:
        """Get 10A outlet weekly energy info and populate energy dict."""
        body = Helpers.req_body(self.manager, 'energy_week')
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/10a/v1/device/energyweek',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(
            logger, "get_weekly_energy", self, r_bytes
            )
        if response is None:
            return

        self.energy['week'] = Helpers.build_energy_dict(response)

    async def get_monthly_energy(self) -> None:
        """Get 10A outlet monthly energy info and populate energy dict."""
        body = Helpers.req_body(self.manager, 'energy_month')
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/10a/v1/device/energymonth',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(
            logger, "get_monthly_energy", self, r_bytes
        )
        if response is None:
            return

        self.energy['month'] = Helpers.build_energy_dict(response)

    async def get_yearly_energy(self) -> None:
        """Get 10A outlet yearly energy info and populate energy dict."""
        body = Helpers.req_body(self.manager, 'energy_year')
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/10a/v1/device/energyyear',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(
            logger, "get_yearly_energy", self, r_bytes
        )
        if response is None:
            return

        self.energy['year'] = Helpers.build_energy_dict(response)

    async def turn_on(self) -> bool:
        """Turn 10A outlet on - return True if successful."""
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = 'on'

        r_bytes, _ = await self.manager.call_api(
            '/10a/v1/device/devicestatus',
            'put',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(logger, "turn_on", self, r_bytes)
        if response is None:
            return False

        self.device_status = 'on'
        return True

    async def turn_off(self) -> bool:
        """Turn 10A outlet off - return True if successful."""
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = 'off'

        r_bytes, _ = await self.manager.call_api(
            '/10a/v1/device/devicestatus',
            'put',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(logger, "turn_off", self, r_bytes)
        if response is None:
            return False

        self.device_status = 'off'
        return True


class VeSyncOutlet15A(VeSyncOutlet):
    """Class for Etekcity 15A Rectangular Outlets."""

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initialize 15A rectangular outlets."""
        super().__init__(details, manager)
        self.nightlight_status = 'off'
        self.nightlight_brightness = 0

    async def get_details(self) -> None:
        """Get 15A outlet details."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/15a/v1/device/devicedetail',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )

        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        # Leave this in for typing purposes
        attr_list = (  # pylint: disable=unused-variable # noqa: F841
            'deviceStatus',
            'activeTime',
            'energy',
            'power',
            'voltage',
            'nightLightStatus',
            'nightLightAutomode',
            'nightLightBrightness',
        )

        self.device_status = r.get('deviceStatus')
        self.connection_status = r.get('connectionStatus')
        self.nightlight_status = r.get('nightLightStatus')
        self.nightlight_brightness = r.get('nightLightBrightness')
        self.details = Helpers.build_details_dict(r)

    async def get_config(self) -> None:
        """Get 15A outlet configuration info."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/15a/v1/device/configurations',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_config", self, r_bytes)
        if r is None:
            return

        self.config = Helpers.build_config_dict(r)

    async def get_weekly_energy(self) -> None:
        """Get 15A outlet weekly energy info and populate energy dict."""
        body = Helpers.req_body(self.manager, 'energy_week')
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/15a/v1/device/energyweek',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(
            logger, "get_weekly_energy", self, r_bytes
        )
        if response is None:
            return
        self.energy['week'] = Helpers.build_energy_dict(response)

    async def get_monthly_energy(self) -> None:
        """Get 15A outlet monthly energy info and populate energy dict."""
        body = Helpers.req_body(self.manager, 'energy_month')
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/15a/v1/device/energymonth',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(
            logger, "get_monthly_energy", self, r_bytes
        )
        if response is None:
            return

        self.energy['month'] = Helpers.build_energy_dict(response)

    async def get_yearly_energy(self) -> None:
        """Get 15A outlet yearly energy info and populate energy dict."""
        body = Helpers.req_body(self.manager, 'energy_year')
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/15a/v1/device/energyyear',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(
            logger, "get_yearly_energy", self, r_bytes
        )
        if response is None:
            return

        self.energy['year'] = Helpers.build_energy_dict(response)

    async def turn_on(self) -> bool:
        """Turn 15A outlet on - return True if successful."""
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = 'on'

        r_bytes, _ = await self.manager.call_api(
            '/15a/v1/device/devicestatus',
            'put',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(logger, "turn_on", self, r_bytes)
        if response is None:
            return False

        if Helpers.code_check(response):
            self.device_status = 'on'
            return True
        logger.warning('Error turning %s on', self.device_name)
        return False

    async def turn_off(self) -> bool:
        """Turn 15A outlet off - return True if successful."""
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = 'off'

        r_bytes, _ = await self.manager.call_api(
            '/15a/v1/device/devicestatus',
            'put',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(logger, "turn_off", self, r_bytes)
        if response is None:
            return False

        self.device_status = 'off'
        return True

    async def turn_on_nightlight(self) -> bool:
        """Turn on nightlight."""
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['mode'] = 'auto'

        r_bytes, _ = await self.manager.call_api(
            '/15a/v1/device/nightlightstatus',
            'put',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(
            logger, "turn_on_nightlight", self, r_bytes
        )
        return bool(response)

    async def turn_off_nightlight(self) -> bool:
        """Turn Off Nightlight."""
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['mode'] = 'manual'

        r_bytes, _ = await self.manager.call_api(
            '/15a/v1/device/nightlightstatus',
            'put',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(
            logger, "turn_off_nightlight", self, r_bytes
        )
        return bool(response)


class VeSyncOutdoorPlug(VeSyncOutlet):
    """Class to hold Etekcity outdoor outlets."""

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initialize Etekcity Outdoor Plug class."""
        super().__init__(details, manager)

    async def get_details(self) -> None:
        """Get details for outdoor outlet."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['uuid'] = self.uuid
        r_bytes, _ = await self.manager.call_api(
            '/outdoorsocket15a/v1/device/devicedetail',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        self.details = Helpers.build_details_dict(r)
        self.connection_status = r.get('connectionStatus')

        dev_no = self.sub_device_no
        sub_device_list = r.get('subDevices')
        if sub_device_list and dev_no <= len(sub_device_list):
            self.device_status = sub_device_list[(dev_no + -1)].get(
                'subDeviceStatus'
            )

    async def get_config(self) -> None:
        """Get configuration info for outdoor outlet."""
        body = Helpers.req_body(self.manager, 'devicedetail')
        body['method'] = 'configurations'
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/outdoorsocket15a/v1/device/configurations',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_config", self, r_bytes)
        if r is None:
            return

        self.config = Helpers.build_config_dict(r)

    async def get_weekly_energy(self) -> None:
        """Get outdoor outlet weekly energy info and populate energy dict."""
        body = Helpers.req_body(self.manager, 'energy_week')
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/outdoorsocket15a/v1/device/energyweek',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(
            logger, "get_weekly_energy", self, r_bytes
        )
        if response is None:
            return

        self.energy['week'] = Helpers.build_energy_dict(response)

    async def get_monthly_energy(self) -> None:
        """Get outdoor outlet monthly energy info and populate energy dict."""
        body = Helpers.req_body(self.manager, 'energy_month')
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/outdoorsocket15a/v1/device/energymonth',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(
            logger, "get_monthly_energy", self, r_bytes
        )
        if response is None:
            return

        self.energy['month'] = Helpers.build_energy_dict(response)

    async def get_yearly_energy(self) -> None:
        """Get outdoor outlet yearly energy info and populate energy dict."""
        body = Helpers.req_body(self.manager, 'energy_year')
        body['uuid'] = self.uuid

        r_bytes, _ = await self.manager.call_api(
            '/outdoorsocket15a/v1/device/energyyear',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(
            logger, "get_yearly_energy", self, r_bytes
        )
        if response is None:
            return

        self.energy['year'] = Helpers.build_energy_dict(response)

    async def toggle(self, status: str) -> bool:
        """Toggle power for outdoor outlet."""
        body = Helpers.req_body(self.manager, 'devicestatus')
        body['uuid'] = self.uuid
        body['status'] = status
        body['switchNo'] = self.sub_device_no

        r_bytes, _ = await self.manager.call_api(
            '/outdoorsocket15a/v1/device/devicestatus',
            'put',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        response = Helpers.process_api_response(logger, "toggle", self, r_bytes)
        if response is None:
            return False

        self.device_status = status
        return True

    async def turn_on(self) -> bool:
        """Turn on outlet."""
        on = await self.toggle('on')
        return bool(on)

    async def turn_off(self) -> bool:
        """Turn off outlet."""
        off = await self.toggle('off')
        return bool(off)


class VeSyncOutletBSDGO1(VeSyncOutlet):
    """VeSync BSDGO1 smart plug."""

    def __init__(self, details: dict, manager: 'VeSync') -> None:
        """Initialize BSDGO1 smart plug class."""
        super().__init__(details, manager)

    async def get_details(self) -> None:
        """Get BSDGO1 device details."""
        body = Helpers.req_body(self.manager, 'bypassV2')
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'method': 'getProperty',
            'source': 'APP',
            'data': {}
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        self.device_status = 'on' if r.get('result', {}).get(
            'powerSwitch_1') == 1 else 'off'

    async def turn_on(self) -> bool:
        """Turn BSDGO1 outlet on."""
        return await self._set_power(True)

    async def turn_off(self) -> bool:
        """Turn BSDGO1 outlet off."""
        return await self._set_power(False)

    async def _set_power(self, power: bool) -> bool:
        """Set power state of BSDGO1 outlet."""
        body = Helpers.req_body(self.manager, 'bypassV2')
        body['cid'] = self.cid
        body['configModule'] = self.config_module
        body['payload'] = {
            'data': {'powerSwitch_1': 1 if power else 0},
            'method': 'setProperty',
            'source': 'APP'
        }

        r_bytes, _ = await self.manager.call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=body,
        )
        r = Helpers.process_api_response(logger, "set_power", self, r_bytes)
        if r is None:
            return False

        self.device_status = 'on' if power else 'off'
        return True
