"""Tests for air fryer temperature unit handling.

Verifies that device_map is the source of truth for temperature units
and steps, that devices/state operate in device units, and that the
API-reported unit overrides the map default after update().
"""

import dataclasses
import inspect
from datetime import UTC, datetime, timedelta

import pytest

import call_json_fryers
from base_test_cases import TestBase
from defaults import build_bypass_v1_response, build_bypass_v2_response
from utils import parse_args

from pyvesync.base_devices.fryer_base import FryerState
from pyvesync.const import (
    AirFryerCookModes,
    AirFryerCookStatus,
    AirFryerFeatures,
    AirFryerModeConfig,
    AirFryerTempLimits,
    TemperatureUnits,
)
from pyvesync.device_map import air_fryer_modules


# setup_entry -> {api_mode: (recipe_id, recipe_name, cook_time,
#                            (C min, max, step), (F min, max, step),
#                            (default C, default F))}
# Copied from docs/development/reviews/apk/kitchen-temperature-limits.md.
_CS_C, _CS_F = (75, 205, 5), (170, 400, 10)
APK_PRESETS = {
    'CS158-AF': {
        'custom': (1, 'Manual Cooking', 900, _CS_C, _CS_F, (175, 350)),
        'steak': (2, 'Steak', 360, _CS_C, _CS_F, (205, 400)),
        'poultry': (3, 'Chicken', 1500, _CS_C, _CS_F, (195, 380)),
        'fish': (4, 'Seafood', 480, _CS_C, _CS_F, (175, 350)),
        'bacon': (5, 'Bacon', 480, _CS_C, _CS_F, (160, 320)),
        'vegetables': (6, 'Vegetables', 600, _CS_C, _CS_F, (150, 300)),
        'rootVeggies': (7, 'Root Vegetables', 720, _CS_C, _CS_F, (205, 400)),
        'frozenFood': (8, 'Frozen Food', 600, _CS_C, _CS_F, (175, 300)),
        'desserts': (9, 'Desserts', 1800, _CS_C, _CS_F, (150, 300)),
        'shrimp': (10, 'Shrimp', 2100, _CS_C, _CS_F, (190, 370)),
        'bread': (11, 'Bread', 480, _CS_C, _CS_F, (160, 320)),
        'frenchFries': (12, 'French Fries', 1500, _CS_C, _CS_F, (195, 380)),
    },
    'CAF-DC601S': {
        'AirFry': (14, 'Air Fry', 600, (150, 230, 5), (300, 450, 5), (195, 385)),
        'Roast': (13, 'Roast', 720, (175, 230, 5), (350, 450, 5), (220, 425)),
        'Broil': (17, 'Broil', 300, (220, 230, 5), (425, 450, 5), (230, 450)),
        'Frozen': (5, 'Frozen', 840, (150, 230, 5), (300, 450, 5), (200, 390)),
        'Reheat': (16, 'Reheat', 300, (150, 220, 5), (300, 425, 5), (200, 390)),
        'Bake': (9, 'Bake', 1200, (125, 205, 5), (260, 400, 5), (165, 330)),
        'Dry': (21, 'Dry', 21600, (35, 95, 5), (100, 200, 5), (55, 135)),
        'Proof': (27, 'Proof', 3600, (30, 45, 1), (90, 110, 1), (30, 90)),
        'Warm': (26, 'Warm', 1800, (75, 75, 1), (170, 170, 1), (75, 170)),
    },
    'CAF-P583S': {
        'AirFry': (14, 'Air Fry', 600, (80, 205, 5), (175, 400, 5), (180, 360)),
        'Broil': (17, 'Broil', 600, (175, 205, 5), (350, 400, 5), (205, 400)),
        'Roast': (13, 'Roast', 600, (80, 205, 5), (175, 400, 5), (205, 400)),
        'Bake': (9, 'Bake', 1200, (120, 205, 5), (250, 400, 5), (160, 320)),
        'Chicken': (2, 'Chicken', 1200, (175, 205, 5), (350, 400, 5), (200, 390)),
        'Steak': (1, 'Steak', 480, (80, 205, 5), (175, 400, 5), (205, 400)),
        'Seafood': (3, 'Seafood', 480, (160, 205, 5), (320, 400, 5), (190, 375)),
        'Veggies': (15, 'Veggies', 360, (160, 205, 5), (320, 400, 5), (195, 385)),
        'French fries': (6, 'French Fries', 1200, (175, 205, 5), (350, 400, 5), (195, 385)),
        'Frozen': (5, 'Frozen', 720, (175, 205, 5), (350, 400, 5), (200, 395)),
        'Reheat': (16, 'Reheat', 300, (150, 205, 5), (300, 400, 5), (175, 350)),
    },
    'CAF-TF101S': {
        'AirFry': (14, 'Air Fry', 1200, (120, 205, 5), (250, 400, 5), (200, 390)),
        'Roast': (13, 'Roast', 1800, (120, 205, 5), (250, 400, 5), (190, 375)),
        'Bake': (9, 'Bake', 1500, (80, 205, 5), (175, 400, 5), (160, 320)),
        'Grill': (20, 'Grill', 600, (205, 240, 5), (400, 465, 5), (240, 465)),
        'Reheat': (16, 'Reheat', 900, (40, 205, 5), (105, 400, 5), (165, 330)),
        'Dry': (21, 'Dry', 21600, (35, 95, 5), (95, 205, 5), (55, 130)),
    },
    # APK i61.C114379l (DC111SEUConfig).
    'CAF-DC111S-AEU': {
        'AirFry': (14, 'Air Fry', 600, (120, 230, 5), (250, 450, 5), (195, 385)),
        'Bake': (9, 'Bake', 1200, (125, 205, 5), (260, 400, 5), (165, 330)),
        'Roast': (13, 'Roast', 720, (175, 230, 5), (350, 450, 5), (220, 425)),
        'Grill': (20, 'Grill', 600, (160, 230, 5), (320, 450, 5), (230, 450)),
        'Reheat': (16, 'Reheat', 300, (40, 205, 5), (105, 400, 5), (165, 330)),
        'Dry': (21, 'Dry', 21600, (35, 95, 5), (100, 200, 5), (55, 130)),
        'Proof': (27, 'Proof', 3600, (30, 45, 1), (90, 115, 1), (30, 90)),
    },
}
APK_PRESETS['CAF-P583S-KEU'] = APK_PRESETS['CAF-P583S']
# APK i61.C67932h0 (TF102SEUConfig): the TF101S presets without Dry.
APK_PRESETS['CAF-TF102S'] = {
    mode: row for mode, row in APK_PRESETS['CAF-TF101S'].items() if mode != 'Dry'
}


