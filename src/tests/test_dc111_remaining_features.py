"""DC111S features transferred onto the common fryer interface.

Request fields and sync values come from the owner's direct PR 564 checks.
Duration ranges/steps were read by the owner from the app; these tests use no
live hardware and do not claim physical verification of the new methods.
"""

from copy import deepcopy
from dataclasses import replace

import pytest
from base_test_cases import TestBase
from defaults import build_bypass_v2_response
from utils import parse_args

from pyvesync.const import AirFryerChamber as Ch, AirFryerCookStatus, AirFryerFeatures, AirFryerSyncType, TemperatureUnits
from pyvesync.device_map import air_fryer_modules


RANGES = {
    'AirFry': (60, 3600, 60), 'Bake': (60, 3600, 60),
    'Roast': (60, 3600, 60), 'Grill': (60, 3600, 60),
    'Reheat': (60, 3600, 60), 'Dry': (1800, 86400, 1800),
    'Proof': (900, 43200, 900),
}


def test_new_chamber_modes_are_enabled_only_on_verified_model():
    assert [m.setup_entry for m in air_fryer_modules if AirFryerFeatures.CHAMBER_MODES in m.features] == ['CAF-DC111S-AEU']


def test_existing_temperature_configuration_is_preserved():
    dc111 = next(m for m in air_fryer_modules if m.setup_entry == 'CAF-DC111S-AEU')
    assert dc111.cook_modes['proof'].temp_c.step == 1
    for entry in air_fryer_modules:
        if entry.setup_entry != 'CAF-DC111S-AEU':
            assert all(m.time_limits is None for m in entry.cook_modes.values())


