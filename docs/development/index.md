# pyvesync Library Development

This is a community driven library, so contributions are welcome! Due to the size of the library and variety of API calls and devices there are guidelines that need to be followed to ensure the continued development and maintanability.

There is a new nomenclature for product types that defines the device class. The
`device.product_type` attribute defines the product type based on the VeSync API. The product type is used to determine the device class and module. The currently supported product types are:

1. `outlet` - Outlet devices
2. `switch` - Wall switches
3. `fan` - Fans (not air purifiers or humidifiers)
4. `purifier` - Air purifiers (not humidifiers)
5. `humidifier` - Humidifiers (not air purifiers)
6. `bulb` - Light bulbs (not dimmers or switches)
7. `airfryer` - Air fryers

## Architecture

The `pyvesync.vesync.VeSync` class, also referred to as the `manager` is the central control for the entire library. This is the only class that should be directly instantiated.

The `VeSync` instance contains the authentication information and holds the device objects. The `VeSync` class has the method `async_call_api` which should be used for all API calls. It is as you might has guessed asynchronous. The session can either be passed in when instantiating the manager or generated internally.

Devices have a base class in the `pyvesync.base_devices` module. Each device type has a separate module that contains the device class and the API calls that are specific to that device type. The device classes inherit from the `VeSyncBaseDevice` and `VeSyncToggleDevice` base classes and implement the API calls for that device type.

The base class for the device state is also located in the `base_devices` module. The device state is a dataclass that contains all the attributes for that device type. The state is updated when `update()` is called. All attributes should be kept in the device base state class and attributes that are not supported by all models should have a `IntFlag.NOT_SUPPORTED` or `StrFlag.NOT_SUPPORTED` value.

## Naming conventions

All attributes and methods should be named using snake_case and follow the naming convention outlined below.

### On/Off States

States that have a string value, such as "on" or "off", should be appended with `_status`. For example, `device_status` or `connection_status`. The use of bool for on/off state attributes should be avoided. The `status` attributes should use a `StrEnum` constant from the `pyvesync.const` module. The `status` attributes should be set to `StrEnum.NOT_SUPPORTED` if the feature is not supported by all devices.

The general method to act on an on/off attribute should be `toggle_` and accept a boolean value. The method should be named `toggle_<attribute>` and the attribute should be set to the appropriate value. For example, `toggle_power` or `toggle_light_detection`. The method should accept a boolean value and set the attribute to the appropriate value.

The methods that specifically turn a device or or off should be named `turn_on_<attribute>` or `turn_off_<attribute>`. The attribute should be set to the appropriate value. For example, `turn_on_power` or `turn_off_light_detection`. The method should accept a boolean value and set the attribute to the appropriate value.

With the exception of Air Fryers, all devices inherit from the `VeSyncToggleDevice` class, which includes the `toggle_power`, `turn_on` and `turn_off` methods.

### Named Modes and Levels

For modes or levels, such as `fan_level` or `mode` attributes should use a `StrEnum` defined in the `pyvesync.const` module.

To change the mode or level, the methods should be named as `set_<attribute>` and accept a string value. The method should be named `set_<attribute>` and the attribute should be set to the appropriate value. For example, `set_fan_level` or `set_mode`. The method should accept a string value and set the attribute to the appropriate value.

## Library Utils Module

There are several helper methods and utilities that are provided for convenience:

### helpers module

The helpers module contains the `Validators`, `Helpers` and `Timer` classes that are used throughout the library. The `Validators` class contains methods to validate the input values for the API calls. The `Helpers` class contains methods to help with the API calls and the `Timer` class is used to handle timers and delays.

## STRONG Typing of responses and requests

All data coming in or going out should be strongly typed by a dataclass or TypedDict. The data models are located in the `pyvesync.models` module. The `pyvesync.models.base_models` contains the `DefaultValues` class that is used to hold the constant values that do not change with each API call. It can also contain class or static methods that do not accept any arguments.

The helper function `pyvesync.helpers.Helpers.get_class_attributes` is used to fill the values of the API calls by looking up class attributes, such as `token` in the `VeSync` instance and `cid` in the device instance. It accepts a list of keys and pulls the values of each key as they are found in the passed object:

