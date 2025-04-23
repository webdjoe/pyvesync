# pyvesync V3.0 Changes

**BREAKING CHANGES** - The release of pyvesync 3.0 comes with many improvements and new features, but as a result there are many breaking changes. The structure has been completely refactored, so please read through the documentation and thoroughly test before deploying.

The goal is to standardize the library across all devices to allow easier and consistent maintainability moving forward. The original library was created 8 years ago for supporting only a few outlets, it was not designed for supporting 20+ different devices.

Some of the changes are:

- Asynchronous network requests with aiohttp
- Strong typing of all network requests and responses.
- New `product_type` nomenclature to map with API.
- Base classes for all product types for easier `isinstance` checks.
- Standardized the API for all device to follow a common naming convention.
- Custom exceptions and error (code) handling for API responses.
- `last_response` attribute on device instances to hold information on the last API response.
- [`DeviceContainer`][pyvesync.device_container] object holds all devices in a mutable set structure with additional convenience methods and properties for managing devices. This is located in the `VeSync.manager.devices` attribute.
- Custom exceptions for better error handling - [`VeSyncError`][pyvesync.utils.errors.VeSyncError], `VeSyncAPIException`, `VeSyncLoginException`, `VeSyncRateLimitException`, `VeSyncNoDevicesException`
- Device state has been separated from the device object and is now managed by the device specific subclasses of [`DeviceState`][pyvesync.base_devices.vesyncbasedevice.DeviceState]. The state object is located in the `state` attribute of the device object.
- [`const`][pyvesync.const] module to hold all library constants.
- [`device_map`][pyvesync.device_map] module holds all device type mappings and configuration.

If you submit a PR please ensure that it follows all conventions outlined in [CONTRIBUTING](./development/contributing.md).

## Asynchronous operation

Library is now asynchronous, using aiohttp as a replacement for requests. The `pyvesync.VeSync` class is an asynchronous context manager. A `aiohttp.ClientSession` can be passed or created internally.

```python
import asyncio
import aiohttp
from pyvesync.vesync import VeSync

async def main():
    async with VeSync("user", "password") as manager:
        await manager.login()  # Still returns true
        if not manager.enabled:
            print("Not logged in.")
            return
        await manager.get_devices() # Instantiates supported devices in device list
        await manager.update() # Updates the state of all devices

        for outlet in manager.devices.outlets:
            # The outlet object contain all action methods and static device attributes
            await outlet.update()
            await outlet.turn_off()
            outlet.display() # Print static device information, name, type, CID, etc.

            # State of object held in `device.state` attribute
            print(outlet.state)
            state_json = outlet.dumps() # Returns JSON string of device state
            state_bytes = orjson.dumps(outlet.state) # Returns bytes of device state

            # to view the response information of the last API call
            print(outlet.last_response)
            # Prints a ResponseInfo object containing error code,
            # and other response information


# Or use your own session
session = aiohttp.ClientSession()

async def main():
    async with VeSync("user", "password", session=session):
        await manager.login()
        await manager.update()



if __name__ == "__main__":
    asyncio.run(main())
```

If using `async with` is not ideal, the `__aenter__()` and `__aexit__()` methods need to be called manually:

```python
manager = VeSync(user, password)

await manager.__aenter__()

...

await manager.__aexit__(None, None, None)
```

pvesync will close the `ClientSession` that was created by the library on `__aexit__`. If a session is passed in as an argument, the library does not close it. If a session is passed in and not closed, aiohttp will generate an error on exit:

```text
2025-02-16 14:41:07 - ERROR - asyncio - Unclosed client session
2025-02-16 14:41:07 - ERROR - asyncio - Unclosed connector
```

## VeSync Class Signature

The VeSync signature is:

```python
VeSync(
    username: str,
    password: str,
    session: ClientSession | None = None,
    time_zone: str = DEFAULT_TZ  # America/New_York
    )
```

The VeSync class no longer accepts a `debug` or `redact` argument. To set debug the library set `manager.debug = True` to the instance and `manager.redact = True`.

## Product Types

There is a new nomenclature for product types that defines the device class. The
`device.product_type` attribute defines the product type based on the VeSync API. The product type is used to determine the device class and module. The currently supported product types are:

