"""
This tests requests for Air Purifiers.

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
import pytest

import pyvesync.const as const
from pyvesync.base_devices.purifier_base import VeSyncPurifier
from base_test_cases import TestBase
from utils import assert_test, parse_args
from pyvesync.utils.helpers import Timer
import call_json_purifiers


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
        Name of product class - air_purifiers
    air_purifiers : list
        List of setup_entry's for air purifiers, this variable is named
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

    device = "air_purifiers"
    air_purifiers = call_json_purifiers.PURIFIER_MODELS
    base_methods = [
        ["turn_on"],
        ["turn_off"],
        ["set_sleep_mode"],
        ["set_manual_mode"],
        ["set_fan_speed", {"speed": 3}],
    ]
    # TODO: Add timer tests
    device_methods = {
        "Core200S": [["set_sleep_mode"],],
        "Core300S": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],
        "Core400S": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],
        "Core600S": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],
        "LV-PUR131S": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],
        "LV-RH131S": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],
        "LAP-V102S": [["set_auto_mode"], ['set_sleep_mode'], ['set_pet_mode'], ["turn_on_display"], ["turn_off_display"]],
        "LAP-V201S": [["set_auto_mode"], ['set_sleep_mode'], ['set_pet_mode'], ["turn_on_display"], ["turn_off_display"]],
        "EL551S": [["set_auto_mode"], ["set_sleep_mode"], ["set_turbo_mode"], ["turn_on_display"], ["turn_off_display"]],
        "LAP-B851S-WUS": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],
        "LAP-P501S": [
            ["set_auto_mode"],
            ["set_auto_mode_type", {"auto_mode_type": "odorShieldQuiet"}],
            ["set_sleep_mode"],
            ["turn_on_display"],
            ["turn_off_display"],
            ["turn_on_child_lock"],
            ["turn_off_child_lock"],
            ["turn_on_buzzer"],
            ["turn_off_buzzer"],
            ["turn_on_auto_clean"],
            ["turn_off_auto_clean"],
            ["set_timer", {"duration": 1800}],
            ["get_timer"],
        ],
    }

    def test_details(self, setup_entry, method):
        """Test the device details API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of product class - air_purifiers),
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
        return_dict = call_json_purifiers.DETAILS_RESPONSES[setup_entry]
        return_val = (return_dict, 200)
        self.mock_api.return_value = return_val

        # Instantiate device from device list return item
        fan_obj = self.get_device("air_purifiers", setup_entry)
        assert isinstance(fan_obj, VeSyncPurifier)

        method_call = getattr(fan_obj, method)
        self.run_in_loop(method_call)

        # Test state attributes
        assert fan_obj.state.device_status == const.DeviceStatus.ON
        assert fan_obj.state.mode == call_json_purifiers.PurifierDefaults.purifier_mode
        assert fan_obj.state.fan_level == call_json_purifiers.PurifierDefaults.fan_level

        # Parse mock_api args tuple from arg, kwargs to kwargs
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recorded request or write new records
        assert assert_test(
            method_call, all_kwargs, setup_entry, self.write_api, self.overwrite
        )

    def test_methods(self, setup_entry, method):
        """Test device methods API request and response.

        This method is automatically parametrized by `pytest_generate_tests`
        based on class variables `device` (name of product class - air_purifiers),
        device name (air_purifiers) list of setup_entry's, `base_methods` - list of
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
        # TODO: FIX `clear_timer` recorded API request in yaml
        if method[0] == "clear_timer":
            pytest.skip("Incorrect clear_timer API request")
        # Get method name and kwargs from method fixture
        method_name = method[0]
        if len(method) == 2 and isinstance(method[1], dict):
            method_kwargs = method[1]
        else:
            method_kwargs = {}

        # Set return value for call_api based on call_json_fans.METHOD_RESPONSES
        method_response = call_json_purifiers.METHOD_RESPONSES[setup_entry][method_name]
        if callable(method_response):
            if method_kwargs:
                return_dict = method_response(method_kwargs)
            else:
                return_dict = method_response()
        else:
            return_dict = method_response
        self.mock_api.return_value = (return_dict, 200)

        # Get device configuration from call_json.DeviceList.device_list_item()
        fan_obj = self.get_device("air_purifiers", setup_entry)
        assert isinstance(fan_obj, VeSyncPurifier)

        # Get method from device object
        method_call = getattr(fan_obj, method_name)

        # Ensure method runs based on device configuration
        if method_name == "turn_on":
            fan_obj.state.device_status = const.DeviceStatus.OFF
        elif method_name == "turn_off":
            fan_obj.state.device_status = const.DeviceStatus.ON
        elif method_name == "set_fan_speed":
            fan_obj.state.mode = const.PurifierModes.MANUAL
        elif method_name in ["set_auto_mode", "set_sleep_mode", "set_pet_mode", "set_turbo_mode"]:
            fan_obj.state.mode = const.PurifierModes.MANUAL
        elif method_name == "set_manual_mode":
            fan_obj.state.mode = const.PurifierModes.AUTO
        elif method_name in ["turn_on_display"]:
            fan_obj.state.display_set_status = const.DeviceStatus.OFF
            # Display on-mode normally comes from the last status (Vital Pet Pro)
            fan_obj.state.display_on_type = const.PurifierScreenOnType.ALWAYS_ON
        elif method_name in ["turn_off_display"]:
            fan_obj.state.display_set_status = const.DeviceStatus.ON
        elif method_name in ["turn_on_child_lock", "turn_off_child_lock"]:
            # Auto child lock settings normally come from the last status
            fan_obj.state.child_lock_auto_switch = 0
            fan_obj.state.child_lock_auto_time = 60

        # Call method with kwargs if defined
        if method_kwargs:
            self.run_in_loop(method_call, **method_kwargs)
        else:
            self.run_in_loop(method_call)

        if method_name == "turn_on":
            assert fan_obj.state.device_status == const.DeviceStatus.ON
        elif method_name == "turn_off":
            assert fan_obj.state.device_status == const.DeviceStatus.OFF
        elif method_name == "set_fan_speed":
            assert fan_obj.state.fan_level == method_kwargs["speed"]
        elif method_name in ["set_auto_mode"]:
            assert fan_obj.state.mode == const.PurifierModes.AUTO
        elif method_name == "set_auto_mode_type":
            assert fan_obj.state.mode == const.PurifierModes.AUTO
            assert fan_obj.state.auto_mode_type == method_kwargs["auto_mode_type"]
        elif method_name in ["set_sleep_mode"]:
            assert fan_obj.state.mode == const.PurifierModes.SLEEP
        elif method_name in ["set_pet_mode"]:
            assert fan_obj.state.mode == const.PurifierModes.PET
        elif method_name in ["set_turbo_mode"]:
            assert fan_obj.state.mode == const.PurifierModes.TURBO
        elif method_name in ["turn_on_display"]:
            assert fan_obj.state.display_set_status == const.DeviceStatus.ON
        elif method_name in ["turn_off_display"]:
            assert fan_obj.state.display_set_status == const.DeviceStatus.OFF
        elif method_name == "turn_on_child_lock":
            assert fan_obj.state.child_lock is True
        elif method_name == "turn_off_child_lock":
            assert fan_obj.state.child_lock is False
        elif method_name == "turn_on_buzzer":
            assert fan_obj.state.buzzer_status == const.DeviceStatus.ON
        elif method_name == "turn_off_buzzer":
            assert fan_obj.state.buzzer_status == const.DeviceStatus.OFF
        elif method_name == "turn_on_auto_clean":
            assert fan_obj.state.auto_clean_status is True
        elif method_name == "turn_off_auto_clean":
            assert fan_obj.state.auto_clean_status is False
        elif method_name == "set_timer":
            assert fan_obj.state.timer is not None
            assert fan_obj.state.timer.timer_duration == method_kwargs["duration"]
        elif method_name == "get_timer":
            assert fan_obj.state.timer is not None

        # Parse arguments from mock_api call into a dictionary
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recorded request or write new records
        assert assert_test(
            method_call, all_kwargs, setup_entry, self.write_api, self.overwrite
        )


class TestVitalPetPro(TestBase):
    """Vital Pet Pro (LAP-P501S) behavior not covered by the YAML tests.

    Request bodies are checked against the shapes captured from the VeSync
    app. Methods are called with several arguments here because the YAML
    fixtures hold one request per method name.
    """

    setup_entry = "LAP-P501S"

    def _device(self, setup_entry: str = "LAP-P501S") -> VeSyncPurifier:
        device = self.get_device("air_purifiers", setup_entry)
        assert isinstance(device, VeSyncPurifier)
        return device

    def _sent_data(self) -> dict:
        return parse_args(self.mock_api)["json_object"]["payload"]["data"]

    def _sent_method(self) -> str:
        return parse_args(self.mock_api)["json_object"]["payload"]["method"]

    def test_details_state(self):
        """getPurifierStatus fields map to state."""
        self.mock_api.return_value = (
            call_json_purifiers.DETAILS_RESPONSES[self.setup_entry],
            200,
        )
        device = self._device()
        self.run_in_loop(device.update)

        state = device.state
        assert state.mode == const.PurifierModes.MANUAL
        assert state.fan_set_level == call_json_purifiers.PurifierDefaults.fan_set_level
        assert state.voc == 1
        assert state.filter_remain_day == 159
        assert state.buzzer_status == const.DeviceStatus.ON
        assert state.auto_clean_status is False
        assert state.auto_clean_remaining == 0
        assert state.child_lock is True
        assert state.child_lock_auto_switch == 0
        assert state.child_lock_auto_time == 60
        assert state.timer is None
        assert state.auto_mode_type is None

    @pytest.mark.parametrize(
        "work_mode",
        ["odorShieldQuiet", "odorShieldBalanced", "odorShieldPerformance"],
    )
    def test_details_auto_mode_type(self, work_mode):
        """An odorShield workMode is reported as mode auto with its type."""
        details = dict(call_json_purifiers.PURIFIER_DETAILS[self.setup_entry])
        details["workMode"] = work_mode
        self.mock_api.return_value = (
            call_json_purifiers.build_bypass_v2_response(inner_result=details),
            200,
        )
        device = self._device()
        self.run_in_loop(device.update)

        assert device.state.mode == const.PurifierModes.AUTO
        assert device.state.auto_mode_type == work_mode

    def test_details_keeps_auto_mode_type(self):
        """Leaving auto keeps the last auto mode type for set_auto_mode()."""
        details = dict(call_json_purifiers.PURIFIER_DETAILS[self.setup_entry])
        details["workMode"] = "sleep"
        self.mock_api.return_value = (
            call_json_purifiers.build_bypass_v2_response(inner_result=details),
            200,
        )
        device = self._device()
        device.state.auto_mode_type = "odorShieldPerformance"
        self.run_in_loop(device.update)

        assert device.state.mode == const.PurifierModes.SLEEP
        assert device.state.auto_mode_type == "odorShieldPerformance"

    def test_details_timer_remain(self):
        """A status timerRemain keeps the id of a timer set earlier."""
        details = dict(call_json_purifiers.PURIFIER_DETAILS[self.setup_entry])
        details["timerRemain"] = 1500
        self.mock_api.return_value = (
            call_json_purifiers.build_bypass_v2_response(inner_result=details),
            200,
        )
        device = self._device()
        device.state.timer = Timer(1800, const.DeviceStatus.OFF, id=7)
        self.run_in_loop(device.update)

        assert device.state.timer is not None
        assert device.state.timer.id == 7
        assert device.state.timer.timer_duration == 1800
        assert 0 < device.state.timer.time_remaining <= 1500

    @pytest.mark.parametrize(
        ("requested", "sent"),
        [
            ("odorShieldQuiet", "odorShieldQuiet"),
            ("odorShieldBalanced", "odorShieldBalanced"),
            ("odorShieldPerformance", "odorShieldPerformance"),
            ("ODORSHIELDQUIET", "odorShieldQuiet"),
        ],
    )
    def test_set_auto_mode_type(self, requested, sent):
        """Each auto mode type is sent as its workMode; state.mode is auto."""
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device()
        assert self.run_in_loop(device.set_auto_mode_type, requested) is True
        assert self._sent_method() == "setPurifierMode"
        assert self._sent_data() == {"workMode": sent}
        assert device.state.mode == const.PurifierModes.AUTO
        assert device.state.auto_mode_type == sent

    def test_set_auto_mode_type_invalid(self):
        """An unknown auto mode type sends nothing."""
        device = self._device()
        assert self.run_in_loop(device.set_auto_mode_type, "turbo") is False
        self.mock_api.assert_not_called()

    @pytest.mark.parametrize(
        ("known_type", "sent"),
        [
            (None, "odorShieldBalanced"),
            ("odorShieldQuiet", "odorShieldQuiet"),
        ],
    )
    def test_set_mode_auto(self, known_type, sent):
        """Auto sends the last known type, or odorShieldBalanced."""
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device()
        device.state.auto_mode_type = known_type
        assert self.run_in_loop(device.set_mode, "AUTO") is True
        assert self._sent_data() == {"workMode": sent}
        assert device.state.mode == const.PurifierModes.AUTO
        assert device.state.auto_mode_type == sent

    def test_set_mode_sleep(self):
        """Sleep is sent as is."""
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device()
        assert self.run_in_loop(device.set_mode, "sleep") is True
        assert self._sent_data() == {"workMode": "sleep"}
        assert device.state.mode == const.PurifierModes.SLEEP

    @pytest.mark.parametrize("mode", ["turbo", "odorShieldQuiet"])
    def test_set_mode_invalid(self, mode):
        """Modes not in device.modes, auto mode types included, send nothing."""
        device = self._device()
        assert self.run_in_loop(device.set_mode, mode) is False
        self.mock_api.assert_not_called()

    def test_auto_mode_type_stub(self):
        """Purifiers without auto mode types refuse set_auto_mode_type()."""
        device = self._device("LAP-V201S")
        assert self.run_in_loop(device.set_auto_mode_type, "odorShieldQuiet") is False
        self.mock_api.assert_not_called()

    def test_child_lock_needs_status(self):
        """Child lock is not sent until the auto lock settings are known."""
        device = self._device()
        assert self.run_in_loop(device.turn_on_child_lock) is False
        self.mock_api.assert_not_called()

    def test_auto_clean_payloads(self):
        """Start sends autoCleanState 1, stop sends 2."""
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device()
        self.run_in_loop(device.turn_on_auto_clean)
        assert self._sent_data() == {"autoCleanState": 1}
        self.run_in_loop(device.turn_off_auto_clean)
        assert self._sent_data() == {"autoCleanState": 2}

    def test_get_timer(self):
        """getTimerV2 startAct parses into the timer."""
        self.mock_api.return_value = (
            call_json_purifiers.METHOD_RESPONSES[self.setup_entry]["get_timer"],
            200,
        )
        device = self._device()
        timer = self.run_in_loop(device.get_timer)
        assert isinstance(timer, Timer)
        assert timer.id == call_json_purifiers.VITAL_PET_PRO_TIMER["id"]
        assert timer.action == const.DeviceStatus.OFF

    @pytest.mark.parametrize("known_timer", [False, True])
    def test_clear_timer_default_id(self, known_timer):
        """clear_timer sends one delTimerV2 with id 1, whether or not a timer is known.

        The device holds one timer; no getTimerV2 read and no state check.
        """
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device()
        if known_timer:
            device.state.timer = Timer(1500, const.DeviceStatus.OFF)
        assert self.run_in_loop(device.clear_timer) is True

        assert self.mock_api.call_count == 1
        assert self._sent_method() == "delTimerV2"
        assert self._sent_data() == {"id": const.DEFAULT_TIMER_ID}
        assert device.state.timer is None

    def test_set_timer_default_id(self):
        """set_timer sends addTimerV2 without a read and stores the timer with id 1."""
        self.mock_api.return_value = (
            call_json_purifiers.build_bypass_v2_response(inner_result={"id": 1}),
            200,
        )
        device = self._device()
        assert self.run_in_loop(device.set_timer, 600) is True

        assert self.mock_api.call_count == 1
        assert self._sent_method() == "addTimerV2"
        assert device.state.timer is not None
        assert device.state.timer.id == const.DEFAULT_TIMER_ID
        assert device.state.timer.timer_duration == 600

    def test_details_timer_default_id(self):
        """A status timerRemain with no known timer builds a timer with id 1."""
        details = dict(call_json_purifiers.PURIFIER_DETAILS[self.setup_entry])
        details["timerRemain"] = 1500
        self.mock_api.return_value = (
            call_json_purifiers.build_bypass_v2_response(inner_result=details),
            200,
        )
        device = self._device()
        self.run_in_loop(device.update)

        assert device.state.timer is not None
        assert device.state.timer.id == const.DEFAULT_TIMER_ID

    @pytest.mark.parametrize("method", ["turn_on_light_detection", "reset_filter"])
    def test_unsupported_send_nothing(self, method):
        """No light sensor and no captured filter reset: nothing is sent."""
        device = self._device()
        assert self.run_in_loop(getattr(device, method)) is False
        self.mock_api.assert_not_called()

    def test_manual_mode_uses_manual_level(self):
        """Manual re-sends manualSpeedLevel even when Auto reports fan level 0.

        Captured: workMode odorShieldQuiet, fanSpeedLevel 0, powerSwitch 1.
        """
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device()
        device.state.mode = const.PurifierModes.AUTO
        device.state.fan_level = 0
        device.state.fan_set_level = 2
        assert self.run_in_loop(device.set_manual_mode) is True
        assert self._sent_method() == "setLevel"
        assert self._sent_data() == {
            "levelIdx": 0,
            "levelType": "wind",
            "manualSpeedLevel": 2,
        }
        assert device.state.mode == const.PurifierModes.MANUAL

    def test_details_display_preference(self):
        """screenPreference maps to the display state fields."""
        details = dict(call_json_purifiers.PURIFIER_DETAILS[self.setup_entry])
        details["screenPreference"] = {
            "screenOnType": 2,
            "screenStartTime": 28800,
            "screenEndTime": 79200,
        }
        self.mock_api.return_value = (
            call_json_purifiers.build_bypass_v2_response(inner_result=details),
            200,
        )
        device = self._device()
        self.run_in_loop(device.update)
        assert device.state.display_on_type == 2
        assert device.state.display_start_time == 28800
        assert device.state.display_end_time == 79200

    def test_display_on_keeps_schedule(self):
        """A scheduled display is turned on with its window (captured variant)."""
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device()
        device.state.display_set_status = const.DeviceStatus.OFF
        device.state.display_on_type = const.PurifierScreenOnType.SCHEDULED
        device.state.display_start_time = 28800
        device.state.display_end_time = 79200
        assert self.run_in_loop(device.turn_on_display) is True
        assert self._sent_data() == {
            "screenEndTime": 79200,
            "screenOnType": 2,
            "screenStartTime": 28800,
            "screenSwitch": 1,
        }

    def test_display_on_needs_status(self):
        """Display on is not sent until the display on-mode is known."""
        device = self._device()
        device.state.display_set_status = const.DeviceStatus.OFF
        assert self.run_in_loop(device.turn_on_display) is False
        self.mock_api.assert_not_called()

    def test_set_timer_on_action_rejected(self):
        """Only power-off timers were captured, so an 'on' timer is refused."""
        device = self._device()
        assert self.run_in_loop(device.set_timer, 600, const.DeviceStatus.ON) is False
        self.mock_api.assert_not_called()

    def test_vital_200s_set_mode_case(self):
        """VeSyncAirBaseV2 sends the mode as listed in device.modes."""
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device("LAP-V201S")
        assert self.run_in_loop(device.set_mode, "AUTO") is True
        assert self._sent_data() == {"workMode": "auto"}
