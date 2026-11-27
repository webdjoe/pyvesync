"""Air fryer request and state tests pinned to packet capture values.

Each test uses request/response shapes from the air fryer packet captures
(CS137/CS158, CAF-DC601S, CAF-P583S-KUS and CAF-TF101S) to verify the
library sends the captured request and parses the captured response.
"""

from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import call_json_fryers
import pytest
from base_test_cases import TestBase
from defaults import (
    TestDefaults,
    build_base_response,
    build_bypass_v1_response,
    build_bypass_v2_response,
)
from utils import parse_args

from pyvesync.base_devices.fryer_base import VeSyncFryer
from pyvesync.const import (
    AirFryerCookModes,
    AirFryerCookStatus,
    AirFryerFeatures,
    AirFryerPresets,
    TemperatureUnits,
)
from pyvesync.const import AirFryerChamber as Ch
from pyvesync.device_map import air_fryer_modules


def _158_status(**temp: int) -> dict:
    """Build a 158 cooking status response with the given temperature keys."""
    return build_bypass_v1_response(
        result_dict={
            'returnStatus': {
                'cookSetTemp': 350,
                'mode': 'custom',
                'cookSetTime': 15,
                'cookLastTime': 15,
                'cookStatus': 'cooking',
                'tempUnit': 'fahrenheit',
                **temp,
            }
        }
    )


P583_COOK_END_RESULT = {
    'stepArray': [
        {
            'cookSetTime': 60,
            'cookTemp': 400,
            'mode': 'Broil',
            'cookLastTime': 0,
            'shakeTime': 0,
            'cookEndTime': 1747848005,
            'recipeName': 'Broil',
            'recipeId': 17,
            'recipeType': 3,
        }
    ],
    'stepIndex': 0,
    'cookMode': 'normal',
    'cookStatus': 'cookEnd',
    'tempUnit': 'f',
    'preheatSetTime': 0,
    'preheatLastTime': 0,
    'preheatEndTime': 0,
    'preheatTemp': 0,
    'startTime': 1747847911,
    'totalTimeRemaining': 0,
    'currentTemp': 80,
    'appointLastTime': 0,
    'shakeStatus': 0,
    'linkageStatus': 0,
}


def _dc601s_status(
    cook_status: str,
    *,
    cook_last_time: int = 1200,
    preheat: tuple[int, int, int] = (0, 0, 0),
    step_index: int = 0,
) -> dict:
    """Build a DC601S getAirfryerStatus response (Bake 330 F, 1200 s capture)."""
    preheat_set, preheat_last, preheat_temp = preheat
    return build_bypass_v2_response(
        inner_result={
            'stepArray': [
                {
                    'cookSetTime': 1200,
                    'cookTemp': 330,
                    'mode': 'Bake',
                    'cookLastTime': cook_last_time,
                    'shakeTime': 0,
                    'cookEndTime': 0,
                    'recipeName': 'Bake',
                    'recipeId': 9,
                    'recipeType': 3,
                }
            ],
            'cookMode': 'normal',
            'tempUnit': 'f',
            'stepIndex': step_index,
            'cookStatus': cook_status,
            'preheatSetTime': preheat_set,
            'preheatLastTime': preheat_last,
            'preheatEndTime': 0,
            'preheatTemp': preheat_temp,
            'startTime': 1767318116,
            'totalTimeRemaining': preheat_last + cook_last_time,
            'currentTemp': 112,
            'shakeStatus': 0,
        }
    )


# CS358 command acknowledgement (Air Fryer CS358.har entry 95 and every other
# command): no result.result.
CS358_COMMAND_RESPONSE = build_base_response(
    merge_dict={'result': {'traceId': TestDefaults.trace_id, 'code': 0}}
)

CS358_MODES = [  # Air Fryer CS358.har entries 977-1102, each at 60 s / 170 F
    (AirFryerCookModes.STEAK, 'Steak', 1, 'Steak'),
    (AirFryerCookModes.CHICKEN, 'Chicken', 2, 'Chicken'),
    (AirFryerCookModes.SEAFOOD, 'Seafood', 3, 'Seafood'),
    (AirFryerCookModes.BACON, 'Bacon', 4, 'Bacon'),
    (AirFryerCookModes.FROZEN, 'Frozen', 5, 'Frozen'),
    (AirFryerCookModes.FRENCH_FRIES, 'French fries', 6, 'French Fries'),
    (AirFryerCookModes.VEGETABLES, 'Vegetables', 7, 'Vegetables'),
    (AirFryerCookModes.SHRIMP, 'Shrimp', 8, 'Shrimp'),
    (AirFryerCookModes.BAKE, 'Bake', 9, 'Bake'),
    (AirFryerCookModes.TOAST, 'Toast', 10, 'Toast'),
    (AirFryerCookModes.CUSTOM, 'Custom', 11, 'Manual'),
]


def _cs358_status(
    cook_status: str,
    *,
    step: dict | None = None,
    steps: list[dict] | None = None,
    step_index: int = 0,
    preheat: tuple[int, int, int] = (0, 0, 0),
    total: int = 900,
    cook_mode: str = 'normal',
    temp_unit: str = 'f',
) -> dict:
    """Build a CS358 getAirfryerStatus response (Air Fryer CS358.har entry 134).

    The defaults are that entry's Manual 350 F, 900 s cook. ``step`` overrides
    keys of the default step; ``steps`` replaces the whole ``stepArray``.
    ``preheat`` is (preheatSetTime, preheatLastTime, preheatTemp). startTime,
    preheatEndTime and cookEndTime, which the parser ignores, keep entry
    134's values for every status.
    """
    preheat_set, preheat_last, preheat_temp = preheat
    default_step = {
        'cookSetTime': 900,
        'cookTemp': 350,
        'mode': 'Custom',
        'cookLastTime': 900,
        'shakeTime': 0,
        'cookEndTime': 0,
        'recipeName': 'Manual',
        'recipeId': 11,
        'recipeType': 3,
    }
    return build_bypass_v2_response(
        inner_result={
            'stepArray': steps if steps is not None else [default_step | (step or {})],
            'stepIndex': step_index,
            'cookMode': cook_mode,
            'cookStatus': cook_status,
            'tempUnit': temp_unit,
            'preheatSetTime': preheat_set,
            'preheatLastTime': preheat_last,
            'preheatEndTime': 0,
            'preheatTemp': preheat_temp,
            'startTime': 1794066380,
            'totalTimeRemaining': total,
            'currentTemp': 0,
            'appointLastTime': 0,
            'shakeStatus': 0,
        }
    )


