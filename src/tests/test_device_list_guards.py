"""Device-list envelope and busy-flag regressions from PR 564."""

import asyncio
from unittest.mock import patch

import pytest
from base_test_cases import TestBase
from call_json import DeviceList

from pyvesync.utils.errors import VeSyncAPIResponseError, VeSyncServerError


class TestDeviceListGuards(TestBase):
    @pytest.mark.parametrize('result', [None, [], '', 0, False])
    def test_invalid_result_is_classified_and_busy_flag_cleared(self, result):
        body = DeviceList.device_list_response('CAF-DC111S-AEU')
        body['result'] = result
        self.mock_api.return_value = (body, 200)
        with pytest.raises(VeSyncAPIResponseError, match='result must be an object'):
            self.run_in_loop(self.manager.get_devices)
        assert self.manager.in_process is False

    @pytest.mark.parametrize('body', [None, [], 'invalid'])
    def test_invalid_outer_response_clears_busy_flag(self, body):
        self.mock_api.return_value = (body, 200)
        with pytest.raises(VeSyncAPIResponseError):
            self.run_in_loop(self.manager.get_devices)
        assert self.manager.in_process is False

    def test_missing_result_is_classified(self):
        body = DeviceList.device_list_response('CAF-DC111S-AEU')
        body.pop('result')
        self.mock_api.return_value = (body, 200)
        with pytest.raises(VeSyncAPIResponseError):
            self.run_in_loop(self.manager.get_devices)
        assert self.manager.in_process is False

    @pytest.mark.parametrize('error', [VeSyncServerError('offline test'), RuntimeError('offline test'), asyncio.CancelledError()])
    def test_request_error_clears_busy_flag_without_masking(self, error):
        self.mock_api.side_effect = error
        with pytest.raises(type(error)) as caught:
            self.run_in_loop(self.manager.get_devices)
        assert caught.value is error
        assert self.manager.in_process is False

    def test_logged_out_path_clears_busy_flag_without_request(self):
        self.manager.auth._token = None
        assert self.run_in_loop(self.manager.get_devices) is False
        assert self.manager.in_process is False
        self.mock_api.assert_not_called()

    def test_server_error_with_null_result_keeps_server_classification(self):
        body = DeviceList.device_list_response('CAF-DC111S-AEU')
        body['code'] = -11102000  # Existing INTERNAL_ERROR / SERVER_ERROR code.
        body['result'] = None
        self.mock_api.return_value = (body, 200)
        with pytest.raises(VeSyncServerError):
            self.run_in_loop(self.manager.get_devices)
        assert self.manager.in_process is False

    def test_valid_list_still_discovers_the_fryer(self):
        self.mock_api.return_value = (DeviceList.device_list_response('CAF-DC111S-AEU'), 200)
        assert self.run_in_loop(self.manager.get_devices) is True
        assert len(self.manager.devices.air_fryers) == 1
        assert self.manager.in_process is False

    def test_processing_error_clears_busy_flag(self):
        self.mock_api.return_value = (DeviceList.device_list_response('CAF-DC111S-AEU'), 200)
        with patch.object(type(self.manager), 'process_devices', side_effect=RuntimeError('offline test')):
            with pytest.raises(RuntimeError):
                self.run_in_loop(self.manager.get_devices)
        assert self.manager.in_process is False
