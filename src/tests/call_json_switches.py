"""
Switch Device API Responses

SWITCHES variable is a list of device types

DETAILS_RESPONSES variable is a dictionary of responses from the API
for get_details() methods.  The keys are the device types and the
values are the responses.  The responses are tuples of (response, status)

METHOD_RESPONSES variable is a defaultdict of responses from the API. This is
the FunctionResponse variable from the utils module in the tests dir.
The default response is a tuple with the value {"code": 0, "msg": "success"}.

"""
from copy import deepcopy
from pyvesync import vesyncswitch
from utils import FunctionResponses, Defaults

SWITCHES = vesyncswitch.switch_classes.keys()
SWITCHES_NUM = len(SWITCHES)


class SwitchDetails:
    details_ws = {
        'code': 0,
        'msg': None,
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'activeTime': Defaults.active_time,
        'power': 'None',
        'voltage': 'None',
    }

    details_eswd16 = {
        "code": 0,
        "msg": "请求成功",
        "traceId": Defaults.trace_id,
        "indicatorlightStatus": "on",
        "timer": None,
        "schedule": None,
        "brightness": "100",
        "startMode": None,
        "activeTime": Defaults.active_time,
        "rgbStatus": "on",
        "rgbValue": {
            "red": Defaults.color.rgb.red,
            "blue": Defaults.color.rgb.blue,
            "green": Defaults.color.rgb.green
        },
        "connectionStatus": "online",
        "devicename": Defaults.name('ESWD16'),
        "deviceStatus": "on"
    }


DETAILS_RESPONSES = {
    'ESWL01': SwitchDetails.details_ws,
    'ESWL03': SwitchDetails.details_ws,
    'ESWD16': SwitchDetails.details_eswd16,
}

METHOD_RESPONSES = {k: deepcopy(FunctionResponses) for k in SWITCHES}
