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

HEALTH_PROTECT_METHODS = [
    "set_health_protect_profile",
    "turn_off_adaptive_start",
    "turn_off_dynamic_manual",
    "turn_off_dynamic_sleep",
]
"""Methods that re-send the Health Protect settings from the last status."""


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
        "LAP-P201S": [
            ["set_auto_mode"],
            ["set_auto_mode_type", {"auto_mode_type": "odorShieldQuiet"}],
            ["set_sleep_mode"],
            ["turn_on_display"],
            ["turn_off_display"],
            ["turn_on_child_lock"],
            ["turn_off_child_lock"],
            ["turn_on_buzzer"],
            ["turn_off_buzzer"],
            ["set_timer", {"duration": 1800}],
            ["get_timer"],
        ],
        "LAP-C341S": [
            ["set_auto_mode"],
            ["turn_on_display"],
            ["turn_off_display"],
            ["turn_on_child_lock"],
            ["turn_off_child_lock"],
            ["turn_on_light_detection"],
            ["turn_off_light_detection"],
            ["set_aqi_light_mode", {"mode": "dim"}],
            ["set_timer", {"duration": 1800}],
            ["get_timer"],
            ["set_health_protect_profile", {"profile": "focused_care"}],
            ["turn_off_adaptive_start"],
            ["turn_off_dynamic_manual"],
            ["turn_off_dynamic_sleep"],
            ["turn_off_quiet_period"],
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
        elif method_name in HEALTH_PROTECT_METHODS:
            # Health Protect settings normally come from the last status (HAR #264)
            fan_obj.state.health_protect_profile = "daily_comfort"
            fan_obj.state.adaptive_start = True
            fan_obj.state.dynamic_manual = True
            fan_obj.state.dynamic_sleep = True
        elif method_name == "turn_off_quiet_period":
            # The Quiet Period mode normally comes from the last status (HAR #264)
            fan_obj.state.quiet_period_mode = "light_control"

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
        elif method_name == "set_aqi_light_mode":
            assert fan_obj.state.aqi_light_mode == method_kwargs["mode"]
        elif method_name == "set_health_protect_profile":
            assert fan_obj.state.health_protect_profile == method_kwargs["profile"]
        elif method_name == "turn_off_adaptive_start":
            assert fan_obj.state.adaptive_start is False
        elif method_name == "turn_off_dynamic_manual":
            assert fan_obj.state.dynamic_manual is False
        elif method_name == "turn_off_dynamic_sleep":
            assert fan_obj.state.dynamic_sleep is False
        elif method_name == "turn_off_quiet_period":
            assert fan_obj.state.quiet_period_switch is False

        # Parse arguments from mock_api call into a dictionary
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recorded request or write new records
        assert assert_test(
            method_call, all_kwargs, setup_entry, self.write_api, self.overwrite
        )


class PurifierTestHelpers:
    """Helpers shared by the purifier behavior test classes (not collected by pytest).

    `setup_entry` is the class default; family tests pass it explicitly.
    """

    setup_entry: str | None = None

    def _device(self, setup_entry: str | None = None) -> VeSyncPurifier:
        device = self.get_device("air_purifiers", setup_entry or self.setup_entry)
        assert isinstance(device, VeSyncPurifier)
        return device

    def _sent_data(self) -> dict:
        return parse_args(self.mock_api)["json_object"]["payload"]["data"]

    def _sent_method(self) -> str:
        return parse_args(self.mock_api)["json_object"]["payload"]["method"]

    def _status_response(self, setup_entry: str | None = None, **fields) -> dict:
        """Wrap the device's details dict, with `fields` overridden."""
        entry = setup_entry or self.setup_entry
        details = dict(call_json_purifiers.PURIFIER_DETAILS[entry]) | fields
        return call_json_purifiers.build_bypass_v2_response(inner_result=details)


class TestVitalPetPro(PurifierTestHelpers, TestBase):
    """Vital Pet Pro (LAP-P501S) behavior not covered by the YAML tests.

    Request bodies are checked against the shapes captured from the VeSync
    app. Methods are called with several arguments here because the YAML
    fixtures hold one request per method name.
    """

    setup_entry = "LAP-P501S"

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
        # Captured buzzerSwitch 1 is the app's Mute switch on: the beep is off.
        assert state.buzzer_status == const.DeviceStatus.OFF
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

    def test_pro_extends_vital_pet(self):
        """The Pro is a VeSyncAirVitalPet subclass and keeps self-cleaning."""
        from pyvesync.devices.vesyncpurifier import (
            VeSyncAirVitalPet,
            VeSyncAirVitalPetPro,
        )

        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device()
        assert type(device) is VeSyncAirVitalPetPro
        assert isinstance(device, VeSyncAirVitalPet)
        assert self.run_in_loop(device.turn_on_auto_clean) is True
        assert self._sent_method() == "setAutoClean"

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


VITAL_PET_ENTRIES = ["LAP-P501S", "LAP-P201S"]
"""Setup entries of the VeSyncAirVitalPet family: the Pro and the P201S."""

TIMER_V2_ENTRIES = ["LAP-P501S", "LAP-P201S", "LAP-C341S"]
"""Setup entries of the VeSyncAirTimerV2 classes (schedule-module v2 timer)."""


class TestTimerV2Family(PurifierTestHelpers, TestBase):
    """Shared VeSyncAirTimerV2 countdown timer behavior, run on each subclass."""

    @pytest.mark.parametrize("setup_entry", TIMER_V2_ENTRIES)
    def test_uses_shared_timer_class(self, setup_entry):
        """Each listed purifier gets its timer from VeSyncAirTimerV2."""
        from pyvesync.devices.vesyncpurifier import VeSyncAirTimerV2

        assert isinstance(self._device(setup_entry), VeSyncAirTimerV2)

    @pytest.mark.parametrize("setup_entry", TIMER_V2_ENTRIES)
    def test_set_timer_stores_returned_id(self, setup_entry):
        """The addTimerV2 response id is stored, and clear_timer cancels that id."""
        self.mock_api.return_value = (
            call_json_purifiers.build_bypass_v2_response(inner_result={"id": 7}),
            200,
        )
        device = self._device(setup_entry)
        assert self.run_in_loop(device.set_timer, 600) is True
        assert self.mock_api.call_count == 1
        assert self._sent_method() == "addTimerV2"
        assert device.state.timer is not None
        assert device.state.timer.id == 7
        assert device.state.timer.timer_duration == 600

        self.mock_api.reset_mock()
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        assert self.run_in_loop(device.clear_timer) is True
        assert self.mock_api.call_count == 1
        assert self._sent_method() == "delTimerV2"
        assert self._sent_data() == {"id": 7}
        assert device.state.timer is None

    @pytest.mark.parametrize("setup_entry", TIMER_V2_ENTRIES)
    @pytest.mark.parametrize("inner_result", ["no_id", "absent"])
    def test_set_timer_without_id_stores_default(self, setup_entry, inner_result):
        """An accepted add with no id (or no inner result) stores id 1."""
        response = call_json_purifiers.build_bypass_v2_response(inner_result={})
        if inner_result == "absent":
            del response["result"]["result"]
        self.mock_api.return_value = (response, 200)
        device = self._device(setup_entry)
        assert self.run_in_loop(device.set_timer, 600) is True
        assert device.state.timer is not None
        assert device.state.timer.id == 1

    @pytest.mark.parametrize("setup_entry", TIMER_V2_ENTRIES)
    def test_clear_timer_without_known_timer(self, setup_entry):
        """With no known timer, clear_timer sends one delTimerV2 with id 1."""
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device(setup_entry)
        assert device.state.timer is None
        assert self.run_in_loop(device.clear_timer) is True
        assert self.mock_api.call_count == 1
        assert self._sent_method() == "delTimerV2"
        assert self._sent_data() == {"id": 1}

    @pytest.mark.parametrize("setup_entry", TIMER_V2_ENTRIES)
    def test_status_poll_keeps_returned_id(self, setup_entry):
        """A status poll after set_timer keeps the id the add response returned."""
        self.mock_api.return_value = (
            call_json_purifiers.build_bypass_v2_response(inner_result={"id": 7}),
            200,
        )
        device = self._device(setup_entry)
        assert self.run_in_loop(device.set_timer, 1800) is True

        self.mock_api.return_value = (
            self._status_response(setup_entry, timerRemain=1500),
            200,
        )
        self.run_in_loop(device.update)
        assert device.state.timer is not None
        assert device.state.timer.id == 7
        assert device.state.timer.timer_duration == 1800


class TestVitalPetFamily(PurifierTestHelpers, TestBase):
    """Shared VeSyncAirVitalPet behavior, run on the Pro (LAP-P501S) and P201S."""

    @pytest.mark.parametrize("setup_entry", VITAL_PET_ENTRIES)
    @pytest.mark.parametrize(
        ("method", "sent", "status"),
        [
            ("turn_on_buzzer", 0, const.DeviceStatus.ON),
            ("turn_off_buzzer", 1, const.DeviceStatus.OFF),
        ],
    )
    def test_buzzer_sends_mute_switch(self, setup_entry, method, sent, status):
        """buzzerSwitch is the app's Mute switch: beep on sends 0, mute sends 1."""
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device(setup_entry)
        assert self.run_in_loop(getattr(device, method)) is True
        assert self._sent_method() == "setBuzzer"
        assert self._sent_data() == {"buzzerSwitch": sent}
        assert device.state.buzzer_status == status

    @pytest.mark.parametrize("setup_entry", VITAL_PET_ENTRIES)
    @pytest.mark.parametrize(
        ("current", "sent", "status"),
        [
            (const.DeviceStatus.ON, 1, const.DeviceStatus.OFF),
            (const.DeviceStatus.OFF, 0, const.DeviceStatus.ON),
        ],
    )
    def test_toggle_buzzer_flips_state(self, setup_entry, current, sent, status):
        """toggle_buzzer() with no argument flips the beep, sending the Mute value."""
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device(setup_entry)
        device.state.buzzer_status = current
        assert self.run_in_loop(device.toggle_buzzer) is True
        assert self._sent_data() == {"buzzerSwitch": sent}
        assert device.state.buzzer_status == status

    @pytest.mark.parametrize("setup_entry", VITAL_PET_ENTRIES)
    @pytest.mark.parametrize(
        ("buzzer_switch", "status"),
        [(0, const.DeviceStatus.ON), (1, const.DeviceStatus.OFF)],
    )
    def test_status_buzzer_is_mute_switch(self, setup_entry, buzzer_switch, status):
        """A reported buzzerSwitch 1 (muted) reads as buzzer off, 0 as on."""
        self.mock_api.return_value = (
            self._status_response(setup_entry, buzzerSwitch=buzzer_switch),
            200,
        )
        device = self._device(setup_entry)
        self.run_in_loop(device.update)
        assert device.state.buzzer_status == status


class TestVitalPet(PurifierTestHelpers, TestBase):
    """Vital Pet (LAP-P201S) behavior not covered by the YAML tests.

    No P201S packet capture exists. Requests follow APK 6.0.10 (profile
    `a60.d`, the same Snoopy screen as the Pro), and the responses in
    `call_json_purifiers` are synthetic, shaped from PR #535's field list.
    """

    setup_entry = "LAP-P201S"

    def test_vital_pet_map(self):
        """P201S maps to VeSyncAirVitalPet with the APK profile's controls."""
        from pyvesync.device_map import get_purifier
        from pyvesync.devices.vesyncpurifier import (
            VeSyncAirVitalPet,
            VeSyncAirVitalPetPro,
        )

        module = get_purifier("LAP-P201S-WUS")
        assert module is not None
        assert module.dev_types == ["LAP-P201S-WUS"]
        assert module.setup_entry == "LAP-P201S"
        assert module.class_name == "VeSyncAirVitalPet"
        assert module.modes == ["auto", "sleep", "manual"]
        assert module.auto_mode_types == [
            "odorShieldQuiet",
            "odorShieldBalanced",
            "odorShieldPerformance",
        ]
        assert module.fan_levels == [1, 2, 3]
        assert module.auto_preferences == []
        assert set(module.features) == {"air_quality", "buzzer"}

        device = self.get_device("air_purifiers", self.setup_entry)
        assert type(device) is VeSyncAirVitalPet
        assert not isinstance(device, VeSyncAirVitalPetPro)
        assert device.supports_buzzer is True
        assert device.supports_auto_clean is False
        assert device.supports_light_detection is False
        assert device.supports_nightlight is False

    @pytest.mark.parametrize(
        "work_mode",
        ["odorShieldQuiet", "odorShieldBalanced", "odorShieldPerformance"],
    )
    def test_details_state(self, work_mode):
        """Status fields map to state; absent light and self-cleaning fields are fine."""
        self.mock_api.return_value = (
            self._status_response(workMode=work_mode, fanSpeedLevel=2),
            200,
        )
        device = self._device()
        self.run_in_loop(device.update)

        state = device.state
        assert state.connection_status == const.ConnectionStatus.ONLINE
        assert state.device_status == const.DeviceStatus.ON
        assert state.mode == const.PurifierModes.AUTO
        assert state.auto_mode_type == work_mode
        assert state.fan_level == 2
        assert state.fan_set_level == 3
        assert state.air_quality_level == 2
        assert state.pm25 == 12
        assert state.voc == 2
        assert state.filter_life == 90
        assert state.filter_remain_day == 120
        assert state.display_set_status == const.DeviceStatus.ON
        assert state.display_on_type == 1
        assert state.display_start_time == 25200
        assert state.display_end_time == 75600
        assert state.child_lock is False
        assert state.child_lock_auto_switch == 1
        assert state.child_lock_auto_time == 120
        assert state.buzzer_status == const.DeviceStatus.ON
        assert state.timer is None
        # No light sensor and no self-cleaning: the fields are absent.
        assert state.light_detection_switch is None
        assert state.light_detection_status is None
        assert state.auto_clean_status is None
        assert state.auto_clean_remaining is None
        assert state.auto_clean_total is None

    def test_set_auto_mode_type_case(self):
        """An auto mode type is matched ignoring case and sent as listed."""
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device()
        assert self.run_in_loop(device.set_auto_mode_type, "ODORSHIELDQUIET") is True
        assert self._sent_method() == "setPurifierMode"
        assert self._sent_data() == {"workMode": "odorShieldQuiet"}
        assert device.state.mode == const.PurifierModes.AUTO

    @pytest.mark.parametrize("level", [1, 2])
    def test_set_fan_speed_levels(self, level):
        """Manual levels 1 and 2 send setLevel (level 3 is in the YAML tests)."""
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        device = self._device()
        assert self.run_in_loop(device.set_fan_speed, level) is True
        assert self._sent_method() == "setLevel"
        assert self._sent_data() == {
            "levelIdx": 0,
            "levelType": "wind",
            "manualSpeedLevel": level,
        }
        assert device.state.fan_set_level == level
        assert device.state.mode == const.PurifierModes.MANUAL

    def test_manual_mode_sends_level(self):
        """Manual sends the status manualSpeedLevel with setLevel, never workMode."""
        self.mock_api.return_value = (
            self._status_response(workMode="odorShieldBalanced", fanSpeedLevel=0),
            200,
        )
        device = self._device()
        self.run_in_loop(device.update)

        self.mock_api.reset_mock()
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        assert self.run_in_loop(device.set_manual_mode) is True
        assert self.mock_api.call_count == 1
        assert self._sent_method() == "setLevel"
        assert self._sent_data() == {
            "levelIdx": 0,
            "levelType": "wind",
            "manualSpeedLevel": 3,
        }
        assert device.state.mode == const.PurifierModes.MANUAL

    @pytest.mark.parametrize(
        ("method", "args"),
        [
            ("toggle_auto_clean", ()),
            ("turn_on_auto_clean", ()),
            ("turn_off_auto_clean", ()),
            ("toggle_light_detection", (True,)),
            ("turn_on_light_detection", ()),
            ("reset_filter", ()),
            ("set_auto_preference", ("default",)),
            ("set_nightlight_mode", ("on",)),
        ],
    )
    def test_unsupported_send_nothing(self, method, args):
        """Controls missing from the P201S app profile return False, send nothing."""
        device = self._device()
        assert self.run_in_loop(getattr(device, method), *args) is False
        self.mock_api.assert_not_called()

    @pytest.mark.parametrize("method", ["turn_on_display", "turn_on_child_lock"])
    def test_needs_status_first(self, method):
        """Display on and child lock refuse before update() and send nothing."""
        device = self._device()
        assert self.run_in_loop(getattr(device, method)) is False
        self.mock_api.assert_not_called()

    @pytest.mark.parametrize(
        ("preference", "sent"),
        [
            (
                {"screenOnType": 1, "screenStartTime": 25200, "screenEndTime": 75600},
                {"screenOnType": 1, "screenSwitch": 1},
            ),
            (
                {"screenOnType": 2, "screenStartTime": 25200, "screenEndTime": 75600},
                {
                    "screenEndTime": 75600,
                    "screenOnType": 2,
                    "screenStartTime": 25200,
                    "screenSwitch": 1,
                },
            ),
        ],
    )
    def test_display_on_resends_status_preference(self, preference, sent):
        """Display on re-sends the status on-type, with the window when it is 2."""
        self.mock_api.return_value = (
            self._status_response(screenSwitch=0, screenPreference=preference),
            200,
        )
        device = self._device()
        self.run_in_loop(device.update)

        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        assert self.run_in_loop(device.turn_on_display) is True
        assert self._sent_method() == "setDisplay"
        assert self._sent_data() == sent
        assert device.state.display_set_status == const.DeviceStatus.ON

    def test_child_lock_resends_status_preference(self):
        """Child lock re-sends the status auto-lock preference."""
        self.mock_api.return_value = (self._status_response(), 200)
        device = self._device()
        self.run_in_loop(device.update)

        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        assert self.run_in_loop(device.turn_on_child_lock) is True
        assert self._sent_method() == "setChildLock"
        assert self._sent_data() == {
            "childLockAutoSwitch": 1,
            "childLockAutoSwitchTime": 120,
            "childLockSwitch": 1,
        }
        assert device.state.child_lock is True

    @pytest.mark.parametrize(
        ("method", "args", "sent_method"),
        [
            ("set_sleep_mode", (), "setPurifierMode"),
            ("set_fan_speed", (2,), "setLevel"),
            ("turn_off", (), "setSwitch"),
        ],
    )
    def test_setters_work_while_locked(self, method, args, sent_method):
        """The app controls the purifier while Control Lock is on (manual p14)."""
        self.mock_api.return_value = (self._status_response(childLockSwitch=1), 200)
        device = self._device()
        self.run_in_loop(device.update)
        assert device.state.child_lock is True

        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)
        assert self.run_in_loop(getattr(device, method), *args) is True
        assert self._sent_method() == sent_method

    def test_failed_poll_keeps_state(self):
        """A rejected status poll leaves the last known state unchanged."""
        self.mock_api.return_value = (
            self._status_response(workMode="odorShieldPerformance"),
            200,
        )
        device = self._device()
        self.run_in_loop(device.update)

        self.mock_api.return_value = (
            call_json_purifiers.build_bypass_v2_response(inner_code=-1),
            200,
        )
        self.run_in_loop(device.update)
        assert device.state.mode == const.PurifierModes.AUTO
        assert device.state.auto_mode_type == "odorShieldPerformance"
        assert device.state.voc == 2
        assert device.state.filter_life == 90
        assert device.state.buzzer_status == const.DeviceStatus.ON


