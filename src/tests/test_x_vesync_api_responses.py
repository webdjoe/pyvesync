"""General VeSync tests."""

import logging
import asyncio
import orjson
import pytest
from unittest.mock import patch, MagicMock

from pyvesync import VeSync
from pyvesync.utils.errors import VeSyncRateLimitError, VeSyncServerError
from pyvesync.const import API_BASE_URL_US
from pyvesync.utils.errors import (
    VeSyncAPIStatusCodeError
    )
from defaults import TestDefaults
from aiohttp_mocker import AiohttpMockSession

DEFAULT_ENDPOINT = '/endpoint'
DEFAULT_POST_DATA = {'key': 'value'}


def response_dict(code, msg):
    """Return a response dictionary."""
    return {'code': code, 'msg': msg}


PARAM_ARGS = "endpoint, method, resp_bytes, resp_status"

# Successful API calls should return the response in bytes and a 200 status code
SUCCESS_RESP = response_dict(0, 'Success')


# Rate limit errors should raise an exception in `async_call_api`
RATE_LIMIT_CODE = -11003000
RATE_LIMIT_RESP = response_dict(RATE_LIMIT_CODE, "Rate limit exceeded")


# Server errors should raise an exception in `async_call_api`
SERVER_ERROR = -11102000
SERVER_ERROR_RESP = response_dict(SERVER_ERROR, "Server error")


# Status code errors should raise an exception in `async_call_api`
STATUS_CODE_ERROR = 400
STATUS_CODE_RESP = None


# Login errors should not raise an exception in `async_call_api`, but are raised in login() method
STATUS_CODE_ERROR = 400
STATUS_CODE_RESP = None


# Device errors should return the response and a 200 status code
# with no exception thrown by `async_call_api`
DEVICE_ERROR_CODE = -11901000
DEVICE_ERROR_RESP = response_dict(DEVICE_ERROR_CODE, "Device error")


class TestApiFunc:
    """Test call_api() method."""
    @pytest.fixture(autouse=True, scope='function')
    def setup(self, caplog):
        """Fixture to instantiate VeSync object, start logging and start Mock.

        Attributes
        ----------
        self.mock_api : Mock
        self.manager : VeSync
        self.caplog : LogCaptureFixture

        Yields
        ------
        Class instance with mocked call_api() function and VeSync object
        """
        self.caplog = caplog
        self.caplog.set_level(logging.DEBUG)
        self.loop = asyncio.new_event_loop()
        # self.mock_api = self.mock_api_call.start()
        # self.mock_api.return_value.ok = True
        # self.mock = aioresponses()
        # self.mock.start()
        self.mock = MagicMock()
        self.manager = VeSync('EMAIL', 'PASSWORD')
        self.manager.verbose = True
        self.manager.enabled = True
        self.manager.auth._token = TestDefaults.token
        self.manager.auth._account_id = TestDefaults.account_id
        caplog.set_level(logging.DEBUG)
        yield
        self.mock.stop()
        self.loop.stop()

    async def run_coro(self, coro):
        """Run a coroutine in the event loop."""
        return await coro

    def run_in_loop(self, func, *args, **kwargs):
        """Run a function in the event loop."""
        return self.loop.run_until_complete(self.run_coro(func(*args, **kwargs)))

    @patch("pyvesync.vesync.ClientSession")
    def test_api_success(self, mock):
        """Test successful api call - returns tuple of response bytes and status code."""
        mock.return_value.request.return_value = AiohttpMockSession(
            method='post',
            url=API_BASE_URL_US + DEFAULT_ENDPOINT,
            status=200,
            response=orjson.dumps(SUCCESS_RESP),
        )
        resp = self.run_in_loop(self.manager.async_call_api, DEFAULT_ENDPOINT, method="get")
        mock_dict, mock_status = resp

        assert SUCCESS_RESP == mock_dict
        assert mock_status == 200

    @patch("pyvesync.vesync.ClientSession")
    def test_api_rate_limit(self, mock):
        """Test rate limit error - raises `VeSyncRateLimitError` from `VeSync.async_call_api`."""
        rate_limit_resp = response_dict(RATE_LIMIT_CODE, "Rate limit exceeded")
        mock.return_value.request.return_value = AiohttpMockSession(
            method="post",
            url=API_BASE_URL_US + DEFAULT_ENDPOINT,
            status=200,
            response=orjson.dumps(rate_limit_resp),
        )
        with pytest.raises(VeSyncRateLimitError):
            self.run_in_loop(self.manager.async_call_api, DEFAULT_ENDPOINT, 'post', json_object=DEFAULT_POST_DATA)

    @patch("pyvesync.vesync.ClientSession")
    def test_api_server_error(self, mock):
        """Test server error - raises `VeSyncServerError` from `VeSync.async_call_api`."""
        mock.return_value.request.return_value = AiohttpMockSession(
            method='post',
            url=API_BASE_URL_US + DEFAULT_ENDPOINT,
            status=200,
            response=orjson.dumps(SERVER_ERROR_RESP),
        )
        with pytest.raises(VeSyncServerError):
            self.run_in_loop(self.manager.async_call_api, DEFAULT_ENDPOINT, 'post', json_object=DEFAULT_POST_DATA)

    @patch("pyvesync.vesync.ClientSession")
    def test_api_status_code_error(self, mock):
        """Test status code error - raises `VeSyncAPIStatusCodeError` from `VeSync.async_call_api`."""
        mock.return_value.request.return_value = AiohttpMockSession(
            method='get',
            url=API_BASE_URL_US + DEFAULT_ENDPOINT,
            status=404,
            response=None,
        )
        with pytest.raises(VeSyncAPIStatusCodeError):
            self.run_in_loop(self.manager.async_call_api, DEFAULT_ENDPOINT, 'get')
