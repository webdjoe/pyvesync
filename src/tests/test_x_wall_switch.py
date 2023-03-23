import pytest
from unittest.mock import patch
import logging
from pyvesync import VeSync
from pyvesync.vesyncswitch import VeSyncWallSwitch
from pyvesync.helpers import Helpers as helpers
import call_json
import call_json_switches

DEVICE_TYPE = 'ESWL01'

DEV_LIST_DETAIL = call_json.DeviceList.device_list_item(DEVICE_TYPE)

CORRECT_WS_LIST = call_json.DeviceList.device_list_response(DEVICE_TYPE)

CORRECT_WS_DETAILS = call_json_switches.DETAILS_RESPONSES[DEVICE_TYPE]

BAD_LIST = call_json.DETAILS_BADCODE

DEFAULTS = call_json.Defaults


class TestVesyncWallSwitch(object):
    @pytest.fixture()
    def api_mock(self, caplog):
        self.mock_api_call = patch('pyvesync.helpers.Helpers.call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospect()
        self.mock_api.return_value.ok = True
        self.vesync_obj = VeSync('sam@mail.com', 'pass', debug=True)
        self.vesync_obj.enabled = True
        self.vesync_obj.login = True
        self.vesync_obj.token = DEFAULTS.token
        self.vesync_obj.account_id = DEFAULTS.account_id
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    def test_ws_conf(self, api_mock):
        """Tests that Wall Switch is instantiated properly"""
        self.mock_api.return_value = CORRECT_WS_LIST
        self.vesync_obj.get_devices()
        switch = self.vesync_obj.switches
        assert len(switch) == 1
        wswitch = switch[0]
        assert isinstance(wswitch, VeSyncWallSwitch)
        assert wswitch.device_name == DEFAULTS.name(DEVICE_TYPE)
        assert wswitch.device_type == DEVICE_TYPE
        assert wswitch.cid == DEFAULTS.cid(DEVICE_TYPE)
        assert wswitch.uuid == DEFAULTS.uuid(DEVICE_TYPE)

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
        self.mock_api.return_value = ({'code': 0}, 200)
        wswitch = VeSyncWallSwitch(DEV_LIST_DETAIL, self.vesync_obj)
        head = helpers.req_headers(self.vesync_obj)
        body = helpers.req_body(self.vesync_obj, 'devicestatus')

        body['status'] = 'on'
        body['uuid'] = wswitch.uuid
        on = wswitch.turn_on()
        self.mock_api.assert_called_with(
            '/inwallswitch/v1/device/devicestatus', 'put', headers=head, json_object=body
        )
        assert on
        off = wswitch.turn_off()
        body['status'] = 'off'
        self.mock_api.assert_called_with(
            '/inwallswitch/v1/device/devicestatus', 'put', headers=head, json_object=body
        )
        assert off

    def test_ws_onoff_fail(self, api_mock):
        """Test ws On/Off Fail with Code>0"""
        self.mock_api.return_value = ({'code': 1}, 400)
        vswitch15a = VeSyncWallSwitch(DEV_LIST_DETAIL, self.vesync_obj)
        assert not vswitch15a.turn_on()
        assert not vswitch15a.turn_off()
