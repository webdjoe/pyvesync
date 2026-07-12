"""Tests for air fryer temperature unit handling.

Verifies that device_map is the source of truth for temperature units
and steps, that devices/state operate in device units, and that the
API-reported unit overrides the map default after update().
"""

import inspect

import call_json_fryers
from base_test_cases import TestBase
from defaults import build_bypass_v1_response

from pyvesync.base_devices.fryer_base import FryerState
from pyvesync.const import AIRFRYER_STEP_F_TO_C, TemperatureUnits
from pyvesync.device_map import air_fryer_modules


def test_map_declares_temp_unit_and_step():
    """Every AirFryerMap entry declares a unit and a single (Fahrenheit) step."""
    for entry in air_fryer_modules:
        assert isinstance(entry.temp_unit, TemperatureUnits)
        assert entry.temperature_step_f > 0
        # Celsius step is derived, not declared on the map.
        assert not hasattr(entry, 'temperature_step_c')
        assert entry.temperature_step_f in AIRFRYER_STEP_F_TO_C


def test_celsius_step_derived_from_map():
    """The F-to-C step map converts 5F to 2C and 10F to 5C."""
    assert AIRFRYER_STEP_F_TO_C[5] == 2
    assert AIRFRYER_STEP_F_TO_C[10] == 5


def test_region_entries_have_expected_units():
    """Region-split entries declare the correct unit."""
    units = {m.setup_entry: m.temp_unit for m in air_fryer_modules}
    assert units['CS158-AF'] == TemperatureUnits.FAHRENHEIT
    assert units['CAF-DC601S'] == TemperatureUnits.FAHRENHEIT
    assert units['CAF-P583S'] == TemperatureUnits.FAHRENHEIT
    assert units['CAF-P583S-KEU'] == TemperatureUnits.CELSIUS
    assert units['CAF-TF101S'] == TemperatureUnits.CELSIUS


def test_dual_blaze_split_by_region():
    """KUS and KEU Dual Blaze variants are separate entries."""
    kus = [m for m in air_fryer_modules if 'CAF-P583S-KUS' in m.dev_types]
    keu = [m for m in air_fryer_modules if 'CAF-P583S-KEU' in m.dev_types]
    assert len(kus) == 1
    assert len(keu) == 1
    assert kus[0] is not keu[0]


class TestFryerUnitHandling(TestBase):
    """Device/state unit behavior driven by the device map."""

    def test_unit_seeded_from_map(self):
        us_fryer = self.get_device('air_fryers', 'CAF-P583S')
        eu_fryer = self.get_device('air_fryers', 'CAF-P583S-KEU')
        assert us_fryer.temp_unit == TemperatureUnits.FAHRENHEIT
        assert eu_fryer.temp_unit == TemperatureUnits.CELSIUS

    def test_state_exposes_device_unit(self):
        eu_fryer = self.get_device('air_fryers', 'CAF-P583S-KEU')
        assert eu_fryer.state.temp_unit == TemperatureUnits.CELSIUS
        assert eu_fryer.state_chamber_2.temp_unit == TemperatureUnits.CELSIUS

    def test_temperature_step_follows_unit(self):
        eu_fryer = self.get_device('air_fryers', 'CAF-P583S-KEU')
        assert eu_fryer.temperature_step == eu_fryer.temperature_step_c
        eu_fryer.temp_unit = TemperatureUnits.FAHRENHEIT
        assert eu_fryer.temperature_step == eu_fryer.temperature_step_f

    def test_round_temperature_celsius_whole_steps(self):
        eu_fryer = self.get_device('air_fryers', 'CAF-P583S-KEU')
        # EU Dual Blaze: 5F step derives a 2C step; temps round to nearest 2C.
        assert eu_fryer.temperature_step == 2
        assert eu_fryer.round_temperature(184) == 184
        assert eu_fryer.round_temperature(200) == 200
        assert eu_fryer.round_temperature(183) == 184
        assert eu_fryer.round_temperature(181) == 180

    def test_min_max_temp_follow_unit(self):
        eu_fryer = self.get_device('air_fryers', 'CAF-P583S-KEU')
        assert (eu_fryer.min_temp, eu_fryer.max_temp) == (80, 205)
        eu_fryer.temp_unit = TemperatureUnits.FAHRENHEIT
        assert (eu_fryer.min_temp, eu_fryer.max_temp) == (175, 400)

    def test_api_unit_overrides_map_default(self):
        """CAF-TF101S map default is Celsius; fixture reports fahrenheit."""
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        assert fryer.temp_unit == TemperatureUnits.CELSIUS
        self.mock_api.return_value = (
            call_json_fryers.DETAILS_RESPONSES_COOKING['CAF-TF101S'],
            200,
        )
        self.run_in_loop(fryer.update)
        assert fryer.temp_unit == TemperatureUnits.FAHRENHEIT
        assert fryer.state.temp_unit == TemperatureUnits.FAHRENHEIT

    def test_api_unit_overrides_for_158(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (
            call_json_fryers.DETAILS_RESPONSES_COOKING['CS158-AF'],
            200,
        )
        self.run_in_loop(fryer.update)
        assert fryer.temp_unit == TemperatureUnits.FAHRENHEIT

    def test_set_state_has_no_temp_unit_param(self):
        """set_state must not mutate device config; unit comes via get_details."""
        params = inspect.signature(FryerState.set_state).parameters
        assert 'temp_unit' not in params

    def test_turboblaze_set_mode_rejects_out_of_range(self):
        """TurboBlaze previously skipped validation entirely."""
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.reset_mock()
        result = self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=500)
        assert result is False
        assert self.mock_api.call_count == 0

    def test_set_mode_rounds_before_validating(self):
        """402F rounds to 400F (max) and must be accepted, not rejected."""
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (
            build_bypass_v1_response(result_dict={}),
            200,
        )
        result = self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=402)
        assert result is True
        assert fryer.state.cook_set_temp == 400

    def test_dual_set_mode_rejects_out_of_range(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.reset_mock()
        # Map unit is Celsius; 300C is above the 240C max.
        result = self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=300)
        assert result is False
        assert self.mock_api.call_count == 0