def _tf101s_chamber(chamber: int, cook_status: str, total: int | None = None) -> dict:
    """Build one TF101S statusList item (AirFry 200 C, 1200 s capture)."""
    active = cook_status != 'standby'
    remaining = 1140 if active else 0
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
        'currentRemainingTime': remaining,
        'totalTimeRemaining': remaining if total is None else total,
        'chamber': chamber,
    }


def _tf101s_status(status_list: list[dict], work_chamber: int) -> dict:
    """Build a TF101S getAirfryerMultiStatus response."""
    return build_bypass_v2_response(
        inner_result={
            'statusList': status_list,
            'tempUnit': 'c',
            'syncType': 0,
            'workChamber': work_chamber,
        }
    )


# CS158 getStatus returnStatus captures (accountId removed).
CS158_PREHEAT_STOP = {  # 2025 Captures/GetHome.har, 2022-07-23 19:27:28
    'curentTemp': 108, 'mode': 'custom', 'preheatLastTime': 5, 'preheatSetTime': 5,
    'cookStatus': 'preheatStop', 'targetTemp': 400, 'tempUnit': 'fahrenheit',
    'customRecipe': 'Manual',
}
CS158_PREHEAT_END = {  # same file, 2022-07-23 19:31:11
    'curentTemp': 401, 'mode': 'custom', 'preheatLastTime': 0, 'preheatSetTime': 5,
    'cookStatus': 'preheatEnd', 'targetTemp': 400, 'tempUnit': 'fahrenheit',
    'customRecipe': 'Manual', 'recipeId': 1, 'recipeType': 3,
}
CS158_PULLOUT_PREHEAT = {  # Air Fryer.chls.har, 2022-11-16 20:32:46
    'curentTemp': 253, 'mode': 'custom', 'preheatLastTime': 3, 'preheatSetTime': 4,
    'cookStatus': 'pullOut', 'targetTemp': 350, 'tempUnit': 'fahrenheit',
    'customRecipe': 'Manual',
}
CS158_PULLOUT_COOK = {  # same file, 2022-11-16 20:35:09
    'curentTemp': 361, 'cookSetTemp': 350, 'mode': 'custom', 'cookSetTime': 15,
    'cookLastTime': 15, 'cookStatus': 'pullOut', 'tempUnit': 'fahrenheit',
    'customRecipe': 'Manual',
}
CS158_PULLOUT_BARE = {'cookStatus': 'pullOut'}  # Air Fryer - Tablet.chls.har, 2025-03-22
CS158_APPOINTING = {  # Air Fryer.chls.har, 2022-11-16 20:37:28
    'cookSetTemp': 350, 'mode': 'custom', 'cookSetTime': 15, 'cookStatus': 'appointing',
    'tempUnit': 'fahrenheit', 'appointLastTime': 60, 'customRecipe': 'Manual',
}
CS168_COOK_END = {  # CS168-AF (API deviceType CS137-AF/CS158-AF), 2026-11-20 16:33:37
    'cookSetTemp': 350, 'mode': 'manual', 'cookSetTime': 4, 'cookLastTime': 0,
    'cookStatus': 'cookEnd', 'tempUnit': 'fahrenheit', 'recipeId': 15, 'recipeType': 3,
}

def _158_return_status(return_status: dict) -> dict:
    """Wrap a captured CS158 returnStatus in a bypassV1 response."""
    return build_bypass_v1_response(result_dict={'returnStatus': deepcopy(return_status)})


