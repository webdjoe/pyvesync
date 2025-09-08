"""
Air Purifier Device API Responses

FANS variable is a list of device types

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
        lambda: ({"code": 0, "msg": "success"}, 200))
    )
}

# For a function to handle the response
def status_response(request_body=None):
    # do work with request_body
    return request_body, 200

METHOD_RESPONSES['DEV_TYPE']['set_status'] = status_response

# To change the default value for a device type

METHOD_RESPONSES['DEVTYPE'].default_factory = lambda: ({"code": 0, "msg": "success"}, 200)
"""

from copy import deepcopy
from typing import Any
from pyvesync.device_map import purifier_modules
from pyvesync.const import ConnectionStatus, PurifierModes, DeviceStatus, AirQualityLevel
from defaults import (
    TestDefaults,
    FunctionResponses,
    build_bypass_v2_response,
    build_bypass_v1_response,
    FunctionResponsesV1,
    FunctionResponsesV2,
)


PURIFIER_MODELS = [m.setup_entry for m in purifier_modules]
# FANS = ['Core200S', 'Core300S', 'Core400S', 'Core600S', 'LV-PUR131S', 'LV600S',
#         'Classic300S', 'Classic200S', 'Dual200S', 'LV600S']
PURIFIERS_NUM = len(PURIFIER_MODELS)


class PurifierDefaults:
    purifier_mode = PurifierModes.MANUAL.value
    air_quality_enum = AirQualityLevel.GOOD
    fan_level = 1
    fan_set_level = 2
    filter_life = 80
    humidity = 50
    night_light = DeviceStatus.ON
    display = DeviceStatus.ON
    display_config = DeviceStatus.ON
    display_forever = True
    light_detection = False
    light_detected = True
    child_lock = DeviceStatus.ON
    air_quality_level = 1
    filter_open = 0
    aq_percent = 75
    air_quality_value_pm25 = 3
    pm1 = 10
    pm10 = 5
    rotate_angle = 45
    voc = 120
    co2 = 669
    temperature = 791