def _as_rows(entry):
    def lim(t):
        return (t.min_temp, t.max_temp, t.step)

    return {
        m.api_mode: (
            m.recipe_id,
            m.recipe_name,
            m.cook_time,
            lim(m.temp_c),
            lim(m.temp_f),
            (m.default_temp_c, m.default_temp_f),
        )
        for m in entry.cook_modes.values()
    }


def test_presets_match_apk():
    for entry in air_fryer_modules:
        assert _as_rows(entry) == APK_PRESETS[entry.setup_entry], entry.setup_entry


def test_every_preset_is_recipe_type_3_and_keyed_by_enum():
    for entry in air_fryer_modules:
        for key, mode in entry.cook_modes.items():
            assert isinstance(key, AirFryerCookModes), (entry.setup_entry, key)
            assert isinstance(mode, AirFryerModeConfig)
            assert mode.recipe_type == 3


def test_default_preset_agrees_with_its_mode():
    for entry in air_fryer_modules:
        assert isinstance(entry.temp_unit, TemperatureUnits)
        default = entry.default_preset
        match = [m for m in entry.cook_modes.values() if m.api_mode == default.cook_mode]
        assert len(match) == 1, entry.setup_entry
        assert match[0].recipe_id == default.recipe_id
        assert match[0].recipe_type == default.recipe_type
        assert entry.cook_modes[entry.default_cook_mode].api_mode == default.cook_mode


def test_tf102s_has_own_entry_without_dry():
    by_type = {t: e for e in air_fryer_modules for t in e.dev_types}
    tf102 = by_type['CAF-TF102S']
    assert tf102.setup_entry == 'CAF-TF102S'
    assert tf102.class_name == by_type['CAF-TF101S'].class_name == 'VeSyncDualAirFryer'
    assert AirFryerCookModes.DRY not in tf102.cook_modes
    assert AirFryerCookModes.DRY in by_type['CAF-TF101S'].cook_modes
    assert tf102.status_map == by_type['CAF-TF101S'].status_map
    assert tf102.features == by_type['CAF-TF101S'].features


