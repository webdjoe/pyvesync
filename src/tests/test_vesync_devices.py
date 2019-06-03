
import pytest
from unittest.mock import patch, MagicMock
import logging
import pyvesync
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
    @pytest.fixture()
    def api_mock(self, caplog):
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
        """Tests to ensure call_api is being called correctly"""
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
        """Test the get_devices, process_devices and VSFactory methods
            to build list with device objects from details
                Test for all 6 known devices -
                4 outlets, 1 switch, 1 fan"""

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
        assert len(outlets) == 4
        assert len(switches) == 1
        assert len(fans) == 1
        assert len(bulbs) == 0

    def test_getdevs_code(self, caplog, api_mock):
        """Test get_devices with code > 0 returned"""
        device_list = ({'code': 1, 'msg': 'gibberish'}, 200)

        self.mock_api.return_value = device_list
        dev_list = self.vesync_obj.get_devices()

        assert len(dev_list) == 4
        assert 'Error retrieving device list' in caplog.text

    def test_get_devices_resp_changes(self, caplog, api_mock):
        """Test if structure of device list response has changed"""
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
        self.mock_api.return_value = (BAD_DEV_LIST, 200)
        devs = self.vesync_obj.get_devices()
        assert len(devs) == 4
        assert len(caplog.records) == 2

    def test_get_devices_deviceType_error(self, caplog, api_mock):
        """Test result and list keys exist but deviceType not in list"""
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

    @patch('pyvesync.vesync.VeSyncOutlet7A', autospec=True)
    @patch('pyvesync.vesync.VeSyncOutlet15A', autospec=True)
    @patch('pyvesync.vesync.VeSyncOutlet10A', autospec=True)
    @patch('pyvesync.vesync.VeSyncWallSwitch', autospec=True)
    @patch('pyvesync.vesync.VeSyncAir131', autospec=True)
    def test_resolve_updates(self, air_patch, ws_patch, out10a_patch,
                             out15a_patch, out7a_patch, caplog, api_mock):
        """Test process_devices() with all devices -
            Creates vesync object with all devices and returns
            device list with new set of all devices"""
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

        json_ret = json_vals.FULL_DEV_LIST

        self.vesync_obj.outlets = [outlet_10a, outlet_15a, outlet_7a]
        self.vesync_obj.switches = [switch]
        self.vesync_obj.fans = [air]

        outlets, switches, fans, bulbs = self.vesync_obj.process_devices(
            json_ret)

        assert len(self.vesync_obj.outlets) == 0
        assert len(self.vesync_obj.switches) == 0
        assert len(self.vesync_obj.fans) == 0

        assert len(outlets) == 4
        assert len(switches) == 1
        assert len(fans) == 1
        assert len(bulbs) == 0
