"""General VeSync tests."""

import unittest
import importlib
import logging
import asyncio
import orjson
import pytest
from unittest.mock import patch, MagicMock

from pyvesync import VeSync
from pyvesync.utils.errors import VeSyncRateLimitError, VeSyncServerError, VesyncLoginError
from pyvesync.utils.helpers import Helpers, API_BASE_URL
from pyvesync.utils.errors import (
    VeSyncAPIStatusCodeError
    )
from defaults import Defaults
from aiohttp_mocker import AiohttpMockSession

DEFAULT_ENDPOINT = '/endpoint'
DEFAULT_POST_DATA = {'key': 'value'}


def response_dict(code, msg):
    """Return a response dictionary."""
    return orjson.dumps({'code': code, 'msg': msg}, option=orjson.OPT_NON_STR_KEYS)


PARAM_ARGS = "endpoint, method, resp_bytes, resp_status"

# Successful API calls should return the response in bytes and a 200 status code
SUCCESS_RESP = response_dict(0, 'Success')
SUCCESS_PARAMS = [
    pytest.param('/endpoint', 'get', SUCCESS_RESP, 200, id='get_success'),
    pytest.param('/endpoint', 'post', SUCCESS_RESP, 200, id='post_success'),
    pytest.param('/endpoint', 'put', SUCCESS_RESP, 200, id='put_success'),
]

# Rate limit errors should raise an exception in `async_call_api`
RATE_LIMIT_CODE = -11003000
RATE_LIMIT_RESP = response_dict(RATE_LIMIT_CODE, "Rate limit exceeded")
RATE_LIMIT_PARAMS = [
    pytest.param('/endpoint', 'get', RATE_LIMIT_RESP, 200, id='get_rate_limit'),
    pytest.param('/endpoint', 'post', RATE_LIMIT_RESP, 200, id='post_rate_limit'),
    pytest.param('/endpoint', 'put', RATE_LIMIT_RESP, 200, id='put_rate_limit'),
]

# Server errors should raise an exception in `async_call_api`
SERVER_ERROR = -11102000
SERVER_ERROR_RESP = response_dict(SERVER_ERROR, "Server error")
SERVER_ERROR_PARAMS = [
    pytest.param('/endpoint', 'get', SERVER_ERROR_RESP, 200, id='get_server_error'),
    pytest.param('/endpoint', 'post', SERVER_ERROR_RESP, 200, id='post_server_error'),
    pytest.param('/endpoint', 'put', SERVER_ERROR_RESP, 200, id='put_server_error'),
]

# Status code errors should raise an exception in `async_call_api`
STATUS_CODE_ERROR = 400
STATUS_CODE_RESP = None
STATUS_CODE_PARAMS = [
    pytest.param('/endpoint', 'get', STATUS_CODE_RESP, STATUS_CODE_ERROR, id='get_status_code'),
    pytest.param('/endpoint', 'post', STATUS_CODE_RESP, STATUS_CODE_ERROR, id='post_status_code'),
    pytest.param('/endpoint', 'put', STATUS_CODE_RESP, STATUS_CODE_ERROR, id='put_status_code'),
]

# Login errors should not raise an exception in `async_call_api`, but are raised in login() method
STATUS_CODE_ERROR = 400
STATUS_CODE_RESP = None
STATUS_CODE_PARAMS = [
    pytest.param('/endpoint', 'get', STATUS_CODE_RESP, STATUS_CODE_ERROR, id='get_status_code'),
    pytest.param('/endpoint', 'post', STATUS_CODE_RESP, STATUS_CODE_ERROR, id='post_status_code'),
    pytest.param('/endpoint', 'put', STATUS_CODE_RESP, STATUS_CODE_ERROR, id='put_status_code'),
]

