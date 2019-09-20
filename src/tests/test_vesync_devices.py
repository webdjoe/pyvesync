"""Test VeSync manager methods."""

import pytest
from unittest.mock import patch, MagicMock
import logging
import pyvesync
import time
import copy
from itertools import chain
from pyvesync import (VeSyncAir131, VeSyncBulbESL100, VeSyncOutdoorPlug,
                      VeSyncOutlet10A, VeSyncOutlet15A, VeSyncOutlet7A,
                      VeSyncWallSwitch)
from . import call_json as json_vals

BAD_DEV_LIST = {
    "result": {
        "total": 5,
        "pageNo": 1,
        "pageSize": 50,
        "list": [{
            "NoConfigKeys": None
        }]
    },
    "code": 0
}


class TestDeviceList(object):
    """Test getting and populating device lists."""

    @pytest.fixture()
    def api_mock(self, caplog):
        """Mock call_api and initialize VeSync object."""
        self.mock_api_call = patch('pyvesync.helpers.Helpers.call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospec()
        self.mock_api.return_value.ok = True
        self.vesync_obj = pyvesync.vesync.VeSync('sam@mail.com', 'pass')
        self.vesync_obj.enabled = True
        self.vesync_obj.token = 'sample_tk'
        self.vesync_obj.account_id = 'sample_id'
        self.vesync_obj.in_process = False
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    def test_device_api(self, caplog, api_mock):
        """Tests to ensure call_api is being called correctly."""
        head = json_vals.DEFAULT_HEADER
        self.mock_api.return_value = ({'V': 2}, 200)
        out, sw, fan, bulb = self.vesync_obj.get_devices()
        call_list = self.mock_api.call_args_list
        call_p1 = call_list[0][0]
        call_p2 = call_list[0][1]
        assert call_p1[0] == '/cloud/v1/deviceManaged/devices'
        assert call_p1[1] == 'post'
        assert call_p2['headers'] == head
        assert self.vesync_obj.enabled

    @patch('pyvesync.vesync.VeSyncOutlet7A')
    @patch('pyvesync.vesync.VeSyncOutlet15A')
    @patch('pyvesync.vesync.VeSyncOutlet10A')
    @patch('pyvesync.vesync.VeSyncWallSwitch')
    @patch('pyvesync.vesync.VeSyncAir131')
    def test_getdevs_vsfact(self, air_patch, ws_patch, out10a_patch,
                            out15a_patch, out7a_patch, api_mock):
        """Test the get_devices, process_devices and VSFactory methods.
        Build list with device objects from details
        Test for all 6 known devices - 4 outlets, 2 switches, 1 fan.
        """

        device_list = json_vals.DEVLIST_ALL

        self.mock_api.return_value = device_list

        proc_dev = self.vesync_obj.get_devices()

        assert out7a_patch.called
        assert out10a_patch.called
        assert out15a_patch.called
        assert ws_patch.called
        assert air_patch.called

        assert len(proc_dev) == 4
        outlets = proc_dev[0]
        switches = proc_dev[1]
        fans = proc_dev[2]
        bulbs = proc_dev[3]
        assert len(outlets) == 6
        assert len(switches) == 1
        assert len(fans) == 1
        assert len(bulbs) == 1

    def test_getdevs_code(self, caplog, api_mock):
        """Test get_devices with code > 0 returned."""
        device_list = ({'code': 1, 'msg': 'gibberish'}, 200)

        self.mock_api.return_value = device_list
        dev_list = self.vesync_obj.get_devices()

        assert len(dev_list) == 4
        assert 'Error retrieving device list' in caplog.text

    def test_get_devices_resp_changes(self, caplog, api_mock):
        """Test if structure of device list response has changed."""
        device_list = ({'code': 0,
                        'NOTresult': {
                            'NOTlist': [{
                                'deviceType': 'wifi-switch-1.3',
                                'type': 'wifi-switch',
                                'cid': 'cid1'
                            }]
                        }
                        }, 200)
        self.mock_api.return_value = device_list
        devs = self.vesync_obj.get_devices()
        assert len(devs) == 4
        assert len(caplog.records) == 1
        assert 'Device list in response not found' in caplog.text

    def test_7a_bad_conf(self, caplog, api_mock):
        """Test bad device list response."""
        self.mock_api.return_value = (BAD_DEV_LIST, 200)
        devs = self.vesync_obj.get_devices()
        assert len(devs) == 4
        assert len(caplog.records) == 2

    def test_7a_no_dev_list(self, caplog, api_mock):
        """Test if empty device list is handled correctly."""
        empty_list = []

        self.vesync_obj.process_devices(empty_list)

        assert len(caplog.records) == 1

    def test_get_devices_deviceType_error(self, caplog, api_mock):
        """Test result and list keys exist but deviceType not in list."""
        device_list = ({'code': 0,
                        'result': {
                            'list': [{
                                'type': 'wifi-switch',
                                'cid': 'cid1'
                            }]
                        }
                        }, 200)
        self.mock_api.return_value = device_list
        devs = self.vesync_obj.get_devices()
        assert len(devs) == 4
        assert len(caplog.records) == 2
        assert 'Details keys not found' in caplog.text

    def test_unknown_device(self, caplog, api_mock):
        """Test unknown device type is handled correctly."""
        unknown_dev = json_vals.LIST_CONF_7A

        unknown_dev['devType'] = "UNKNOWN-DEVTYPE"

        pyvesync.vesync.get_device(
            'unkown_device', unknown_dev, self.vesync_obj)

        assert len(caplog.records) == 1
        assert 'Unknown' in caplog.text

    def test_time_check(self, api_mock):
        """Test device details update throttle."""
        time_check = self.vesync_obj.device_time_check()
        assert time_check is True
        self.vesync_obj.last_update_ts = time.time()
        time_check = self.vesync_obj.device_time_check()
        assert time_check is False
        self.vesync_obj.last_update_ts = (
            time.time() - self.vesync_obj.update_interval - 1)
        time_check = self.vesync_obj.device_time_check()
        assert time_check is True

    @patch('pyvesync.vesync.VeSyncOutlet7A', autospec=True)
    @patch('pyvesync.vesync.VeSyncOutlet15A', autospec=True)
    @patch('pyvesync.vesync.VeSyncOutlet10A', autospec=True)
    @patch('pyvesync.vesync.VeSyncOutdoorPlug', autospec=True)
    @patch('pyvesync.vesync.VeSyncBulbESL100', autospec=True)
    @patch('pyvesync.vesync.VeSyncWallSwitch', autospec=True)
    @patch('pyvesync.vesync.VeSyncAir131', autospec=True)
    def test_resolve_updates(self, air_patch, ws_patch, esl100_patch,
                             outdoor_patch, out10a_patch, out15a_patch,
                             out7a_patch, caplog, api_mock):
        """Test process_devices() with all devices.
        Creates vesync object with all devices and returns
        device list with new set of all devices.
        """
        outlet_10a = out10a_patch.return_value
        outlet_10a.cid = '10A-CID1'
        outlet_10a.device_type = 'ESW10-EU'
        outlet_10a.device_name = '10A Removed'

        outlet_15a = out15a_patch.return_value
        outlet_15a.cid = '15A-CID1'
        outlet_15a.device_type = 'ESW15-USA'
        outlet_15a.device_name = '15A Removed'

        outlet_7a = out7a_patch.return_value
        outlet_7a.cid = '7A-CID1'
        outlet_7a.device_type = 'wifi-switch-1.3'
        outlet_7a.device_name = '7A Removed'

        outlet_outdoor = outdoor_patch.return_value
        outlet_outdoor.cid = 'OUTDOOR-CID1'
        outlet_outdoor.device_type = 'ESO15-TB'
        outlet_outdoor.device_name = 'Outdoor Removed'

        bulb_esl100 = esl100_patch.return_value
        bulb_esl100.cid = 'BULB-CID1'
        bulb_esl100.device_type = 'ESL100'
        bulb_esl100.device_name = 'Bulb Removed'

        switch = ws_patch.return_value
        switch.cid = 'WS-CID2'
        switch.device_name = 'Switch Removed'
        switch.device_type = 'ESWL01'

        air = air_patch.return_value
        air.cid = 'AirCID2'
        air.device_type = 'LV-PUR131S'
        air.device_name = 'fan Removed'

        out10a_attr = MagicMock()
        out10a_attr.device_type = 'ESW01-EU'
        out10a_attr.device_name = '10A Added'
        out10a_patch.return_value = out10a_attr

        out15a_attr = MagicMock()
        out15a_attr.device_type = 'ESW15A-USA'
        out15a_attr.device_name = '15A Added'
        out15a_patch.return_value = out15a_attr

        out7a_attr = MagicMock()
        out7a_attr.device_type = 'wifi-switch-1.3'
        out7a_attr.device_name = '7A Added'
        out7a_patch.return_value = out7a_attr

        air_attr = MagicMock()
        air_attr.device_type = 'LV-PUR131S'
        air_attr.device_name = 'Air Added'
        air_patch.return_value = air_attr

        ws_attr = MagicMock()
        ws_attr.device_name = 'Switch Added'
        ws_attr.device_type = 'ESWL01'
        ws_patch.return_value = ws_attr

        outdoor_attr = MagicMock()
        outdoor_attr.device_name = 'Outdoor added'
        outdoor_attr.device_type = 'ESO15-TB'
        outdoor_patch.return_value = outdoor_attr

        esl100_attr = MagicMock()
        esl100_attr.device_name = 'ESL100 Bulb Added'
        esl100_attr.device_type = 'ESL100'
        esl100_patch.return_value = esl100_attr

        json_ret = json_vals.FULL_DEV_LIST

        self.vesync_obj.outlets = [outlet_10a, outlet_15a,
                                   outlet_7a, outlet_outdoor]
        self.vesync_obj.switches = [switch]
        self.vesync_obj.fans = [air]
        self.vesync_obj.bulbs = [bulb_esl100]

        outlets, switches, fans, bulbs = self.vesync_obj.process_devices(
            json_ret)

        assert len(self.vesync_obj.outlets) == 0
        assert len(self.vesync_obj.switches) == 0
        assert len(self.vesync_obj.fans) == 0
        assert len(self.vesync_obj.bulbs) == 0

        assert len(outlets) == 6
        assert len(switches) == 1
        assert len(fans) == 1
        assert len(bulbs) == 1

    @patch('pyvesync.vesync.VeSyncOutlet7A', autospec=True)
    def test_remove_device(self, outlet_patch, caplog, api_mock):
        """Test remove device test."""
        device = copy.deepcopy(json_vals.LIST_CONF_7A)

        outlet_test = outlet_patch.return_value
        outlet_test.cid = '7A-CID'
        outlet_test.device_type = 'wifi-switch-1.3'
        outlet_test.device_name = '7A Device'

        new_list = [device]

        device_exists = pyvesync.vesync.VeSync.remove_dev_test(
            outlet_test, new_list)

        assert device_exists

        del device['cid']

        device_exists = pyvesync.vesync.VeSync.remove_dev_test(
            outlet_test, new_list)

        assert device_exists is False

        assert len(caplog.records) == 2
        assert 'cid' in caplog.text

    @patch('pyvesync.vesync.VeSyncOutdoorPlug', autospec=True)
    def test_add_dev_test(self, outdoor_patch, caplog, api_mock):
        """Test add_device_test to return if device found in existing conf."""
        outdoor_inst = pyvesync.VeSyncOutdoorPlug(
            json_vals.LIST_CONF_OUTDOOR_2, self.vesync_obj)
        self.vesync_obj.oulets = [outdoor_inst]

        add_test = self.vesync_obj.add_dev_test(json_vals.LIST_CONF_OUTDOOR_1)

        assert add_test

    def test_display_func(self, caplog, api_mock):
        """Test display function outputs text."""
        self.vesync_obj.outlets.append(
            VeSyncOutdoorPlug(json_vals.LIST_CONF_OUTDOOR_1, self.vesync_obj))
        self.vesync_obj.outlets.append(
            VeSyncOutlet10A(json_vals.LIST_CONF_10AUS, self.vesync_obj))
        self.vesync_obj.outlets.append(
            VeSyncOutlet15A(json_vals.LIST_CONF_15A, self.vesync_obj))
        self.vesync_obj.outlets.append(
            VeSyncOutlet7A(json_vals.LIST_CONF_7A, self.vesync_obj))
        self.vesync_obj.switches.append(
            VeSyncWallSwitch(json_vals.LIST_CONF_WS, self.vesync_obj))
        self.vesync_obj.fans.append(
            VeSyncAir131(json_vals.LIST_CONF_AIR, self.vesync_obj))
        self.vesync_obj.bulbs.append(
            VeSyncBulbESL100(json_vals.LIST_CONF_ESL100, self.vesync_obj))

        dev_list = [self.vesync_obj.outlets, self.vesync_obj.switches,
                    self.vesync_obj.fans, self.vesync_obj.bulbs]

        for device in chain(*dev_list):
            device.display()

        assert len(caplog.records) == 0
