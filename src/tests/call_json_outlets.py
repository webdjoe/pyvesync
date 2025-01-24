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
from utils import FunctionResponses, Defaults
from pyvesync.vesyncoutlet import outlet_modules

OUTLETS = outlet_modules.keys()
OUTLETS_NUM = len(OUTLETS)

# OUTLETS = ['wifi-switch-1.3', 'ESW03-USA', 'ESW01-EU', 'ESW15-USA', 'ESO15-TB']


class OutletDefaults:
    voltage = 1  # volts
    energy = 1  # kilowatt-hours
    power = 1  # kilowatt
    round_7a_voltage = '1000:1000'  # 1 volt
    round_7a_power = '1000:1000'  # 1 watt


class OutletDetails:
    details_15a = (
        {
            'code': 0,
            'msg': None,
            'deviceStatus': 'on',
            'connectionStatus': 'online',
            'activeTime': Defaults.active_time,
            'energy': 1,
            'nightLightStatus': 'on',
            'nightLightBrightness': 50,
            'nightLightAutomode': 'manual',
            'power': '1',
            'voltage': '1',
        },
        200,
    )

    details_7a = (
        {
            'deviceStatus': 'on',
            'deviceImg': '',
            'activeTime': Defaults.active_time,
            'energy': OutletDefaults.energy,
            'power': OutletDefaults.round_7a_power,
            'voltage': OutletDefaults.round_7a_voltage,
        },
        200,
    )

    details_10a = (
        {
            'code': 0,
            'msg': None,
            'deviceStatus': 'on',
            'connectionStatus': 'online',
            'activeTime': Defaults.active_time,
            'energy': OutletDefaults.energy,
            'nightLightStatus': None,
            'nightLightBrightness': None,
            'nightLightAutomode': None,
            'power': OutletDefaults.power,
            'voltage': OutletDefaults.voltage,
        },
        200,
    )

    details_outdoor = (
        {
            'code': 0,
            'msg': None,
            'connectionStatus': 'online',
            'activeTime': Defaults.active_time,
            'energy': OutletDefaults.energy,
            'power': OutletDefaults.power,
            'voltage': OutletDefaults.voltage,
            'deviceStatus': 'on',
            'deviceName': Defaults.name('ESO15-TB'),
            'subDevices': [
                {
                    'subDeviceNo': 1,
                    'defaultName': 'Socket A',
                    'subDeviceName': Defaults.name('ESO15-TB'),
                    'subDeviceStatus': 'on',
                },
                {
                    'subDeviceNo': 2,
                    'defaultName': 'Socket B',
                    'subDeviceName': Defaults.name('ESO15-TB'),
                    'subDeviceStatus': 'on',
                },
            ],
        },
        200,
    )

    bsdgo1_details = ({
        "code": 0,
        "msg": "request success",
        "result": {
            "powerSwitch_1": 1,
            "traceId": "1735308365651",
            "active_time": Defaults.active_time,
            "connectionStatus": "online",
            "code": 0
        }
    }, 200)

    wysmtod16a_details = ({
        "code": 0,
        "msg": "request success",
        "result": {
            "code": 0,
            "traceId": "1735308365651",
            "result": {
                "code": 0,
                "powerSwitch_1": 1,
            }
        }
    }, 200)


DETAILS_RESPONSES = {
    'wifi-switch-1.3': OutletDetails.details_7a,
    'ESW03-USA': OutletDetails.details_10a,
    'ESW01-EU': OutletDetails.details_10a,
    'ESW15-USA': OutletDetails.details_15a,
    'ESO15-TB': OutletDetails.details_outdoor,
    'BSDOG01': OutletDetails.bsdgo1_details,
    'WYSMTOD16A': OutletDetails.wysmtod16a_details,
}

ENERGY_HISTORY = (
    {
        'code': 0,
        'msg': 'request success',
        'energyConsumptionOfToday': 1,
        'costPerKWH': 1,
        'maxEnergy': 1,
        'totalEnergy': 1,
        'data': [
            1,
            1,
        ],
    },
    200,
)


METHOD_RESPONSES = {k: deepcopy(FunctionResponses) for k in OUTLETS}

for k in METHOD_RESPONSES:
    METHOD_RESPONSES[k]['get_weekly_energy'] = ENERGY_HISTORY
    METHOD_RESPONSES[k]['get_monthly_energy'] = ENERGY_HISTORY
    METHOD_RESPONSES[k]['get_yearly_energy'] = ENERGY_HISTORY

# Add BSDGO1 specific responses
METHOD_RESPONSES['BSDOG01'] = defaultdict(lambda: ({
    "code": 0,
    "msg": "request success",
    "result": {
        "traceId": Defaults.trace_id,
        "code": 0
    }
}, 200))

# Add WYSMTOD16A specific responses
METHOD_RESPONSES['WYSMTOD16A'] = defaultdict(lambda: ({
    "code": 0,
    "msg": "request success",
    "result": {
        "traceId": Defaults.trace_id,
        "code": 0
    }
}, 200))