def test_dc111s_entry_is_dual_without_whole_and_maps_hold():
    by_type = {t: e for e in air_fryer_modules for t in e.dev_types}
    dc111 = by_type['CAF-DC111S-AEU']
    assert dc111.setup_entry == 'CAF-DC111S-AEU'
    assert dc111.class_name == 'VeSyncDualAirFryer'
    assert dc111.features == [AirFryerFeatures.DUAL_CHAMBER]
    assert dc111.temp_unit == TemperatureUnits.CELSIUS
    assert dc111.status_map['hold'] == AirFryerCookStatus.HOLD
    tf10x = by_type['CAF-TF101S'].status_map
    assert {k: v for k, v in dc111.status_map.items() if k != 'hold'} == dict(tf10x)
    assert 'hold' not in tf10x


def test_limits_are_frozen():
    limits = AirFryerTempLimits(min_temp=80, max_temp=205, step=5)
    with pytest.raises(dataclasses.FrozenInstanceError):
        limits.max_temp = 250


def test_to_recipe_uses_unit_default():
    mode = next(
        m for m in next(e for e in air_fryer_modules if e.setup_entry == 'CAF-TF101S')
        .cook_modes.values() if m.api_mode == 'Grill'
    )
    recipe = mode.to_recipe(TemperatureUnits.CELSIUS)
    assert (recipe.cook_mode, recipe.recipe_id, recipe.recipe_name) == ('Grill', 20, 'Grill')
    assert (recipe.target_temp, recipe.temp_unit, recipe.cook_time) == (240, 'c', 600)
    assert mode.to_recipe(TemperatureUnits.FAHRENHEIT).target_temp == 465


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


@pytest.mark.parametrize(
    ('raw', 'unit'),
    [
        ('c', TemperatureUnits.CELSIUS),
        ('celsius', TemperatureUnits.CELSIUS),
        ('Celcius', TemperatureUnits.CELSIUS),
        (' C ', TemperatureUnits.CELSIUS),
        ('f', TemperatureUnits.FAHRENHEIT),
        ('fahrenheit', TemperatureUnits.FAHRENHEIT),
        ('Farenheit', TemperatureUnits.FAHRENHEIT),
        ('F', TemperatureUnits.FAHRENHEIT),
    ],
)
def test_from_string_matches_first_letter(raw, unit):
    assert TemperatureUnits.from_string(raw) is unit


def test_from_string_rejects_other_units():
    with pytest.raises(ValueError):
        TemperatureUnits.from_string('kelvin')


