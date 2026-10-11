"""Tests for continuing from preheat into cooking on bypassV2 fryers.

`VeSyncTurboBlazeFryer.cook_from_preheat` sends `preheatCook`, which was
confirmed on a physical CS358-AF: once preheat has finished the unit keeps the
queued cook step and waits, and `preheatCook` starts that step.
"""

from copy import deepcopy

import call_json_fryers
from base_test_cases import TestBase
from defaults import build_bypass_v2_response
from utils import parse_args

from pyvesync.const import AirFryerCookStatus, AirFryerFeatures, TemperatureUnits

BYPASS_V2_URL = '/cloud/v2/deviceManaged/bypassV2'


class TestFryerCookFromPreheat(TestBase):
    """Request and state tests for cook_from_preheat on bypassV2 fryers."""

    def _preheated_fryer(self):
        fryer = self.get_device('air_fryers', 'CS358-AF')
        self.mock_api.return_value = (call_json_fryers.CS358_PREHEAT_END_RESPONSE, 200)
        self.run_in_loop(fryer.update)
        return fryer

    def test_update_reports_preheat_end_with_cook_step(self):
        fryer = self._preheated_fryer()
        defaults = call_json_fryers.AirFryerDefaults
        assert fryer.state.cook_status == AirFryerCookStatus.PREHEAT_END
        assert fryer.state.cook_set_temp == defaults.cook_temp_f
        assert fryer.state.cook_set_time == defaults.cook_time_s
        assert fryer.state.cook_mode == 'Custom'

    def test_cook_from_preheat_sends_preheat_cook(self):
        fryer = self._preheated_fryer()
        self.mock_api.reset_mock()
        self.mock_api.return_value = (build_bypass_v2_response(inner_result={}), 200)

        assert self.run_in_loop(fryer.cook_from_preheat) is True

        assert self.mock_api.call_count == 1
        kwargs = parse_args(self.mock_api)
        assert kwargs['url'] == BYPASS_V2_URL
        payload = kwargs['json_object']['payload']
        assert payload['method'] == 'preheatCook'
        assert payload['data'] == {}
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING

    def test_cook_from_preheat_requires_preheat_end(self):
        fryer = self.get_device('air_fryers', 'CS358-AF')
        self.mock_api.return_value = (
            call_json_fryers.DETAILS_RESPONSES_COOKING['CS358-AF'],
            200,
        )
        self.run_in_loop(fryer.update)
        self.mock_api.reset_mock()

        assert self.run_in_loop(fryer.cook_from_preheat) is False
        assert self.mock_api.call_count == 0

    def test_cook_from_preheat_requires_preheat_feature(self):
        """The Dual Blaze shares the class but has no preheat function."""
        fryer = self.get_device('air_fryers', 'CAF-P583S')
        assert AirFryerFeatures.PREHEAT not in fryer.features
        # Force the status so only the feature check can stop the call.
        fryer.state.cook_status = AirFryerCookStatus.PREHEAT_END
        self.mock_api.reset_mock()

        assert self.run_in_loop(fryer.cook_from_preheat) is False
        assert self.mock_api.call_count == 0

    def test_cook_from_preheat_failure_leaves_state(self):
        fryer = self._preheated_fryer()
        self.mock_api.reset_mock()
        self.mock_api.return_value = (None, 200)

        assert self.run_in_loop(fryer.cook_from_preheat) is False
        assert fryer.state.cook_status == AirFryerCookStatus.PREHEAT_END


class TestCS358TemperatureRange(TestBase):
    """The declared range must be settable at both ends in both units."""

    def test_range_ends_are_settable(self):
        fryer = self.get_device('air_fryers', 'CS358-AF')
        for unit in (TemperatureUnits.FAHRENHEIT, TemperatureUnits.CELSIUS):
            fryer.temp_unit = unit
            assert fryer.prepare_temperature(fryer.min_temp) == fryer.min_temp
            assert fryer.prepare_temperature(fryer.max_temp) == fryer.max_temp


class TestCS358Statuses(TestBase):
    """Every status the physical unit reported maps to a library status."""

    def test_reported_statuses_are_mapped(self):
        fryer = self.get_device('air_fryers', 'CS358-AF')
        expected = {
            'ready': AirFryerCookStatus.COOK_STOP,
            'heating': AirFryerCookStatus.HEATING,
            'preheatStop': AirFryerCookStatus.PREHEAT_STOP,
            'preheatEnd': AirFryerCookStatus.PREHEAT_END,
            'cooking': AirFryerCookStatus.COOKING,
            'cookStop': AirFryerCookStatus.COOK_STOP,
            'cookEnd': AirFryerCookStatus.COOK_END,
            'pullOut': AirFryerCookStatus.PULL_OUT,
            'keeping': AirFryerCookStatus.COOKING,
        }
        for reported, status in expected.items():
            details = deepcopy(call_json_fryers.CS358_PREHEAT_END_DETAILS)
            details['cookStatus'] = reported
            self.mock_api.return_value = (
                build_bypass_v2_response(inner_result=details),
                200,
            )
            self.run_in_loop(fryer.update)
            assert fryer.state.cook_status == status, reported
