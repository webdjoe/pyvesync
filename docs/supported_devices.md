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
      - [Etekcity 10A Rount Outlet USA][pyvesync.devices.vesyncoutlet.VeSyncESW10USA]
      - [Etekcity 15A Rectangle Outlet][pyvesync.devices.vesyncoutlet.VeSyncOutlet15A]
      - [Etekcity 15A Outdoor Dual Outlet][pyvesync.devices.vesyncoutlet.VeSyncOutdoorPlug]
      - [Round Smart Outlet Series][pyvesync.devices.vesyncoutlet.VeSyncOutletBSDGO1] - WHOPLUG / GREENSUN
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
5. Humidifiers
      - [Classic 200S][pyvesync.devices.vesynchumidifier.VeSyncHumid200S] - 2L Smart Humidifier
      - [Classic 300S][pyvesync.devices.vesynchumidifier.VeSyncHumid200300S] - 3L Smart Humidifier
      - [Dual 200S][pyvesync.devices.vesynchumidifier.VeSyncHumid200300S]
      - [LV600S][pyvesync.devices.vesynchumidifier.VeSyncHumid200300S] - 6L Smart Humidifier
      - [OasisMist 4.5L Humidifier][pyvesync.devices.vesynchumidifier.VeSyncHumid200300S]
      - [OasisMist 1000S Humidifier][pyvesync.devices.vesynchumidifier.VeSyncHumid1000S]
      - [Superior 6000S][pyvesync.devices.vesynchumidifier.VeSyncSuperior6000S] - 6L Smart Humidifier
6. Fans
      - [42" Tower Fan][pyvesync.devices.vesyncfan.VeSyncTowerFan]
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

| Device Name | Power Stats | Nightlight |
| :------: | :----: | :----: |
| 7A Round Outlet | ✔ | |
| 10A Round EU Outlet | ✔ | |
| 10A Round US Outlet | | |
| 15A Rectangle Outlet | ✔ | ✔ |
| 15A Outdoor Dual Outlet | ✔ | |
| Round Smart Series | | |

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

### Humidifiers

| Device Name | Night Light | Warm Mist |
| ------ | ----- | ----- |
| Classic 200S | | |
| Classic 300S | | ✔ |
| Dual 200S | | |
| LV600S | ✔ | ✔ |
| OasisMist | ✔ | ✔ |
| Superior 6000S | ✔ | ✔ |

### Fans

Tower Fan - Fan Rotate

### Air Fryers

Air Fryer - All supported features of CS137 and CS158
