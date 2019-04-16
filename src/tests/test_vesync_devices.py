import pytest
from unittest import mock
from unittest.mock import Mock, patch, mock_open, call
import unittest
import pyvesync
from pyvesync.vesync import (VeSync,
                             VeSyncSwitch,
                             VeSyncSwitch15A,
                             VeSyncSwitch7A,
                             VeSyncSwitch10A,
                             VeSyncSwitchInWall)
import os
import requests
import logging


class TestDeviceList(object):
    @pytest.fixture()
    def api_mock(self, caplog):
        self.mock_api_call = patch('pyvesync.vesync.VeSync.call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospec()
        self.mock_api.return_value.ok = True
        self.vesync_obj = VeSync('sam@mail.com', 'pass')
        self.vesync_obj.enabled = True
        self.vesync_obj.tk = 'sample_tk'
        self.vesync_obj.account_id = 'sample_id'
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    def test_get_devices(self, caplog, mocker, api_mock):
        '''Test get_devices for all switches with an unknown switch'''
        vesync_7a = mocker.patch.object(
            pyvesync.vesync, 'VeSyncSwitch7A', autospec=True)
        vesync_15a = mocker.patch.object(
            pyvesync.vesync, 'VeSyncSwitch15A', autospec=True)
        vesync_wallswitch = mocker.patch.object(
            pyvesync.vesync, 'VeSyncSwitchInWall', autospec=True)
        vesync_10a = mocker.patch.object(
            pyvesync.vesync, 'VeSyncSwitch10A', autospec=True)

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
        device_list = ({'code': 0, 'result': {'list': devs}}, 200)

        self.mock_api.return_value = device_list
        devs = self.vesync_obj.get_devices()
        assert len(devs) == 4
        for device in devs:
            assert isinstance(device, VeSyncSwitch)
        vesync_7a.assert_called_with(dev1, self.vesync_obj)
        vesync_15a.assert_called_with(dev2, self.vesync_obj)
        vesync_wallswitch.assert_called_with(dev3, self.vesync_obj)
        vesync_10a.assert_called_with(dev4, self.vesync_obj)

        assert 'Unknown device' in caplog.text

    def test_get_devices_code_error(self, caplog, api_mock):
        '''Test if code in response is greater than 0'''
        device_list = ({'code': 2455645641,
                        'result': {
                            'list': [{
                                'deviceType': 'wifi-switch-1.3',
                                'type': 'wifi-switch',
                                'cid': 'cid1'}]
                        }
                        }, 200)
        self.mock_api.return_value = device_list
        devs = self.vesync_obj.get_devices()
        assert len(devs) == 0
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
        assert len(devs) == 0
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
        assert len(devs) == 0
        assert len(caplog.records) == 1
        assert 'deviceType key not found' in caplog.text
