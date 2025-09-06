"""
Light Bulbs Device API Responses

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
    'ESL100': defaultdict(
        lambda: ({"code": 0, "msg": "success"}, 200))
    )
}

# For a function to handle the response
def status_response(request_body=None):
    # do work with request_body
    return request_body, 200

METHOD_RESPONSES['ESL100']['set_status'] = status_response

# To change the default value for a device type

METHOD_RESPONSES['XYD0001'].default_factory = lambda: ({"code": 0, "msg": "success"}, 200)

"""
from copy import deepcopy
from pyvesync.device_map import bulb_modules
from pyvesync.const import DeviceStatus, ConnectionStatus
from defaults import (
    TestDefaults,
    FunctionResponsesV2,
    FunctionResponsesV1,
    build_bypass_v1_response,
    build_bypass_v2_response,
)

# BULBS = ['ESL100', 'ESL100CW', 'ESL100MC', 'XYD0001']
BULBS = [m.setup_entry for m in bulb_modules]
BULBS_NUM = len(BULBS)


BULB_DETAILS: dict[str, dict[str, str | float | dict | None]] = {
    "ESL100": {
        "deviceName": "Dimmable",
        "name": "Dimmable",
        "brightNess": str(TestDefaults.brightness),
        "deviceStatus": DeviceStatus.ON.value,
        "activeTime": TestDefaults.active_time,
        "defaultDeviceImg": "",
        "timer": None,
        "scheduleCount": 0,
        "away": None,
        "schedule": None,
        "ownerShip": "1",
        "deviceImg": "",
        "connectionStatus": ConnectionStatus.ONLINE.value,
    },
    "ESL100CW": {
        "light": {
            "action": DeviceStatus.ON.value,
            "brightness": TestDefaults.brightness,
            "colorTempe": TestDefaults.color_temp,
        }
    },
    "ESL100MC": {
        "action": DeviceStatus.ON.value,
        "brightness": TestDefaults.brightness,
        "colorMode": "color",
        "speed": 0,
        "red": TestDefaults.color.rgb.red,
        "green": TestDefaults.color.rgb.green,
        "blue": TestDefaults.color.rgb.blue,
    },
    "XYD0001": {
        "enabled": DeviceStatus.ON.value,
        "colorMode": "color",
        "brightness": TestDefaults.brightness,
        "colorTemp": TestDefaults.color_temp,
        "hue": TestDefaults.color.hsv.hue * 27.7778,
        "saturation": TestDefaults.color.hsv.saturation * 100,
        "value": TestDefaults.color.hsv.value,
    },
}

# class BulbDetails:
#     details_esl100 = ({
#         'code': 0,
#         'msg': None,
#         'deviceStatus': 'on',
#         'connectionStatus': 'online',
#         'name': Defaults.name('ESL100'),
#         'brightNess': Defaults.brightness,
#         'timer': None,
#         'away': None,
#         'schedule': None,
#         'ownerShip': '1',
#         'scheduleCount': 0,
#     }, 200)

#     details_esl100cw = {
# 		"light": {
# 			"action": "off",
# 			"brightness": 4,
# 			"colorTempe": 50
# 		}
# 	}

#     details_esl100mc = ({
#         "traceId": Defaults.trace_id,
#         "code": 0,
#         "msg": "request success",
#         "result": {
#             "traceId": Defaults.trace_id,
#             "code": 0,
#             "result": {
#                 "action": "on",
#                 "brightness": Defaults.brightness,
#                 "colorMode": "color",
#                 "speed": 0,
#                 "red": Defaults.color.rgb.red,
#                 "green": Defaults.color.rgb.green,
#                 "blue": Defaults.color.rgb.blue,
#             }
#         }
#     }, 200)

#     details_valceno = (
#             {
#                 "traceId": TRACE_ID,
#                 "code": 0,
#                 "msg": "request success",
#                 "result": {
#                     "traceId": TRACE_ID,
#                     "code": 0,
#                     "result": {
#                         "enabled": "on",
#                         "colorMode": "color",
#                         "brightness": Defaults.brightness,
#                         "colorTemp": Defaults.color_temp,
#                         "hue": Defaults.color.hsv.hue*27.7778,
#                         "saturation": Defaults.color.hsv.saturation*100,
#                         "value": Defaults.color.hsv.value,
#                     }
#                 }
#             }, 200
#         )


DETAILS_RESPONSES = {
    'ESL100': build_bypass_v1_response(result_dict=BULB_DETAILS['ESL100']),
    'ESL100CW': build_bypass_v1_response(result_dict=BULB_DETAILS['ESL100CW']),
    'ESL100MC': build_bypass_v2_response(inner_result=BULB_DETAILS['ESL100MC']),
    'XYD0001': build_bypass_v2_response(inner_result=BULB_DETAILS['XYD0001']),
}


def valceno_set_status_response(kwargs=None):
    default_resp = {
        "traceId": TestDefaults.trace_id,
        "code": 0,
        "msg": "request success",
        "result": {
            "traceId": TestDefaults.trace_id,
            "code": 0,
            "result": {
                "enabled": "on",
                "colorMode": "hsv",
                "brightness": TestDefaults.brightness,
                "colorTemp": TestDefaults.color_temp,
                "hue": TestDefaults.color.hsv.hue*27.7778,
                "saturation": TestDefaults.color.hsv.saturation*100,
                "value": TestDefaults.color.hsv.value
            }
        }
    }
    if isinstance(kwargs, dict):
        if kwargs.get('hue') is not None:
            default_resp['result']['result']['hue'] = kwargs['hue'] * 27.7778
        if kwargs.get('saturation') is not None:
            default_resp['result']['result']['saturation'] = kwargs['saturation'] * 100
        if kwargs.get('value') is not None:
            default_resp['result']['result']['value'] = kwargs['value']
    return default_resp, 200


METHOD_RESPONSES = {
    'ESL100': deepcopy(FunctionResponsesV1),
    'ESL100CW': deepcopy(FunctionResponsesV1),
    'ESL100MC': deepcopy(FunctionResponsesV2),
    'XYD0001': deepcopy(FunctionResponsesV2),
}

# METHOD_RESPONSES['XYD0001'].default_factory = lambda: ({
#                                                 "traceId": Defaults.trace_id,
#                                                 "code": 0,
#                                                 "msg": "request success",
#                                                 "result": {
#                                                     "traceId": Defaults.trace_id,
#                                                     "code": 0
#                                                 }
#                                             }, 200)

# METHOD_RESPONSES['ESL100MC'].default_factory = lambda: ({
#                                                 "traceId": Defaults.trace_id,
#                                                 "code": 0,
#                                                 "msg": "request success",
#                                                 "result": {
#                                                     "traceId": Defaults.trace_id,
#                                                     "code": 0
#                                                 }
#                                             }, 200)

XYD0001_RESP = {
    'set_brightness': valceno_set_status_response,
    'set_color_temp': valceno_set_status_response,
    'set_hsv': valceno_set_status_response,
    'set_rgb': valceno_set_status_response,
}

METHOD_RESPONSES['XYD0001'].update(XYD0001_RESP)
