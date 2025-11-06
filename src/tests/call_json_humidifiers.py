"""
Air Purifier and Humidifier Device API Responses

FANS variable is a list of setup_entry's from the device_map

DETAILS_RESPONSES variable is a dictionary of responses from the API
for get_details() methods.  The keys are the device types and the
values are the responses.  The responses are tuples of (response, status)

METHOD_RESPONSES variable is a defaultdict of responses from the API. This is
the FunctionResponse variable from the utils module in the tests dir.
The default response is a tuple with the value ({"code": 0, "msg": "success"}, 200).

The values of METHOD_RESPONSES can be a function that takes a single argument or
a static value. The value is checked if callable at runtime and if so, it is called
with the provided argument. If not callable, the value is returned as is.

METHOD_RESPONSES = {
    'DEV_TYPE': defaultdict(
        lambda: {"code": 0, "msg": "success"}
    )
}

# For a function to handle the response
def status_response(request_body=None):
    # do work with request_body
    return request_body, 200

METHOD_RESPONSES['DEV_TYPE']['set_status'] = status_response

# To change the default value for a device type

METHOD_RESPONSES['DEVTYPE'].default_factory = lambda: {"code": 0, "msg": "success"}
"""
from typing import Any
from copy import deepcopy

from pyvesync.device_map import humidifier_modules
from pyvesync.const import DRYING_MODES, HumidifierModes, DeviceStatus, ConnectionStatus, DryingModes
from defaults import TestDefaults, FunctionResponses, build_bypass_v2_response, FunctionResponsesV2

HUMIDIFIERS = [m.setup_entry for m in humidifier_modules]
HUMIDIFIERS_NUM = len(HUMIDIFIERS)


class HumidifierDefaults:
    device_status = DeviceStatus.ON
    connection_status = ConnectionStatus.ONLINE
    humidifier_mode = HumidifierModes.MANUAL
    nightlight_status = DeviceStatus.ON
    drying_state = DryingModes.RUNNING
    drying_mode_switch = DeviceStatus.ON
    nightlight_brightness = 50
    humidity = 50
    target_humidity = 60
    mist_level = 3
    virtual_mist_level = 3
    warm_mist_level = 1
    warm_mist_enabled = True
    water_lacks = False
    water_tank_lifted = False
    auto_stop = False
    auto_stop_reached = False
    display = True
    display_config = True
    humidity_high = False