```python
keys = ['token', 'accountId', 'cid', 'timeZone', 'countryCode']
manager_dict = get_class_attributes(manager, keys)
# request_dict = {"token": "AUTH_TOKEN", "accountId": "ACCOUNT_ID"}
device_dict = get_class_attributes(device, keys)
# device_dict = {"cid": "DEVICE CID"}
```

It can also handle class methods for items such as traceId which need to be calculated each API call:

```python
keys = ['traceId']
default_dict = get_class_attributes(DefaultValues, keys)
# {"traceId": "TIMESTAMP"}

# It can also handle underscores and different capitalization schemes
# It will always return the format of the key being passed in:
keys = ["trace_id", "AccountID"]
request_dict = get_class_attributes(DefaultValues, keys)
# {"trace_id": "TIMESTAMP"}
manager_dict = get_class_attributes(manager, keys)
# {"AccountID": "ACCOUNT ID"}
```

### Base Models

The data models are located in the `models` folder in separate models. The `base_model` module contains a dataclass holding the default values that do not change between library changes. The `base_model` module is imported into all other models to ensure that the default values stay consistent. The `base_model` module also contains base models that can be inherited for easy configuration and common fields.

```python
@dataclass
class ResponseBaseModel(DataClassORJSONMixin):
    """Base response model for API responses."""

    class Config(BaseConfig):
        """orjson config for dataclasses."""
        orjson_options = orjson.OPT_NON_STR_KEYS
        forbid_extra_keys = False
```

`ResponseCodeModel` - Inherits from `ResponseBaseModel` and contains the base keys in most API responses:

```python
@dataclass
class ResponseCodeModel(ResponseBaseModel):
    """Model for the 'result' field in response."""
    traceId: str
    code: int
    msg: str | None

```

### Request and Response Serialization/Deserialization with Mashumaro

pyvesync uses Mashumaro with orjson for data models and serializing/deserializing data structures. The models are located in the `pyvesync.data_models` model. These models should be used to deserialize all API responses. The `base_model.DefaultValues` should be used to define constant and calculated fields throughout each API call. There are additional helper base classes to simplify models:

`ResponseBaseModel` - this contains configuration overrides to allow Mashumaro to deserialize non-string keys and allows extra keys in the response. Only the keys that are needed can be defined.

```python
@dataclass
class ResponseBaseModel(DataClassORJSONMixin):
    """Base response model for API responses."""

    class Config(BaseConfig):
        """orjson config for dataclasses."""
        orjson_options = orjson.OPT_NON_STR_KEYS
        forbid_extra_keys = False
```

`ResponseCodeModel` - Inherits from `ResponseBaseModel` and contains the base keys in most API responses:

```python
@dataclass
class ResponseCodeModel(ResponseBaseModel):
    """Model for the 'result' field in response."""
    traceId: str
    code: int
    msg: str | None

````

Models for each device should be kept in the `data_models` folder with the appropriate device name:

- `bulb_models`
- `humidifier_models`
- `purifier_models`
- `outlet_models`
- `switch_models`
- `fan_models`

There are multiple levels to some requests with nested dictionaries. These must be defined in different classes:

```python
# The ResponseESL100CWDeviceDetail inherits from ResponseCodeModel
@dataclass
class ResponseESL100CWDeviceDetail(ResponseCodeModel):
    """Response model for Etekcity bulb details."""
    result: ResponseESL100CWDetailResult


@dataclass
class ResponseESL100CWLight(ResponseBaseModel):
    """ESL100CW Tunable Bulb Device Detail Response."""
    action: str
    brightness: int = 0
    colorTempe: int = 0


@dataclass
class ResponseESL100CWDetailResult(ResponseBaseModel):
    """Result model for ESL100CW Tunable bulb details."""
    light: ResponseESL100CWLight
```

This model parses the following json response:

```python
from pyvesync.data_models.bulb_models import ResponseESL100CWDeviceDetail
import orjson

api_response = {
    "traceId": "12345678",
    "code": 0,
    "msg": "success",
    "module": None,
    "stacktrace": None,
    "result": {
        "light": {
            "action": "on",
            "brightness": 5,
            "colorTempe": 0
        }
    }
}

api_response_dict, status_code = await manager.async_call_api(
    "/v1/endpoint",
    "post",
    request_body,
    request_headers
)

response_model = ResponseESL100CWDeviceDetail.from_dict(response_bytes)

