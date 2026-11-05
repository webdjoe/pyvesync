"""Air fryer failure resistance and local state consistency tests.

Bad units and failed polls must not raise or wipe the state, a command the
library sends must leave the state in the phase it sent, and invalid times
must be rejected before a request is sent.
"""

import logging
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from base_test_cases import TestBase
from call_json import ALL_DEVICE_MAP_DICT, DeviceList
from defaults import build_bypass_v1_response, build_bypass_v2_response
from test_fryer_captures import _158_status, _dc601s_status
from test_fryer_chambers import _tf101s_chamber, _tf101s_status
from utils import parse_args

from pyvesync.const import (
    AirFryerChamber,
    AirFryerCookModes,
    AirFryerCookStatus,
    AirFryerPresets,
    ConnectionStatus,
    TemperatureUnits,
)
from pyvesync.models.vesync_models import ResponseDeviceDetailsModel

V1_OK = (build_bypass_v1_response(result_dict={}), 200)
V2_OK = (build_bypass_v2_response(), 200)


def _age(state, seconds: int) -> None:
    """Move a running state's countdown start back by ``seconds``."""
    state.last_timestamp = datetime.now(UTC) - timedelta(seconds=seconds)


class TestFryerResilience(TestBase):
    """Failure resistance and state consistency of the air fryer classes."""

    def _sent(self) -> dict:
        return parse_args(self.mock_api)['json_object']

    def _send(self, method, *args, ok=V1_OK, **kwargs):
        self.mock_api.reset_mock()
        self.mock_api.return_value = ok
        return self.run_in_loop(method, *args, **kwargs)

    # Temperature units

    def test_bad_temp_unit_setter_keeps_unit_and_warns(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        fryer.temp_unit = 'kelvin'
        assert fryer.temp_unit == TemperatureUnits.FAHRENHEIT
        assert 'kelvin' in self.caplog.text

    def test_158_poll_with_bad_unit_still_updates_state(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        status = _158_status(currentTemp=108)
        status['result']['returnStatus']['tempUnit'] = 'x'
        self._send(fryer.update, ok=(status, 200))
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING
        assert fryer.temp_unit == TemperatureUnits.FAHRENHEIT

    def test_turboblaze_poll_with_null_unit_still_updates_state(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        status = _dc601s_status('cooking')
        status['result']['result']['tempUnit'] = None
        self._send(fryer.update, ok=(status, 200))
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING
        assert fryer.temp_unit == TemperatureUnits.FAHRENHEIT

    @pytest.mark.parametrize('unit', ['x', None, 'missing'])
    def test_dual_poll_with_bad_or_missing_unit_still_updates_state(self, unit):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        status = _tf101s_status([_tf101s_chamber(1, 'cooking')], work_chamber=1)
        if unit == 'missing':
            del status['result']['result']['tempUnit']
        else:
            status['result']['result']['tempUnit'] = unit
        self._send(fryer.update, ok=(status, 200))
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOKING
        assert fryer.temp_unit == TemperatureUnits.CELSIUS

    def test_recipe_with_bad_unit_returns_false_without_request(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        recipe = replace(fryer.get_mode_recipe(), temp_unit='kelvin')
        assert self._send(fryer.set_mode_from_recipe, recipe) is False
        assert self.mock_api.call_count == 0
        assert 'kelvin' in self.caplog.text

    # CS158 stop / resume

    def test_158_stop_in_standby_sends_cook_stop(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        assert self._send(fryer.stop) is True
        assert self._sent()['jsonCmd'] == {'cookMode': {'cookStatus': 'stop'}}
        assert fryer.state.cook_status == AirFryerCookStatus.COOK_STOP

    def test_158_resume_in_standby_sends_cook_resume(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        assert self._send(fryer.resume) is True
        assert self._sent()['jsonCmd'] == {'cookMode': {'cookStatus': 'cooking'}}
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING

    def test_158_resume_while_cooking_keeps_countdown(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        assert self._send(fryer.set_mode, cook_time=600, cook_temp=350)
        _age(fryer.state, 300)
        assert self._send(fryer.resume) is True
        assert self._sent()['jsonCmd'] == {'cookMode': {'cookStatus': 'cooking'}}
        assert fryer.state.cook_time_remaining <= 300

    def test_158_resume_while_preheating_keeps_countdown(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        assert self._send(fryer.set_mode, cook_time=600, cook_temp=350, preheat_time=300)
        _age(fryer.state, 120)
        assert self._send(fryer.resume) is True
        assert self._sent()['jsonCmd'] == {'preheat': {'preheatStatus': 'heating'}}
        assert fryer.state.preheat_time_remaining <= 180

    @pytest.mark.parametrize(
        ('preheat_time', 'key', 'status_key', 'running'),
        [
            (None, 'cookMode', 'cookStatus', 'cooking'),
            (300, 'preheat', 'preheatStatus', 'heating'),
        ],
    )
    def test_158_commands_keep_state_in_the_sent_phase(
        self, preheat_time, key, status_key, running
    ):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        assert self._send(fryer.set_mode, cook_time=600, cook_temp=350, preheat_time=preheat_time)
        for method, value in [
            (fryer.stop, 'stop'),
            (fryer.stop, 'stop'),
            (fryer.resume, running),
            (fryer.resume, running),
            (fryer.stop, 'stop'),
        ]:
            assert self._send(method) is True
            assert self._sent()['jsonCmd'] == {key: {status_key: value}}
        assert self._send(fryer.end) is True
        assert self._sent()['jsonCmd'] == {key: {status_key: 'end'}}
        assert fryer.state.cook_status == AirFryerCookStatus.STANDBY

    def test_158_stopped_preheat_keeps_remaining_on_resume(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        assert self._send(fryer.set_mode, cook_time=600, cook_temp=350, preheat_time=300)
        _age(fryer.state, 120)
        assert self._send(fryer.stop)
        assert fryer.state.preheat_time_remaining <= 180
        assert self._send(fryer.resume)
        assert fryer.state.preheat_time_remaining <= 180

    # Dual end

    def _poll_dual(self, fryer, items, work_chamber, sync_type=0):
        self._send(fryer.update, ok=(_tf101s_status(items, work_chamber, sync_type), 200))

    def test_end_chamber_1_during_whole_cook_sends_whole(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self._poll_dual(fryer, [_tf101s_chamber(3, 'cooking')], work_chamber=3)
        assert fryer.work_chamber == AirFryerChamber.WHOLE
        assert self._send(fryer.end, ok=V2_OK) is True
        assert self._sent()['payload']['data'] == {'chamber': 3}
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.STANDBY
        assert fryer.work_chamber is None

    def test_local_whole_start_then_end_sends_whole(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        assert self._send(fryer.set_mode, 1200, 200, chamber=AirFryerChamber.WHOLE, ok=V2_OK)
        assert fryer.work_chamber == AirFryerChamber.WHOLE
        assert self._send(fryer.end, ok=V2_OK) is True
        assert self._sent()['payload']['data'] == {'chamber': 3}

    def test_single_chamber_start_after_whole_ends_chamber_1(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self._poll_dual(fryer, [_tf101s_chamber(3, 'cooking')], work_chamber=3)
        assert self._send(fryer.set_mode, 1200, 200, ok=V2_OK)
        assert fryer.work_chamber is None
        assert self._send(fryer.end, ok=V2_OK) is True
        assert self._sent()['payload']['data'] == {'chamber': 1}

    def test_end_both_clears_work_chamber(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        items = [_tf101s_chamber(1, 'cooking'), _tf101s_chamber(2, 'cooking')]
        self._poll_dual(fryer, items, work_chamber=4, sync_type=2)
        assert self._send(fryer.end, AirFryerChamber.BOTH, ok=V2_OK) is True
        assert fryer.work_chamber is None

    # Times

    @pytest.mark.parametrize(
        ('setup_entry', 'kwargs'),
        [
            ('CS158-AF', {'cook_time': 0}),
            ('CS158-AF', {'cook_time': 30}),
            ('CS158-AF', {'cook_time': -600}),
            ('CS158-AF', {'cook_time': 600, 'preheat_time': 30}),
            ('CS158-AF', {'cook_time': 600, 'preheat_time': -60}),
            ('CAF-DC601S', {'cook_time': 0}),
            ('CAF-DC601S', {'cook_time': -5}),
            ('CAF-DC601S', {'cook_time': 600, 'preheat_time': -5}),
            ('CAF-TF101S', {'cook_time': 0, 'chamber': AirFryerChamber.BOTH}),
        ],
    )
    def test_invalid_times_rejected_without_request(self, setup_entry, kwargs):
        fryer = self.get_device('air_fryers', setup_entry)
        temp = fryer.temp_limits().min_temp
        assert self._send(fryer.set_mode, cook_temp=temp, **kwargs) is False
        assert self.mock_api.call_count == 0

    def test_float_cook_time_stored_as_whole_seconds(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        assert self._send(fryer.set_mode, cook_time=600.5, cook_temp=400, ok=V2_OK)
        assert self._sent()['payload']['data']['startAct']['cookSetTime'] == 600
        assert fryer.state.cook_set_time == 600
        assert isinstance(fryer.state.cook_set_time, int)

    # Failed polls

    @pytest.mark.parametrize(
        'response',
        [
            (None, 200),
            ({'code': 0, 'result': None}, 200),
            (build_bypass_v1_response(code=-11000000), 200),
        ],
    )
    def test_158_failed_poll_keeps_state(self, response):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self._send(fryer.update, ok=(_158_status(currentTemp=108), 200))
        self._send(fryer.update, ok=response)
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING
        assert fryer.state.cook_set_temp == 350

    def test_158_unknown_status_keeps_state(self):
        fryer = self.get_device('air_fryers', 'CS158-AF')
        self._send(fryer.update, ok=(_158_status(currentTemp=108), 200))
        unknown = _158_status()
        unknown['result']['returnStatus']['cookStatus'] = 'bogus'
        self._send(fryer.update, ok=(unknown, 200))
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING
        assert 'bogus' in self.caplog.text

    @pytest.mark.parametrize(
        'response',
        [
            (None, 200),
            (build_bypass_v2_response(inner_code=11000000), 200),
            (_dc601s_status('cooking', step_index=3), 200),
            (_dc601s_status('bogus'), 200),
        ],
    )
    def test_turboblaze_failed_poll_keeps_state(self, response):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        self._send(fryer.update, ok=(_dc601s_status('cooking'), 200))
        self._send(fryer.update, ok=response)
        assert fryer.state.cook_status == AirFryerCookStatus.COOKING

    @pytest.mark.parametrize(
        'response',
        [
            (None, 200),
            (build_bypass_v2_response(inner_code=11000000), 200),
        ],
    )
    def test_dual_failed_poll_keeps_state(self, response):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        items = [_tf101s_chamber(1, 'cooking'), _tf101s_chamber(2, 'cooking')]
        self._poll_dual(fryer, items, work_chamber=4, sync_type=2)
        self._send(fryer.update, ok=response)
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOKING
        assert fryer.state_chamber_2.cook_status == AirFryerCookStatus.COOKING
        assert fryer.work_chamber == AirFryerChamber.BOTH
        assert fryer.sync_chambers is True

    def test_dual_unknown_chamber_status_keeps_that_chamber(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        items = [_tf101s_chamber(1, 'cooking'), _tf101s_chamber(2, 'cooking')]
        self._poll_dual(fryer, items, work_chamber=4)
        items = [_tf101s_chamber(1, 'bogus'), _tf101s_chamber(2, 'cooking')]
        self._poll_dual(fryer, items, work_chamber=4)
        assert fryer.state_chamber_1.cook_status == AirFryerCookStatus.COOKING
        assert 'bogus' in self.caplog.text

    def test_dual_offline_poll_marks_both_chambers(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self._poll_dual(fryer, [_tf101s_chamber(1, 'cooking')], work_chamber=1)
        self._send(fryer.update, ok=(build_bypass_v2_response(code=4041004), 200))
        assert fryer.state_chamber_1.connection_status == ConnectionStatus.OFFLINE
        assert fryer.state_chamber_2.connection_status == ConnectionStatus.OFFLINE
        assert fryer.state_chamber_2.last_update_ts == fryer.state_chamber_1.last_update_ts

    # set_mode_from_recipe

    @pytest.mark.parametrize(
        ('setup_entry', 'preset'),
        [('CAF-DC601S', 'custom'), ('CS158-AF', 'bake'), ('CAF-TF101S', 'broil')],
    )
    def test_recipe_with_mode_fryer_lacks_is_rejected(self, setup_entry, preset):
        fryer = self.get_device('air_fryers', setup_entry)
        # 350 F is inside every default mode's range, so only the mode can fail.
        recipe = replace(getattr(AirFryerPresets, preset), target_temp=350, temp_unit='f')
        assert self._send(fryer.set_mode_from_recipe, recipe) is False
        assert self.mock_api.call_count == 0
        assert recipe.cook_mode in self.caplog.text

    def test_recipe_mode_key_is_sent_as_api_mode(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        recipe = replace(fryer.get_mode_recipe(AirFryerCookModes.ROAST), cook_mode='roast')
        assert self._send(fryer.set_mode_from_recipe, recipe, ok=V2_OK) is True
        assert self._sent()['payload']['data']['mode'] == 'Roast'
        assert fryer.state.cook_mode == 'Roast'
        assert recipe.cook_mode == 'roast'

    def test_out_of_range_log_names_mode_whose_limits_apply(self):
        fryer = self.get_device('air_fryers', 'CAF-TF101S')
        self.caplog.set_level(logging.WARNING)
        assert fryer.prepare_temperature(500, 'Grill') is None
        assert 'Grill range' in self.caplog.text
        self.caplog.clear()
        assert fryer.prepare_temperature(500, 'Nope') is None
        assert 'AirFry range' in self.caplog.text

    # Shared presets

    def test_default_preset_is_per_device(self):
        first = self.get_device('air_fryers', 'CAF-DC601S')
        second = type(first)(
            _details('CAF-DC601S'), self.manager, ALL_DEVICE_MAP_DICT['CAF-DC601S']
        )
        first.default_preset.cook_time = 42
        assert second.default_preset.cook_time != 42
        assert AirFryerPresets.air_fry.cook_time != 42


def _details(setup_entry: str) -> ResponseDeviceDetailsModel:
    """Return device-list details for a setup entry."""
    return ResponseDeviceDetailsModel.from_dict(
        DeviceList.device_list_item(ALL_DEVICE_MAP_DICT[setup_entry])
    )