HUMIDIFIER_DETAILS: dict[str, Any] = {
    "Classic300S": {
        "enabled": bool(HumidifierDefaults.device_status),
        "humidity": HumidifierDefaults.humidity,
        "mist_virtual_level": HumidifierDefaults.virtual_mist_level,
        "mist_level": HumidifierDefaults.mist_level,
        "mode": HumidifierDefaults.humidifier_mode.value,
        "water_lacks": HumidifierDefaults.water_lacks,
        "humidity_high": HumidifierDefaults.humidity_high,
        "water_tank_lifted": HumidifierDefaults.water_tank_lifted,
        "display": HumidifierDefaults.display,
        "automatic_stop_reach_target": HumidifierDefaults.auto_stop_reached,
        "night_light_brightness": HumidifierDefaults.nightlight_brightness,
        "configuration": {
            "auto_target_humidity": HumidifierDefaults.target_humidity,
            "display": HumidifierDefaults.display_config,
            "automatic_stop": HumidifierDefaults.auto_stop,
        },
    },
    "Classic200S": {
        "enabled": bool(HumidifierDefaults.device_status),
        "humidity": HumidifierDefaults.humidity,
        "mist_virtual_level": HumidifierDefaults.virtual_mist_level,
        "mist_level": HumidifierDefaults.mist_level,
        "mode": HumidifierDefaults.humidifier_mode.value,
        "water_lacks": HumidifierDefaults.water_lacks,
        "humidity_high": HumidifierDefaults.humidity_high,
        "water_tank_lifted": HumidifierDefaults.water_tank_lifted,
        "display": HumidifierDefaults.display,
        "automatic_stop_reach_target": HumidifierDefaults.auto_stop_reached,
        "configuration": {
            "auto_target_humidity": HumidifierDefaults.target_humidity,
            "display": HumidifierDefaults.display_config,
            "automatic_stop": HumidifierDefaults.auto_stop,
        },
    },
    "Dual200S": {
        "enabled": bool(HumidifierDefaults.device_status),
        "humidity": HumidifierDefaults.humidity,
        "mist_virtual_level": HumidifierDefaults.virtual_mist_level,
        "mist_level": HumidifierDefaults.mist_level,
        "mode": HumidifierDefaults.humidifier_mode.value,
        "water_lacks": HumidifierDefaults.water_lacks,
        "humidity_high": HumidifierDefaults.humidity_high,
        "water_tank_lifted": HumidifierDefaults.water_tank_lifted,
        "display": HumidifierDefaults.display,
        "automatic_stop_reach_target": HumidifierDefaults.auto_stop_reached,
        "night_light_brightness": HumidifierDefaults.nightlight_brightness,
        "configuration": {
            "auto_target_humidity": HumidifierDefaults.target_humidity,
            "display": HumidifierDefaults.display_config,
            "automatic_stop": HumidifierDefaults.auto_stop,
        },
    },
    "LUH-A602S-WUS": {  # LV600S
        "enabled": bool(HumidifierDefaults.device_status),
        "humidity": HumidifierDefaults.humidity,
        "mist_virtual_level": HumidifierDefaults.virtual_mist_level,
        "mist_level": HumidifierDefaults.mist_level,
        "mode": HumidifierDefaults.humidifier_mode.value,
        "water_lacks": HumidifierDefaults.water_lacks,
        "humidity_high": HumidifierDefaults.humidity_high,
        "water_tank_lifted": HumidifierDefaults.water_tank_lifted,
        "display": HumidifierDefaults.display,
        "automatic_stop_reach_target": HumidifierDefaults.auto_stop_reached,
        "night_light_brightness": HumidifierDefaults.nightlight_brightness,
        "warm_mist_level": HumidifierDefaults.warm_mist_level,
        "warm_mist_enabled": HumidifierDefaults.warm_mist_enabled,
        "configuration": {
            "auto_target_humidity": HumidifierDefaults.target_humidity,
            "display": HumidifierDefaults.display_config,
            "automatic_stop": HumidifierDefaults.auto_stop,
        },
    },
    "LUH-O451S-WUS": {
        "enabled": bool(HumidifierDefaults.device_status),
        "mist_virtual_level": HumidifierDefaults.virtual_mist_level,
        "mist_level": HumidifierDefaults.mist_level,
        "mode": HumidifierDefaults.humidifier_mode.value,
        "water_lacks": HumidifierDefaults.water_lacks,
        "water_tank_lifted": HumidifierDefaults.water_tank_lifted,
        "humidity": HumidifierDefaults.humidity,
        "humidity_high": HumidifierDefaults.humidity_high,
        "display": HumidifierDefaults.display,
        "warm_enabled": HumidifierDefaults.warm_mist_enabled,
        "warm_level": HumidifierDefaults.warm_mist_level,
        "automatic_stop_reach_target": HumidifierDefaults.auto_stop_reached,
        "configuration": {
            "auto_target_humidity": HumidifierDefaults.target_humidity,
            "display": HumidifierDefaults.display_config,
            "automatic_stop": HumidifierDefaults.auto_stop,
        },
        "extension": {"schedule_count": 0, "timer_remain": 0},
    },
    "LUH-O451S-WEU": {
        "enabled": bool(HumidifierDefaults.device_status),
        "mist_virtual_level": HumidifierDefaults.virtual_mist_level,
        "mist_level": HumidifierDefaults.mist_level,
        "mode": HumidifierDefaults.humidifier_mode.value,
        "water_lacks": HumidifierDefaults.water_lacks,
        "water_tank_lifted": HumidifierDefaults.water_tank_lifted,
        "humidity": HumidifierDefaults.humidity,
        "humidity_high": HumidifierDefaults.humidity_high,
        "display": HumidifierDefaults.display,
        "warm_enabled": HumidifierDefaults.warm_mist_enabled,
        "warm_level": HumidifierDefaults.warm_mist_level,
        "automatic_stop_reach_target": HumidifierDefaults.auto_stop_reached,
        "configuration": {
            "auto_target_humidity": HumidifierDefaults.target_humidity,
            "display": HumidifierDefaults.display_config,
            "automatic_stop": HumidifierDefaults.auto_stop,
        },
        "extension": {"schedule_count": 0, "timer_remain": 0},
    },
    "LUH-M101-WUS": {
            "powerSwitch": int(HumidifierDefaults.device_status),
            "humidity": int(HumidifierDefaults.humidity),
            "targetHumidity": int(HumidifierDefaults.target_humidity),
            "virtualLevel": int(HumidifierDefaults.virtual_mist_level),
            "mistLevel": int(HumidifierDefaults.mist_level),
            "workMode": HumidifierDefaults.humidifier_mode.value,
            "waterLacksState": int(HumidifierDefaults.water_lacks),
            "waterTankLifted": int(HumidifierDefaults.water_tank_lifted),
            "autoStopSwitch": int(HumidifierDefaults.auto_stop),
            "autoStopState": int(HumidifierDefaults.auto_stop_reached),
            "screenSwitch": int(HumidifierDefaults.display_config),
            "screenState": int(HumidifierDefaults.display),
            "scheduleCount": 0,
            "timerRemain": 0,
            "errorCode": 0
        },
    "LUH-M101S-WEUR": {
        "powerSwitch": int(DeviceStatus.ON),
        "humidity": HumidifierDefaults.humidity,
        "targetHumidity": HumidifierDefaults.target_humidity,
        "virtualLevel": HumidifierDefaults.virtual_mist_level,
        "mistLevel": HumidifierDefaults.mist_level,
        "workMode": HumidifierDefaults.humidifier_mode.value,
        "waterLacksState": int(HumidifierDefaults.water_lacks),
        "waterTankLifted": int(HumidifierDefaults.water_tank_lifted),
        "autoStopSwitch": int(HumidifierDefaults.auto_stop),
        "autoStopState": int(HumidifierDefaults.auto_stop_reached),
        "screenSwitch": int(HumidifierDefaults.display_config),
        "screenState": int(HumidifierDefaults.display),
        "nightLight": {
            "nightLightSwitch": 0,
            "brightness": HumidifierDefaults.nightlight_brightness,
        },
        "scheduleCount": 0,
        "timerRemain": 0,
        "errorCode": 0,
    },
    "LEH-S601S": {
        "powerSwitch": int(DeviceStatus.ON),
        "humidity": HumidifierDefaults.humidity,
        "targetHumidity": HumidifierDefaults.target_humidity,
        "virtualLevel": HumidifierDefaults.virtual_mist_level,
        "mistLevel": HumidifierDefaults.mist_level,
        "workMode": HumidifierDefaults.humidifier_mode.value,
        "waterLacksState": int(HumidifierDefaults.water_lacks),
        "waterTankLifted": int(HumidifierDefaults.water_tank_lifted),
        "autoStopSwitch": int(HumidifierDefaults.auto_stop),
        "autoStopState": int(HumidifierDefaults.auto_stop_reached),
        "screenSwitch": int(HumidifierDefaults.display_config),
        "screenState": int(HumidifierDefaults.display),
        "scheduleCount": 0,
        "timerRemain": 0,
        "errorCode": 0,
        "dryingMode": {
            "dryingLevel": 1,
            "autoDryingSwitch": int(HumidifierDefaults.drying_mode_switch),
            "dryingState": DRYING_MODES[HumidifierDefaults.drying_state],
            "dryingRemain": 7200,
        },
        "autoPreference": 1,
        "childLockSwitch": 0,
        "filterLifePercent": 93,
        "temperature": 662,
    },
}
"""This dictionary contains the details response for each humidifier.

It stores the innermost result that is passed to the DETAILS_RESPONSE variable where
the full API response is built."""


