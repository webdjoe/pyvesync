"""Levoit Air Purifier tests."""

import pytest
from unittest.mock import patch
import logging
from pyvesync import VeSync, VeSyncAir131
from pyvesync.helpers import Helpers as helpers
from . import call_json

DEV_LIST_DETAIL = call_json.LIST_CONF_AIR

CORRECT_LIST = call_json.DEVLIST_AIR

ENERGY_HISTORY = call_json.ENERGY_HISTORY

CORRECT_DETAILS = call_json.DETAILS_AIR

BAD_LIST = call_json.DETAILS_BADCODE


class TestVesyncAirPurifier(object):
    """Air purifier tests."""

    @pytest.fixture()
    def api_mock(self, caplog):
        """Mock call_api and initialize VeSync object."""
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

    def test_airpur_conf(self, api_mock):
        """Tests that 15A Outlet is instantiated properly."""
        self.mock_api.return_value = CORRECT_LIST
        fans = self.vesync_obj.get_devices()
        fan = fans[2]
        assert len(fan) == 1
        fan = fan[0]
        assert isinstance(fan, VeSyncAir131)
        assert fan.device_name == "Name Air Purifier"
        assert fan.device_type == "LV-PUR131S"
        assert fan.cid == "AIRPUR-CID"
        assert fan.uuid == "UUID"

    def test_airpur_details(self, api_mock):
        """Test 15A get_details()."""
        self.mock_api.return_value = CORRECT_DETAILS
        fan = VeSyncAir131(DEV_LIST_DETAIL, self.vesync_obj)
        fan.get_details()
        dev_details = fan.details
        assert fan.device_status == 'on'
        assert type(dev_details) == dict
        assert dev_details['active_time'] == 1
        assert fan.filter_life == 100
        assert dev_details['screen_status'] == 'on'
        assert fan.mode == 'manual'
        assert dev_details['level'] == 1
        assert fan.fan_level == 1
        assert dev_details['air_quality'] == 'excellent'
        assert fan.air_quality == 'excellent'

    def test_airpur_details_fail(self, caplog, api_mock):
        """Test Air Purifier get_details with Code>0."""
        self.mock_api.return_value = BAD_LIST
        fan = VeSyncAir131(DEV_LIST_DETAIL, self.vesync_obj)
        fan.get_details()
        assert len(caplog.records) == 1
        assert 'details' in caplog.text

    def test_airpur_onoff(self, caplog, api_mock):
        """Test Air Purifier Device On/Off Methods."""
        self.mock_api.return_value = ({"code": 0}, 200)
        fan = VeSyncAir131(DEV_LIST_DETAIL, self.vesync_obj)
        head = helpers.req_headers(self.vesync_obj)
        body = helpers.req_body(self.vesync_obj, 'devicestatus')
        fan.device_status = 'off'
        body['status'] = 'on'
        body['uuid'] = fan.uuid
        on = fan.turn_on()
        self.mock_api.assert_called_with(
            '/131airPurifier/v1/device/deviceStatus', 'put',
            json=body, headers=head)
        call_args = self.mock_api.call_args_list[0][0]
        assert call_args[0] == '/131airPurifier/v1/device/deviceStatus'
        assert call_args[1] == 'put'
        assert on
        fan.device_status = 'on'
        off = fan.turn_off()
        body['status'] = 'off'
        self.mock_api.assert_called_with(
            '/131airPurifier/v1/device/deviceStatus', 'put',
            json=body, headers=head)
        assert off

    def test_airpur_onoff_fail(self, api_mock):
        """Test Air Purifier On/Off Fail with Code>0."""
        self.mock_api.return_value = ({"code": 1}, 400)
        vswitch15a = VeSyncAir131(DEV_LIST_DETAIL, self.vesync_obj)
        assert not vswitch15a.turn_on()
        assert not vswitch15a.turn_off()

    def test_airpur_fanspeed(self, caplog, api_mock):
        """Test changing fan speed of."""
        self.mock_api.return_value = ({'code': 0}, 200)
        fan = VeSyncAir131(DEV_LIST_DETAIL, self.vesync_obj)
        fan.details['level'] = 1
        b = fan.change_fan_speed()
        assert fan.fan_level == 2
        b = fan.change_fan_speed()
        assert fan.fan_level == 3
        b = fan.change_fan_speed()
        assert fan.fan_level == 1
        assert b
        b = fan.change_fan_speed(2)
        assert b
        assert fan.fan_level == 2

    def test_mode_toggle(self, caplog, api_mock):
        """Test changing modes on air purifier."""
        self.mock_api.return_value = ({'code': 0}, 200)
        fan = VeSyncAir131(DEV_LIST_DETAIL, self.vesync_obj)
        f = fan.auto_mode()
        assert f
        assert fan.mode == 'auto'
        f = fan.manual_mode()
        assert fan.mode == 'manual'
        assert f
        f = fan.sleep_mode()
        assert fan.mode == 'sleep'
        assert f