class TestFryerUnitHandling(TestBase):
    """Device/state unit behavior driven by the device map."""

    def test_preheat_helpers_take_seconds(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')  # minutes on the API
        fryer.state.set_preheat_stop_state(preheat_set_time=300)
        assert fryer.state.preheat_set_time == 300
        fryer.state.set_preheat_resume_state(preheat_set_time=240)
        assert fryer.state.preheat_set_time == 240

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
        fryer = self.get_device('air_fryers', 'CS158-AF')
        fryer.temp_unit = TemperatureUnits.CELSIUS
        assert fryer.temperature_step == 5
        fryer.temp_unit = TemperatureUnits.FAHRENHEIT
        assert fryer.temperature_step == 10

    def test_round_temperature_celsius_five_degree_step(self):
        eu_fryer = self.get_device('air_fryers', 'CAF-P583S-KEU')
        # APK i61.C114382w: every mode 5 C.
        assert eu_fryer.temperature_step == 5
        assert eu_fryer.round_temperature(185) == 185
        assert eu_fryer.round_temperature(183) == 185
        assert eu_fryer.round_temperature(181) == 180

    def test_min_max_temp_follow_unit(self):
        eu_fryer = self.get_device('air_fryers', 'CAF-P583S-KEU')
        assert (eu_fryer.min_temp, eu_fryer.max_temp) == (80, 205)
        eu_fryer.temp_unit = TemperatureUnits.FAHRENHEIT
        assert (eu_fryer.min_temp, eu_fryer.max_temp) == (175, 400)

    def test_device_span_is_widest_mode_span(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        assert (fryer.min_temp_c, fryer.max_temp_c) == (35, 240)
        assert (fryer.min_temp_f, fryer.max_temp_f) == (95, 465)
        dc601 = self.get_device('air_fryers', 'CAF-DC601S')
        assert (dc601.min_temp_f, dc601.max_temp_f) == (90, 450)

    def test_get_cook_mode_by_key_or_api_mode(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        by_key = fryer.get_cook_mode(AirFryerCookModes.CHICKEN)
        assert by_key is fryer.get_cook_mode('poultry')
        assert by_key.recipe_id == 3
        assert fryer.get_cook_mode().api_mode == 'custom'
        assert fryer.get_cook_mode('Grill') is None

    def test_mode_recipe_in_current_unit(self):
        fryer = self.get_device('air_fryers', 'CAF-P583S-KEU')  # Celsius
        recipe = fryer.get_mode_recipe('french_fries')
        assert (recipe.cook_mode, recipe.recipe_id, recipe.target_temp) == ('French fries', 6, 195)
        assert fryer.get_mode_recipe('Grill') is None

    def test_temp_limits_per_mode(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')  # Celsius
        assert fryer.temp_limits('Grill') == AirFryerTempLimits(205, 240, 5)
        assert fryer.temp_limits(AirFryerCookModes.DRY) == AirFryerTempLimits(35, 95, 5)
        assert fryer.temp_limits() == AirFryerTempLimits(120, 205, 5)
        fryer.temp_unit = TemperatureUnits.FAHRENHEIT
        assert fryer.temp_limits('Grill') == AirFryerTempLimits(400, 465, 5)

    def test_unknown_mode_uses_default_mode_limits(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        assert fryer.temp_limits('Frozen') == fryer.temp_limits()

    def test_validate_uses_request_mode(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        assert fryer.validate_temperature(240, cook_mode='Grill') is True
        assert fryer.validate_temperature(240, cook_mode='AirFry') is False
        assert fryer.validate_temperature(40, cook_mode='Dry') is True
        assert fryer.validate_temperature(40, cook_mode='Bake') is False

    def test_dc601s_proof_one_degree_step(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')  # Fahrenheit
        assert fryer.round_temperature(97, cook_mode='Proof') == 97
        assert fryer.round_temperature(97, cook_mode='AirFry') == 95
        assert fryer.validate_temperature(111, cook_mode='Proof') is False

    def test_dc601s_warm_is_fixed(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        assert fryer.validate_temperature(170, cook_mode='Warm') is True
        assert fryer.validate_temperature(175, cook_mode='Warm') is False

    def test_cook_stop_freezes_live_remaining(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        st = fryer.state
        st.set_state(cook_status=AirFryerCookStatus.COOKING, cook_time=10, cook_last_time=10, cook_temp=350)
        st.last_timestamp = datetime.now(UTC) - timedelta(seconds=120)
        st.set_cook_stop_state()
        assert st.cook_last_time == 600 - 120

    def test_cook_stop_from_api_uses_reported_remaining(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        fryer.state.set_state(cook_status=AirFryerCookStatus.COOK_STOP, cook_time=1200, cook_last_time=900)
        assert fryer.state.cook_time_remaining == 900

    def test_preheat_stop_from_api_keeps_reported_values(self):
        # CS158 preheatStop capture: preheatSetTime 5, preheatLastTime 5 (minutes), targetTemp 400.
        fryer = self.get_device('air_fryers', 'CS158-AF')
        fryer.state.set_state(
            cook_status=AirFryerCookStatus.PREHEAT_STOP,
            preheat_set_time=5, preheat_last_time=5, cook_temp=400, cook_mode='custom',
        )
        assert fryer.state.preheat_time_remaining == 300
        assert fryer.state.cook_set_temp == 400
        assert fryer.state.cook_mode == 'custom'

    def test_set_mode_converts_given_unit(self):
        # TF101S map unit is Celsius; 390 F = 198.9 C -> 200 C on the 5 C step.
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=390, temp_unit='f')
        data = parse_args(self.mock_api)['json_object']['payload']['data']
        assert data['tempUnit'] == 'c'
        assert data['cookConfigs'][0]['cookTemp'] == 200
        assert fryer.state_chamber_1.cook_set_temp == 200

    def test_set_mode_same_unit_is_unchanged(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=400, temp_unit=TemperatureUnits.FAHRENHEIT)
        assert parse_args(self.mock_api)['json_object']['payload']['data']['startAct']['cookTemp'] == 400

    def test_set_mode_converted_out_of_range_rejected(self):
        # 250 C = 482 F, above the CS158 400 F max.
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.reset_mock()
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=250, temp_unit='c') is False
        assert self.mock_api.call_count == 0

    def test_set_mode_invalid_unit_returns_false(self):
        fryer = self.get_device('air_fryers', 'CAF-P583S')
        self.mock_api.reset_mock()
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=400, temp_unit='kelvin') is False
        assert self.mock_api.call_count == 0

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
