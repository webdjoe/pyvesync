"""
Thermostat Device API Responses

THERMOSTATS variable is a list of setup_entry's from the device_map

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
from copy import deepcopy
from pyvesync.device_map import thermostat_modules
from pyvesync.const import ThermostatConst
from defaults import (
    build_bypass_v2_response,
    FunctionResponsesV2,
)

THERMOSTATS = [m.setup_entry for m in thermostat_modules]
THERMOSTATS_NUM = len(THERMOSTATS)


class ThermostatDefaults:
    current_temp = 65
    target_temp = 75
    humidity = 45
    work_mode = ThermostatConst.WorkMode.HEAT
    work_status = ThermostatConst.WorkStatus.HEATING
    eco_mode = ThermostatConst.EcoType.BALANCE
    temp_unit = "f"
    schedule_enabled = "on"
    away_mode = "off"
    child_lock = "off"
    screen_display = "on"
    outdoor_temp = 600
    outdoor_humidity = 300
    filter_life = 100
    battery_level = 100
    hvac_state = "idle"
    compressor_state = "off"
    fan_state = "off"
    fan_speed = "auto"
    fan_speed_level = 1
    swing_mode = "off"
    aux_heat_state = "off"


THERMOSTAT_DETAILS: dict[str, dict] = {
    "LTM-A401S-WUS": {
        "supportMode": [0, 1, 2, 3, 5],
        "workMode": 3,
        "workStatus": 2,
        "fanMode": 1,
        "fanStatus": 1,
        "routineRunningId": 2,
        "tempUnit": "f",
        "temperature": 75.570000,
        "humidity": 56,
        "heatToTemp": 60,
        "coolToTemp": 70,
        "lockStatus": False,
        "scheduleOrHold": 2,
        "holdEndTime": 1696033274,
        "holdOption": 5,
        "deadband": 4,
        "safetyTempLow": "40.00",
        "safetyTempHigh": "100.00",
        "ecoType": 3,
        "alertStatus": 2,
        "routines": [
            {"name": "Home", "routineId": 2},
            {"name": "Away", "routineId": 1},
            {"name": "Sleep", "routineId": 3},
        ],
    },
}
"""Dictionary with setup_entry as the key and the value being the result object of
the device response from the get_details API for thermostats."""


DEVICE_DETAILS = {
    "LTM-A401S-WUS": build_bypass_v2_response(inner_result=THERMOSTAT_DETAILS["LTM-A401S-WUS"]),
}

METHOD_RESPONSES = {
    "LTM-A401S-WUS": deepcopy(FunctionResponsesV2)
}
