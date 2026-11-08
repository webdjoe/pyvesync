"""Manager and device container failure handling tests.

A device whose class rejects it must be skipped without stopping discovery,
and an unexpected error while updating a device must be logged.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, patch

import pytest
from base_test_cases import TestBase
from call_json import ALL_DEVICE_MAP_DICT, DeviceList

from pyvesync.models.vesync_models import (
    ResponseDeviceDetailsModel,
    ResponseDeviceListModel,
)
from pyvesync.utils.errors import VeSyncAPIResponseError, VeSyncServerError
from pyvesync.utils.helpers import Helpers
from pyvesync.utils.logs import LibraryLogger

_PAGE = {'total': 1, 'pageSize': 100, 'pageNo': 1}


class TestManagerResilience(TestBase):
    """Failure handling in device discovery and update_all_devices()."""

    def test_device_class_error_skips_device_with_warning(self):
        # The CS158 class raises VeSyncError for a config module missing from
        # AIRFRYER_PID_MAP.
        config = DeviceList.device_list_item(ALL_DEVICE_MAP_DICT['CS158-AF'])
        config['configModule'] = 'WiFi_SKA_AirFryer158_XX'
        self.manager.devices.add_device_from_model(
            ResponseDeviceDetailsModel.from_dict(config), self.manager
        )
        assert self.manager.devices.air_fryers == []
        assert 'WiFi_SKA_AirFryer158_XX' in self.caplog.text
        other = DeviceList.device_list_item(ALL_DEVICE_MAP_DICT['CAF-DC601S'])
        self.manager.devices.add_device_from_model(
            ResponseDeviceDetailsModel.from_dict(other), self.manager
        )
        assert len(self.manager.devices.air_fryers) == 1

    def test_update_all_devices_logs_unexpected_errors(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        with patch.object(
            type(fryer), 'update', new=AsyncMock(side_effect=RuntimeError('boom'))
        ):
            self.run_in_loop(self.manager.update_all_devices)
        assert 'Unexpected error updating device: boom' in self.caplog.text

    def test_parse_error_debug_log_redacts_the_response(self):
        # A row with no deviceRegion fails to parse, so the response is dumped.
        row = DeviceList.device_list_item(ALL_DEVICE_MAP_DICT['CAF-DC601S'])
        row.pop('deviceRegion')
        row['cid'] = 'cid-not-for-logs'
        body = {
            'traceId': 'trace',
            'code': 0,
            'msg': 'request success',
            'result': {'total': 1, 'pageSize': 100, 'pageNo': 1, 'list': [row]},
        }
        logger = logging.getLogger('pyvesync.vesync')
        with (
            patch.object(LibraryLogger, 'debug_enabled', True),
            patch.object(LibraryLogger, 'shouldredact', True),
            self.caplog.at_level(logging.DEBUG, logger='pyvesync.vesync'),
        ):
            model = Helpers.model_maker(
                logger, ResponseDeviceListModel, 'get_devices', body
            )
        assert model is None
        assert 'Full Response' in self.caplog.text
        assert 'cid-not-for-logs' not in self.caplog.text

    @pytest.mark.parametrize(
        'result',
        [
            None,
            [],
            '',
            0,
            False,
            {},
            {**_PAGE, 'list': None},
            {**_PAGE, 'list': [5]},
            {**_PAGE, 'list': [{'deviceType': 'CAF-DC111S-AEU'}]},
        ],
    )
    def test_get_devices_malformed_result_raises_api_error(self, result):
        body = DeviceList.device_list_response('CAF-DC111S-AEU')
        body['result'] = result
        self.mock_api.return_value = (body, 200)
        with pytest.raises(VeSyncAPIResponseError, match='Invalid device list response'):
            self.run_in_loop(self.manager.get_devices)
        assert self.manager.in_process is False

    def test_get_devices_missing_result_raises_api_error(self):
        body = DeviceList.device_list_response('CAF-DC111S-AEU')
        body.pop('result')
        self.mock_api.return_value = (body, 200)
        with pytest.raises(VeSyncAPIResponseError, match='Invalid device list response'):
            self.run_in_loop(self.manager.get_devices)
        assert self.manager.in_process is False

    def test_get_devices_no_json_response_raises_api_error(self):
        self.mock_api.return_value = (None, 200)
        with pytest.raises(VeSyncAPIResponseError):
            self.run_in_loop(self.manager.get_devices)
        assert self.manager.in_process is False

    def test_get_devices_malformed_result_keeps_known_devices(self):
        body = DeviceList.device_list_response('CAF-DC111S-AEU')
        self.mock_api.return_value = (body, 200)
        assert self.run_in_loop(self.manager.get_devices) is True
        self.mock_api.return_value = ({**body, 'result': None}, 200)
        with pytest.raises(VeSyncAPIResponseError):
            self.run_in_loop(self.manager.get_devices)
        assert len(self.manager.devices.air_fryers) == 1

    def test_get_devices_api_error_with_null_result_keeps_code_and_msg(self):
        # An unknown code passes async_call_api() and reaches get_devices().
        body = {'traceId': 'trace', 'code': 987654, 'msg': 'list refused', 'result': None}
        self.mock_api.return_value = (body, 200)
        with pytest.raises(VeSyncAPIResponseError, match='list refused'):
            self.run_in_loop(self.manager.get_devices)
        assert self.manager.in_process is False

    def test_get_devices_server_error_with_null_result(self):
        body = {'traceId': 'trace', 'code': -11102000, 'msg': None, 'result': None}
        self.mock_api.return_value = (body, 200)
        with pytest.raises(VeSyncServerError):
            self.run_in_loop(self.manager.get_devices)
        assert self.manager.in_process is False

    @pytest.mark.parametrize(
        'error',
        [VeSyncServerError('offline'), RuntimeError('offline'), asyncio.CancelledError()],
    )
    def test_get_devices_request_error_clears_in_process(self, error):
        self.mock_api.side_effect = error
        with pytest.raises(type(error)) as caught:
            self.run_in_loop(self.manager.get_devices)
        assert caught.value is error
        assert self.manager.in_process is False

    def test_get_devices_logged_out_clears_in_process(self):
        self.manager.auth._token = None
        assert self.run_in_loop(self.manager.get_devices) is False
        assert self.manager.in_process is False
        self.mock_api.assert_not_called()

    def test_get_devices_processing_error_clears_in_process(self):
        self.mock_api.return_value = (
            DeviceList.device_list_response('CAF-DC111S-AEU'),
            200,
        )
        with (
            patch.object(
                type(self.manager), 'process_devices', side_effect=RuntimeError('offline')
            ),
            pytest.raises(RuntimeError),
        ):
            self.run_in_loop(self.manager.get_devices)
        assert self.manager.in_process is False

    def test_get_devices_valid_list_clears_in_process(self):
        self.mock_api.return_value = (
            DeviceList.device_list_response('CAF-DC111S-AEU'),
            200,
        )
        assert self.run_in_loop(self.manager.get_devices) is True
        assert len(self.manager.devices.air_fryers) == 1
        assert self.manager.in_process is False
