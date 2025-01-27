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
from utils import TestBase, assert_test, parse_args
import call_json
import call_json_outlets


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

OUTLET_DEV_TYPES = call_json_outlets.OUTLETS
POWER_METHODS = ['get_energy_update']
OUTLET_PARAMS = [[dev, method] for dev in OUTLET_DEV_TYPES for method in POWER_METHODS]


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
    base_methods = [
        ['turn_on'],
        ['turn_off']
    ]
    device_methods = {
        'ESW15-USA': [
            ['turn_on_nightlight'],
            ['turn_off_nightlight']
        ],
        'wifi-switch-1.3': [
            ['get_weekly_energy'],
            ['get_monthly_energy'],
            ['get_yearly_energy']
        ],
        'ESW03-USA': [
            ['get_weekly_energy'],
            ['get_monthly_energy'],
            ['get_yearly_energy']
        ],
        'ESW01-EU': [
            ['get_weekly_energy'],
            ['get_monthly_energy'],
            ['get_yearly_energy']
        ],
        'ESW15-USA': [
            ['get_weekly_energy'],
            ['get_monthly_energy'],
            ['get_yearly_energy']
        ],
        'ESO15-TB': [
            ['get_weekly_energy'],
            ['get_monthly_energy'],
            ['get_yearly_energy']
        ]
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
        """        # Get response for device details
        details_response = call_json_outlets.DETAILS_RESPONSES[dev_type]
        if callable(details_response):
            self.mock_api.return_value = details_response()
        else:
            self.mock_api.return_value = details_response

        # Get device configuration
        device_config = call_json.DeviceList.device_list_item(dev_type)

        # Instantiate device
        outlet_obj = self.manager.object_factory(dev_type, device_config)

        # Call get_details() directly
        assert outlet_obj.get_details() == True

        # Parse arguments from mock_api call into dictionary
        all_kwargs = parse_args(self.mock_api)

        # Set both write_api and overwrite to True to update YAML files
        assert outlet_obj.get_details() == True
        assert_test(outlet_obj.get_details, all_kwargs, dev_type,
                   write_api=True, overwrite=True)

        # Test bad responses
        self.mock_api.reset_mock()
        if dev_type == 'wifi-switch-1.3':
            self.mock_api.return_value = (None, 400)
        else:
            self.mock_api.return_value = call_json.DETAILS_BADCODE
        assert outlet_obj.get_details() == False
        assert len(self.caplog.records) == 1
        assert 'Failed' in self.caplog.text

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

        """        # Get method name and kwargs from method fixture
        method_name = method[0]
        if len(method) == 2 and isinstance(method[1], dict):
            method_kwargs = method[1]
        else:
            method_kwargs = {}

        # Set return value for call_api based on METHOD_RESPONSES
        method_response = call_json_outlets.METHOD_RESPONSES[dev_type][method_name]
        if callable(method_response):
            if method_kwargs:
                self.mock_api.return_value = method_response(**method_kwargs)
            else:
                self.mock_api.return_value = method_response()
        else:
            self.mock_api.return_value = method_response

        # Get device configuration
        device_config = call_json.DeviceList.device_list_item(dev_type)

        # Instantiate device
        outlet_obj = self.manager.object_factory(dev_type, device_config)

        # Get method from device object
        method_call = getattr(outlet_obj, method[0])

        # Ensure method runs based on device configuration
        outlet_obj.device_status = 'offline'

        # Call method with kwargs if present
        if method_kwargs:
            method_call(**method_kwargs)
        else:
            method_call()

        # Parse arguments from mock_api call into dictionary
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recorded request or write new records
        if ('data' in all_kwargs):
            if ('headers' in all_kwargs):
                all_kwargs['json_object'] = all_kwargs['data']
            else:
                all_kwargs['headers'] = all_kwargs['data']
            del all_kwargs['data']
        assert_test(method_call, all_kwargs, dev_type,
                   self.write_api, self.overwrite)

        # Test bad responses
        self.mock_api.reset_mock()
        if dev_type == 'wifi-switch-1.3':
            self.mock_api.return_value = (None, 400)
        else:
            self.mock_api.return_value = call_json.DETAILS_BADCODE
        if method[0] == 'turn_on':
            outlet_obj.device_status = 'off'
        if method[0] == 'turn_off':
            outlet_obj.device_status = 'on'
        if 'energy' in method[0]:
            return
        assert method_call() is False

    @pytest.mark.parametrize('dev_type', [d for d in OUTLET_DEV_TYPES if (d != 'BSDOG01') and (d != 'WYSMTOD16A')])
    def test_energy(self, dev_type):
        """Test outlets power history methods."""
        self.mock_api.return_value = call_json_outlets.ENERGY_HISTORY

        # Get device configuration
        device_config = call_json.DeviceList.device_list_item(dev_type)

        # Instantiate device
        outlet_obj = self.manager.object_factory(dev_type, device_config)
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
        assert self.mock_api.call_count == 0
        outlet_obj.update_energy(bypass_check=True)
        self.mock_api.assert_called_once()
        assert 'Unable to get' in self.caplog.records[-1].message
