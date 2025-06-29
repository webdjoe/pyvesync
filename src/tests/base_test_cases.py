"""Contains base test cases for mocking devices and API calls."""


import asyncio
import logging
import pytest
from unittest.mock import MagicMock, patch

from pyvesync import VeSync
from defaults import Defaults, API_DEFAULTS


class TestApiFunc:
    """Test case to instantiate vs object and patch the session object."""
    default_endpoint = '/endpoint'

    @pytest.fixture(autouse=True, scope='function')
    def setup(self, caplog):
        """Fixture to instantiate VeSync object, start logging and start Mock.


        Yields:
            self: Class instance with mocked session object to test response handling.
        """
        self.mock_api_call = patch("pyvesync.vesync.ClientSession")
        self.caplog = caplog
        self.caplog.set_level(logging.DEBUG)
        self.mock_api = self.mock_api_call.start()
        self.loop = asyncio.new_event_loop()
        self.mock = MagicMock()
        self.manager = VeSync(API_DEFAULTS['EMAIL'], API_DEFAULTS['PASSWORD'])
        self.manager.verbose = True
        self.manager.enabled = True
        self.manager.redact = False
        self.manager._token = Defaults.token
        self.manager._account_id = Defaults.account_id
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


class TestBase:
    """Base class for tests with the call_api() method mocked.

    Contains instantiated VeSync object and mocked API call for call_api() function.

    Attributes:
        mock_api (Mock): Mock for call_api() function.
        manager (VeSync): Instantiated VeSync object that is logged in.
        caplog (LogCaptureFixture): Pytest fixture for capturing logs.
    """
    overwrite = False
    write_api = False

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
        self.loop = asyncio.new_event_loop()
        self.mock_api_call = patch('pyvesync.vesync.VeSync.async_call_api')
        self.caplog = caplog
        self.caplog.set_level(logging.DEBUG)
        self.mock_api = self.mock_api_call.start()
        self.mock_api.return_value.ok = True
        self.manager = VeSync('EMAIL', 'PASSWORD')
        self.manager.debug = True
        self.manager.verbose = True
        self.manager.redact = False
        self.manager.time_zone = Defaults.time_zone
        self.manager.enabled = True
        self.manager._token = Defaults.token
        self.manager._account_id = Defaults.account_id
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    async def run_coro(self, coro):
        """Run a coroutine in the event loop."""
        return await coro

    def run_in_loop(self, func, *args, **kwargs):
        """Run a function in the event loop."""
        return self.loop.run_until_complete(self.run_coro(func(*args, **kwargs)))