# Device errors should return the response and a 200 status code
# with no exception thrown by `async_call_api`
DEVICE_ERROR_CODE = -11901000
DEVICE_ERROR_RESP = response_dict(DEVICE_ERROR_CODE, "Device error")
DEVICE_ERROR_PARAMS = [
    pytest.param('/endpoint', 'get', DEVICE_ERROR_RESP, 200, id='get_device_error'),
    pytest.param('/endpoint', 'post', DEVICE_ERROR_RESP, 200, id='post_device_error'),
    pytest.param('/endpoint', 'put', DEVICE_ERROR_RESP, 200, id='put_device_error'),
]


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
        self.manager = VeSync('EMAIL', 'PASSWORD', debug=True)
        self.manager.enabled = True
        self.manager.token = Defaults.token
        self.manager.account_id = Defaults.account_id
        caplog.set_level(logging.DEBUG)
        yield
        self.mock.stop()
        self.loop.stop()

    async def run_coro(self, coro):
        """Run a coroutine in the event loop."""
        return await coro

    def run_in_loop(self, func, *args, **kwargs):
        """Run a function in the event loop."""
        return asyncio.run_coroutine_threadsafe(self.run_coro(func(*args, **kwargs)), self.loop)

    @pytest.mark.parametrize(PARAM_ARGS, SUCCESS_PARAMS)
    @patch("pyvesync.vesync.ClientSession")
    async def test_api_success(self, mock, endpoint, method, resp_bytes, resp_status):
        """Test successful api call - returns tuple of response bytes and status code."""
        mock.return_value.request.return_value = AiohttpMockSession(
            method=method,
            url=API_BASE_URL + endpoint,
            status=resp_status,
            response=resp_bytes,
        )
        mock_bytes, mock_status = await self.manager.async_call_api("/call/location", method="get")

        assert resp_bytes == mock_bytes
        assert mock_status == resp_status

    @pytest.mark.parametrize(PARAM_ARGS, RATE_LIMIT_PARAMS)
    @patch("pyvesync.vesync.ClientSession")
    async def test_api_rate_limit(self, mock, endpoint, method, resp_bytes, resp_status):
        """Test rate limit error - raises `VeSyncRateLimitError` from `VeSync.async_call_api`."""
        mock.return_value.request.return_value = AiohttpMockSession(
            method=method,
            url=API_BASE_URL + endpoint,
            status=resp_status,
            response=resp_bytes,
        )
        with pytest.raises(VeSyncRateLimitError):
            await self.manager.async_call_api(endpoint, method, json_object=DEFAULT_POST_DATA)

    @pytest.mark.parametrize(PARAM_ARGS, SERVER_ERROR_PARAMS)
    @patch("pyvesync.vesync.ClientSession")
    async def test_api_server_error(self, mock, endpoint, method, resp_bytes, resp_status):
        """Test server error - raises `VeSyncServerError` from `VeSync.async_call_api`."""
        mock.return_value.request.return_value = AiohttpMockSession(
            method=method,
            url=API_BASE_URL + endpoint,
            status=resp_status,
            response=resp_bytes,
        )
        with pytest.raises(VeSyncServerError):
            await self.manager.async_call_api(endpoint, method, json_object=DEFAULT_POST_DATA)

    @pytest.mark.parametrize(PARAM_ARGS, STATUS_CODE_PARAMS)
    @patch("pyvesync.vesync.ClientSession")
    async def test_api_status_code_error(self, mock, endpoint, method, resp_bytes, resp_status):
        """Test status code error - raises `VeSyncAPIStatusCodeError` from `VeSync.async_call_api`."""
        mock.return_value.request.return_value = AiohttpMockSession(
            method=method,
            url=API_BASE_URL + endpoint,
            status=resp_status,
            response=resp_bytes,
        )
        with pytest.raises(VeSyncAPIStatusCodeError):
            await self.manager.async_call_api(endpoint, method, json_object=DEFAULT_POST_DATA)

    @pytest.mark.parametrize(PARAM_ARGS, DEVICE_ERROR_PARAMS)
    @patch("pyvesync.vesync.ClientSession")
    async def test_api_device_error(self, mock, endpoint, method, resp_bytes, resp_status):
        """Test device error - no exception returned from `VeSync.async_call_api`."""
        mock.return_value.request.return_value = AiohttpMockSession(
            method=method,
            url=API_BASE_URL + endpoint,
            status=resp_status,
            response=resp_bytes,
        )
        resp, status = await self.manager.async_call_api(endpoint, method, json_object=DEFAULT_POST_DATA)
        assert resp == resp_bytes
        assert status == resp_status


