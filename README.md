# pyvesync [![build status](https://img.shields.io/pypi/v/pyvesync.svg)](https://pypi.python.org/pypi/pyvesync) [![Build Status](https://dev.azure.com/webdjoe/pyvesync/_apis/build/status/webdjoe.pyvesync?branchName=master)](https://dev.azure.com/webdjoe/pyvesync/_build/latest?definitionId=4&branchName=master) [![Open Source? Yes!](https://badgen.net/badge/Open%20Source%20%3F/Yes%21/blue?icon=github)](https://github.com/Naereen/badges/) [![PyPI license](https://img.shields.io/pypi/l/ansicolortags.svg)](https://pypi.python.org/pypi/ansicolortags/) <!-- omit in toc -->

pyvesync is a library to manage VeSync compatible [smart home devices](#supported-devices)

<a href="https://webdjoe.github.io/pyvesync/latest"><img src="./docs/assets/docs.svg"></a>

**Check out the new [pyvesync documentation](https://webdjoe.github.io/pyvesync/) for usage and full API details.**

## Supported Product Types

1. Outlets
2. Switches
3. Fans
4. Air Purifiers
5. Humidifiers
6. Bulbs
7. Air Fryers
8. Thermostats

See the [supported devices](https://webdjoe.github.io/pyvesync/latest/supported_devices/) page for a complete list of supported devices and device types.

## What's new in pyvesync 3.0

**BREAKING CHANGES** - The release of pyvesync 3.0 comes with many improvements and new features, but as a result there are many breaking changes. The structure has been completely refactored, so please read through the README and thoroughly test before deploying.

The goal is to standardize the library across all devices to allow easier and consistent maintainability moving forward. The original library was created 8 years ago for supporting only a few outlets, it was not designed for supporting 20+ different devices.

Some of the changes are:

- Asynchronous network requests with aiohttp.
- Strong typing of all network requests and responses.
- Created base classes for all devices for easier `isinstance` checks.
- Separated the instantiated devices to a `DeviceContainer` class that acts as a mutable set with convenience methods.
- Standardized the API for all device to follow a common naming convention. No more devices with different names for the same functionality.
- Implemented custom exceptions and error (code) handling for API responses.
- `const` module to hold all library constants
- Built the `DeviceMap` class to hold the mapping and features of devices.
- COMING SOON: Use API to pull device modes and operating features.

See [pyvesync V3](https://webdjoe.github.io/pyvesync/latest/pyvesync3/) for more information on the changes.

### Asynchronous operation

Library is now asynchronous, using aiohttp as a replacement for requests. The `pyvesync.VeSync` class is an asynchronous context manager. A `aiohttp.ClientSession` can be passed or created internally.

```python
import asyncio
import aiohttp
from pyvesync.vesync import VeSync

async def main():
    async with VeSync(
        username="user",
        password="password",
        country_code="US",  # Optional - country Code to select correct server
        session=session,  # Optional - aiohttp.ClientSession
        time_zone="America/New_York",  # Optional - Timezone, defaults to America/New_York
        debug=False,  # Optional - Debug output
        redact=True  # Optional - Redact sensitive information from logs
        ) as manager:

        # To enable debug mode - prints request and response content for
        # api calls that return an error code
        manager.debug = True
        # Redact mode is enabled by default, set to False to disable
        manager.redact = False

        # To print request & response content for all API calls enable verbose mode
        manager.verbose = True

        # To print logs to file
        manager.log_to_file("pyvesync.log")

        await manager.login()
        if not manager.enabled:
            print("Not logged in.")
            return
        await manager.get_devices() # Instantiates supported devices in device list, automatically called by login, only needed if you would like updates
        await manager.update() # Updates the state of all devices

        # manager.devices is a DeviceContainer object
        # manager.devices.outlets is a list of VeSyncOutlet objects
        # manager.devices.switches is a list of VeSyncSwitch objects
        # manager.devices.fans is a list of VeSyncFan objects
        # manager.devices.bulbs is a list of VeSyncBulb objects
        # manager.devices.humidifiers is a list of VeSyncHumid objects
        # manager.devices.air_purifiers is a list of VeSyncAir objects
        # manager.devices.air_fryers is a list of VeSyncAirFryer objects
        # manager.devices.thermostats is a list of VeSyncThermostat objects

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

### VeSync Class Signature

The VeSync signature is:

```python
VeSync(
    username: str,
    password: str,
    country_code: str = DEFAULT_COUNTRY_CODE,  # US
    session: ClientSession | None = None,
    time_zone: str = DEFAULT_TZ  # America/New_York
    debug: bool = False,
    redact: bool = True,
    )
```

### Product Types

There is a new nomenclature for product types that defines the device class. The
`device.product_type` attribute defines the product type based on the VeSync API. The product type is used to determine the device class and module. The currently supported product types are:

1. `outlet` - Outlet devices
2. `switch` - Wall switches
3. `fan` - Fans (not air purifiers or humidifiers)
4. `purifier` - Air purifiers (not humidifiers)
5. `humidifier` - Humidifiers (not air purifiers)
6. `bulb` - Light bulbs (not dimmers or switches)
7. `airfryer` - Air fryers

See [Supported Devices](#supported-devices) for a complete list of supported devices and models.

### Custom Exceptions

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
- `VeSyncLoginError` - The username or password is incorrect.

## Installation

Install the latest version from pip:

```bash
pip install pyvesync
```

<!--SUPPORTED DEVICES START-->

## Supported Devices

<!--SUPPORTED OUTLETS START-->

### Etekcity Outlets

1. Voltson Smart WiFi Outlet- Round (7A model ESW01-USA)
2. Voltson Smart WiFi Outlet - Round (10A model ESW01-EU)
3. Voltson Smart Wifi Outlet - Round (10A model ESW03-USA)
4. Voltson Smart Wifi Outlet - Round (10A model ESW10-USA)
5. Voltson Smart WiFi Outlet - Rectangle (15A model ESW15-USA)
6. Two Plug Outdoor Outlet (ESO15-TB) (Each plug is a separate `VeSyncOutlet` object, energy readings are for both plugs combined)

<!--SUPPORTED OUTLETS END-->

<!--SUPPORTED SWITCHES START-->

### Wall Switches

1. Etekcity Smart WiFi Light Switch (model ESWL01)
2. Etekcity Wifi Dimmer Switch (ESD16)

<!--SUPPORTED SWITCHES END-->

### Levoit Air Purifiers

1. LV-PUR131S
2. Core 200S
3. Core 300S
4. Core 400S
5. Core 600S
6. Vital 100S
7. Vital 200S
8. Everest Air

### Etekcity Bulbs

1. Soft White Dimmable Smart Bulb (ESL100)
2. Cool to Soft White Tunable Dimmable Bulb (ESL100CW)

### Valceno Bulbs

1. Valceno Multicolor Bulb (XYD0001)

### Levoit Humidifiers

1. Dual 200S
2. Classic 300S
3. LV600S
4. OasisMist 450S
5. OasisMist 600S
6. OasisMist 1000S

### Cosori Air Fryer

1. Cosori 3.7 and 5.8 Quart Air Fryer

### Fans

1. 42 in. Tower Fan

<!--SUPPORTED DEVICES END-->

## Usage

```python
import asyncio
from pyvesync import VeSync
from pyvesync.logs import VeSyncLoginError

# VeSync is an asynchronous context manager
# VeSync(username, password, debug=False, redact=True, session=None)

async def main():
    async with VeSync("user", "password") as manager:
        await manager.login()
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

If you want to reuse your token and account_id between runs. The `VeSync.auth` object holds the credentials and helper methods to save and load credentials.

```python
import asyncio
from pyvesync import VeSync
from pyvesync.logs import VeSyncLoginError

# VeSync is an asynchronous context manager
# VeSync(username, password, debug=False, redact=True, session=None)

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




Devices are stored in the respective lists in the instantiated `VeSync` class:

```python
await manager.login()  # Asynchronous
await manager.update()  # Asynchronous


# Acts as set with properties that return product type lists
manager.devices = DeviceContainer instance

manager.devices.outlets = [VeSyncOutletInstances]
manager.devices.switches = [VeSyncSwitchInstances]
manager.devices.fans = [VeSyncFanInstances]
manager.devices.bulbs = [VeSyncBulbInstances]
manager.devices.air_purifiers = [VeSyncPurifierInstances]
manager.devices.humidifiers = [VeSyncHumidifierInstances]
manager.devices.air_fryers = [VeSyncAirFryerInstances]
managers.devices.thermostats = [VeSyncThermostatInstances]

# Get device by device name
dev_name = "My Device"
for device in manager.devices:
  if device.device_name == dev_name:
    my_device = device
    device.display()

# Turn on switch by switch name
switch_name = "My Switch"
for switch in manager.devices.switches:
  if switch.device_name == switch_name:
    await switch.turn_on()   # Asynchronous
```

See the [device documentation](https://webdjoe.github.io/pyvesync/latest/devices/) for more information on the device classes and their methods/states.

## Debug mode and redact

To make it easier to debug, there is a `debug` argument in the `VeSync` method. This prints out your device list and any other debug log messages.

The `redact` argument removes any tokens and account identifiers from the output to allow for easier sharing. The `redact` argument has no impact if `debug` is not `True`.

```python
import asyncio
import aiohttp
from pyvesync.vesync import VeSync

async def main():
    async with VeSync("user", "password") as manager:
        manager.debug = True
        manager.redact = True  # True by default
        await manager.login()
        await manager.update()

        outlet = manager.outlets[0]
        await outlet.update()
        await outlet.turn_off()
        outlet.display()


if __name__ == "__main__":
    asyncio.run(main())
```

## Feature Requests

Before filing an issue to request a new feature or device, please ensure that you will take the time to test the feature throuroughly. New features cannot be simply tested on Home Assistant. A separate integration must be created which is not part of this library. In order to test a new feature, clone the branch and install into a new virtual environment.

```bash
mkdir python_test && cd python_test

# Check Python version is 3.11 or higher
python3 --version # or python --version or python3.8 --version
# Create a new venv
python3 -m venv pyvesync-venv
# Activate the venv on linux
source pyvesync-venv/bin/activate
# or ....
pyvesync-venv\Scripts\activate.ps1 # on powershell
pyvesync-venv\Scripts\activate.bat # on command prompt

# Install branch to be tested into new virtual environment:
pip install git+https://github.com/webdjoe/pyvesync.git@BRANCHNAME

# Install a PR that has not been merged:
pip install git+https://github.com/webdjoe/pyvesync.git@refs/pull/PR_NUMBER/head
```

Test functionality with a script, please adjust methods and logging statements to the device you are testing.

`test.py`

```python
import asyncio
import sys
import logging
import json
from functool import chain
from pyvesync import VeSync

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

USERNAME = "YOUR USERNAME"
PASSWORD = "YOUR PASSWORD"

DEVICE_NAME = "Device" # Device to test

async def test_device():
    # Instantiate VeSync class and login
  async with VeSync(USERNAME, PASSWORD, debug=True, redact=True) as manager:
      await manager.login()

      # Pull and update devices
      await manager.update()

      for dev in manager.devices:
          # Print all device info
          logger.debug(dev.device_name + "\n")
          logger.debug(dev.display())

          # Find correct device
          if dev.device_name.lower() != DEVICE_NAME.lower():
              logger.debug("%s is not %s, continuing", self.device_name, DEVICE_NAME)
              continue

          logger.debug('--------------%s-----------------' % dev.device_name)
          logger.debug(dev.display())
          logger.debug(dev.displayJSON())
          # Test all device methods and functionality
          # Test Properties
          logger.debug("Fan is on - %s", dev.is_on)
          logger.debug("Modes - %s", dev.modes)
          logger.debug("Fan Level - %s", dev.fan_level)
          logger.debug("Fan Air Quality - %s", dev.air_quality)
          logger.debug("Screen Status - %s", dev.screen_status)

          logger.debug("Turning on")
          await fan.turn_on()
          logger.debug("Device is on %s", dev.is_on)

          logger.debug("Turning off")
          await fan.turn_off()
          logger.debug("Device is on %s", dev.is_on)

          logger.debug("Sleep mode")
          fan.sleep_mode()
          logger.debug("Current mode - %s", dev.details['mode'])

          fan.auto_mode()

          logger.debug("Set Fan Speed - %s", dev.set_fan_speed)
          logger.debug("Current Fan Level - %s", dev.fan_level)
          logger.debug("Current mode - %s", dev.mode)

          # Display all device info
          logger.debug(dev.display(state=True))
          logger.debug(dev.to_json(state=True, indent=True))
          dev_dict = dev.to_dict(state=True)

if __name__ == "__main__":
    logger.debug("Testing device")
    asyncio.run(test_device())
...

```

## Device Requests

SSL pinning makes capturing packets much harder. In order to be able to capture packets, SSL pinning needs to be disabled before running an SSL proxy. Use an Android emulator such as Android Studio, which is available for Windows and Linux for free. Download the APK from APKPure or a similiar site and use [Objection](https://github.com/sensepost/objection) or [Frida](https://frida.re/docs/gadget/). Followed by capturing the packets with Charles Proxy or another SSL proxy application.

Be sure to capture all packets from the device list and each of the possible device menus and actions. Please redact the `accountid` and `token` from the captured packets. If you feel you must redact other keys, please do not delete them entirely. Replace letters with "A" and numbers with "1", leave all punctuation intact and maintain length.

For example:

Before:

```json
{
  "tk": "abc123abc123==3rf",
  "accountId": "123456789",
  "cid": "abcdef12-3gh-ij"
}
```

After:

```json
{
  "tk": "AAA111AAA111==1AA",
  "accountId": "111111111",
  "cid": "AAAAAA11-1AA-AA"
}
```

## Contributing

All [contributions](CONTRIBUTING.md) are welcome.

This project is licensed under [MIT](LICENSE).

## Contributors

This is an open source project and cannot exist without the contributions of its community. Thank you to all the contributors who have helped make this project better!

A special thanks for helping with V3 go live:

| [<img src="https://github.com/cdninja.png" width="60px;"/><br /><sub><a href="https://github.com/cdninja">cdninja</a></sub>](https://github.com/cdninja) | [<img src="https://github.com/sapuseven.png" width="60px;"/><br /><sub><a href="https://github.com/sapuseven">sapuseven</a></sub>](https://github.com/sapuseven) | [<img src="https://github.com/sdrapha.png" width="60px;"/><br /><sub><a href="https://github.com/sdrapha">sdrapha</a></sub>](https://github.com/sdrapha) |
| :------- | :------- | :------- |

And to all of those that contributed to the project:

<a href="https://github.com/webdjoe/pyvesync/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=webdjoe/pyvesync" />
</a>

Made with [contrib.rocks](https://contrib.rocks).