class TestFryerCaptures(TestBase):
    """Air fryer behavior checked against captured API traffic."""

    def test_158_reads_misspelled_temp_key(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (_158_status(curentTemp=108), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.current_temp == 108

    def test_158_reads_corrected_temp_key(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (_158_status(currentTemp=108), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.current_temp == 108

    def test_158_prefers_corrected_temp_key(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (
            _158_status(currentTemp=110, curentTemp=108),
            200,
        )
        self.run_in_loop(fryer.update)
        assert fryer.state.current_temp == 110

    def test_158_set_mode_matches_capture(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (build_bypass_v1_response(result_dict={}), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=900, cook_temp=350) is True
        body = parse_args(self.mock_api)['json_object']
        assert body['jsonCmd'] == {
            'cookMode': {
                'accountId': self.manager.account_id,
                'appointmentTs': 0,
                'cookSetTemp': 350,
                'cookSetTime': 15,
                'cookStatus': 'cooking',
                'customRecipe': 'Manual Cooking',
                'mode': 'custom',
                # Air Fryer.chls.har entry 205: readyStart false reports cooking at once.
                'readyStart': False,
                'recipeId': 1,
                'recipeType': 3,
                'tempUnit': 'fahrenheit',
            }
        }

    def test_tf101s_celsius_step_is_5(self):
        # TF101S preset menu temps (55/160/165/190/200/240 C) are all on a 5 C step.
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        assert fryer.temperature_step == 5
        assert fryer.round_temperature(163) == 165

    def test_tf101s_grill_allows_240c(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=240, cook_mode='Grill')
        assert self._sent_body()['payload']['data']['cookConfigs'][0]['cookTemp'] == 240

    def test_tf101s_airfry_rejects_240c(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.reset_mock()
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=240, cook_mode='AirFry') is False
        assert self.mock_api.call_count == 0

    def test_p583_bake_recipe_below_mode_min_rejected(self):
        # P583S Bake is 250-400 F; AirFry allows 175.
        fryer = self.get_device('air_fryers', 'CAF-P583S')
        self.mock_api.reset_mock()
        recipe = replace(AirFryerPresets.bake, target_temp=200)
        assert self.run_in_loop(fryer.set_mode_from_recipe, recipe) is False
        assert self.mock_api.call_count == 0

    def test_158_steak_mode_matches_capture(self):
        # CS158 cookMode captures: mode steak, recipeId 2, customRecipe "Steak".
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (build_bypass_v1_response(result_dict={}), 200)
        assert self.run_in_loop(
            fryer.set_mode, cook_time=360, cook_temp=400, cook_mode='steak'
        )
        cook = self._sent_body()['jsonCmd']['cookMode']
        assert (cook['mode'], cook['recipeId'], cook['customRecipe'], cook['recipeType']) == (
            'steak', 2, 'Steak', 3,
        )

    def test_158_chicken_key_sends_poultry(self):
        # CS158 cookMode captures: mode poultry, recipeId 3, customRecipe "Chicken".
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (build_bypass_v1_response(result_dict={}), 200)
        assert self.run_in_loop(
            fryer.set_mode, cook_time=1500, cook_temp=380, cook_mode=AirFryerCookModes.CHICKEN
        )
        cook = self._sent_body()['jsonCmd']['cookMode']
        assert (cook['mode'], cook['recipeId'], cook['customRecipe']) == ('poultry', 3, 'Chicken')

    def test_dc601s_bake_mode_matches_capture(self):
        # DC601S Bake capture: mode Bake, recipeId 9, recipeName "Bake", 330 F.
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(
            fryer.set_mode, cook_time=1200, cook_temp=330, cook_mode='Bake'
        )
        data = self._sent_body()['payload']['data']
        assert (data['mode'], data['recipeId'], data['recipeName'], data['recipeType']) == (
            'Bake', 9, 'Bake', 3,
        )
        assert data['startAct']['cookTemp'] == 330

    def test_p583_broil_mode_matches_capture(self):
        # P583S-KUS Broil capture: mode Broil, recipeId 17, recipeName "Broil".
        fryer = self.get_device('air_fryers', 'CAF-P583S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(
            fryer.set_mode, cook_time=600, cook_temp=400, cook_mode=AirFryerCookModes.BROIL
        )
        data = self._sent_body()['payload']['data']
        assert (data['mode'], data['recipeId'], data['recipeName']) == ('Broil', 17, 'Broil')

    @pytest.mark.parametrize(
        ('chamber', 'work_chamber', 'sync_type', 'config_chambers'),
        [(Ch.WHOLE, 3, 0, [3]), (Ch.BOTH, 4, 2, [1, 2])],
    )
    def test_tf101s_request_matches_app_capture(self, chamber, work_chamber, sync_type, config_chambers):
        # AirFryer TF101SEU 2 HAR.har entry 0 (workChamber 3) and AirFryer
        # TF101SEU HAR.har entry 24 (workChamber 4), app 5.7.50. recipeName
        # follows the phone's language in the app.
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=1200, cook_temp=200, cook_mode='AirFry', chamber=chamber)
        data = self._sent_body()['payload']['data']
        assert (data['workChamber'], data['syncType'], data['tempUnit']) == (work_chamber, sync_type, 'c')
        assert data['cookConfigs'] == [
            {
                'chamber': config_chamber,
                'cookSetTime': 1200,
                'cookTemp': 200,
                'mode': 'AirFry',
                'recipeId': 14,
                'recipeName': 'Air Fry',
                'recipeType': 3,
            }
            for config_chamber in config_chambers
        ]

    def test_dc111s_cook_config_matches_capture(self):
        # CAF-DC111S-AEU_complete_captures.json, startMultiCook_chamber_1. That
        # file is pyvesync traffic, so it shows the fryer accepted this config
        # (code 0), not what the app sends. APK DualZoneCookSetVM.s1 sends it too.
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=300, cook_temp=180, cook_mode='AirFry')
        assert self._sent_body()['payload']['data']['cookConfigs'] == [
            {
                'chamber': 1,
                'cookSetTime': 300,
                'cookTemp': 180,
                'mode': 'AirFry',
                'recipeId': 14,
                'recipeName': 'Air Fry',
                'recipeType': 3,
                'shakeTime': 0,
            }
        ]

    def test_tf101s_grill_sends_grill_recipe(self):
        # Structure: TF101S startMultiCook capture; values: APK i61.C67928f0.
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=240, cook_mode='Grill')
        config = self._sent_body()['payload']['data']['cookConfigs'][0]
        assert (config['mode'], config['recipeId'], config['recipeName']) == ('Grill', 20, 'Grill')

    def test_unknown_cook_mode_sends_nothing(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.reset_mock()
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=200, cook_mode='Proof') is False
        assert self.mock_api.call_count == 0

    def test_default_mode_request_unchanged(self):
        # Passing the default mode sends exactly what no cook_mode sends.
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (build_bypass_v1_response(result_dict={}), 200)
        self.run_in_loop(fryer.set_mode, cook_time=900, cook_temp=350)
        plain = self._sent_body()
        self.run_in_loop(fryer.set_mode, cook_time=900, cook_temp=350, cook_mode='custom')
        assert self._sent_body() == plain

    def test_cook_stop_poll_keeps_temp_and_mode(self):
        # DC601S captures report cookStop with the step's cookTemp and mode.
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (_dc601s_status('cookStop', cook_last_time=900), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.cook_status == AirFryerCookStatus.COOK_STOP
        assert fryer.state.cook_set_temp == 330
        assert fryer.state.cook_mode == 'Bake'
        assert fryer.state.cook_time_remaining == 900

    @pytest.mark.parametrize(
        ('status', 'expected'),
        [
            (CS158_PREHEAT_STOP, AirFryerCookStatus.PREHEAT_STOP),
            (CS158_PREHEAT_END, AirFryerCookStatus.PREHEAT_END),
            (CS158_PULLOUT_PREHEAT, AirFryerCookStatus.PULL_OUT),
            (CS158_PULLOUT_COOK, AirFryerCookStatus.PULL_OUT),
            (CS158_PULLOUT_BARE, AirFryerCookStatus.PULL_OUT),
        ],
    )
    def test_158_captured_status_is_mapped(self, status, expected):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (_158_return_status(status), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.cook_status == expected
        assert 'Unknown cook status' not in self.caplog.text

    def test_158_poll_after_preheat_end_allows_cook(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (_158_return_status(CS158_PREHEAT_END), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.cook_set_temp == 400
        self.mock_api.return_value = (build_bypass_v1_response(result_dict={}), 200)
        assert self.run_in_loop(fryer.cook_from_preheat) is True
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING

    def test_158_poll_after_preheat_stop_allows_resume(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (_158_return_status(CS158_PREHEAT_STOP), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.can_resume is True
        assert fryer.state.preheat_time_remaining == 300
        assert fryer.state.cook_set_temp == 400
        self.mock_api.return_value = (build_bypass_v1_response(result_dict={}), 200)
        assert self.run_in_loop(fryer.resume) is True
        assert self._sent_body()['jsonCmd']['preheat'] == {'preheatStatus': 'heating'}

    def test_158_pullout_during_preheat_is_preheat_mode(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (_158_return_status(CS158_PULLOUT_PREHEAT), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.is_in_preheat_mode is True
        assert fryer.state.preheat_time_remaining == 180
        assert fryer.state.cook_set_temp == 350

    def test_158_pullout_during_cook_is_cook_mode(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (_158_return_status(CS158_PULLOUT_COOK), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.is_in_cook_mode is True
        assert fryer.state.cook_time_remaining == 900

    def test_158_bare_pullout_keeps_previous_cook_values(self):
        # The 2025 tablet capture reports only cookStatus. set_state keeps the
        # values it is not given, and clears preheat outside preheat statuses.
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (_158_return_status(CS158_PULLOUT_COOK), 200)
        self.run_in_loop(fryer.update)
        self.mock_api.return_value = (_158_return_status(CS158_PULLOUT_BARE), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.cook_status == AirFryerCookStatus.PULL_OUT
        assert fryer.state.cook_time_remaining == 900
        assert fryer.state.cook_set_temp == 350

    def test_158_appointing_shows_scheduled_cook(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (_158_return_status(CS158_APPOINTING), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.cook_status == AirFryerCookStatus.APPOINTING
        assert fryer.state.cook_set_temp == 350
        assert fryer.state.cook_set_time == 900
        assert fryer.state.is_running is False
        assert fryer.state.can_resume is False
        assert 'Unknown cook status' not in self.caplog.text

    def test_158_cook_end_is_mapped(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (_158_return_status(CS168_COOK_END), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.cook_status == AirFryerCookStatus.COOK_END
        assert 'Unknown cook status' not in self.caplog.text

    def test_total_time_ready_with_preheat_uses_reported_total(self):
        # DC601S capture 2026-01-01 20:38:51: ready (readyStart true), preheat 240/240,
        # step 720/720, totalTimeRemaining 960. Same relationship with the Bake step here.
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (_dc601s_status('ready', preheat=(240, 240, 330)), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.cook_time_remaining == 1200
        assert fryer.state.total_time_remaining == 240 + 1200

    def test_total_time_while_heating_counts_down(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (_dc601s_status('heating', preheat=(240, 230, 425)), 200)
        self.run_in_loop(fryer.update)
        fryer.state.last_timestamp -= timedelta(seconds=10)
        assert abs(fryer.state.total_time_remaining - (230 + 1200 - 10)) <= 1

    def test_total_time_frozen_in_pullout(self):
        # DC601S capture 2026-01-01 20:43:47: pullOut, total 1152 on two polls 15 s apart.
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (_dc601s_status('pullOut', cook_last_time=1152), 200)
        self.run_in_loop(fryer.update)
        fryer.state.last_timestamp = datetime.now(UTC) - timedelta(seconds=60)
        assert fryer.state.total_time_remaining == 1152

    def test_total_time_from_cook_stop_poll(self):
        # DC601S capture 2026-01-01 20:44:32: cookStop, total 1143.
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (_dc601s_status('cookStop', cook_last_time=1143), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.total_time_remaining == 1143

    def test_local_start_drops_stale_reported_total(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (_dc601s_status('cooking', cook_last_time=1186), 200)
        self.run_in_loop(fryer.update)
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=400) is True
        assert fryer.state.total_last_time is None
        assert abs(fryer.state.total_time_remaining - 600) <= 1

    def test_dual_total_per_chamber(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        status = _tf101s_status(
            [_tf101s_chamber(1, 'cooking'), _tf101s_chamber(2, 'cookStop', total=900)],
            work_chamber=4,
        )
        self.mock_api.return_value = (status, 200)
        self.run_in_loop(fryer.update)
        assert abs(fryer.state_chamber_1.total_time_remaining - 1140) <= 1
        assert fryer.state_chamber_2.total_time_remaining == 900

    def test_total_time_158_cooking_is_computed(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (_158_return_status(CS158_PULLOUT_COOK), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.total_last_time is None
        assert fryer.state.total_time_remaining == 900

    def test_total_time_158_none_while_preheat_paused(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (_158_return_status(CS158_PREHEAT_STOP), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.total_time_remaining is None

    def test_total_time_none_in_standby(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        assert fryer.state.total_time_remaining is None

    def test_dc601s_out_of_range_step_index(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (_dc601s_status('cooking', step_index=3), 200)
        self.run_in_loop(fryer.update)  # must not raise IndexError
        # An unreadable poll keeps the last state (None on a fresh device).
        assert fryer.state.cook_status is None
        assert 'stepIndex 3 out of range' in self.caplog.text

    def test_dc601s_failed_start_keeps_state(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (_dc601s_status('cooking'), 200)
        self.run_in_loop(fryer.update)
        self.mock_api.return_value = (build_bypass_v2_response(inner_code=11000000), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=400) is False
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING

    def test_p583_standby_updates_unit(self):
        # P583S-KUS standby capture 2025-05-21 carries tempUnit with an empty stepArray.
        fryer = self.get_device('air_fryers', 'CAF-P583S')
        standby = deepcopy(call_json_fryers.AIR_FRYER_STANDBY_DETAILS['CAF-P583S'])
        standby['tempUnit'] = 'c'
        self.mock_api.return_value = (build_bypass_v2_response(inner_result=standby), 200)
        self.run_in_loop(fryer.update)
        assert fryer.temp_unit == TemperatureUnits.CELSIUS
        assert fryer.state.cook_status == AirFryerCookStatus.STANDBY

    def test_dc601s_poll_reports_recipe_name(self):
        # DC601S Bake capture: stepArray[0].recipeName 'Bake'.
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (_dc601s_status('cooking'), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.recipe == 'Bake'

    def test_p583_cook_end_reports_recipe_name(self):
        fryer = self.get_device('air_fryers', 'CAF-P583S')
        self.mock_api.return_value = (build_bypass_v2_response(inner_result=deepcopy(P583_COOK_END_RESULT)), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.recipe == 'Broil'

    def test_turboblaze_empty_recipe_name_is_not_stored(self):
        fryer = self.get_device('air_fryers', 'CAF-P583S')
        result = deepcopy(P583_COOK_END_RESULT)
        result['stepArray'][0]['recipeName'] = ''
        self.mock_api.return_value = (build_bypass_v2_response(inner_result=result), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.recipe is None

    def _sent_body(self) -> dict:
        return parse_args(self.mock_api)['json_object']

    def test_158_recipe_seconds_converted(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (build_bypass_v1_response(result_dict={}), 200)
        assert self.run_in_loop(fryer.set_mode_from_recipe, AirFryerPresets.custom)
        assert self._sent_body()['jsonCmd']['cookMode']['cookSetTime'] == 10
        assert fryer.state.cook_set_time == 600

    def test_158_preheat_request_times(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (build_bypass_v1_response(result_dict={}), 200)
        recipe = replace(AirFryerPresets.custom, cook_time=600, preheat_time=300)
        assert self.run_in_loop(fryer.set_mode_from_recipe, recipe)
        preheat = self._sent_body()['jsonCmd']['preheat']
        assert preheat['cookSetTime'] == 10
        assert preheat['preheatSetTime'] == 5
        # Air Fryer.chls.har entry 316: readyStart false reports heating at once.
        assert preheat['readyStart'] is False
        assert fryer.state.preheat_set_time == 300
        assert fryer.state.cook_status == AirFryerCookStatus.HEATING

    def test_158_sub_minute_truncates(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self.mock_api.return_value = (build_bypass_v1_response(result_dict={}), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=90, cook_temp=350)
        assert self._sent_body()['jsonCmd']['cookMode']['cookSetTime'] == 1
        assert fryer.state.cook_set_time == 60

    def test_turboblaze_set_mode_seconds(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=1200, cook_temp=330)
        assert self._sent_body()['payload']['data']['startAct']['cookSetTime'] == 1200

    def test_p583_rejects_preset_above_max(self):
        # Broil preset is 450 F; the P583 preset menu and range top out at 400 F.
        fryer = self.get_device('air_fryers', 'CAF-P583S')
        self.mock_api.reset_mock()
        assert self.run_in_loop(fryer.set_mode_from_recipe, AirFryerPresets.broil) is False
        assert self.mock_api.call_count == 0

    def test_tf101s_converts_fahrenheit_recipe(self):
        # 400 F is 204.4 C, which rounds to 205 C on the 5 C step.
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.set_mode_from_recipe, AirFryerPresets.air_fry)
        configs = self._sent_body()['payload']['data']['cookConfigs']
        assert configs[0]['cookTemp'] == 205

    def test_ready_status_not_resumable(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (_dc601s_status('ready'), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.cook_status == AirFryerCookStatus.READY
        assert fryer.state.can_resume is False
        assert fryer.state.cook_time_remaining == 1200

    def test_tf101s_start_sets_cooking(self):
        # No TF101S capture with readyStart false; cooking is inferred from CS158.
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(
            fryer.set_mode, cook_time=1200, cook_temp=200, chamber=3
        )
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOKING

    def test_tf101s_whole_chamber_clears_chamber_2(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        fryer.state_chamber_2.set_state(
            cook_status=AirFryerCookStatus.COOKING, cook_time=600, cook_temp=180
        )
        self.mock_api.return_value = (
            _tf101s_status([_tf101s_chamber(3, 'cooking')], work_chamber=3),
            200,
        )
        self.run_in_loop(fryer.update)
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOKING
        assert fryer.state_chamber_2.cook_status == AirFryerCookStatus.STANDBY

    def test_tf101s_standby_after_whole_chamber(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (
            _tf101s_status([_tf101s_chamber(3, 'cooking')], work_chamber=3),
            200,
        )
        self.run_in_loop(fryer.update)
        self.mock_api.return_value = (
            _tf101s_status(
                [_tf101s_chamber(1, 'standby'), _tf101s_chamber(2, 'standby')],
                work_chamber=0,
            ),
            200,
        )
        self.run_in_loop(fryer.update)
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.STANDBY
        assert fryer.state_chamber_2.cook_status == AirFryerCookStatus.STANDBY

    def test_pullout_plain_cook_is_cook_mode(self):
        # DC601S capture 2026-01-01 20:43:47: basket pulled during a Bake cook.
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (_dc601s_status('pullOut', cook_last_time=1152), 200)
        self.run_in_loop(fryer.update)
        assert fryer.state.is_in_cook_mode is True
        assert fryer.state.is_in_preheat_mode is False
        assert fryer.state.cook_time_remaining == 1152

    def test_pullout_during_preheat_is_preheat_mode(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (
            _dc601s_status('pullOut', preheat=(240, 230, 425)),
            200,
        )
        self.run_in_loop(fryer.update)
        assert fryer.state.is_in_preheat_mode is True
        assert fryer.state.preheat_time_remaining == 230

    def test_pullout_after_preheat_done_is_cook_mode(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (
            _dc601s_status('pullOut', cook_last_time=1152, preheat=(240, 0, 425)),
            200,
        )
        self.run_in_loop(fryer.update)
        assert fryer.state.is_in_cook_mode is True
        assert fryer.state.is_in_preheat_mode is False

    def test_tf101s_end_payload(self):
        # TF101S endCook capture 2026-01-17 (whole chamber).
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.end, chamber=3)
        assert self._sent_body()['payload'] == {
            'data': {'chamber': 3},
            'method': 'endCook',
            'source': 'APP',
            'subDeviceNo': 0,
            'subDeviceType': '',
        }

    def test_tf101s_start_payload(self):
        # TF101S startMultiCook capture 2026-01-17 (whole chamber).
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(
            fryer.set_mode, cook_time=1200, cook_temp=200, chamber=3
        )
        payload = self._sent_body()['payload']
        assert payload['subDeviceNo'] == 0
        assert payload['subDeviceType'] == ''
        assert payload['data']['workChamber'] == 3
        assert payload['data']['syncType'] == 0
        assert payload['data']['readyStart'] is False

    def test_p583_start_payload(self):
        # P583-KUS cook/request.json 2025-05-21: accountID, hasLinkage, sub-device.
        fryer = self.get_device('air_fryers', 'CAF-P583S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=400)
        payload = self._sent_body()['payload']
        data = payload['data']
        assert data['accountID'] == self.manager.account_id
        assert 'accountId' not in data
        assert data['hasLinkage'] is False
        assert data['startAct'] == {
            'cookSetTime': 600,
            'cookTemp': 400,
            'preheatTemp': 0,
            'shakeTime': 0,
        }
        assert data['tempUnit'] == 'f'
        assert payload['subDeviceNo'] == 0
        assert payload['subDeviceType'] == ''

    def test_p583_ignores_uncaptured_preheat(self):
        # Every P583 startCook capture has hasPreheat 0; the map declares no PREHEAT.
        fryer = self.get_device('air_fryers', 'CAF-P583S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(
            fryer.set_mode, cook_time=600, cook_temp=400, preheat_time=240
        )
        data = self._sent_body()['payload']['data']
        assert data['hasPreheat'] == 0
        assert data['startAct']['preheatTemp'] == 0
        assert fryer.state.preheat_set_time is None

    def test_dc601s_keeps_preheat(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(
            fryer.set_mode, cook_time=600, cook_temp=400, preheat_time=240
        )
        data = self._sent_body()['payload']['data']
        assert data['hasPreheat'] == 1
        assert data['startAct']['preheatTemp'] == 400

    def test_dc601s_preheat_start_sets_heating(self):
        # DC601S capture 2026-01-01 20:39:06 reports heating while a preheat runs.
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(
            fryer.set_mode, cook_time=720, cook_temp=425, preheat_time=240
        )
        assert fryer.state.cook_status == AirFryerCookStatus.HEATING
        assert fryer.state.is_in_preheat_mode is True
        assert fryer.state.preheat_set_time == 240

    def test_dc601s_start_without_preheat_sets_cooking(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=1200, cook_temp=330)
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING
        assert fryer.state.is_in_preheat_mode is False
        assert fryer.state.preheat_set_time is None

    def test_dc601s_heating_status_is_preheat_mode(self):
        # DC601S capture 2026-01-01 20:39:06: Roast 425 F with a 240 s preheat.
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (
            _dc601s_status('heating', preheat=(240, 237, 425)),
            200,
        )
        self.run_in_loop(fryer.update)
        assert fryer.state.cook_status == AirFryerCookStatus.HEATING
        assert fryer.state.is_in_preheat_mode is True
        assert fryer.state.preheat_time_remaining == 237

    def test_p583_end_payload(self):
        # P583-KUS end-cook/request.json 2025-05-21.
        fryer = self.get_device('air_fryers', 'CAF-P583S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.end)
        assert self._sent_body()['payload'] == {
            'data': {},
            'method': 'endCook',
            'source': 'APP',
            'subDeviceNo': 0,
            'subDeviceType': '',
        }

    def test_dc601s_start_payload_unchanged(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=600, cook_temp=400)
        payload = self._sent_body()['payload']
        assert 'accountId' in payload['data']
        assert 'accountID' not in payload['data']
        assert 'subDeviceNo' not in payload

    def test_p583_cook_end_status(self):
        # P583-KUS get-status/cook-end/response.json 2025-05-21.
        fryer = self.get_device('air_fryers', 'CAF-P583S')
        self.mock_api.return_value = (
            build_bypass_v2_response(inner_result=P583_COOK_END_RESULT),
            200,
        )
        self.run_in_loop(fryer.update)
        assert fryer.state.cook_status == AirFryerCookStatus.COOK_END
        assert fryer.state.cook_set_temp == 400
        assert fryer.state.cook_mode == 'Broil'


    # CAF-DC111S-AEU hardware test 2026-11-07 (firmware 2.0.02 / MCU 1.0.10):
    # chamber 1 AirFry 120 C / 180 s and chamber 2 Bake 125 C / 120 s cooking.
    @staticmethod
    def _dc111s_both_cooking() -> dict:
        def item(chamber, status, mode, temp, set_time, rest):
            return {
                'cookStatus': status,
                'startTime': 1794066414,
                'recipeType': 3,
                'recipeId': 14 if mode == 'AirFry' else 9,
                'recipeName': 'Air Fry' if mode == 'AirFry' else 'Bake',
                'upc': '',
                'holdTime': 0,
                'cookSetTime': set_time,
                'cookTemp': temp,
                'mode': mode,
                'currentRemainingTime': rest,
                'totalTimeRemaining': rest,
                'chamber': chamber,
            }

        return build_bypass_v2_response(
            inner_result={
                'statusList': [
                    item(1, 'cooking', 'AirFry', 120, 180, 176),
                    item(2, 'cooking', 'Bake', 125, 120, 116),
                ],
                'tempUnit': 'c',
                'syncType': 0,
                'workChamber': 4,
            }
        )

    @pytest.mark.parametrize('chamber', [1, 2, 4])
    def test_dc111s_pause_resume_payload(self, chamber):
        # pauseWork / resumeWork {"chamber": n}: chamber 1 and 2 paused the
        # chamber, 4 paused and resumed both in one request (hardware test).
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        self.mock_api.return_value = (self._dc111s_both_cooking(), 200)
        self.run_in_loop(fryer.update)
        for method, call in (('pauseWork', fryer.stop), ('resumeWork', fryer.resume)):
            self.mock_api.return_value = (build_bypass_v2_response(), 200)
            assert self.run_in_loop(call, chamber)
            assert self._sent_body()['payload'] == {
                'data': {'chamber': chamber},
                'method': method,
                'source': 'APP',
                'subDeviceNo': 0,
                'subDeviceType': '',
            }

    def test_dc111s_pause_one_chamber_state(self):
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        self.mock_api.return_value = (self._dc111s_both_cooking(), 200)
        self.run_in_loop(fryer.update)
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.stop, 1)
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOK_STOP
        assert fryer.state_chamber_1.cook_time_remaining is not None
        assert fryer.state_chamber_2.cook_status == AirFryerCookStatus.COOKING
        assert self.run_in_loop(fryer.resume, 1)
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOKING

    def test_dc111s_pause_both_chambers_state(self):
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        self.mock_api.return_value = (self._dc111s_both_cooking(), 200)
        self.run_in_loop(fryer.update)
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(fryer.stop, 4)
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOK_STOP
        assert fryer.state_chamber_2.cook_status == AirFryerCookStatus.COOK_STOP
        assert self.run_in_loop(fryer.resume, 4)
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOKING
        assert fryer.state_chamber_2.cook_status == AirFryerCookStatus.COOKING

    def test_dc111s_refused_pause_keeps_state(self):
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        self.mock_api.return_value = (self._dc111s_both_cooking(), 200)
        self.run_in_loop(fryer.update)
        # pauseWork without a chamber was refused with 11000000 (hardware test).
        self.mock_api.return_value = (
            build_bypass_v2_response(inner_result={}, inner_code=11000000), 200
        )
        assert self.run_in_loop(fryer.stop, 1) is False
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOKING

    @pytest.mark.parametrize('setup_entry', ['CAF-TF101S', 'CAF-TF102S'])
    def test_dual_without_resumable_sends_nothing(self, setup_entry):
        fryer = self.get_device('air_fryers', setup_entry)
        self.mock_api.reset_mock()
        assert self.run_in_loop(fryer.stop, 1) is False
        assert self.run_in_loop(fryer.resume, 1) is False
        assert self.mock_api.call_count == 0

    def test_dc111s_rejects_whole_pause_without_request(self):
        fryer = self.get_device('air_fryers', 'CAF-DC111S-AEU')
        self.mock_api.reset_mock()
        assert self.run_in_loop(fryer.stop, 3) is False
        assert self.mock_api.call_count == 0

    # CS358-AF (Air Fryer CS358.har; entry N is log.entries[N])

    @pytest.mark.parametrize(('key', 'mode', 'recipe_id', 'name'), CS358_MODES)
    def test_cs358_mode_start_matches_capture(self, key, mode, recipe_id, name):
        fryer = self.get_device('air_fryers', 'CS358-AF')
        self.mock_api.return_value = (CS358_COMMAND_RESPONSE, 200)
        assert self.run_in_loop(
            fryer.set_mode, cook_time=60, cook_temp=170, cook_mode=key
        )
        data = self._sent_body()['payload']['data']
        assert (
            data['mode'],
            data['recipeId'],
            data['recipeName'],
            data['recipeType'],
            data['tempUnit'],
        ) == (mode, recipe_id, name, 3, 'f')
        assert data['startAct'] == {
            'cookSetTime': 60,
            'cookTemp': 170,
            'preheatTemp': 0,
            'shakeTime': 0,
        }
        assert 'accountId' in data

    def test_cs358_default_start_is_manual(self):
        # Air Fryer CS358.har entry 95: Custom, recipeId 11, recipeName "Manual",
        # 350 F, 900 s.
        fryer = self.get_device('air_fryers', 'CS358-AF')
        self.mock_api.return_value = (CS358_COMMAND_RESPONSE, 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=900, cook_temp=350)
        data = self._sent_body()['payload']['data']
        assert (data['mode'], data['recipeId'], data['recipeName']) == (
            'Custom', 11, 'Manual',
        )
        assert data['startAct'] == {
            'cookSetTime': 900,
            'cookTemp': 350,
            'preheatTemp': 0,
            'shakeTime': 0,
        }

    def test_cs358_preheat_start_matches_capture(self):
        # Air Fryer CS358.har entry 251: hasPreheat 1 and preheatTemp equal to
        # cookTemp; no preheat time.
        fryer = self.get_device('air_fryers', 'CS358-AF')
        self.mock_api.return_value = (CS358_COMMAND_RESPONSE, 200)
        assert self.run_in_loop(
            fryer.set_mode, cook_time=900, cook_temp=350, preheat_time=240
        )
        data = self._sent_body()['payload']['data']
        assert data['hasPreheat'] == 1
        assert data['startAct']['preheatTemp'] == 350
        assert not any(
            'preheat' in key.lower() and 'time' in key.lower()
            for key in (*data, *data['startAct'])
        )

    def test_cs358_celsius_start_rounds_capture_temp(self):
        # Air Fryer CS358.har entry 1187: Custom, recipeId 11, recipeName
        # "Manual", 900 s at 204 C. The request has that entry's shape, but
        # Celsius uses 5 C steps, so 205 C is sent.
        fryer = self.get_device('air_fryers', 'CS358-AF')
        fryer.temp_unit = TemperatureUnits.CELSIUS
        self.mock_api.return_value = (CS358_COMMAND_RESPONSE, 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=900, cook_temp=204)
        data = self._sent_body()['payload']['data']
        assert (
            data['mode'],
            data['recipeId'],
            data['recipeName'],
            data['recipeType'],
            data['tempUnit'],
        ) == ('Custom', 11, 'Manual', 3, 'c')
        assert data['startAct'] == {
            'cookSetTime': 900,
            'cookTemp': 205,
            'preheatTemp': 0,
            'shakeTime': 0,
        }

    def test_cs358_fahrenheit_recipe_sent_in_celsius(self):
        # 350 F is 176.7 C, sent as 175 C on the 5 C step.
        fryer = self.get_device('air_fryers', 'CS358-AF')
        fryer.temp_unit = TemperatureUnits.CELSIUS
        self.mock_api.return_value = (CS358_COMMAND_RESPONSE, 200)
        assert self.run_in_loop(fryer.set_mode_from_recipe, AirFryerPresets.cs358_manual)
        assert self._sent_body()['payload']['data']['startAct']['cookTemp'] == 175

    def test_cs358_celsius_rounded_to_step(self):
        fryer = self.get_device('air_fryers', 'CS358-AF')
        fryer.temp_unit = TemperatureUnits.CELSIUS
        self.mock_api.return_value = (CS358_COMMAND_RESPONSE, 200)
        assert self.run_in_loop(fryer.set_mode, cook_time=360, cook_temp=178)
        assert self._sent_body()['payload']['data']['startAct']['cookTemp'] == 180
        assert fryer.state.cook_set_temp == 180

    def test_cs358_cs158_custom_preset_sends_manual(self):
        # The CS158 preset (recipeId 1, "Manual Cooking") names the CUSTOM mode;
        # the CS358 sends its own Manual, as in Air Fryer CS358.har entry 95.
        fryer = self.get_device('air_fryers', 'CS358-AF')
        self.mock_api.return_value = (CS358_COMMAND_RESPONSE, 200)
        assert self.run_in_loop(fryer.set_mode_from_recipe, AirFryerPresets.custom)
        data = self._sent_body()['payload']['data']
        assert (data['mode'], data['recipeId'], data['recipeName'], data['recipeType']) == (
            'Custom', 11, 'Manual', 3,
        )

    @pytest.mark.parametrize(('key', 'mode', 'recipe_id', 'name'), CS358_MODES)
    def test_cs358_recipe_sends_the_mode_id_and_name(self, key, mode, recipe_id, name):
        fryer = self.get_device('air_fryers', 'CS358-AF')
        recipe = replace(
            fryer.get_mode_recipe(key), recipe_id=99, recipe_name='Mine', recipe_type=5
        )
        self.mock_api.return_value = (CS358_COMMAND_RESPONSE, 200)
        assert self.run_in_loop(fryer.set_mode_from_recipe, recipe)
        data = self._sent_body()['payload']['data']
        assert (data['mode'], data['recipeId'], data['recipeName'], data['recipeType']) == (
            mode, recipe_id, name, 3,
        )

    def test_cs358_end_matches_capture(self):
        # Air Fryer CS358.har entry 1194: endCook with empty data. The app also
        # sends subDeviceNo 0 and subDeviceType ''; the TurboBlaze requests
        # leave them out.
        fryer = self.get_device('air_fryers', 'CS358-AF')
        self.mock_api.return_value = (CS358_COMMAND_RESPONSE, 200)
        assert self.run_in_loop(fryer.end)
        assert self._sent_body()['payload'] == {
            'data': {},
            'method': 'endCook',
            'source': 'APP',
        }
        assert fryer.state.cook_status == AirFryerCookStatus.STANDBY

    def _cs358_poll(self, status: dict):
        fryer = self.get_device('air_fryers', 'CS358-AF')
        self.mock_api.return_value = (status, 200)
        self.run_in_loop(fryer.update)
        return fryer

    # Each case has the status and the times of the entry named beside it, and
    # the state times (in seconds) parsed from them.
    @pytest.mark.parametrize(
        ('status', 'kwargs', 'expected', 'times'),
        [
            (  # entry 96
                'ready',
                {},
                AirFryerCookStatus.READY,
                {'cook_last_time': 900, 'total_last_time': 900},
            ),
            (  # entry 260
                'heating',
                {'preheat': (240, 238, 350), 'total': 1138},
                AirFryerCookStatus.HEATING,
                {
                    'preheat_set_time': 240,
                    'preheat_last_time': 238,
                    'total_last_time': 1138,
                },
            ),
            (  # entry 264
                'preheatStop',
                {'preheat': (240, 215, 350), 'total': 1115},
                AirFryerCookStatus.PREHEAT_STOP,
                {
                    'preheat_set_time': 240,
                    'preheat_last_time': 215,
                    'total_last_time': 1115,
                },
            ),
            (  # entry 540
                'preheatEnd',
                {'preheat': (240, 0, 350)},
                AirFryerCookStatus.PREHEAT_END,
                {'preheat_set_time': 240, 'preheat_last_time': 0},
            ),
            (  # entry 134
                'cooking',
                {'step': {'cookLastTime': 898}, 'total': 898},
                AirFryerCookStatus.COOKING,
                {'cook_last_time': 898, 'total_last_time': 898},
            ),
            (  # entry 163
                'cookStop',
                {'step': {'cookLastTime': 835}, 'total': 835},
                AirFryerCookStatus.COOK_STOP,
                {'cook_last_time': 835, 'total_last_time': 835},
            ),
            (  # entry 205
                'pullOut',
                {'step': {'cookLastTime': 812}, 'total': 812},
                AirFryerCookStatus.PULL_OUT,
                {'cook_last_time': 812, 'total_last_time': 812},
            ),
            (  # entry 724
                'cookEnd',
                {'step': {'cookSetTime': 60, 'cookLastTime': 0}, 'total': 0},
                AirFryerCookStatus.COOK_END,
                {'cook_set_time': 60, 'cook_last_time': 0, 'total_last_time': 0},
            ),
        ],
    )
    def test_cs358_captured_statuses(self, status, kwargs, expected, times):
        fryer = self._cs358_poll(_cs358_status(status, **kwargs))
        assert fryer.state.cook_status == expected
        assert fryer.state.current_temp is None
        for name, value in times.items():
            assert getattr(fryer.state, name) == value, name

    def test_cs358_keeping_is_cooking(self):
        # Keep Warm reports 'keeping'. No CS358 capture has it; PR #557 saw it
        # on a CS358-AF (US) and maps it to COOKING, as the CAF-P583S does.
        fryer = self._cs358_poll(_cs358_status('keeping'))
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING
        assert 'Unknown cook status' not in self.caplog.text

    def test_cs358_ready_does_not_count_down(self):
        fryer = self._cs358_poll(_cs358_status('ready'))  # entry 96
        fryer.state.last_timestamp = datetime.now(UTC) - timedelta(seconds=60)
        assert fryer.state.cook_time_remaining == 900

    def test_cs358_preheat_stop_freezes_preheat(self):
        # Entry 264. cook_set_time is not asserted: the PREHEAT_STOP branch of
        # FryerState.set_state() does not apply the cook fields.
        fryer = self._cs358_poll(
            _cs358_status('preheatStop', preheat=(240, 215, 350), total=1115)
        )
        fryer.state.last_timestamp = datetime.now(UTC) - timedelta(seconds=60)
        assert fryer.state.preheat_time_remaining == 215
        assert fryer.state.total_time_remaining == 1115

    def test_cs358_preheat_end_keeps_loaded_cook(self):
        # Entry 540.
        fryer = self._cs358_poll(_cs358_status('preheatEnd', preheat=(240, 0, 350)))
        assert fryer.state.cook_set_time == 900
        assert fryer.state.cook_last_time == 900

    def test_cs358_cook_end_is_zero(self):
        # Entry 724: a 60 s cook that has finished.
        fryer = self._cs358_poll(
            _cs358_status(
                'cookEnd', step={'cookSetTime': 60, 'cookLastTime': 0}, total=0
            )
        )
        assert fryer.state.cook_last_time == 0
        assert fryer.state.total_time_remaining == 0

    @pytest.mark.parametrize('temp_unit', ['f', 'c'])
    def test_cs358_sensor_zero_is_not_fahrenheit(self, temp_unit):
        # currentTemp is 0 in all 363 captured polls; it is not a reading.
        status = _cs358_status(
            'cooking', step={'cookLastTime': 898}, total=898, temp_unit=temp_unit
        )
        fryer = self._cs358_poll(status)
        assert fryer.state.current_temp is None

    def test_cs358_program_status_uses_active_step(self):
        # Entry 1140: an app-loaded program, two Chicken steps, stepIndex 0.
        steps = [
            {
                'cookSetTime': 1380,
                'cookTemp': temp,
                'mode': 'Chicken',
                'cookLastTime': 1380,
                'shakeTime': 0,
                'cookEndTime': 0,
                'recipeName': 'Chicken',
                'recipeId': 2,
                'recipeType': 3,
            }
            for temp in (380, 230)
        ]
        fryer = self._cs358_poll(
            _cs358_status('ready', steps=steps, cook_mode='programs', total=2760)
        )
        assert fryer.state.cook_status == AirFryerCookStatus.READY
        assert fryer.state.cook_mode == 'Chicken'
        assert fryer.state.cook_set_temp == 380
        assert fryer.state.cook_set_time == 1380

    def test_cs358_preheat_handoff_matches_capture(self):
        # Entry 566 preheatEnd poll, then entry 567 preheatCook with empty data.
        fryer = self._cs358_poll(_cs358_status('preheatEnd', preheat=(240, 0, 350)))
        self.mock_api.reset_mock()
        self.mock_api.return_value = (CS358_COMMAND_RESPONSE, 200)
        assert self.run_in_loop(fryer.cook_from_preheat)
        assert self.mock_api.call_count == 1
        assert self._sent_body()['payload'] == {
            'data': {},
            'method': 'preheatCook',
            'source': 'APP',
        }
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING
        assert fryer.state.cook_time_remaining == 900  # entry 568 reports 900
        assert fryer.state.preheat_set_time is None

    def test_cs358_standby_updates_unit(self):
        # Entry 1154: standby in Celsius, with no steps.
        fryer = self._cs358_poll(
            _cs358_status('standby', steps=[], total=0, temp_unit='c')
        )
        assert fryer.state.cook_status == AirFryerCookStatus.STANDBY
        assert fryer.temp_unit == TemperatureUnits.CELSIUS

def test_air_fry_recipe_name():
    # DC601S startCook capture: recipeId 14, recipeName "Air Fry".
    assert AirFryerPresets.air_fry.recipe_name == 'Air Fry'
    assert AirFryerPresets.air_fry.recipe_id == 14


def test_resumable_flag_has_implementation():
    # RESUMABLE must only be declared where stop()/resume() are implemented.
    for entry in air_fryer_modules:
        if AirFryerFeatures.RESUMABLE not in entry.features:
            continue
        cls = getattr(entry.module, entry.class_name)
        assert cls.stop is not VeSyncFryer.stop, entry.setup_entry
        assert cls.resume is not VeSyncFryer.resume, entry.setup_entry
