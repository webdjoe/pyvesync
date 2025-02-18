"""Test scripts for WYSMTOD16A Outlets."""

from unittest.mock import patch
from pyvesync.vesyncoutlet import VeSyncOutletWYSMTOD16A
from pyvesync.helpers import Helpers as helpers
import call_json
import call_json_outlets
from utils import Defaults, TestBase

DEVICE_TYPE = 'WYSMTOD16A'

DEV_LIST_DETAIL = call_json.DeviceList.device_list_item(DEVICE_TYPE)

CORRECT_WYSMTOD16A_LIST = call_json.DeviceList.device_list_response(DEVICE_TYPE)

CORRECT_WYSMTOD16A_DETAILS = call_json_outlets.DETAILS_RESPONSES[DEVICE_TYPE]

BAD_WYSMTOD16A_LIST = call_json.DETAILS_BADCODE


class TestVeSyncWYSMTOD16ASwitch(TestBase):
    """Test WYSMTOD16A outlet API."""

    def test_wysmtod16a_conf(self):
        """Test initialization of WYSMTOD16A outlet."""
        self.mock_api.return_value = CORRECT_WYSMTOD16A_LIST
        self.manager.get_devices()
        outlets = self.manager.outlets
        assert len(outlets) == 1
        wysmtod16a_outlet = outlets[0]
        assert isinstance(wysmtod16a_outlet, VeSyncOutletWYSMTOD16A)
        assert wysmtod16a_outlet.device_name == call_json.Defaults.name(DEVICE_TYPE)
        assert wysmtod16a_outlet.device_type == DEVICE_TYPE
        assert wysmtod16a_outlet.cid == call_json.Defaults.cid(DEVICE_TYPE)
        assert wysmtod16a_outlet.uuid == call_json.Defaults.uuid(DEVICE_TYPE)

    def test_wysmtod16a_details(self):
        """Test WYSMTOD16A get_details()."""
        self.mock_api.return_value = CORRECT_WYSMTOD16A_DETAILS
        wysmtod16a_outlet = VeSyncOutletWYSMTOD16A(DEV_LIST_DETAIL, self.manager)
        wysmtod16a_outlet.get_details()
        response = CORRECT_WYSMTOD16A_DETAILS
        properties = response.get('result', {}).get('result', {})
        expected_status = 'on' if properties.get('powerSwitch_1') == 1 else 'off'
        assert wysmtod16a_outlet.device_status == expected_status

    def test_wysmtod16a_details_fail(self):
        """Test WYSMTOD16A get_details with bad response."""
        self.mock_api.return_value = BAD_WYSMTOD16A_LIST
        wysmtod16a_outlet = VeSyncOutletWYSMTOD16A(DEV_LIST_DETAIL, self.manager)
        wysmtod16a_outlet.get_details()
        assert len(self.caplog.records) == 1
        assert 'FAILED' in self.caplog.text

    def test_wysmtod16a_onoff(self):
        """Test WYSMTOD16A Device On/Off Methods."""
        self.mock_api.return_value = {'code': 0, 'msg': 'success', 'result': {'code': 0}}
        wysmtod16a_outlet = VeSyncOutletWYSMTOD16A(DEV_LIST_DETAIL, self.manager)
        head = self.manager.req_header_bypass()
        body = {
            **self.manager.req_body_bypass_v2(),
            'cid': wysmtod16a_outlet.cid,
            'configModule': wysmtod16a_outlet.config_module,
            'payload': {
                'method': 'setSwitch',
                'source': 'APP',
                'data': {'enabled': True, 'id': 0},
            }
        }
        assert wysmtod16a_outlet.turn_on()
        self.mock_api.assert_called_with(
            api='/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

        # Test turn_off
        body['payload'] = {
            'method': 'setSwitch',
            'source': 'APP',
            'data': {'enabled': False, 'id': 0},
        }
        assert wysmtod16a_outlet.turn_off()
        self.mock_api.assert_called_with(
            api='/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=head,
            json_object=body,
        )

    def test_wysmtod16a_onoff_fail(self):
        """Test WYSMTOD16A On/Off Fail with bad response."""
        self.mock_api.return_value = BAD_WYSMTOD16A_LIST
        wysmtod16a_outlet = VeSyncOutletWYSMTOD16A(DEV_LIST_DETAIL, self.manager)
        assert not wysmtod16a_outlet.turn_on()
        assert not wysmtod16a_outlet.turn_off()

