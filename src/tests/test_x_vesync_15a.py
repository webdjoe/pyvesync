import orjson
from pyvesync.vesyncoutlet import VeSyncOutlet15A
from pyvesync.helpers import Helpers as Helpers
import call_json
import utils
import call_json_outlets

DEVICE_TYPE = 'ESW15-USA'

DEV_LIST_DETAIL = call_json.DeviceList.device_list_item(DEVICE_TYPE)

CORRECT_15A_LIST = call_json.DeviceList.device_list_response(DEVICE_TYPE)

ENERGY_HISTORY = call_json_outlets.ENERGY_HISTORY

CORRECT_15A_DETAILS = call_json_outlets.DETAILS_RESPONSES[DEVICE_TYPE]

BAD_15A_LIST = call_json.DETAILS_BADCODE


class TestVeSyncSwitch(utils.TestBase):

    def test_15aswitch_conf(self):
        """Tests that 15A Outlet is instantiated properly"""
        self.mock_api.return_value = CORRECT_15A_LIST
        self.run_in_loop(self.manager.get_devices)
        outlets = self.manager.outlets
        assert len(outlets) == 1
        vswitch15a = outlets[0]
        assert isinstance(vswitch15a, VeSyncOutlet15A)
        assert vswitch15a.device_name == call_json.Defaults.name(DEVICE_TYPE)
        assert vswitch15a.device_type == DEVICE_TYPE
        assert vswitch15a.cid == call_json.Defaults.cid(DEVICE_TYPE)
        assert vswitch15a.uuid == call_json.Defaults.uuid(DEVICE_TYPE)

    def test_15a_details(self):
        """Test 15A get_details() """
        resp_dict, status_code = CORRECT_15A_DETAILS
        self.mock_api.return_value = orjson.dumps(resp_dict), status_code
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch15a.get_details)
        dev_details = vswitch15a.details
        assert vswitch15a.device_status == 'on'
        assert isinstance(dev_details, dict)
        assert dev_details['active_time'] == 1
        assert dev_details['energy'] == 1
        assert dev_details['power'] == '1'
        assert dev_details['voltage'] == '1'
        assert vswitch15a.power == 1
        assert vswitch15a.voltage == 1
        assert vswitch15a.active_time == 1
        assert vswitch15a.energy_today == 1


class TestVesync15ASwitch(utils.TestBase):

    def test_15aswitch_conf(self):
        """Tests that 15A Outlet is instantiated properly"""
        self.mock_api.return_value = CORRECT_15A_LIST
        self.run_in_loop(self.manager.get_devices)
        outlets = self.manager.outlets
        assert len(outlets) == 1
        vswitch15a = outlets[0]
        assert isinstance(vswitch15a, VeSyncOutlet15A)
        assert vswitch15a.device_name == call_json.Defaults.name(DEVICE_TYPE)
        assert vswitch15a.device_type == DEVICE_TYPE
        assert vswitch15a.cid == call_json.Defaults.cid(DEVICE_TYPE)
        assert vswitch15a.uuid == call_json.Defaults.uuid(DEVICE_TYPE)

    def test_15a_details_fail(self):
        """Test 15A get_details with Code>0"""
        resp_dict, status_code = BAD_15A_LIST
        self.mock_api.return_value = orjson.dumps(resp_dict), status_code
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch15a.get_details)
        assert len(self.caplog.records) == 1
        assert 'details' in self.caplog.text

    def NO_test_15a_no_details(self):
        """Test 15A details return with no details and code=0"""
        # Removed test - will not be needed with API response validation
        bad_15a_details = {'code': 0, 'deviceStatus': 'on'}
        self.mock_api.return_value = (orjson.dumps(bad_15a_details), 200)
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch15a.get_details)
        assert len(self.caplog.records) == 1

    def test_15a_onoff(self):
        """Test 15A Device On/Off Methods"""
        self.mock_api.return_value = (orjson.dumps({'code': 0}), 200)
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        head = Helpers.req_headers(self.manager)
        body = Helpers.req_body(self.manager, 'devicestatus')

        body['status'] = 'on'
        body['uuid'] = vswitch15a.uuid
        on = self.run_in_loop(vswitch15a.turn_on)
        self.mock_api.assert_called_with(
            '/15a/v1/device/devicestatus', 'put', headers=head, json_object=body
        )
        assert on
        off = self.run_in_loop(vswitch15a.turn_off)
        body['status'] = 'off'
        self.mock_api.assert_called_with(
            '/15a/v1/device/devicestatus', 'put', headers=head, json_object=body
        )
        assert off

    def test_15a_onoff_fail(self):
        """Test 15A On/Off Fail with Code>0"""
        self.mock_api.return_value = (orjson.dumps({'code': 1}), 400)
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        assert not self.run_in_loop(vswitch15a.turn_on)
        assert not self.run_in_loop(vswitch15a.turn_off)

    def test_15a_weekly(self):
        """Test 15A get_weekly_energy"""
        resp_dict, status = ENERGY_HISTORY
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch15a.get_weekly_energy)
        body = Helpers.req_body(self.manager, 'energy_week')
        body['uuid'] = vswitch15a.uuid
        self.mock_api.assert_called_with(
            '/15a/v1/device/energyweek',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        energy_dict = vswitch15a.energy['week']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert vswitch15a.weekly_energy_total == 1

    def test_15a_monthly(self):
        """Test 15A get_monthly_energy"""
        resp_dict, status = ENERGY_HISTORY
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch15a.get_monthly_energy)
        body = Helpers.req_body(self.manager, 'energy_month')
        body['uuid'] = vswitch15a.uuid
        self.mock_api.assert_called_with(
            '/15a/v1/device/energymonth',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        energy_dict = vswitch15a.energy['month']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert vswitch15a.monthly_energy_total == 1

    def test_15a_yearly(self):
        """Test 15A get_yearly_energy"""
        resp_dict, status = ENERGY_HISTORY
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch15a.get_yearly_energy)
        body = Helpers.req_body(self.manager, 'energy_year')
        body['uuid'] = vswitch15a.uuid
        self.mock_api.assert_called_with(
            '/15a/v1/device/energyyear',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        energy_dict = vswitch15a.energy['year']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert vswitch15a.yearly_energy_total == 1

    def test_history_fail(self):
        """Test 15A energy failure"""
        bad_history = {'code': 1}
        self.mock_api.return_value = (orjson.dumps(bad_history), 200)
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch15a.update_energy)
        assert len(self.caplog.records) == 1
        assert 'weekly' in self.caplog.text
        self.caplog.clear()
        self.run_in_loop(vswitch15a.get_monthly_energy)
        assert len(self.caplog.records) == 1
        assert 'monthly' in self.caplog.text
        self.caplog.clear()
        self.run_in_loop(vswitch15a.get_yearly_energy)
        assert len(self.caplog.records) == 1
        assert 'yearly' in self.caplog.text
