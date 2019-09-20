import pytest
from unittest.mock import patch
import logging
from pyvesync import VeSync, VeSyncOutlet15A
from pyvesync.helpers import Helpers as helpers
from . import call_json

DEV_LIST_DETAIL = call_json.LIST_CONF_15A

CORRECT_15A_LIST = call_json.DEVLIST_15A

ENERGY_HISTORY = call_json.ENERGY_HISTORY

CORRECT_15A_DETAILS = call_json.DETAILS_15A

BAD_15A_LIST = call_json.DETAILS_BADCODE


class TestVesync15ASwitch(object):
    @pytest.fixture()
    def api_mock(self, caplog):
        self.mock_api_call = patch('pyvesync.helpers.Helpers.call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospect()
        self.mock_api.return_value.ok = True
        self.vesync_obj = VeSync('sam@mail.com', 'pass')
        self.vesync_obj.enabled = True
        self.vesync_obj.login = True
        self.vesync_obj.token = 'sample_tk'
        self.vesync_obj.account_id = 'sample_actid'
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    def test_15aswitch_conf(self, api_mock):
        """Tests that 15A Outlet is instantiated properly"""
        self.mock_api.return_value = CORRECT_15A_LIST
        outlets = self.vesync_obj.get_devices()
        outlets = outlets[0]
        assert len(outlets) == 1
        vswitch15a = outlets[0]
        assert isinstance(vswitch15a, VeSyncOutlet15A)
        assert vswitch15a.device_name == "Name 15A Outlet"
        assert vswitch15a.device_type == "ESW15-USA"
        assert vswitch15a.cid == "15A-CID"
        assert vswitch15a.uuid == "UUID"

    def test_15a_details(self, api_mock):
        """Test 15A get_details() """
        self.mock_api.return_value = CORRECT_15A_DETAILS
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch15a.get_details()
        dev_details = vswitch15a.details
        assert vswitch15a.device_status == 'on'
        assert type(dev_details) == dict
        assert dev_details['active_time'] == 1
        assert dev_details['energy'] == 1
        assert dev_details['power'] == '1'
        assert dev_details['voltage'] == '1'
        assert vswitch15a.power == 1
        assert vswitch15a.voltage == 1
        assert vswitch15a.active_time == 1
        assert vswitch15a.energy_today == 1

    def test_15a_details_fail(self, caplog, api_mock):
        """Test 15A get_details with Code>0"""
        self.mock_api.return_value = BAD_15A_LIST
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch15a.get_details()
        assert len(caplog.records) == 1
        assert 'details' in caplog.text

    def test_15a_no_details(self, caplog, api_mock):
        """Test 15A details return with no details and code=0"""
        bad_15a_details = {
            "code": 0,
            "deviceStatus": "on"
        }
        self.mock_api.return_value = (bad_15a_details, 200)
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch15a.get_details()
        assert len(caplog.records) == 1

    def test_15a_onoff(self, caplog, api_mock):
        """Test 15A Device On/Off Methods"""
        self.mock_api.return_value = ({"code": 0}, 200)
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.vesync_obj)
        head = helpers.req_headers(self.vesync_obj)
        body = helpers.req_body(self.vesync_obj, 'devicestatus')

        body['status'] = 'on'
        body['uuid'] = vswitch15a.uuid
        on = vswitch15a.turn_on()
        self.mock_api.assert_called_with(
            '/15a/v1/device/devicestatus', 'put', headers=head, json=body)
        assert on
        off = vswitch15a.turn_off()
        body['status'] = 'off'
        self.mock_api.assert_called_with(
            '/15a/v1/device/devicestatus', 'put', headers=head, json=body)
        assert off

    def test_15a_onoff_fail(self, api_mock):
        """Test 15A On/Off Fail with Code>0"""
        self.mock_api.return_value = ({"code": 1}, 400)
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.vesync_obj)
        assert not vswitch15a.turn_on()
        assert not vswitch15a.turn_off()

    def test_15a_weekly(self, api_mock):
        """Test 15A get_weekly_energy"""
        self.mock_api.return_value = ENERGY_HISTORY
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch15a.get_weekly_energy()
        body = helpers.req_body(self.vesync_obj, 'energy_week')
        body['uuid'] = vswitch15a.uuid
        self.mock_api.assert_called_with(
            '/15a/v1/device/energyweek', 'post',
            headers=helpers.req_headers(self.vesync_obj), json=body)
        energy_dict = vswitch15a.energy['week']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert vswitch15a.weekly_energy_total == 1

    def test_15a_monthly(self, api_mock):
        """Test 15A get_monthly_energy"""
        self.mock_api.return_value = ENERGY_HISTORY
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch15a.get_monthly_energy()
        body = helpers.req_body(self.vesync_obj, 'energy_month')
        body['uuid'] = vswitch15a.uuid
        self.mock_api.assert_called_with(
            '/15a/v1/device/energymonth', 'post',
            headers=helpers.req_headers(self.vesync_obj), json=body)
        energy_dict = vswitch15a.energy['month']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert vswitch15a.monthly_energy_total == 1

    def test_15a_yearly(self, api_mock):
        """Test 15A get_yearly_energy"""
        self.mock_api.return_value = ENERGY_HISTORY
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch15a.get_yearly_energy()
        body = helpers.req_body(self.vesync_obj, 'energy_year')
        body['uuid'] = vswitch15a.uuid
        self.mock_api.assert_called_with(
            '/15a/v1/device/energyyear', 'post',
            headers=helpers.req_headers(self.vesync_obj), json=body)
        energy_dict = vswitch15a.energy['year']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert vswitch15a.yearly_energy_total == 1

    def test_history_fail(self, caplog, api_mock):
        """Test 15A energy failure"""
        bad_history = {"code": 1}
        self.mock_api.return_value = (bad_history, 200)
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch15a.update_energy()
        assert len(caplog.records) == 1
        assert 'weekly' in caplog.text
        caplog.clear()
        vswitch15a.get_monthly_energy()
        assert len(caplog.records) == 1
        assert 'monthly' in caplog.text
        caplog.clear()
        vswitch15a.get_yearly_energy()
        assert len(caplog.records) == 1
        assert 'yearly' in caplog.text
