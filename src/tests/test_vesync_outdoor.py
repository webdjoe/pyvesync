"""Test scripts for Etekcity Outdoor Outlet."""

import pytest
from unittest.mock import patch
import logging
from pyvesync import VeSync, VeSyncOutdoorPlug
from pyvesync.helpers import Helpers as helpers
from . import call_json

DEV_LIST_DETAIL = call_json.LIST_CONF_OUTDOOR_1

DEV_LIST_DETAIL_2 = call_json.LIST_CONF_OUTDOOR_2

CORRECT_OUTDOOR_LIST = call_json.DEVLIST_OUTDOOR

ENERGY_HISTORY = call_json.ENERGY_HISTORY

CORRECT_OUTDOOR_DETAILS = call_json.DETAILS_OUTDOOR

BAD_OUTDOOR_LIST = call_json.DETAILS_BADCODE


class TestVesyncOutdoorPlug:
    """Test class for outdoor outlet."""

    @pytest.fixture()
    def api_mock(self, caplog):
        """Mock call_api and initialize VeSync object."""
        self.mock_api_call = patch('pyvesync.helpers.Helpers.call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospec()
        self.mock_api.return_value.ok = True
        self.vesync_obj = VeSync('sam@mail.com', 'pass')
        self.vesync_obj.enabled = True
        self.vesync_obj.login = True
        self.vesync_obj.token = 'sample_tk'
        self.vesync_obj.account_id = 'sample_actid'
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    def test_outdoor_conf(self, api_mock):
        """Tests outdoor outlet is instantiated properly."""
        self.mock_api.return_value = CORRECT_OUTDOOR_LIST
        outlets = self.vesync_obj.get_devices()
        outlets = outlets[0]
        assert len(outlets) == 2
        outdoor_outlet = outlets[0]
        assert isinstance(outdoor_outlet, VeSyncOutdoorPlug)
        assert outdoor_outlet.device_type == 'ESO15-TB'
        assert outdoor_outlet.uuid == 'UUID'

    def test_outdoor_details(self, api_mock):
        """Tests retrieving outdoor outlet details."""
        self.mock_api.return_value = CORRECT_OUTDOOR_DETAILS
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.vesync_obj)
        outdoor_outlet.get_details()
        dev_details = outdoor_outlet.details
        assert outdoor_outlet.device_status == 'on'
        assert isinstance(outdoor_outlet, VeSyncOutdoorPlug)
        assert dev_details['active_time'] == 1

    def test_outdoor_details_fail(self, caplog, api_mock):
        """Test outdoor outlet get_details response."""
        self.mock_api.return_value = BAD_OUTDOOR_LIST
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.vesync_obj)
        outdoor_outlet.get_details()
        assert len(caplog.records) == 1
        assert 'details' in caplog.text

    def test_outdoor_outlet_onoff(self, caplog, api_mock):
        """Test Outdoor Outlet Device On/Off Methods."""
        self.mock_api.return_value = ({"code": 0}, 200)
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.vesync_obj)
        head = helpers.req_headers(self.vesync_obj)
        body = helpers.req_body(self.vesync_obj, 'devicestatus')

        body['status'] = 'on'
        body['uuid'] = outdoor_outlet.uuid
        body['switchNo'] = outdoor_outlet.sub_device_no
        on = outdoor_outlet.turn_on()
        self.mock_api.assert_called_with(
            '/outdoorsocket15a/v1/device/devicestatus',
            'put',
            headers=head,
            json=body
            )
        assert on
        off = outdoor_outlet.turn_off()
        body['status'] = 'off'
        self.mock_api.assert_called_with(
            '/outdoorsocket15a/v1/device/devicestatus',
            'put',
            headers=head,
            json=body
            )
        assert off

    def test_outdoor_outlet_onoff_fail(self, api_mock):
        """Test outdoor outlet On/Off Fail with Code>0."""
        self.mock_api.return_value = ({"code": 1}, 400)
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.vesync_obj)
        assert not outdoor_outlet.turn_on()
        assert not outdoor_outlet.turn_off()

    def test_outdoor_outlet_weekly(self, api_mock):
        """Test outdoor outlet get_weekly_energy."""
        self.mock_api.return_value = ENERGY_HISTORY
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.vesync_obj)
        outdoor_outlet.get_weekly_energy()
        body = helpers.req_body(self.vesync_obj, 'energy_week')
        body['uuid'] = outdoor_outlet.uuid
        self.mock_api.assert_called_with(
            '/outdoorsocket15a/v1/device/energyweek', 'post',
            headers=helpers.req_headers(self.vesync_obj), json=body)
        energy_dict = outdoor_outlet.energy['week']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert outdoor_outlet.weekly_energy_total == 1

    def test_outdoor_outlet_monthly(self, api_mock):
        """Test outdoor outlet get_monthly_energy."""
        self.mock_api.return_value = ENERGY_HISTORY
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.vesync_obj)
        outdoor_outlet.get_monthly_energy()
        body = helpers.req_body(self.vesync_obj, 'energy_month')
        body['uuid'] = outdoor_outlet.uuid
        self.mock_api.assert_called_with(
            '/outdoorsocket15a/v1/device/energymonth',
            'post',
            headers=helpers.req_headers(self.vesync_obj),
            json=body)
        energy_dict = outdoor_outlet.energy['month']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert outdoor_outlet.monthly_energy_total == 1

    def test_outdoor_outlet_yearly(self, api_mock):
        """Test outdoor outlet get_yearly_energy."""
        self.mock_api.return_value = ENERGY_HISTORY
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.vesync_obj)
        outdoor_outlet.get_yearly_energy()
        body = helpers.req_body(self.vesync_obj, 'energy_year')
        body['uuid'] = outdoor_outlet.uuid
        self.mock_api.assert_called_with(
            '/outdoorsocket15a/v1/device/energyyear',
            'post',
            headers=helpers.req_headers(self.vesync_obj),
            json=body)
        energy_dict = outdoor_outlet.energy['year']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert outdoor_outlet.yearly_energy_total == 1

    def test_history_fail(self, caplog, api_mock):
        """Test outdoor outlet energy failure."""
        bad_history = {"code": 1}
        self.mock_api.return_value = (bad_history, 200)
        outdoor_outlet = VeSyncOutdoorPlug(DEV_LIST_DETAIL, self.vesync_obj)
        outdoor_outlet.update_energy()
        assert len(caplog.records) == 1
        assert 'weekly' in caplog.text
        caplog.clear()
        outdoor_outlet.get_monthly_energy()
        assert len(caplog.records) == 1
        assert 'monthly' in caplog.text
        caplog.clear()
        outdoor_outlet.get_yearly_energy()
        assert len(caplog.records) == 1
        assert 'yearly' in caplog.text
