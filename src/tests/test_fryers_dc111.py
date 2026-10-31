"""Tests for CAF-DC111S-AEU air fryer support."""

import asyncio
import copy
from unittest.mock import AsyncMock, patch

import pytest

from pyvesync.device_map import get_device_config
from pyvesync.devices.vesynckitchen import VeSyncAirFryerDC111
from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
from tests.call_json_fryers import (
    DEVICE_DETAILS,
    STATUS_READY,
    STATUS_STANDBY,
    bypass_response,
)


@pytest.fixture
def manager():
    """Return a minimal mocked manager."""
    mocked = AsyncMock()
    mocked.account_id = 'test-account'
    mocked.token = 'test-token'
    mocked.time_zone = 'Europe/Warsaw'
    mocked.country_code = 'PL'
    mocked.accept_language = 'pl'
    mocked.app_version = '5.9.20'
    mocked.phone_brand = 'pytest'
    mocked.phone_os = 'Android'
    mocked.debug_mode = False
    mocked.trace_id = 'test-trace'
    return mocked


@pytest.fixture
def fryer(manager):
    """Create the CAF-DC111S-AEU device."""
    details = ResponseDeviceDetailsModel.from_dict(DEVICE_DETAILS)
    feature_map = get_device_config('CAF-DC111S-AEU')

    assert feature_map is not None

    return VeSyncAirFryerDC111(details, manager, feature_map)


def test_dc111_device_map() -> None:
    """The device map selects the new DC111 class."""
    config = get_device_config('CAF-DC111S-AEU')

    assert config is not None
    assert config.class_name == 'VeSyncAirFryerDC111'
    assert config.setup_entry == 'CAF-DC111S-AEU'


def test_get_details_reads_both_chambers(fryer) -> None:
    """Status response populates both cooking chambers."""
    mocked = AsyncMock(return_value=bypass_response(STATUS_STANDBY)[0])

    with patch.object(
        VeSyncAirFryerDC111,
        'call_bypassv2_api',
        new=mocked,
    ):
        asyncio.run(fryer.get_details())

    assert fryer.temp_unit == 'celsius'
    assert fryer.state.sync_type == 0
    assert fryer.state.work_chamber == 0
    assert set(fryer.state.chambers) == {1, 2}
    assert fryer.state.chambers[1].cook_status == 'standby'
    assert fryer.state.chambers[2].cook_status == 'standby'
    assert fryer.state.cook_status == 'standby'
    assert fryer.state.cook_set_temp is None
    assert fryer.state.cook_set_time is None


def test_get_details_ready_program(fryer) -> None:
    """Prepared program is represented as ready."""
    mocked = AsyncMock(return_value=bypass_response(STATUS_READY)[0])

    with patch.object(
        VeSyncAirFryerDC111,
        'call_bypassv2_api',
        new=mocked,
    ):
        asyncio.run(fryer.get_details())

    chamber = fryer.state.chambers[1]

    assert fryer.state.work_chamber == 1
    assert chamber.cook_status == 'ready'
    assert chamber.mode == 'AirFry'
    assert chamber.cook_set_temp == 180
    assert chamber.cook_set_time == 5
    assert chamber.remaining_time == 5

    # Top-level attributes report the active chamber, as read by Home Assistant.
    assert fryer.state.active_chamber is chamber
    assert fryer.state.cook_status == 'ready'
    assert fryer.state.cook_set_temp == 180
    assert fryer.state.cook_set_time == 5
    assert fryer.state.current_temp is None
    assert fryer.state.preheat_set_time is None


def test_active_chamber_is_second_when_first_idle(fryer) -> None:
    """A program only in chamber 2 is reported at the top level."""
    status = copy.deepcopy(STATUS_READY)
    status['statusList'][0], status['statusList'][1] = (
        {**status['statusList'][1], 'chamber': 1},
        {**status['statusList'][0], 'chamber': 2},
    )
    mocked = AsyncMock(return_value=bypass_response(status)[0])

    with patch.object(VeSyncAirFryerDC111, 'call_bypassv2_api', new=mocked):
        asyncio.run(fryer.get_details())

    assert fryer.state.active_chamber.chamber == 2
    assert fryer.state.cook_status == 'ready'


def test_state_serializes(fryer) -> None:
    """Device and state can be dumped to dict and JSON."""
    mocked = AsyncMock(return_value=bypass_response(STATUS_READY)[0])

    with patch.object(VeSyncAirFryerDC111, 'call_bypassv2_api', new=mocked):
        asyncio.run(fryer.get_details())

    state = fryer.to_dict()
    assert state['cook_status'] == 'ready'
    assert state['temp_unit'] == 'celsius'
    assert 'chambers' in state
    assert '"cook_set_temp":180' in fryer.state.to_json()


def test_fahrenheit_unit(fryer) -> None:
    """Fahrenheit status switches validation range and request unit."""
    status = {**STATUS_STANDBY, 'tempUnit': 'f'}
    mocked = AsyncMock(return_value=bypass_response(status)[0])

    with patch.object(VeSyncAirFryerDC111, 'call_bypassv2_api', new=mocked):
        asyncio.run(fryer.get_details())
        assert fryer.temp_unit == 'fahrenheit'

        mocked.return_value = bypass_response()[0]
        assert asyncio.run(fryer.prepare_program(1, 400, 10)) is True

    assert mocked.await_args.kwargs['data']['tempUnit'] == 'f'
    assert mocked.await_args.kwargs['data']['cookConfigs'][0]['cookTemp'] == 400