result = response_model.result
light_model = result.light
print(light_model.action)  # prints: on
print(light_model.brightness)  # prints: 5
print(light_model.colorTempe)  # prints: 0
```

## Constants

All constants should be located in the `pyvesync.const` module, including default values. There should not be any constants defined in the code. Use `enum.StrEnum` or `enum.IntEnum` for Enum values.

All device modes and feature names are defined in this module.

`IntEnum` and `StrEnum` are preferred for device status and state because boolean only allows for two states. There is no way to tell if the state is not yet known or unsupported.

The `IntFlag` and `StrFlag` classes are used to define attributes in the state class that may not be supported by all devices.

```python
class IntFlag(IntEnum):
    """Integer flag to indicate if a device is not supported.

    This is used by data models as a default value for feature attributes
    that are not supported by all devices.

    The default value is -999.
    """
    NOT_SUPPORTED = -999

    def __str__(self) -> str:
        """Return string representation of IntFlag."""
        return str(self.name)


class StrFlag(StrEnum):
    """String flag to indicate if a device is not supported.

    This is used by data models as a default value for feature attributes
    that are not supported by all devices.

    The default value is "not_supported".
    """
    NOT_SUPPORTED = "not_supported"
```

The string states that support 'on' and 'off' have helper methods that allow for
easy conversion from bool and int values:

```python
from pyvesync.const import DeviceStatus

api_int = 1
api_bool = True

device.state.device_status = DeviceStatus.from_int(api_int)
assert device.state.device_status == DeviceStatus.ON

device.state.device_status = DeviceStatus.from_bool(api_bool)
assert device.state.device_status == DeviceStatus.ON

api_int = int(device.state.device_status)
assert api_int == 1

api_bool = bool(device.state.device_status)
assert api_bool == True

```

**Note that this only works for on/off values.**

## Device Map

All features and configuration options for devices are held in the `pyveysnc.device_map` module. Older versions of pyvesync held the device configuration in each device module, all of these have moved to the `device_map` module. Each product type has a dataclass structure that is used to define all of the configuration options for each type. The `device_map.get_device_config(device_type: str)` method is used to lookup the configuration dataclass instance by the `deviceType` value in the device list response.

There are also methods for each device to return the device configuration with the correct type. For example, `get_outlet_config()` returns the configuration for the outlet device. The configuration is a dataclass that contains all of the attributes for that device type. The configuration is used to define the attributes in the device state class.

## Authentication

The two primary authentication attributes are `manager.token` and `manager.account_id`. These are used to authenticate all API calls, in combination with other attributes. The `country_code` and `time_zone` attributes are also used in the majority of calls. They are retrieved when calling the `login()` method.

## Device Container

Devices are held in the `pyvesync.device_container.DeviceContainer` class in the `manager.devices` attribute. The `DeviceContainer` class is a singleton class, so only one instance can exist. The class inherits from `MutableSet` so it contains unique objects, with the ability to add and remove devices using the `add`, `remove` and `clear` methods. However, these methods only accept device objects. To simplify removing devices, there is the `remove_by_cid(cid: str)` method.

To get devices by device name, use the `get_by_name(name: str)` method. There are two convenience methods `add_new_devices` and `remove_stale_devices` that accept the device list response model.

The `DeviceContainer` object has a property for each product type that returns a list of devices. For example, `DeviceContainer.outlets` returns a list of all outlets product type devices.

## Custom Exceptions

Exceptions are no longer caught by the library and must be handled by the user. Exceptions are raised by server errors and aiohttp connection errors.

Errors that occur at the aiohttp level are raised automatically and propagated to the user. That means exceptions raised by aiohttp that inherit from `aiohttp.ClientError` are propagated.

When the connection to the VeSync API succeeds but returns an error code that prevents the library from functioning a custom exception inherited from `pyvesync.logs.VeSyncError` is raised.

Custom Exceptions raised by all API calls:

- `pyvesync.logs.VeSyncServerError` - The API connected and returned a code indicated there is a server-side error.
- `pyvesync.logs.VeSyncRateLimitError` - The API's rate limit has been exceeded.
- `pyvesync.logs.VeSyncAPIStatusCodeError` - The API returned a non-200 status code.
- `pyvesync.logs.VeSyncAPIResponseError` - The response from the API was not in an expected format.

Login API Exceptions

- `pyvesync.logs.VeSyncLoginError` - The username or password is incorrect.

See [errors.py](./utils/errors.md) for a complete list of error codes and exceptions.

## VeSync API's

The vesync API is typically one of two different types. The first is the Bypass V1 API, which is used for most devices. The second is the Bypass V2 API, which is used for newer devices.

The `pyvesync.utils.device_mixins` module contains mixins for common device API's and helper methods. This allows for easy reuse of code and keeps the device modules clean(er).

### General Response Structure

The general response structure for API calls is as follows:

```json
{
    "traceId": "TIMESTAMP",
    "code": 0,
    "msg": "request success",
    "module": null,
    "stacktrace": null,
}
```

The error code contains information from the API call on whether the request was successful or details on the error. The `code` value is parsed by the library and stored in `device.last_response` attribute.

### Bypass V1

The `BypassV1Mixin` class is used for generally older devices, such as bulbs, switches, outlets and the first air purifier model (LV-PUR131S). The API calls use the `post` method and the base endpoint path `/cloud/v1/deviceManaged/`. The final path segment can either be `bypass` or a specific function, such as `PowerCtl`.

#### Bypass V1 Request Structure

When the final path segment is not `bypass`, e.g. `/cloud/v1/deviceManaged/deviceDetail`, the method key of the API call is the same as the last path segment:

```json
    {
        "method": "deviceDetail",
        "acceptLanguage": "en_US",
        "appVersion": "1.0.0",
        "phoneBrand": "Android",
        "phoneOS": "Android 10",
        "accountID": "1234567890",
        "cid": deviceCID,
        "configModule": configModule,
        "debugMode": False,
        "traceId": 1234567890,
        "timeZone": "America/New_York",
        "token": "abcdefg1234567",
        "userCountryCode": "+1",
        "uuid": 1234567890,
        "configModel": configModule,
        "deviceId": deviceCID,
    }
