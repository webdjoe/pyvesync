# pyvesync Library

[![build status](https://img.shields.io/pypi/v/pyvesync.svg)](https://pypi.python.org/pypi/pyvesync) [![Build Status](https://dev.azure.com/webdjoe/pyvesync/_apis/build/status/webdjoe.pyvesync?branchName=master)](https://dev.azure.com/webdjoe/pyvesync/_build/latest?definitionId=4&branchName=master) [![Open Source? Yes!](https://badgen.net/badge/Open%20Source%20%3F/Yes%21/blue?icon=github)](https://github.com/Naereen/badges/) [![PyPI license](https://img.shields.io/pypi/l/ansicolortags.svg)](https://pypi.python.org/pypi/ansicolortags/) <!-- omit in toc -->

**This is a work in progress, PR's greatly appreciated 🙂.**

pyvesync is a python library that interacts with devices that are connected to the VeSync app. The library can pull state details and perform actions to devices once they are set up in the app. This is not a local connection, the pyvesync library connects the VeSync cloud API, which reads and sends commands to the device, so internet access is required for both the device and library. There is no current method to control locally.

## Supported devices

The following product types are supported:

1. `outlet` - Outlet devices
2. `switch` - Wall switches
3. `fan` - Fans (not air purifiers or humidifiers)
4. `purifier` - Air purifiers (not humidifiers)
5. `humidifier` - Humidifiers (not air purifiers)
6. `bulb` - Light bulbs (not dimmers or switches)
7. `airfryer` - Air fryers

See [Supported Devices](supported_devices.md) for a complete list of supported devices and models.

## What's New

**BREAKING CHANGES** - The release of pyvesync 3.0 comes with many improvements and new features, but as a result there are many breaking changes. The structure has been completely refactored, so please read through the documentation and thoroughly test before deploying.

The goal is to standardize the library across all devices to allow easier and consistent maintainability moving forward. The original library was created 8 years ago for supporting only a few outlets, it was not designed for supporting 20+ different devices.

This will **DEFINITELY** cause breaking changes with existing code, but the new structure should be easier to work with and more consistent across all devices in the future.

Some of the major structural changes include:

- Asynchronous API calls through aiohttp
- [`DeviceContainer`][pyvesync.device_container.DeviceContainer] object holds all devices in a mutable set structure with additional convenience methods and properties for managing devices. This is located in the `VeSync.manager` attribute.
- Custom exceptions for better error handling there are custom exceptions that inherit from [`VeSyncError`][pyvesync.utils.errors.VeSyncError], `VeSyncAPIError`, `VeSyncLoginError`, `VeSyncRateLimitError`.
- Device state has been separated from the device object and is now managed by the device specific subclasses of [`DeviceState`][pyvesync.base_devices.vesyncbasedevice.DeviceState]. The state object is located in the `state` attribute of the device object.
- Device Classes have been refactored to be more consistent and easier to manage. No more random property and method names for different types of the same device.
- [`const`][pyvesync.const] module to hold all library constants.
- [`device_map`][pyvesync.device_map] module holds all device type mappings and configuration.
- Authentication logic has been moved to the [`auth`][pyvesync.auth] module and is now handled by the `VeSync.auth` attribute. This can store and load credentials, so login is not required every time.

See [pyvesync V3](./pyvesync3.md) for more details.

## Questions or Help?

If you have a bug or enhancement request for the pyvesync library, please submit an [issue](https://github.com/webdjoe/pyvesync/issues).

Looking to submit a request for a new device or have a general functionality question, check out [discussions](https://github.com/webdjoe/pyvesync/discussions).

For home assistant issues, please submit on that repository.

### New Devices

If you would like to add a new device, packet captures must be provided. The iOS and Android VeSync app implements certificate pinning to prevent standard MITM intercepts. Currently, the only known way is to patch the APK and run on a rooted android emulator with frida. This is a complex process that has had varying levels of success. If you successful in capturing packets, please capture all functionality, including the device list and configuraiton screen. Redact accountId and token keys or contact me for a more secure way to share. See the [Packet Capturing for New Device Support](./development/capturing.md) document for more details.

## General Usage

The [`pyvesync.vesync.VeSync`][pyvesync.vesync.VeSync] object is the primary class that is referred to as the `manager` because it provides all the methods and properties to control the library. This should be the only class that is directly instantiated. All devices will be instantiated and managed by the `VeSync` object.

See the [Usage](./usage.md) documentation for a quick start guide on how to use the library.

### VeSync Manager

The `VeSync` class has the following parameters, `username` and `password` are mandatory:

```python
import asyncio
from pyvesync import VeSync

# To enable debug logging:
import logging
vs_logger = logging.getLogger("pyvesync")
vs_logger.setLevel(logging.DEBUG)

async def main():
    async with VeSync(
        username="user",
        password="password",
        country_code="US",  # Optional - country Code to select correct server
        session=session,  # Optional - aiohttp.ClientSession
        time_zone="America/New_York",  # Optional - Timezone, defaults to America/New_York
        redact=True  # Optional - Redact sensitive information from logs
        ) as manager:

    # VeSync object is now instantiated
    await manager.login()
    # Check if logged in
    assert manager.enabled
    # Debug and Redact are optional arguments
    manager.redact = True

    # Get devices
    await manager.get_devices()
    # Device objects are now instantiated, but do not have state
    await manager.update() # Pulls in state and updates all devices

    # Or iterate through devices and update individually
    for device in manager.outlets:
        await device.update()

    # Or update a product type of devices:
    for outlet in manager.devices.outlets:
        await outlet.update()

if __name__ == "__main__":
    asyncio.run(main())

```


If you want to reuse your token and account_id between runs. The `VeSync.auth` object holds the credentials and helper methods to save and load credentials.

```python
import asyncio
from pyvesync import VeSync

# VeSync is an asynchronous context manager
# VeSync(username, password, redact=True, session=None)

async def main():
    async with VeSync("user", "password") as manager:

        # If credentials are stored in a file, it can be loaded
        # the default location is ~/.vesync_token
        await manager.load_credentials_from_file()
        # or the file path can be passed
        await manager.load_credentials_from_file("/path/to/token_file")

        # Or credentials can be passed directly
        manager.set_credentials("your_token", "your_account_id")

        # No login needed
        # await manager.login()

        # To store credentials to a file after login
        await manager.save_credentials() # Saves to default location ~/.vesync_token
        # or pass a file path
        await manager.save_credentials("/path/to/token_file")

        # Output Credentials as JSON String
        await manager.output_credentials()

        await manager.update()

        # Acts as a set of device instances
        device_container = manager.devices

        outlets = device_container.outlets # List of outlet instances
        outlet = outlets[0]
        await outlet.update()
        await outlet.turn_off()
        outlet.display()

        # Iterate of entire device list
        for devices in device_container:
            device.display()


if __name__ == "__main__":
    asyncio.run(main())
```

### Getting Devices

Once logged in, the next call should be to the `update()` method which:

- calls the `get_devices()` method to retrieve the list of devices from the server
- Removes stale devices that are not present in the new API call
- Adds new devices to the device list attributes
- Instantiates all new device classes
- Updates all devices via the device instance `device.update()` method

```python
# Get/Update Devices from server - populate device lists
manager.update()

# Device instances are now located in the devices attribute:

devices = manager.devices  # Mutable set-like class

# The entire container can be iterated over:
for device in manager.devices:
    print(device)


# Or iterate over specific device types:
for outlet in manager.outlets:
    print(outlet)
```

Updating all devices without pulling a device list:

```python
manager.update_all_devices()
```

The devices attribute is a [`DeviceContainer`][pyvesync.device_container.DeviceContainer] object that holds all devices in a mutable set-like structure. Each product type is a property in the `devices` attribute:

```python
manager.devices.outlets = [VeSyncOutletInstances]
manager.devices.switches = [VeSyncSwitchInstances]
manager.devices.fans = [VeSyncFanInstances]
manager.devices.bulbs = [VeSyncBulbInstances]
manager.devices.purifiers = [VeSyncPurifierInstances]
manager.devices.humidifiers = [VeSyncHumidifierInstances]
manager.devices.air_fryers = [VeSyncAirFryerInstances]
managers.devices.thermostats = [VeSyncThermostatInstances]
```

### Debugging and Getting Help

The library has built-in debug logging that can be enabled by setting the log level of the `pyvesync` logger to `DEBUG`. This will log the API calls and response codes to the console.

```python
import logging
from pyvesync import VeSync
# To enable debug logging:

vs_logger = logging.getLogger("pyvesync")
vs_logger.setLevel(logging.DEBUG)

async def main():
    async with VeSync(username="EMAIL", password="PASSWORD") as manager:
        await manager.login()
        await manager.update()
```

### Logging to a File

Since verbose debugging can output a lot of information, there is a helper function to log to a file instead of the console. This will automatically set the logging level to `DEBUG` and log all API calls and responses to the specified file. Optionally, logging to stdout can also be enabled.

```python
from pyvesync import VeSync

async def main():
    async with VeSync(username="EMAIL", password="PASSWORD") as manager:
        manager.debug = True  # Enable debug logging
        manager.verbose = True  # Enable verbose logging
        await manager.log_to_file("debug.log", stdout=True)  # Can be an absolute or path relative to the current working directory
        await manager.login()
        await manager.get_devices()
```

### Authentication

The `VeSync` object requires username and password to be instantiated, but once logged in the token and account_id can be stored and reused to prevent logging in every time. The `VeSync.auth` attribute holds the authentication logic and credentials with the `pyvesync.auth.VeSyncAuth` class. Username and password are required because the token can expire after a period of time. See the [Authentication](./authentication.md) and [VeSync](./development/vesync_api.md) documentation for more details.

```python
from pyvesync import VeSync


async def main():
    async with VeSync(username="EMAIL", password="PASSWORD") as manager:
        await manager.login()  # Login with username and password
        if not manager.enabled:
            print("Login failed")
            return

        # Save credentials to file
        await manager.save_credentials("/path/to/token_file")
        # Will save to user's home directory as .vesync_token if no path is provided

        # Load credentials from file
        await manager.load_credentials_from_file("/path/to/token_file")
        # Calling with no argument will load the .vesync_token file from user's home directory and then the current working directory.

        # Or set credentials directly
        creds = {
            "token": "your_token",
            "account_id": "your_account_id",
            "country_code": "US"  # Optional
            "region": "US"  # Optional
        }
        manager.set_credentials(**creds)

        # Output credentials as JSON string
        await manager.output_credentials_json()
        # or as a dictionary
        await manager.output_credentials_dict()

        # No login needed if token is valid
        # await manager.login()
```

## Device Usage

Devices and their attributes and methods can be accessed via the device lists in the manager instance.

One device is simple to access, an outlet for example:

```python
for devices in manager.outlets:
    print(outlet)
    print(outlet.device_name)
    print(outlet.device_type)
    print(outlet.sub_device_no)
    print(outlet.state)
```

The last response information is stored in the `last_response` attribute of the device and returns the [`ResponseInfo`][pyvesync.utils.errors.ResponseInfo] object.

```python
# Get the last response information
print(outlet.last_response)
ResponseInfo(
    error_name="SUCCESS",
    error_type=SUCCESS,  # StrEnum from ErrorTypes class
    message="Success",
    critical_error=False,
    operational_error=False,
    device_online=True,
)
```

### Device State

All device state information is stored in a separate object in the `device.state` attribute. Each device has it's own state class that inherits from the `pyvesync.base_devices.vesyncbasedevice.DeviceState` class. The state object is updated when the device is updated, so it will always be the most recent state of the device. Each product type has it's own state class that hold all available attribute for every device type supported for that product type. For example, purifiers have the `PurifierState` class, which holds all attributes, some of which may not be supported by all devices.

```python
print(outlet.state.device_status)
DeviceStatus.ON  # StrEnum representing the "on" state

print(outlet.state.connection_status)
ConnectionStatus.ONLINE  # StrEnum representing the "online" state

print(outlet.state.voltage)
120.0  # Voltage of the device

```

For a full listing of available device attributes and methods, see the individual device documentation:

1. [Outlets](./devices/outlets.md)
2. [Bulbs](./devices/bulbs.md)
3. [Switches](./devices/switches.md)
4. [Purifiers](./devices/air_purifiers.md)
5. [Humidifiers](./devices/humidifiers.md)
6. [Fans](./devices/fans.md)
7. [Air Fryers](./devices/kitchen.md)
8. [Thermostats](./devices/thermostats.md)


## Serializing/Deserializing devices and state

All devices have the `to_json()` and `to_jsonb()` methods which will serialize the device and state to a JSON string or binary json string.

```python

device = manager.outlets[0]
print(device.to_json(state=True, indent=True))  # JSON string
# Setting `state=False` will only serialize the attributes in the device class and not the state class

print(device.to_jsonb(state=True))  # Binary JSON string

# State classes also have the `to_json()` and `to_jsonb()` methods but this does not include any device information, such as device_name, device_type, etc.
print(device.state.to_json(indent=True))  # JSON string
```

Devices and state objects can also output to a dictionary using the `to_dict()` method or as a list of tuples with `as_tuple()`. This is useful for logging or debugging.

```python
device = manager.outlets[0]
dev_dict = device.to_dict(state=True)  # Dictionary of device and state attributes
dev_dict["device_name"]  # Get the device name from the dictionary
dev_dict["device_status"] # Returns device status as a StrEnum
```

## Custom Exceptions

Exceptions are no longer caught by the library and must be handled by the user. Exceptions are raised by server errors and aiohttp connection errors.

Errors that occur at the aiohttp level are raised automatically and propogated to the user. That means exceptions raised by aiohttp that inherit from `aiohttp.ClientError` are propogated.

When the connection to the VeSync API succeeds but returns an error code that prevents the library from functioning a custom exception inherrited from `pyvesync.logs.VeSyncError` is raised.

Custom Exceptions raised by all API calls:

- `pyvesync.logs.VeSyncServerError` - The API connected and returned a code indicated there is a server-side error.
- `pyvesync.logs.VeSyncRateLimitError` - The API's rate limit has been exceeded.
- `pyvesync.logs.VeSyncAPIStatusCodeError` - The API returned a non-200 status code.
- `pyvesync.logs.VeSyncAPIResponseError` - The response from the API was not in an expected format.

Login API Exceptions

- `pyvesync.logs.VeSyncLoginError` - The username or password is incorrect.

See [errors](https://webdjoe.github.io/pyvesync/latest/development/utils/errors) documentation for a complete list of error codes and exceptions.

The [raise_api_errors()](https://webdjoe.github.io/pyvesync/latest/development/utils/errors/#pyvesync.utils.errors.raise_api_errors) function is called for every API call and checks for general response errors. It can raise the following exceptions:

- `VeSyncServerError` - The API connected and returned a code indicated there is a server-side error.
- `VeSyncRateLimitError` - The API's rate limit has been exceeded.
- `VeSyncAPIStatusCodeError` - The API returned a non-200 status code.
- `VeSyncTokenError` - The API returned a token error and requires `login()` to be called again.
- `VeSyncLoginError` - The user name or password is incorrect.

## Development

For details on the structure and architecture of the library, see the [Development](./development/index.md) documentation.
