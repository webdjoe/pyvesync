"""
This tests requests for AIR FRYERS.

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
`call_json_fryers` - Contains API responses
"""

import logging
import pytest
import pyvesync.const as const
from pyvesync.base_devices.fryer_base import VeSyncFryer
from base_test_cases import TestBase
from utils import assert_test, parse_args
import call_json_fryers


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


DETAILS_PARAMS_STANDBY = [
    pytest.param(
        const.AirFryerCookStatus.STANDBY,
        "CS158-AF",
        "update",
        call_json_fryers.DETAILS_RESPONSES_STANDBY["CS158-AF"],
        id="CS158-AF.update.standby",
    ),
    pytest.param(
        const.AirFryerCookStatus.STANDBY,
        "CAF-DC601S",
        "update",
        call_json_fryers.DETAILS_RESPONSES_STANDBY["CAF-DC601S"],
        id="CAF-DC601S.update.standby",
    ),
    pytest.param(
        const.AirFryerCookStatus.STANDBY,
        "CAF-TF101S",
        "update",
        call_json_fryers.DETAILS_RESPONSES_STANDBY["CAF-TF101S"],
        id="CAF-TF101S.update.standby",
    ),
]

DETAILS_PARAMS_COOKING = [
    pytest.param(
        const.AirFryerCookStatus.COOKING,
        "CS158-AF",
        "update",
        call_json_fryers.DETAILS_RESPONSES_COOKING["CS158-AF"],
        id="CS158-AF.update.cooking",
    ),
    pytest.param(
        const.AirFryerCookStatus.COOKING,
        "CAF-DC601S",
        "update",
        call_json_fryers.DETAILS_RESPONSES_COOKING["CAF-DC601S"],
        id="CAF-DC601S.update.cooking",
    ),
    pytest.param(
        const.AirFryerCookStatus.COOKING,
        "CAF-TF101S",
        "update",
        call_json_fryers.DETAILS_RESPONSES_COOKING["CAF-TF101S"],
        id="CAF-TF101S.update.cooking",
    ),
]


class TestFryers(TestBase):
    """Fryer testing class.

    This class tests Fryer product details and methods. The methods are
    parametrized from the class variables using `pytest_generate_tests`.
    The call_json_fryers module contains the responses for the API requests.
    The device is instantiated from the details provided by
    `call_json_fryers.DeviceList.device_list_item()`. Inherits from `utils.TestBase`.

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
        Name of product class - fryers
    fryers : list
        List of setup_entry's for fryers, this variable is named
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
    >>> device = 'fryers'
    >>> fryers = call_json_fryers.FRYER_MODELS
    >>> base_methods = [['turn_on'], ['turn_off'], ['update']]
    >>> device_methods = {
        'ESWD16': [['method1'], ['method2', {'kwargs': 'value'}]]
        }

    """

    device = 'fryers'
    fryers = call_json_fryers.FRYERS
    base_methods = []  # type: ignore
    device_methods = {  # type: ignore
        "CS158-AF": [],
        "CAF-DC601S": [],
        "CAF-TF101S": [],
    }

    @pytest.mark.parametrize(
        "cook_status, setup_entry, method, response_dict",
        DETAILS_PARAMS_STANDBY + DETAILS_PARAMS_COOKING,
    )
    def test_details_fryers(self, cook_status: const.AirFryerCookStatus, setup_entry: str, method: str, response_dict: dict):
        """Test the device details API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of product class - fryers),
        device name (fryers) list of setup_entry's.

        Example:
            >>> device = 'fryers'
            >>> fryers = call_json_fryers.FRYERS

        See Also
        --------
        `utils.TestBase` class docstring
        `call_json_fryers` module docstring

        Notes
        ------
        The device is instantiated using the `call_json.DeviceList.device_list_item()`
        method. The device details contain the default values set in `utils.Defaults`
        """
        # Set return value for call_api based on call_json_fan.DETAILS_RESPONSES
        return_dict = response_dict
        self.mock_api.return_value = (return_dict, 200)

        # Instantiate device from device list return item
        fryer_obj = self.get_device("air_fryers", setup_entry)
        assert isinstance(fryer_obj, VeSyncFryer)

        method_call = getattr(fryer_obj, method)
        self.run_in_loop(method_call)

        # Parse mock_api args tuple from arg, kwargs to kwargs
        all_kwargs = parse_args(self.mock_api)

        if cook_status == const.AirFryerCookStatus.STANDBY:
            assert fryer_obj.state_chamber_1.cook_status == cook_status
            assert fryer_obj.state_chamber_1.cook_set_temp is None
            assert fryer_obj.state_chamber_1.cook_set_time is None
            assert fryer_obj.state_chamber_1.cook_mode is None
            assert fryer_obj.state_chamber_1.current_temp is None
            assert fryer_obj.state_chamber_1.preheat_last_time is None
            assert fryer_obj.state_chamber_1.cook_last_time is None
            assert fryer_obj.state_chamber_1.last_timestamp is None
            if const.AirFryerFeatures.DUAL_CHAMBER in fryer_obj.features:
                assert fryer_obj.state_chamber_2.cook_status == cook_status
                assert fryer_obj.state_chamber_2.cook_set_temp is None
                assert fryer_obj.state_chamber_2.cook_set_time is None
                assert fryer_obj.state_chamber_2.cook_mode is None
                assert fryer_obj.state_chamber_2.current_temp is None
                assert fryer_obj.state_chamber_2.preheat_last_time is None
                assert fryer_obj.state_chamber_2.cook_last_time is None
                assert fryer_obj.state_chamber_2.last_timestamp is None

        elif cook_status == const.AirFryerCookStatus.COOKING:
            assert fryer_obj.state_chamber_1.cook_status == cook_status
            assert fryer_obj.state_chamber_1.cook_set_temp == call_json_fryers.AirFryerDefaults.cook_temp_f
            assert fryer_obj.state_chamber_1.cook_set_time == call_json_fryers.AirFryerDefaults.cook_time_s
            assert fryer_obj.state_chamber_1.cook_mode is not None
            assert fryer_obj.state_chamber_1.cook_last_time == call_json_fryers.AirFryerDefaults.cook_last_time_s
            if const.AirFryerFeatures.DUAL_CHAMBER in fryer_obj.features:
                # Chamber 2 should be standby in cooking test data
                assert fryer_obj.state_chamber_2.cook_status == const.AirFryerCookStatus.STANDBY

        # Assert request matches recorded request or write new records
        assert assert_test(
            method_call, all_kwargs, setup_entry, self.write_api, self.overwrite
        )