@pytest.mark.parametrize(
    ('kwargs', 'error'),
    [
        ({'chamber': 3, 'temperature': 180, 'minutes': 5}, 'chamber'),
        ({'chamber': 1, 'temperature': 180, 'minutes': 0}, 'minutes'),
        ({'chamber': 1, 'temperature': 400, 'minutes': 5}, 'temperature'),
        ({'chamber': 1, 'temperature': 180, 'minutes': 5, 'mode': 'Roast'}, 'mode'),
    ],
)
def test_prepare_program_rejects_invalid(fryer, kwargs, error) -> None:
    """Invalid arguments raise before any API call."""
    mocked = AsyncMock()

    with (
        patch.object(VeSyncAirFryerDC111, 'call_bypassv2_api', new=mocked),
        pytest.raises(ValueError, match=error),
    ):
        asyncio.run(fryer.prepare_program(**kwargs))

    mocked.assert_not_awaited()


def test_prepare_program(fryer) -> None:
    """Prepare sends startMultiCook with correct chamber data."""
    mocked = AsyncMock(return_value=bypass_response()[0])

    with patch.object(
        VeSyncAirFryerDC111,
        'call_bypassv2_api',
        new=mocked,
    ):
        result = asyncio.run(
            fryer.prepare_program(
                chamber=1,
                temperature=180,
                minutes=5,
            )
        )

    assert result is True
    mocked.assert_awaited_once()

    method = mocked.await_args.args[0]
    data = mocked.await_args.kwargs['data']

    assert method == 'startMultiCook'
    assert data['workChamber'] == 1
    assert data['readyStart'] is True

    config = data['cookConfigs'][0]
    assert config['chamber'] == 1
    assert config['cookTemp'] == 180
    assert config['cookSetTime'] == 300
    assert config['mode'] == 'AirFry'


def test_stop_chamber(fryer) -> None:
    """End prepared or running program."""
    mocked = AsyncMock(return_value=bypass_response()[0])

    with patch.object(
        VeSyncAirFryerDC111,
        'call_bypassv2_api',
        new=mocked,
    ):
        result = asyncio.run(fryer.stop_chamber(1))

    assert result is True
    mocked.assert_awaited_once_with(
        'endCook',
        data={'chamber': 1},
    )


def test_stop_empty_chamber_returns_false(fryer) -> None:
    """Error 11923000 means there was no program to stop."""
    response = bypass_response()[0]
    response['result']['code'] = 11923000
    response['result']['msg'] = 'af_iot_bypass_end_cook'

    mocked = AsyncMock(return_value=response)

    with patch.object(
        VeSyncAirFryerDC111,
        'call_bypassv2_api',
        new=mocked,
    ):
        result = asyncio.run(fryer.stop_chamber(1))

    assert result is False


def test_prepare_both_chambers_sync_finish(
    fryer: VeSyncAirFryerDC111,
) -> None:
    """Prepare both chambers with synchronized finishing times."""
    mocked = AsyncMock(return_value=bypass_response()[0])

    with patch.object(
        VeSyncAirFryerDC111,
        'call_bypassv2_api',
        new=mocked,
    ):
        result = asyncio.run(
            fryer.prepare_both_chambers(
                chamber_1={
                    'temperature': 180,
                    'minutes': 10,
                    'mode': 'AirFry',
                },
                chamber_2={
                    'temperature': 195,
                    'minutes': 15,
                    'mode': 'AirFry',
                },
                sync_type=1,
            )
        )

    assert result is True

    method = mocked.await_args.args[0]
    data = mocked.await_args.kwargs['data']

    assert method == 'startMultiCook'
    assert data['syncType'] == 1
    assert data['workChamber'] == 4
    assert len(data['cookConfigs']) == 2

    chamber_1 = data['cookConfigs'][0]
    chamber_2 = data['cookConfigs'][1]

    assert chamber_1['chamber'] == 1
    assert chamber_1['cookSetTime'] == 600
    assert chamber_1['cookTemp'] == 180

    assert chamber_2['chamber'] == 2
    assert chamber_2['cookSetTime'] == 900
    assert chamber_2['cookTemp'] == 195


def test_prepare_both_chambers_match(
    fryer: VeSyncAirFryerDC111,
) -> None:
    """Prepare both chambers with matching settings."""
    mocked = AsyncMock(return_value=bypass_response()[0])
    matching = {
        'temperature': 195,
        'minutes': 10,
        'mode': 'AirFry',
    }

    with patch.object(
        VeSyncAirFryerDC111,
        'call_bypassv2_api',
        new=mocked,
    ):
        result = asyncio.run(
            fryer.prepare_both_chambers(
                chamber_1=matching,
                chamber_2=matching,
                sync_type=2,
            )
        )

    assert result is True

    data = mocked.await_args.kwargs['data']

    assert data['syncType'] == 2
    assert data['workChamber'] == 4
    assert data['cookConfigs'][0]['cookTemp'] == 195
    assert data['cookConfigs'][1]['cookTemp'] == 195
    assert data['cookConfigs'][0]['cookSetTime'] == 600
    assert data['cookConfigs'][1]['cookSetTime'] == 600
