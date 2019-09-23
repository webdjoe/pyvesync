"""Test scripts for Etekcity 10A Outlets."""

import pytest
from unittest.mock import patch
import logging
from pyvesync import VeSync, VeSyncOutlet10A
from pyvesync.helpers import Helpers as helpers
from . import call_json

DEV_LIST_DETAIL_EU = call_json.LIST_CONF_10AEU
DEV_LIST_DETAIL_US = call_json.LIST_CONF_10AUS
CORRECT_10AUS_LIST = call_json.DEVLIST_10AUS
CORRECT_10AEU_LIST = call_json.DEVLIST_10AEU

ENERGY_HISTORY = call_json.ENERGY_HISTORY

CORRECT_10A_DETAILS = call_json.DETAILS_10A

BAD_10A_LIST = call_json.DETAILS_BADCODE


class TestVesync10ASwitch(object):
    """Test class for 10A outlets."""

    @pytest.fixture()
    def api_mock(self, caplog):
        """Mock call_api() method and initialize VeSync object."""
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

    @pytest.mark.parametrize('mock_return, devtype',
                             [(CORRECT_10AEU_LIST, 'ESW01-EU'),
                              (CORRECT_10AUS_LIST, 'ESW03-USA')])
    def test_10a_conf(self, mock_return, devtype, api_mock):
        """Tests that 10A US & EU Outlet is instantiated properly."""
        self.mock_api.return_value = mock_return
        outlets = self.vesync_obj.get_devices()
        outlets = outlets[0]
        assert len(outlets) == 1
        outlet = outlets[0]
        assert isinstance(outlet, VeSyncOutlet10A)
        assert outlet.device_name == "Name 10A Outlet"
        assert outlet.device_type == devtype
        assert outlet.cid == "10A-CID"
        assert outlet.uuid == "UUID"

    def test_10a_details(self, api_mock):
        """Test 10A get_details()."""
        self.mock_api.return_value = CORRECT_10A_DETAILS
        outlet = VeSyncOutlet10A(DEV_LIST_DETAIL_US, self.vesync_obj)
        outlet.get_details()
        dev_details = outlet.details
        assert outlet.device_status == 'on'
        assert type(dev_details) == dict
        assert dev_details['active_time'] == 1
        assert dev_details['energy'] == 1
        assert dev_details['power'] == '1'
        assert dev_details['voltage'] == '1'
        assert outlet.power == 1
        assert outlet.voltage == 1

    def test_10a_details_fail(self, caplog, api_mock):
        """Test 10A get_details with Code>0."""
        self.mock_api.return_value = BAD_10A_LIST
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_EU, self.vesync_obj)
        out.get_details()
        assert len(caplog.records) == 1
        assert 'details' in caplog.text

    def test_10a_onoff(self, caplog, api_mock):
        """Test 10A Device On/Off Methods."""
        self.mock_api.return_value = ({"code": 0}, 200)
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_EU, self.vesync_obj)
        head = helpers.req_headers(self.vesync_obj)
        body = helpers.req_body(self.vesync_obj, 'devicestatus')

        body['status'] = 'on'
        body['uuid'] = out.uuid
        on = out.turn_on()
        self.mock_api.assert_called_with('/10a/v1/device/devicestatus',
                                         'put',
                                         headers=head,
                                         json=body)
        assert on
        off = out.turn_off()
        body['status'] = 'off'
        self.mock_api.assert_called_with('/10a/v1/device/devicestatus',
                                         'put',
                                         headers=head,
                                         json=body)
        assert off

    def test_10a_onoff_fail(self, api_mock):
        """Test 10A On/Off Fail with Code>0."""
        self.mock_api.return_value = ({"code": 1}, 400)
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_US, self.vesync_obj)
        assert not out.turn_on()
        assert not out.turn_off()

    def test_10a_weekly(self, api_mock):
        """Test 10A get_weekly_energy."""
        self.mock_api.return_value = ENERGY_HISTORY
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_EU, self.vesync_obj)
        out.get_weekly_energy()
        body = helpers.req_body(self.vesync_obj, 'energy_week')
        body['uuid'] = out.uuid
        self.mock_api.assert_called_with('/10a/v1/device/energyweek',
                                         'post',
                                         headers=helpers.req_headers(
                                             self.vesync_obj),
                                         json=body)
        energy_dict = out.energy['week']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert out.weekly_energy_total == 1

    def test_10a_monthly(self, api_mock):
        """Test 10A get_monthly_energy."""
        self.mock_api.return_value = ENERGY_HISTORY
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_EU, self.vesync_obj)
        out.get_monthly_energy()
        body = helpers.req_body(self.vesync_obj, 'energy_month')
        body['uuid'] = out.uuid
        self.mock_api.assert_called_with('/10a/v1/device/energymonth',
                                         'post',
                                         headers=helpers.req_headers(
                                             self.vesync_obj),
                                         json=body)
        energy_dict = out.energy['month']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert out.monthly_energy_total == 1

    def test_10a_yearly(self, api_mock):
        """Test 10A get_yearly_energy."""
        self.mock_api.return_value = ENERGY_HISTORY
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_US, self.vesync_obj)
        out.get_yearly_energy()
        body = helpers.req_body(self.vesync_obj, 'energy_year')
        body['uuid'] = out.uuid
        self.mock_api.assert_called_with('/10a/v1/device/energyyear',
                                         'post',
                                         headers=helpers.req_headers(
                                             self.vesync_obj),
                                         json=body)
        energy_dict = out.energy['year']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert out.yearly_energy_total == 1

    def test_history_fail(self, caplog, api_mock):
        """Test 15A energy failure."""
        bad_history = {"code": 1}
        self.mock_api.return_value = (bad_history, 200)
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_US, self.vesync_obj)
        out.update_energy()
        assert len(caplog.records) == 1
        assert 'weekly' in caplog.text
        caplog.clear()
        out.get_monthly_energy()
        assert len(caplog.records) == 1
        assert 'monthly' in caplog.text
        caplog.clear()
        out.get_yearly_energy()
        assert len(caplog.records) == 1
        assert 'yearly' in caplog.text
