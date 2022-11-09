"""Test scripts for Etekcity 10A Outlets."""

import pytest
from unittest.mock import patch
import logging
from pyvesync import VeSync, VeSyncOutlet10A
from pyvesync.helpers import Helpers as helpers
import call_json
import call_json_outlets
from utils import Defaults, TestBase

OutletDefaults = call_json_outlets.OutletDefaults

DEV_TYPE_US = 'ESW03-USA'
DEV_TYPE_EU = 'ESW01-EU'
DEV_LIST_DETAIL_EU = call_json.DeviceList.device_list_item(DEV_TYPE_EU)
DEV_LIST_DETAIL_US = call_json.DeviceList.device_list_item(DEV_TYPE_US)
CORRECT_10AUS_LIST = call_json.DeviceList.device_list_response(DEV_TYPE_US)
CORRECT_10AEU_LIST = call_json.DeviceList.device_list_response(DEV_TYPE_EU)

ENERGY_HISTORY = call_json_outlets.ENERGY_HISTORY

CORRECT_10A_DETAILS = call_json_outlets.DETAILS_RESPONSES[DEV_TYPE_US]

BAD_10A_LIST = call_json.DETAILS_BADCODE


class TestVesync10ASwitch(TestBase):
    """Test class for 10A outlets."""

    @pytest.mark.parametrize(
        'mock_return, devtype',
        [(CORRECT_10AEU_LIST, DEV_TYPE_EU), (CORRECT_10AUS_LIST, DEV_TYPE_US)],
    )
    def test_10a_conf(self, mock_return, devtype):
        """Tests that 10A US & EU Outlet is instantiated properly."""
        self.mock_api.return_value = mock_return
        self.manager.get_devices()
        outlets = self.manager.outlets
        assert len(outlets) == 1
        outlet = outlets[0]
        assert isinstance(outlet, VeSyncOutlet10A)
        assert outlet.device_name == Defaults.name(devtype)
        assert outlet.device_type == devtype
        assert outlet.cid == Defaults.cid(devtype)
        assert outlet.uuid == Defaults.uuid(devtype)

    def test_10a_details(self):
        """Test 10A get_details()."""
        self.mock_api.return_value = CORRECT_10A_DETAILS
        outlet = VeSyncOutlet10A(DEV_LIST_DETAIL_US, self.manager)
        outlet.get_details()
        dev_details = outlet.details
        assert outlet.device_status == 'on'
        assert type(dev_details) == dict
        assert dev_details['active_time'] == Defaults.active_time
        assert dev_details['energy'] == OutletDefaults.energy
        assert dev_details['power'] == OutletDefaults.power
        assert dev_details['voltage'] == OutletDefaults.voltage
        assert outlet.power == OutletDefaults.power
        assert outlet.voltage == OutletDefaults.voltage

    def test_10a_details_fail(self):
        """Test 10A get_details with Code>0."""
        self.mock_api.return_value = BAD_10A_LIST
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_EU, self.manager)
        out.get_details()
        assert len(self.caplog.records) == 1
        assert 'details' in self.caplog.text

    def test_10a_onoff(self):
        """Test 10A Device On/Off Methods."""
        self.mock_api.return_value = ({'code': 0}, 200)
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_EU, self.manager)
        head = helpers.req_headers(self.manager)
        body = helpers.req_body(self.manager, 'devicestatus')

        body['status'] = 'on'
        body['uuid'] = out.uuid
        on = out.turn_on()
        self.mock_api.assert_called_with(
            '/10a/v1/device/devicestatus', 'put', headers=head, json_object=body
        )
        assert on
        off = out.turn_off()
        body['status'] = 'off'
        self.mock_api.assert_called_with(
            '/10a/v1/device/devicestatus', 'put', headers=head, json_object=body
        )
        assert off

    def test_10a_onoff_fail(self):
        """Test 10A On/Off Fail with Code>0."""
        self.mock_api.return_value = ({'code': 1}, 400)
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_US, self.manager)
        assert not out.turn_on()
        assert not out.turn_off()

    def test_10a_weekly(self):
        """Test 10A get_weekly_energy."""
        self.mock_api.return_value = ENERGY_HISTORY
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_EU, self.manager)
        out.get_weekly_energy()
        body = helpers.req_body(self.manager, 'energy_week')
        body['uuid'] = out.uuid
        self.mock_api.assert_called_with(
            '/10a/v1/device/energyweek',
            'post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )
        energy_dict = out.energy['week']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert out.weekly_energy_total == 1

    def test_10a_monthly(self):
        """Test 10A get_monthly_energy."""
        self.mock_api.return_value = ENERGY_HISTORY
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_EU, self.manager)
        out.get_monthly_energy()
        body = helpers.req_body(self.manager, 'energy_month')
        body['uuid'] = out.uuid
        self.mock_api.assert_called_with(
            '/10a/v1/device/energymonth',
            'post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )
        energy_dict = out.energy['month']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert out.monthly_energy_total == 1

    def test_10a_yearly(self):
        """Test 10A get_yearly_energy."""
        self.mock_api.return_value = ENERGY_HISTORY
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_US, self.manager)
        out.get_yearly_energy()
        body = helpers.req_body(self.manager, 'energy_year')
        body['uuid'] = out.uuid
        self.mock_api.assert_called_with(
            '/10a/v1/device/energyyear',
            'post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )
        energy_dict = out.energy['year']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert out.yearly_energy_total == 1

    def test_history_fail(self):
        """Test 15A energy failure."""
        bad_history = {'code': 1}
        self.mock_api.return_value = (bad_history, 200)
        out = VeSyncOutlet10A(DEV_LIST_DETAIL_US, self.manager)
        out.update_energy()
        assert len(self.caplog.records) == 1
        assert 'weekly' in self.caplog.text
        self.caplog.clear()
        out.get_monthly_energy()
        assert len(self.caplog.records) == 1
        assert 'monthly' in self.caplog.text
        self.caplog.clear()
        out.get_yearly_energy()
        assert len(self.caplog.records) == 1
        assert 'yearly' in self.caplog.text
