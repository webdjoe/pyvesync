"""Air fryer chamber interface tests (AirFryerChamber, supported chambers)."""

import logging

import pytest
from base_test_cases import TestBase
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
