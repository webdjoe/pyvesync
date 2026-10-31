"""Air fryer request and state tests pinned to packet capture values.

Each test uses request/response shapes from the air fryer packet captures
(CS137/CS158, CAF-DC601S, CAF-P583S-KUS and CAF-TF101S) to verify the
library sends the captured request and parses the captured response.
"""

from dataclasses import replace

from base_test_cases import TestBase
from defaults import build_bypass_v1_response, build_bypass_v2_response
from utils import parse_args

from pyvesync import const
from pyvesync.base_devices.fryer_base import VeSyncFryer
from pyvesync.const import AirFryerCookStatus, AirFryerFeatures, AirFryerPresets
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
            'stepIndex': 0,
            'cookStatus': cook_status,
            'preheatSetTime': preheat_set,
            'preheatLastTime': preheat_last,
            'preheatEndTime': 0,
            'preheatTemp': preheat_temp,
            'startTime': 1767318116,
            'totalTimeRemaining': cook_last_time,
            'currentTemp': 112,
            'shakeStatus': 0,
        }
    )


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
                'readyStart': True,
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
        assert fryer.state.preheat_set_time == 300

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

    def test_tf101s_start_sets_ready(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.mock_api.return_value = (build_bypass_v2_response(), 200)
        assert self.run_in_loop(
            fryer.set_mode, cook_time=1200, cook_temp=200, chamber=3
        )
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.READY

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


def test_air_fry_recipe_name():
    # DC601S startCook capture: recipeId 14, recipeName "Air Fry".
    assert AirFryerPresets.air_fry.recipe_name == 'Air Fry'
    assert AirFryerPresets.air_fry.recipe_id == 14


def test_p583_cook_modes_captured_only():
    for setup_entry in ('CAF-P583S', 'CAF-P583S-KEU'):
        entry = next(m for m in air_fryer_modules if m.setup_entry == setup_entry)
        assert set(entry.cook_modes.values()) == {'AirFry', 'Broil', 'Roast', 'Bake'}


def test_no_uncaptured_presets():
    assert not hasattr(const, 'AIRFRYER_PRESET_MAP')
    for name in (
        'reheat',
        'steak',
        'seafood',
        'veggies',
        'french_fries',
        'frozen',
        'chicken',
    ):
        assert not hasattr(AirFryerPresets, name)


def test_resumable_flag_has_implementation():
    # RESUMABLE must only be declared where stop()/resume() are implemented.
    for entry in air_fryer_modules:
        if AirFryerFeatures.RESUMABLE not in entry.features:
            continue
        cls = getattr(entry.module, entry.class_name)
        assert cls.stop is not VeSyncFryer.stop, entry.setup_entry
        assert cls.resume is not VeSyncFryer.resume, entry.setup_entry
