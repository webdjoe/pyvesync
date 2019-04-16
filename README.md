pyvesync [![build status](https://img.shields.io/pypi/v/pyvesync.svg)](https://pypi.python.org/pypi/pyvesync)
========


pyvesync is a library to manage Etekcity Switches.


Installation
------------

Install the latest version from pip:

```python
pip install pyvesync
```


Supported Devices
-----------------

1. Etekcity Voltson Smart WiFi Outlet (7A model ESW01-USA)
2. Etekcity Voltson Smart WiFi Outlet (15A model ESW15-USA)
3. Etekcity Voltson Smart WiFi Outlet (10A model ESW01-EU)
4. Etekcity Smart WiFi Light Switch (model ESWL01)


Usage
-----

To start with the module:

```python
from pyvesync.vesync import VeSync

manager = VeSync("USERNAME", "PASSWORD")
manager.login()
manager.update()


# Get electricity metrics of devices
for s in manager.devices:
    s.update_energy() # Get energy history for each device
    print("switch %s is currently %s" % (s.device_name, s.device_status))
    print("  active time: %s, energy: %s, power: %s, voltage: %s" % (s.active_time(), s.energy_today(), s.power(), s.voltage()))
    print("  weekly energy: %s, monthly energy: %s, yearly energy: %s" % (s.weekly_energy_total(), s.monthly_energy_total(), s.yearly_energy_total()))

# Turn on the first device
my_switch = manager.devices[0]
print("Turning on switch '%s'" % (my_switch.device_name))
my_switch.turn_on()
print("Turning off switch '%s'" % (my_switch.device_name))
my_switch.turn_off()
```


Manager API
-----------

`VeSync.get_devices()` - Returns a list of devices

`VeSync.login()` - Uses class username and password to login to VeSync

`VeSync.update()` - Fetch updated information about devices


Device API
----------

`VeSyncSwitch.turn_on()` - Turn on the device

`VeSyncSwitch.turn_off()` - Turn off the device

`VeSyncSwitch.update()` - Fetch updated information about device

`VeSyncSwitch.active_time()` - Return active time of the device in minutes

`VeSyncSwitch.energy_today()` - Return current energy usage

`VeSyncSwitch.power()` - Return current power in watts of the device

`VeSyncSwitch.voltage()` - Return current voltage reading

`VeSyncSwitch.energy_update()` - Get switch energy history

`VesyncSwitch.weekly_energy_total()` - Return total energy reading for the past week, starts 12:01AM Sunday morning

`VesyncSwitch.monthly_energy_total()` - Return total energy reading for the past month

`VesyncSwitch.yearly_energy_total()` - Return total energy reading for the past year


Model ESW15-USA 15A/1800W API
---------------------------------
The rectangular smart switch model supports some additional functionality on top of the regular api call

`VeSyncSwitch.turn_on_nightlight()` - Turn on the nightlight

`VeSyncSwitch.turn_off_nightlight()` - Turn off the nightlight


Notes
-----

More detailed data is available within the `VesyncSwitch` by inspecting the `VesyncSwitch.energy` dictionary.

The `VesyncSwitch.energy` object includes 3 nested dictionaries `week`, `month`, and `year` that contain detailed weekly, monthly and yearly data

```
VesyncSwitch.energy['week']['energy_consumption_of_today']
VesyncSwitch.energy['week']['cost_per_kwh']
VesyncSwitch.energy['week']['max_energy']
VesyncSwitch.energy['week']['total_energy']
VesyncSwitch.energy['week']['data'] which itself is a list of values
```

The VeSync api is hit or miss with this data so access is currently limited to direct lookup calls

Integration with Home Assistant
-------------------------------

This library is integrated with Home Assistant and documentation can be found at https://www.home-assistant.io/components/vesync/. The library version included with Home Assistant may lag behind development within this repository so those wanting to use the latest version can do the following to integrate with HA

1. Add a `custom_components` directory to your Home Assistant configuration directory
2. Add a `vesync` directory as a directory within `custom_components`
3. Add `switch.py` to the `vesync` directory so the following structure is in place `<config dir>/custom_components/vesync/switch.py`
4. Restart Home Assistant

The version of the library defined in `switch.py` should now get loaded within Home Assistant