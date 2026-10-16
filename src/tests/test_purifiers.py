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
from unittest.mock import patch

import pytest

import pyvesync.const as const
from pyvesync.base_devices.purifier_base import VeSyncPurifier
from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
from pyvesync.vesync import DEVICE_PROPS_REUSE_SECONDS
from base_test_cases import TestBase
from call_json import ALL_DEVICE_MAP_DICT, DeviceList
from defaults import TestDefaults, build_bypass_v2_response
from utils import assert_test, parse_args
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
        "LAP-C511S": [["set_auto_mode"], ["set_sleep_mode"], ["turn_on_display"], ["turn_off_display"]],
        "LAP-B851S-WUS": [["set_auto_mode"], ['set_sleep_mode'], ["turn_on_display"], ["turn_off_display"]],

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
        elif method_name in ["turn_off_display"]:
            fan_obj.state.display_set_status = const.DeviceStatus.ON

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

        # Parse arguments from mock_api call into a dictionary
        all_kwargs = parse_args(self.mock_api)

        # Assert request matches recorded request or write new records
        assert assert_test(
            method_call, all_kwargs, setup_entry, self.write_api, self.overwrite
        )


class TestElevaPurifier(TestBase):
    """Test the Eleva purifier."""

    setup_entry = "LAP-C511S"

    def _device_list_response(self, device_prop):
        device = {"cid": TestDefaults.cid(self.setup_entry), "deviceProp": device_prop}
        return {"code": 0, "msg": "request success", "result": {"list": [device]}}

    def test_details_overlays_device_prop(self):
        """Values from deviceProp replace the stale snapshot values."""
        device_prop = {
            "powerSwitch": 1,
            "workMode": "sleep",
            "fanSpeedLevel": 1,
            "manualSpeedLevel": 2,
            "AQLevel": 3,
            "PM1": 41,
            "PM25": 42,
            "PM10": 43,
            "AQI": 144,
            "VOC": 145,
            "NO2": 6,
        }
        self.mock_api.side_effect = [
            (self._device_list_response(device_prop), 200),
            (call_json_purifiers.DETAILS_RESPONSES[self.setup_entry], 200),
        ]
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.run_in_loop(purifier.get_details)

        state = purifier.state
        assert state.mode == "sleep"
        assert state.fan_level == 1
        assert state.fan_set_level == 2
        assert state.air_quality_level == 3
        assert (state.pm1, state.pm25, state.pm10) == (41, 42, 43)
        assert (state.aqi, state.voc, state.no2) == (144, 145, 6)
        # Snapshot-only fields still come from getPurifierStatus.
        assert state.carbon_filter_life == 97
        assert state.pre_filter_life == 90

    def test_concurrent_updates_share_device_list(self):
        """Eleva devices updated together send one device list request."""
        first = self.get_device("air_purifiers", self.setup_entry)
        config = DeviceList.device_list_item(ALL_DEVICE_MAP_DICT[self.setup_entry])
        config["cid"] = "eleva-second-cid"
        self.manager.devices.add_device_from_model(
            ResponseDeviceDetailsModel.from_dict(config), self.manager
        )
        second = next(d for d in self.manager.devices if d.cid == "eleva-second-cid")
        device_list = {
            "code": 0,
            "msg": "request success",
            "result": {
                "list": [
                    {"cid": first.cid, "deviceProp": {"PM25": 11}},
                    {"cid": second.cid, "deviceProp": {"PM25": 22}},
                ]
            },
        }

        def api(endpoint, *args, **kwargs):
            if endpoint == "/cloud/v1/deviceManaged/devices":
                return (device_list, 200)
            return (call_json_purifiers.DETAILS_RESPONSES[self.setup_entry], 200)

        self.mock_api.side_effect = api
        self.run_in_loop(self.manager.update_all_devices)

        endpoints = [call.args[0] for call in self.mock_api.call_args_list]
        assert endpoints.count("/cloud/v1/deviceManaged/devices") == 1
        assert len(endpoints) == 3
        assert (first.state.pm25, second.state.pm25) == (11, 22)

    def test_device_props_reused_within_window(self):
        """A device list result is reused briefly, then requested again."""
        response = self._device_list_response({"PM25": 5})
        self.mock_api.side_effect = [(response, 200), (response, 200)]
        with patch("pyvesync.vesync.time.monotonic") as monotonic:
            monotonic.return_value = 1000.0
            assert self.run_in_loop(self.manager.get_device_props)
            monotonic.return_value = 1000.0 + DEVICE_PROPS_REUSE_SECONDS - 1
            assert self.run_in_loop(self.manager.get_device_props)
            assert self.mock_api.call_count == 1
            monotonic.return_value = 1000.0 + DEVICE_PROPS_REUSE_SECONDS
            assert self.run_in_loop(self.manager.get_device_props)
            assert self.mock_api.call_count == 2

    def test_failed_device_props_not_reused(self):
        """A failed device list request is retried on the next call."""
        self.mock_api.side_effect = [
            ({"code": -1, "msg": "error"}, 200),
            (self._device_list_response({"PM25": 5}), 200),
        ]
        assert self.run_in_loop(self.manager.get_device_props) == {}
        props = self.run_in_loop(self.manager.get_device_props)
        assert props == {TestDefaults.cid(self.setup_entry): {"PM25": 5}}
        assert self.mock_api.call_count == 2

    def test_device_props_error_not_stuck(self):
        """An exception does not leave a pending request behind."""
        self.mock_api.side_effect = [
            RuntimeError("boom"),
            (self._device_list_response({"PM25": 5}), 200),
        ]
        with pytest.raises(RuntimeError):
            self.run_in_loop(self.manager.get_device_props)
        assert self.run_in_loop(self.manager.get_device_props)
        assert self.mock_api.call_count == 2

    def test_details_without_device_prop(self):
        """The snapshot is used unchanged when the device list call fails."""
        self.mock_api.side_effect = [
            ({"code": -1, "msg": "error"}, 200),
            (call_json_purifiers.DETAILS_RESPONSES[self.setup_entry], 200),
        ]
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.run_in_loop(purifier.get_details)

        details = call_json_purifiers.PURIFIER_DETAILS[self.setup_entry]
        assert purifier.state.pm25 == details["PM25"]
        assert purifier.state.aqi == details["AQI"]
        assert purifier.state.no2 == details["NO2"]

    def _set_success(self):
        return (build_bypass_v2_response(), 200)

    def _details(self, **override):
        return (
            build_bypass_v2_response(
                inner_result=call_json_purifiers.PURIFIER_DETAILS[self.setup_entry],
                inner_result_override=override,
            ),
            200,
        )

    def test_command_value_held_over_stale_snapshot(self):
        """A commanded value is kept while the snapshot still reports the old one."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [self._set_success()]
        assert self.run_in_loop(purifier.toggle_child_lock, True)

        # Snapshot still reports child lock off.
        self.mock_api.side_effect = [(None, 200), self._details(childLockSwitch=0)]
        self.run_in_loop(purifier.get_details)
        assert purifier.state.child_lock is True

        # Snapshot catches up: hold is released.
        self.mock_api.side_effect = [(None, 200), self._details(childLockSwitch=1)]
        self.run_in_loop(purifier.get_details)
        assert purifier.state.child_lock is True
        assert "child_lock" not in purifier._pending_state

    def test_held_value_expires(self):
        """After the hold period the snapshot value is used again."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [self._set_success()]
        assert self.run_in_loop(purifier.toggle_child_lock, True)
        value, set_at = purifier._pending_state["child_lock"]
        purifier._pending_state["child_lock"] = (
            value,
            set_at - purifier.PENDING_HOLD_SECONDS - 1,
        )

        self.mock_api.side_effect = [(None, 200), self._details(childLockSwitch=0)]
        self.run_in_loop(purifier.get_details)
        assert purifier.state.child_lock is False
        assert purifier._pending_state == {}

    def _timer_list(self, timers):
        return (build_bypass_v2_response(inner_result={"timers": timers}), 200)

    def test_set_timer_uses_countdown_format(self):
        """set_timer sends the countdown payload the device stores."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [
            (build_bypass_v2_response(inner_result={"id": 1}), 200)
        ]
        assert self.run_in_loop(purifier.set_timer, 7200)

        payload = self.mock_api.call_args.args[2].payload
        assert payload.method == "addTimerV2"
        assert payload.data == {
            "startAct": [{"type": "powerSwitch", "num": 0, "act": 0}],
            "total": 7200,
        }
        assert purifier.state.timer.id == 1
        assert purifier.state.timer.action == const.DeviceStatus.OFF

    def test_get_and_clear_timer(self):
        """get_timer parses getTimerV2 and clear_timer deletes by its ID."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        timer = {
            "id": 3,
            "remain": 7175,
            "total": 7200,
            "startAct": [{"type": "powerSwitch", "act": 0, "num": 0}],
        }
        self.mock_api.side_effect = [self._timer_list([timer])]
        result = self.run_in_loop(purifier.get_timer)
        assert result is not None
        assert (result.id, result.timer_duration) == (3, 7200)

        self.mock_api.side_effect = [self._timer_list([timer]), self._set_success()]
        assert self.run_in_loop(purifier.clear_timer)
        payload = self.mock_api.call_args.args[2].payload
        assert payload.method == "delTimerV2"
        assert payload.data == {"id": 3}
        assert purifier.state.timer is None

    def test_clear_timer_without_timer(self):
        """clear_timer succeeds without a request when the device has no timer."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [self._timer_list([])]
        assert self.run_in_loop(purifier.clear_timer) is True
        assert self.mock_api.call_count == 1
        assert purifier.state.timer is None
        assert purifier._pending_state["timer"][0] is None

        # A failed getTimerV2 request is still an error.
        self.mock_api.reset_mock()
        self.mock_api.side_effect = [(None, 200)]
        assert self.run_in_loop(purifier.clear_timer) is False
        assert self.mock_api.call_count == 1

    def test_auto_preference_read_only(self):
        """Auto preference is reported but cannot be set."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        assert purifier.auto_preferences == []
        self.mock_api.side_effect = [(None, 200), self._details()]
        self.run_in_loop(purifier.get_details)
        assert purifier.state.auto_preference_type == "default"
        self.mock_api.reset_mock()
        assert self.run_in_loop(purifier.set_auto_preference, "quiet") is False
        self.mock_api.assert_not_called()

    def test_eleva_settings_from_snapshot(self):
        """Personalized settings are read from the status snapshot."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [(None, 200), self._details()]
        self.run_in_loop(purifier.get_details)

        state = purifier.state
        assert state.auto_profile == const.PurifierAutoProfiles.ADVANCED_CARE
        assert state.dynamic_manual is True
        assert state.dynamic_sleep is True
        assert state.adaptive_start is False
        assert state.indicator_ring == const.PurifierIndicatorRingLevels.BRIGHT
        assert state.quiet_period_switch == const.DeviceStatus.OFF
        assert state.quiet_period_mode == const.PurifierQuietPeriodModes.LIGHT_CONTROL
        assert (state.quiet_period_start, state.quiet_period_end) == (79200, 21600)

    def test_auto_profile_from_device_prop(self):
        """The auto profile in deviceProp replaces the snapshot value."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [
            (self._device_list_response({"healthProtectMode": 2}), 200),
            self._details(group=3),
        ]
        self.run_in_loop(purifier.get_details)
        assert purifier.state.auto_profile == const.PurifierAutoProfiles.FOCUSED_CARE

    def test_set_quiet_period(self):
        """set_quiet_period sends all four values and holds them."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [(None, 200), self._details(), self._set_success()]
        self.run_in_loop(purifier.get_details)
        assert self.run_in_loop(
            purifier.set_quiet_period, True, "schedule", 79200, 22500
        )

        payload = self.mock_api.call_args.args[2].payload
        assert payload.method == "setQuietPeriod"
        assert payload.data == {
            "quietPeriodSwitch": 1,
            "modeIdx": 1,
            "startTime": 79200,
            "endTime": 22500,
        }

        # The stale snapshot still reports the old values.
        self.mock_api.side_effect = [(None, 200), self._details()]
        self.run_in_loop(purifier.get_details)
        assert purifier.state.quiet_period_switch == const.DeviceStatus.ON
        assert purifier.state.quiet_period_mode == const.PurifierQuietPeriodModes.SCHEDULE
        assert purifier.state.quiet_period_end == 22500

    def test_set_quiet_period_keeps_current_values(self):
        """Values not passed keep their current setting."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [(None, 200), self._details(), self._set_success()]
        self.run_in_loop(purifier.get_details)
        assert self.run_in_loop(purifier.set_quiet_period, True)
        payload = self.mock_api.call_args.args[2].payload
        assert payload.data == {
            "quietPeriodSwitch": 1,
            "modeIdx": 0,
            "startTime": 79200,
            "endTime": 21600,
        }

    def test_set_quiet_period_invalid_time(self):
        """Times outside a day are rejected without a request."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [(None, 200), self._details()]
        self.run_in_loop(purifier.get_details)
        self.mock_api.reset_mock()
        assert self.run_in_loop(purifier.set_quiet_period, True, None, 90000) is False
        self.mock_api.assert_not_called()

    def test_set_indicator_ring(self):
        """set_indicator_ring sends setAqiLight with the ring mode."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [self._set_success()]
        assert self.run_in_loop(purifier.set_indicator_ring, "dim")
        payload = self.mock_api.call_args.args[2].payload
        assert payload.method == "setAqiLight"
        assert payload.data == {"mode": 2}
        assert purifier.state.indicator_ring == const.PurifierIndicatorRingLevels.DIM

        self.mock_api.reset_mock()
        assert self.run_in_loop(purifier.set_indicator_ring, "medium") is False
        self.mock_api.assert_not_called()

    def test_timer_state_from_snapshot(self):
        """timerRemain sets a timer, and 0 clears it."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [(None, 200), self._details(timerRemain=600)]
        self.run_in_loop(purifier.get_details)
        assert purifier.state.timer is not None
        assert 0 < purifier.state.timer.time_remaining <= 600

        self.mock_api.side_effect = [(None, 200), self._details(timerRemain=0)]
        self.run_in_loop(purifier.get_details)
        assert purifier.state.timer is None

    def test_timer_set_held_over_stale_snapshot(self):
        """A timer set from the library survives a stale snapshot."""
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [
            (build_bypass_v2_response(inner_result={"id": 1}), 200)
        ]
        assert self.run_in_loop(purifier.set_timer, 7200)
        timer = purifier.state.timer

        # Snapshot has not caught up yet.
        self.mock_api.side_effect = [(None, 200), self._details(timerRemain=0)]
        self.run_in_loop(purifier.get_details)
        assert purifier.state.timer is timer

        # Snapshot reports the timer: the local countdown is kept.
        self.mock_api.side_effect = [(None, 200), self._details(timerRemain=7000)]
        self.run_in_loop(purifier.get_details)
        assert purifier.state.timer is timer
        assert "timer" not in purifier._pending_state


class TestLightDetectionToggle(TestBase):
    """Test toggling light detection on V2 purifiers."""

    setup_entry = "LAP-V201S"

    def test_light_detection_off_in_dark_room(self):
        """Turning light detection off is sent when the room is dark."""
        details = build_bypass_v2_response(
            inner_result=call_json_purifiers.PURIFIER_DETAILS[self.setup_entry],
            inner_result_override={"lightDetectionSwitch": 1, "environmentLightState": 0},
        )
        purifier = self.get_device("air_purifiers", self.setup_entry)
        self.mock_api.side_effect = [
            (details, 200),
            (build_bypass_v2_response(), 200),
        ]
        self.run_in_loop(purifier.get_details)
        assert self.run_in_loop(purifier.toggle_light_detection, False)

        payload = self.mock_api.call_args.args[2].payload
        assert payload.method == "setLightDetection"
        assert payload.data == {"lightDetectionSwitch": 0}
        assert purifier.state.light_detection_switch == const.DeviceStatus.OFF
