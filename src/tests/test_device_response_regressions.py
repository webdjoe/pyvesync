"""Regression tests for observed device-list errors and chamber metadata."""
import asyncio
import copy
from unittest.mock import AsyncMock, patch
import pytest
from pyvesync import VeSync
from pyvesync.device_map import get_device_config
from pyvesync.devices.vesynckitchen import VeSyncAirFryerDC111, FryerChamberState
from pyvesync.models.fryer_models import AirFryerMultiStatusResult
from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
from pyvesync.utils.errors import VeSyncAPIResponseError, VeSyncServerError
from tests.call_json_fryers import DEVICE_DETAILS, STATUS_READY


def manager():
    m=VeSync('offline-test','not-a-real-password',session=AsyncMock())
    m.set_credentials('test-token','test-account','DE','EU')
    return m


@pytest.mark.parametrize('payload',[None,[],{}, {'code':0,'result':None},{'code':0,'result':[]},{'code':0,'result':'bad'}])
def test_invalid_list_is_library_error_and_releases_flag(payload):
    m=manager()
    with patch.object(VeSync,'async_call_api',AsyncMock(return_value=(payload,200))),patch.object(VeSync,'process_devices') as process:
        with pytest.raises(VeSyncAPIResponseError):asyncio.run(m.get_devices())
        process.assert_not_called()
    assert m.in_process is False


def test_server_error_with_null_result_preserves_category():
    m=manager()
    with patch.object(VeSync,'async_call_api',AsyncMock(return_value=({'code':-11102000,'result':None},200))):
        with pytest.raises(VeSyncServerError):asyncio.run(m.get_devices())
    assert m.in_process is False


def test_transport_error_and_no_credentials_release_flag():
    m=manager()
    with patch.object(VeSync,'async_call_api',AsyncMock(side_effect=VeSyncAPIResponseError('offline'))):
        with pytest.raises(VeSyncAPIResponseError):asyncio.run(m.get_devices())
    assert not m.in_process
    m.auth.clear_credentials()
    with patch.object(VeSync,'async_call_api',AsyncMock()) as api:
        assert asyncio.run(m.get_devices()) is False
        api.assert_not_called()
    assert not m.in_process


def test_valid_empty_list_still_processed():
    m=manager();data={'traceId':'offline','code':0,'msg':'success','result':{'total':0,'pageSize':100,'pageNo':1,'list':[]}}
    with patch.object(VeSync,'async_call_api',AsyncMock(return_value=(data,200))):
        assert asyncio.run(m.get_devices()) is True
    assert not m.in_process


@pytest.mark.parametrize('recipe_type',[None,0,3,9])
def test_chamber_recipe_category_is_preserved(recipe_type):
    m=AsyncMock();fryer=VeSyncAirFryerDC111(ResponseDeviceDetailsModel.from_dict(DEVICE_DETAILS),m,get_device_config('CAF-DC111S-AEU'))
    data=copy.deepcopy(STATUS_READY);data['statusList'][0]['recipeType']=recipe_type
    fryer.state.status_response(AirFryerMultiStatusResult.from_dict(data))
    assert fryer.state.chambers[1].recipe_type==recipe_type


def test_existing_positional_state_constructor_remains_compatible():
    state=FryerChamberState(1,'ready','AirFry',14,'Air Fry',180,10,5,5)
    assert state.cook_set_temp==180 and state.total_time_remaining==5
    assert state.recipe_type is None