class TestPurifierBaseStubs(TestBase):
    """VeSyncPurifier stubs refuse features the device map does not list."""

    def test_aqi_light_stub(self):
        """Purifiers without an AQI light ring refuse set_aqi_light_mode()."""
        device = self.get_device("air_purifiers", "LAP-V201S")
        assert device.supports_aqi_light is False
        assert device.state.aqi_light_mode is None
        assert self.run_in_loop(device.set_aqi_light_mode, "dim") is False
        self.mock_api.assert_not_called()


class TestEleva(PurifierTestHelpers, TestBase):
    """Core 300S MaxAQ / Eleva 300X (LAP-C341S) behavior not covered by YAML tests.

    Status and request bodies come from the US app capture (HAR entry numbers
    in the docstrings) and the EU status posted in issue #545. Timer responses
    are SYNTHETIC (see `call_json_purifiers.ELEVA_TIMER`).
    """

    setup_entry = "LAP-C341S"

    def test_eleva_result_us_capture(self):
        """The captured US status (HAR #264) parses."""
        from pyvesync.models.purifier_models import PurifierElevaResult

        result = PurifierElevaResult.from_dict(
            call_json_purifiers.PURIFIER_DETAILS["LAP-C341S"]
        )
        assert result.workMode == "manual"
        assert result.group == 1
        assert result.quietPeriod is not None and result.quietPeriod.endTime == 21600
        assert result.autoPreference is not None
        assert result.autoPreference.autoPreferenceType == "default"

    def test_eleva_result_eu_shape(self):
        """The EU status (issue #545) parses without group and with buzzerSwitch."""
        from pyvesync.models.purifier_models import PurifierElevaResult

        result = PurifierElevaResult.from_dict(call_json_purifiers.ELEVA_EU_STATUS)
        assert result.group is None
        assert result.sleepGuardSwitch == 0
        assert result.preFilterLifePercent == 96

    def _ok(self):
        """Return a successful bypassV2 command response."""
        self.mock_api.return_value = (call_json_purifiers.build_bypass_v2_response(), 200)

    def _update(self, inner_result: dict | None = None):
        """Return a device after update() with `inner_result` (default HAR #264)."""
        if inner_result is None:
            response = call_json_purifiers.DETAILS_RESPONSES[self.setup_entry]
        else:
            response = call_json_purifiers.build_bypass_v2_response(
                inner_result=inner_result
            )
        self.mock_api.return_value = (response, 200)
        device = self._device()
        self.run_in_loop(device.update)
        self.mock_api.reset_mock()
        return device

    def test_eleva_map(self):
        """US and EU device types map to VeSyncAirEleva with levels 1-4."""
        from pyvesync.device_map import get_purifier

        for dev_type in ("LAP-C341S-WUSZ", "LAP-C341S-WEU"):
            module = get_purifier(dev_type)
            assert module is not None and module.class_name == "VeSyncAirEleva"
            assert module.setup_entry == "LAP-C341S"
        assert module.fan_levels == [1, 2, 3, 4]
        assert module.auto_preferences == []
        assert set(module.features) == {
            "air_quality",
            "light_detect",
            "aqi_light",
            "health_protect",
        }
        assert type(self._device()).__name__ == "VeSyncAirEleva"

    def test_details_state(self):
        """HAR #264 maps to state."""
        state = self._update().state
        assert state.connection_status == const.ConnectionStatus.ONLINE
        assert state.device_status == const.DeviceStatus.ON
        assert state.mode == const.PurifierModes.MANUAL
        assert state.fan_level == 1
        assert state.fan_set_level == 1
        assert state.air_quality_level == 1
        assert state.pm25 == 2
        assert state.pm1 == 1
        assert state.pm10 == 3
        assert state.aq_percent == 20
        assert state.filter_life == 96
        assert state.filter_remain_day == 686
        assert state.carbon_filter_life == 86
        assert state.pre_filter_life == 0
        assert state.display_status == const.DeviceStatus.ON
        assert state.display_set_status == const.DeviceStatus.ON
        assert state.child_lock is False
        assert state.light_detection_switch == const.DeviceStatus.ON
        assert state.light_detection_status == const.DeviceStatus.ON
        assert state.auto_preference_type == "default"
        assert state.aqi_light_mode == "bright"
        assert state.health_protect_profile == "daily_comfort"
        assert state.adaptive_start is True
        assert state.dynamic_manual is True
        assert state.dynamic_sleep is True
        assert state.quiet_period_switch is False
        assert state.quiet_period_mode == "light_control"
        assert state.quiet_period_start == 79200
        assert state.quiet_period_end == 21600
        assert state.timer is None
        assert state.buzzer_status is None

    def test_details_eu_state(self):
        """The EU status (issue #545): no group, Dynamic Sleep off, Quiet Period on."""
        state = self._update(call_json_purifiers.ELEVA_EU_STATUS).state
        assert state.mode == const.PurifierModes.AUTO
        assert state.fan_level == 0
        assert state.fan_set_level == 2
        assert state.pre_filter_life == 96
        assert state.health_protect_profile is None
        assert state.adaptive_start is True
        assert state.dynamic_manual is True
        assert state.dynamic_sleep is False
        assert state.quiet_period_switch is True
        assert state.buzzer_status is None

    def test_details_unknown_enums(self):
        """Enum values the APK does not list read as None."""
        self.mock_api.return_value = (
            self._status_response(
                aqiLightMode=3,
                group=4,
                quietPeriod={"quietPeriodSwitch": 1, "modeIdx": 2},
            ),
            200,
        )
        device = self._device()
        self.run_in_loop(device.update)
        assert device.state.aqi_light_mode is None
        assert device.state.health_protect_profile is None
        assert device.state.quiet_period_mode is None
        assert device.state.quiet_period_switch is True

    def test_details_sleep_fan_zero(self):
        """Sleep reports fanSpeedLevel 0 (HAR #145); the manual level is kept."""
        self.mock_api.return_value = (
            self._status_response(workMode="sleep", fanSpeedLevel=0),
            200,
        )
        device = self._device()
        self.run_in_loop(device.update)
        assert device.state.mode == const.PurifierModes.SLEEP
        assert device.state.fan_level == 0
        assert device.state.fan_set_level == 1

    def test_status_timeout_keeps_state(self):
        """A device timeout (HAR #151, outer -11302030) leaves state unchanged."""
        device = self._update()
        self.mock_api.return_value = (
            {"traceId": "1", "code": -11302030, "msg": "device timeout", "result": None},
            200,
        )
        self.run_in_loop(device.update)
        assert device.state.mode == const.PurifierModes.MANUAL
        assert device.state.fan_set_level == 1
        assert device.state.display_set_status == const.DeviceStatus.ON
        assert device.state.health_protect_profile == "daily_comfort"
        assert device.state.device_status == const.DeviceStatus.ON
        assert device.state.connection_status == const.ConnectionStatus.OFFLINE
        assert device.last_response is not None
        assert device.last_response.name == "DEVICE_TIMEOUT"

    def test_set_state_rejects_other_model(self):
        """A status parsed into another purifier's model is refused; state is kept.

        The shared `InnerPurifierBaseResult` base cannot tell the status models
        apart, so `_set_state()` accepts only `PurifierElevaResult`.
        """
        from pyvesync.models.purifier_models import PurifierVitalPetProResult

        device = self._update()
        other = PurifierVitalPetProResult.from_dict(
            call_json_purifiers.PURIFIER_DETAILS["LAP-P501S"]
        )
        self.caplog.set_level(logging.WARNING)
        device._set_state(other)
        assert "Invalid details model" in self.caplog.text
        assert device.state.mode == const.PurifierModes.MANUAL
        assert device.state.fan_set_level == 1
        assert device.state.aqi_light_mode == "bright"

    @pytest.mark.parametrize("toggle", [True, False])
    def test_power_sent_when_state_matches(self, toggle):
        """Power is sent even when the (possibly stale) state already matches."""
        self._ok()
        device = self._device()
        device.state.device_status = const.DeviceStatus.from_bool(toggle)
        assert self.run_in_loop(device.toggle_switch, toggle) is True
        assert self._sent_method() == "setSwitch"
        assert self._sent_data() == {"powerSwitch": int(toggle), "switchIdx": 0}
        assert device.state.device_status == const.DeviceStatus.from_bool(toggle)

    def test_manual_mode_resumes_manual_level(self):
        """Manual is a work mode (HAR #129); the device resumes manualSpeedLevel.

        HAR #157 -> #160: from sleep with fanSpeedLevel 0, setPurifierMode
        manual gives fanSpeedLevel equal to manualSpeedLevel.
        """
        self._ok()
        device = self._device()
        device.state.mode = const.PurifierModes.SLEEP
        device.state.fan_level = 0
        device.state.fan_set_level = 3
        assert self.run_in_loop(device.set_mode, "manual") is True
        assert self._sent_method() == "setPurifierMode"
        assert self._sent_data() == {"workMode": "manual"}
        assert device.state.mode == const.PurifierModes.MANUAL
        assert device.state.fan_level == 3
        assert device.state.fan_set_level == 3

    def test_set_fan_speed_turbo_level(self):
        """Level 4 (the app's Turbo) is a fan level; level 5 is refused."""
        self._ok()
        device = self._device()
        assert self.run_in_loop(device.set_fan_speed, 4) is True
        assert self._sent_method() == "setLevel"
        assert self._sent_data() == {
            "levelIdx": 0,
            "manualSpeedLevel": 4,
            "levelType": "wind",
        }
        self.mock_api.reset_mock()
        assert self.run_in_loop(device.set_fan_speed, 5) is False
        self.mock_api.assert_not_called()

    @pytest.mark.parametrize(
        ("fan_set_level", "fan_level", "sent"),
        [
            (3, 2, 4),  # Quiet Period: running one level below the set level
            (2, 0, 3),  # Sleep reports fanSpeedLevel 0 (HAR #145)
            (4, 1, 1),  # Auto at set level 4 (HAR #116) wraps to 1
            (None, None, 1),  # nothing known
        ],
    )
    def test_set_fan_speed_steps_from_set_level(self, fan_set_level, fan_level, sent):
        """set_fan_speed() with no argument steps up from the set level, not the
        running level."""
        self._ok()
        device = self._device()
        device.state.fan_set_level = fan_set_level
        device.state.fan_level = fan_level
        assert self.run_in_loop(device.set_fan_speed) is True
        assert self._sent_method() == "setLevel"
        assert self._sent_data()["manualSpeedLevel"] == sent
        assert device.state.fan_set_level == sent

    def test_set_turbo_mode_sets_level_4(self):
        """set_turbo_mode() sends fan level 4, the app's Turbo (APK 6.0.10).

        Turbo is Manual at level 4: HAR #116-#128 report manualSpeedLevel 4 in
        Auto, and after setPurifierMode manual (#129) #131 reports workMode
        manual with fanSpeedLevel 4.
        """
        self._ok()
        device = self._device()
        device.state.mode = const.PurifierModes.AUTO
        assert self.run_in_loop(device.set_turbo_mode) is True
        assert self._sent_method() == "setLevel"
        assert self._sent_data() == {
            "levelIdx": 0,
            "manualSpeedLevel": 4,
            "levelType": "wind",
        }
        assert device.state.mode == const.PurifierModes.MANUAL
        assert device.state.fan_level == 4
        assert device.state.fan_set_level == 4

    def test_set_fan_speed_steps_from_last_set_level(self):
        """Back-to-back steps without update() start from the level last set."""
        device = self._update()  # HAR #264: set level 1
        self._ok()
        assert self.run_in_loop(device.set_fan_speed, 2) is True
        assert self.run_in_loop(device.set_fan_speed) is True
        assert self._sent_data()["manualSpeedLevel"] == 3
        assert device.state.fan_set_level == 3

    @pytest.mark.parametrize("mode", ["turbo", "pet"])
    def test_set_mode_invalid(self, mode):
        """Turbo is fan level 4, not a work mode; unlisted modes send nothing."""
        device = self._device()
        assert self.run_in_loop(device.set_mode, mode) is False
        self.mock_api.assert_not_called()

    @pytest.mark.parametrize("mode", [True, False])
    def test_display_sent_when_state_matches(self, mode):
        """Display is sent with light detection on and the state already matching."""
        self._ok()
        device = self._device()
        device.state.display_set_status = const.DeviceStatus.from_bool(mode)
        device.state.light_detection_switch = const.DeviceStatus.ON
        device.state.light_detection_status = const.DeviceStatus.ON
        assert self.run_in_loop(device.toggle_display, mode) is True
        assert self._sent_method() == "setDisplay"
        assert self._sent_data() == {"screenSwitch": int(mode)}
        assert device.state.display_set_status == const.DeviceStatus.from_bool(mode)

    @pytest.mark.parametrize("toggle", [True, False])
    def test_light_detection_sent_when_state_matches(self, toggle):
        """Light detection is sent even when the switch state already matches."""
        self._ok()
        device = self._device()
        device.state.light_detection_switch = const.DeviceStatus.from_bool(toggle)
        assert self.run_in_loop(device.toggle_light_detection, toggle) is True
        assert self._sent_method() == "setLightDetection"
        assert self._sent_data() == {"lightDetectionSwitch": int(toggle)}

    def test_light_detection_toggle_flips_switch(self):
        """toggle_light_detection() flips the switch, not the ambient light state."""
        self._ok()
        device = self._device()
        device.state.light_detection_switch = const.DeviceStatus.ON
        device.state.light_detection_status = const.DeviceStatus.OFF
        assert self.run_in_loop(device.toggle_light_detection) is True
        assert self._sent_data() == {"lightDetectionSwitch": 0}
        assert device.state.light_detection_switch == const.DeviceStatus.OFF

    @pytest.mark.parametrize(
        ("mode", "sent", "state"),
        [("bright", 1, "bright"), ("dim", 2, "dim"), ("DIM", 2, "dim")],
    )
    def test_set_aqi_light_mode(self, mode, sent, state):
        """The light ring sends setAqiLight mode 1 bright / 2 dim (HAR #179, #172)."""
        self._ok()
        device = self._device()
        assert device.supports_aqi_light is True
        assert self.run_in_loop(device.set_aqi_light_mode, mode) is True
        assert self._sent_method() == "setAqiLight"
        assert self._sent_data() == {"mode": sent}
        assert device.state.aqi_light_mode == state

    def test_set_aqi_light_mode_invalid(self):
        """An unknown light ring mode sends nothing."""
        device = self._device()
        assert self.run_in_loop(device.set_aqi_light_mode, "off") is False
        self.mock_api.assert_not_called()

    def test_set_aqi_light_mode_enum_member(self):
        """A `PurifierAqiLightMode` member is accepted like its name."""
        self._ok()
        device = self._device()
        assert (
            self.run_in_loop(device.set_aqi_light_mode, const.PurifierAqiLightMode.DIM)
            is True
        )
        assert self._sent_data() == {"mode": 2}
        assert device.state.aqi_light_mode == "dim"

    def test_set_aqi_light_mode_none(self):
        """None sends nothing and returns False instead of raising."""
        device = self._device()
        assert self.run_in_loop(device.set_aqi_light_mode, None) is False
        self.mock_api.assert_not_called()

    @pytest.mark.parametrize("toggle", [True, False])
    def test_child_lock_sent_when_state_matches(self, toggle):
        """Child lock (inherited, no state check) is sent when the state matches."""
        self._ok()
        device = self._device()
        device.state.child_lock = toggle
        assert self.run_in_loop(device.toggle_child_lock, toggle) is True
        assert self._sent_method() == "setChildLock"
        assert self._sent_data() == {"childLockSwitch": int(toggle)}

    @pytest.mark.parametrize("mode", ["auto", "sleep"])
    def test_mode_sent_when_state_matches(self, mode):
        """Auto and Sleep (inherited) are sent when the mode already matches."""
        self._ok()
        device = self._device()
        device.state.mode = mode
        assert self.run_in_loop(device.set_mode, mode) is True
        assert self._sent_method() == "setPurifierMode"
        assert self._sent_data() == {"workMode": mode}

    @pytest.mark.parametrize(
        ("method", "args"),
        [
            ("reset_filter", ()),
            ("turn_on_buzzer", ()),
            ("set_auto_preference", ("default",)),
        ],
    )
    def test_unsupported_send_nothing(self, method, args):
        """No captured filter reset, buzzer or auto preference: nothing is sent."""
        device = self._device()
        assert self.run_in_loop(getattr(device, method), *args) is False
        self.mock_api.assert_not_called()

    def test_set_timer_device_off_error(self):
        """A refused add (inner 11005000 BYPASS_DEVICE_IS_OFF) stores no timer."""
        self.mock_api.return_value = (
            call_json_purifiers.build_bypass_v2_response(inner_code=11005000),
            200,
        )
        device = self._device()
        device.state.device_status = const.DeviceStatus.OFF
        assert self.run_in_loop(device.set_timer, 600) is False
        assert device.state.timer is None
        assert self.mock_api.call_count == 1
        assert self._sent_method() == "addTimerV2"

    def test_status_timer_remain_sets_timer(self):
        """A status timerRemain with no known timer builds an off timer with id 1."""
        self.mock_api.return_value = (self._status_response(timerRemain=1500), 200)
        device = self._device()
        self.run_in_loop(device.update)
        assert device.state.timer is not None
        assert device.state.timer.timer_duration == 1500
        assert 0 < device.state.timer.time_remaining <= 1500
        assert device.state.timer.action == const.DeviceStatus.OFF
        assert device.state.timer.id == const.DEFAULT_TIMER_ID

    def test_health_protect_eu_group_fallback(self):
        """EU status has no group; switch setters send group 1 as the app does.

        APK 6.0.10 protectDetail senders fill a missing group with
        protectGuide/a$a.a(null), DAILY_COMFORT.
        """
        device = self._update(call_json_purifiers.ELEVA_EU_STATUS)
        assert device.state.health_protect_profile is None
        self._ok()
        assert self.run_in_loop(device.turn_off_dynamic_manual) is True
        assert self._sent_method() == "setHealthProtect"
        assert self._sent_data() == {
            "group": 1,
            "standbyGuardSwitch": 1,
            "manualGuardSwitch": 0,
            "sleepGuardSwitch": 0,
        }
        assert device.state.health_protect_profile == "daily_comfort"
        assert device.state.dynamic_manual is False

    def test_health_protect_eu_set_profile(self):
        """On the EU unit a profile is sent with the three reported switches."""
        device = self._update(call_json_purifiers.ELEVA_EU_STATUS)
        self._ok()
        assert self.run_in_loop(device.set_health_protect_profile, "advanced_care")
        assert self._sent_data() == {
            "group": 3,
            "standbyGuardSwitch": 1,
            "manualGuardSwitch": 1,
            "sleepGuardSwitch": 0,
        }
        assert device.state.health_protect_profile == "advanced_care"

    def test_health_protect_unrecognised_group(self):
        """An unrecognised group is sent as Daily Comfort, and the log says so.

        APK 6.0.10 protectGuide/a$a.a() maps a null or unknown group to
        DAILY_COMFORT.
        """
        device = self._update(
            call_json_purifiers.PURIFIER_DETAILS["LAP-C341S"] | {"group": 4}
        )
        assert device.state.health_protect_profile is None
        self.caplog.set_level(logging.DEBUG)
        self._ok()
        assert self.run_in_loop(device.turn_off_dynamic_manual) is True
        assert self._sent_data()["group"] == 1
        assert "not reported or not recognised" in self.caplog.text

    def test_health_protect_needs_switches(self):
        """Before update() the switches are unknown, so nothing is sent."""
        device = self._device()
        assert self.run_in_loop(device.turn_off_dynamic_manual) is False
        assert self.run_in_loop(device.set_health_protect_profile, "daily_comfort") is False
        self.mock_api.assert_not_called()

    @pytest.mark.parametrize(
        ("method", "args", "sent"),
        [
            (
                "set_health_protect_profile",
                ("FOCUSED_CARE",),
                {"group": 2, "standbyGuardSwitch": 1, "manualGuardSwitch": 1, "sleepGuardSwitch": 1},
            ),
            (
                "set_health_protect_profile",
                ("advanced_care",),
                {"group": 3, "standbyGuardSwitch": 1, "manualGuardSwitch": 1, "sleepGuardSwitch": 1},
            ),
            (
                "turn_off_adaptive_start",
                (),
                {"group": 1, "standbyGuardSwitch": 0, "manualGuardSwitch": 1, "sleepGuardSwitch": 1},
            ),
            (
                "turn_off_dynamic_manual",
                (),
                {"group": 1, "standbyGuardSwitch": 1, "manualGuardSwitch": 0, "sleepGuardSwitch": 1},
            ),
            (
                "turn_off_dynamic_sleep",
                (),
                {"group": 1, "standbyGuardSwitch": 1, "manualGuardSwitch": 1, "sleepGuardSwitch": 0},
            ),
        ],
    )
    def test_health_protect_resends_all_fields(self, method, args, sent):
        """setHealthProtect always carries all four fields (HAR #205)."""
        device = self._update()
        self._ok()
        assert self.run_in_loop(getattr(device, method), *args) is True
        assert self._sent_method() == "setHealthProtect"
        assert self._sent_data() == sent
        state = device.state
        assert state.health_protect_profile == const.PurifierHealthProtectProfile(
            sent["group"]
        ).name.lower()
        assert state.adaptive_start is bool(sent["standbyGuardSwitch"])
        assert state.dynamic_manual is bool(sent["manualGuardSwitch"])
        assert state.dynamic_sleep is bool(sent["sleepGuardSwitch"])

    def test_health_protect_sent_when_state_matches(self):
        """A switch already on is sent again (HAR #205 is such a re-send)."""
        device = self._update()
        self._ok()
        assert self.run_in_loop(device.turn_on_dynamic_manual) is True
        assert self._sent_data() == {
            "group": 1,
            "standbyGuardSwitch": 1,
            "manualGuardSwitch": 1,
            "sleepGuardSwitch": 1,
        }

    def test_health_protect_toggle_flips(self):
        """toggle_dynamic_sleep() with no argument flips the cached switch."""
        device = self._update()
        self._ok()
        assert self.run_in_loop(device.toggle_dynamic_sleep) is True
        assert self._sent_data()["sleepGuardSwitch"] == 0
        assert device.state.dynamic_sleep is False

    def test_health_protect_back_to_back(self):
        """Back-to-back changes without update() keep the earlier change."""
        device = self._update()
        self._ok()
        assert self.run_in_loop(device.turn_off_dynamic_manual) is True
        assert self.run_in_loop(device.turn_off_dynamic_sleep) is True
        assert self._sent_data() == {
            "group": 1,
            "standbyGuardSwitch": 1,
            "manualGuardSwitch": 0,
            "sleepGuardSwitch": 0,
        }

    def test_health_protect_invalid_profile(self):
        """An unknown profile name sends nothing."""
        device = self._update()
        assert self.run_in_loop(device.set_health_protect_profile, "max") is False
        self.mock_api.assert_not_called()

    def test_health_protect_profile_enum_member(self):
        """A `PurifierHealthProtectProfile` member is accepted like its name."""
        device = self._update()
        self._ok()
        assert (
            self.run_in_loop(
                device.set_health_protect_profile,
                const.PurifierHealthProtectProfile.FOCUSED_CARE,
            )
            is True
        )
        assert self._sent_data()["group"] == 2
        assert device.state.health_protect_profile == "focused_care"

    def test_health_protect_profile_none(self):
        """None sends nothing and returns False instead of raising."""
        device = self._update()
        assert self.run_in_loop(device.set_health_protect_profile, None) is False
        self.mock_api.assert_not_called()

    def test_health_protect_stub(self):
        """Purifiers without Health Protect refuse the setters."""
        device = self._device("LAP-V201S")
        assert device.supports_health_protect is False
        assert self.run_in_loop(device.set_health_protect_profile, "daily_comfort") is False
        assert self.run_in_loop(device.turn_off_dynamic_manual) is False
        assert self.run_in_loop(device.turn_on_quiet_period) is False
        self.mock_api.assert_not_called()

    def test_quiet_period_needs_mode(self):
        """The Quiet Period mode is unknown before update(), so nothing is sent."""
        device = self._device()
        assert device.state.quiet_period_mode is None
        self.caplog.set_level(logging.WARNING)
        assert self.run_in_loop(device.turn_on_quiet_period) is False
        self.mock_api.assert_not_called()
        assert "run update() first" in self.caplog.text

    def test_quiet_period_unrecognised_mode(self):
        """A reported but unrecognised modeIdx sends nothing, and the log says so."""
        device = self._update(
            call_json_purifiers.PURIFIER_DETAILS["LAP-C341S"]
            | {"quietPeriod": {"quietPeriodSwitch": 0, "modeIdx": 2}}
        )
        assert device.state.quiet_period_switch is False
        assert device.state.quiet_period_mode is None
        self.caplog.set_level(logging.WARNING)
        assert self.run_in_loop(device.turn_on_quiet_period) is False
        self.mock_api.assert_not_called()
        assert "not recognised" in self.caplog.text
        assert "run update() first" not in self.caplog.text

    def test_quiet_period_body(self):
        """The switch is sent with the reported mode and no times (HAR #208)."""
        device = self._update()
        self._ok()
        assert self.run_in_loop(device.turn_on_quiet_period) is True
        assert self._sent_method() == "setQuietPeriod"
        assert self._sent_data() == {"quietPeriodSwitch": 1, "modeIdx": 0}
        assert device.state.quiet_period_switch is True

    def test_quiet_period_keeps_customized_mode(self):
        """A Customized Quiet Period keeps modeIdx 1."""
        device = self._update()
        device.state.quiet_period_mode = "customized"
        self._ok()
        assert self.run_in_loop(device.turn_on_quiet_period) is True
        assert self._sent_data() == {"quietPeriodSwitch": 1, "modeIdx": 1}

    def test_quiet_period_eu(self):
        """The EU unit (Quiet Period on, Light Control) turns it off."""
        device = self._update(call_json_purifiers.ELEVA_EU_STATUS)
        self._ok()
        assert self.run_in_loop(device.turn_off_quiet_period) is True
        assert self._sent_data() == {"quietPeriodSwitch": 0, "modeIdx": 0}
        assert device.state.quiet_period_switch is False

    def test_quiet_period_toggle_flips(self):
        """toggle_quiet_period() with no argument flips the cached switch."""
        device = self._update()
        self._ok()
        assert self.run_in_loop(device.toggle_quiet_period) is True
        assert self._sent_data() == {"quietPeriodSwitch": 1, "modeIdx": 0}