PURIFIER_DETAILS: dict[str, dict[str, Any]] = {
    "Core200S": {
        "enabled": True,
        "filter_life": PurifierDefaults.filter_life,
        "mode": PurifierDefaults.purifier_mode,
        "level": PurifierDefaults.fan_level,
        "air_quality": PurifierDefaults.air_quality_enum.value,
        "air_quality_value": PurifierDefaults.air_quality_value_pm25,
        "display": bool(PurifierDefaults.display),
        "child_lock": bool(PurifierDefaults.child_lock),
        "configuration": {
            "display": bool(PurifierDefaults.display_config),
            "display_forever": PurifierDefaults.display_forever,
            "auto_preference": {"type": "default", "room_size": 0},
        },
        "extension": {"schedule_count": 0, "timer_remain": 0},
        "device_error_code": 0,
    },
    "Core300S": {
        "enabled": True,
        "filter_life": PurifierDefaults.filter_life,
        "mode": PurifierDefaults.purifier_mode,
        "level": PurifierDefaults.fan_level,
        "air_quality": PurifierDefaults.air_quality_enum.value,
        "air_quality_value": PurifierDefaults.air_quality_value_pm25,
        "display": bool(PurifierDefaults.display),
        "child_lock": bool(PurifierDefaults.child_lock),
        "configuration": {
            "display": bool(PurifierDefaults.display_config),
            "display_forever": PurifierDefaults.display_forever,
            "auto_preference": {"type": "default", "room_size": 0},
        },
        "extension": {"schedule_count": 0, "timer_remain": 0},
        "device_error_code": 0,
    },
    "Core400S": {
        "enabled": True,
        "filter_life": PurifierDefaults.filter_life,
        "mode": PurifierDefaults.purifier_mode,
        "level": PurifierDefaults.fan_level,
        "air_quality": PurifierDefaults.air_quality_enum.value,
        "air_quality_value": PurifierDefaults.air_quality_value_pm25,
        "display": bool(PurifierDefaults.display),
        "child_lock": bool(PurifierDefaults.child_lock),
        "configuration": {
            "display": bool(PurifierDefaults.display_config),
            "display_forever": PurifierDefaults.display_forever,
            "auto_preference": {"type": "default", "room_size": 0},
        },
        "extension": {"schedule_count": 0, "timer_remain": 0},
        "device_error_code": 0,
    },
    "Core600S": {
        "enabled": True,
        "filter_life": PurifierDefaults.filter_life,
        "mode": PurifierDefaults.purifier_mode,
        "level": PurifierDefaults.fan_level,
        "air_quality": PurifierDefaults.air_quality_enum.value,
        "air_quality_value": PurifierDefaults.air_quality_value_pm25,
        "display": bool(PurifierDefaults.display),
        "child_lock": bool(PurifierDefaults.child_lock),
        "configuration": {
            "display": bool(PurifierDefaults.display_config),
            "display_forever": PurifierDefaults.display_forever,
            "auto_preference": {"type": "default", "room_size": 0},
        },
        "extension": {"schedule_count": 0, "timer_remain": 0},
        "device_error_code": 0,
    },
    "LV-PUR131S": {
        "screenStatus": PurifierDefaults.display.value,
        "filterLife": {
            "change": False,
            "useHour": 3520,
            "percent": PurifierDefaults.filter_life,
        },
        "activeTime": TestDefaults.active_time,
        "timer": None,
        "scheduleCount": 0,
        "schedule": None,
        "levelNew": PurifierDefaults.fan_set_level,
        "airQuality": str(PurifierDefaults.air_quality_enum),
        "level": PurifierDefaults.fan_level,
        "mode": PurifierDefaults.purifier_mode,
        "deviceName": "Levoit 131S Air Purifier",
        "currentFirmVersion": "2.0.58",
        "childLock": PurifierDefaults.child_lock.value,
        "deviceStatus": DeviceStatus.ON.value,
        "deviceImg": "https://image.vesync.com/defaultImages/deviceDefaultImages/airpurifier131_240.png",
        "connectionStatus": ConnectionStatus.ONLINE.value,
    },
    "LAP-V102S": {  # Vital 100S
        "powerSwitch": int(DeviceStatus.ON),
        "filterLifePercent": PurifierDefaults.filter_life,
        "workMode": PurifierDefaults.purifier_mode,
        "manualSpeedLevel": PurifierDefaults.fan_set_level,
        "fanSpeedLevel": PurifierDefaults.fan_level,
        "AQLevel": int(PurifierDefaults.air_quality_enum),
        "PM25": PurifierDefaults.air_quality_value_pm25,
        "screenState": int(PurifierDefaults.display),
        "childLockSwitch": int(PurifierDefaults.child_lock),
        "screenSwitch": int(PurifierDefaults.display_config),
        "lightDetectionSwitch": int(PurifierDefaults.light_detection),
        "environmentLightState": int(PurifierDefaults.light_detected),
        "autoPreference": {"autoPreferenceType": "default", "roomSize": 600},
        "scheduleCount": 0,
        "timerRemain": 0,
        "efficientModeTimeRemain": 0,
        "errorCode": 0,
    },
    "LAP-V201S": {  # Vital 200S
        "powerSwitch": int(DeviceStatus.ON),
        "filterLifePercent": PurifierDefaults.filter_life,
        "workMode": PurifierDefaults.purifier_mode,
        "manualSpeedLevel": PurifierDefaults.fan_set_level,
        "fanSpeedLevel": PurifierDefaults.fan_level,
        "AQLevel": PurifierDefaults.air_quality_enum.value,
        "PM25": PurifierDefaults.air_quality_value_pm25,
        "screenState": PurifierDefaults.display,
        "childLockSwitch": PurifierDefaults.child_lock,
        "screenSwitch": PurifierDefaults.display_config,
        "lightDetectionSwitch": PurifierDefaults.light_detection,
        "environmentLightState": PurifierDefaults.light_detected,
        "autoPreference": {"autoPreferenceType": "default", "roomSize": 0},
        "scheduleCount": 0,
        "timerRemain": 0,
        "efficientModeTimeRemain": 0,
        "sleepPreference": {
            "sleepPreferenceType": "default",
            "cleaningBeforeBedSwitch": 1,
            "cleaningBeforeBedSpeedLevel": 3,
            "cleaningBeforeBedMinutes": 5,
            "whiteNoiseSleepAidSwitch": 1,
            "whiteNoiseSleepAidSpeedLevel": 1,
            "whiteNoiseSleepAidMinutes": 45,
            "duringSleepSpeedLevel": 5,
            "duringSleepMinutes": 480,
            "afterWakeUpPowerSwitch": 1,
            "afterWakeUpWorkMode": "auto",
            "afterWakeUpFanSpeedLevel": 1,
        },
        "errorCode": 0,
    },
    "EL551S": {  # Everest Air
        "fanRotateAngle": PurifierDefaults.rotate_angle,
        "filterOpenState": PurifierDefaults.filter_open,
        "powerSwitch": int(DeviceStatus.ON),
        "filterLifePercent": PurifierDefaults.filter_life,
        "workMode": PurifierDefaults.purifier_mode,
        "manualSpeedLevel": PurifierDefaults.fan_set_level,
        "fanSpeedLevel": PurifierDefaults.fan_level,
        "AQLevel": PurifierDefaults.air_quality_enum.value,
        "AQPercent": PurifierDefaults.aq_percent,
        "PM25": PurifierDefaults.air_quality_value_pm25,
        "PM1": PurifierDefaults.pm1,
        "PM10": PurifierDefaults.pm10,
        "screenState": int(PurifierDefaults.display),
        "childLockSwitch": int(PurifierDefaults.child_lock),
        "screenSwitch": int(PurifierDefaults.display_config),
        "lightDetectionSwitch": int(PurifierDefaults.light_detection),
        "environmentLightState": int(PurifierDefaults.light_detected),
        "autoPreference": {"autoPreferenceType": "default", "roomSize": 0},
        "routine": {"routineType": "normal", "runSeconds": 0},
        "scheduleCount": 0,
        "timerRemain": 0,
        "efficientModeTimeRemain": 0,
        "ecoModeRunTime": 0,
        "errorCode": 0,
    },
    "LAP-B851S-WUS": {
        "traceId": TestDefaults.trace_id,
        "code": 0,
        "msg": "request success",
        "module": None,
        "stacktrace": None,
        "result": {
            "traceId": TestDefaults.trace_id,
            "code": 0,
            "result": {
                "powerSwitch": TestDefaults.bin_toggle,
                "workMode": "auto",
                "manualSpeedLevel": PurifierDefaults.fan_level,
                "fanSpeedLevel": PurifierDefaults.fan_set_level,
                "PM25": PurifierDefaults.air_quality_value_pm25,
                "PM1": PurifierDefaults.pm1,
                "PM10": PurifierDefaults.pm10,
                "screenState": int(PurifierDefaults.display),
                "childLockSwitch": int(PurifierDefaults.child_lock),
                "screenSwitch": int(PurifierDefaults.display_config),
                "lampType": 0,
                "roomSize": 242,
                "lampSwitch": int(PurifierDefaults.display),
                "autoPreference": {"autoPreferenceType": "default", "roomSize": 630},
                "scheduleCount": 0,
                "timerRemain": 0,
                "efficientModeTimeRemain": 1182,
                "humidity": PurifierDefaults.humidity,
                "AQI": PurifierDefaults.aq_percent,
                "AQLevel": PurifierDefaults.air_quality_level,
                "VOC": PurifierDefaults.voc,
                "CO2": PurifierDefaults.co2,
                "temperature": PurifierDefaults.temperature,
                "nightLight": {
                    "nightLightSwitch": int(PurifierDefaults.night_light),
                    "brightness": TestDefaults.brightness,
                    "colorTemperature": TestDefaults.color_temp_k,
                },
                "breathingLamp": {
                    "breathingLampSwitch": TestDefaults.bin_toggle,
                    "colorTemperature": TestDefaults.color_temp_k,
                    "timeInterval": 5,
                    "brightnessStart": 10,
                    "brightnessEnd": 90,
                },
                "errorCode": 0,
                "dumpedState": 0,
                "whiteNoiseInfo": {
                    "playStatus": 0,
                    "soundId": 100006,
                    "countDown": 1800,
                    "countingDown": 1800,
                    "downloadStatus": 2,
                },
                "guardingInfo": {"guarding": 0, "remainTS": 100},
            },
        },
    },
}


