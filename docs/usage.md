# Quick Start Guide

This is a quick start guide to get you up and running with the library. Each device has it's own properties and methods that can be found on the specific [device pages](./devices/index.md).

## Installing

```bash
mkdir python_test && cd python_test

# Check Python version is 3.11 or higher
python3 --version # or python --version or python3.11 --version
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

## Running the Library

The `pyvesync.VeSync` object is the main entrypoint of the library. It is an asynchronous context manager, so it must be used with `async with`. The `VeSync` object is the main object that is used to interact with the library. It is responsible for logging in, getting devices, and updating devices. It is referred to as `manager` in the examples.

```python
import asyncio
from pyvesync import VeSync

async def main():
    # Create a new VeSync object
    async with VeSync(username="EMAIL", password="PASSWORD") as manager:

        # To enable debugging
        manager.debug = True

        # Login to the VeSync account
        await manager.login()

        # Check if logged in
        assert manager.enabled

        # Get devices
        await manager.get_devices()

        # Update all devices
        await manager.update()

        # OR Iterate through devices and update individually
        for device in manager.outlets:
            await device.update()
```

Devices are held in the `manager.devices` attribute, which acts as a mutable set. There are properties for each product type that return a list of those device instances. For example, to get all the outlets, use `manager.devices.outlets` or `manager.devices.purifiers`.

```python

async def main():
    # I've excluded the login and get_devices methods for simplicity.
    for outlet in manager.devices.outlets:
        print(outlet)
        await outlet.update() # Update the outlet state
        await outlet.turn_on() # Turn on the outlet
        await outlet.turn_off() # Turn off the outlet
        await outlet.toggle() # Toggle the outlet state

        await outlet.set_timer(10, DeviceStatus.OFF) # Set a timer to turn off the outlet in 10 seconds
```

For more information on the device methods and properties, see the [device pages](./devices/index.md).

All devices have the ability to serialize the attributes and state with the `to_json()` and `to_jsonb()` methods. The `to_json()` method returns a JSON string, while the `to_jsonb()` method returns a JSON object. The `to_jsonb()` method is useful for storing the device state in a database or sending it to an API.

```python
async def main():
    # I've excluded the login and get_devices methods for simplicity.
    for outlet in manager.devices.outlets:
        print(outlet.to_json(state=True, indent=True)) # Print the JSON string of the outlet state
        print(outlet.to_jsonb(state=True)) # Print the JSON object of the outlet and state
        # Setting `state=False` will only show the static device attributes

        # State objects also have these methods
        print(outlet.state.to_json(state=True, indent=True)) # Print the JSON string of the outlet state
        print(outlet.state.to_jsonb(state=True)) # Print the JSON object of the outlet state
```

The `to_dict()` and `as_tuple()` methods are also available for each device and state object. The `to_dict()` method returns a dictionary of the device attributes, while the `as_tuple()` method returns a tuple of the device attributes.

They have the same signature as the `to_json()` and `to_jsonb()` methods.

```python
device_dict = outlet.to_dict(state=True) # Returns a dictionary of the outlet attributes
device_tuple = outlet.as_tuple(state=True) # Returns a tuple of the outlet attributes
```
