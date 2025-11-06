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
from pyvesync.device_map import fan_modules
from pyvesync.const import DeviceStatus
from defaults import (
    build_bypass_v2_response,
    FunctionResponsesV2,
)
from pyvesync.const import FanModes

FANS = [m.setup_entry for m in fan_modules]
FANS_NUM = len(FANS)


class FanDefaults:
    fan_status = DeviceStatus.ON
    screen_status = DeviceStatus.ON
    oscillation_status = DeviceStatus.ON
    oscillation_horizontal = DeviceStatus.ON
    oscillation_vertical = DeviceStatus.ON
    mute_status = DeviceStatus.ON
    child_lock = DeviceStatus.OFF
    fan_mode = FanModes.NORMAL
    yaw = 45
    pitch = 90
    top = 120
    bottom = 0
    left = 0
    right = 90
    fan_level = 1
    fan_speed_level = 1
    temperature_fan = 75.0


FAN_DETAILS: dict[str, dict] = {
    "LTF-F422S": {
        "powerSwitch": int(FanDefaults.fan_status),
        "workMode": FanModes.NORMAL.value,
        "manualSpeedLevel": FanDefaults.fan_level,
        "fanSpeedLevel": FanDefaults.fan_speed_level,
        "screenState": int(FanDefaults.screen_status),
        "screenSwitch": int(FanDefaults.screen_status),
        "oscillationSwitch": int(FanDefaults.oscillation_status),
        "oscillationState": int(FanDefaults.oscillation_status),
        "muteSwitch": int(FanDefaults.mute_status),
        "muteState": int(FanDefaults.mute_status),
        "timerRemain": 0,
        "temperature": FanDefaults.temperature_fan,
        "sleepPreference": {
            "sleepPreferenceType": "default",
            "oscillationSwitch": int(FanDefaults.oscillation_status),
            "initFanSpeedLevel": 0,
            "fallAsleepRemain": 0,
            "autoChangeFanLevelSwitch": int(FanDefaults.fan_status),
        },
        "scheduleCount": 0,
        "displayingType": 0,
        "errorCode": 0,
    },
    "LPF-R423S": {
        "powerSwitch": int(FanDefaults.fan_status),
        "workMode": FanDefaults.fan_mode.value,
        "fanSpeedLevel": FanDefaults.fan_speed_level,
        "scheduleCount": 0,
        "timerRemain": 0,
        "sleepPreference": {
            "sleepPreferenceType": "default",
            "oscillationState": int(FanDefaults.oscillation_status),
            "initFanSpeedLevel": 0,
            "fallAsleepRemain": 0,
        },
        "temperature": FanDefaults.temperature_fan * 10,
        "muteState": int(FanDefaults.mute_status),
        "muteSwitch": int(FanDefaults.mute_status),
        "screenState": int(FanDefaults.screen_status),
        "screenSwitch": int(FanDefaults.screen_status),
        "errorCode": 0,
        "horizontalOscillationState": int(FanDefaults.oscillation_horizontal),
        "verticalOscillationState": int(FanDefaults.oscillation_vertical),
        "childLock": FanDefaults.child_lock,
        "oscillationCoordinate": {"yaw": FanDefaults.yaw, "pitch": FanDefaults.pitch},
        "oscillationRange": {
            "left": FanDefaults.left,
            "right": FanDefaults.right,
            "top": FanDefaults.top,
            "bottom": FanDefaults.bottom,
        },
        "highTemperatureReminderState": 1,
        "highTemperature": 806,
        "smartCleaningReminderState": 1,
        "oscillationCalibrationState": 0,
        "oscillationCalibrationProgress": 0,
        "levelMemory": [
            {"workMode": "normal", "level": 2, "enable": 1},
            {"workMode": "turbo", "level": 12, "enable": 0},
            {"workMode": "eco", "level": 3, "enable": 1},
            {"workMode": "advancedSleep", "level": 3, "enable": 1},
        ],
        "horizontalOscillationDemo": 0,
        "verticalOscillationDemo": 0,
        "isSupportSetOnceOscillation": 1,
        "isTimerSupportPowerOn": 1,
        "isSupportSetRelativeCoordinate": 1,
    },
}
"""Contains the result dictionary of the device response details for fans.

Dictionary with key being the `setup_entry` attribute for each fan device
found in the `pyvesync.device_map.fan_modules` object. The value is the
return dictionary for a successful `fan.update()` API request.
"""

DETAILS_RESPONSES = {
    "LTF-F422S": build_bypass_v2_response(inner_result=FAN_DETAILS["LTF-F422S"]),
    "LPF-R423S": build_bypass_v2_response(inner_result=FAN_DETAILS["LPF-R423S"]),
}


METHOD_RESPONSES = {
    "LTF-F422S": deepcopy(FunctionResponsesV2),
    "LPF-R423S": deepcopy(FunctionResponsesV2)
}
"""Default responses for device methods.

This dictionary maps the setup_entry to the default response for that device.

Examples:
    - For legacy API responses `defaults.FunctionResponses`
    - For Bypass V1 `defaults.FunctionResponsesV1`
    - For Bypass V2 `defaults.FunctionResponsesV2`
"""

# Add responses for methods with different responses than the default
