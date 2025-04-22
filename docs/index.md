# pyvesync Library

[![build status](https://img.shields.io/pypi/v/pyvesync.svg)](https://pypi.python.org/pypi/pyvesync) [![Build Status](https://dev.azure.com/webdjoe/pyvesync/_apis/build/status/webdjoe.pyvesync?branchName=master)](https://dev.azure.com/webdjoe/pyvesync/_build/latest?definitionId=4&branchName=master) [![Open Source? Yes!](https://badgen.net/badge/Open%20Source%20%3F/Yes%21/blue?icon=github)](https://github.com/Naereen/badges/) [![PyPI license](https://img.shields.io/pypi/l/ansicolortags.svg)](https://pypi.python.org/pypi/ansicolortags/) <!-- omit in toc -->

pyvesync is a python library that interacts with devices that are connected to the VeSync app. The library can pull state details and perform actions to devices once they are set up in the app. This is not a local connection, the pyvesync library connects the VeSync cloud API, which reads and sends commands to the device, so internet access is required for both the device and library. There is no current method to control locally.

## What's New

**BREAKING CHANGES** - The release of pyvesync 3.0 comes with many improvements and new features, but as a result there are many breaking changes. The structure has been completely refactored, so please read through the documentation and thoroughly test before deploying.

The goal is to standardize the library across all devices to allow easier and consistent maintainability moving forward. The original library was created 8 years ago for supporting only a few outlets, it was not designed for supporting 20+ different devices.

This will likely cause breaking changes with existing code, but the new structure should be easier to work with and more consistent across all devices in the future.

Some of the major structural changes include:

- Asynchronous API calls through aiohttp
- `DeviceContainer` object holds all devices in a mutable set structure with additional convenience methods and properties for managing devices. This is located in the `VeSync.manager` attribute.
- Custom exceptions for better error handling - `VeSyncException`, `VeSyncAPIException`, `VeSyncLoginException`, `VeSyncRateLimitException`, `VeSyncNoDevicesException`
- Device state has been separated from the device object and is now managed by the subclasses of `DeviceState`. The state object is located in the `state` attribute of the device object.
- Device Classes have been refactored to be more consistent and easier to manage. No more random property and method names for different types of the same device.

See [pyvesync V2](./pyvesync3.md) for more details.

## Questions or Help?

If you have a bug or enhancement request for the pyvesync library, please submit an [issue](https://github.com/webdjoe/pyvesync/issues).

Looking to submit a request for a new device or have a general functionality question, check out [discussions](https://github.com/webdjoe/pyvesync/discussions).

For home assistant issues, please submit on that repository.

### New Devices

If you would like to add a new device, packet captures must be provided. The iOS and Android VeSync app implements certificate pinning to prevent standard MITM intercepts. Currently, the only known way is to patch the APK and run on a rooted android emulator with frida. This is a complex process that has had varying levels of success. If you successful in capturing packets, please capture all functionality, including the device list and configuraiton screen. Redact accountId and token keys or contact me for a more secure way to share.

## Supported Devices

The following product types are supported:

1. `outlet` - Outlet devices
2. `switch` - Wall switches
3. `fan` - Fans (not air purifiers or humidifiers)
4. `purifier` - Air purifiers (not humidifiers)
5. `humidifier` - Humidifiers (not air purifiers)
6. `bulb` - Light bulbs (not dimmers or switches)
7. `airfryer` - Air fryers

For a full listing of supported devices, see [Supported Devices](./supported_devices.md).

## General Usage

The `pyvesync.VeSync` object is the primary class that is referred to as the `manager` because it provides all the methods and properties to control the library. This should be the only class that is directly instantiated, all devices will be automatically pulled into instance attributes.

### VeSync Manager

The `VeSync` class has the following parameters, `username` and `password` are mandatory:

**BREAKING CHANGE** The VeSync object is now an asynchronous context manager, so it must be used with `async with`. The debug and redact argument have also been removed. To enable debug logging, set `manager.debug = True` and redacting by `manager.redact = True` to the instantiated object.

```python
from pyvesync import VeSync

# debug and redact are optional arguments, the above values are
# the defaults. The library will try to automatically pull in
# the correct time zone from the API responses.
async with VeSync(username="EMAIL", password="PASSWORD", time_zone=DEFAULT_TZ):

    # VeSync object is now instantiated
    await manager.login()
    # Check if logged in
    assert manager.enabled
    # Debug and Redact are optional arguments
    manager.debug = True
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

```

Once logged in, the next call should be to the `update()` method which:

- Retrieves list of devices from server
- Removes stale devices that are not present in the new API call
- Adds new devices to the device list attributes
- Instantiates all device classes
- Updates all devices via the device instance `update()` method

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

### Device Usage

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

The last response information is stored in the `last_response` attribute of the device and returns the `ResponseInfo` object.

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

## Development

For details on the structure and architecture of the library, see the [Development](./development/index.md) documentation.
