"""
This tests requests for FANS (not purifiers or humidifiers).

All tests inherit from the TestBase class which contains the fixtures
and methods needed to run the tests.

The tests are automatically parametrized by `pytest_generate_tests` in
conftest.py. The two methods that are parametrized are `test_details`
and `test_methods`. The class variables are used to build the list of
devices, test methods and arguments.

The `helpers.call_api` method is patched to return a mock response.
The method, endpoint, headers and json arguments are recorded
in YAML files in the api directory, categorized in folders by
module and files by the class name.

The default is to record requests that do not exist and compare requests
that already exist. If the API changes, set the overwrite argument to True
in order to overwrite the existing YAML file with the new request.

See Also
--------
`utils.TestBase` - Base class for all tests, containing mock objects
`confest.pytest_generate_tests` - Parametrizes tests based on
    method names & class attributes
`call_json_fans` - Contains API responses
"""

import logging
from dataclasses import asdict
import pyvesync.const as const
from pyvesync.base_devices.fan_base import VeSyncFanBase
from base_test_cases import TestBase
from utils import assert_test, parse_args
from defaults import TestDefaults
import call_json_fans


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEFAULT_COLOR = TestDefaults.color
DEFAULT_COLOR_RGB = dict(asdict(DEFAULT_COLOR.rgb))
DEFAULT_COLOR_HSV = dict(asdict(DEFAULT_COLOR.hsv))


class TestFans(TestBase):
    """Fan testing class.

    This class tests Fan product details and methods. The methods are
    parametrized from the class variables using `pytest_generate_tests`.
    The call_json_fans module contains the responses for the API requests.
    The device is instantiated from the details provided by
    `call_json.DeviceList.device_list_item()`. Inherits from `utils.TestBase`.

    Instance Attributes
    -------------------
    self.manager : VeSync
        Instantiated VeSync object
    self.mock_api : Mock
        Mock with patched `helpers.call_api` method
    self.caplog : LogCaptureFixture
        Pytest fixture for capturing logs

    Class Variables
    ---------------
    device : str
        Name of product class - humidifiers
    humidifers : list
        List of setup_entry's for humidifiers, this variable is named
        after the device variable value
    base_methods : List[List[str, Dict[str, Any]]]
        List of common methods for all devices
    device_methods : Dict[List[List[str, Dict[str, Any]]]]
        Dictionary of methods specific to device types

    Methods
    --------
    test_details()
        Test the device details API request and response
    test_methods()
        Test device methods API request and response

    Examples
    --------
    >>> device = 'fans'
    >>> fans = call_json_fans.FAN_MODELS
    >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
    >>> device_methods = {
        'ESWD16': [['method1'], ['method2', {'kwargs': 'value'}]]
        }

    """

    device = 'fans'
    fans = call_json_fans.FANS
    base_methods = [['turn_on'], ['turn_off'], ['set_fan_speed', {'speed': 3}],]
    device_methods = {
        "LTF-F422S": [
            ["turn_off_oscillation",],
            ["turn_off_mute",],
        ],
        "LPF-R423S": [
            ["turn_off_vertical_oscillation",],
            ["turn_off_horizontal_oscillation",],
            ["set_horizontal_oscillation_range", {"left": 10, "right": 80}],
            ["set_vertical_oscillation_range", {"top": 100, "bottom": 20}],
        ],
    }

    def test_details(self, setup_entry, method):
        """Test the device details API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of product class - fans),
        device name (fans) list of setup_entry's.

        Example:
            >>> device = 'air_purifiers'
            >>> air_purifiers = call_json_fans.AIR_MODELS

        See Also
        --------
        `utils.TestBase` class docstring
        `call_json_fans` module docstring

        Notes
        ------
        The device is instantiated using the `call_json.DeviceList.device_list_item()`
        method. The device details contain the default values set in `utils.Defaults`
        """
        # Set return value for call_api based on call_json_fan.DETAILS_RESPONSES
        return_dict = call_json_fans.DETAILS_RESPONSES[setup_entry]
        self.mock_api.return_value = (return_dict, 200)

        # Instantiate device from device list return item
        fan_obj = self.get_device("fans", setup_entry)
        assert isinstance(fan_obj, VeSyncFanBase)

        method_call = getattr(fan_obj, method)
        self.run_in_loop(method_call)

        # Parse mock_api args tuple from arg, kwargs to kwargs
        all_kwargs = parse_args(self.mock_api)

        # Assert state is set correctly
        assert fan_obj.state.device_status == call_json_fans.FanDefaults.fan_status
        assert fan_obj.state.display_set_status == call_json_fans.FanDefaults.screen_status
        if fan_obj.supports_oscillation:
            assert fan_obj.state.oscillation_status == call_json_fans.FanDefaults.oscillation_status

        if fan_obj.supports_horizontal_oscillation:
            assert fan_obj.state.horizontal_oscillation_status == call_json_fans.FanDefaults.oscillation_horizontal
        if fan_obj.supports_vertical_oscillation:
            assert fan_obj.state.vertical_oscillation_status == call_json_fans.FanDefaults.oscillation_vertical
        if fan_obj.supports_mute:
            assert fan_obj.state.mute_status == call_json_fans.FanDefaults.mute_status

        # Assert request matches recorded request or write new records
        assert assert_test(
            method_call, all_kwargs, setup_entry, self.write_api, self.overwrite
        )

    def test_methods(self, setup_entry, method):
        """Test device methods API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of product class - humidifiers),
        device name (humidifiers) list of setup_entry's, `base_methods` - list of
        methods for all devices, and `device_methods` - list of methods for
        each device type.

        Example:
            >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
            >>> device_methods = {
                'setup_entry': [['method1'], ['method2', {'kwargs': 'value'}]]
                }

        Notes
        -----
        The response can be a callable that accepts the `kwargs` argument to
        sync the device response with the API response. In some cases the API
        returns data from the method call, such as `get_yearly_energy`, in other cases the
        API returns a simple confirmation the command was successful.

        See Also
        --------
        `TestBase` class method
        `call_json_fans` module

        """
        # Get method name and kwargs from method fixture
        method_name = method[0]
        if len(method) == 2 and isinstance(method[1], dict):
            method_kwargs = method[1]
        else:
            method_kwargs = {}

        # Set return value for call_api based on call_json_fans.METHOD_RESPONSES
        method_response = call_json_fans.METHOD_RESPONSES[setup_entry][method_name]
        if callable(method_response):
            if method_kwargs:
                self.mock_api.return_value = method_response(method_kwargs), 200
            else:
                self.mock_api.return_value = method_response(), 200
        else:
            self.mock_api.return_value = method_response, 200

        # Get device configuration from call_json.DeviceList.device_list_item()
        fan_obj = self.get_device("fans", setup_entry)
        assert isinstance(fan_obj, VeSyncFanBase)

        # Get method from device object
        method_call = getattr(fan_obj, method[0])

        # Ensure method runs based on device configuration
        if method[0] == 'turn_on':
            fan_obj.state.device_status = const.DeviceStatus.OFF
        elif method[0] == 'turn_off':
            fan_obj.state.device_status = const.DeviceStatus.ON

        # Call method with kwargs if defined
        if method_kwargs:
            self.run_in_loop(method_call, **method_kwargs)
        else:
            self.run_in_loop(method_call)

        # Parse arguments from mock_api call into a dictionary
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recorded request or write new records
        assert assert_test(
            method_call, all_kwargs, setup_entry, self.write_api, self.overwrite
        )
