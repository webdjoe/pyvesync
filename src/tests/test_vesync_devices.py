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

#Not working - Trying to figure out way to separate testing device_list() and update()
#from switch classes

class TestDeviceList(object):
    @pytest.fixture()
    def api_mock(self):
        self.mock_api_call = patch('pyvesync.vesync.VeSync.call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospec()
        self.mock_api.return_value.ok = True
        yield
        self.mock_api_call.stop()

    def test_device_list(self, api_mock):
        device_list = ({'code': 0, 'result': {'list':
                                             [{'deviceType': 'wifi-switch-1.3',
                                               'type': 'wifi-switch',
                                               'cid': 'cid1'},
                                              {'deviceType': 'ESW15-USA',
                                               'type': 'wifi-switch',
                                               'cid': 'cid2'},
                                              {'deviceType': 'ESWL01',
                                                 'type': 'Switches',
                                                 'cid': 'cid3'},
                                              {'deviceType': 'ESW01-EU',
                                                 'type': 'wifi-switch',
                                                 'cid': 'cid4'}]
                                             }}, 200)
        self.mock_api.return_value = device_list
        vesync_obj = VeSync('sam@mail.com', 'pass')
        vesync_obj.enabled = True
        vesync_obj.tk = 'sample_tk'
        vesync_obj.account_id = 'sample_id'
        vesync_obj.get_devices()
        assert len(vesync_obj.get_devices.devs) == 4
