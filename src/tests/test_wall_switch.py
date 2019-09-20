import pytest
from unittest.mock import patch
import logging
from pyvesync import VeSync, VeSyncWallSwitch
from pyvesync.helpers import Helpers as helpers
from . import call_json

DEV_LIST_DETAIL = call_json.LIST_CONF_WS

CORRECT_WS_LIST = call_json.DEVLIST_WS

ENERGY_HISTORY = call_json.ENERGY_HISTORY

CORRECT_WS_DETAILS = call_json.DETAILS_WS

BAD_LIST = call_json.DETAILS_BADCODE


class TestVesyncWallSwitch(object):
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

    def test_ws_conf(self, api_mock):
        """Tests that Wall Switch is instantiated properly"""
        self.mock_api.return_value = CORRECT_WS_LIST
        devices = self.vesync_obj.get_devices()
        switch = devices[1]
        assert len(switch) == 1
        wswitch = switch[0]
        assert isinstance(wswitch, VeSyncWallSwitch)
        assert wswitch.device_name == "Name Wall Switch"
        assert wswitch.device_type == "ESWL01"
        assert wswitch.cid == "WS-CID"
        assert wswitch.uuid == "UUID"

    def test_ws_details(self, api_mock):
        """Test WS get_details() """
        self.mock_api.return_value = CORRECT_WS_DETAILS
        wswitch = VeSyncWallSwitch(DEV_LIST_DETAIL, self.vesync_obj)
        wswitch.get_details()
        dev_details = wswitch.details
        assert wswitch.device_status == 'on'
        assert type(dev_details) == dict
        assert dev_details['active_time'] == 1
        assert wswitch.connection_status == 'online'

    def test_ws_details_fail(self, caplog, api_mock):
        """Test WS get_details with Code>0"""
        self.mock_api.return_value = BAD_LIST
        vswitch15a = VeSyncWallSwitch(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch15a.get_details()
        assert len(caplog.records) == 1
        assert 'details' in caplog.text

    def test_ws_onoff(self, caplog, api_mock):
        """Test 15A Device On/Off Methods"""
        self.mock_api.return_value = ({"code": 0}, 200)
        wswitch = VeSyncWallSwitch(DEV_LIST_DETAIL, self.vesync_obj)
        head = helpers.req_headers(self.vesync_obj)
        body = helpers.req_body(self.vesync_obj, 'devicestatus')

        body['status'] = 'on'
        body['uuid'] = wswitch.uuid
        on = wswitch.turn_on()
        self.mock_api.assert_called_with(
            '/inwallswitch/v1/device/devicestatus',
            'put',
            headers=head,
            json=body)
        assert on
        off = wswitch.turn_off()
        body['status'] = 'off'
        self.mock_api.assert_called_with(
            '/inwallswitch/v1/device/devicestatus',
            'put',
            headers=head,
            json=body)
        assert off

    def test_ws_onoff_fail(self, api_mock):
        """Test ws On/Off Fail with Code>0"""
        self.mock_api.return_value = ({"code": 1}, 400)
        vswitch15a = VeSyncWallSwitch(DEV_LIST_DETAIL, self.vesync_obj)
        assert not vswitch15a.turn_on()
        assert not vswitch15a.turn_off()
