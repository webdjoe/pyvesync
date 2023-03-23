# pyvesync [![build status](https://img.shields.io/pypi/v/pyvesync.svg)](https://pypi.python.org/pypi/pyvesync) [![Build Status](https://dev.azure.com/webdjoe/pyvesync/_apis/build/status/webdjoe.pyvesync?branchName=master)](https://dev.azure.com/webdjoe/pyvesync/_build/latest?definitionId=4&branchName=master) [![Open Source? Yes!](https://badgen.net/badge/Open%20Source%20%3F/Yes%21/blue?icon=github)](https://github.com/Naereen/badges/) [![PyPI license](https://img.shields.io/pypi/l/ansicolortags.svg)](https://pypi.python.org/pypi/ansicolortags/) <!-- omit in toc -->

pyvesync is a library to manage VeSync compatible [smart home devices](#supported-devices)

## Table of Contents <!-- omit in toc -->

- [Installation](#installation)
- [Supported Devices](#supported-devices)
  - [Etekcity Outlets](#etekcity-outlets)
  - [Wall Switches](#wall-switches)
  - [Levoit Air Purifiers](#levoit-air-purifiers)
  - [Etekcity Bulbs](#etekcity-bulbs)
  - [Valceno Bulbs](#valceno-bulbs)
  - [Levoit Humidifiers](#levoit-humidifiers)
- [Usage](#usage)
- [Configuration](#configuration)
  - [Time Zones](#time-zones)
  - [Outlet energy data update interval](#outlet-energy-data-update-interval)
- [Example Usage](#example-usage)
  - [Get electricity metrics of outlets](#get-electricity-metrics-of-outlets)
- [API Details](#api-details)
  - [Manager API](#manager-api)
  - [Standard Device API](#standard-device-api)
    - [Standard Properties](#standard-properties)
    - [Standard Methods](#standard-methods)
  - [Outlet API Methods \& Properties](#outlet-api-methods--properties)
    - [Outlet power and energy API Methods \& Properties](#outlet-power-and-energy-api-methods--properties)
    - [Model ESW15-USA 15A/1800W Methods (Have a night light)](#model-esw15-usa-15a1800w-methods-have-a-night-light)
  - [Standard Air Purifier Properties \& Methods](#standard-air-purifier-properties--methods)
    - [Air Purifier Properties](#air-purifier-properties)
    - [Air Purifier Methods](#air-purifier-methods)
    - [Levoit Purifier Core200S/300S/400S Properties](#levoit-purifier-core200s300s400s-properties)
    - [Levoit Purifier Core200S/300S/400S Methods](#levoit-purifier-core200s300s400s-methods)
  - [Lights API Methods \& Properties](#lights-api-methods--properties)
    - [Brightness Light Bulb Method and Properties](#brightness-light-bulb-method-and-properties)
    - [Light Bulb Color Temperature Methods and Properties](#light-bulb-color-temperature-methods-and-properties)
    - [Multicolor Light Bulb Methods and Properties](#multicolor-light-bulb-methods-and-properties)
    - [Dimmable Switch Methods and Properties](#dimmable-switch-methods-and-properties)
  - [Levoit Humidifier Methods and Properties](#levoit-humidifier-methods-and-properties)
    - [Humidifier Properties](#humidifier-properties)
    - [Humidifer Methods](#humidifer-methods)
    - [600S warm mist feature](#600s-warm-mist-feature)
  - [Cosori Devices](#cosori-devices)
    - [Cosori 3.7 and 5.8 Quart Air Fryer](#cosori-37-and-58-quart-air-fryer)
      - [Air Fryer Properties](#air-fryer-properties)
      - [Air Fryer Methods](#air-fryer-methods)
  - [JSON Output API](#json-output-api)
    - [JSON Output for All Devices](#json-output-for-all-devices)
    - [JSON Output for Outlets](#json-output-for-outlets)
    - [JSON Output for Dimmable Switch](#json-output-for-dimmable-switch)
    - [JSON Output for Dimmable Bulb](#json-output-for-dimmable-bulb)
    - [JSON Output for Tunable Bulb](#json-output-for-tunable-bulb)
    - [JSON Output for Multicolor Bulb](#json-output-for-multicolor-bulb)
    - [JSON Output for Air Purifier](#json-output-for-air-purifier)
    - [JSON Output for 300S Humidifier](#json-output-for-300s-humidifier)
    - [JSON Output for Core200S Purifier](#json-output-for-core200s-purifier)
    - [JSON Output for 400S Purifier](#json-output-for-400s-purifier)
    - [JSON Output for 600S Purifier](#json-output-for-600s-purifier)
- [Notes](#notes)
- [Debug mode](#debug-mode)
- [Feature Requests](#feature-requests)


## Installation

Install the latest version from pip:

```bash
pip install pyvesync
```

## Supported Devices

### Etekcity Outlets

1. Voltson Smart WiFi Outlet- Round (7A model ESW01-USA)
2. Voltson Smart WiFi Outlet - Round (10A model ESW01-EU)
3. Voltson Smart Wifi Outlet - Round (10A model ESW03-USA)
4. Voltson Smart WiFi Outlet - Rectangle (15A model ESW15-USA)
5. Two Plug Outdoor Outlet (ESO15-TB) (Each plug is a separate `VeSyncOutlet` object, energy readings are for both plugs combined)

### Wall Switches
1. Etekcity Smart WiFi Light Switch (model ESWL01)
2. Etekcity Wifi Dimmer Switch (ESD16)

### Levoit Air Purifiers

1. LV-PUR131S
2. Core 200S
3. Core 300S
4. Core 400S
5. Core 600S

### Etekcity Bulbs

1. Soft White Dimmable Smart Bulb (ESL100)
2. Cool to Soft White Tunable Dimmable Bulb (ESL100CW)

### Valceno Bulbs
1. Multicolor Bulb (XYD0001)

### Levoit Humidifiers
1. Dual 200S
2. Classic 300S
3. LUH-D301S-WEU Dual (200S)
4. LV600S
5. OasisMist LUS-O415S-WUS

Cosori Air Fryer
1. Cosori 3.7 and 5.8 Quart Air Fryer

## Usage

To start with the module:

```python
from pyvesync import VeSync

manager = VeSync("EMAIL", "PASSWORD", "TIME_ZONE", debug=False)
manager.login()

# Get/Update Devices from server - populate device lists
manager.update()

my_switch = manager.outlets[0]
# Turn on the first switch
my_switch.turn_on()
# Turn off the first switch
my_switch.turn_off()

# Get energy usage data for outlets
manager.update_energy()

# Set bulb brightness to 75% of first bulb in the list
my_bulb = manager.bulbs[0]
my_bulb.set_brightness(75)
# get its details in JSON and print
print(my_bulb.displayJSON())
```
Devices are stored in the respective lists in the instantiated `VeSync` class:

```python
manager.login()
manager.update()

manager.outlets = [VeSyncOutletObjects]
manager.switches = [VeSyncSwitchObjects]
manager.fans = [VeSyncFanObjects]
manager.bulbs = [VeSyncBulbObjects]

# Get device (outlet, etc.) by device name
dev_name = "My Device"
for device in manager.outlets:
  if device.device_name == dev_name:
    my_device = device
    device.display()

# Turn on switch by switch name
switch_name = "My Switch"
for switch in manager.switches:
  if switch.device_name == switch_name:
    switch.turn_on()
```
## Configuration

### Time Zones
The `time_zone` argument is optional but the specified time zone must match time zone in the tz database (IANNA Time Zone Database), see this link for reference:
[tz database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
The time zone determines how the energy history is generated for the smart outlets, i.e. for the week starts at 12:01AM Sunday morning at the specified time zone.  If no time zone or an invalid time zone is entered the default is America/New_York

### Outlet energy data update interval
If outlets are going to be continuously polled, a custom energy update interval can be set - The default is 6 hours (21600 seconds)

```python
manager.energy_update_interval = 360 # time in seconds
```

## Example Usage

### Get electricity metrics of outlets

Bypass the interval check to trigger outlet energy update.
```python
for s in manager.outlets:
  s.update_energy(check_bypass=False) # Get energy history for each device
```

## API Details

### Manager API

`VeSync.get_devices()` - Returns a list of devices

`VeSync.login()` - Uses class username and password to login to VeSync

`VeSync.update()` - Fetch updated information about devices

`VeSync.update_all_devices()` - Fetch details for all devices (run `VeSyncDevice.update()`)

`VeSync.update_energy(bypass_check=False)` - Get energy history for all outlets - Builds week, month and year nested energy dictionary.  Set `bypass_check=True` to disable the library from checking the update interval

### Standard Device API

These properties and methods are available for all devices.

#### Standard Properties

`VeSyncDevice.device_name` - Name given when registering device

`VeSyncDevice.device_type` - Model of device, used to determine proper device class.

`VeSyncDevice.connection_status` - Device online/offline

`VeSyncDevice.config_module` - Special configuration identifier for device. Currently, not used in this API.

`VeSyncDevice.sub_device_no` - Sub-device number for certain devices. Used for the outdoor outlet.

`VeSyncDevice.device_status` - Device on/off

`VeSyncDevice.is_on` - Returns boolean True/False if device is on.

`VeSyncDevice.firmware_update` - Returns True is new firmware is available

#### Standard Methods

`VeSyncDevice.turn_on()` - Turn on the device

`VeSyncDevice.turn_off()` - Turn off the device

`VeSyncDevice.update()` - Fetch updated information about device

`VeSyncDevice.active_time` - Return active time of the device in minutes

`VeSyncDevice.get_config()` - Retrieve Configuration data such as firmware version for device and store in the `VeSyncDevice.config` dictionary

### Outlet API Methods & Properties

#### Outlet power and energy API Methods & Properties

`VeSyncOutlet.update_energy(bypass_check=False)` - Get outlet energy history - Builds week, month and year nested energy dictionary. Set `bypass_check=True` to disable the library from checking the update interval

`VeSyncOutlet.energy_today` - Return current energy usage in kWh

`VeSyncOutlet.power` - Return current power in watts of the device

`VeSyncOutlet.voltage` - Return current voltage reading

`VesyncOutlet.weekly_energy_total` - Return total energy reading for the past week in kWh, starts 12:01AM Sunday morning

`VesyncOutlet.monthly_energy_total` - Return total energy reading for the past month in kWh

`VesyncOutlet.yearly_energy_total` - Return total energy reading for the past year in kWh

#### Model ESW15-USA 15A/1800W Methods (Have a night light)

The rectangular smart switch model supports some additional functionality on top of the regular api call

`VeSyncOutlet.nightlight_status` - Get the status of the nightlight

`VeSyncOutlet.nightlight_brightness` - Get the brightness of the nightlight

`VeSyncOutlet.turn_on_nightlight()` - Turn on the nightlight

`VeSyncOutlet.turn_off_nightlight()` - Turn off the nightlight

### Standard Air Purifier Properties & Methods

#### Air Purifier Properties

`VeSyncFan.details` - Dictionary of device details

```python
VeSyncFan.update()

VeSyncFan.details = {
  'active_time': 30004, # minutes
  'filter_life': 45, # percent of filter life remaining
  'screen_status': 'on', # display on/off
  'level': 3, # fan level
  'air_quality': 2, # air quality level
}

```

NOTE: LV-PUR131S outputs `air_quality` as a string, such as `Excellent`

`VeSyncFan.features` - Unique features to air purifier model. Currently, the only feature is air_quality, which is not supported on Core 200S.

`VeSyncFan.modes` - Modes of operation supported by model - [sleep, off, auto]

`VeSyncFan.fan_level` - Return the level of the fan

`VeSyncFan.filter_life` - Return the percentage of filter life remaining

`VeSyncFan.air_quality` - Return air quality level as integer, 1 being the best - Not available on Core 200S

`VeSyncFan.air_quality_value` - PM2.5 air quality reading

`VeSyncFan.screen_status` - Get Status of screen on/off

#### Air Purifier Methods

`VeSyncFan.auto_mode()` - Change mode to auto

`VeSyncFan.manual_mode()` - Change fan mode to manual with fan level 1

`VeSyncFan.sleep_mode()` - Change fan mode to sleep

`VeSyncFan.change_fan_speed(speed=None)` - Change fan speed. Call without speed to toggle to next speed

Compatible levels for each model:
- Core 200S [1, 2, 3]
- Core 300S/400S [1, 2, 3, 4]
- PUR131S [1, 2, 3]

#### Levoit Purifier Core200S/300S/400S Properties

`VeSyncFan.child_lock` - Return the state of the child lock (True=On/False=off)

`VeSyncAir.night_light` - Return the state of the night light (on/dim/off)

#### Levoit Purifier Core200S/300S/400S Methods

`VeSyncFan.child_lock_on()` Enable child lock

`VeSyncFan.child_lock_off()` Disable child lock

`VeSyncFan.turn_on_display()` Turn display on

`VeSyncFan.turn_off_display()` Turn display off

`VeSyncFan.set_night_light('on'|'dim'|'off')` - Set night light brightness


### Lights API Methods & Properties

#### Brightness Light Bulb Method and Properties

*Compatible with all bulbs*
`VeSyncBulb.brightness` - Return brightness in percentage (1 - 100)

`VeSyncBulb.set_brightness(brightness)` - Set bulb brightness values from 1 - 100

#### Light Bulb Color Temperature Methods and Properties

**NOTE: only compatible with ESL100CW and Valceno Bulbs, NOT compatible with ESL100MC Bulbs**
`VeSyncBulb.color_temp_pct` - Return color temperature in percentage (0 - 100)

`VeSyncBulb.color_temp_kelvin` - Return brightness in Kelvin

`VeSyncBulb.set_color_temp(color_temp)` - Set white temperature in percentage (0 - 100)

#### Multicolor Light Bulb Methods and Properties

*Compatible with ESL100MC & Valceno Bulbs*
**Properties**
`VeSyncBulb.color` - Returns a dataclass with HSV and RGB attributes that are named tuples

```
VeSyncBulb.color.rbg = namedtuple('RGB', ['red', 'green', 'blue'])
VeSyncBulb.color.hsv = namedtuple('HSV', ['hue', 'saturation', 'value'])
```

`VeSyncBulb.color_hsv` - Returns a named tuple with HSV values

`VeSyncBulb.color_rgb` - Returns a named tuple with RGB values

`VeSyncBulb.color_mode` - Return bulb color mode (string values: 'white', 'color', 'hsv')

`VeSyncBulb.color_hue` - Return color hue (float values from 0.0 - 360.0)

`VeSyncBulb.color_saturation` - Return color saturation (float values from 0.0 - 100.0)

`VeSyncBulb.color_value` - Return color value (int values from 0 - 100)

*The following properties are also still available for backwards compatibility*
`VeSyncBulb.color_value_hsv` - Return color value in HSV named tuple format (hue: float 0.0-360.0, saturation: float 0.0-100.0, value: float 0-100 )

`VeSyncBulb.color_value_rgb` - Return color value in RGB named tuple format (red: float, green: float, blue: float 0-255.0)

**Methods**
`VeSyncBulb.set_hsv(hue, saturation, value)`

- Set bulb color in HSV format
- Arguments: hue (numeric) 0 - 360, saturation (numeric) 0-100, value (numeric) 0-100
- Returns bool

`VeSyncBulb.set_rgb(red, green, blue)`

- Set bulb color in RGB format
- Arguments: red (numeric) 0-255, green (numeric) 0-255, blue (numeric) 0-255
- Returns bool

`VeSyncBulb.enable_white_mode()`

- Turn bulb to white mode - returns bool

`VeSyncBulb.set_color_temp(color_temp)`

- Set bulb white temperature (int values from 0 - 100)
- Setting this will automatically force the bulb into White mode

`VeSyncBulb.set_status(brightness, color_temp, color_saturation, color_hue, color_mode color_value)`

- Set every property, in a single call
- All parameters are optional

**NOTE: Due to the varying API between bulbs, avoid setting the `color_mode` argument directly, instead set colors values with `set_hsv` or `set_rgb` to turn on color and use `enable_white_mode()` to turn off color.**

#### Dimmable Switch Methods and Properties

`VeSyncSwitch.brightness` - Return brightness of switch in percentage (1 - 100)

`VeSyncSwitch.indicator_light_status` - return status of indicator light on switch

`VeSyncSwitch.rgb_light_status` - return status of rgb light on faceplate

`VeSyncSwitch.rgb_light_value` - return dictionary of rgb light color (0 - 255)

`VeSyncSwitch.set_brightness(brightness)` - Set brightness of switch (1 - 100)

`VeSyncSwitch.indicator_light_on()` - Turn indicator light on

`VeSyncSwitch.indicator_light_off()` - Turn indicator light off

`VeSyncSwitch.rgb_color_on()` - Turn rgb light on

`VeSyncSwitch.rgb_color_off()` - Turn rgb light off

`VeSyncSwitch.rgb_color_set(red, green, blue)` - Set color of rgb light (0 - 255)

### Levoit Humidifier Methods and Properties

#### Humidifier Properties

The details dictionary contains all device status details

```python
VeSyncHumid.details = {
    'humidity': 80, # percent humidity in room
    'mist_virtual_level': 0, # Level of mist output 1 - 9
    'mist_level': 0,
    'mode': 'manual', # auto, manual, sleep
    'water_lacks': False,
    'humidity_high': False,
    'water_tank_lifted': False,
    'display': False,
    'automatic_stop_reach_target': False,
    'night_light_brightness': 0
    }
```

The configuration dictionary shows current settings

```python
VeSyncHumid.config = {
    'auto_target_humidity': 80, # percent humidity in room
    'display': True, # Display on/off
    'automatic_stop': False
    }
```

The LV600S has warm mist settings that show in the details dictionary in addition to the key/values above.

```python
VeSyncLV600S.details = {
  'warm_mist_enabled': True,
  'warm_mist_level': 2
}
```

`VeSyncHumid.humidity` - current humidity level in room

`VeSyncHumid.mist_level` - current mist level

`VeSyncHumid.mode` - Mode of operation - sleep, off, auto/humidity

`VeSyncHumid.water_lacks` - Returns True if water is low

`VeSyncHumid.auto_humidity` - Target humidity for auto mode

`VeSyncHumid.auto_enabled` - Returns true if auto stop enabled at target humidity

#### Humidifer Methods

`VeSyncHumid.automatic_stop_on()` Set humidifier to stop at set humidity

`VeSyncHumid.automatic_stop_off` Set humidifier to run continuously

`VeSyncHumid.turn_on_display()` Turn display on

`VeSyncHumid.turn_off_display()` Turn display off

`VeSyncHumid.set_humidity(30)` Set humidity between 30 and 80 percent

`VeSyncHumid.set_night_light_brightness(50)` Set nightlight brightness between 1 and 100

`VeSyncHumid.set_humidity_mode('sleep')` Set humidity mode - sleep/auto

`VeSyncHumid.set_mist_level(4)` Set mist output 1 - 9

#### 600S warm mist feature

`VeSync600S.warm_mist_enabled` - Returns true if warm mist feature is enabled

`VeSync600S.set_warm_level(2)` - Sets warm mist level

### Cosori Devices

Cosori devices are found under the `manager.kitchen` VeSync class attribute.

#### Cosori 3.7 and 5.8 Quart Air Fryer

The Cosori 3.7 and 5.8 Quart Air Fryer has several methods and properties that can be used to monitor and control
the device.

This library splits the functionality and status into two classes that are both accessible from the device instance.

To maintain consistency of state, the update() method is called after each of the methods that change the state of the device.

There is also an instance attribute that can be set `VeSyncAirFryer158.refresh_interval` that will set the interval in seconds that the state of the air fryer should be updated before a method that changes state is called. This is an additional API call but is necessary to maintain state, especially when trying to `pause` or `resume` the device. Defaults to 60 seconds but can be set via:

```python
# Change to 120 seconds before status is updated between calls
VeSyncAirFryer158.refresh_interval = 120

# Set status update before every call
VeSyncAirFryer158.refresh_interval = 0

# Disable status update before every call
VeSyncAirFryer158.refresh_interval = -1
```

##### Air Fryer Properties

All properties cannot be directly set, they must be set from the `get_details()` or methods that set the status.
They can be set through the `VeSyncAirFryer158.fryer_status` dataclass but should be avoided. This separation of functionality and status is purposeful to avoid inconsistent states.

`VeSyncAirFryer158.temp_unit` - Temperature units of the device (`fahrenheit` or `celsius`)

`VeSyncAirFryer158.current_temp` - Current temperature in the defined temperature units. If device is not running, this defaults to `None`

`VeSyncAirFryer158.cook_set_temp` - Set temperature or target temperature for preheat

`VeSyncAirFryer158.cook_last_time` - The last minutes remaining returned from API for cook mode

`VeSyncAirFryer158.preheat_last_time` - The last minutes remaining returned from API for preheat mode

`VeSyncAirFryer158.cook_status` - Status of air fryer. This can be the following states:
1. `standby` - Air fryer is off and no cook or preheat is in progress
2. `cooking` - Air fryer is actively cooking
3. `cookStop` - Cooking is paused and can be resumed
4. `cookEnd` - Cooking is ended and can be resumed
5. `heating` - Air fryer is preheating
6. `preheatStop` - Preheat is paused and can be resumed
7. `heatEnd` - Preheat is ended and cooking mode can be started with `cook_from_preheat()` method

`VeSyncAirFryer158.is_heating` - Returns true if air fryer is preheating

`VeSyncAirFryer158.is_cooking` - Returns true if air fryer is cooking

`VeSyncAirFryer158.is_paused` - Returns true if air fryer is paused and can be resumed

`VeSyncAirFryer158.remaining_time` - Returns minutes remaining based on timestamp of last API return when air fryer is running. Returns `None` if not running

`VeSyncAirFryer158.fryer_status` - Dataclass that contains the status of the air fryer. The attributes of this dataclass are directly accessible from the `VeSyncAirFryer158` properties and **should not be directly set.**

##### Air Fryer Methods

`VeSyncAirFryer158.update()` - Retrieve current status

`VeSyncAirFryer158.cook(set_temp: int, set_time: int)` - Set air fryer cook mode based on time and temp in defined units

`VeSyncAirFryer158.set_preheat(target_temp: int, cook_time: int)` - Set air fryer preheat mode based on time and temp in defined units

`VeSyncAirFryer158.cook_from_preheat()` - Start cook mode when air fryer is in `preheatEnd` state

`VeSyncAirFryer158.pause()` - Pause air fryer when in `cooking` or `heating` state

`VeSyncAirFryer158.resume()` - Resume air fryer when in `cookStop` or `preheatStop` state

`VeSyncAirFryer158.end()` - End cooking or preheating and return air fryer to `standby` state

### JSON Output API

The `device.displayJSON()` method outputs properties and status of the device

#### JSON Output for All Devices

```python
device.displayJSON()

#Returns:

{
  "Device Name": "Device 1",
  "Model": "Device Model",
  "Subdevice No": "1",
  "Status": "on",
  "Online": "online",
  "Type": "Device Type",
  "CID": "DEVICE-CID"
}
```

#### JSON Output for Outlets

```python
{
  "Active Time": "1", # in minutes
  "Energy": "2.4", # today's energy in kWh
  "Power": "12", # current power in W
  "Voltage": "120", # current voltage
  "Energy Week": "12", # totaly energy of week in kWh
  "Energy Month": "50", # total energy of month in kWh
  "Energy Year": "89", # total energy of year in kWh
}
```

#### JSON Output for Dimmable Switch

This output only applies to dimmable switch.  The standard switch has the default device JSON output shown [above](#json-output-for-all-devices)

```python
{
  "Indicator Light": "on", # status of indicator light
  "Brightness": "50", # percent brightness
  "RGB Light": "on" # status of RGB Light on faceplate
}
```

#### JSON Output for Dimmable Bulb

```python
# output for dimmable bulb
{
  # all default outputs plus...
  "Brightness": "50" # brightness in percent
}
```

#### JSON Output for Tunable Bulb

```python
# output for tunable bulb
{
  # all default outputs plus...
  "Brightness": "50" # brightness in percent
  "Kelvin": "5400" # white temperature in Kelvin
}


```

#### JSON Output for Multicolor Bulb

```python
# output for valceno multicolor bulb
{
  # all default outputs plus...
  "Brightness": "100", # brightness in percent (also used for color value in hsv mode)
  "WhiteTemperaturePct": "0", # white temperature in percent
  "WhiteTemperatureKelvin": "2700", # white temperature in Kelvin
  "ColorHSV": "hsv(hue=79.99, saturation=90.0, value=100)", # color definition in HSV model
  "ColorRGB": "rgb(red=178.5, green=255.0, blue=25.5)", # color definition in RGB model
  "ColorMode": "hsv" # color mode ( white / hsv )
}

```

#### JSON Output for Air Purifier

```python
{
  "Active Time": "50", # minutes
  "Fan Level": "2", # fan level 1-3
  "Air Quality": "95", # air quality in percent
  "Mode": "auto",
  "Screen Status": "on",
  "Filter Life": "99" # remaining filter life in percent
}
```
#### JSON Output for 300S Humidifier

```python
{
  "Mode": "manual", # auto, manual, sleep
  "Humidity": 20, # percent
  "Mist Virtual Level": 6, # Mist level 1 - 9
  "Water Lacks": true, # True/False
  "Water Tank Lifted": true, # True/False
  "Display": true, # True/False
  "Automatic Stop Reach Target": true,
  "Night Light Brightness": 10, # 1 - 100
  "Auto Target Humidity": true, # True/False
  "Automatic Stop": true # True/False
}
```

#### JSON Output for Core200S Purifier

```python
{
	"Device Name": "MyPurifier",
	"Model": "Core200S",
	"Subdevice No": "None",
	"Status": "on",
	"Online": "online",
	"Type": "wifi-air",
	"CID": "asd_sdfKIHG7IJHGwJGJ7GJ_ag5h3G55",
	"Mode": "manual",
	"Filter Life": "99",
	"Fan Level": "1",
	"Display": true,
	"Child Lock": false,
	"Night Light": "off",
	"Display Config": true,
	"Display_Forever Config": false
}
```

#### JSON Output for 400S Purifier

```python
{
  "Device Name": "MyPurifier",
  "Model": "Core200S",
  "Subdevice No": "None",
  "Status": "on",
  "Online": "online",
  "Type": "wifi-air",
  "CID": "<CID>",
  "Mode": "manual",
  "Filter Life": "100",
  "Air Quality Level": "5",
  "Air Quality Value": "1",
  "Fan Level": "1",
  "Display": true,
  "Child Lock": false,
  "Night Light": "off",
  "Display Config": true,
  "Display_Forever Config": false
}
```
#### JSON Output for 600S Purifier

```python
{
  "Device Name": "My 600s",
  "Model": "LAP-C601S-WUS",
  "Subdevice No": "None",
  "Status": "on",
  "Online": "online",
  "Type": "wifi-air",
  "CID": "<CID>",
  "Mode": "manual",
  "Filter Life": "98",
  "Air Quality Level": "5",
  "Air Quality Value": "1",
  "Fan Level": "3",
  "Display": true,
  "Child Lock": false,
  "Night Light": "off",
  "Display Config": true,
  "Display_Forever Config": false
}
```

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

## Debug mode

To make it easier to debug, there is a `debug` argument in the `VeSync` method. This prints out your device list and any other debug log messages.

```python
import pyvesync.vesync as vs

manager = vs.VeSync('user', 'pass', debug=True)
manager.login()
manager.update()
# Prints device list returned from Vesync
```

## Feature Requests

~~If you would like new devices to be added, you will need to capture the packets from the app. The easiest way to do this is by using [Packet Capture for Android](https://play.google.com/store/apps/details?id=app.greyshirts.sslcapture&hl=en_US&gl=US). This works without rooting the device. If you do not have an android or are concerned with adding an app that uses a custom certificate to read the traffic, you can use an Android emulator such as [Nox](https://www.bignox.com/).~~

SSL pinning makes capturing packets with Android ~~not feasible anymore~~ harder than before. A system-wide proxy (https://play.google.com/store/apps/details?id=org.proxydroid&hl=en) can be used if ssl pinning is disabled (https://github.com/ViRb3/TrustMeAlready).

Charles Proxy is a proxy that allows you to perform MITM SSL captures on an iOS device. This is the only way to capture packets that I am aware of that is currently possible.

When capturing packets make sure all packets are captured from the device list, along with all functions that the app contains. The captured packets are stored in text files, please do not capture with pcap format.

After you capture the packets, please redact the `accountid` and `token`. If you feel you must redact other keys, please do not delete them entirely. Replace letters with "A" and numbers with "1", leave all punctuation intact and maintain length.

For example:

Before:
```
{
  'tk': 'abc123abc123==3rf',
  'accountId': '123456789',
  'cid': 'abcdef12-3gh-ij'
}
```
After:
```
{
  'tk': 'AAA111AAA111==1AA',
  'accountId': '111111111',
  'cid': 'AAAAAA11-1AA-AA'
}
```

All [contributions](CONTRIBUTING.md) are welcome, please run `tox` before submitting a PR to ensure code is valid.

Ensure new devices are integrated in tests, please review the [testing](tests/README.md) documentation for more information.

This project is licensed under [MIT](LICENSE).
