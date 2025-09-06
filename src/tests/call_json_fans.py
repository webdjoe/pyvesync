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
from defaults import TestDefaults, FunctionResponses, build_bypass_v2_response, FunctionResponsesV2
from pyvesync.const import FanModes

FANS = [m.setup_entry for m in fan_modules]
FANS_NUM = len(FANS)


class FanDefaults:
    fan_mode = FanModes.NORMAL
    fan_level = 1
    fan_speed_level = 1
    temperature_fan = 750


FAN_DETAILS: dict[str, dict] = {
    "LTF-F422S": {
        "powerSwitch": TestDefaults.bin_toggle,
        "workMode": FanModes.NORMAL.value,
        "manualSpeedLevel": FanDefaults.fan_level,
        "fanSpeedLevel": FanDefaults.fan_speed_level,
        "screenState": TestDefaults.bin_toggle,
        "screenSwitch": TestDefaults.bin_toggle,
        "oscillationSwitch": TestDefaults.bin_toggle,
        "oscillationState": TestDefaults.bin_toggle,
        "muteSwitch": TestDefaults.bin_toggle,
        "muteState": TestDefaults.bin_toggle,
        "timerRemain": 0,
        "temperature": FanDefaults.temperature_fan,
        "sleepPreference": {
            "sleepPreferenceType": "default",
            "oscillationSwitch": TestDefaults.bin_toggle,
            "initFanSpeedLevel": 0,
            "fallAsleepRemain": 0,
            "autoChangeFanLevelSwitch": TestDefaults.bin_toggle,
        },
        "scheduleCount": 0,
        "displayingType": 0,
        "errorCode": 0,
    }
}
"""Contains the result dictionary of the device response details for fans.

Dictionary with key being the `setup_entry` attribute for each fan device
found in the `pyvesync.device_map.fan_modules` object. The value is the
return dictionary for a successful `fan.update()` API request.
"""

DETAILS_RESPONSES = {
    "LTF-F422S": build_bypass_v2_response(inner_result=FAN_DETAILS["LTF-F422S"]),

}


FunctionResponses.default_factory = lambda: (
    {
        "traceId": TestDefaults.trace_id,
        "code": 0,
        "msg": "request success",
        "result": {"traceId": TestDefaults.trace_id, "code": 0},
    }
)

METHOD_RESPONSES = {
    "LTF-F422S": deepcopy(FunctionResponsesV2)
}
"""Default responses for device methods.

This dictionary maps the setup_entry to the default response for that device.

Examples:
    - For legacy API responses `defaults.FunctionResponses`
    - For Bypass V1 `defaults.FunctionResponsesV1`
    - For Bypass V2 `defaults.FunctionResponsesV2`
"""

# Add responses for methods with different responses than the default