DETAILS_RESPONSES = {
    "Classic300S": build_bypass_v2_response(inner_result=HUMIDIFIER_DETAILS["Classic300S"]),
    "Classic200S": build_bypass_v2_response(inner_result=HUMIDIFIER_DETAILS["Classic200S"]),
    "Dual200S": build_bypass_v2_response(inner_result=HUMIDIFIER_DETAILS["Dual200S"]),
    "LUH-A602S-WUS": build_bypass_v2_response(inner_result=HUMIDIFIER_DETAILS["LUH-A602S-WUS"]),
    "LUH-O451S-WUS": build_bypass_v2_response(inner_result=HUMIDIFIER_DETAILS["LUH-O451S-WUS"]),
    "LUH-O451S-WEU": build_bypass_v2_response(inner_result=HUMIDIFIER_DETAILS["LUH-O451S-WEU"]),
    "LUH-M101S-WEUR": build_bypass_v2_response(inner_result=HUMIDIFIER_DETAILS["LUH-M101S-WEUR"]),
    "LUH-M101S-WUS": build_bypass_v2_response(inner_result=HUMIDIFIER_DETAILS["LUH-M101-WUS"]),
    "LEH-S601S": build_bypass_v2_response(inner_result=HUMIDIFIER_DETAILS["LEH-S601S"]),
}


FunctionResponses.default_factory = lambda: (
    {
        "traceId": TestDefaults.trace_id,
        "code": 0,
        "msg": "request success",
        "result": {"traceId": TestDefaults.trace_id, "code": 0},
    },
    200,
)

METHOD_RESPONSES = {
    "Classic300S": deepcopy(FunctionResponsesV2),
    "Classic200S": deepcopy(FunctionResponsesV2),
    "Dual200S": deepcopy(FunctionResponsesV2),
    "LUH-A602S-WUS": deepcopy(FunctionResponsesV2),
    "LUH-O451S-WUS": deepcopy(FunctionResponsesV2),
    "LUH-O451S-WEU": deepcopy(FunctionResponsesV2),
    "LUH-M101S-WEUR": deepcopy(FunctionResponsesV2),
    "LUH-M101S-WUS": deepcopy(FunctionResponsesV2),
    "LEH-S601S": deepcopy(FunctionResponsesV2),
}


# Add responses for methods with different responses than the default

# Timer Responses

# for k in AIR_MODELS:
#     METHOD_RESPONSES[k]["set_timer"] = (INNER_RESULT({"id": 1}), 200)
#     METHOD_RESPONSES[k]["get_timer"] = (
#         INNER_RESULT({"id": 1, "remain": 100, "total": 100, "action": "off"}),
#         200,
#     )
# FAN_TIMER = helpers.Timer(100, "off")
