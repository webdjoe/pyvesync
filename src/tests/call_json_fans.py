"""
Air Purifier and Humidifier Device API Responses

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
from pyvesync import vesyncfan, helpers
from defaults import Defaults, FunctionResponses

HUMID_MODELS = []
for model_type, model_dict in vesyncfan.humid_features.items():
    HUMID_MODELS.append(model_dict["models"][0])

AIR_MODELS = []
for model_type, model_dict in vesyncfan.air_features.items():
    AIR_MODELS.append(model_dict["models"][0])

FANS = HUMID_MODELS + AIR_MODELS
FANS_NUM = len(FANS)
# FANS = ['Core200S', 'Core300S', 'Core400S', 'Core600S', 'LV-PUR131S', 'LV600S',
#         'Classic300S', 'Classic200S', 'Dual200S', 'LV600S']


def INNER_RESULT(inner: dict) -> dict:
    return {
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "request success",
        "module": None,
        "stacktrace": None,
        "result": {"traceId": Defaults.trace_id, "code": 0, "result": inner},
    }


class FanDefaults:
    fan_level = 1
    filter_life = 80
    humidity = 50
    mist_level = 3
    warm_mist_level = 2
    air_quality = 3
    air_quality_value = 4
    filter_open = 0
    aq_percent = 75
    pm1 = 10
    pm10 = 5
    rotate_angle = 45


class FanDetails:
    details_air = ({
        "code": 0,
        "msg": None,
        "deviceStatus": "on",
        "connectionStatus": "online",
        "activeTime": Defaults.active_time,
        "deviceImg": None,
        "deviceName": "LV-PUR131S-NAME",
        "filterLife": {
            "change": False,
            "useHour": None,
            "percent": FanDefaults.filter_life,
        },
        "airQuality": "excellent",
        "screenStatus": "on",
        "mode": "manual",
        "level": FanDefaults.fan_level,
        "schedule": None,
        "timer": None,
        "scheduleCount": 0,
    }, 200)

    details_lv600s = ({
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "请求成功",
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": {
                "enabled": True,
                "humidity": FanDefaults.humidity,
                "mist_virtual_level": 8,
                "mist_level": FanDefaults.mist_level,
                "mode": "manual",
                "water_lacks": False,
                "humidity_high": False,
                "water_tank_lifted": False,
                "display": False,
                "automatic_stop_reach_target": True,
                "night_light_brightness": 0,
                "warm_mist_level": 0,
                "warm_mist_enabled": False,
                "configuration": {
                    "auto_target_humidity": 50,
                    "display": False,
                    "automatic_stop": True,
                },
            },
        },
    }, 200)

    details_classic200s300s = ({
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "请求成功",
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": {
                "enabled": True,
                "humidity": FanDefaults.humidity,
                "mist_virtual_level": 8,
                "mist_level": FanDefaults.mist_level,
                "mode": "manual",
                "water_lacks": False,
                "humidity_high": False,
                "water_tank_lifted": False,
                "display": False,
                "automatic_stop_reach_target": True,
                "night_light_brightness": 0,
                "configuration": {
                    "auto_target_humidity": 50,
                    "display": False,
                    "automatic_stop": True,
                },
            },
        },
    }, 200)

    details_oasismist1000S = ({
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "request success",
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": {
                "powerSwitch": 0,
                "humidity": FanDefaults.humidity,
                "targetHumidity": 50,
                "virtualLevel": 1,
                "mistLevel": FanDefaults.mist_level,
                "workMode": "manual",
                "waterLacksState": 0,
                "waterTankLifted": 0,
                "autoStopSwitch": 1,
                "autoStopState": 0,
                "screenSwitch": 1,
                "screenState": 0,
                "scheduleCount": 0,
                "timerRemain": 0,
                "errorCode": 0,
            },
        },
    }, 200)

    details_core = ({

        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "request success",
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": {
                "enabled": True,
                "filter_life": FanDefaults.filter_life,
                "mode": "manual",
                "level": FanDefaults.fan_level,
                "air_quality": FanDefaults.air_quality,
                "air_quality_value": FanDefaults.air_quality_value,
                "display": True,
                "child_lock": True,
                "configuration": {
                    "display": True,
                    "display_forever": True,
                    "auto_preference": {"type": "default", "room_size": 0},
                },
                "extension": {"schedule_count": 0, "timer_remain": 0},
                "device_error_code": 0,
            },
        },
    }, 200)

    details_vital100s = ({
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "request success",
        "module": None,
        "stacktrace": None,
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": {
                "powerSwitch": Defaults.bin_toggle,
                "filterLifePercent": FanDefaults.filter_life,
                "workMode": "manual",
                "manualSpeedLevel": FanDefaults.fan_level,
                "fanSpeedLevel": FanDefaults.fan_level,
                "AQLevel": FanDefaults.air_quality,
                "PM25": FanDefaults.air_quality_value,
                "screenState": Defaults.bin_toggle,
                "childLockSwitch": Defaults.bin_toggle,
                "screenSwitch": Defaults.bin_toggle,
                "lightDetectionSwitch": Defaults.bin_toggle,
                "environmentLightState": Defaults.bin_toggle,
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
        },
    }, 200)

    details_superior6000S = ({
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "request success",
        "module": None,
        "stacktrace": None,
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": {
                "powerSwitch": 1,
                "humidity": 44,
                "targetHumidity": 50,
                "virtualLevel": 1,
                "mistLevel": 1,
                "workMode": "manual",
                "waterLacksState": 0,
                "waterTankLifted": 0,
                "autoStopSwitch": 1,
                "autoStopState": 0,
                "screenSwitch": 1,
                "screenState": 1,
                "scheduleCount": 0,
                "timerRemain": 0,
                "errorCode": 0,
                "dryingMode": {
                    "dryingLevel": 1,
                    "autoDryingSwitch": 1,
                    "dryingState": 2,
                    "dryingRemain": 7200,
                },
                "autoPreference": 1,
                "childLockSwitch": 0,
                "filterLifePercent": 93,
                "temperature": 662,
            },
        },
    }, 200)

    details_everest = ({
        "traceId": "1691789977402",
        "code": 0,
        "msg": "request success",
        "module": None,
        "stacktrace": None,
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": {
                "fanRotateAngle": FanDefaults.rotate_angle,
                "filterOpenState": FanDefaults.filter_open,
                "powerSwitch": Defaults.bin_toggle,
                "filterLifePercent": FanDefaults.filter_life,
                "workMode": "auto",
                "manualSpeedLevel": FanDefaults.fan_level,
                "fanSpeedLevel": FanDefaults.fan_level,
                "AQLevel": FanDefaults.air_quality,
                "AQPercent": FanDefaults.aq_percent,
                "PM25": FanDefaults.air_quality_value,
                "PM1": FanDefaults.pm1,
                "PM10": FanDefaults.pm10,
                "screenState": Defaults.bin_toggle,
                "childLockSwitch": Defaults.bin_toggle,
                "screenSwitch": Defaults.bin_toggle,
                "lightDetectionSwitch": Defaults.bin_toggle,
                "environmentLightState": Defaults.bin_toggle,
                "autoPreference": {"autoPreferenceType": "default", "roomSize": 0},
                "routine": {"routineType": "normal", "runSeconds": 0},
                "scheduleCount": 0,
                "timerRemain": 0,
                "efficientModeTimeRemain": 0,
                "ecoModeRunTime": 0,
                "errorCode": 0,
            },
        },
    }, 200)

    details_towerfan42 = ({
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "request success",
        "module": None,
        "stacktrace": None,
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": {
                "powerSwitch": Defaults.bin_toggle,
                "workMode": "turbo",
                "manualSpeedLevel": 3,
                "fanSpeedLevel": 12,
                "screenState": Defaults.bin_toggle,
                "screenSwitch": Defaults.bin_toggle,
                "oscillationSwitch": Defaults.bin_toggle,
                "oscillationState": Defaults.bin_toggle,
                "muteSwitch": Defaults.bin_toggle,
                "muteState": Defaults.bin_toggle,
                "timerRemain": 0,
                "temperature": 750,
                "sleepPreference": {
                  "sleepPreferenceType": "default",
                  "oscillationSwitch": Defaults.bin_toggle,
                  "initFanSpeedLevel": 0,
                  "fallAsleepRemain": 0,
                  "autoChangeFanLevelSwitch": Defaults.bin_toggle
                },
                "scheduleCount": 0,
                "displayingType": 0,
                "errorCode": 0,
            }
        },
    }, 200)


DETAILS_RESPONSES = {
    "LV-PUR131S": FanDetails.details_air,
    "Classic300S": FanDetails.details_classic200s300s,
    "Classic200S": FanDetails.details_classic200s300s,
    "Dual200S": FanDetails.details_classic200s300s,
    "LUH-A602S-WUSR": FanDetails.details_lv600s,
    "Core200S": FanDetails.details_core,
    "Core300S": FanDetails.details_core,
    "Core400S": FanDetails.details_core,
    "Core600S": FanDetails.details_core,
    "LUH-O451S-WEU": FanDetails.details_lv600s,
    "LUH-O451S-WUS": FanDetails.details_lv600s,
    "LAP-V201S-AASR": FanDetails.details_vital100s,
    "LAP-V102S-AASR": FanDetails.details_vital100s,
    "LUH-M101S-WUS": FanDetails.details_oasismist1000S,
    "LEH-S601S-WUS": FanDetails.details_superior6000S,
    "LAP-EL551S-AUS": FanDetails.details_everest,
    "LTF-F422S-KEU": FanDetails.details_towerfan42,
}

FunctionResponses.default_factory = lambda: (
    {
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "request success",
        "result": {"traceId": Defaults.trace_id, "code": 0},
    },
    200,
)

METHOD_RESPONSES = {k: deepcopy(FunctionResponses) for k in FANS}

# Add responses for methods with different responses than the default

# Timer Responses

for k in AIR_MODELS:
    METHOD_RESPONSES[k]["set_timer"] = (INNER_RESULT({"id": 1}), 200)
    METHOD_RESPONSES[k]["get_timer"] = (
        INNER_RESULT({"id": 1, "remain": 100, "total": 100, "action": "off"}),
        200,
    )
FAN_TIMER = helpers.Timer(100, "off")
