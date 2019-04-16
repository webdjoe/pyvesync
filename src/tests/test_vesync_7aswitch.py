import pytest
from unittest import mock
from unittest.mock import Mock, patch, mock_open, call
import unittest
import pyvesync
import logging
from pyvesync.vesync import (VeSync,
                             VeSyncSwitch,
                             VeSyncSwitch15A,
                             VeSyncSwitch7A,
                             VeSyncSwitch10A,
                             VeSyncSwitchInWall)
import os
import requests

DEV_LIST_DETAIL = {
    "deviceType": "wifi-switch-1.3",
    "extension": None,
    "macID": None,
    "type": "wifi-switch",
    "deviceName": "Device Name",
    "deviceImg": "dev_img_url",
    "connectionType": "wifi",
    "uuid": None,
    "speed": None,
    "deviceStatus": "on",
    "mode": None,
    "configModule": "7AOutlet",
    "currentFirmVersion": "1.95",
    "connectionStatus": "online",
    "cid": "7a-cid"
}

CORRECT_7A_LIST = {
    "traceId": "1552110321929",
    "msg": None,
    "result": {
        "total": 5,
        "pageNo": 1,
        "pageSize": 50,
        "list": [DEV_LIST_DETAIL]
    },
    "code": 0
}

BAD_7A_LIST = {
    "result": {
        "total": 5,
        "pageNo": 1,
        "pageSize": 50,
        "list": [{
            "deviceType": "wifi-switch-1.3",
            "NoConfigKeys": None
        }
        ]
    },
    "code": 0
}

ENERGY_HISTORY = {
    "code": 0,
    "energyConsumptionOfToday": 1,
    "costPerKWH": 1,
    "maxEnergy": 1,
    "totalEnergy": 1,
    "data": [
        1,
        1,
    ]
}


class TestVesync7ASwitch(object):
    @pytest.fixture()
    def api_mock(self, caplog):
        self.mock_api_call = patch('pyvesync.vesync.VeSync.call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospect()
        self.mock_api.return_value.ok = True
        self.vesync_obj = VeSync('sam@mail.com', 'pass')
        self.vesync_obj.enabled = True
        self.vesync_obj.login = True
        self.vesync_obj.tk = 'sample_tk'
        self.vesync_obj.account_id = 'sample_actid'
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    def test_7aswitch_conf(self, api_mock):
        self.mock_api.return_value = (CORRECT_7A_LIST, 200)
        devs = self.vesync_obj.get_devices()
        assert len(devs) == 1
        vswitch7a = devs[0]
        assert isinstance(vswitch7a, VeSyncSwitch7A)
        assert vswitch7a.device_name == "Device Name"
        assert vswitch7a.device_type == "wifi-switch-1.3"
        assert vswitch7a.cid == "7a-cid"

    def test_7a_bad_conf(self, caplog, api_mock):
        self.mock_api.return_value = (BAD_7A_LIST, 200)
        devs = self.vesync_obj.get_devices()
        assert len(devs) == 1
        assert len(caplog.records) == 12

    def test_7a_details(self, api_mock):
        correct_7a_details = {
            "deviceStatus": "on",
            "deviceImg": "",
            "activeTime": 1,
            "energy": 1,
            "power": "1000:1000",
            "voltage": "1000:1000"
        }
        self.mock_api.return_value = (correct_7a_details, 200)
        vswitch7a = VeSyncSwitch7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.get_details()
        dev_details = vswitch7a.details
        assert vswitch7a.device_status == 'on'
        assert type(dev_details) == dict
        assert dev_details['active_time'] == 1
        assert dev_details['energy'] == 1
        assert dev_details['power'] == "1000:1000"
        assert dev_details['voltage'] == "1000:1000"
        assert vswitch7a.power() == 1
        assert vswitch7a.voltage() == 1

    def test_7a_no_devstatus(self, caplog, api_mock):
        bad_7a_details = {
            "deviceImg": "",
            "activeTime": 1,
            "energy": 1,
            "power": "1A:1A",
            "voltage": "1A:1A"
        }
        self.mock_api.return_value = (bad_7a_details, 200)
        vswitch7a = VeSyncSwitch7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.get_details()
        assert len(caplog.records) == 1
        assert 'details' in caplog.text

    def test_7a_no_details(self, caplog, api_mock):
        bad_7a_details = {
            "deviceStatus": "on"
        }
        self.mock_api.return_value = (bad_7a_details, 200)
        vswitch7a = VeSyncSwitch7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.get_details()
        assert len(caplog.records) == 4

    def test_7a_onoff(self, caplog, api_mock):
        self.mock_api.return_value = ("response", 200)
        vswitch7a = VeSyncSwitch7A(DEV_LIST_DETAIL, self.vesync_obj)
        on = vswitch7a.turn_on()
        head = self.vesync_obj.get_headers()
        self.mock_api.assert_called_with(
            vswitch7a.url_build(vswitch7a.cid, 'on'), 'put', headers=head)
        assert on
        off = vswitch7a.turn_off()
        self.mock_api.assert_called_with(vswitch7a.url_build(
            vswitch7a.cid, 'off'), 'put', headers=head)
        assert off

    def test_7a_onoff_fail(self, api_mock):
        self.mock_api.return_value = ('response', 400)
        vswitch7a = VeSyncSwitch7A(DEV_LIST_DETAIL, self.vesync_obj)
        assert not vswitch7a.turn_on()
        assert not vswitch7a.turn_off()

    def test_7a_weekly(self, api_mock):
        self.mock_api.return_value = (ENERGY_HISTORY, 200)
        vswitch7a = VeSyncSwitch7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.get_weekly_energy()
        self.mock_api.assert_called_with(
            vswitch7a.url_build(vswitch7a.cid, 'week'), 'get',
            headers=self.vesync_obj.get_headers())
        energy_dict = vswitch7a.energy['week']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]

    def test_7a_monthly(self, api_mock):
        self.mock_api.return_value = (ENERGY_HISTORY, 200)
        vswitch7a = VeSyncSwitch7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.get_monthly_energy()
        self.mock_api.assert_called_with(
            vswitch7a.url_build(vswitch7a.cid, 'month'), 'get',
            headers=self.vesync_obj.get_headers())
        energy_dict = vswitch7a.energy['month']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]

    def test_7a_yearly(self, api_mock):
        self.mock_api.return_value = (ENERGY_HISTORY, 200)
        vswitch7a = VeSyncSwitch7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.get_yearly_energy()
        self.mock_api.assert_called_with(
            vswitch7a.url_build(vswitch7a.cid, 'year'), 'get',
            headers=self.vesync_obj.get_headers())
        energy_dict = vswitch7a.energy['year']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]

    def test_history_fail(self, caplog, api_mock):
        bad_history = {"code": 1}
        self.mock_api.return_value = (bad_history, 200)
        vswitch7a = VeSyncSwitch7A(DEV_LIST_DETAIL, self.vesync_obj)
        vswitch7a.update_energy()
        assert len(caplog.records) == 1
        assert 'weekly' in caplog.text
        caplog.clear()
        vswitch7a.get_monthly_energy()
        assert len(caplog.records) == 1
        assert 'monthly' in caplog.text
        caplog.clear()
        vswitch7a.get_yearly_energy()
        assert len(caplog.records) == 1
        assert 'yearly' in caplog.text
