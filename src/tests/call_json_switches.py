"""
Switch Device API Responses

SWITCHES variable is a list of device types

DETAILS_RESPONSES variable is a dictionary of responses from the API
for get_details() methods.  The keys are the device types and the
values are the responses.  The responses are tuples of (response, status)

METHOD_RESPONSES variable is a defaultdict of responses from the API. This is
the FunctionResponse variable from the utils module in the tests dir.
The default response is a tuple with the value ({"code": 0, "msg": "success"}, 200).

"""
from copy import deepcopy
# from pyvesync.devices import vesyncswitch
from pyvesync.device_map import switch_modules
from pyvesync.const import DeviceStatus, ConnectionStatus
from defaults import TestDefaults, FunctionResponsesV1

SWITCHES = [m.setup_entry for m in switch_modules]
SWITCHES_NUM = len(SWITCHES)


class SwitchDefaults:
    device_status = DeviceStatus.ON
    connection_status = ConnectionStatus.ONLINE
    indicator_status = DeviceStatus.ON
    rgb_status = DeviceStatus.ON


SWITCH_DETAILS: dict[str, dict] = {
    "ESWL01": {  # V1
        "deviceStatus": SwitchDefaults.device_status.value,
        "activeTime": TestDefaults.active_time,
        "deviceName": "Etekcity Light Switch",
        "deviceImg": "",
        "connectionStatus": SwitchDefaults.connection_status.value,
    },
    "ESWL03": {  # V1
        "deviceStatus": SwitchDefaults.device_status.value,
        "activeTime": TestDefaults.active_time,
        "deviceName": "Etekcity Light Switch",
        "deviceImg": "",
        "connectionStatus": SwitchDefaults.connection_status.value,
    },
    "ESWD16": {
        "deviceStatus": SwitchDefaults.device_status.value,
        "activeTime": TestDefaults.active_time,
        "devicename": "Etekcity Dimmer Switch",
        "indicatorlightStatus": SwitchDefaults.indicator_status.value,
        "startMode": None,
        "brightness": TestDefaults.brightness,
        "rgbStatus": SwitchDefaults.rgb_status.value,
        "rgbValue": TestDefaults.color.rgb.to_dict(),
        "timer": None,
        "schedule": None,
        "deviceImg": "https://image.vesync.com/defaultImages/deviceDefaultImages/wifiwalldimmer_240.png",
        "connectionStatus": SwitchDefaults.connection_status.value,
    },
}


# class SwitchDetails:
#     details_ws = (
#         {
#             'code': 0,
#             'msg': None,
#             'deviceStatus': 'on',
#             'connectionStatus': 'online',
#             'activeTime': Defaults.active_time,
#             'power': 'None',
#             'voltage': 'None',
#         },
#         200,
#     )
#     details_eswd16 = ({
#                           "code": 0,
#                           "msg": "请求成功",
#                           "traceId": Defaults.trace_id,
#                           "indicatorlightStatus": "on",
#                           "timer": None,
#                           "schedule": None,
#                           "brightness": "100",
#                           "startMode": None,
#                           "activeTime": Defaults.active_time,
#                           "rgbStatus": "on",
#                           "rgbValue": {
#                               "red": Defaults.color.rgb.red,
#                               "blue": Defaults.color.rgb.blue,
#                               "green": Defaults.color.rgb.green
#                           },
#                           "connectionStatus": "online",
#                           "devicename": Defaults.name('ESWD16'),
#                           "deviceStatus": "on"
#                       }, 200)


DETAILS_RESPONSES = {
    'ESWL01': SWITCH_DETAILS['ESWL01'],
    'ESWD16': SWITCH_DETAILS['ESWD16'],
    'ESWL03': SWITCH_DETAILS['ESWL03'],
}

METHOD_RESPONSES = {
    'ESWL01': deepcopy(FunctionResponsesV1),
    'ESWD16': deepcopy(FunctionResponsesV1),
    'ESWL03': deepcopy(FunctionResponsesV1),
}
