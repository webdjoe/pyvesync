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
    current = 0.5  # amps
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
    "ESW03": {
        "activeTime": TestDefaults.active_time,
        "deviceName": "ESW03",
        "deviceStatus": OutletDefaults.device_status.value,
        "power": str(OutletDefaults.power),
        "voltage": str(OutletDefaults.voltage),
        "energy": OutletDefaults.energy,
        "connectionStatus": OutletDefaults.connection_status.value,
    },
    "ESW10-USA": {
        "id": 0,
        "enabled": bool(OutletDefaults.device_status),
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
        "channelNum": 1,
        "powerSwitch_1": 1,
        "realTimeVoltage": OutletDefaults.voltage,
        "realTimePower": OutletDefaults.power,
        "electricalEnergy": OutletDefaults.energy,
        "voltageUpperThreshold": 280,
        "voltageUnderThreshold": 75,
        "protectionStatus": "normal",
        "currentUpperThreshold": 16,
    },
    "WHOGPLUG": {
        "enabled": True,
        "voltage": OutletDefaults.voltage,
        "energy": OutletDefaults.energy,
        "power": OutletDefaults.power,
        "current": OutletDefaults.current,
        "highestVoltage": 240,
        "voltagePtStatus": False,
    },
}


DETAILS_RESPONSES = {
    "wifi-switch-1.3": OUTLET_DETAILS["wifi-switch-1.3"],
    "ESW03": build_bypass_v1_response(result_dict=OUTLET_DETAILS["ESW03"]),
    "ESW10-USA": build_bypass_v2_response(inner_result=OUTLET_DETAILS["ESW10-USA"]),
    "ESW15-USA": build_bypass_v1_response(result_dict=OUTLET_DETAILS["ESW15-USA"]),
    "ESO15-TB": build_bypass_v1_response(result_dict=OUTLET_DETAILS["ESO15-TB"]),
    "BSDOG01": build_bypass_v2_response(inner_result=OUTLET_DETAILS["BSDOG01"]),
    "WHOGPLUG": build_bypass_v2_response(inner_result=OUTLET_DETAILS["WHOGPLUG"]),
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

WHOPLUG_ENERGY_HISTORY_COMMON = {
    "energyInfos": [
        {"timestamp": 1697673600, "energy": 0.06002924054861},
        {"timestamp": 1697587200, "energy": 0.03776630222797},
        {"timestamp": 1697500800, "energy": 0.00002495583819},
        {"timestamp": 1697414400, "energy": 0.00038652237961},
        {"timestamp": 1697328000, "energy": 0},
        {"timestamp": 1697241600, "energy": 0},
        {"timestamp": 1697155200, "energy": 0},
    ],
    "total": 7,
}

WHOPLUG_YEAR_ENERGY_HISTORY = {
    "ELECConsumeList": [
        {"month": "2022-11", "ELECConsume": 0},
        {"month": "2022-12", "ELECConsume": 0},
        {"month": "2023-01", "ELECConsume": 0},
        {"month": "2023-02", "ELECConsume": 0},
        {"month": "2023-03", "ELECConsume": 0},
        {"month": "2023-04", "ELECConsume": 0},
        {"month": "2023-05", "ELECConsume": 0},
        {"month": "2023-06", "ELECConsume": 0},
        {"month": "2023-07", "ELECConsume": 0},
        {"month": "2023-08", "ELECConsume": 0},
        {"month": "2023-09", "ELECConsume": 0},
        {"month": "2023-10", "ELECConsume": 0.0281},
    ]
}

METHOD_RESPONSES = {
    "wifi-switch-1.3": defaultdict(lambda: None),
    "ESW10-USA": deepcopy(FunctionResponsesV2),
    "ESW03": deepcopy(FunctionResponses),
    "ESW15-USA": deepcopy(FunctionResponsesV1),
    "ESO15-TB": deepcopy(FunctionResponsesV1),
    "BSDOG01": deepcopy(FunctionResponsesV2),
    "WHOGPLUG": deepcopy(FunctionResponsesV2),
}

for k in METHOD_RESPONSES:
    if k in ["ESW10-USA"]:
        METHOD_RESPONSES[k]["get_weekly_energy"] = None
        METHOD_RESPONSES[k]["get_monthly_energy"] = None
        METHOD_RESPONSES[k]["get_yearly_energy"] = None
    elif k in ["BSDOG01", "WHOGPLUG"]:
        METHOD_RESPONSES[k]["get_weekly_energy"] = build_bypass_v2_response(
            inner_result=WHOPLUG_ENERGY_HISTORY_COMMON
        )
        METHOD_RESPONSES[k]["get_monthly_energy"] = build_bypass_v2_response(
            inner_result=WHOPLUG_ENERGY_HISTORY_COMMON
        )
        METHOD_RESPONSES[k]["get_yearly_energy"] = build_bypass_v1_response(
            result_dict=WHOPLUG_YEAR_ENERGY_HISTORY
        )
    else:
        METHOD_RESPONSES[k]["get_weekly_energy"] = ENERGY_HISTORY
        METHOD_RESPONSES[k]["get_monthly_energy"] = ENERGY_HISTORY
        METHOD_RESPONSES[k]["get_yearly_energy"] = ENERGY_HISTORY
