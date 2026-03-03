"""
Air Fryer Device API Responses

AIR_FRYER variable is a list of device types

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
    'CS158-AF': defaultdict(
        lambda: ({"code": 0, "msg": "success"}, 200))
    )
}

# For a function to handle the response
def status_response(request_body=None):
    # do work with request_body
    return request_body, 200

METHOD_RESPONSES['CS158-AF']['set_cook_mode'] = status_response

# To change the default value for a device type

METHOD_RESPONSES['CS158-AF'].default_factory = lambda: ({"code": 0, "msg": "success"}, 200)

"""

from copy import deepcopy
from pyvesync.device_map import air_fryer_modules
from pyvesync.const import (
    # DeviceStatus,
    # ConnectionStatus,
    AirFryerPresetRecipe,
    TemperatureUnits,
    AirFryerCookStatus,
)
from defaults import (
    TestDefaults,
    FunctionResponsesV2,
    FunctionResponsesV1,
)

FRYERS = [m.setup_entry for m in air_fryer_modules]
FRYERS_NUM = len(FRYERS)


class AirFryerDefaults:
    temp_unit = TemperatureUnits.FAHRENHEIT
    cook_time_m = 10
    cook_time_s = cook_time_m * 60
    cook_last_time_m = cook_time_m - 2
    cook_last_time_s = cook_last_time_m * 60
    preheat_time_m = 5
    preheat_time_s = preheat_time_m * 60
    cook_temp_f = 350
    cook_temp_c = 175
    cook_mode = "custom"
    current_temp_f = 150
    cook_status = AirFryerCookStatus.COOKING
    recipe = "Manual"


DC601_RECIPE = AirFryerPresetRecipe(
    recipe_name="Air Fry",
    cook_mode="AirFry",
    recipe_id=14,
    recipe_type=3,
    target_temp=AirFryerDefaults.cook_temp_f,
    temp_unit=AirFryerDefaults.temp_unit,
    cook_time=AirFryerDefaults.cook_time_s,
    preheat_time=AirFryerDefaults.preheat_time_s,
)


AIR_FRYER_COOKING_DETAILS: dict[str, dict[str, list | str | float | dict | None]] = {
    "CS158-AF": {
        "returnStatus": {
            "curentTemp": AirFryerDefaults.current_temp_f,
            "cookSetTemp": AirFryerDefaults.cook_temp_f,
            "mode": AirFryerDefaults.cook_mode,
            "cookSetTime": AirFryerDefaults.cook_time_m,  # Minutes
            "cookLastTime": AirFryerDefaults.cook_last_time_m,  # Minutes
            "cookStatus": AirFryerDefaults.cook_status.value,
            "tempUnit": AirFryerDefaults.temp_unit.label,
            "accountId": TestDefaults.account_id,
            "customRecipe": AirFryerDefaults.recipe,
        }
    },
    "CAF-DC601S": {
        "traceId": "1767318172645",
        "code": 0,
        "result": {
            "stepArray": [
                {
                    "cookSetTime": AirFryerDefaults.cook_time_s,  # Seconds
                    "cookTemp": AirFryerDefaults.cook_temp_f,
                    "mode": DC601_RECIPE.cook_mode,
                    "cookLastTime": AirFryerDefaults.cook_last_time_s,  # Seconds
                    "shakeTime": 0,
                    "cookEndTime": 0,
                    "recipeName": DC601_RECIPE.recipe_name,
                    "recipeId": DC601_RECIPE.recipe_id,
                    "recipeType": DC601_RECIPE.recipe_type,
                }
            ],
            "cookMode": "normal",
            "tempUnit": AirFryerDefaults.temp_unit.label,
            "stepIndex": 0,
            "cookStatus": AirFryerDefaults.cook_status.value,
            "preheatSetTime": 0,
            "preheatLastTime": 0,
            "preheatEndTime": 0,
            "preheatTemp": 0,
            "startTime": 1767318116,
            "totalTimeRemaining": 1176,
            "currentTemp": 89,
            "shakeStatus": 0,
        },
    },
}

AIR_FRYER_STANDYBY_DETAILS: dict[str, dict[str, list | str | float | dict | None]] = {
    "CAF-DC601S": {
        "stepArray": [],
        "cookMode": "normal",
        "tempUnit": AirFryerDefaults.temp_unit.label,
        "stepIndex": 0,
        "cookStatus": "standby",
        "preheatSetTime": 0,
        "preheatLastTime": 0,
        "preheatEndTime": 0,
        "preheatTemp": 0,
        "startTime": 0,
        "totalTimeRemaining": 0,
        "currentTemp": 43,
        "shakeStatus": 0,
    },
    "CS158-AF": {"returnStatus": {"cookStatus": "standby"}},
}


METHOD_RESPONSES = {
    'CS158-AF': deepcopy(FunctionResponsesV1),
    'CAF-DC601S': deepcopy(FunctionResponsesV2),
}


DETAILS_RESPONSES_COOKING = {
    "CS158-AF": deepcopy(AIR_FRYER_COOKING_DETAILS['CS158-AF']),
    "CAF-DC601S": deepcopy(AIR_FRYER_COOKING_DETAILS['CAF-DC601S']),
}


DETAILS_RESPONSES_STANDBY = {
    "CS158-AF": deepcopy(AIR_FRYER_STANDYBY_DETAILS['CS158-AF']),
    "CAF-DC601S": deepcopy(AIR_FRYER_STANDYBY_DETAILS['CAF-DC601S']),
}
