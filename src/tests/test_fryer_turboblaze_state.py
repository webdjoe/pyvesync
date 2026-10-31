"""State tests for bypassV2 (TurboBlaze class) fryers around preheat.

Covers the local state after starting a program with preheat, and how a
pulled-out basket is classified when the API reports ``preheatSetTime`` as 0.
"""

from copy import deepcopy

import call_json_fryers
from base_test_cases import TestBase
from defaults import build_bypass_v2_response

from pyvesync.const import AirFryerCookStatus

MODEL = 'CAF-DC601S'


class TestTurboBlazePreheatState(TestBase):
    """Preheat state handling for VeSyncTurboBlazeFryer."""

    def _update_with(self, fryer, **overrides):
        details = deepcopy(call_json_fryers.AIR_FRYER_COOKING_DETAILS[MODEL])
        details.update(overrides)
        self.mock_api.return_value = (
            build_bypass_v2_response(inner_result=details),
            200,
        )
        self.run_in_loop(fryer.update)

    def test_set_mode_with_preheat_starts_in_heating(self):
        fryer = self.get_device('air_fryers', MODEL)
        self.mock_api.return_value = (build_bypass_v2_response(inner_result={}), 200)

        result = self.run_in_loop(
            fryer.set_mode, cook_time=600, cook_temp=350, preheat_time=300
        )

        assert result is True
        assert fryer.state.cook_status == AirFryerCookStatus.HEATING
        assert fryer.state.is_in_preheat_mode is True
        assert fryer.state.preheat_set_time == 300
        assert fryer.state.cook_set_time == 600
        assert fryer.state.cook_set_temp == 350

    def test_set_mode_without_preheat_starts_in_cooking(self):
        fryer = self.get_device('air_fryers', MODEL)
        self.mock_api.return_value = (build_bypass_v2_response(inner_result={}), 200)

        result = self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=350)

        assert result is True
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING
        assert fryer.state.is_in_preheat_mode is False
        assert fryer.state.preheat_set_time is None

    def test_pull_out_during_cook_is_cook_mode(self):
        """preheatSetTime 0 from the API means the program has no preheat."""
        fryer = self.get_device('air_fryers', MODEL)
        self._update_with(
            fryer, cookStatus='pullOut', preheatSetTime=0, preheatLastTime=0
        )

        assert fryer.state.cook_status == AirFryerCookStatus.PULL_OUT
        assert fryer.state.preheat_set_time is None
        assert fryer.state.is_in_preheat_mode is False
        assert fryer.state.is_in_cook_mode is True

    def test_pull_out_during_preheat_is_preheat_mode(self):
        fryer = self.get_device('air_fryers', MODEL)
        self._update_with(
            fryer, cookStatus='pullOut', preheatSetTime=300, preheatLastTime=120
        )

        assert fryer.state.cook_status == AirFryerCookStatus.PULL_OUT
        assert fryer.state.preheat_set_time == 300
        assert fryer.state.preheat_last_time == 120
        assert fryer.state.is_in_preheat_mode is True
        assert fryer.state.is_in_cook_mode is False
