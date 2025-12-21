"""
This tests requests made by bulb devices.

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
`call_json_bulbs` - Contains API responses
"""

import logging
import math
from dataclasses import asdict
import pyvesync.const as const
from pyvesync.utils.helpers import Converters
from pyvesync.base_devices.bulb_base import VeSyncBulb
from base_test_cases import TestBase
from utils import assert_test, parse_args
from defaults import TestDefaults
import call_json_bulbs


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEFAULT_COLOR = TestDefaults.color
DEFAULT_COLOR_RGB = dict(asdict(DEFAULT_COLOR.rgb))
DEFAULT_COLOR_HSV = dict(asdict(DEFAULT_COLOR.hsv))
RGB_SET = {
    'red': 50,
    'green': 200,
    'blue': 255,

}
HSV_SET = {
    'hue': 200,
    'saturation': 50,
    'value': 100,
}


class TestBulbs(TestBase):
    """Bulbs testing class.

    This class tests bulb device details and methods. The methods are
    parametrized from the class variables using `pytest_generate_tests`.
    The call_json_bulbs module contains the responses for the API requests.
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

    Class Attributes
    -----------------
    device : str
        Name of product class - bulbs
    bulbs : list
        List of setup_entry's for bulbs, this variable is named
        after the device class attribute value
    base_methods : List[List[str, Dict[str, Any]]]
        List of common methods for all devices
    device_methods : Dict[List[List[str, Dict[str, Any]]]]
        Dictionary of methods specific to setup_entry's for each
        device.

    Methods
    --------
    test_details()
        Test the device details API request and response
    test_methods()
        Test device methods API request and response

    Examples
    --------
    >>> device = 'bulbs'
    >>> bulbs = call_json_bulbs.bulbs
    >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
    >>> device_methods = {
        'ESWD16': [['method1'], ['method2', {'kwargs': 'value'}]]
        }

    """

    device = 'bulbs'
    bulbs = call_json_bulbs.BULBS
    base_methods = [['turn_on'], ['turn_off'], ['set_brightness', {'brightness': 50}]]
    device_methods = {
        'ESL100CW': [['set_color_temp', {'color_temp': 50}]],
        'ESL100MC': [['set_rgb', RGB_SET],
                     ['set_white_mode']],
        'XYD0001': [['set_hsv', HSV_SET],
                    ['set_color_temp', {'color_temp': 50}],
                    ['set_white_mode']
                    ]
    }

    def test_details(self, setup_entry, method):
        """Test the device details API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class attribute `device` (name of product class - bulbs),
        device name (bulbs) list of `setup_entry` strings for each object.

        Example:
            >>> device = 'bulbs'
            >>> bulbs = call_json_bulbs.BULBS

        See Also
        --------
        `utils.TestBase` class docstring
        `call_json_bulbs` module docstring

        Notes
        ------
        The device is instantiated using the `call_json.DeviceList.device_list_item()`
        method. The device details contain the default values set in `utils.Defaults`
        """
        # Set return value for call_api based on call_json_bulb.DETAILS_RESPONSES
        return_dict = call_json_bulbs.DETAILS_RESPONSES[setup_entry]
        return_val = (return_dict, 200)
        self.mock_api.return_value = return_val

        # Instantiate device from device list return item
        bulb_obj = self.get_device("bulbs", setup_entry)
        assert isinstance(bulb_obj, VeSyncBulb)

        method_call = getattr(bulb_obj, method)
        self.run_in_loop(method_call)

        # Parse mock_api args tuple from arg, kwargs to kwargs
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recorded request or write new records
        assert assert_test(
            method_call, all_kwargs, setup_entry, self.write_api, self.overwrite
        )

        # Assert device details match expected values
        assert bulb_obj.state.brightness == TestDefaults.brightness
        if bulb_obj.supports_multicolor:
            assert self._assert_color(bulb_obj)
        if bulb_obj.supports_color_temp:
            assert bulb_obj.state.color_temp == TestDefaults.color_temp
            assert bulb_obj.state.color_temp_kelvin == Converters.color_temp_pct_to_kelvin(TestDefaults.color_temp)

    def test_methods(self, setup_entry, method):
        """Test device methods API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of product class - bulbs),
        device name (bulbs) list of `setup_entry`'s, `base_methods` - list of
        methods for all devices, and `device_methods` - list of methods for
        each setup_entry.

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
        `call_json_bulbs` module

        """
        # Get method name and kwargs from method fixture
        method_name = method[0]
        if len(method) == 2 and isinstance(method[1], dict):
            method_kwargs = method[1]
        else:
            method_kwargs = {}

        # Set return value for call_api based on call_json_bulbs.METHOD_RESPONSES
        method_response = call_json_bulbs.METHOD_RESPONSES[setup_entry][method_name]
        if callable(method_response):
            if method_kwargs:
                self.mock_api.return_value = method_response(method_kwargs), 200
            else:
                self.mock_api.return_value = method_response(), 200
        else:
            self.mock_api.return_value = method_response, 200

        # Get device configuration from call_json.DeviceList.device_list_item()

        bulb_obj = self.get_device("bulbs", setup_entry)
        assert isinstance(bulb_obj, VeSyncBulb)

        # Get method from device object
        method_call = getattr(bulb_obj, method[0])

        # Ensure method runs based on device configuration
        if method[0] == 'turn_on':
            bulb_obj.state.device_status = const.DeviceStatus.OFF
        elif method[0] == 'turn_off':
            bulb_obj.state.device_status = const.DeviceStatus.ON

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

    def _assert_color(self, bulb_obj):
        assert math.isclose(bulb_obj.state.color.rgb.red, DEFAULT_COLOR.rgb.red, rel_tol=1)
        assert math.isclose(bulb_obj.state.color.rgb.green, DEFAULT_COLOR.rgb.green, rel_tol=1)
        assert math.isclose(bulb_obj.state.color.rgb.blue, DEFAULT_COLOR.rgb.blue, rel_tol=1)
        assert math.isclose(bulb_obj.state.color.hsv.hue, DEFAULT_COLOR.hsv.hue, rel_tol=1)
        assert math.isclose(bulb_obj.state.color.hsv.saturation,
                            DEFAULT_COLOR.hsv.saturation,
                            rel_tol=1)
        assert math.isclose(bulb_obj.state.color.hsv.value, DEFAULT_COLOR.hsv.value, rel_tol=1)
        return True
