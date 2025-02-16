"""
This tests requests for Humidifiers and Air Purifiers.

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
`call_json_fans` - Contains API responses
"""

import logging
import orjson
import pytest
from pyvesync.vesync import object_factory
from utils import TestBase, assert_test, parse_args
from defaults import Defaults
import call_json
import call_json_fans


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEFAULT_COLOR = Defaults.color
DEFAULT_COLOR_RGB = dict(DEFAULT_COLOR.rgb._asdict())
DEFAULT_COLOR_HSV = dict(DEFAULT_COLOR.hsv._asdict())
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


class TestAirPurifiers(TestBase):
    """Air Purifier testing class.

    This class tests Air Purifier device details and methods.
    The methods are parametrized from the class variables using
    `pytest_generate_tests`. The call_json_fans module contains the responses
    for the API requests. The device is instantiated from the details provided by
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
    ---------------
    device : str
        Name of device type - air_purifiers
    air_purifiers : list
        List of device types for air purifiers, this variable is named
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
    >>> device = 'air_purifiers'
    >>> air_purifiers = call_json_fans.AIR_MODELS
    >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
    >>> device_methods = {
        'ESWD16': [['method1'], ['method2', {'kwargs': 'value'}]]
        }
    """

    device = 'air_purifiers'
    air_purifiers = call_json_fans.AIR_MODELS
    base_methods = [['turn_on'], ['turn_off'], ['sleep_mode'], ['manual_mode'],
                    ['change_fan_speed', {'speed': 3}]]
    device_methods = {
        'Core300S': [['auto_mode'], ['turn_on_display'], ['turn_off_display'],
                     ['set_timer', {'timer_duration': 100}], ['clear_timer']],
        'Core400S': [['auto_mode'], ['turn_on_display'], ['turn_off_display'],
                     ['set_timer', {'timer_duration': 100}], ['clear_timer']],
        'Core600S': [['auto_mode'], ['turn_on_display'], ['turn_off_display'],
                     ['set_timer', {'timer_duration': 100}], ['clear_timer']],

    }

    def test_details(self, dev_type, method):
        """Test the device details API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of device type - air_purifiers),
        device name (air_purifiers) list of device types.

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
        return_dict, status_code = call_json_fans.DETAILS_RESPONSES[dev_type]
        return_val = (orjson.dumps(return_dict), status_code)
        self.mock_api.return_value = return_val

        # Instantiate device from device list return item
        device_config = call_json.DeviceList.device_list_item(dev_type)
        _, fan_obj = object_factory(dev_type,
                                    device_config,
                                    self.manager)
        method_call = getattr(fan_obj, method)
        self.run_in_loop(method_call)

        # Parse mock_api args tuple from arg, kwargs to kwargs
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recored request or write new records
        assert_test(method_call, all_kwargs, dev_type, self.write_api, self.overwrite)

    def test_methods(self, dev_type, method):
        """Test device methods API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of device type - air_purifiers),
        device name (air_purifiers) list of device types, `base_methods` - list of
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
        `call_json_fans` module

        """
        # TODO: FIX `clear_timer` recorded API request in yaml
        if method[0] == 'clear_timer':
            pytest.skip("Incorrect clear_timer API request")
        # Get method name and kwargs from method fixture
        method_name = method[0]
        if len(method) == 2 and isinstance(method[1], dict):
            method_kwargs = method[1]
        else:
            method_kwargs = {}

        # Set return value for call_api based on call_json_fans.METHOD_RESPONSES
        method_response = call_json_fans.METHOD_RESPONSES[dev_type][method_name]
        if callable(method_response):
            if method_kwargs:
                return_dict, status_code = method_response(method_kwargs)
            else:
                return_dict, status_code = method_response()
        else:
            return_dict, status_code = method_response
        self.mock_api.return_value = (orjson.dumps(return_dict), status_code)

        # Get device configuration from call_json.DeviceList.device_list_item()
        device_config = call_json.DeviceList.device_list_item(dev_type)

        # Instantiate device from device list return item
        _, fan_obj = object_factory(dev_type,
                                    device_config,
                                    self.manager)

        # Get method from device object
        method_call = getattr(fan_obj, method[0])

        # Ensure method runs based on device configuration
        if method[0] == 'turn_on':
            fan_obj.device_status = 'off'
        elif method[0] == 'turn_off':
            fan_obj.device_status = 'on'
        elif method[0] == 'change_fan_speed':
            fan_obj.mode = 'manual'
            fan_obj.details['level'] = 1
        elif method[0] == 'clear_timer':
            fan_obj.timer = call_json_fans.FAN_TIMER

        # Call method with kwargs if defined
        if method_kwargs:
            self.run_in_loop(method_call, **method_kwargs)
        else:
            self.run_in_loop(method_call)

        # Parse arguments from mock_api call into a dictionary
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recored request or write new records
        assert_test(method_call, all_kwargs, dev_type,
                    self.write_api, self.overwrite)


class TestHumidifiers(TestBase):
    """Humidifier testing class.

    This class tests Humidifier device details and methods. The methods are
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
        Name of device type - humidifiers
    humidifers : list
        List of device types for humidifiers, this variable is named
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
    >>> device = 'humidifiers'
    >>> humidifiers = call_json_fans.HUMID_MODELS
    >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
    >>> device_methods = {
        'ESWD16': [['method1'], ['method2', {'kwargs': 'value'}]]
        }

    """

    device = 'humidifiers'
    humidifiers = call_json_fans.HUMID_MODELS
    base_methods = [['turn_on'], ['turn_off'], ['turn_on_display'], ['turn_off_display'],
                    ['automatic_stop_on'], ['automatic_stop_off'],
                    ['set_humidity', {'humidity': 50}], ['set_auto_mode'],
                    ['set_manual_mode'], ['set_mist_level', {'level': 2}]
                    ]
    device_methods = {
        'LUH-A602S-WUSR': [['set_warm_level', {'warm_level': 3}]],
        'LEH-S601S-WUS': [['set_drying_mode_enabled', {'mode': False}]]
    }

    def test_details(self, dev_type, method):
        """Test the device details API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of device type - fans),
        device name (fans) list of device types.

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
        return_dict, status_code = call_json_fans.DETAILS_RESPONSES[dev_type]
        return_val = (orjson.dumps(return_dict), status_code)
        self.mock_api.return_value = return_val

        # Instantiate device from device list return item
        device_config = call_json.DeviceList.device_list_item(dev_type)
        _, fan_obj = object_factory(dev_type,
                                    device_config,
                                    self.manager)
        method_call = getattr(fan_obj, method)
        self.run_in_loop(method_call)

        # Parse mock_api args tuple from arg, kwargs to kwargs
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recorded request or write new records
        assert_test(method_call, all_kwargs, dev_type,
                    self.write_api, self.overwrite)

    def test_methods(self, dev_type, method):
        """Test device methods API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of device type - humidifiers),
        device name (humidifiers) list of device types, `base_methods` - list of
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
        `call_json_fans` module

        """
        # Get method name and kwargs from method fixture
        method_name = method[0]
        if len(method) == 2 and isinstance(method[1], dict):
            method_kwargs = method[1]
        else:
            method_kwargs = {}

        # Set return value for call_api based on call_json_fans.METHOD_RESPONSES
        method_response = call_json_fans.METHOD_RESPONSES[dev_type][method_name]
        if callable(method_response):
            if method_kwargs:
                self.mock_api.return_value = method_response(method_kwargs)
            else:
                self.mock_api.return_value = method_response()
        else:
            self.mock_api.return_value = method_response

        # Get device configuration from call_json.DeviceList.device_list_item()
        device_config = call_json.DeviceList.device_list_item(dev_type)

        # Instantiate device from device list return item
        _, fan_obj = object_factory(dev_type,
                                    device_config,
                                    self.manager)

        # Get method from device object
        method_call = getattr(fan_obj, method[0])

        # Ensure method runs based on device configuration
        if method[0] == 'turn_on':
            fan_obj.device_status = 'off'
        elif method[0] == 'turn_off':
            fan_obj.device_status = 'on'

        # Call method with kwargs if defined
        if method_kwargs:
            self.run_in_loop(method_call, **method_kwargs)
        else:
            self.run_in_loop(method_call)

        # Parse arguments from mock_api call into a dictionary
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recored request or write new records
        assert_test(method_call, all_kwargs, dev_type,
                    self.write_api, self.overwrite)
