"""Test VeSync manager methods."""

import pytest
from unittest.mock import patch, NonCallableMagicMock
import pyvesync
import logging
import copy
import time
from itertools import chain
from pyvesync.helpers import EDeviceFamily
from pyvesync.vesyncfan import *
from pyvesync.vesyncbulb import *
from pyvesync.vesyncoutlet import *
from pyvesync.vesyncswitch import *
import call_json as json_vals
from call_json_switches import SWITCHES_NUM
from call_json_outlets import OUTLETS_NUM
from call_json_fans import FANS_NUM
from call_json_bulbs import BULBS_NUM

BAD_DEV_LIST = {
    'result': {
        'total': 5,
        'pageNo': 1,
        'pageSize': 50,
        'list': [{'NoConfigKeys': None}],
    },
    'code': 0,
}


class TestDeviceList(object):
    """Test getting and populating device lists."""

    @pytest.fixture(scope='function')
    def api_mock(self, caplog):
        """Mock call_api and initialize VeSync object."""
        self.mock_api_call = patch('pyvesync.helpers.Helpers.call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospec()
        self.mock_api.return_value.ok = True
        self.vesync_obj = pyvesync.vesync.VeSync('sam@mail.com', 'pass', debug=True)
        self.vesync_obj.enabled = True
        self.vesync_obj.token = 'sample_tk'
        self.vesync_obj.account_id = 'sample_id'
        self.vesync_obj.in_process = False
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    def test_device_api(self, caplog, api_mock):
        """Tests to ensure call_api is being called correctly."""
        head = json_vals.DEFAULT_HEADER_BYPASS
        self.mock_api.return_value = {'V': 2}
        self.vesync_obj.get_devices()
        call_list = self.mock_api.call_args_list
        call_p1 = call_list[0][0]
        call_p2 = call_list[0][1]
        assert call_p1[0] == '/cloud/v1/deviceManaged/devices'
        assert call_p2['method'] == 'post'
        assert call_p2['headers'] == head
        assert self.vesync_obj.enabled

    def test_getdevs_vsfact(
        self, api_mock
    ):
        """Test the get_devices, process_devices and VSFactory methods.
        Build list with device objects from details
        Test for all 6 known devices - 4 outlets, 2 switches, 1 fan.
        """

        device_list = json_vals.DeviceList.device_list_response()

        self.mock_api.return_value = device_list

        self.vesync_obj.get_devices()

        assert len(self.vesync_obj.outlets) == OUTLETS_NUM
        assert len(self.vesync_obj.switches) == SWITCHES_NUM
        assert len(self.vesync_obj.fans) == FANS_NUM
        assert len(self.vesync_obj.bulbs) == BULBS_NUM

    def test_lv600(
            self, api_mock
    ):
        """Test the get_devices, process_devices and VSFactory methods.
        Build list with device objects from details
        Test for all 6 known devices - 4 outlets, 2 switches, 1 fan.
        """

        device_list = json_vals.DeviceList.FAN_TEST

        self.mock_api.return_value = device_list

        self.vesync_obj.get_devices()

        assert len(self.vesync_obj.fans) == 3

    def test_dual200s(
            self, api_mock
    ):
        """Test the get_devices, process_devices and VSFactory methods.
        Build list with device objects from details
        Test for all 6 known devices - 4 outlets, 2 switches, 1 fan.
        """

        device_list = json_vals.DeviceList.device_list_response('Dual200S')

        self.mock_api.return_value = device_list
        self.vesync_obj.debug = True
        self.vesync_obj.get_devices()

        assert len(self.vesync_obj.fans) == 1

    def test_getdevs_code(self, caplog, api_mock):
        """Test get_devices with code > 0 returned."""
        device_list = {'code': 1, 'msg': 'gibberish'}

        self.mock_api.return_value = device_list
        self.vesync_obj.get_devices()

        assert 'Error retrieving device list' in caplog.text

    def test_get_devices_resp_changes(self, caplog, api_mock):
        """Test if structure of device list response has changed."""
        device_list = {
            'code': 0,
            'NOTresult': {
                'NOTlist': [
                    {
                        'deviceType': 'wifi-switch-1.3',
                        'type': 'wifi-switch',
                        'cid': 'cid1',
                    }
                ]
            },
        }
        self.mock_api.return_value = device_list
        self.vesync_obj.get_devices()
        assert len(caplog.records) == 1
        assert 'Device list in response not found' in caplog.text

    def test_7a_bad_conf(self, caplog, api_mock):
        """Test bad device list response."""
        self.mock_api.return_value = BAD_DEV_LIST
        self.vesync_obj.get_devices()
        assert len(caplog.records) == 2

    def test_7a_no_dev_list(self, caplog, api_mock):
        """Test if empty device list is handled correctly."""
        empty_list = []

        self.vesync_obj.process_devices(empty_list)

        assert len(caplog.records) == 1

    def test_get_devices_devicetype_error(self, caplog, api_mock):
        """Test result and list keys exist but deviceType not in list."""
        device_list = {'code': 0, 'result': {'list': [{'type': 'wifi-switch', 'cid': 'cid1'}]}}
        self.mock_api.return_value = device_list
        self.vesync_obj.get_devices()
        assert len(caplog.records) == 2
        assert 'Error adding device' in caplog.text

    def test_unknown_device(self, caplog, api_mock):
        """Test unknown device type is handled correctly."""
        unknown_dev = json_vals.DeviceList.LIST_CONF_7A

        original_value = unknown_dev['deviceType']
        unknown_dev['deviceType'] = 'UNKNOWN-DEVTYPE'

        assert self.vesync_obj.object_factory(unknown_dev) is None

        assert len(caplog.records) == 1
        assert 'Unknown' in caplog.text

        unknown_dev['deviceType'] = original_value

    def test_time_check(self, api_mock):
        """Test device details update throttle."""
        time_check = self.vesync_obj.device_time_check()
        assert time_check is True
        self.vesync_obj.last_update_ts = time.time()
        time_check = self.vesync_obj.device_time_check()
        assert time_check is False
        self.vesync_obj.last_update_ts = (
            time.time() - self.vesync_obj.update_interval - 1
        )
        time_check = self.vesync_obj.device_time_check()
        assert time_check is True

    @patch('pyvesync.vesyncoutlet.VeSyncOutlet7A', autospec=True)
    def test_remove_device(self, outlet_patch, caplog, api_mock):
        """Test remove device test."""
        device = copy.deepcopy(json_vals.DeviceList.LIST_CONF_7A)

        outlet_test = outlet_patch.return_value
        outlet_test.cid = '7A-CID'
        outlet_test.device_type = 'wifi-switch-1.3'
        outlet_test.device_name = '7A Device'

        new_list = [device]
        self.vesync_obj._device_list = [outlet_test]
        device_exists = pyvesync.vesync.VeSync.remove_old_devices(
            self.vesync_obj, new_list
        )

        assert device_exists

        del device['cid']

        device_exists = pyvesync.vesync.VeSync.remove_dev_test(outlet_test, new_list)

        assert device_exists is False

        assert len(caplog.records) == 2
        assert 'cid' in caplog.text

    @patch('pyvesync.vesyncoutlet.VeSyncOutdoorPlug', autospec=True)
    def test_add_dev_test(self, outdoor_patch, caplog, api_mock):
        """Test add_device_test to return if device found in existing conf."""
        outdoor_inst = VeSyncOutdoorPlug(
            json_vals.DeviceList.LIST_CONF_OUTDOOR_2, self.vesync_obj
        )
        self.vesync_obj._device_list = [outdoor_inst]

        assert self.vesync_obj.add_dev_test(json_vals.DeviceList.LIST_CONF_OUTDOOR_1)

    def test_display_func(self, caplog, api_mock):
        """Test display function outputs text."""
        self.vesync_obj.device_list.append(
            VeSyncOutdoorPlug(json_vals.DeviceList.device_list_item('ESO15-TB', 0), self.vesync_obj)
        )
        self.vesync_obj.device_list.append(
            VeSyncOutlet10A(json_vals.DeviceList.device_list_item('ESW01-EU'), self.vesync_obj)
        )
        self.vesync_obj.device_list.append(
            VeSyncOutlet15A(json_vals.DeviceList.device_list_item('ESW15-USA'), self.vesync_obj)
        )
        self.vesync_obj.device_list.append(
            VeSyncOutlet7A(json_vals.DeviceList.LIST_CONF_7A, self.vesync_obj)
        )
        self.vesync_obj.device_list.append(
            VeSyncWallSwitch(json_vals.DeviceList.LIST_CONF_WS, self.vesync_obj)
        )
        self.vesync_obj.device_list.append(
            VeSyncAir131(json_vals.DeviceList.LIST_CONF_AIR, self.vesync_obj)
        )
        self.vesync_obj.device_list.append(
            VeSyncBulbESL100(json_vals.DeviceList.LIST_CONF_ESL100, self.vesync_obj)
        )

        dev_list = [
            self.vesync_obj.outlets,
            self.vesync_obj.switches,
            self.vesync_obj.fans,
            self.vesync_obj.bulbs,
        ]

        for device in chain(*dev_list):
            device.display()

        assert len(caplog.records) == 0
    
    def test_resolve_updates(
        self,
        caplog,
        api_mock,
    ):
        """Test process_devices() with all devices.
        Creates vesync object with all devices and returns
        device list with new set of all devices.
        """
        common = {'configModule': 'test', 'connectionStatus': 'unknown'}
        details = {'cid': '7A-CID1', 'deviceType': 'wifi-switch-1.3', 'deviceName': '7A Removed', **common}
        out7a_patch = VeSyncOutlet7A(details, self.vesync_obj)

        details = {'cid': '10A-CID1', 'deviceType': 'ESW10-EU', 'deviceName':  '10A Removed', **common}
        out10a_patch = VeSyncOutlet10A(details, self.vesync_obj)

        details = {'cid': '15A-CID1', 'deviceType': 'ESW15-USA', 'deviceName': '15A Removed', **common}
        out15a_patch = VeSyncOutlet15A(details, self.vesync_obj)

        details = {'cid': 'OUTDOOR-CID1', 'deviceType': 'ESO15-TB', 'deviceName': 'Outdoor Removed', **common}
        outdoor_patch = VeSyncOutdoorPlug(details, self.vesync_obj)

        details = {'cid': 'BULB-CID1', 'deviceType': 'ESL100', 'deviceName': 'Bulb Removed', **common}
        esl100_patch = VeSyncBulbESL100(details, self.vesync_obj)

        details = {'cid': 'WS-CID2', 'deviceType': 'ESWL01', 'deviceName': 'Switch Removed', **common}
        ws_patch = VeSyncWallSwitch(details, self.vesync_obj)

        details = {'cid': 'AirCID2', 'deviceType': 'LV-PUR131S', 'deviceName': 'fan Removed', **common}
        air_patch = VeSyncAir131(details, self.vesync_obj)

        self.vesync_obj._device_list = [
            out7a_patch, out10a_patch, out15a_patch, outdoor_patch,
            ws_patch,
            air_patch,
            esl100_patch
        ]

        json_ret = json_vals.DeviceList.FULL_DEV_LIST
        self.vesync_obj.process_devices(json_ret)

        assert len(self.vesync_obj.device_list) == 16 # single test 6/module test 5?!?
        assert len(self.vesync_obj.outlets) == 6 # single test 6/module test 5?!?
        assert len(self.vesync_obj.switches) == 2
        assert len(self.vesync_obj.fans) == 4
        assert len(self.vesync_obj.bulbs) == 4
