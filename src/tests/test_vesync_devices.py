import pytest
from unittest.mock import patch, Mock
import logging
import pyvesync
from pyvesync import VeSync
from pyvesync.vesyncoutlet import VeSyncOutlet, VeSyncOutlet7A, VeSyncOutlet10A, VeSyncOutlet15A
from pyvesync.vesyncswitch import VeSyncSwitch
from pyvesync.vesyncfan import VeSyncAir131
from pyvesync.vesyncbasedevice import VeSyncBaseDevice
import os, sys, inspect

# Hackish but it works
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)
import call_json as json_vals


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
        devlist_obj = json_vals.DeviceList()
        details_7a = devlist_obj.details_7a
        details_15a = devlist_obj.details_15a
        details_wallsw = devlist_obj.details_wallsw
        details_10eu = devlist_obj.details_10aeu
        details_10us = devlist_obj.details_10aus
        details_air = devlist_obj.details_air

        devlist = [details_7a, details_10us, details_10eu,
                   details_15a, details_air, details_wallsw]

        device_list = ({'code': 0, 'result': {'list': devlist}}, 200)

        self.mock_api.return_value = device_list

        proc_dev = self.vesync_obj.get_devices()

        assert out7a_patch.called
        assert out10a_patch.called
        assert out15a_patch.called
        assert ws_patch.called
        assert air_patch.called

        assert len(proc_dev) == 3
        outlets = proc_dev[0]
        switches = proc_dev[1]
        fans = proc_dev[2]
        assert len(outlets) == 4
        assert len(switches) == 1
        assert len(fans) == 1

    def test_getdevs_code(self, caplog, api_mock):
        """Test get_devices with code > 0 returned"""

        device_list = ({'code': 1, 'msg': 'gibberish'}, 200)

        self.mock_api.return_value = device_list
        dev_list = self.vesync_obj.get_devices()

        assert len(dev_list) == 3
        assert len(caplog.records) == 1
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
        assert len(devs) == 3
        assert len(caplog.records) == 1
        assert 'Device list in response not found' in caplog.text

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
        assert len(devs) == 3
        assert len(caplog.records) == 1
        assert 'devType key not found' in caplog.text

    @patch('pyvesync.vesync.VeSyncOutlet7A', autospec=True)
    @patch('pyvesync.vesync.VeSyncOutlet15A', autospec=True)
    @patch('pyvesync.vesync.VeSyncOutlet10A', autospec=True)
    def test_resolve_updates(self, out10a_patch, out15a_patch, out7a_patch, caplog, api_mock):
        """Test resolve updates function"""

        outlet_10a = out10a_patch.return_value
        outlet_10a.cid = '10A-CID'
        outlet_15a = out15a_patch.return_value
        outlet_15a.cid = '15A-CID'
        outlet_7a = out7a_patch.return_value
        outlet_7a.cid = '7A-CID'
        outlets = [outlet_10a, outlet_15a, outlet_7a]

        resolve = pyvesync.helpers.Helpers.resolve_updates
        self.vesync_obj.outlets = []

        self.vesync_obj.outlets = resolve(self.vesync_obj.outlets, outlets)

        assert self.vesync_obj.outlets == outlets

        outlets = [outlet_10a]

        self.vesync_obj.outlets = resolve(self.vesync_obj.outlets, outlets)

        assert self.vesync_obj.outlets == outlets