DETAILS_RESPONSES = {
    "LV-PUR131S": build_bypass_v1_response(result_dict=PURIFIER_DETAILS["LV-PUR131S"]),
    "Core200S": build_bypass_v2_response(inner_result=PURIFIER_DETAILS["Core200S"]),
    "Core300S": build_bypass_v2_response(inner_result=PURIFIER_DETAILS["Core300S"]),
    "Core400S": build_bypass_v2_response(inner_result=PURIFIER_DETAILS["Core400S"]),
    "Core600S": build_bypass_v2_response(inner_result=PURIFIER_DETAILS["Core600S"]),
    "LAP-V102S": build_bypass_v2_response(inner_result=PURIFIER_DETAILS["LAP-V102S"]),
    "LAP-V201S": build_bypass_v2_response(inner_result=PURIFIER_DETAILS["LAP-V201S"]),
    "EL551S": build_bypass_v2_response(inner_result=PURIFIER_DETAILS["EL551S"]),
    "LAP-B851S-WUS": build_bypass_v2_response(inner_result=PURIFIER_DETAILS["LAP-B851S-WUS"]),
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
    "LV-PUR131S": deepcopy(FunctionResponsesV1),
    "Core200S": deepcopy(FunctionResponsesV2),
    "Core300S": deepcopy(FunctionResponsesV2),
    "Core400S": deepcopy(FunctionResponsesV2),
    "Core600S": deepcopy(FunctionResponsesV2),
    "LAP-V102S": deepcopy(FunctionResponsesV2),
    "LAP-V201S": deepcopy(FunctionResponsesV2),
    "EL551S": deepcopy(FunctionResponsesV2),
    "LAP-B851S-WUS": deepcopy(FunctionResponsesV2),
}

# Add responses for methods with different responses than the default

# # Timer Responses

# for k in AIR_MODELS:
#     METHOD_RESPONSES[k]["set_timer"] = (INNER_RESULT({"id": 1}), 200)
#     METHOD_RESPONSES[k]["get_timer"] = (
#         INNER_RESULT({"id": 1, "remain": 100, "total": 100, "action": "off"}),
#         200,
#     )
# FAN_TIMER = helpers.Timer(100, "off")
