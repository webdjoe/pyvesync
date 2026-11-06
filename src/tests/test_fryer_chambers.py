"""Air fryer chamber interface tests (AirFryerChamber, supported chambers)."""

import logging
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta

import pytest
from base_test_cases import TestBase
from call_json_fryers import AIR_FRYER_COOKING_DETAILS
from defaults import build_bypass_v2_response
from utils import parse_args

from pyvesync.const import AirFryerChamber, AirFryerCookStatus, AirFryerFeatures, AirFryerSyncType
from pyvesync.const import AirFryerChamber as Ch
from pyvesync.device_map import air_fryer_modules


def _tf101s_chamber(chamber: int, cook_status: str) -> dict:
    """Build one TF101S statusList item (AirFry 200 C, 1200 s capture)."""
    active = cook_status != 'standby'
    return {
        'cookStatus': cook_status,
        'startTime': 1768667721 if active else 0,
        'recipeType': 3,
        'recipeId': 14,
        'recipeName': 'Frittura ad aria' if active else '',
        'upc': '',
        'holdTime': 0,
        'cookSetTime': 1200 if active else 0,
        'cookTemp': 200 if active else 0,
        'mode': 'AirFry',
        'currentRemainingTime': 1140 if active else 0,
        'totalTimeRemaining': 1140 if active else 0,
        'chamber': chamber,
    }


def _tf101s_status(status_list: list[dict], work_chamber: int, sync_type: int = 0) -> dict:
    """Build a TF101S getAirfryerMultiStatus response."""
    return build_bypass_v2_response(
        inner_result={
            'statusList': status_list,
            'tempUnit': 'c',
            'syncType': sync_type,
            'workChamber': work_chamber,
        }
    )


# CAF-DC111S-AEU Sync cook (author's HAR, PR #536): chamber 2 waits in
# ``hold`` so both chambers finish together.
DC111S_SYNC_HOLD = {
    'statusList': [
        {'cookStatus': 'cooking', 'startTime': 1793607528, 'recipeType': 3, 'recipeId': 14,
         'recipeName': '', 'upc': '', 'holdTime': 0, 'cookSetTime': 600, 'cookTemp': 195,
         'mode': 'AirFry', 'currentRemainingTime': 596, 'totalTimeRemaining': 596, 'chamber': 1},
        {'cookStatus': 'hold', 'startTime': 1793607528, 'recipeType': 3, 'recipeId': 14,
         'recipeName': '', 'upc': '', 'holdTime': 300, 'cookSetTime': 300, 'cookTemp': 195,
         'mode': 'AirFry', 'currentRemainingTime': 296, 'totalTimeRemaining': 596, 'chamber': 2},
    ],
    'tempUnit': 'c',
    'syncType': 2,
    'workChamber': 4,
}


# The same Sync cook with chamber 1 paused: chamber 2's wait stops at 279 on
# every poll until chamber 1 cooks again (author's HAR, PR #536).
DC111S_SYNC_HOLD_PAUSED = {
    'statusList': [
        {'cookStatus': 'cookStop', 'startTime': 1793607528, 'recipeType': 3, 'recipeId': 14,
         'recipeName': '', 'upc': '', 'holdTime': 0, 'cookSetTime': 600, 'cookTemp': 195,
         'mode': 'AirFry', 'currentRemainingTime': 579, 'totalTimeRemaining': 579, 'chamber': 1},
        {'cookStatus': 'hold', 'startTime': 1793607528, 'recipeType': 3, 'recipeId': 14,
         'recipeName': '', 'upc': '', 'holdTime': 300, 'cookSetTime': 300, 'cookTemp': 195,
         'mode': 'AirFry', 'currentRemainingTime': 279, 'totalTimeRemaining': 579, 'chamber': 2},
    ],
    'tempUnit': 'c',
    'syncType': 2,
    'workChamber': 4,
}


def _entry(setup_entry):
    return next(m for m in air_fryer_modules if m.setup_entry == setup_entry)


def test_chamber_values_match_api_work_chamber():
    # APK WorkChamberType: ZONE_1 1, ZONE_2 2, GRAND_ZONE 3, DOUBLE_ZONE 4.
    assert [int(c) for c in AirFryerChamber] == [1, 2, 3, 4]
    assert AirFryerChamber(3) is AirFryerChamber.WHOLE


def test_whole_chamber_only_on_twinfry_models():
    # TF101S and TF102S (APK config lists GRAND_ZONE for both).
    twinfry = ('CAF-TF101S', 'CAF-TF102S')
    for entry in air_fryer_modules:
        has_whole = AirFryerFeatures.WHOLE_CHAMBER in entry.features
        assert has_whole is (entry.setup_entry in twinfry), entry.setup_entry


