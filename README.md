# pyvesync [![build status](https://img.shields.io/pypi/v/pyvesync.svg)](https://pypi.python.org/pypi/pyvesync)

pyvesync is a library to manage VeSync compatible smart home devices.

## Installation

Install the latest version from pip:

```python
pip install pyvesync
```

## Supported Devices

1. Etekcity Voltson Smart WiFi Outlet (7A model ESW01-USA)
2. Etekcity Voltson Smart WiFi Outlet (10A model ESW01-EU)
3. Etekcity Voltson Smart Wifi Outlet (10A model ESW03-USA)
4. Etekcity Voltson Smart WiFi Outlet (15A model ESW15-USA)
5. Etekcity Smart WiFi Light Switch (model ESWL01)
6. Levoit Smart Wifi Air Purifier (LV-PUR131S)

## Usage

To start with the module:

```python
from pyvesync import VeSync

manager = VeSync("EMAIL", "PASSWORD", time_zone=DEFAULT_TZ)
manager.login()
manager.update()

my_switch = manager.outlets[0]
# Turn on the first switch
my_switch.turn_on()
# Turn off the first switch
my_switch.turn_off()

# Get energy usage data
manager.update_energy()

# Display outlet device information
for device in manager.outlets:
    device.display()
```

## Configuration

The `time_zone` argument is optional but the specified time zone must match time zone in the tz database (IANNA Time Zone Database), see this link for reference:
[tz database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
The time zone determines how the energy history is generated for the smart outlets, i.e. for the week starts at 12:01AM Sunday morning at the specified time zone.  If no time zone or an invalid time zone is entered the default is America/New_York

```python
#Devices are respectively located in their own lists that can be iterated over
manager.outlets = [VeSyncOutletObjects]
manager.switches = [VeSyncSwitchObjects]
manager.fans = [VeSyncFanObjects]
```

If outlets are going to be continuously polled, a custom energy update interval can be set - The default is 6 hours (21600 seconds)
```python
manager.energy_update_interval = time # time in seconds

#The interval check for energy updates can also be disabled (enabled by default)

manager.energy_update_check = False
```

## API Details
### Manager API

`VeSync.get_devices()` - Returns a list of devices

`VeSync.login()` - Uses class username and password to login to VeSync

`VeSync.update()` - Fetch updated information about devices

`VeSync.update_energy()` - Fetch updated energy information about devices


### Device API

`VeSyncDevice.turn_on()` - Turn on the device

`VeSyncDevice.turn_off()` - Turn off the device

`VeSyncDevice.update()` - Fetch updated information about device

`VeSyncDevice.active_time` - Return active time of the device in minutes

### Outlet Specific Energy API

`VeSyncOutlet.update_energy()` - Get outlet energy history - Builds week, month and year nested energy dictionary

`VeSyncOutlet.energy_today` - Return current energy usage in kWh

`VeSyncOutlet.power` - Return current power in watts of the device

`VeSyncOutlet.voltage` - Return current voltage reading

`VesyncOutlet.weekly_energy_total` - Return total energy reading for the past week in kWh, starts 12:01AM Sunday morning

`VesyncOutlet.monthly_energy_total` - Return total energy reading for the past month in kWh

`VesyncOutlet.yearly_energy_total` - Return total energy reading for the past year in kWh

### Model ESW15-USA 15A/1800W API
The rectangular smart switch model supports some additional functionality on top of the regular api call

`VeSyncOutlet.turn_on_nightlight()` - Turn on the nightlight

`VeSyncOutlet.turn_off_nightlight()` - Turn off the nightlight

### Air Purifier LV-PUR131S Functions

`VeSyncFan.fan_level` - Return the level of the fan (1-3) or 0 for off

`VeSyncFan.filter_life` - Return the percentage of filter life remaining

`VeSyncFan.auto_mode()` - Change mode to auto

`VeSyncFan.manual_mode()` - Change fan mode to manual with fan level 1

`VeSyncFan.sleep_mode()` - Change fan mode to sleep  

`VeSyncFan.fan_speed(speed)` - Change fan speed with level 1, 2 or 3

## Notes

More detailed data is available within the `VesyncOutlet` by inspecting the `VesyncOutlet.energy` dictionary.

The `VesyncOutlet.energy` object includes 3 nested dictionaries `week`, `month`, and `year` that contain detailed weekly, monthly and yearly data

```python
VesyncOutlet.energy['week']['energy_consumption_of_today']
VesyncOutlet.energy['week']['cost_per_kwh'] 
VesyncOutlet.energy['week']['max_energy']
VesyncOutlet.energy['week']['total_energy']
VesyncOutlet.energy['week']['data'] # which itself is a list of values
```

## Integration with Home Assistant

This library is integrated with Home Assistant and documentation can be found at https://www.home-assistant.io/components/vesync/. The library version included with Home Assistant may lag behind development compared to this repository so those wanting to use the latest version can do the following to integrate with HA.

1. Add a `custom_components` directory to your Home Assistant configuration directory
2. Add a `vesync` directory as a directory within `custom_components`
3. Add `switch.py` to the `vesync` directory so the following structure is in place `<config dir>/custom_components/vesync/switch.py`
4. Add `__init__.py` to the `vesync` directory so the following structure is in place `<config dir>/custom_components/vesync/__init__.py`
5. Add `manifest.json` to the `vesync` directory so the following structure is in place `<config dir>/custom_components/vesync/manifest.json`
6. Restart Home Assistant

The version of the library defined in `switch.py` should now get loaded within Home Assistant.
