"""Tests for CAF-DC111S-AEU air fryer support."""

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


@pytest.mark.asyncio
async def test_get_details_reads_both_chambers(fryer) -> None:
    """Status response populates both cooking chambers."""
    mocked = AsyncMock(
        return_value=bypass_response(STATUS_STANDBY)[0]
    )

    with patch.object(
        VeSyncAirFryerDC111,
        'call_bypassv2_api',
        new=mocked,
    ):
        await fryer.get_details()

    assert fryer.temp_unit == 'c'
    assert fryer.sync_type == 0
    assert fryer.work_chamber == 0
    assert set(fryer.chambers) == {1, 2}
    assert fryer.chambers[1]['cookStatus'] == 'standby'
    assert fryer.chambers[2]['cookStatus'] == 'standby'


@pytest.mark.asyncio
async def test_get_details_ready_program(fryer) -> None:
    """Prepared program is represented as ready."""
    mocked = AsyncMock(
        return_value=bypass_response(STATUS_READY)[0]
    )

    with patch.object(
        VeSyncAirFryerDC111,
        'call_bypassv2_api',
        new=mocked,
    ):
        await fryer.get_details()

    chamber = fryer.chambers[1]

    assert fryer.work_chamber == 1
    assert chamber['cookStatus'] == 'ready'
    assert chamber['cookTemp'] == 180
    assert chamber['cookSetTime'] == 300
    assert chamber['currentRemainingTime'] == 300


@pytest.mark.asyncio
async def test_prepare_program(fryer) -> None:
    """Prepare sends startMultiCook with correct chamber data."""
    mocked = AsyncMock(return_value=bypass_response()[0])

    with patch.object(
        VeSyncAirFryerDC111,
        'call_bypassv2_api',
        new=mocked,
    ):
        result = await fryer.prepare_program(
            chamber=1,
            temperature=180,
            minutes=5,
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


@pytest.mark.asyncio
async def test_stop_chamber(fryer) -> None:
    """End prepared or running program."""
    mocked = AsyncMock(return_value=bypass_response()[0])

    with patch.object(
        VeSyncAirFryerDC111,
        'call_bypassv2_api',
        new=mocked,
    ):
        result = await fryer.stop_chamber(1)

    assert result is True
    mocked.assert_awaited_once_with(
        'endCook',
        data={'chamber': 1},
    )


@pytest.mark.asyncio
async def test_stop_empty_chamber_returns_false(fryer) -> None:
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
        result = await fryer.stop_chamber(1)

    assert result is False