class TestDc111RemainingFeatures(TestBase):
    def _device(self):
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        fryer.state_chamber_1.set_standby()
        fryer.state_chamber_2.set_standby()
        return fryer

    def _data(self):
        return parse_args(self.mock_api)['json_object']['payload']['data']

    def test_sync_preserves_separate_recipes_and_inputs(self):
        fryer = self._device()
        first = replace(fryer.get_mode_recipe('AirFry'), target_temp=180, cook_time=180)
        second = replace(fryer.get_mode_recipe('Bake'), target_temp=160, cook_time=300)
        before = deepcopy((first, second))
        assert self.run_in_loop(fryer.set_chamber_modes, first, second)
        data = self._data()
        assert data['syncType'] == 2 and data['workChamber'] == 4
        assert data['readyStart'] is False
        assert [(c['chamber'], c['mode'], c['cookTemp'], c['cookSetTime'], c['recipeId'], c['recipeType']) for c in data['cookConfigs']] == [(1, 'AirFry', 180, 180, 14, 3), (2, 'Bake', 160, 300, 9, 3)]
        assert (first, second) == before
        assert fryer.state_chamber_1.cook_set_time == 180
        assert fryer.state_chamber_2.cook_set_time == 300
        assert fryer.state_chamber_1.cook_set_temp == 180
        assert fryer.state_chamber_2.cook_set_temp == 160
        # Captured SYNC semantics: the shorter basket waits 120 seconds.
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.HOLD
        assert fryer.state_chamber_1.cook_last_time == 120
        assert fryer.state_chamber_1.total_last_time == 300
        assert fryer.state_chamber_2.cook_status == AirFryerCookStatus.COOKING
        assert fryer.state_chamber_2.cook_last_time == 300
        assert fryer.state_chamber_2.total_last_time == 300
        assert fryer.sync_chambers is True

    @pytest.mark.parametrize('source_mode', ['AirFry', 'Bake'])
    def test_match_can_use_a_recipe_from_either_basket(self, source_mode):
        fryer = self._device()
        source = replace(fryer.get_mode_recipe(source_mode), target_temp=180, cook_time=180)
        assert self.run_in_loop(fryer.set_chamber_modes, source, sync_type=AirFryerSyncType.MATCH)
        data = self._data()
        assert data['syncType'] == 1 and data['workChamber'] == 4
        a, b = deepcopy(data['cookConfigs'])
        assert a.pop('chamber') == 1 and b.pop('chamber') == 2
        assert a == b and a['mode'] == source_mode
        assert fryer.state_chamber_1.cook_status == fryer.state_chamber_2.cook_status == AirFryerCookStatus.COOKING
        assert fryer.sync_chambers is False  # This property specifically means SYNC, not MATCH.

    @pytest.mark.parametrize('sync_type,second', [(0, True), (3, True), (True, True), (False, True), ('2', True), (2.0, True), (AirFryerSyncType.SYNC, False), (AirFryerSyncType.MATCH, True)])
    def test_invalid_combination_sends_no_request(self, sync_type, second):
        fryer = self._device()
        recipe = fryer.get_mode_recipe('AirFry')
        assert self.run_in_loop(fryer.set_chamber_modes, recipe, recipe if second else None, sync_type=sync_type) is False
        self.mock_api.assert_not_called()

    @pytest.mark.parametrize('setup_entry', ['CS158-AF', 'CAF-DC601S', 'CAF-P583S', 'CAF-TF101S', 'CAF-TF102S'])
    def test_other_models_do_not_gain_untested_controls(self, setup_entry):
        fryer = self.get_device('air_fryers', setup_entry)
        recipe = fryer.get_mode_recipe()
        assert self.run_in_loop(fryer.set_chamber_modes, recipe, recipe) is False
        self.mock_api.assert_not_called()

    def test_invalid_second_recipe_does_not_partially_start_first(self):
        fryer = self._device()
        first = fryer.get_mode_recipe('AirFry')
        second = replace(fryer.get_mode_recipe('Dry'), cook_time=60)
        assert self.run_in_loop(fryer.set_chamber_modes, first, second) is False
        self.mock_api.assert_not_called()
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.STANDBY

    def test_refused_sync_does_not_replace_existing_states(self):
        fryer = self._device()
        fryer.state_chamber_1.set_state(cook_status=AirFryerCookStatus.COOK_STOP, cook_time=180, cook_last_time=100, cook_temp=180)
        self.mock_api.return_value = (build_bypass_v2_response(inner_code=11914000), 200)
        first = fryer.get_mode_recipe('AirFry')
        second = fryer.get_mode_recipe('Bake')
        assert self.run_in_loop(fryer.set_chamber_modes, first, second) is False
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOK_STOP
        assert fryer.state_chamber_1.cook_set_temp == 180
        assert fryer.state_chamber_2.cook_status == AirFryerCookStatus.STANDBY

    @pytest.mark.parametrize('mode', list(RANGES))
    @pytest.mark.parametrize('unit', [TemperatureUnits.CELSIUS, TemperatureUnits.FAHRENHEIT])
    @pytest.mark.parametrize('chamber', [Ch.CHAMBER_1, Ch.CHAMBER_2])
    @pytest.mark.parametrize('boundary', [0, 1])
    def test_owner_reported_time_boundaries(self, mode, unit, chamber, boundary):
        fryer = self._device()
        fryer.temp_unit = unit
        lo, hi, step = RANGES[mode]
        recipe = replace(fryer.get_mode_recipe(mode), cook_time=(lo, hi)[boundary])
        assert self.run_in_loop(fryer.set_mode_from_recipe, recipe, chamber=chamber)
        assert self._data()['cookConfigs'][0]['cookSetTime'] == (lo, hi)[boundary]

    @pytest.mark.parametrize('mode', list(RANGES))
    @pytest.mark.parametrize('bad_kind', ['below', 'above', 'off_step', 'bool', 'fraction'])
    def test_invalid_mode_times_send_no_request(self, mode, bad_kind):
        fryer = self._device()
        lo, hi, step = RANGES[mode]
        seconds = {'below':lo-1, 'above':hi+1, 'off_step':lo+1, 'bool':True, 'fraction':float(lo)+0.5}[bad_kind]
        recipe = replace(fryer.get_mode_recipe(mode), cook_time=seconds)
        assert self.run_in_loop(fryer.set_mode_from_recipe, recipe) is False
        self.mock_api.assert_not_called()
