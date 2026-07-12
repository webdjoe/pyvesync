# Supported Devices

The VeSync API supports a variety of devices. The following is a list of devices that are supported by the VeSync API and the `pyvesync` library. The product type is the terminology used to identify the base device type. The `pyvesync` library uses the product type to instantiate the correct device class and organize devices.

1. Bulbs
      - [ESL100][pyvesync.devices.vesyncbulb.VeSyncBulbESL100] - Etekcity Dimmable Bulb
      - [ESL100CW][pyvesync.devices.vesyncbulb.VeSyncBulbESL100CW] - Etekcity Dimmable Tunable Bulb (Cool to Warm)
      - [ESL100MC][pyvesync.devices.vesyncbulb.VeSyncBulbESL100MC] - Etekcity Multicolor Dimmable Bulb
      - [Valceno Multicolor Smart Bulb][pyvesync.devices.vesyncbulb.VeSyncBulbValcenoA19MC]
2. Outlets
      - [Etekcity 7A Round Outlet][pyvesync.devices.vesyncoutlet.VeSyncOutlet7A]
      - [Etekcity 10A Round Outlet EU][pyvesync.devices.vesyncoutlet.VeSyncOutlet10A]
      - [Etekcity 10A Round Outlet USA][pyvesync.devices.vesyncoutlet.VeSyncESW10USA]
      - [Etekcity 15A Rectangle Outlet][pyvesync.devices.vesyncoutlet.VeSyncOutlet15A]
      - [Etekcity 15A Outdoor Dual Outlet][pyvesync.devices.vesyncoutlet.VeSyncOutdoorPlug]
      - [BSDOG / Greensun Smart Outlet Series][pyvesync.devices.vesyncoutlet.VeSyncBSDOGPlug] - WHOPLUG / GREENSUN
      - [WYLDR Smart Plug][pyvesync.devices.vesyncoutlet.VeSyncBSDOGPlug] - WYLDR16A1081 (energy monitoring without energy history)
3. Switches
      - [ESWL01][pyvesync.devices.vesyncswitch.VeSyncWallSwitch] - Etekcity Wall Switch
      - [ESWL03][pyvesync.devices.vesyncswitch.VeSyncWallSwitch] - Etekcity 3-Way Switch
      - [ESWD16][pyvesync.devices.vesyncswitch.VeSyncDimmerSwitch] - Etekcity Dimmer Switch
4. Purifiers
      - [Everest Air][pyvesync.devices.vesyncpurifier.VeSyncAirBaseV2]
      - [Vital 200S/100S][pyvesync.devices.vesyncpurifier.VeSyncAirBaseV2]
      - [Core600s][pyvesync.devices.vesyncpurifier.VeSyncAirBypass]
      - [Core400s][pyvesync.devices.vesyncpurifier.VeSyncAirBypass]
      - [Core300s][pyvesync.devices.vesyncpurifier.VeSyncAirBypass]
      - [Core200S][pyvesync.devices.vesyncpurifier.VeSyncAirBypass]
      - [LV-PUR131S][pyvesync.devices.vesyncpurifier.VeSyncAir131]
      - [Sprout Air Purifier][pyvesync.devices.vesyncpurifier.VeSyncAirSprout]
5. Humidifiers
      - [Classic 200S][pyvesync.devices.vesynchumidifier.VeSyncHumid200S] - 2L Smart Humidifier
      - [Classic 300S][pyvesync.devices.vesynchumidifier.VeSyncHumid200300S] - 3L Smart Humidifier
      - [Dual 200S][pyvesync.devices.vesynchumidifier.VeSyncHumid200300S]
      - [LV600S][pyvesync.devices.vesynchumidifier.VeSyncHumid200300S] - 6L Smart Humidifier
      - [OasisMist 4.5L Humidifier][pyvesync.devices.vesynchumidifier.VeSyncHumid200300S]
      - [OasisMist 1000S Humidifier][pyvesync.devices.vesynchumidifier.VeSyncHumid1000S]
      - [Superior 6000S][pyvesync.devices.vesynchumidifier.VeSyncSuperior6000S] - 6L Smart Humidifier
      - [Sprout Humidifier][pyvesync.devices.vesynchumidifier.VeSyncSproutHumid]
