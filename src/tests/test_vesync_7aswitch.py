"""Etekcity 7A Outlet tests."""

import logging
from unittest.mock import patch

import pytest
import pyvesync
from pyvesync import VeSync, VeSyncOutlet7A
from pyvesync.helpers import Helpers as helpers

from . import call_json

DEV_LIST_DETAIL = call_json.LIST_CONF_7A

CORRECT_7A_LIST = call_json.DEVLIST_7A

CORRECT_7A_DETAILS = call_json.DETAILS_7A

ENERGY_HISTORY = call_json.ENERGY_HISTORY


class TestVesync7ASwitch(object):
    """Test 7A outlet API."""

    @pytest.fixture()
    def api_mock(self, caplog):
        """Mock call_api() and initialize VeSync object."""
        self.mock_api_call = patch.object(pyvesync.helpers.Helpers,
                                          'call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospect()
        self.mock_api.return_value.ok = True
        self.vesync_obj = VeSync('sam@mail.com', 'pass')
        self.vesync_obj.enabled = True
        self.vesync_obj.login = True
        self.vesync_obj.tk = 'sample_tk'
        self.vesync_obj.account_id = 'sample_actid'
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    def test_7aswitch_conf(self, api_mock):
        """Test inizialization of 7A outlet."""
        self.mock_api.return_value = CORRECT_7A_LIST
        devs = self.vesync_obj.get_devices()
        assert len(devs) == 4
        vswitch7a = devs[0][0]
        assert isinstance(vswitch7a, VeSyncOutlet7A)
        assert vswitch7a.device_name == "Name 7A Outlet"
        assert vswitch7a.device_type == "wifi-switch-1.3"
        assert vswitch7a.cid == "7A-CID"
        assert vswitch7a.is_on

    def test_7a_details(self, api_mock):
        """Test get_details() method for 7A outlet."""
        self.mock_api.return_value = CORRECT_7A_DETAILS
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.get_details()
        dev_details = vswitch7a.details
        assert vswitch7a.device_status == 'on'
        assert type(dev_details) == dict
        assert dev_details['active_time'] == 1
        assert dev_details['energy'] == 1
        assert vswitch7a.power == 1
        assert vswitch7a.voltage == 1

    def test_7a_no_devstatus(self, caplog, api_mock):
        """Test 7A outlet details response with no device status key."""
        bad_7a_details = {
            "deviceImg": "",
            "activeTime": 1,
            "energy": 1,
            "power": "1A:1A",
            "voltage": "1A:1A"
        }
        self.mock_api.return_value = (bad_7a_details, 200)
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.get_details()
        assert len(caplog.records) == 1
        assert 'details' in caplog.text

    def test_7a_no_details(self, caplog, api_mock):
        """Test 7A outlet details response with unknown keys."""
        bad_7a_details = {
            "wrongdetails": "on"
        }
        self.mock_api.return_value = (bad_7a_details, 200)
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.get_details()
        assert len(caplog.records) == 1

    def test_7a_onoff(self, caplog, api_mock):
        """Test 7A outlet on/off methods."""
        self.mock_api.return_value = ("response", 200)
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.vesync_obj)
        on = vswitch7a.turn_on()
        head = helpers.req_headers(self.vesync_obj)
        self.mock_api.assert_called_with(
            '/v1/wifi-switch-1.3/' + vswitch7a.cid + '/status/on', 'put',
            headers=head)
        assert on
        off = vswitch7a.turn_off()
        self.mock_api.assert_called_with(
                '/v1/wifi-switch-1.3/' + vswitch7a.cid + '/status/off', 'put',
                headers=head)
        assert off

    def test_7a_onoff_fail(self, api_mock):
        """Test 7A outlet on/off methods that fail."""
        self.mock_api.return_value = ('response', 400)
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.vesync_obj)
        assert not vswitch7a.turn_on()
        assert not vswitch7a.turn_off()

    def test_7a_weekly(self, api_mock):
        """Test 7A outlet weekly energy API call and energy dict."""
        self.mock_api.return_value = ENERGY_HISTORY
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.get_weekly_energy()
        self.mock_api.assert_called_with(
            '/v1/device/' + vswitch7a.cid + '/energy/week',
            'get',
            headers=helpers.req_headers(self.vesync_obj))
        energy_dict = vswitch7a.energy['week']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]

    def test_7a_monthly(self, api_mock):
        """Test 7A outlet monthly energy API call and energy dict."""
        self.mock_api.return_value = ENERGY_HISTORY
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.get_monthly_energy()
        self.mock_api.assert_called_with(
            '/v1/device/' + vswitch7a.cid + '/energy/month',
            'get',
            headers=helpers.req_headers(self.vesync_obj))
        energy_dict = vswitch7a.energy['month']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]

    def test_7a_yearly(self, api_mock):
        """Test 7A outlet yearly energy API call and energy dict."""
        self.mock_api.return_value = ENERGY_HISTORY
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.get_yearly_energy()
        self.mock_api.assert_called_with(
            '/v1/device/' + vswitch7a.cid + '/energy/year',
            'get',
            headers=helpers.req_headers(self.vesync_obj))
        energy_dict = vswitch7a.energy['year']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]

    def test_history_fail(self, caplog, api_mock):
        """Test handling of energy update failure."""
        bad_history = {"code": 1}
        self.mock_api.return_value = (bad_history, 200)
        vswitch7a = VeSyncOutlet7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.update_energy()
        assert len(caplog.records) == 1
        assert 'weekly' in caplog.text
        caplog.clear()
        vswitch7a.get_monthly_energy()
        assert len(caplog.records) == 1
        assert 'monthly' in caplog.text
        caplog.clear()
        vswitch7a.get_yearly_energy()
        assert len(caplog.records) == 1
        assert 'yearly' in caplog.text
