"""Test scripts for Etekcity Outdoor Outlet."""
from typing import Any, Dict, Union
from copy import deepcopy
import orjson
from pyvesync.devices.vesyncoutlet import VeSyncOutdoorPlug
from pyvesync.utils.helpers import Helpers as Helpers
import call_json
import call_json_outlets
from utils import TestBase
from defaults import Defaults

DEVICE_TYPE = 'ESO15-TB'

DEV_LIST_DETAIL: Dict[str, Union[str, int, float]
                      ] = call_json.DeviceList.device_list_item(DEVICE_TYPE, 0)

DEV_LIST_DETAIL_2: Dict[str, Any] = call_json.DeviceList.device_list_item(DEVICE_TYPE, 1)

CORRECT_OUTDOOR_LIST: Dict[str, Any] = deepcopy(call_json.DeviceList.list_response_base)
CORRECT_OUTDOOR_LIST['result']['list'].extend([DEV_LIST_DETAIL, DEV_LIST_DETAIL_2])
CORRECT_OUTDOOR_RESP: tuple = (CORRECT_OUTDOOR_LIST, 200)


ENERGY_HISTORY: tuple = call_json_outlets.ENERGY_HISTORY

CORRECT_OUTDOOR_DETAILS = call_json_outlets.DETAILS_RESPONSES[DEVICE_TYPE]

BAD_OUTDOOR_LIST: tuple = call_json.DETAILS_BADCODE

DEFAULTS = Defaults


class TestVesyncOutdoorPlug(TestBase):
    """Test class for outdoor outlet."""

    def test_outdoor_conf(self):
        """Tests outdoor outlet is instantiated properly."""
        resp_dict, status = CORRECT_OUTDOOR_RESP
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        self.run_in_loop(self.manager.get_devices)
        outlets = self.manager.outlets
        assert len(outlets) == 2
        outdoor_outlet = outlets[0]
        assert isinstance(outdoor_outlet, VeSyncOutdoorPlug)
        assert outdoor_outlet.device_type == DEVICE_TYPE
        assert outdoor_outlet.uuid == DEFAULTS.uuid(DEVICE_TYPE)

    def test_outdoor_details(self):
        """Tests retrieving outdoor outlet details."""
        resp_dict, status = CORRECT_OUTDOOR_DETAILS
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(outdoor_outlet.get_details)
        dev_details = outdoor_outlet.details
        assert outdoor_outlet.device_status == 'on'
        assert isinstance(outdoor_outlet, VeSyncOutdoorPlug)
        assert dev_details['active_time'] == 1

    def test_outdoor_details_fail(self, caplog):
        """Test outdoor outlet get_details response."""
        resp_dict, status = BAD_OUTDOOR_LIST
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(outdoor_outlet.get_details)
        assert len(caplog.records) == 1
        assert 'details' in caplog.text

    def test_outdoor_outlet_onoff(self):
        """Test Outdoor Outlet Device On/Off Methods."""
        self.mock_api.return_value = (orjson.dumps({'code': 0}), 200)
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.manager)
        head = Helpers.req_legacy_headers(self.manager)
        body = Helpers.req_body(self.manager, 'devicestatus')

        body['status'] = 'on'
        body['uuid'] = outdoor_outlet.uuid
        body['switchNo'] = outdoor_outlet.sub_device_no
        on = self.run_in_loop(outdoor_outlet.turn_on)
        self.mock_api.assert_called_with(
            '/outdoorsocket15a/v1/device/devicestatus', 'put',
            headers=head, json_object=body
        )
        assert on
        off = self.run_in_loop(outdoor_outlet.turn_off)
        body['status'] = 'off'
        self.mock_api.assert_called_with(
            '/outdoorsocket15a/v1/device/devicestatus', 'put',
            headers=head, json_object=body
        )
        assert off

    def test_outdoor_outlet_onoff_fail(self):
        """Test outdoor outlet On/Off Fail with Code>0."""
        self.mock_api.return_value = (orjson.dumps({'code': 1}), 400)
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.manager)
        assert not self.run_in_loop(outdoor_outlet.turn_on)
        assert not self.run_in_loop(outdoor_outlet.turn_off)

    def test_outdoor_outlet_weekly(self):
        """Test outdoor outlet get_weekly_energy."""
        resp_dict, status = ENERGY_HISTORY
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(outdoor_outlet.get_weekly_energy)
        body = Helpers.req_body(self.manager, 'energy_week')
        body['uuid'] = outdoor_outlet.uuid
        self.mock_api.assert_called_with(
            '/outdoorsocket15a/v1/device/energyweek',
            'post',
            headers=Helpers.req_legacy_headers(self.manager),
            json_object=body,
        )
        energy_dict = outdoor_outlet.energy['week']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert outdoor_outlet.weekly_energy_total == 1

    def test_outdoor_outlet_monthly(self):
        """Test outdoor outlet get_monthly_energy."""
        resp_dict, status = ENERGY_HISTORY
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(outdoor_outlet.get_monthly_energy)
        body = Helpers.req_body(self.manager, 'energy_month')
        body['uuid'] = outdoor_outlet.uuid
        self.mock_api.assert_called_with(
            '/outdoorsocket15a/v1/device/energymonth',
            'post',
            headers=Helpers.req_legacy_headers(self.manager),
            json_object=body,
        )
        energy_dict = outdoor_outlet.energy['month']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert outdoor_outlet.monthly_energy_total == 1

    def test_outdoor_outlet_yearly(self):
        """Test outdoor outlet get_yearly_energy."""
        resp_dict, status = ENERGY_HISTORY
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(outdoor_outlet.get_yearly_energy)
        body = Helpers.req_body(self.manager, 'energy_year')
        body['uuid'] = outdoor_outlet.uuid
        self.mock_api.assert_called_with(
            '/outdoorsocket15a/v1/device/energyyear',
            'post',
            headers=Helpers.req_legacy_headers(self.manager),
            json_object=body,
        )
        energy_dict = outdoor_outlet.energy['year']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert outdoor_outlet.yearly_energy_total == 1

    def test_history_fail(self):
        """Test outdoor outlet energy failure."""
        bad_history = orjson.dumps({'code': 1})
        self.mock_api.return_value = (bad_history, 200)
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(outdoor_outlet.update_energy)
        assert len(self.caplog.records) == 1
        assert 'weekly' in self.caplog.text
        self.caplog.clear()
        self.run_in_loop(outdoor_outlet.get_monthly_energy)
        assert len(self.caplog.records) == 1
        assert 'monthly' in self.caplog.text
        self.caplog.clear()
        self.run_in_loop(outdoor_outlet.get_yearly_energy)
        assert len(self.caplog.records) == 1
        assert 'yearly' in self.caplog.text