6. Fans
      - [42" Tower Fan][pyvesync.devices.vesyncfan.VeSyncTowerFan]
      - [Pedestal Fan][pyvesync.devices.vesyncfan.VeSyncPedestalFan]
7. Air Fryers
      - [CS137][pyvesync.devices.vesynckitchen.VeSyncAirFryer158] - 3.7qt Air Fryer
      - [CS158][pyvesync.devices.vesynckitchen.VeSyncAirFryer158] - 5.8qt Air Fryer
8. Thermostats
      - [Aura][pyvesync.devices.vesyncthermostat] Thermostat

## Device Features

### Switches

Switches have minimal features, the dimmer switch is the only switch that has additional functionality.

| Device Name | Device Type | Dimmer | Plate Lighting | RGB Plate Lighting |
| :------: | :----: | :----: | :----: | :----: |
| Etekcity Wall Switch | ESWL01 | | | |
| Etekcity 3-Way Switch | ESWL03 | | | |
| Etekcity Dimmer Switch | ESWD16 | ✔ | ✔ | ✔ |

### Outlets

| Device Name | Power Stats | Energy History | Nightlight |
| :------: | :----: | :----: | :----: |
| 7A Round Outlet | ✔ | ✔ | |
| 10A Round EU Outlet | ✔ | ✔ | |
| 10A Round US Outlet | | | |
| 15A Rectangle Outlet | ✔ | ✔ | ✔ |
| 15A Outdoor Dual Outlet | ✔ | ✔ | |
| Smart Plug Series (WHOGPLUG / BSDOG01) | ✔ | ✔ | |
| WYLDR Smart Plug (WYLDR16A1081) | ✔ | | |

Power stats are realtime power, voltage and energy readings from the device.
Energy history is the weekly, monthly and yearly energy usage retrieved with
`get_weekly_energy()`, `get_monthly_energy()` and `get_yearly_energy()`. Devices
without the energy history feature log a debug message and make no API call when
these methods are used.

### Purifiers

| Device Name | PM2.5 | PM1.0 | PM10 | Vent Angle | Light Detection |
| ------ | ----- | ----- | ----- | ----- | ----- |
| Everest Air | ✔ | ✔ | ✔ | ✔ | ✔ |
| Vital 200S/100S  | ✔ |  | | | ✔ |
| Core600s | ✔ |  | | | |
| Core400s | ✔ |  | | | |
| Core300s | ✔ |  | | | |
| Core200s | ✔ |  | | | |
| LV-PUR131S | ✔ |  | | | |
| Sprout Air Purifier | ✔ |  | | | |

### Humidifiers

| Device Name | Night Light | RGB Night Light | Warm Mist |
| ------ | ----- | ----- | ----- |
| Classic 200S | | | |
| Classic 300S | ✔ | | ✔ |
| Dual 200S | | | |
| LV600S | | | ✔ |
| OasisMist 4.5L | | ✔ | ✔ |
| Superior 6000S | | | ✔ |
| Sprout Humidifier | | | |

The OasisMist 4.5L (`LUH-O451S-WEU`) exposes an RGB nightlight through
[`set_rgb_nightlight`][pyvesync.devices.vesynchumidifier.VeSyncHumid200300S.set_rgb_nightlight].
Other models with the same hardware may work by adding the
`HumidifierFeatures.RGB_NIGHTLIGHT` feature flag, but only the OasisMist 4.5L has
been verified.

### Fans

| Device Name | Oscillation | Multi-Axis Oscillation |
| ------ | ----- | ----- |
| 42" Tower Fan | ✔ | |
| Pedestal Fan | ✔ | ✔ |

### Air Fryers

| Device Name | Device Type | Temperature Control | Timer |
| ------ | ----- | ----- | ----- |
| Cosori 3.7qt Air Fryer | CS137 | ✔ | ✔ |
| Cosori 5.8qt Air Fryer | CS158 | ✔ | ✔ |

### Thermostats

| Device Name | Device Type | Heat | Cool | Auto | Smart Auto | Emergency Heat |
| ------ | ----- | ----- | ----- | ----- | ----- | ----- |
| Aura Thermostat | LTM-A401S-WUS | ✔ | ✔ | ✔ | ✔ | ✔ |