```

There can also be additional keys in the body of the request, such as `"status": "on"`. There are not any nested dictionaries in the request body.

For API calls that have the `bypass` path, the structure is slightly different. The value of the outer `method` key is `bypass` and the request contains the `jsonCmd` key, containing the details of the request:

```json
{
    "method": "bypass",
    "acceptLanguage": "en_US",
    "appVersion": "1.0.0",
    "phoneBrand": "Android",
    "phoneOS": "Android 10",
    "accountID": "1234567890",
    "cid": deviceCID,
    "configModule": configModule,
    "debugMode": False,
    "traceId": 1234567890,
    "timeZone": "America/New_York",
    "token": "abcdefg1234567",
    "userCountryCode": "+1",
    "uuid": 1234567890,
    "configModel": configModule,
    "deviceId": deviceCID,
    "jsonCmd": {
        "getLightStatus": "get"
    }
}
```

#### Bypass V1 Response Structure

Responses for the Bypass V1 API calls have the following structure with the `result` value containing the response information:

```json
{
    "traceId": "TIMESTAMP",
    "code": 0,
    "msg": "request success",
    "module": null,
    "stacktrace": null,
    "result": {
        "light": {
            "action": "off",
            "brightness": 30,
            "colorTempe": 5
        }
    }
}
```

#### Bypass V1 Device Mixin

The `pyvesync.utils.device_mixins.BypassV1Mixin` class contains boilerplate code for the devices that use the Bypass V1 api. The mixin contains the `call_bypassv1_mixin` method that builds the request and calls the api. The method accepts the following parameters:

```python
async def call_bypassv1_mixin(
    self,
    requestModel: type[RequestBypassV1],  # Model for the request body
    update_dict: dict | None = None,  # Allows additional keys to be provided in the request body
    method: str = "bypass",  # Method value in request body
    endpoint: bool = False,  # Last segment of API path
) -> tuple[dict[str, Any], int]: ...
```

The process_bypassv1_response method is used to parse the response, check for errors and return the value of the `result` key. The method accepts the following parameters:

```python
def process_bypassv1_result(
    device: VeSyncBaseDevice,
    logger: Logger,
    method: str,
    resp_dict: dict | None,
) -> dict | None: ...
```

This is an example of the implementation:

```python
from pyvesync.devices import VeSyncSwitch
from pvyesync.models.switch_models import RequestSwitchDetails
from pyvesync.utils.device_mixins import BypassV1Mixin, process_bypassv1_response


class VSDevice(BypassV1Mixin, VeSyncSwitch):


