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
from defaults import FunctionResponses, Defaults
from pyvesync.devices.vesyncbulb import bulb_modules
TRACE_ID = "TRACE_ID"

# BULBS = ['ESL100', 'ESL100CW', 'ESL100MC', 'XYD0001']
BULBS = bulb_modules.keys()
BULBS_NUM = len(BULBS)


class BulbDetails:
    details_esl100 = ({
        'code': 0,
        'msg': None,
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'name': Defaults.name('ESL100'),
        'brightNess': Defaults.brightness,
        'timer': None,
        'away': None,
        'schedule': None,
        'ownerShip': '1',
        'scheduleCount': 0,
    }, 200)

    details_esl100cw = ({
        "traceId": TRACE_ID,
        "code": 0,
        "msg": None,
        "module": None,
        "stacktrace": None,
        "result": {
            "light": {
                "action": "on",
                "brightness": Defaults.brightness,
                "colorTempe": Defaults.color_temp,
            }
        }
    }, 200)

    details_esl100mc = ({
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "request success",
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": {
                "action": "on",
                "brightness": Defaults.brightness,
                "colorMode": "color",
                "speed": 0,
                "red": Defaults.color.rgb.red,
                "green": Defaults.color.rgb.green,
                "blue": Defaults.color.rgb.blue,
            }
        }
    }, 200)

    details_valceno = (
            {
                "traceId": TRACE_ID,
                "code": 0,
                "msg": "request success",
                "result": {
                    "traceId": TRACE_ID,
                    "code": 0,
                    "result": {
                        "enabled": "on",
                        "colorMode": "color",
                        "brightness": Defaults.brightness,
                        "colorTemp": Defaults.color_temp,
                        "hue": Defaults.color.hsv.hue*27.7778,
                        "saturation": Defaults.color.hsv.saturation*100,
                        "value": Defaults.color.hsv.value,
                    }
                }
            }, 200
        )


DETAILS_RESPONSES = {
    'ESL100': BulbDetails.details_esl100,
    'ESL100CW': BulbDetails.details_esl100cw,
    'ESL100MC': BulbDetails.details_esl100mc,
    'XYD0001': BulbDetails.details_valceno,
}


def valceno_set_status_response(kwargs=None):
    default_resp = {
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "request success",
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": {
                "enabled": "on",
                "colorMode": "hsv",
                "brightness": Defaults.brightness,
                "colorTemp": Defaults.color_temp,
                "hue": Defaults.color.hsv.hue*27.7778,
                "saturation": Defaults.color.hsv.saturation*100,
                "value": Defaults.color.hsv.value
            }
        }
    }
    if kwargs is not None and isinstance(kwargs, dict):
        if kwargs.get('hue') is not None:
            default_resp['result']['result']['hue'] = kwargs['hue'] * 27.7778
        if kwargs.get('saturation') is not None:
            default_resp['result']['result']['saturation'] = kwargs['saturation'] * 100
        if kwargs.get('value') is not None:
            default_resp['result']['result']['value'] = kwargs['value']
    return default_resp, 200


METHOD_RESPONSES = {k: deepcopy(FunctionResponses) for k in BULBS}

METHOD_RESPONSES['XYD0001'].default_factory = lambda: ({
                                                "traceId": Defaults.trace_id,
                                                "code": 0,
                                                "msg": "request success",
                                                "result": {
                                                    "traceId": Defaults.trace_id,
                                                    "code": 0
                                                }
                                            }, 200)

METHOD_RESPONSES['ESL100MC'].default_factory = lambda: ({
                                                "traceId": Defaults.trace_id,
                                                "code": 0,
                                                "msg": "request success",
                                                "result": {
                                                    "traceId": Defaults.trace_id,
                                                    "code": 0
                                                }
                                            }, 200)

XYD0001_RESP = {
    'set_brightness': valceno_set_status_response,
    'set_color_temp': valceno_set_status_response,
    'set_hsv': valceno_set_status_response,
    'set_rgb': valceno_set_status_response,
}

METHOD_RESPONSES['XYD0001'].update(XYD0001_RESP)
