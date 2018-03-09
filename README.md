pyvesync [![build status](https://img.shields.io/pypi/v/pyvesync.svg)](https://pypi.python.org/pypi/pyvesync)
========


pyvesync is a library to manage Etekcity Switches.


Installation
------------

Install the latest version from pip:

```python
pip install pyvesync
```


Usage
-----

To start with the module:

```python
from pyvesync.vesync import VeSync

manager = VeSync("USERNAME", "PASSWORD")
manager.login()
manager.update()

# Get electricity metrics of devices
for switch in manager.devices:
    print("Switch %s is currently using %s watts" % (switch.device_name, switch.get_power()))
    print("It has used %skWh of electricity today" % (switch.get_kwh_today()))

# Turn on the first device
my_switch = manager.devices[0]
print("Turning on switch '%s'" % (my_switch.device_name))
my_switch.turn_on()
```


Manager API
-----------

`VeSync.get_devices()` - Returns a list of devices

`VeSync.login()` - Uses class username and password to login to VeSync

`VeSync.update()` - Fetch updated information about devices


Device API
----------

`VeSyncSwitch.get_active_time()` - Return active time of a device in minutes

`VeSyncSwitch.get_kwh_today()` - Return total kWh for current date of a device

`VeSyncSwitch.get_power()` - Return current power in watts of a device

`VeSyncSwitch.turn_on()` - Turn on a device

`VeSyncSwitch.turn_off()` - Turn off a device

`VeSyncSwitch.update()` - Fetch updated information about device


Notes
-----

VeSync switches controlled through the Etekcity api do not always respond to the initial request for turn_on() and turn_off(). Retrying once or twice as needed often works.
