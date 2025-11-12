"""Contains base test cases for mocking devices and API calls."""

from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import pytest
from unittest.mock import MagicMock, patch

from pyvesync import VeSync
from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
from defaults import TestDefaults, API_DEFAULTS
from call_json import ALL_DEVICE_MAP_DICT, DeviceList

if TYPE_CHECKING:
    from pyvesync.base_devices import VeSyncBaseDevice


class TestApiFunc:
    """Test case to instantiate vs object and patch the session object."""
    default_endpoint = '/endpoint'

    @pytest.fixture(autouse=True, scope='function')
    def setup(self, caplog):
        """Fixture to instantiate VeSync object, start logging and start Mock.

        This fixture mocks the ClientSession object directly.

        Yields:
            self: Class instance with mocked session object to test response handling.
        """
        self.mock_api_call = patch("pyvesync.vesync.ClientSession")
        self.caplog = caplog
        self.mock_api = self.mock_api_call.start()
        self.loop = asyncio.new_event_loop()
        self.mock = MagicMock()
        self.manager = VeSync(API_DEFAULTS['EMAIL'], API_DEFAULTS['PASSWORD'])
        self.manager.enabled = True
        self.manager.redact = False
        self.manager.auth._token = TestDefaults.token
        self.manager.auth._account_id = TestDefaults.account_id
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
        self.mock_api = self.mock_api_call.start()
        self.mock_api.return_value.ok = True
        self.manager = VeSync(TestDefaults.email, TestDefaults.password)
        self.manager.redact = False
        self.manager.time_zone = TestDefaults.time_zone
        self.manager.enabled = True
        self.manager.auth._token = TestDefaults.token
        self.manager.auth._account_id = TestDefaults.account_id
        yield
        self.mock_api_call.stop()

    async def run_coro(self, coro):
        """Run a coroutine in the event loop."""
        return await coro

    def run_in_loop(self, func, *args, **kwargs) -> VeSyncBaseDevice | None:
        """Run a function in the event loop."""
        return self.loop.run_until_complete(self.run_coro(func(*args, **kwargs)))

    def get_device(self, product_type: str, setup_entry: str) -> VeSyncBaseDevice:
        """Get device from device details dict.

        Args:
            device_details (dict): Device details dictionary from call_json module.

        Returns:
            Device object from VeSync.devices
        """
        if len(self.manager.devices) > 0:
            self.manager.devices.clear()
        device_map = ALL_DEVICE_MAP_DICT[setup_entry]
        device_config = DeviceList.device_list_item(device_map)
        self.manager.devices.add_device_from_model(
            ResponseDeviceDetailsModel.from_dict(device_config), self.manager
        )
        device_list = getattr(self.manager.devices, product_type)
        assert len(device_list) == 1, f"Could not instantiate {product_type} device."
        return device_list[0]
