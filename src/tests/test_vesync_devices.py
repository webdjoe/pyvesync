import pytest
from unittest.mock import Mock, patch, mock_open, call
import unittest
import pyvesync
from pyvesync.vesync import (VeSync,
                             VeSyncSwitch,
                             VeSyncSwitch15A,
                             VeSyncSwitch7A,
                             VeSyncSwitchEU10A,
                             VeSyncSwitchInWall)
import os
import responses
import requests


class TestDeviceList(object):
    @pytest.fixture()
    def api_mock(self):
        self.mock_api_call = patch('pyvesync.vesync.VeSync.call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospec()
        self.mock_api.return_value.ok = True
        self.vesync_obj = VeSync('sam@mail.com', 'pass')
        self.vesync_obj.enabled = True
        self.vesync_obj.tk = 'sample_tk'
        self.vesync_obj.account_id = 'sample_id'
        yield
        self.mock_api_call.stop()

    def test_get_devices(self, mocker, api_mock):
        mocker.patch.object(pyvesync.vesync, 'VeSyncSwitch7A', 
                            autospec=True)
        mocker.patch.object(pyvesync.vesync, 'VeSyncSwitch15A',
                            autospec=True)
        mocker.patch.object(pyvesync.vesync, 'VeSyncSwitchInWall',
                            autospec=True)
        mocker.patch.object(pyvesync.vesync, 'VeSyncSwitchEU10A',
                            autospec=True)
        devs = []
        dev1 = {'deviceType': 'wifi-switch-1.3', 'type': 'wifi-switch',
                'cid': 'cid1'}
        dev2 = {'deviceType': 'ESW15-USA', 'type': 'wifi-switch',
                'cid': 'cid2'}
        dev3 = {'deviceType': 'ESWL01', 'type': 'Switches',
                'cid': 'cid3'}
        dev4 = {'deviceType': 'ESW01-EU', 'type': 'wifi-switch',
                'cid': 'cid4'}
        dev5 = {'deviceType': 'unknown'}
        devs.extend([dev1, dev2, dev3, dev4, dev5])
        device_list = ({'code': 0, 'result': {'list': devs }}, 200)
        
        self.mock_api.return_value = device_list
        
        devs = self.vesync_obj.get_devices()
        
        assert len(devs) == 4
        for device in devs:
            assert isinstance(device, VeSyncSwitch)
        pyvesync.vesync.VeSyncSwitch7A.assert_called_with(dev1, self.vesync_obj)
        pyvesync.vesync.VeSyncSwitch15A.assert_called_with(dev2, self.vesync_obj)
        pyvesync.vesync.VeSyncSwitchInWall.assert_called_with(dev3, self.vesync_obj)
        pyvesync.vesync.VeSyncSwitchEU10A.assert_called_with(dev4, self.vesync_obj)

    def test_get_devices_error(self, api_mock):
        device_list = ({'code':2, 'result':{'list':
                        {'deviceType': 'wifi-switch-1.3', 'type': 'wifi-switch',
                        'cid': 'cid1'}}}, 200)
        self.mock_api.return_value = device_list
        devs = self.vesync_obj.get_devices()
        assert len(devs) == 0