1. `outlet` - Outlet devices
2. `switch` - Wall switches
3. `fan` - Fans (not air purifiers or humidifiers)
4. `purifier` - Air purifiers (not humidifiers)
5. `humidifier` - Humidifiers (not air purifiers)
6. `bulb` - Light bulbs (not dimmers or switches)
7. `airfryer` - Air fryers

See [Supported Devices](./supported_devices.md) for a complete list of supported devices and models.

## Custom Exceptions

Exceptions are no longer caught by the library and must be handled by the user. Exceptions are raised by server errors and aiohttp connection errors.

Errors that occur at the aiohttp level are raised automatically and propogated to the user. That means exceptions raised by aiohttp that inherit from `aiohttp.ClientError` are propogated.

When the connection to the VeSync API succeeds but returns an error code that prevents the library from functioning a custom exception inherrited from `pyvesync.utils.errors.VeSyncError` is raised.

Custom Exceptions raised by all API calls:

- [VeSyncServerError][pyvesync.utils.errors.VeSyncServerError] - The API connected and returned a code indicated there is a server-side error.
- [VeSyncRateLimitError][pyvesync.utils.errors.VeSyncRateLimitError] - The API's rate limit has been exceeded.
- [VeSyncAPIStatusCodeError][pyvesync.utils.errors.VeSyncAPIStatusCodeError] - The API returned a non-200 status code.
- [VeSyncAPIResponseError][pyvesync.utils.errors.VeSyncAPIResponseError] - The response from the API was not in an expected format.

Login API Exceptions

- [VeSyncLoginError][pyvesync.utils.errors.VesyncLoginError] - The username or password is incorrect.

See [errors](./development/utils/errors.md) documentation for a complete list of error codes and exceptions.

## Device Last Response Information

If no exception is raised by the API, the response code and message of the last API call is stored in the `device.last_response` attribute. This is a [`ResponseInfo`][pyvesync.utils.errors.ResponseInfo] object that contains the following attributes:

```python
ResponseInfo(
    name="SUCCESS",
    error_type="",
    message="",
    critical_error=False,
    operational_error=False,
    device_online=True
)
```

The ResponseInfo object is populated from the API response and source code.

## Input Validation

When values that are required to be in a range are input, such as RGB/HSV colors, fan levels, etc. the library will no longer automatically adjust values outside of that range. The function performing the operation will just return False, with a debug message in the log. This is to minimize complexity and utility of the underlying code. If an invalid input is provided, the library should not assume to correct it.

For example, setting bulb RGB color:

**OLD OPERATION** - Entering values outside the accepted range were corrected to the nearest extreme and the operation is performed.

```python
set_rgb = await bulb.set_rgb(300,0,-50)
assert set_rgb == True # Bulb was set to the min/max RGB 255,0,0
```

**NEW OPERATION** - invalid values return false and operation is not performed.

```python
set_rgb = await bulb.set_rgb(300,0,-50)
assert set_rgb == False
```

All methods that set RGB/HSV color now require all three inputs, red/green/blue or hue/saturation/value. I do not see the use in updating `red`, `green` or `blue`/`hue`, `saturation` or `value` individually. If you have a strong need for this, please open an issue with a detailed use case.

## Strong Typing with Mashumaro

All API requests and responses must be deserialized with a mashumaro dataclass. The dataclass is used to validate the response and ensure that the data is in the expected format. Requests are also serialized with a dataclass model to ensure that there are no breaking changes when changes are made to the library.

The data models are located in the `models` folder in separate models. The [`base_models`][pyvesync.models.base_models] module contains a dataclass holding the default values that do not change between library changes. The `base_models` module is imported into all other models to ensure that the default values stay consistent. The `base_models` module also contains base models that can be inherited for easy configuration and common fields.

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

Models for each device should be kept in the `data_models` folder with the appropriate device name:

