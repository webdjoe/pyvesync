"""Mocked API responses for air fryer tests."""

from collections import defaultdict
from typing import Any

DEVICE_TYPE = 'CAF-DC111S-AEU'
SETUP_ENTRY = 'CAF-DC111S-AEU'

DEVICE_DETAILS = {
    'deviceRegion': 'EU',
    'isOwner': True,
    'authKey': None,
    'deviceName': 'Turbo Tower Pro Smart Air Fryer',
    'deviceImg': '',
    'cid': 'test-dc111-cid',
    'deviceStatus': 'off',
    'connectionStatus': 'online',
    'connectionType': 'WiFi+BTOnboarding+BTNotify',
    'deviceType': DEVICE_TYPE,
    'type': 'SKA',
    'uuid': 'test-dc111-uuid',
    'configModule': 'VS_WFON_CAF-DC111S-AEU_EU',
    'macID': '00:00:00:00:00:00',
    'mode': None,
    'speed': None,
    'currentFirmVersion': None,
    'subDeviceNo': None,
    'subDeviceType': None,
    'deviceFirstSetupTime': '',
    'subDeviceList': None,
    'extension': None,
    'deviceProp': None,
}


def bypass_response(result: dict[str, Any] | None = None) -> tuple[dict[str, Any], int]:
    """Create a successful bypassV2 response."""
    return (
        {
            'traceId': 'test-trace',
            'code': 0,
            'msg': 'request success',
            'module': None,
            'stacktrace': None,
            'result': {
                'traceId': 'test-trace',
                'code': 0,
                **({'result': result} if result is not None else {}),
            },
        },
        200,
    )


STATUS_STANDBY = {
    'statusList': [
        {
            'cookStatus': 'standby',
            'startTime': 0,
            'recipeType': 3,
            'recipeId': 14,
            'recipeName': '',
            'upc': '',
            'holdTime': 0,
            'cookSetTime': 0,
            'cookTemp': 0,
            'mode': 'AirFry',
            'currentRemainingTime': 0,
            'totalTimeRemaining': 0,
            'chamber': 1,
        },
        {
            'cookStatus': 'standby',
            'startTime': 0,
            'recipeType': 3,
            'recipeId': 14,
            'recipeName': '',
            'upc': '',
            'holdTime': 0,
            'cookSetTime': 0,
            'cookTemp': 0,
            'mode': 'AirFry',
            'currentRemainingTime': 0,
            'totalTimeRemaining': 0,
            'chamber': 2,
        },
    ],
    'tempUnit': 'c',
    'syncType': 0,
    'workChamber': 0,
}


STATUS_READY = {
    'statusList': [
        {
            'cookStatus': 'ready',
            'startTime': 0,
            'recipeType': 3,
            'recipeId': 14,
            'recipeName': 'Air Fry',
            'upc': '',
            'holdTime': 0,
            'cookSetTime': 300,
            'cookTemp': 180,
            'mode': 'AirFry',
            'currentRemainingTime': 300,
            'totalTimeRemaining': 300,
            'chamber': 1,
        },
        {
            'cookStatus': 'standby',
            'startTime': 0,
            'recipeType': 3,
            'recipeId': 14,
            'recipeName': '',
            'upc': '',
            'holdTime': 0,
            'cookSetTime': 0,
            'cookTemp': 0,
            'mode': 'AirFry',
            'currentRemainingTime': 0,
            'totalTimeRemaining': 0,
            'chamber': 2,
        },
    ],
    'tempUnit': 'c',
    'syncType': 0,
    'workChamber': 1,
}


DETAILS_RESPONSES = {
    SETUP_ENTRY: bypass_response(STATUS_STANDBY),
}


METHOD_RESPONSES: defaultdict[str, dict[str, tuple[dict[str, Any], int]]] = (
    defaultdict(dict)
)

METHOD_RESPONSES[SETUP_ENTRY]['get_details'] = bypass_response(STATUS_STANDBY)
METHOD_RESPONSES[SETUP_ENTRY]['prepare_program'] = bypass_response()
METHOD_RESPONSES[SETUP_ENTRY]['stop_chamber'] = bypass_response()
