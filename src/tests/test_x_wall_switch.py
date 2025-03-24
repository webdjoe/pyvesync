import orjson
import pytest
from unittest.mock import patch
import logging
from pyvesync import VeSync
from pyvesync.devices.vesyncswitch import VeSyncWallSwitch
from pyvesync.utils.helpers import Helpers as Helpers
import call_json
import call_json_switches
from utils import TestBase

DEVICE_TYPE = 'ESWL01'

DEV_LIST_DETAIL = call_json.DeviceList.device_list_item(DEVICE_TYPE)

CORRECT_WS_LIST = call_json.DeviceList.device_list_response(DEVICE_TYPE)

CORRECT_WS_DETAILS = call_json_switches.DETAILS_RESPONSES[DEVICE_TYPE]

BAD_LIST = call_json.DETAILS_BADCODE

DEFAULTS = call_json.Defaults


class TestVesyncWallSwitch(TestBase):
    # @pytest.fixture()
    # def api_mock(self, caplog):
    #     self.mock_api_call = patch('pyvesync.vesync.VeSync.async_call_api')
    #     self.mock_api = self.mock_api_call.start()
    #     self.mock_api.create_autospect()
    #     self.mock_api.return_value.ok = True
    #     self.vesync_obj = VeSync('sam@mail.com', 'pass', debug=True)
    #     self.vesync_obj.enabled = True
    #     self.vesync_obj.login = True
    #     self.vesync_obj.token = DEFAULTS.token
    #     self.vesync_obj.account_id = DEFAULTS.account_id
    #     caplog.set_level(logging.DEBUG)
    #     yield
    #     self.mock_api_call.stop()

    def test_ws_conf(self):
        """Tests that Wall Switch is instantiated properly"""
        self.mock_api.return_value = CORRECT_WS_LIST
        self.run_in_loop(self.manager.get_devices)
        switch = self.manager.switches
        assert len(switch) == 1
        wswitch = switch[0]
        assert isinstance(wswitch, VeSyncWallSwitch)
        assert wswitch.device_name == DEFAULTS.name(DEVICE_TYPE)
        assert wswitch.device_type == DEVICE_TYPE
        assert wswitch.cid == DEFAULTS.cid(DEVICE_TYPE)
        assert wswitch.uuid == DEFAULTS.uuid(DEVICE_TYPE)

    def test_ws_details(self):
        """Test WS get_details() """
        resp_dict, status = CORRECT_WS_DETAILS
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        wswitch = VeSyncWallSwitch(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(wswitch.get_details)
        dev_details = wswitch.details
        assert wswitch.device_status == 'on'
        assert isinstance(dev_details, dict)
        assert dev_details['active_time'] == 1
        assert wswitch.connection_status == 'online'

    def test_ws_details_fail(self, caplog):
        """Test WS get_details with Code>0"""
        resp_dict, status = BAD_LIST
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        vswitch15a = VeSyncWallSwitch(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(vswitch15a.get_details)
        assert len(caplog.records) == 1
        assert 'details' in caplog.text

    def test_ws_onoff(self, caplog):
        """Test 15A Device On/Off Methods"""
        self.mock_api.return_value = (orjson.dumps({'code': 0}), 200)
        wswitch = VeSyncWallSwitch(DEV_LIST_DETAIL, self.manager)
        head = Helpers.req_headers(self.manager)
        body = Helpers.req_body(self.manager, 'devicestatus')

        body['status'] = 'on'
        body['uuid'] = wswitch.uuid
        on = self.run_in_loop(wswitch.turn_on)
        self.mock_api.assert_called_with(
            '/inwallswitch/v1/device/devicestatus', 'put', headers=head, json_object=body
        )
        assert on
        off = self.run_in_loop(wswitch.turn_off)
        body['status'] = 'off'
        self.mock_api.assert_called_with(
            '/inwallswitch/v1/device/devicestatus', 'put', headers=head, json_object=body
        )
        assert off

    def test_ws_onoff_fail(self):
        """Test ws On/Off Fail with Code>0"""
        self.mock_api.return_value = (orjson.dumps({'code': 1}), 400)
        vswitch15a = VeSyncWallSwitch(DEV_LIST_DETAIL, self.manager)
        assert not self.run_in_loop(vswitch15a.turn_on)
        assert not self.run_in_loop(vswitch15a.turn_off)