- [`bypass_models`][pyvesync.models.bypass_models] - See [`Development`](./development/index.md) for more information on bypass devices.
- [`bulb_models`][pyvesync.models.bulb_models]
- [`humidifier_models`][pyvesync.models.humidifier_models]
- [`purifier_models`][pyvesync.models.purifier_models]
- [`outlet_models`][pyvesync.models.outlet_models]
- [`switch_models`][pyvesync.models.switch_models]
- [`fan_models`][pyvesync.models.fan_models]
- [`airfryer_models`][pyvesync.models.fryer_models]
- [`thermostat_models`][pyvesync.models.thermostat_models]

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

# Response will already be in bytes, so this is unecessary
response_bytes = orjson.dumps(api_response, options=orjson.OPT_NON_STR_KEYS)

response_model = ResponseESL100CWDeviceDetail.from_json(response_bytes)

result = response_model.result
light_model = result.light
print(light_model.action)  # prints: on
print(light_model.brightness)  # prints: 5
print(light_model.colorTempe)  # prints: 0
```

### Making API Calls

The helper function `pyvesync.utils.helpers.Helpers.get_class_attributes` is used to fill the values of the API calls by looking up class attributes, such as `token` in the `VeSync` instance and `cid` in the device instance. It accepts a list of keys and pulls the values of each key as they are found in the passed object:

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

## Device Container

Devices are held in the [DeviceContainer][pyvesync.device_container.DeviceContainer] class in the `manager.devices` attribute. The `DeviceContainer` class is a singleton class, so only one instance can exist. The class inherits from `MutableSet` so it contains unique objects, with the ability to add and remove devices using the `add`, `remove` and `clear` methods. However, these methods only accept device objects. To simplify removing devices, there is the `remove_by_cid(cid: str)` method.

To get devices by device name, use the `get_by_name(name: str)` method. There are two convenience methods `add_new_devices` and `remove_stale_devices` that accept the device list response model.

The `DeviceContainer` object has a property for each product type that returns a list of devices. For example, `DeviceContainer.outlets` returns a list of all outlets product type devices.

See [DeviceContainer](./development/device_container.md) for more information on the device container.

```python
import asyncio
from pyvesync import VeSync

async def main():
    async with VeSync(user, password) as manager:
        assert len(manager.devices) == 0 # No devices yet
        await manager.login()

        await manager.get_devices() # Pulls in devices
        assert len(manager.devices) > 0 # Devices are now in the container

        for device in manager.devices:
            print(device) # Prints all devices in the container

        manager.update()  # Pull state into devices

        # also holds the product types as properties

        outlets = manager.devices.outlets  # list of VeSyncOutlet objects
        switches = manager.devices.switches # list of VeSyncSwitch objects
        fans = manager.devices.fans  # list of VeSyncFan objects
        bulbs = manager.devices.bulbs  # list of VeSyncBulb objects
        humidifiers = manager.devices.humidifiers # VeSyncHumid objects
        air_purifiers = manager.devices.air_purifiers # list of VeSyncPurifier objects


if __name__ == '__main__':
    asyncio.run(main())
```

## Device Base Classes

The device classes are now all inherited from their own product type specific base class. All base classes still inherit from [`vesyncbasedevice`][pyvesync.base_devices.vesyncbasedevice.VeSyncBaseDevice]. The base class provides the common functionality for all devices and the device classes provide the specific functionality for each device. The `pyvesync.base_devices` module contains the base classes for all devices in their respective modules by product type. The base state class is [`DeviceState`][pyvesync.base_devices.vesyncbasedevice.DeviceState]. Both `VeSyncBaseDevice` and `DeviceState` are inherited by device and their state classes.

The base module should hold all properties and methods that are common to all devices. The base module also contains the base devices state class. The base device state class holds all state attributes for all underlying devices.

## Device Configuration with device_map module

All features and configuration options for devices are held in the `pyveysnc.device_map` module. Older versions of pyvesync held the device configuration in each device module, all of these have moved to the `device_map` module. Each product type has a dataclass structure that is used to define all of the configuration options for each type. The `device_map.get_device_config(device_type: str)` method is used to lookup the configuration dataclass instance by the `deviceType` value in the device list response.

## Constants

All constants should be located in the [const][pyvesync.const] module, including default values. There should not be any constants defined in the code. Use `enum.StrEnum` or `enum.IntEnum` for Enum values.

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
