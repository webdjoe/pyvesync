"""Etekcity 7A Outlet tests."""

import orjson
from pyvesync.devices.vesyncoutlet import VeSyncOutlet7A
from pyvesync.utils.helpers import Helpers as Helpers
import call_json
import call_json_outlets
from base_test_cases import TestBase

DEVICE_TYPE = 'wifi-switch-1.3'

DEV_LIST_DETAIL = call_json.DeviceList.device_list_item(DEVICE_TYPE)

CORRECT_7A_LIST = call_json.DeviceList.device_list_response(DEVICE_TYPE)

CORRECT_7A_DETAILS = call_json_outlets.DETAILS_RESPONSES[DEVICE_TYPE]

ENERGY_HISTORY = call_json_outlets.ENERGY_HISTORY

DEVICE_TYPE = 'wifi-switch-1.3'

CALL_LIST = [
    'turn_on',
    'turn_off',
    'update'
]


class TestVesync7ASwitch(TestBase):
    """Test 7A outlet API."""

    def test_7aswitch_conf(self):
        """Test inizialization of 7A outlet."""
        self.mock_api.return_value = CORRECT_7A_LIST
        self.run_in_loop(self.manager.get_devices)
        outlets = self.manager.outlets
        assert len(outlets) == 1
        vswitch7a = outlets[0]
        assert isinstance(vswitch7a, VeSyncOutlet7A)
        assert vswitch7a.device_name == call_json.Defaults.name(DEVICE_TYPE)
        assert vswitch7a.device_type == DEVICE_TYPE
        assert vswitch7a.cid == call_json.Defaults.cid(DEVICE_TYPE)
        assert vswitch7a.is_on

    def test_7a_details(self):
        """Test get_details() method for 7A outlet."""
        resp_dict, status = CORRECT_7A_DETAILS
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch7a.get_details)
        dev_details = vswitch7a.details
        assert vswitch7a.device_status == 'on'
        assert isinstance(dev_details, dict)
        assert dev_details['active_time'] == 1
        assert dev_details['energy'] == 1
        assert vswitch7a.power == 1
        assert vswitch7a.voltage == 1

    def NO_test_7a_no_devstatus(self):
        """Test 7A outlet details response with no device status key."""
        # Remove test for invalid key - will be addressed by Validation
        bad_7a_details = {
            'deviceImg': '',
            'activeTime': 1,
            'energy': 1,
            'power': '1A:1A',
            'voltage': '1A:1A',
        }
        self.mock_api.return_value = (orjson.dumps(bad_7a_details), 200)
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch7a.get_details)
        assert len(self.caplog.records) == 1
        assert 'details' in self.caplog.text

    def NO_test_7a_no_details(self):
        """Test 7A outlet details response with unknown keys."""
        # Remove test for invalid key - will be addressed by Validation
        bad_7a_details = {'wrongdetails': 'on'}
        self.mock_api.return_value = (orjson.dumps(bad_7a_details), 200)
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch7a.get_details)
        assert len(self.caplog.records) == 1

    def test_7a_onoff(self):
        """Test 7A outlet on/off methods."""
        self.mock_api.return_value = (None, 200)
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.manager)
        on = self.run_in_loop(vswitch7a.turn_on)
        head = Helpers.req_legacy_headers(self.manager)
        self.mock_api.assert_called_with(
            '/v1/wifi-switch-1.3/' + vswitch7a.cid + '/status/on', 'put', headers=head
        )
        assert on
        off = self.run_in_loop(vswitch7a.turn_off)
        self.mock_api.assert_called_with(
            '/v1/wifi-switch-1.3/' + vswitch7a.cid + '/status/off', 'put', headers=head
        )
        assert off

    def test_7a_onoff_fail(self):
        """Test 7A outlet on/off methods that fail."""
        self.mock_api.return_value = (None, 400)
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.manager)
        assert not self.run_in_loop(vswitch7a.turn_on)
        assert not self.run_in_loop(vswitch7a.turn_off)

    def test_7a_weekly(self):
        """Test 7A outlet weekly energy API call and energy dict."""
        resp_dict, status = ENERGY_HISTORY
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch7a.get_weekly_energy)
        self.mock_api.assert_called_with(
            '/v1/device/' + vswitch7a.cid + '/energy/week',
            'get',
            headers=Helpers.req_legacy_headers(self.manager),
        )
        energy_dict = vswitch7a.energy['week']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]

    def test_7a_monthly(self):
        """Test 7A outlet monthly energy API call and energy dict."""
        resp_dict, status = ENERGY_HISTORY
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch7a.get_monthly_energy)
        self.mock_api.assert_called_with(
            '/v1/device/' + vswitch7a.cid + '/energy/month',
            'get',
            headers=Helpers.req_legacy_headers(self.manager),
        )
        energy_dict = vswitch7a.energy['month']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]

    def test_7a_yearly(self):
        """Test 7A outlet yearly energy API call and energy dict."""
        resp_dict, status = ENERGY_HISTORY
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch7a.get_yearly_energy)
        self.mock_api.assert_called_with(
            '/v1/device/' + vswitch7a.cid + '/energy/year',
            'get',
            headers=Helpers.req_legacy_headers(self.manager),
        )
        energy_dict = vswitch7a.energy['year']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]

    def test_history_fail(self):
        """Test handling of energy update failure."""
        bad_history = {'code': 1}
        self.mock_api.return_value = (orjson.dumps(bad_history), 200)
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch7a.update_energy)
        assert len(self.caplog.records) == 1
        assert 'weekly' in self.caplog.text
        self.caplog.clear()
        self.run_in_loop(vswitch7a.get_monthly_energy)
        assert len(self.caplog.records) == 1
        assert 'monthly' in self.caplog.text
        self.caplog.clear()
        self.run_in_loop(vswitch7a.get_yearly_energy)
        assert len(self.caplog.records) == 1
        assert 'yearly' in self.caplog.text
