# Quick Start Guide

This is a quick start guide to get you up and running with the library. Each device has it's own properties and methods that can be found on the specific [device pages](./devices/index.md).

## Installing

### On Linux

You can install the library using pip or from source. The library is compatible with Python 3.11 and higher.

Before either method of installation, make sure you have python 3.11 or later and the following packages installed:

```bash
sudo apt install python3-venv python3-pip git
```

#### Install from source

These are the directions for installing the library from source in a folder in the `$HOME` directory. Change the first line `cd ~` to the directory you want to install the library in if `$HOME` is not suitable.

The git checkout line is used to switch to the appropriate branch. If you are using `master`, then you can skip this line. The `dev-2.0` branch is the latest development branch and may contain breaking changes.

```bash
cd ~
git clone https://github.com/webdjoe/pyvesync.git
cd pyvesync
git checkout dev-2.0
```

Then create a new virtual environment and install the library.

```bash
# Starting in the pyvesync directory
# Check Python version is 3.11 or higher - or python3.11 --version
python3 --version
# Create a new venv - or use python3.11 -m venv venv
python3 -m venv venv
# Activate the virtual environment
source venv/bin/activate
# Install the library
pip install .
```

#### Install via pip from github

This method installs the library or a specific branch from the repository. The `BRANCHNAME` is the name of the branch you want to install.

```bash
cd ~
mkdir pyvesync && cd pyvesync

# Check Python version is 3.11 or higher - or python3.11 --version
python3 --version
# Create a new venv
python3 -m venv venv
# Activate the venv on linux
source venv/bin/activate

# Install branch to be tested into new virtual environment:
pip install git+https://github.com/webdjoe/pyvesync.git@dev-2.0

# Install a PR that has not been merged using the PR number:
pip install git+https://github.com/webdjoe/pyvesync.git@refs/pull/{PR_NUMBER}/head

# Or if you are installing the latest release:
pip install pyvesync
```

### On Windows

You can install the library using pip or from source. The library is compatible with Python 3.11 and higher.
The instructions are similar to the Linux instructions with a few differences.

Before either method of installation, make sure you have python 3.11 or later and have git installed. You can download git from [git-scm.com](https://git-scm.com/downloads).

#### Windows from source

This method installs the library from source in a folder in the `%USERPROFILE%` directory. Change the first line `cd %USERPROFILE%` to the directory you want to install the library in if `%USERPROFILE%` is not suitable.

```powershell
cd %USERPROFILE%
git clone "https://github.com/webdjoe/pyvesync.git"
cd pyvesync
git checkout dev-2.0

# Check python version is 3.11 or higher
python --version # or python3 --version
# Create a new venv
python -m venv venv
# Activate the virtual environment
.\venv\Scripts\activate.ps1 # If you are using PowerShell
.\venv\Scripts\activate.bat # If you are using cmd.exe

# Install the library
pip install .
```

#### Windows via pip from github
This method installs the library or a specific branch from the repository. The `BRANCHNAME` is the name of the branch you want to install.

```powershell
cd %USERPROFILE%
mkdir pyvesync && cd pyvesync
python --version # Check python version is 3.11 or higher
python -m venv venv # Create a new venv
.\venv\Scripts\activate.ps1 # Activate the venv on PowerShell
# OR
.\venv\Scripts\activate.bat # Activate the venv on cmd.exe

# Install branch to be tested into new virtual environment:
pip install git+https://github.com/webdjoe/pyvesync.git@dev-2.0
# Install a PR that has not been merged using the PR number:
pip install git+https://github.com/webdjoe/pyvesync.git@refs/pull/{PR_NUMBER}/head
# Or if you are installing the latest release:
pip install pyvesync
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

Devices are held in the `manager.devices` attribute, which is the instance of [`DeviceContainer`][pyvesync.device_container.DeviceContainer] that acts as a mutable set. The entire device list can be iterated over or there are properties for each product type that return a list of those device instances. For example, to get all the outlets, use `manager.devices.outlets` or `manager.devices.purifiers`.

```python
import asyncio
from pyvesync import VeSync
from pyvesync.const import DeviceStatus  # This is a device constant StrEnum

USER = "EMAIL"
PASSWORD = "PASSWORD"

async def main():
    manager = VeSync(username=USER, password=PASSWORD)
    await manager.login() # Login to the VeSync account
    if not manager.enabled:
        print("Login failed")
        return
    await manager.get_devices() # Get devices
    await manager.update() # Update all devices
    for device in manager.devices:
        print(device) # Print the device name and type
        await device.update() # Update the device state, this is not required if `manager.update()` has already been called.
        print(device.state) # Print the device state

        # Turn on or off the device
        await device.turn_on() # Turn on the device
        await device.turn_off() # Turn off the device

        # Toggle the device state
        await device.toggle() # Toggle the device state
    for outlet in manager.devices.outlets:
        print(outlet)
        await outlet.update() # Update the outlet state this is not required if `manager.update()` has already been called.
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

## Device Specific Scripts

This section contains scripts that illustrate the functionality of each product type. The scripts are not exhaustive and are meant to be used as a starting point for your own scripts.