class TestVesync(unittest.TestCase):
    """Test VeSync object initialization."""

    def setUp(self):
        """Setup VeSync argument cases."""
        self.vesync_1 = VeSync('sam@email.com', 'password', 'America/New_York')
        self.vesync_2 = VeSync('sam@email.com', 'password')
        self.vesync_3 = VeSync('sam@email.com', 'password', None)
        self.vesync_4 = VeSync('sam@email.com', 'password')
        self.vesync_5 = VeSync('', '')
        self.vesync_6 = VeSync(None, None, None)
        self.vesync_7 = VeSync(None, 'password')
        self.vesync_8 = VeSync('sam@email.com', None)
        self.vesync_9 = VeSync('sam@email.com', 'password', 1)

    def tearDown(self):
        """Clean up test."""
        pass

    def test_instance(self):
        """Test VeSync object is successfully initialized."""
        self.assertIsInstance(self.vesync_1, VeSync)

    def test_imports(self):
        """Test that __all__ contains only names that are actually exported."""
        modules = ['pyvesync.vesyncfan',
                   'pyvesync.vesyncbulb',
                   'pyvesync.vesyncoutlet',
                   'pyvesync.vesyncswitch']
        for mod in modules:
            import_mod = importlib.import_module(mod)

            missing = set(n for n in import_mod.__all__
                          if getattr(import_mod, n, None) is None)
            self.assertFalse(
                missing, msg="__all__ contains unresolved names: %s" % (
                    ", ".join(missing),))

    def test_username(self):
        """Test invalid username arguments."""
        self.assertEqual(self.vesync_1.username, 'sam@email.com')
        self.assertEqual(self.vesync_5.username, '')
        self.assertEqual(self.vesync_6.username, None)

        self.vesync_1.username = 'tom@email.com'
        self.assertEqual(self.vesync_1.username, 'tom@email.com')

    def test_password(self):
        """Test invalid password arguments."""
        self.assertEqual(self.vesync_1.password, 'password')
        self.assertEqual(self.vesync_5.password, '')
        self.assertEqual(self.vesync_6.password, None)

        self.vesync_1.password = 'other'
        self.assertEqual(self.vesync_1.password, 'other')

    def test_hash_password(self):
        """Test password hash method."""
        self.assertEqual(
            Helpers.hash_password(self.vesync_1.password),
            '5f4dcc3b5aa765d61d8327deb882cf99',
        )
        self.assertEqual(
            Helpers.hash_password(self.vesync_5.password),
            'd41d8cd98f00b204e9800998ecf8427e',
        )
        with self.assertRaises(AttributeError):
            Helpers.hash_password(self.vesync_6.password)

    def test_time_zone(self):
        """Test time zone argument handling."""
        self.assertEqual(self.vesync_1.time_zone, 'America/New_York')
        self.assertEqual(self.vesync_2.time_zone, 'America/New_York')
        self.assertEqual(self.vesync_3.time_zone, 'America/New_York')
        self.assertEqual(self.vesync_9.time_zone, 'America/New_York')

        self.vesync_1.time_zone = 'America/East'
        self.assertEqual(self.vesync_1.time_zone, 'America/East')

    def NO_test_login(self):
        """Test login method."""
        # Tested in other test cases
        mock_vesync = mock.Mock()
        mock_vesync.login.return_value = True
        self.assertTrue(mock_vesync.login())
        mock_vesync.login.return_value = False
        self.assertFalse(mock_vesync.login())

        with patch('pyvesync.helpers.Helpers.call_api') as mocked_post:
            d = {
                'result': {
                    'accountID': '12346536',
                    'userType': '1',
                    'token': 'somevaluehere',
                },
                'code': 0,
            }
            mocked_post.return_value = (d, 200)

            data = self.vesync_1.login()
            body = Helpers.req_body(self.vesync_1, 'login')
            body['email'] = self.vesync_1.username
            body['password'] = Helpers.hash_password(self.vesync_1.password)
            mocked_post.assert_called_with('/cloud/v1/user/login', 'post',
                                           json_object=body)
            self.assertTrue(data)


if __name__ == '__main__':
    unittest.main()
