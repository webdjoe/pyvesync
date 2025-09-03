"""Test scripts for WHOGPLUG Outlets."""

import pytest
from unittest.mock import patch
import logging
from pyvesync import VeSync
from pyvesync.vesyncoutlet import VeSyncOutletWhogPlug
from pyvesync.helpers import Helpers as helpers
import call_json
import call_json_outlets
from utils import Defaults, TestBase

DEVICE_TYPE = 'WHOGPLUG'

DEV_LIST_DETAIL = call_json.DeviceList.device_list_item(DEVICE_TYPE)

CORRECT_WHOGPLUG_LIST = call_json.DeviceList.device_list_response(DEVICE_TYPE)

CORRECT_WHOGPLUG_DETAILS = call_json_outlets.DETAILS_RESPONSES[DEVICE_TYPE]

BAD_WHOGPLUG_LIST = call_json.DETAILS_BADCODE


class TestVeSyncWhogPlugSwitch(TestBase):
    """Test WhogPlug outlet API."""

    def test_whogplug_conf(self):
        """Test initialization of WhogPlug outlet."""
        self.mock_api.return_value = CORRECT_WHOGPLUG_LIST
        self.manager.get_devices()
        outlets = self.manager.outlets
        assert len(outlets) == 1
        whogplug_outlet = outlets[0]
        assert isinstance(whogplug_outlet, VeSyncOutletWhogPlug)
        assert whogplug_outlet.device_name == call_json.Defaults.name(DEVICE_TYPE)
        assert whogplug_outlet.device_type == DEVICE_TYPE
        assert whogplug_outlet.cid == call_json.Defaults.cid(DEVICE_TYPE)
        assert whogplug_outlet.uuid == call_json.Defaults.uuid(DEVICE_TYPE)

    def test_whogplug_details(self):
        """Test WhogPlug get_details()."""
        self.mock_api.return_value = CORRECT_WHOGPLUG_DETAILS
        whogplug_outlet = VeSyncOutletWhogPlug(DEV_LIST_DETAIL, self.manager)
        whogplug_outlet.get_details()
        response = CORRECT_WHOGPLUG_DETAILS[0]
        result = response.get('result', {}).get('result', {})
        
        expected_status = 'on' if result.get('enabled') else 'off'
        assert whogplug_outlet.device_status == expected_status
        assert whogplug_outlet.power == 1
        assert whogplug_outlet.voltage == 1
        assert whogplug_outlet.energy_today == 1

    def test_whogplug_details_fail(self):
        """Test WhogPlug get_details with bad response."""
        self.mock_api.return_value = BAD_WHOGPLUG_LIST
        whogplug_outlet = VeSyncOutletWhogPlug(DEV_LIST_DETAIL, self.manager)
        whogplug_outlet.get_details()
        assert len(self.caplog.records) == 1
        assert 'details' in self.caplog.text

    def test_whogplug_onoff(self):
        """Test WhogPlug Device On/Off Methods."""
        self.mock_api.return_value = ({'code': 0}, 200)
        whogplug_outlet = VeSyncOutletWhogPlug(DEV_LIST_DETAIL, self.manager)
        head = helpers.req_header_bypass()
        body = helpers.req_body(self.manager, 'bypassV2')
        body['cid'] = whogplug_outlet.cid
        body['configModule'] = whogplug_outlet.config_module
        
        # Test turn_on
        body['payload'] = {
            'data': {
                'enabled': True,
                'id': 0
            },
            'method': 'setSwitch',
            'source': 'APP'
        }
        on = whogplug_outlet.turn_on()
        self.mock_api.assert_called_with(
            '/cloud/v2/deviceManaged/bypassV2',
            'post',
            headers=head,
            json_object=body
        )
        assert on
        
        # Test turn_off
        body['payload'] = {
            'data': {
                'enabled': False,
                'id': 0
            },
            'method': 'setSwitch',
            'source': 'APP'
        }
        off = whogplug_outlet.turn_off()
        self.mock_api.assert_called_with(
            '/cloud/v2/deviceManaged/bypassV2',
            'post',
            headers=head,
            json_object=body
        )
        assert off

    def test_whogplug_onoff_fail(self):
        """Test WhogPlug On/Off Fail with bad response."""
        self.mock_api.return_value = BAD_WHOGPLUG_LIST
        bsdgo1_outlet = VeSyncOutletWhogPlug(DEV_LIST_DETAIL, self.manager)
        assert not bsdgo1_outlet.turn_on()
        assert not bsdgo1_outlet.turn_off() 