def test_sync_type_values_match_apk():
    assert [int(m) for m in AirFryerSyncType] == [0, 1, 2]
    assert AirFryerSyncType.SYNC.name == 'SYNC'


class TestChamberInterface(TestBase):
    def test_supported_chambers_single(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        assert fryer.supported_chambers == (Ch.CHAMBER_1,)
        assert fryer.is_dual_chamber is False

    def test_supported_chambers_tf101s(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        assert fryer.supported_chambers == (Ch.CHAMBER_1, Ch.CHAMBER_2, Ch.WHOLE, Ch.BOTH)
        assert fryer.is_dual_chamber is True

    def test_supported_chambers_dual_without_whole(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        fryer.features = [f for f in fryer.features if f != 'whole_chamber']
        assert fryer.supported_chambers == (Ch.CHAMBER_1, Ch.CHAMBER_2, Ch.BOTH)

    def test_supported_chambers_dc111s(self):
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        assert fryer.supported_chambers == (Ch.CHAMBER_1, Ch.CHAMBER_2, Ch.BOTH)
        assert fryer.is_dual_chamber is True

    @pytest.mark.parametrize('chamber', [Ch.WHOLE, 3], ids=['enum', 'int'])
    def test_dc111s_rejects_whole_without_request(self, chamber):
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        self.mock_api.reset_mock()
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=195, chamber=chamber) is False
        assert self.run_in_loop(fryer.end, chamber) is False
        assert self.mock_api.call_count == 0

    def test_dc111s_sync_hold_chamber(self):
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        self.mock_api.return_value = (build_bypass_v2_response(inner_result=DC111S_SYNC_HOLD), 200)
        self.caplog.set_level(logging.WARNING)
        self.run_in_loop(fryer.update)
        held = fryer.state_chamber_2
        assert held.cook_status == AirFryerCookStatus.HOLD
        assert 'Unknown cook status' not in self.caplog.text
        assert (held.cook_set_time, held.cook_last_time, held.total_last_time) == (300, 296, 596)
        assert fryer.sync_chambers is True
        assert fryer.work_chamber is Ch.BOTH
        assert held.is_in_cook_mode is True
        assert held.is_cooking is False
        assert held.is_running is False
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOKING

    def test_dc111s_hold_wait_counts_down(self):
        # The hold wait counts down between polls (HAR: 300 -> 296 -> 279).
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        self.mock_api.return_value = (build_bypass_v2_response(inner_result=DC111S_SYNC_HOLD), 200)
        self.run_in_loop(fryer.update)
        held = fryer.state_chamber_2
        assert held.last_timestamp is not None
        held.last_timestamp -= timedelta(seconds=10)
        assert held.cook_time_remaining is not None
        assert held.cook_time_remaining <= 286
        assert held.total_time_remaining is not None
        assert held.total_time_remaining <= 586

    def _poll(self, fryer, inner_result):
        self.mock_api.return_value = (build_bypass_v2_response(inner_result=inner_result), 200)
        self.run_in_loop(fryer.update)

    def test_dc111s_hold_wait_pauses_with_other_chamber(self):
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        self._poll(fryer, DC111S_SYNC_HOLD_PAUSED)
        held = fryer.state_chamber_2
        assert held.cook_status == AirFryerCookStatus.HOLD
        assert held.last_timestamp is None
        assert held.cook_time_remaining == 279
        assert held.total_time_remaining == 579
        assert held.is_in_cook_mode is True
        assert held.is_running is False

    def test_dc111s_hold_wait_follows_other_chamber(self):
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        held = fryer.state_chamber_2
        self._poll(fryer, DC111S_SYNC_HOLD)
        assert held.last_timestamp is not None
        self._poll(fryer, DC111S_SYNC_HOLD_PAUSED)
        assert held.last_timestamp is None
        assert held.cook_time_remaining == 279
        self._poll(fryer, DC111S_SYNC_HOLD)
        assert held.last_timestamp is not None

    @pytest.mark.parametrize(
        ('inner_code', 'name'),
        [
            (11914000, 'BYPASS_SYNC_FINISH_FAIL_1'),
            (11915000, 'BYPASS_SYNC_FINISH_FAIL_2'),
            (11926000, 'BYPASS_AVATAR_SYNC_FAIL'),
        ],
    )
    def test_dc111s_refused_sync_cook_keeps_state(self, inner_code, name):
        # APK DC111S ErrorInfo map (i61.C114379l.z0()): Sync refused codes.
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        self._poll(fryer, deepcopy(AIR_FRYER_COOKING_DETAILS['CAF-DC111S-AEU']))
        self.mock_api.return_value = (build_bypass_v2_response(inner_code=inner_code), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=195, chamber=Ch.BOTH) is False
        assert fryer.last_response is not None
        assert fryer.last_response.name == name
        assert fryer.last_response.code == inner_code
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOKING
        assert fryer.state_chamber_2.cook_status == AirFryerCookStatus.STANDBY
        assert fryer.work_chamber is Ch.CHAMBER_1
        assert fryer.sync_chambers is False

    def test_validate_chamber_accepts_int(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        assert fryer._validate_chamber(2) is Ch.CHAMBER_2

    @pytest.mark.parametrize('bad', [0, 7, -1])
    def test_validate_chamber_rejects_invalid_int(self, bad):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        assert fryer._validate_chamber(bad) is None

    def test_validate_chamber_rejects_unsupported(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        assert fryer._validate_chamber(Ch.CHAMBER_2) is None

    def test_get_chamber_state(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        assert fryer.get_chamber_state(Ch.CHAMBER_2) is fryer.state_chamber_2
        assert fryer.get_chamber_state(Ch.WHOLE) is fryer.state_chamber_1

    @pytest.mark.parametrize(
        ('setup_entry', 'chamber'),
        [('CAF-TF101S', Ch.BOTH), ('CAF-TF101S', 5), ('CS158-AF', Ch.CHAMBER_2)],
    )
    def test_get_chamber_state_returns_none_without_raising(self, setup_entry, chamber):
        fryer = self.get_device('air_fryers', setup_entry)
        self.caplog.set_level(logging.DEBUG)
        assert fryer.get_chamber_state(chamber) is None
        assert 'chamber' in self.caplog.text.lower()

    @pytest.mark.parametrize('setup_entry', ['CS158-AF', 'CAF-DC601S', 'CAF-P583S'])
    @pytest.mark.parametrize('chamber', [Ch.CHAMBER_2, Ch.WHOLE, Ch.BOTH, 5])
    def test_single_chamber_rejects_other_chambers(self, setup_entry, chamber):
        fryer = self.get_device('air_fryers', setup_entry)
        self.mock_api.reset_mock()
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=fryer.min_temp, chamber=chamber) is False
        assert self.run_in_loop(fryer.end, chamber) is False
        assert self.mock_api.call_count == 0

    def _start(self, fryer, chamber):
        self.mock_api.reset_mock()
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        ok = self.run_in_loop(fryer.set_mode, cook_time=1200, cook_temp=200, chamber=chamber)
        return ok, parse_args(self.mock_api)['json_object']['payload']['data'] if ok else None

    def test_both_sends_work_chamber_4_and_two_configs(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        ok, data = self._start(fryer, Ch.BOTH)
        assert ok
        assert (data['workChamber'], data['syncType']) == (4, 2)
        assert [c['chamber'] for c in data['cookConfigs']] == [1, 2]
        assert fryer.sync_chambers is True

    def test_reported_sync_does_not_leak_into_single_chamber_start(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        status = _tf101s_status([_tf101s_chamber(1, 'cooking'), _tf101s_chamber(2, 'cooking')], work_chamber=4, sync_type=2)
        self.mock_api.return_value = (status, 200)
        self.run_in_loop(fryer.update)
        assert fryer.sync_chambers is True
        ok, data = self._start(fryer, Ch.CHAMBER_1)
        assert ok
        assert (data['workChamber'], data['syncType']) == (1, 0)
        assert [c['chamber'] for c in data['cookConfigs']] == [1]

    def test_end_both_sends_chamber_4_and_clears_both(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.end, Ch.BOTH)
        assert parse_args(self.mock_api)['json_object']['payload']['data'] == {'chamber': 4}
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.STANDBY
        assert fryer.state_chamber_2.cook_status == AirFryerCookStatus.STANDBY
        assert fryer.sync_chambers is False

    def test_end_one_chamber_during_sync_logs_and_sends_that_chamber(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        status = _tf101s_status([_tf101s_chamber(1, 'cooking'), _tf101s_chamber(2, 'cooking')], work_chamber=4, sync_type=2)
        self.mock_api.return_value = (status, 200)
        self.run_in_loop(fryer.update)
        self.caplog.set_level(logging.DEBUG)
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.end)
        assert parse_args(self.mock_api)['json_object']['payload']['data'] == {'chamber': 1}
        assert 'pass AirFryerChamber.BOTH to end both' in self.caplog.text

    @pytest.mark.parametrize('chamber', [Ch.WHOLE, 0, 9])
    def test_dual_without_whole_rejects(self, chamber):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        fryer.features = [f for f in fryer.features if f != 'whole_chamber']
        ok, _ = self._start(fryer, chamber)
        assert ok is False
        assert self.run_in_loop(fryer.end, chamber) is False
        assert self.mock_api.call_count == 0

    def test_update_stamps_both_chambers(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (_tf101s_status([_tf101s_chamber(1, 'standby'), _tf101s_chamber(2, 'standby')], work_chamber=0), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state_chamber_2.last_update_ts is not None

    @pytest.mark.parametrize(
        ('reported', 'expected'),
        [(0, None), (1, Ch.CHAMBER_1), (2, Ch.CHAMBER_2), (3, Ch.WHOLE), (4, Ch.BOTH), (9, None)],
    )
    def test_update_reports_work_chamber(self, reported, expected):
        # TF101S captures report workChamber 0 (idle), 1, 2, 3 (whole) and 4 (sync).
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (_tf101s_status([_tf101s_chamber(1, 'cooking')], work_chamber=reported), 200)
        self.run_in_loop(fryer.update)
        assert fryer.work_chamber is expected

    @pytest.mark.parametrize('attr', ['sync_chambers', 'work_chamber'])
    def test_reported_chamber_status_is_read_only(self, attr):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        with pytest.raises(AttributeError):
            setattr(fryer, attr, True)

    def test_reported_status_mirrored_to_both_states(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        status = _tf101s_status([_tf101s_chamber(1, 'cooking'), _tf101s_chamber(2, 'cooking')], work_chamber=4, sync_type=2)
        self.mock_api.return_value = (status, 200)
        self.run_in_loop(fryer.update)
        for st in (fryer.state_chamber_1, fryer.state_chamber_2):
            assert st.work_chamber is Ch.BOTH
            assert st.sync_chambers is True
        assert fryer.work_chamber is Ch.BOTH

    def test_local_start_sets_sync_but_not_work_chamber(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        ok, _ = self._start(fryer, Ch.BOTH)
        assert ok
        assert fryer.sync_chambers is True
        assert fryer.work_chamber is None

    def test_single_chamber_work_chamber_is_none(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        assert fryer.work_chamber is None

    # set_chamber_modes() (CAF-DC111S-AEU)

    def _dc111s(self):
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        fryer.state_chamber_1.set_standby()
        fryer.state_chamber_2.set_standby()
        return fryer

    def _start_data(self):
        return parse_args(self.mock_api)['json_object']['payload']['data']

    def test_sync_sends_separate_recipes(self):
        fryer = self._dc111s()
        first = replace(fryer.get_mode_recipe('AirFry'), target_temp=180, cook_time=180)
        second = replace(fryer.get_mode_recipe('Bake'), target_temp=160, cook_time=300)
        before = deepcopy((first, second))
        assert self.run_in_loop(fryer.set_chamber_modes, first, second)
        data = self._start_data()
        assert data['syncType'] == AirFryerSyncType.SYNC
        assert data['workChamber'] == Ch.BOTH
        assert [
            (c['chamber'], c['mode'], c['cookTemp'], c['cookSetTime'], c['recipeId'], c['recipeType'])
            for c in data['cookConfigs']
        ] == [(1, 'AirFry', 180, 180, 14, 3), (2, 'Bake', 160, 300, 9, 3)]
        assert (first, second) == before

    def test_sync_with_different_times_holds_the_shorter_chamber(self):
        # Same split as DC111S_SYNC_HOLD: the shorter chamber waits for the
        # difference, and both report the longer time as the total.
        fryer = self._dc111s()
        first = replace(fryer.get_mode_recipe('AirFry'), target_temp=180, cook_time=180)
        second = replace(fryer.get_mode_recipe('Bake'), target_temp=160, cook_time=300)
        assert self.run_in_loop(fryer.set_chamber_modes, first, second)
        held, cooking = fryer.state_chamber_1, fryer.state_chamber_2
        assert held.cook_status == AirFryerCookStatus.HOLD
        assert held.cook_set_time == 180
        assert held.cook_set_temp == 180
        assert held.cook_last_time == 120
        assert held.total_last_time == 300
        assert cooking.cook_status == AirFryerCookStatus.COOKING
        assert cooking.cook_set_time == 300
        assert cooking.cook_set_temp == 160
        assert cooking.cook_last_time == 300
        assert cooking.total_last_time == 300
        assert fryer.sync_chambers is True

    def test_sync_with_equal_times_cooks_both_chambers(self):
        fryer = self._dc111s()
        first = replace(fryer.get_mode_recipe('AirFry'), cook_time=300)
        second = replace(fryer.get_mode_recipe('Bake'), cook_time=300)
        assert self.run_in_loop(fryer.set_chamber_modes, first, second)
        for state in (fryer.state_chamber_1, fryer.state_chamber_2):
            assert state.cook_status == AirFryerCookStatus.COOKING
            assert state.total_last_time is None

    def test_sync_converts_each_recipe_to_the_device_unit(self):
        fryer = self._dc111s()
        first = replace(fryer.get_mode_recipe('AirFry'), target_temp=390, temp_unit='f', cook_time=180)
        second = replace(fryer.get_mode_recipe('Bake'), target_temp=160, temp_unit='c', cook_time=300)
        assert self.run_in_loop(fryer.set_chamber_modes, first, second)
        data = self._start_data()
        assert data['tempUnit'] == 'c'
        assert [c['cookTemp'] for c in data['cookConfigs']] == [200, 160]

    def test_match_copies_one_recipe_to_both_chambers(self):
        fryer = self._dc111s()
        source = replace(fryer.get_mode_recipe('Bake'), target_temp=180, cook_time=180)
        assert self.run_in_loop(fryer.set_chamber_modes, source, sync_type=AirFryerSyncType.MATCH)
        data = self._start_data()
        assert data['syncType'] == AirFryerSyncType.MATCH
        assert data['workChamber'] == Ch.BOTH
        one, two = deepcopy(data['cookConfigs'])
        assert (one.pop('chamber'), two.pop('chamber')) == (1, 2)
        assert one == two
        assert one['mode'] == 'Bake'
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOKING
        assert fryer.state_chamber_2.cook_status == AirFryerCookStatus.COOKING
        # sync_chambers means the app's Sync mode only.
        assert fryer.sync_chambers is False

    @pytest.mark.parametrize(
        ('sync_type', 'with_second'),
        [
            (AirFryerSyncType.OFF, True),
            (3, True),
            ('2', True),
            (AirFryerSyncType.SYNC, False),
            (AirFryerSyncType.MATCH, True),
        ],
    )
    def test_invalid_recipe_combination_sends_no_request(self, sync_type, with_second):
        fryer = self._dc111s()
        recipe = fryer.get_mode_recipe('AirFry')
        second = recipe if with_second else None
        assert self.run_in_loop(fryer.set_chamber_modes, recipe, second, sync_type=sync_type) is False
        self.mock_api.assert_not_called()

    @pytest.mark.parametrize(
        'entry',
        [e.setup_entry for e in air_fryer_modules if AirFryerFeatures.CHAMBER_MODES not in e.features],
    )
    def test_chamber_modes_not_configured_sends_no_request(self, entry):
        fryer = self.get_device('air_fryers', entry)
        recipe = fryer.get_mode_recipe()
        assert self.run_in_loop(fryer.set_chamber_modes, recipe, recipe) is False
        self.mock_api.assert_not_called()

    def test_chamber_modes_only_on_dc111s(self):
        with_feature = [
            e.setup_entry for e in air_fryer_modules if AirFryerFeatures.CHAMBER_MODES in e.features
        ]
        assert with_feature == ['CAF-DC111S-AEU']

    def test_invalid_second_recipe_does_not_start_the_first(self):
        fryer = self._dc111s()
        first = fryer.get_mode_recipe('AirFry')
        second = replace(fryer.get_mode_recipe('Dry'), cook_time=60)
        assert self.run_in_loop(fryer.set_chamber_modes, first, second) is False
        self.mock_api.assert_not_called()
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.STANDBY

    def test_refused_sync_keeps_both_chamber_states(self):
        # APK DC111S ErrorInfo map (i61.C114379l.z0()): 11914000 "Sync is unavailable".
        fryer = self._dc111s()
        fryer.state_chamber_1.set_state(
            cook_status=AirFryerCookStatus.COOK_STOP,
            cook_time=180,
            cook_last_time=100,
            cook_temp=180,
        )
        self.mock_api.return_value = (build_bypass_v2_response(inner_code=11914000), 200)
        first = fryer.get_mode_recipe('AirFry')
        second = fryer.get_mode_recipe('Bake')
        assert self.run_in_loop(fryer.set_chamber_modes, first, second) is False
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOK_STOP
        assert fryer.state_chamber_1.cook_set_temp == 180
        assert fryer.state_chamber_2.cook_status == AirFryerCookStatus.STANDBY
