"""
This tests requests made by switch devices.

All tests inherit from the TestBase class which contains the fixtures
and methods needed to run the tests.

The tests are automatically parametrized by `pytest_generate_tests` in
conftest.py. The two methods that are parametrized are `test_details`
and `test_methods`. The class variables are used to build the list of
devices, test methods and arguments.

The `helpers.call_api` method is patched to return a mock response.
The method, endpoint, headers and json arguments are recorded
in YAML files in the api directory, catagorized in folders by
module and files by the class name.

The default is to record requests that do not exist and compare requests
that already exist. If the API changes, set the overwrite argument to True
in order to overwrite the existing YAML file with the new request.

See Also
--------
`utils.TestBase` - Base class for all tests, containing mock objects
`confest.pytest_generate_tests` - Parametrizes tests based on
    method names & class attributes
`call_json_switches` - Contains API responses
"""

import logging
from pyvesync.base_devices.switch_base import VeSyncSwitch
import pyvesync.const as const
from base_test_cases import TestBase
from utils import assert_test, parse_args
from defaults import TestDefaults
import call_json
import call_json_switches


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEFAULT_COLOR = TestDefaults.color.rgb
COLOR_DICT = {
    'red': DEFAULT_COLOR.red,
    'blue': DEFAULT_COLOR.blue,
    'green': DEFAULT_COLOR.green,
}


class TestSwitches(TestBase):
    """Switches testing class.

    This class tests switch device details and methods. The methods are
    parametrized from the class variables using `pytest_generate_tests`.
    The call_json_switches module contains the responses for the API requests.
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
        Name of device type - switches
    switches : list
        List of device types for switches, this variable is named
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
    >>> device = 'switches'
    >>> switches = call_json_switches.SWITCHES
    >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
    >>> device_methods = {
        'ESWD16': [['method1'], ['method2', {'kwargs': 'value'}]]
        }

    """

    device = 'switches'
    switches = call_json_switches.SWITCHES
    base_methods = [['turn_on'], ['turn_off']]
    device_methods = {
        'ESWD16': [['turn_on_indicator_light'],
                   ['turn_on_rgb_backlight'],
                   ['set_backlight_color', COLOR_DICT],
                   ['set_brightness', {'brightness': TestDefaults.brightness}]],
    }

    def test_details(self, setup_entry, method):
        """Test the device details API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of device type - switches),
        device name (switches) list of device types.

        Example:
            >>> device = 'switches'
            >>> switches = call_json_switches.SWITCHES

        See Also
        --------
        `utils.TestBase` class docstring
        `call_json_switches` module docstring

        Notes
        ------
        The device is instantiated using the `call_json.DeviceList.device_list_item()`
        method. The device details contain the default values set in `utils.Defaults`
        """
        # Set return value for call_api based on call_json_bulb.DETAILS_RESPONSES
        resp_dict = call_json_switches.DETAILS_RESPONSES[setup_entry]
        self.mock_api.return_value = resp_dict, 200

        # Instantiate device from device list return item
        device_map = call_json.ALL_DEVICE_MAP_DICT[setup_entry]
        device_config = call_json.DeviceList.device_list_item(device_map)
        switch_obj = self.get_device("switches", device_config)
        assert isinstance(switch_obj, VeSyncSwitch)

        self.run_in_loop(switch_obj.get_details)

        # Parse mock_api args tuple from arg, kwargs to kwargs
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recored request or write new records
        assert_test(switch_obj.get_details, all_kwargs, setup_entry, self.write_api, self.overwrite)

        # Assert device details match expected values
        if switch_obj.supports_dimmable:
            assert switch_obj.state.brightness == str(TestDefaults.brightness)
            assert switch_obj.state.indicator_status == 'on'
            assert switch_obj.state.backlight_status == 'on'
            assert switch_obj.state.backlight_color is not None
            assert switch_obj.state.backlight_color.rgb.to_dict() == COLOR_DICT
        self.mock_api.reset_mock()
        bad_dict, status = call_json.DETAILS_BADCODE
        self.mock_api.return_value = bad_dict, status
        self.run_in_loop(switch_obj.get_details)
        assert 'details' in self.caplog.records[-1].message

    def test_methods(self, setup_entry, method):
        """Test switch methods API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of device type - switches),
        device name (switches) list of device types, `base_methods` - list of
        methods for all devices, and `device_methods` - list of methods for
        each device type.

        Example:
            >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
            >>> device_methods = {
                'dev_type': [['method1'], ['method2', {'kwargs': 'value'}]]
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
        `call_json_switches` module

        """
        # Get method name and kwargs from method fixture
        method_name = method[0]
        if len(method) == 2 and isinstance(method[1], dict):
            method_kwargs = method[1]
        else:
            method_kwargs = {}

        # Set return value for call_api based on call_json_switches.METHOD_RESPONSES
        method_response = call_json_switches.METHOD_RESPONSES[setup_entry][method_name]
        if callable(method_response):
            if method_kwargs:
                resp_dict = method_response(**method_kwargs)
            else:
                resp_dict = method_response()
        else:
            resp_dict = method_response
        self.mock_api.return_value = resp_dict, 200
        # Get device configuration from call_json.DeviceList.device_list_item()
        device_map = call_json.ALL_DEVICE_MAP_DICT[setup_entry]
        device_config = call_json.DeviceList.device_list_item(device_map)
        switch_obj = self.get_device("switches", device_config)
        assert isinstance(switch_obj, VeSyncSwitch)

        # Get method from device object
        method_call = getattr(switch_obj, method[0])

        # Ensure method runs based on device configuration
        if method[0] == 'turn_on':
            switch_obj.state.device_status = const.DeviceStatus.OFF
        elif method[0] == 'turn_off':
            switch_obj.state.device_status = const.DeviceStatus.ON

        # Call method with kwargs if defined
        if method_kwargs:
            self.run_in_loop(method_call, **method_kwargs)
        else:
            self.run_in_loop(method_call)

        # Parse arguments from mock_api call into a dictionary
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recored request or write new records
        assert_test(method_call, all_kwargs, setup_entry,
                    self.write_api, self.overwrite)

        self.mock_api.reset_mock()
        resp_dict, status = call_json.DETAILS_BADCODE
        self.mock_api.return_value = resp_dict, status
        if method_kwargs:
            return_val = self.run_in_loop(method_call, **method_kwargs)
            assert return_val is False
        else:
            return_val = self.run_in_loop(method_call)
            assert return_val is False