def get_details(self) -> bool:
    ...
    update_dict = {
        "jsonCmd": {
            "getStatus": "get"
        }
    }
    response = await self.call_bypassv1_api(
        requestModel=RequestSwitchDetails,
        update_dict=update_dict,
        method="PowerCtl",
        endpoint=True
    )

    # The process_bypassv1_response method makes the appropriate logs if error in response
    result = process_bypassv1_response(self, logger, 'get_details', response)
```

**NOTE** The `process_bypassv1_response` method is not necessary for API calls that perform an action and return the simple response shown above with the `code` and `msg` keys and no `result` key.

### Bypass V2

The Bypass V2 API is used for newer devices, such as humidifiers. The API calls use the `post` method and the base endpoint path `/cloud/v2/deviceManaged/bypassV2`. The final path segment is always `bypassV2`.

#### Bypass V2 Request Structure

The bypass V2 request structure is very similar between API calls. The outer `method` key always has the `bypassv2` attribute. The payload structure is always the same with the `method`, `data` and `source` keys. The `source` key always contains the value `APP`. The payload `method` and `data` keys change.

```json
{
    "acceptLanguage": "en",
    "accountID": "ACCOUNTID",
    "appVersion": "VeSync 5.5.60",
    "cid": "deviceCID",
    "configModule": "configModule",
    "debugMode": false,
    "method": "bypassV2",
    "phoneBrand": "SM-A5070",
    "phoneOS": "Android 12",
    "timeZone": "America/New_York",
    "token": "TOKEN",
    "traceId": "1743902977493",
    "userCountryCode": "US",
    "deviceId": "deviceCID",
    "configModel": "configModule",
    "payload": {
        "data": {},
        "method": "getPurifierStatus",
        "source": "APP"
    }
}
```

#### Bypass V2 Response Structure

The response structure has a relatively similar structure for all calls with a nested result dictionary, containing an additional `code` and `device_error_code` key that provides information on errors that are specific to the device:

```json
{
    "traceId": "TIMESTAMP",
    "code": 0,
    "msg": "request success",
    "module": null,
    "stacktrace": null,
    "result": {
        "traceId": "TIMESTAMP",
        "code": 0,
        "result": {
            "enabled": true,
            "filter_life": 98,
            "mode": "manual",
            "level": 4,
            "air_quality": 1,
            "air_quality_value": 2,
            "display": true,
            "child_lock": false,
            "configuration": {
                "display": true,
                "display_forever": true,
                "auto_preference": {
                    "type": "efficient",
                    "room_size": 1050
                }
            },
            "extension": {
                "schedule_count": 0,
                "timer_remain": 0
            },
            "device_error_code": 0
        }
    }
}
```

#### Bypass V2 Device Mixin

The `pyvesync.utils.device_mixins.BypassV2Mixin` class contains boilerplate code for the devices that use the Bypass V1 api. The mixin contains the `call_bypassv1_mixin` method that builds the request and calls the api. The method accepts the following parameters:

```python
    async def call_bypassv2_api(
        self,
        payload_method: str,  # Value of method in the payload key
        data: dict | None = None,  # Dictionary to be passed in the payload data key
        method: str = "bypassV2",  # Allows the outer method value to be changed
        endpoint: str = "bypassV2",  # Allows the last segment of API path to be changed
    ) -> dict | None: ...
```

The process_bypassv2_response method is used to parse the response, check for errors and return the value of the inner `result` key. The method accepts the following parameters:

```python
def process_bypassv2_results(
    device: VeSyncBaseDevice,
    logger: Logger,
    method: str,
    resp_dict: dict | None,
) -> dict | None:
```

This is an example of how it is used:

```python
from pyvesync.base_devices import VeSyncPurifier
from pyvesync.models.purifier_models import RequestPurifierDetails
from pyvesync.utils.device_mixins import BypassV2Mixin, process_bypassv2_response


class VSDevice(BypassV2Mixin, VeSyncPurifier):
    """VeSync Purifier device class."""

    async def get_details(self) -> bool:
        """Get the details of the device."""
        response = await self.call_bypassv2_api(
            payload_method="getPurifierStatus",
            data=update_dict
        )

        # The process_bypassv2_response method makes the appropriate logs if error in response
        result = process_bypassv2_response(self, logger, 'get_details', response)
```

**NOTE** The `process_bypassv2_response` method is not necessary for API calls that perform an action and return the simple response shown above with the `code` and `msg` keys and no `result` key.
