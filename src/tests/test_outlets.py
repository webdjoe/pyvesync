"""
This tests all requests made by outlet devices.

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
`call_json_outlets` - Contains API responses
"""

import pytest
import logging
from pyvesync.vesync import object_factory
from utils import TestBase, assert_test, parse_args
import call_json
import call_json_outlets
from utils import Defaults


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

OUTLET_DEV_TYPES = call_json_outlets.OUTLETS
POWER_METHODS = ['get_energy_update']
OUTLET_PARAMS = []
[OUTLET_PARAMS.append([dev, method]
                      ) for dev in OUTLET_DEV_TYPES for method in POWER_METHODS]


class TestOutlets(TestBase):
    """Outlets testing class.

    This class tests outlets device details and methods. The methods are
    parametrized from the class variables using `pytest_generate_tests`.
    The call_json_outlets module contains the responses for the API requests.
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
    ---------------
    device : str
        Name of device type - outlets
    outlets : list
        List of device types for outlets, this variable is named
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
    >>> device = 'outlets'
    >>> outlets = ['ESW01-USA', 'ESW01-EU', 'ESW01-AU']
    >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
    >>> device_methods = {
        'dev_type': [['method1'], ['method2', {'kwargs': 'value'}]]
        }

    """

    device = 'outlets'
    outlets = call_json_outlets.OUTLETS
    base_methods = [['turn_on'], ['turn_off'], ['get_yearly_energy'],
                    ['get_monthly_energy'], ['get_weekly_energy']]
    device_methods = {
        'ESW15-USA': [['turn_on_nightlight'], ['turn_off_nightlight']],
    }

    def test_details(self, dev_type, method):
        """Test the device details API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of device type - outlets),
        device name (outlets) list of device types.

        Example:
            >>> device = 'outlets'
            >>> outlets = ['ESW01-USA', 'ESW01-EU', 'ESW01-AU']

        See Also
        --------
        `utils.TestBase` class docstring
        `call_json_outlets` module docstring

        Notes
        ------
        The device is instantiated using the `call_json.DeviceList.device_list_item()`
        method. The device details contain the default values set in `utils.Defaults`
        """
        # Set return value for call_api based on call_json_bulb.DETAILS_RESPONSES
        self.mock_api.return_value = call_json_outlets.DETAILS_RESPONSES[dev_type]

        # Instantiate device from device list return item
        device_config = call_json.DeviceList.device_list_item(dev_type)
        _, outlet_obj = object_factory(dev_type,
                                       device_config,
                                       self.manager)

        # Get and run method from object
        method_call = getattr(outlet_obj, method)
        method_call()

        # Parse mock_api args tuple from arg, kwargs to kwargs
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recored request or write new records
        assert_test(method_call, all_kwargs, dev_type)

        # Assert device attributes match default values
        assert int(outlet_obj.details['active_time']) == int(Defaults.active_time)
        assert int(outlet_obj.details['energy']) == int(
            call_json_outlets.OutletDefaults.energy)
        assert int(outlet_obj.details['power']) == int(
            call_json_outlets.OutletDefaults.power)
        assert int(outlet_obj.details['voltage']) == int(
            call_json_outlets.OutletDefaults.voltage)

    def test_methods(self, dev_type, method):
        """Test device methods API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of device type - outlets),
        device name (outlets) list of device types, `base_methods` - list of
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
        `call_json_outlets` module

        """
        # Get method name and kwargs from method fixture
        method_name = method[0]
        if len(method) == 2 and isinstance(method[1], dict):
            method_kwargs = method[1]
        else:
            method_kwargs = {}

        # Set return value for call_api based on call_json_bulbs.METHOD_RESPONSES
        method_response = call_json_outlets.METHOD_RESPONSES[dev_type][method_name]
        if callable(method_response):
            if method_kwargs:
                self.mock_api.return_value = method_response(**method_kwargs)
            else:
                self.mock_api.return_value = method_response()
        else:
            self.mock_api.return_value = method_response

        # Get device configuration from call_json.DeviceList.device_list_item()
        device_config = call_json.DeviceList.device_list_item(dev_type)

        # Instantiate device from device list return item
        _, outlet_obj = object_factory(dev_type,
                                       device_config,
                                       self.manager)

        # Ensure method runs based on device configuration
        if method[0] == 'turn_on':
            outlet_obj.device_status == 'off'
        if method[0] == 'turn_off':
            outlet_obj.device_status == 'on'

        # Get method from device object
        method_call = getattr(outlet_obj, method[0])

        # Call method with kwargs if present
        if method_kwargs:
            method_call(method_kwargs)
        else:
            method_call()

        # Parse arguments from mock_api call into a dictionary
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recored request or write new records
        assert_test(method_call, all_kwargs, dev_type)

        # Test bad responses
        self.mock_api.reset_mock()
        if dev_type == 'wifi-switch-1.3':
            self.mock_api.return_value = (None, 400)
        else:
            self.mock_api.return_value = call_json.DETAILS_BADCODE
        if method[0] == 'turn_on':
            outlet_obj.device_status == 'off'
        if method[0] == 'turn_off':
            outlet_obj.device_status == 'on'
        if 'energy' in method[0]:
            return
        assert method_call() is False

    @pytest.mark.parametrize('dev_type', OUTLET_DEV_TYPES)
    def test_power(self, dev_type):
        """Test outlets power history methods."""
        self.mock_api.return_value = call_json_outlets.ENERGY_HISTORY
        device_config = call_json.DeviceList.device_list_item(dev_type)
        _, outlet_obj = object_factory(dev_type, device_config, self.manager)
        outlet_obj.update_energy()
        assert self.mock_api.call_count == 3
        assert list(outlet_obj.energy.keys()) == ['week', 'month', 'year']
        self.mock_api.reset_mock()
        outlet_obj.energy = {}
        if dev_type == 'wifi-switch-1.3':
            self.mock_api.return_value = (None, 400)
        else:
            self.mock_api.return_value = call_json.DETAILS_BADCODE
        outlet_obj.update_energy()
        self.mock_api.call_count == 0
        outlet_obj.update_energy(bypass_check=True)
        self.mock_api.assert_called_once()
        assert 'Unable to get' in self.caplog.records[-1].message
