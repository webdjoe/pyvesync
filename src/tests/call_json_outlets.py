"""
Outlet Device API Responses

OUTLET variable is a list of device types

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

### For a function to handle the response
def status_response(request_kwargs=None):
    # do work with request_kwargs
    return request_body, 200

METHOD_RESPONSES['DEV_TYPE']['set_status'] = status_response

### To change the default value for a device type

METHOD_RESPONSES['DEVTYPE'].default_factory = lambda: ({"code": 0, "msg": "success"}, 200)

If changing default response for all devices, change the default factory of the import
default dict but make sure to use `deepcopy` to avoid unintended side effects.
"""

from copy import deepcopy
from collections import defaultdict
from pyvesync.const import (
    DeviceStatus,
    ConnectionStatus,
    NightlightModes,
    NightlightStatus,
)
from pyvesync.device_map import outlet_modules
from defaults import (
    FunctionResponses,
    TestDefaults,
    build_bypass_v1_response,
    build_bypass_v2_response,
    FunctionResponsesV1,
    FunctionResponsesV2,
)

OUTLETS = [m.setup_entry for m in outlet_modules]
OUTLETS_NUM = len(OUTLETS)


class OutletDefaults:
    device_status = DeviceStatus.ON
    connection_status = ConnectionStatus.ONLINE
    night_light_status = NightlightStatus.ON
    night_light_mode = NightlightModes.AUTO
    voltage = 120  # volts
    energy = 10  # kilowatt
    power = 20  # kilowatt-hours
    round_7a_voltage = "78000:78000"  # 120 Volts
    round_7a_power = "1000:1000"  # 1 watt


OUTLET_DETAILS: dict[str, dict] = {
    "wifi-switch-1.3": {
        "deviceStatus": OutletDefaults.device_status.value,
        "deviceImg": "https://image.vesync.com/defaultImages/deviceDefaultImages/7aoutlet_240.png",
        "energy": OutletDefaults.energy,
        "activeTime": TestDefaults.active_time,
        "power": OutletDefaults.round_7a_power,
        "voltage": OutletDefaults.round_7a_voltage,
    },
    "ESW03-USA": {
        "code": 0,
        "msg": None,
        "deviceStatus": OutletDefaults.device_status.value,
        "connectionStatus": OutletDefaults.connection_status.value,
        "activeTime": TestDefaults.active_time,
        "energy": OutletDefaults.energy,
        "nightLightStatus": None,
        "nightLightBrightness": None,
        "nightLightAutomode": None,
        "power": OutletDefaults.power,
        "voltage": OutletDefaults.voltage,
    },
    "ESW01-EU": {
        "code": 0,
        "msg": None,
        "deviceStatus": OutletDefaults.device_status.value,
        "connectionStatus": OutletDefaults.connection_status.value,
        "activeTime": TestDefaults.active_time,
        "energy": OutletDefaults.energy,
        "nightLightStatus": None,
        "nightLightBrightness": None,
        "nightLightAutomode": None,
        "power": OutletDefaults.power,
        "voltage": OutletDefaults.voltage,
    },
    "ESW15-USA": {  # V1
        "activeTime": TestDefaults.active_time,
        "deviceName": "Etekcity 15A WiFi Outlet US/CA",
        "deviceStatus": OutletDefaults.device_status.value,
        "power": OutletDefaults.power,
        "voltage": OutletDefaults.voltage,
        "energy": OutletDefaults.energy,
        "nightLightStatus": OutletDefaults.night_light_status.value,
        "nightLightAutomode": OutletDefaults.night_light_mode.value,
        "nightLightBrightness": 50,
        "deviceImg": "https://image.vesync.com/defaultImages/deviceDefaultImages/15aoutletnightlight_240.png",
        "connectionStatus": OutletDefaults.connection_status.value,
    },
    "ESO15-TB": {
        "activeTime": TestDefaults.active_time,
        "deviceName": "Etekcity Outdoor Plug",
        "deviceStatus": OutletDefaults.device_status.value,
        "power": OutletDefaults.power,
        "voltage": OutletDefaults.voltage,
        "energy": OutletDefaults.energy,
        "subDevices": [
            {
                "subDeviceNo": 1,
                "defaultName": "Socket A",
                "subDeviceName": "Socket A",
                "subDeviceImg": "",
                "subDeviceStatus": OutletDefaults.device_status.value,
            },
            {
                "subDeviceNo": 2,
                "defaultName": "Socket B",
                "subDeviceName": "Socket B",
                "subDeviceImg": "",
                "subDeviceStatus": OutletDefaults.device_status.value,
            },
        ],
        "deviceImg": "",
        "connectionStatus": OutletDefaults.connection_status.value,
    },
    "BSDOG01": {
        "powerSwitch_1": int(OutletDefaults.device_status),
        "active_time": TestDefaults.active_time,
        "connectionStatus": OutletDefaults.connection_status.value,
        "code": 0,
    },
}


DETAILS_RESPONSES = {
    "wifi-switch-1.3": OUTLET_DETAILS["wifi-switch-1.3"],
    "ESW03-USA": OUTLET_DETAILS["ESW03-USA"],
    "ESW01-EU": OUTLET_DETAILS["ESW01-EU"],
    "ESW15-USA": build_bypass_v1_response(result_dict=OUTLET_DETAILS["ESW15-USA"]),
    "ESO15-TB": build_bypass_v1_response(result_dict=OUTLET_DETAILS["ESO15-TB"]),
    "BSDOG01": build_bypass_v2_response(inner_result=OUTLET_DETAILS["BSDOG01"]),
}


ENERGY_HISTORY = {
    "traceId": TestDefaults.trace_id,
    "code": 0,
    "msg": "request success",
    "module": None,
    "stacktrace": None,
    "result": {
        "energyConsumptionOfToday": 1,
        "costPerKWH": 0.50,
        "maxEnergy": 0.7,
        "totalEnergy": 2.0,
        "totalMoney": 1.0,
        "averageEnergy": 0.01,
        "averageMoney": 0.0,
        "maxCost": 35.0,
        "energySavingStatus": "off",
        "currency": "USD",
        "energyInfos": [
            {"timestamp": 1742184000025, "energyKWH": 0.0015, "money": 0.0},
            {"timestamp": 1742270400025, "energyKWH": 0.0016, "money": 0.0},
            {"timestamp": 1742356800025, "energyKWH": 0.0017, "money": 0.0},
        ],
    },
}


METHOD_RESPONSES = {
    "wifi-switch-1.3": defaultdict(lambda: None),
    "ESW03-USA": deepcopy(FunctionResponses),
    "ESW01-EU": deepcopy(FunctionResponses),
    "ESW15-USA": deepcopy(FunctionResponsesV1),
    "ESO15-TB": deepcopy(FunctionResponsesV1),
    "BSDOG01": deepcopy(FunctionResponsesV2),
}

for k in METHOD_RESPONSES:
    METHOD_RESPONSES[k]["get_weekly_energy"] = ENERGY_HISTORY
    METHOD_RESPONSES[k]["get_monthly_energy"] = ENERGY_HISTORY
    METHOD_RESPONSES[k]["get_yearly_energy"] = ENERGY_HISTORY

# # Add BSDGO1 specific responses
# METHOD_RESPONSES['BSDOG01'] = defaultdict(lambda: ({
#     "code": 0,
#     "msg": "request success",
#     "result": {
#         "traceId": Defaults.trace_id,
#         "code": 0
#     }
# }, 200))
