"""Device and module mappings for VeSync devices.

**To add a new device type to existing module: Add the device_type to the end
of the existing dev_types list.**

This module contains mappings for VeSync devices to their respective classes.
The mappings are used to create instances of the appropriate device class
based on the device type and define features and modes. The device type is taken
from the `deviceType` field in the device list API.

The AirFryerMap, OutletMap, SwitchMap, BulbMap, FanMap, HumidifierMap, PurifierMap
and ThermostatMap dataclasses are used to define the mappings for each product type
with the associated module, class, features and other device specific configuration. The
[`get_device_config`][pyvesync.device_map.get_device_config] function is used
to get the device map object from the device type to instantiate the appropriate class.
The individual `get_<product-type>` functions are used to get the device details
for the specific to the device type. Both functions return the same model,
the individual product type functions are used to satisfy type checking in
the individual devices.

Attributes:
    outlet_modules: list[OutletMap]: List of Outlet device mappings.
    switch_modules: list[SwitchMap]: List of Switch device mappings.
    bulb_modules: list[BulbMap]: List of Bulb device mappings.
    fan_modules: list[FanMap]: List of Fan device mappings.
    purifier_modules: list[PurifierMap]: List of Purifier device mappings.
    humidifier_modules: list[HumidifierMap]: List of Humidifier device mappings.
    air_fryer_modules: list[AirFryerMap]: List of Air Fryer device mappings.
    thermostat_modules: list[ThermostatMap]: List of Thermostat device mappings.

Classes:
    ProductTypes: Enum: General device types enum.
    DeviceMapTemplate: Template for DeviceModules mapping.
    OutletMap: Template for Outlet device mapping.
    SwitchMap: Template for Switch device mapping.
    BulbMap: dataclass: Template for Bulb device mapping.
    FanMap: dataclass: Template for Fan device mapping.
    HumidifierMap: dataclass: Template for Humidifier device mapping.
    PurifierMap: dataclass: Template for Purifier device mapping.
    AirFryerMap: dataclass: Template for Air Fryer device mapping.
    ThermostatMap: dataclass: Template for Thermostat device mapping.

Functions:
    get_device_config: Get the device map object from the device type.
    get_outlet: Get outlet device config, returning OutletMap object.
    get_switch: Get switch device config, returning SwitchMap object.
    get_bulb: Get the bulb device config, returning BulbMap object.
    get_fan: Get the fan device config, returning the FanMap object.
    get_humidifier: Get the humidfier config, returning the HumidifierMap object.
    get_purifier: Get the purifier config, returning the PurifierMap object.
    get_air_fryer: Get the Air Fryer config, returning the AirFryerMap object.
    get_thermostat: Get the thermostat config, returning the ThermostatMap object.

Note:
    To add devices, add the device mapping to the appropriate `<product-type>_modules`
    list, ensuring all required fields are present based on the `<product-type>Map`
    fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import chain
from types import MappingProxyType, ModuleType
from typing import Union

from pyvesync.const import (
    CUSTOM_COOK_MODE,
    CUSTOM_RECIPE_ID,
    CUSTOM_RECIPE_NAME,
    AirFryerCookModes,
    AirFryerCookStatus,
    AirFryerFeatures,
    AirFryerModeConfig,
    AirFryerPresetRecipe,
    AirFryerPresets,
    AirFryerTempLimits,
    AirFryerTimeLimits,
    BulbFeatures,
    ColorMode,
    EnergyIntervals,
    FanFeatures,
    FanModes,
    FanSleepPreference,
    HumidifierFeatures,
    HumidifierModes,
    NightlightModes,
    OutletFeatures,
    ProductLines,
    ProductTypes,
    PurifierAutoPreference,
    PurifierFeatures,
    PurifierModes,
    SwitchFeatures,
    TemperatureUnits,
    ThermostatEcoTypes,
    ThermostatFanModes,
    ThermostatHoldOptions,
    ThermostatRoutineTypes,
    ThermostatWorkModes,
    TimeUnits,
)
from pyvesync.devices import (
    vesyncbulb,
    vesyncfan,
    vesynchumidifier,
    vesynckitchen,
    vesyncoutlet,
    vesyncpurifier,
    vesyncswitch,
    vesyncthermostat,
)

T_MAPS = Union[  # noqa: UP007, RUF100
    list['OutletMap'],
    list['SwitchMap'],
    list['BulbMap'],
    list['FanMap'],
    list['HumidifierMap'],
    list['PurifierMap'],
    list['AirFryerMap'],
    list['ThermostatMap'],
]


@dataclass(kw_only=True)
class DeviceMapTemplate:
    """Template for DeviceModules mapping.

    Attributes:
        dev_types (list[str]): List of device types to match from API.
        class_name (str): Class name of the device.
        product_type (str): Product type of the device.
        module (ModuleType): Module for the device.
        setup_entry (str): Setup entry for the device, if unknown use the device_type
            base without region
        model_display (str): Display name of the model.
        model_name (str): Name of the model.
        device_alias (str | None): Alias for the device, if any.
        features (list[str]): List of features for the device.
    """

    dev_types: list[str]
    class_name: str
    product_type: str
    product_line: str
    module: ModuleType
    setup_entry: str
    model_display: str
    model_name: str
    features: list[str]
    device_alias: str


@dataclass(kw_only=True)
class OutletMap(DeviceMapTemplate):
    """Template for DeviceModules mapping.

    Attributes:
        dev_types (list[str]): List of device types to match from API.
        class_name (str): Class name of the device.
        product_type (str): Product type of the device - ProductTypes.OUTLET
        module (ModuleType): Module for the device.
        setup_entry (str): Setup entry for the device, if unknown use the device_type
            base without region
        model_display (str): Display name of the model.
        model_name (str): Name of the model.
        device_alias (str | None): Alias for the device, if any.
        features (list[str]): List of features for the device.
        product_type (str): Product type of the device.
        module (ModuleType): Module for the device.
        nightlight_modes (list[str]): List of nightlight modes for the device.
    """

    product_line: str = ProductLines.WIFI_LIGHT
    product_type: str = ProductTypes.OUTLET
    module: ModuleType = vesyncoutlet
    energy_intervals: tuple[str, ...] = (
        EnergyIntervals.YEAR,
        EnergyIntervals.MONTH,
        EnergyIntervals.WEEK,
    )
    nightlight_modes: list[NightlightModes] = field(default_factory=list)


@dataclass(kw_only=True)
class SwitchMap(DeviceMapTemplate):
    """Template for DeviceModules mapping.

    Attributes:
        dev_types (list[str]): List of device types to match from API.
        class_name (str): Class name of the device.
        product_type (str): Product type of the device - ProductTypes.SWITCH
        module (ModuleType): Module for the device.
        setup_entry (str): Setup entry for the device, if unknown use the device_type
            base without region
        model_display (str): Display name of the model.
        model_name (str): Name of the model.
        device_alias (str | None): Alias for the device, if any.
        features (list[str]): List of features for the device.
        product_type (str): Product type of the device.
        module (ModuleType): Module for the device.
    """

    product_line: str = ProductLines.SWITCHES
    product_type: str = ProductTypes.SWITCH
    module: ModuleType = vesyncswitch


@dataclass(kw_only=True)
class BulbMap(DeviceMapTemplate):
    """Template for DeviceModules mapping.

    Attributes:
        dev_types (list[str]): List of device types to match from API.
        class_name (str): Class name of the device.
        product_type (str): Product type of the device - ProductTypes.BULB
        module (ModuleType): Module for the device.
        setup_entry (str): Setup entry for the device, if unknown use the device_type
            base without region
        model_display (str): Display name of the model.
        model_name (str): Name of the model.
        device_alias (str | None): Alias for the device, if any.
        features (list[str]): List of features for the device.
        color_model (str | None): Color model for the device.
        color_modes (list[str]): List of color modes for the device.
    """

    product_line: str = ProductLines.WIFI_LIGHT
    color_model: str | None = None
    product_type: str = ProductTypes.BULB
    module: ModuleType = vesyncbulb
    color_modes: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class FanMap(DeviceMapTemplate):
    """Template for DeviceModules mapping.

    Attributes:
        dev_types (list[str]): List of device types to match from API.
        class_name (str): Class name of the device.
        product_type (str): Product type of the device - ProductTypes.FAN
        module (ModuleType): Module for the device.
        setup_entry (str): Setup entry for the device, if unknown use the device_type
            base without region
        model_display (str): Display name of the model.
        model_name (str): Name of the model.
        device_alias (str | None): Alias for the device, if any.
        features (list[str]): List of features for the device.
        fan_levels (list[int]): List of fan levels for the device.
        modes (list[str]): List of modes for the device.
        sleep_preferences (list[str]): List of sleep preferences for the device.
        set_mode_method (str): Method to set the mode for the device.
    """

    modes: dict[str, str]
    fan_levels: list[int]
    product_line: str = ProductLines.WIFI_AIR
    product_type: str = ProductTypes.FAN
    module: ModuleType = vesyncfan
    sleep_preferences: list[str] = field(default_factory=list)
    set_mode_method: str = ''


@dataclass(kw_only=True)
class HumidifierMap(DeviceMapTemplate):
    """Template for DeviceModules mapping.

    Attributes:
        dev_types (list[str]): List of device types to match from API.
        class_name (str): Class name of the device.
        product_type (str): Product type of the device - ProductTypes.HUMIDIFIER
        module (ModuleType): Module for the device.
        setup_entry (str): Setup entry for the device, if unknown use the device_type
            base without region
        model_display (str): Display name of the model.
        model_name (str): Name of the model.
        device_alias (str | None): Alias for the device, if any.
        features (list[str]): List of features for the device.
        mist_modes (dict[str, str]): Dictionary of mist modes for the device.
        mist_levels (list[int | str]): List of mist levels for the device.
        target_minmax (tuple[int, int]): Minimum and maximum target humidity levels.
        warm_mist_levels (list[int | str]): List of warm mist levels for the device.
    """

    mist_modes: dict[str, str]
    mist_levels: list[int]
    product_line: str = ProductLines.WIFI_AIR
    product_type: str = ProductTypes.HUMIDIFIER
    module: ModuleType = vesynchumidifier
    target_minmax: tuple[int, int] = (30, 80)
    warm_mist_levels: list[int] = field(default_factory=list)


@dataclass(kw_only=True)
class PurifierMap(DeviceMapTemplate):
    """Template for DeviceModules mapping.

    Attributes:
        dev_types (list[str]): List of device types to match from API.
        class_name (str): Class name of the device.
        product_type (str): Product type of the device - ProductTypes.PURIFIER

        module (ModuleType): Module for the device.
        setup_entry (str): Setup entry for the device, if unknown use the device_type
            base without region
        model_display (str): Display name of the model.
        model_name (str): Name of the model.
        device_alias (str | None): Alias for the device, if any.
        features (list[str]): List of features for the device.
        fan_levels (list[int]): List of fan levels for the device.
        modes (list[str]): List of modes for the device.
        nightlight_modes (list[str]): List of nightlight modes for the device.
        auto_preferences (list[str]): List of auto preferences for the device.
    """

    fan_levels: list[int]
    modes: list[str]
    product_line: str = ProductLines.WIFI_AIR
    product_type: str = ProductTypes.PURIFIER
    module: ModuleType = vesyncpurifier
    nightlight_modes: list[str] = field(default_factory=list)
    auto_preferences: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class AirFryerMap(DeviceMapTemplate):
    """Device map entry for an air fryer model.

    Attributes:
        dev_types (list[str]): List of device types to match from API.
        class_name (str): Class name of the device.
        product_type (str): Product type of the device - ProductTypes.AIR_FRYER
        product_line (str): Product line, ``ProductLines.WIFI_KITCHEN``.
        module (ModuleType): Module for the device.
        setup_entry (str): Setup entry for the device, if unknown use the device_type
            base without region
        model_display (str): Display name of the model.
        model_name (str): Name of the model.
        device_alias (str | None): Alias for the device, if any.
        features (list[str]): ``AirFryerFeatures`` values for the device.
        time_units (TimeUnits): The time unit of the device's API. Defaults to
            minutes (CS137/CS158); the bypassV2 fryers set seconds.
        temp_unit (TemperatureUnits): The temperature unit the device model
            uses (map default; may be updated from the API on update()).
        status_map (MappingProxyType[str, AirFryerCookStatus]): API status
            string to ``AirFryerCookStatus``. A status not in it logs a
            warning on update() and keeps the chamber's last state.
        cook_modes (dict[str, AirFryerModeConfig]): The fryer's APK presets,
            keyed by ``AirFryerCookModes``. Each holds the mode's request
            values, default time and temperatures, and its Celsius and
            Fahrenheit limits. The device-wide temperature range is the widest
            span over these modes.
        default_preset (AirFryerPresetRecipe): Preset whose mode, recipe ID,
            name and type ``set_mode()`` sends when no mode is given; the
            caller's time and temperature replace its own. Its ``cook_mode``
            and ``recipe_id`` match one entry of ``cook_modes``, and the
            library finds the default mode from its ``cook_mode``.
        default_cook_mode (str): Key in ``cook_modes`` of the mode
            ``default_preset`` sends. Not read by the library; the map tests
            keep it in step with ``default_preset``.
    """

    time_units: TimeUnits = TimeUnits.MINUTES
    temp_unit: TemperatureUnits = TemperatureUnits.FAHRENHEIT
    product_line: str = ProductLines.WIFI_KITCHEN
    product_type: str = ProductTypes.AIR_FRYER
    module: ModuleType = vesynckitchen
    default_preset: AirFryerPresetRecipe = field(
        default_factory=lambda: AirFryerPresets.custom
    )
    cook_modes: dict[str, AirFryerModeConfig] = field(default_factory=dict)
    default_cook_mode: str = AirFryerCookModes.AIRFRY
    status_map: MappingProxyType[str, AirFryerCookStatus] = field(
        default_factory=lambda: MappingProxyType({})
    )


@dataclass(kw_only=True)
class ThermostatMap(DeviceMapTemplate):
    """Template for Thermostat device mapping.

    Attributes:
        dev_types (list[str]): List of device types to match from API.
        class_name (str): Class name of the device.
        product_type (str): Product type of the device.
        module (ModuleType): Module for the device.
        setup_entry (str): Setup entry for the device, if unknown use the device_type
            base without region
        model_display (str): Display name of the model.
        model_name (str): Name of the model.
        device_alias (str | None): Alias for the device, if any.
        features (list[str]): List of features for the device.
        modes (list[int]): List of modes for the device.
        fan_modes (list[int]): List of fan modes for the device.
        eco_types (list[int]): List of eco types for the device.
        hold_options (list[int]): List of hold options for the device.
        routine_types (list[int]): List of routine types for the device.
    """

    product_line: str = ProductLines.THERMOSTAT
    product_type: str = ProductTypes.THERMOSTAT
    module: ModuleType = vesyncthermostat
    modes: list[int] = field(default_factory=list)
    fan_modes: list[int] = field(default_factory=list)
    eco_types: list[int] = field(default_factory=list)
    hold_options: list[int] = field(default_factory=list)
    routine_types: list[int] = field(default_factory=list)


thermostat_modules = [
    ThermostatMap(
        dev_types=['LTM-A401S-WUS'],
        class_name='VeSyncAuraThermostat',
        features=[],
        fan_modes=[
            ThermostatFanModes.AUTO,
            ThermostatFanModes.CIRCULATE,
            ThermostatFanModes.ON,
        ],
        modes=[
            ThermostatWorkModes.HEAT,
            ThermostatWorkModes.COOL,
            ThermostatWorkModes.AUTO,
            ThermostatWorkModes.OFF,
            ThermostatWorkModes.SMART_AUTO,
            ThermostatWorkModes.EM_HEAT,
        ],
        eco_types=[
            ThermostatEcoTypes.BALANCE,
            ThermostatEcoTypes.COMFORT_FIRST,
            ThermostatEcoTypes.COMFORT_SECOND,
            ThermostatEcoTypes.ECO_FIRST,
            ThermostatEcoTypes.ECO_SECOND,
        ],
        hold_options=[
            ThermostatHoldOptions.PERMANENTLY,
            ThermostatHoldOptions.FOUR_HOURS,
            ThermostatHoldOptions.TWO_HOURS,
            ThermostatHoldOptions.UNTIL_NEXT_SCHEDULED_ITEM,
        ],
        routine_types=[
            ThermostatRoutineTypes.AWAY,
            ThermostatRoutineTypes.CUSTOM,
            ThermostatRoutineTypes.HOME,
            ThermostatRoutineTypes.SLEEP,
        ],
        setup_entry='LTM-A401S-WUS',
        model_display='LTM-A401S Series',
        device_alias='Aura Thermostat',
        model_name='Aura Thermostat',
    )
]


outlet_modules = [
    OutletMap(
        dev_types=['wifi-switch-1.3'],
        class_name='VeSyncOutlet7A',
        features=[OutletFeatures.ENERGY_MONITOR, OutletFeatures.ENERGY_HISTORY],
        model_name='WiFi Outlet US/CA',
        device_alias='Round 7A WiFi Outlet',
        model_display='ESW01-USA Series',
        setup_entry='wifi-switch-1.3',
    ),
    OutletMap(  # TODO: Add energy
        dev_types=['ESW10-USA', 'ESW10-EU'],
        class_name='VeSyncESW10USA',
        features=[],
        model_name='10A WiFi Outlet USA',
        model_display='ESW10-USA Series',
        device_alias='10A Round WiFi Outlet',
        setup_entry='ESW10-USA',
    ),
    OutletMap(
        dev_types=['ESW01-EU', 'ESW01-USA', 'ESW03-USA', 'ESW03-EU'],
        class_name='VeSyncOutlet10A',
        features=[OutletFeatures.ENERGY_MONITOR, OutletFeatures.ENERGY_HISTORY],
        model_name='ESW03 10A WiFi Outlet',
        model_display='ESW01/03 USA/EU',
        device_alias='10A Round WiFi Outlet',
        setup_entry='ESW03',
    ),
    OutletMap(
        dev_types=['ESW15-USA'],
        class_name='VeSyncOutlet15A',
        features=[
            OutletFeatures.ENERGY_MONITOR,
            OutletFeatures.ENERGY_HISTORY,
            OutletFeatures.NIGHTLIGHT,
        ],
        nightlight_modes=[NightlightModes.ON, NightlightModes.OFF, NightlightModes.AUTO],
        model_name='15A WiFi Outlet US/CA',
        model_display='ESW15-USA Series',
        device_alias='15A Rectangular WiFi Outlet',
        setup_entry='ESW15-USA',
    ),
    OutletMap(
        dev_types=['ESO15-TB'],
        class_name='VeSyncOutdoorPlug',
        features=[OutletFeatures.ENERGY_MONITOR, OutletFeatures.ENERGY_HISTORY],
        model_name='Outdoor Plug',
        model_display='ESO15-TB Series',
        device_alias='Outdoor Smart Plug',
        setup_entry='ESO15-TB',
    ),
    OutletMap(
        dev_types=[
            'WHOGPLUG',
        ],
        class_name='VeSyncOutletWHOGPlug',
        features=[
            OutletFeatures.ONOFF,
            OutletFeatures.ENERGY_MONITOR,
            OutletFeatures.ENERGY_HISTORY,
        ],
        model_name='Smart Plug',
        model_display='Smart Plug Series',
        setup_entry='WHOGPLUG',
        device_alias='Greensun Smart Plug',
    ),
    OutletMap(
        dev_types=[
            'BSDOG01',
            'BSDOG02',
            'WYSMTOD16A',
            'WM-PLUG',
            'JXUK13APLUG',
            'WYZYOGMINIPLUG',
            'HWPLUG16A',
            'FY-PLUG',
            'HWPLUG16',
        ],
        class_name='VeSyncBSDOGPlug',
        features=[
            OutletFeatures.ONOFF,
            OutletFeatures.ENERGY_MONITOR,
            OutletFeatures.ENERGY_HISTORY,
        ],
        model_name='Smart Plug',
        model_display='Smart Plug Series',
        setup_entry='BSDOG01',
        device_alias='Smart Plug Series',
    ),
    OutletMap(
        dev_types=['WYLDR16A1081'],
        class_name='VeSyncBSDOGPlug',
        features=[OutletFeatures.ONOFF, OutletFeatures.ENERGY_MONITOR],
        model_name='Smart Plug',
        model_display='WYLDR Smart Plug',
        setup_entry='WYLDR16A1081',
        device_alias='WYLDR Smart Plug',
    ),
]
"""List of ['OutletMap'][pyvesync.device_map.OutletMap] configuration
objects for outlet devices."""

switch_modules = [
    SwitchMap(
        dev_types=['ESWL01'],
        class_name='VeSyncWallSwitch',
        device_alias='Wall Switch',
        features=[SwitchFeatures.ONOFF],
        model_name='Light Switch',
        model_display='ESWL01 Series',
        setup_entry='ESWL01',
    ),
    SwitchMap(
        dev_types=['ESWD16'],
        class_name='VeSyncDimmerSwitch',
        features=[
            SwitchFeatures.DIMMABLE,
            SwitchFeatures.INDICATOR_LIGHT,
            SwitchFeatures.BACKLIGHT_RGB,
        ],
        device_alias='Dimmer Switch',
        model_name='Dimmer Switch',
        model_display='ESWD16 Series',
        setup_entry='ESWD16',
    ),
    SwitchMap(
        dev_types=['ESWL03'],
        class_name='VeSyncWallSwitch',
        device_alias='Three-Way Wall Switch',
        features=[SwitchFeatures.ONOFF],
        model_name='Light Switch 3 way',
        model_display='ESWL03 Series',
        setup_entry='ESWL03',
    ),
]
"""List of ['SwitchMap'][pyvesync.device_map.SwitchMap] configuration
objects for switch devices."""


bulb_modules = [
    BulbMap(
        dev_types=['ESL100'],
        class_name='VeSyncBulbESL100',
        features=[SwitchFeatures.DIMMABLE],
        color_model=None,
        device_alias='Dimmable Bright White Bulb',
        color_modes=[ColorMode.WHITE],
        model_display='ESL100 Series',
        model_name='Soft white light bulb',
        setup_entry='ESL100',
    ),
    BulbMap(
        dev_types=['ESL100CW'],
        class_name='VeSyncBulbESL100CW',
        features=[BulbFeatures.DIMMABLE, BulbFeatures.COLOR_TEMP],
        color_model=None,
        device_alias='Dimmable Tunable White Bulb',
        color_modes=[ColorMode.WHITE],
        model_display='ESL100CW Series',
        model_name='Cool-to-Warm White Light Bulb',
        setup_entry='ESL100CW',
    ),
    BulbMap(
        dev_types=['XYD0001'],
        class_name='VeSyncBulbValcenoA19MC',
        features=[
            BulbFeatures.DIMMABLE,
            BulbFeatures.MULTICOLOR,
            BulbFeatures.COLOR_TEMP,
        ],
        color_model=ColorMode.HSV,
        device_alias='Valceno Dimmable RGB Bulb',
        color_modes=[ColorMode.WHITE, ColorMode.COLOR],
        model_display='XYD0001',
        model_name='Valceno WiFi Bulb',
        setup_entry='XYD0001',
    ),
    BulbMap(
        dev_types=['ESL100MC'],
        class_name='VeSyncBulbESL100MC',
        features=[
            BulbFeatures.MULTICOLOR,
            BulbFeatures.DIMMABLE,
        ],
        color_model=ColorMode.RGB,
        device_alias='Etekcity Dimmable RGB Bulb',
        color_modes=[ColorMode.WHITE, ColorMode.COLOR],
        model_name='Multicolor Bulb',
        model_display='ESL100MC',
        setup_entry='ESL100MC',
    ),
]
"""List of ['BulbMap'][pyvesync.device_map.BulbMap] configuration
objects for bulb devices."""


humidifier_modules = [
    HumidifierMap(
        class_name='VeSyncHumid200300S',
        dev_types=[
            'Classic300S',
            'LUH-A601S-WUSB',
            'LUH-A601S-AUSW',
        ],
        features=[
            HumidifierFeatures.NIGHTLIGHT,
            HumidifierFeatures.NIGHTLIGHT_BRIGHTNESS,
            HumidifierFeatures.AUTO_STOP,
        ],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
        },
        mist_levels=list(range(1, 10)),
        device_alias='Classic 300S',
        model_display='LUH-A601S Series',
        model_name='Classic 300S',
        setup_entry='Classic300S',
    ),
    HumidifierMap(
        class_name='VeSyncHumid200S',
        dev_types=['Classic200S'],
        features=[HumidifierFeatures.AUTO_STOP],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.MANUAL: 'manual',
        },
        mist_levels=list(range(1, 10)),
        device_alias='Classic 200S',
        model_display='Classic 200S Series',
        model_name='Classic 200S',
        setup_entry='Classic200S',
    ),
    HumidifierMap(
        class_name='VeSyncHumid200300S',
        dev_types=[
            'Dual200S',
            'LUH-D301S-WUSR',
            'LUH-D301S-WJP',
            'LUH-D301S-WEU',
            'LUH-D301S-KEUR',
        ],
        features=[HumidifierFeatures.AUTO_STOP],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.MANUAL: 'manual',
        },
        mist_levels=list(range(1, 3)),
        device_alias='Dual 200S',
        model_display='LUH-D301S Series',
        model_name='Dual 200S',
        setup_entry='Dual200S',
    ),
    HumidifierMap(
        class_name='VeSyncHumid200300S',
        dev_types=[
            'LUH-A602S-WUSR',
            'LUH-A602S-WUS',
            'LUH-A602S-WEUR',
            'LUH-A602S-WEU',
            'LUH-A602S-WJP',
            'LUH-A602S-WUSC',
        ],
        features=[HumidifierFeatures.WARM_MIST, HumidifierFeatures.AUTO_STOP],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
        },
        mist_levels=list(range(1, 10)),
        warm_mist_levels=[0, 1, 2, 3],
        device_alias='LV600S',
        model_display='LUH-A602S Series',
        model_name='LV600S',
        setup_entry='LUH-A602S-WUS',
    ),
    HumidifierMap(
        class_name='VeSyncLV600S',
        dev_types=[
            'LUH-A603S-WUS',
        ],
        features=[HumidifierFeatures.WARM_MIST],
        mist_modes={
            HumidifierModes.AUTO: 'humidity',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
        },
        mist_levels=list(range(1, 10)),
        warm_mist_levels=[0, 1, 2, 3],
        device_alias='LV600S',
        model_display='LUH-A603S Series',
        model_name='LV600S',
        setup_entry='LUH-A603S-WUS',
    ),
    HumidifierMap(
        class_name='VeSyncHumid200300S',
        dev_types=['LUH-O451S-WEU'],
        features=[
            HumidifierFeatures.WARM_MIST,
            HumidifierFeatures.AUTO_STOP,
            HumidifierFeatures.RGB_NIGHTLIGHT,
        ],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
        },
        mist_levels=list(range(1, 10)),
        warm_mist_levels=list(range(4)),
        device_alias='OasisMist 450S EU',
        model_name='OasisMist 4.5L',
        model_display='LUH-O451S Series',
        setup_entry='LUH-O451S-WEU',
    ),
    HumidifierMap(
        class_name='VeSyncHumid200300S',
        dev_types=['LUH-O451S-WUS', 'LUH-O451S-WUSR', 'LUH-O601S-WUS', 'LUH-O601S-KUS'],
        features=[HumidifierFeatures.WARM_MIST, HumidifierFeatures.AUTO_STOP],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
            HumidifierModes.HUMIDITY: 'humidity',
        },
        mist_levels=list(range(1, 10)),
        warm_mist_levels=list(range(4)),
        device_alias='OasisMist 450S',
        model_display='OasisMist 4.5L Series',
        model_name='OasisMist 4.5L',
        setup_entry='LUH-O451S-WUS',
    ),
    HumidifierMap(
        class_name='VeSyncHumid1000S',
        dev_types=['LUH-M101S-WUS', 'LUH-M101S-WUSR'],
        features=[HumidifierFeatures.AUTO_STOP],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
        },
        mist_levels=list(range(1, 10)),
        device_alias='Oasismist 1000S',
        model_display='Oasismist Series',
        model_name='Oasismist 1000S',
        setup_entry='LUH-M101S-WUS',
    ),
    HumidifierMap(
        class_name='VeSyncHumid1000S',
        dev_types=['LUH-M101S-WEUR'],
        features=[
            HumidifierFeatures.NIGHTLIGHT,
            HumidifierFeatures.NIGHTLIGHT_BRIGHTNESS,
            HumidifierFeatures.AUTO_STOP,
        ],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
        },
        mist_levels=list(range(1, 10)),
        device_alias='Oasismist 1000S EU',
        model_display='Oasismist Series EU',
        model_name='Oasismist 1000S EU',
        setup_entry='LUH-M101S-WEUR',
    ),
    HumidifierMap(
        class_name='VeSyncSuperior6000S',
        dev_types=['LEH-S601S-WUS', 'LEH-S601S-WUSR', 'LEH-S601S-WEUR', 'LEH-S602S-WUS'],
        features=[HumidifierFeatures.DRYING_MODE, HumidifierFeatures.AUTO_STOP],
        mist_modes={
            HumidifierModes.AUTO: 'autoPro',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.HUMIDITY: 'humidity',
            HumidifierModes.MANUAL: 'manual',
        },
        mist_levels=list(range(1, 10)),
        device_alias='Superior 6000S',
        model_display='LEH-S601S Series',
        model_name='Superior 6000S',
        setup_entry='LEH-S601S',
    ),
    HumidifierMap(
        class_name='VeSyncSproutHumid',
        dev_types=['LEH-B381S-WUS', 'LEH-B381S-WEU'],
        features=[
            HumidifierFeatures.DRYING_MODE,
            HumidifierFeatures.NIGHTLIGHT,
            HumidifierFeatures.NIGHTLIGHT_BRIGHTNESS,
            HumidifierFeatures.AUTO_STOP,
        ],
        mist_modes={
            HumidifierModes.AUTO: 'autoPro',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
        },
        mist_levels=list(range(1, 3)),
        device_alias='Sprout Humidifier',
        model_display='LEH-B381S Series',
        model_name='Sprout Humidifier',
        setup_entry='LEH-B381S',
    ),
]
"""List of ['HumidifierMap'][pyvesync.device_map.HumidifierMap] configuration
objects for humidifier devices."""


purifier_modules: list[PurifierMap] = [
    PurifierMap(
        class_name='VeSyncAirBypass',
        dev_types=['Core200S', 'LAP-C201S-AUSR', 'LAP-C202S-WUSR'],
        modes=[PurifierModes.SLEEP, PurifierModes.MANUAL],
        features=[PurifierFeatures.RESET_FILTER, PurifierFeatures.NIGHTLIGHT],
        auto_preferences=[
            PurifierAutoPreference.DEFAULT,
            PurifierAutoPreference.EFFICIENT,
            PurifierAutoPreference.QUIET,
        ],
        fan_levels=list(range(1, 4)),
        nightlight_modes=[NightlightModes.ON, NightlightModes.OFF, NightlightModes.DIM],
        device_alias='Core 200S',
        model_display='Core 200S',
        model_name='Core 200S',
        setup_entry='Core200S',
    ),
    PurifierMap(
        class_name='VeSyncAirBypass',
        dev_types=[
            'Core300S',
            'LAP-C301S-WJP',
            'LAP-C302S-WUSB',
            'LAP-C301S-WAAA',
            'LAP-C302S-WGC',
        ],
        modes=[PurifierModes.SLEEP, PurifierModes.MANUAL, PurifierModes.AUTO],
        auto_preferences=[
            PurifierAutoPreference.DEFAULT,
            PurifierAutoPreference.EFFICIENT,
            PurifierAutoPreference.QUIET,
        ],
        features=[PurifierFeatures.AIR_QUALITY],
        fan_levels=list(range(1, 4)),
        device_alias='Core 300S',
        model_display='Core 300S',
        model_name='Core 300S',
        setup_entry='Core300S',
    ),
    PurifierMap(
        class_name='VeSyncAirBypass',
        dev_types=['Core400S', 'LAP-C401S-WJP', 'LAP-C401S-WUSR', 'LAP-C401S-WAAA'],
        modes=[PurifierModes.SLEEP, PurifierModes.MANUAL, PurifierModes.AUTO],
        features=[PurifierFeatures.AIR_QUALITY],
        fan_levels=list(range(1, 5)),
        device_alias='Core 400S',
        auto_preferences=[
            PurifierAutoPreference.DEFAULT,
            PurifierAutoPreference.EFFICIENT,
            PurifierAutoPreference.QUIET,
        ],
        model_display='Core 400S',
        model_name='Core 400S',
        setup_entry='Core400S',
    ),
    PurifierMap(
        class_name='VeSyncAirBypass',
        dev_types=['Core600S', 'LAP-C601S-WUS', 'LAP-C601S-WUSR', 'LAP-C601S-WEU'],
        modes=[PurifierModes.SLEEP, PurifierModes.MANUAL, PurifierModes.AUTO],
        features=[PurifierFeatures.AIR_QUALITY],
        auto_preferences=[
            PurifierAutoPreference.DEFAULT,
            PurifierAutoPreference.EFFICIENT,
            PurifierAutoPreference.QUIET,
        ],
        fan_levels=list(range(1, 5)),
        device_alias='Core 600S',
        model_display='Core 600S',
        model_name='Core 600S',
        setup_entry='Core600S',
    ),
    PurifierMap(
        class_name='VeSyncAir131',
        dev_types=['LV-PUR131S'],
        modes=[PurifierModes.SLEEP, PurifierModes.MANUAL, PurifierModes.AUTO],
        features=[PurifierFeatures.AIR_QUALITY],
        fan_levels=list(range(1, 4)),
        device_alias='LV-PUR131S',
        model_display='LV-PUR131S Series',
        model_name='LV131S',
        setup_entry='LV-PUR131S',
    ),
    PurifierMap(
        class_name='VeSyncAirRH131',
        dev_types=['LV-RH131S-WM', 'LV-RH131S'],
        modes=[PurifierModes.SLEEP, PurifierModes.MANUAL, PurifierModes.AUTO],
        features=[PurifierFeatures.AIR_QUALITY],
        fan_levels=list(range(1, 4)),
        device_alias='LV-RH131S',
        model_display='LV-RH131S Series',
        model_name='LV131S',
        setup_entry='LV-RH131S',
    ),
    PurifierMap(
        class_name='VeSyncAirBaseV2',
        dev_types=[
            'LAP-V102S-AASR',
            'LAP-V102S-WUS',
            'LAP-V102S-WEU',
            'LAP-V102S-AUSR',
            'LAP-V102S-WJP',
            'LAP-V102S-AJPR',
            'LAP-V102S-AEUR',
        ],
        modes=[
            PurifierModes.SLEEP,
            PurifierModes.MANUAL,
            PurifierModes.AUTO,
            PurifierModes.PET,
        ],
        features=[PurifierFeatures.AIR_QUALITY],
        fan_levels=list(range(1, 5)),
        device_alias='Vital 100S',
        auto_preferences=[
            PurifierAutoPreference.DEFAULT,
            PurifierAutoPreference.EFFICIENT,
            PurifierAutoPreference.QUIET,
        ],
        model_display='LAP-V102S Series',
        model_name='Vital 100S',
        setup_entry='LAP-V102S',
    ),
    PurifierMap(
        class_name='VeSyncAirBaseV2',
        dev_types=[
            'LAP-V201S-AASR',
            'LAP-V201S-WJP',
            'LAP-V201S-WEU',
            'LAP-V201S-WUS',
            'LAP-V201-AUSR',
            'LAP-V201S-AUSR',
            'LAP-V201S-AEUR',
        ],
        modes=[
            PurifierModes.SLEEP,
            PurifierModes.MANUAL,
            PurifierModes.AUTO,
            PurifierModes.PET,
        ],
        features=[PurifierFeatures.AIR_QUALITY, PurifierFeatures.LIGHT_DETECT],
        fan_levels=list(range(1, 5)),
        device_alias='Vital 200S',
        auto_preferences=[
            PurifierAutoPreference.DEFAULT,
            PurifierAutoPreference.EFFICIENT,
            PurifierAutoPreference.QUIET,
        ],
        model_display='LAP-V201S Series',
        model_name='Vital 200S',
        setup_entry='LAP-V201S',
    ),
    PurifierMap(
        class_name='VeSyncAirBaseV2',
        dev_types=[
            'LAP-EL551S-AUS',
            'LAP-EL551S-AEUR',
            'LAP-EL551S-WEU',
            'LAP-EL551S-WUS',
        ],
        modes=[
            PurifierModes.SLEEP,
            PurifierModes.MANUAL,
            PurifierModes.AUTO,
            PurifierModes.TURBO,
        ],
        features=[
            PurifierFeatures.AIR_QUALITY,
            PurifierFeatures.VENT_ANGLE,
            PurifierFeatures.LIGHT_DETECT,
        ],
        fan_levels=list(range(1, 4)),
        device_alias='Everest Air',
        auto_preferences=[
            PurifierAutoPreference.DEFAULT,
            PurifierAutoPreference.EFFICIENT,
            PurifierAutoPreference.QUIET,
        ],
        model_display='LAP-EL551S Series',
        model_name='Everest Air',
        setup_entry='EL551S',
    ),
    PurifierMap(
        class_name='VeSyncAirSprout',
        dev_types=[
            'LAP-B851S-WEU',
            'LAP-B851S-WNA',
            'LAP-B851S-AEUR',
            'LAP-B851S-AUS',
            'LAP-B851S-WUS',
            'LAP-BAY-MAX01S',
        ],
        modes=[
            PurifierModes.SLEEP,
            PurifierModes.MANUAL,
            PurifierModes.AUTO,
        ],
        features=[
            PurifierFeatures.AIR_QUALITY,
            PurifierFeatures.NIGHTLIGHT,
        ],
        fan_levels=list(range(1, 4)),
        device_alias='Sprout Air Purifier',
        auto_preferences=[
            PurifierAutoPreference.DEFAULT,
            PurifierAutoPreference.EFFICIENT,
            PurifierAutoPreference.QUIET,
        ],
        model_display='Sprout Air Series',
        model_name='Sprout Air',
        setup_entry='LAP-B851S-WUS',
    ),
]
"""List of ['PurifierMap'][pyvesync.device_map.PurifierMap] configuration
objects for purifier devices."""


fan_modules: list[FanMap] = [
    FanMap(
        class_name='VeSyncTowerFan',
        dev_types=['LTF-F422S-KEU', 'LTF-F422S-WUSR', 'LTF-F422S-WJP', 'LTF-F422S-WUS'],
        modes={
            FanModes.NORMAL: 'normal',
            FanModes.TURBO: 'turbo',
            FanModes.AUTO: 'auto',
            FanModes.SLEEP: 'advancedSleep',
        },
        set_mode_method='setTowerFanMode',
        features=[
            FanFeatures.OSCILLATION,
            FanFeatures.DISPLAYING_TYPE,
            FanFeatures.SOUND,
        ],
        fan_levels=list(range(1, 13)),
        device_alias='Tower Fan',
        sleep_preferences=[
            FanSleepPreference.DEFAULT,
            FanSleepPreference.ADVANCED,
            FanSleepPreference.TURBO,
            FanSleepPreference.EFFICIENT,
            FanSleepPreference.QUIET,
        ],  # Unknown sleep preferences, need to be verified
        model_display='LTF-F422S Series',
        model_name='Classic 42-Inch Tower Fan',
        setup_entry='LTF-F422S',
    ),
    FanMap(
        class_name='VeSyncPedestalFan',
        dev_types=['LPF-R432S-AEU', 'LPF-R432S-AUS'],
        modes={
            FanModes.NORMAL: 'normal',
            FanModes.TURBO: 'turbo',
            FanModes.ECO: 'eco',
            FanModes.SLEEP: 'advancedSleep',
        },
        setup_entry='LPF-R423S',
        features=[
            FanFeatures.SET_OSCILLATION_RANGE,
            FanFeatures.HORIZONTAL_OSCILLATION,
            FanFeatures.VERTICAL_OSCILLATION,
        ],
        fan_levels=list(range(1, 13)),
        set_mode_method='setFanMode',
        device_alias='Pedestal Fan',
        sleep_preferences=[
            FanSleepPreference.DEFAULT,
            FanSleepPreference.ADVANCED,
            FanSleepPreference.TURBO,
            FanSleepPreference.QUIET,
        ],  # Unknown sleep preferences, need to be verified
        model_display='LPF-R432S Pedestal Fan Series',
        model_name='Pedestal Fan',
    ),
]
"""List of ['FanMap'][pyvesync.device_map.FanMap] configuration
objects for fan devices."""


# APK i61.C67931h (US, F) and i61.C67933i (EU, C) CS158 presets. Every mode
# has the same limits: F from the US class, C from the EU class. One
# captured cookMode request verifies the request shape for all of them
# (maintainer, 2026-11-03).
_CS158_TEMP_C = AirFryerTempLimits(min_temp=75, max_temp=205, step=5)
_CS158_TEMP_F = AirFryerTempLimits(min_temp=170, max_temp=400, step=10)

_CS158_COOK_MODES: dict[str, AirFryerModeConfig] = {
    # Label kept as the captured 'Manual Cooking' (CUSTOM_RECIPE_NAME).
    AirFryerCookModes.CUSTOM: AirFryerModeConfig(
        api_mode=CUSTOM_COOK_MODE,
        recipe_id=CUSTOM_RECIPE_ID,
        recipe_name=CUSTOM_RECIPE_NAME,
        cook_time=900,
        temp_c=_CS158_TEMP_C,
        temp_f=_CS158_TEMP_F,
        default_temp_c=175,
        default_temp_f=350,
    ),
    AirFryerCookModes.STEAK: AirFryerModeConfig(
        api_mode='steak',
        recipe_id=2,
        recipe_name='Steak',
        cook_time=360,
        temp_c=_CS158_TEMP_C,
        temp_f=_CS158_TEMP_F,
        default_temp_c=205,
        default_temp_f=400,
    ),
    AirFryerCookModes.CHICKEN: AirFryerModeConfig(
        api_mode='poultry',
        recipe_id=3,
        recipe_name='Chicken',
        cook_time=1500,
        temp_c=_CS158_TEMP_C,
        temp_f=_CS158_TEMP_F,
        default_temp_c=195,
        default_temp_f=380,
    ),
    AirFryerCookModes.SEAFOOD: AirFryerModeConfig(
        api_mode='fish',
        recipe_id=4,
        recipe_name='Seafood',
        cook_time=480,
        temp_c=_CS158_TEMP_C,
        temp_f=_CS158_TEMP_F,
        default_temp_c=175,
        default_temp_f=350,
    ),
    AirFryerCookModes.BACON: AirFryerModeConfig(
        api_mode='bacon',
        recipe_id=5,
        recipe_name='Bacon',
        cook_time=480,
        temp_c=_CS158_TEMP_C,
        temp_f=_CS158_TEMP_F,
        default_temp_c=160,
        default_temp_f=320,
    ),
    AirFryerCookModes.VEGETABLES: AirFryerModeConfig(
        api_mode='vegetables',
        recipe_id=6,
        recipe_name='Vegetables',
        cook_time=600,
        temp_c=_CS158_TEMP_C,
        temp_f=_CS158_TEMP_F,
        default_temp_c=150,
        default_temp_f=300,
    ),
    AirFryerCookModes.ROOT_VEGETABLES: AirFryerModeConfig(
        api_mode='rootVeggies',
        recipe_id=7,
        recipe_name='Root Vegetables',
        cook_time=720,
        temp_c=_CS158_TEMP_C,
        temp_f=_CS158_TEMP_F,
        default_temp_c=205,
        default_temp_f=400,
    ),
    AirFryerCookModes.FROZEN: AirFryerModeConfig(
        api_mode='frozenFood',
        recipe_id=8,
        recipe_name='Frozen Food',
        cook_time=600,
        temp_c=_CS158_TEMP_C,
        temp_f=_CS158_TEMP_F,
        default_temp_c=175,
        default_temp_f=300,
    ),
    AirFryerCookModes.DESSERTS: AirFryerModeConfig(
        api_mode='desserts',
        recipe_id=9,
        recipe_name='Desserts',
        cook_time=1800,
        temp_c=_CS158_TEMP_C,
        temp_f=_CS158_TEMP_F,
        default_temp_c=150,
        default_temp_f=300,
    ),
    # US class default time; the EU class has 360 s.
    AirFryerCookModes.SHRIMP: AirFryerModeConfig(
        api_mode='shrimp',
        recipe_id=10,
        recipe_name='Shrimp',
        cook_time=2100,
        temp_c=_CS158_TEMP_C,
        temp_f=_CS158_TEMP_F,
        default_temp_c=190,
        default_temp_f=370,
    ),
    AirFryerCookModes.BREAD: AirFryerModeConfig(
        api_mode='bread',
        recipe_id=11,
        recipe_name='Bread',
        cook_time=480,
        temp_c=_CS158_TEMP_C,
        temp_f=_CS158_TEMP_F,
        default_temp_c=160,
        default_temp_f=320,
    ),
    AirFryerCookModes.FRENCH_FRIES: AirFryerModeConfig(
        api_mode='frenchFries',
        recipe_id=12,
        recipe_name='French Fries',
        cook_time=1500,
        temp_c=_CS158_TEMP_C,
        temp_f=_CS158_TEMP_F,
        default_temp_c=195,
        default_temp_f=380,
    ),
}

# APK i61.C114380m (DC601S) presets. One captured startCook verifies the
# request shape for all of them (maintainer, 2026-11-03).
_DC601S_COOK_MODES: dict[str, AirFryerModeConfig] = {
    AirFryerCookModes.AIRFRY: AirFryerModeConfig(
        api_mode='AirFry',
        recipe_id=14,
        recipe_name='Air Fry',
        cook_time=600,
        temp_c=AirFryerTempLimits(min_temp=150, max_temp=230, step=5),
        temp_f=AirFryerTempLimits(min_temp=300, max_temp=450, step=5),
        default_temp_c=195,
        default_temp_f=385,
    ),
    AirFryerCookModes.ROAST: AirFryerModeConfig(
        api_mode='Roast',
        recipe_id=13,
        recipe_name='Roast',
        cook_time=720,
        temp_c=AirFryerTempLimits(min_temp=175, max_temp=230, step=5),
        temp_f=AirFryerTempLimits(min_temp=350, max_temp=450, step=5),
        default_temp_c=220,
        default_temp_f=425,
    ),
    AirFryerCookModes.BROIL: AirFryerModeConfig(
        api_mode='Broil',
        recipe_id=17,
        recipe_name='Broil',
        cook_time=300,
        temp_c=AirFryerTempLimits(min_temp=220, max_temp=230, step=5),
        temp_f=AirFryerTempLimits(min_temp=425, max_temp=450, step=5),
        default_temp_c=230,
        default_temp_f=450,
    ),
    AirFryerCookModes.FROZEN: AirFryerModeConfig(
        api_mode='Frozen',
        recipe_id=5,
        recipe_name='Frozen',
        cook_time=840,
        temp_c=AirFryerTempLimits(min_temp=150, max_temp=230, step=5),
        temp_f=AirFryerTempLimits(min_temp=300, max_temp=450, step=5),
        default_temp_c=200,
        default_temp_f=390,
    ),
    AirFryerCookModes.REHEAT: AirFryerModeConfig(
        api_mode='Reheat',
        recipe_id=16,
        recipe_name='Reheat',
        cook_time=300,
        temp_c=AirFryerTempLimits(min_temp=150, max_temp=220, step=5),
        temp_f=AirFryerTempLimits(min_temp=300, max_temp=425, step=5),
        default_temp_c=200,
        default_temp_f=390,
    ),
    AirFryerCookModes.BAKE: AirFryerModeConfig(
        api_mode='Bake',
        recipe_id=9,
        recipe_name='Bake',
        cook_time=1200,
        temp_c=AirFryerTempLimits(min_temp=125, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=260, max_temp=400, step=5),
        default_temp_c=165,
        default_temp_f=330,
    ),
    AirFryerCookModes.DRY: AirFryerModeConfig(
        api_mode='Dry',
        recipe_id=21,
        recipe_name='Dry',
        cook_time=21600,
        temp_c=AirFryerTempLimits(min_temp=35, max_temp=95, step=5),
        temp_f=AirFryerTempLimits(min_temp=100, max_temp=200, step=5),
        default_temp_c=55,
        default_temp_f=135,
    ),
    AirFryerCookModes.PROOF: AirFryerModeConfig(
        api_mode='Proof',
        recipe_id=27,
        recipe_name='Proof',
        cook_time=3600,
        temp_c=AirFryerTempLimits(min_temp=30, max_temp=45, step=1),
        temp_f=AirFryerTempLimits(min_temp=90, max_temp=110, step=1),
        default_temp_c=30,
        default_temp_f=90,
    ),
    AirFryerCookModes.WARM: AirFryerModeConfig(
        api_mode='Warm',
        recipe_id=26,
        recipe_name='Warm',
        cook_time=1800,
        temp_c=AirFryerTempLimits(min_temp=75, max_temp=75, step=1),
        temp_f=AirFryerTempLimits(min_temp=170, max_temp=170, step=1),
        default_temp_c=75,
        default_temp_f=170,
    ),
}

# APK i61.C114381v / i61.C114382w (P583S US / EU, identical) presets. One
# captured startCook verifies the request shape for all of them
# (maintainer, 2026-11-03). 'French fries' keeps the APK key's space.
_P583S_COOK_MODES: dict[str, AirFryerModeConfig] = {
    AirFryerCookModes.AIRFRY: AirFryerModeConfig(
        api_mode='AirFry',
        recipe_id=14,
        recipe_name='Air Fry',
        cook_time=600,
        temp_c=AirFryerTempLimits(min_temp=80, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=175, max_temp=400, step=5),
        default_temp_c=180,
        default_temp_f=360,
    ),
    AirFryerCookModes.BROIL: AirFryerModeConfig(
        api_mode='Broil',
        recipe_id=17,
        recipe_name='Broil',
        cook_time=600,
        temp_c=AirFryerTempLimits(min_temp=175, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=350, max_temp=400, step=5),
        default_temp_c=205,
        default_temp_f=400,
    ),
    AirFryerCookModes.ROAST: AirFryerModeConfig(
        api_mode='Roast',
        recipe_id=13,
        recipe_name='Roast',
        cook_time=600,
        temp_c=AirFryerTempLimits(min_temp=80, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=175, max_temp=400, step=5),
        default_temp_c=205,
        default_temp_f=400,
    ),
    AirFryerCookModes.BAKE: AirFryerModeConfig(
        api_mode='Bake',
        recipe_id=9,
        recipe_name='Bake',
        cook_time=1200,
        temp_c=AirFryerTempLimits(min_temp=120, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=250, max_temp=400, step=5),
        default_temp_c=160,
        default_temp_f=320,
    ),
    AirFryerCookModes.CHICKEN: AirFryerModeConfig(
        api_mode='Chicken',
        recipe_id=2,
        recipe_name='Chicken',
        cook_time=1200,
        temp_c=AirFryerTempLimits(min_temp=175, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=350, max_temp=400, step=5),
        default_temp_c=200,
        default_temp_f=390,
    ),
    AirFryerCookModes.STEAK: AirFryerModeConfig(
        api_mode='Steak',
        recipe_id=1,
        recipe_name='Steak',
        cook_time=480,
        temp_c=AirFryerTempLimits(min_temp=80, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=175, max_temp=400, step=5),
        default_temp_c=205,
        default_temp_f=400,
    ),
    AirFryerCookModes.SEAFOOD: AirFryerModeConfig(
        api_mode='Seafood',
        recipe_id=3,
        recipe_name='Seafood',
        cook_time=480,
        temp_c=AirFryerTempLimits(min_temp=160, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=320, max_temp=400, step=5),
        default_temp_c=190,
        default_temp_f=375,
    ),
    AirFryerCookModes.VEGETABLES: AirFryerModeConfig(
        api_mode='Veggies',
        recipe_id=15,
        recipe_name='Veggies',
        cook_time=360,
        temp_c=AirFryerTempLimits(min_temp=160, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=320, max_temp=400, step=5),
        default_temp_c=195,
        default_temp_f=385,
    ),
    AirFryerCookModes.FRENCH_FRIES: AirFryerModeConfig(
        api_mode='French fries',
        recipe_id=6,
        recipe_name='French Fries',
        cook_time=1200,
        temp_c=AirFryerTempLimits(min_temp=175, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=350, max_temp=400, step=5),
        default_temp_c=195,
        default_temp_f=385,
    ),
    AirFryerCookModes.FROZEN: AirFryerModeConfig(
        api_mode='Frozen',
        recipe_id=5,
        recipe_name='Frozen',
        cook_time=720,
        temp_c=AirFryerTempLimits(min_temp=175, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=350, max_temp=400, step=5),
        default_temp_c=200,
        default_temp_f=395,
    ),
    AirFryerCookModes.REHEAT: AirFryerModeConfig(
        api_mode='Reheat',
        recipe_id=16,
        recipe_name='Reheat',
        cook_time=300,
        temp_c=AirFryerTempLimits(min_temp=150, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=300, max_temp=400, step=5),
        default_temp_c=175,
        default_temp_f=350,
    ),
}

# APK i61.C67928f0 (TF101S) presets without Dry, shared with the TF102S
# (i61.C67932h0). One captured startMultiCook verifies the request shape
# for all of them (maintainer, 2026-11-03). Time limits are the app's picker
# (N() tables); no capture or report tests them on these models.
_TF10X_COOK_MODES: dict[str, AirFryerModeConfig] = {
    AirFryerCookModes.AIRFRY: AirFryerModeConfig(
        api_mode='AirFry',
        recipe_id=14,
        recipe_name='Air Fry',
        cook_time=1200,
        temp_c=AirFryerTempLimits(min_temp=120, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=250, max_temp=400, step=5),
        default_temp_c=200,
        default_temp_f=390,
        time_limits=AirFryerTimeLimits(min_seconds=60, max_seconds=3600, step_seconds=60),
    ),
    AirFryerCookModes.ROAST: AirFryerModeConfig(
        api_mode='Roast',
        recipe_id=13,
        recipe_name='Roast',
        cook_time=1800,
        temp_c=AirFryerTempLimits(min_temp=120, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=250, max_temp=400, step=5),
        default_temp_c=190,
        default_temp_f=375,
        time_limits=AirFryerTimeLimits(
            min_seconds=60, max_seconds=14400, step_seconds=60
        ),
    ),
    AirFryerCookModes.BAKE: AirFryerModeConfig(
        api_mode='Bake',
        recipe_id=9,
        recipe_name='Bake',
        cook_time=1500,
        temp_c=AirFryerTempLimits(min_temp=80, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=175, max_temp=400, step=5),
        default_temp_c=160,
        default_temp_f=320,
        time_limits=AirFryerTimeLimits(
            min_seconds=60, max_seconds=14400, step_seconds=60
        ),
    ),
    AirFryerCookModes.GRILL: AirFryerModeConfig(
        api_mode='Grill',
        recipe_id=20,
        recipe_name='Grill',
        cook_time=600,
        temp_c=AirFryerTempLimits(min_temp=205, max_temp=240, step=5),
        temp_f=AirFryerTempLimits(min_temp=400, max_temp=465, step=5),
        default_temp_c=240,
        default_temp_f=465,
        time_limits=AirFryerTimeLimits(min_seconds=60, max_seconds=1800, step_seconds=60),
    ),
    AirFryerCookModes.REHEAT: AirFryerModeConfig(
        api_mode='Reheat',
        recipe_id=16,
        recipe_name='Reheat',
        cook_time=900,
        temp_c=AirFryerTempLimits(min_temp=40, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=105, max_temp=400, step=5),
        default_temp_c=165,
        default_temp_f=330,
        time_limits=AirFryerTimeLimits(min_seconds=60, max_seconds=3600, step_seconds=60),
    ),
}

# TF101S Dry; its F limits (95-205) are the APK list, not a conversion.
_TF101S_COOK_MODES: dict[str, AirFryerModeConfig] = {
    **_TF10X_COOK_MODES,
    AirFryerCookModes.DRY: AirFryerModeConfig(
        api_mode='Dry',
        recipe_id=21,
        recipe_name='Dry',
        cook_time=21600,
        temp_c=AirFryerTempLimits(min_temp=35, max_temp=95, step=5),
        temp_f=AirFryerTempLimits(min_temp=95, max_temp=205, step=5),
        default_temp_c=55,
        default_temp_f=130,
        time_limits=AirFryerTimeLimits(
            min_seconds=1800, max_seconds=172800, step_seconds=1800
        ),
    ),
}


# ``hold`` is the chamber that waits during a Sync cook, and ``cookEnd`` a finished
# cook. The DC111S reports both (``hold`` captured, ``cookEnd`` in the PR #564 hardware
# test). For the TF101S and TF102S they come only from the APK, whose status handling
# has no model check.
_DUAL_STATUS_MAP: MappingProxyType[str, AirFryerCookStatus] = MappingProxyType(
    {
        'standby': AirFryerCookStatus.STANDBY,
        'ready': AirFryerCookStatus.READY,
        'cooking': AirFryerCookStatus.COOKING,
        'cookStop': AirFryerCookStatus.COOK_STOP,
        'pullOut': AirFryerCookStatus.PULL_OUT,
        'hold': AirFryerCookStatus.HOLD,
        'cookEnd': AirFryerCookStatus.COOK_END,
    }
)

# APK i61.C114379l (DC111SEUConfig) presets, with its time ranges and steps.
# Shake is off for every mode.
_DC111S_COOK_MODES: dict[str, AirFryerModeConfig] = {
    AirFryerCookModes.AIRFRY: AirFryerModeConfig(
        api_mode='AirFry',
        recipe_id=14,
        recipe_name='Air Fry',
        cook_time=600,
        temp_c=AirFryerTempLimits(min_temp=120, max_temp=230, step=5),
        temp_f=AirFryerTempLimits(min_temp=250, max_temp=450, step=5),
        default_temp_c=195,
        default_temp_f=385,
        time_limits=AirFryerTimeLimits(min_seconds=60, max_seconds=3600, step_seconds=60),
    ),
    AirFryerCookModes.BAKE: AirFryerModeConfig(
        api_mode='Bake',
        recipe_id=9,
        recipe_name='Bake',
        cook_time=1200,
        temp_c=AirFryerTempLimits(min_temp=125, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=260, max_temp=400, step=5),
        default_temp_c=165,
        default_temp_f=330,
        time_limits=AirFryerTimeLimits(min_seconds=60, max_seconds=3600, step_seconds=60),
    ),
    AirFryerCookModes.ROAST: AirFryerModeConfig(
        api_mode='Roast',
        recipe_id=13,
        recipe_name='Roast',
        cook_time=720,
        temp_c=AirFryerTempLimits(min_temp=175, max_temp=230, step=5),
        temp_f=AirFryerTempLimits(min_temp=350, max_temp=450, step=5),
        default_temp_c=220,
        default_temp_f=425,
        time_limits=AirFryerTimeLimits(min_seconds=60, max_seconds=3600, step_seconds=60),
    ),
    AirFryerCookModes.GRILL: AirFryerModeConfig(
        api_mode='Grill',
        recipe_id=20,
        recipe_name='Grill',
        cook_time=600,
        temp_c=AirFryerTempLimits(min_temp=160, max_temp=230, step=5),
        temp_f=AirFryerTempLimits(min_temp=320, max_temp=450, step=5),
        default_temp_c=230,
        default_temp_f=450,
        time_limits=AirFryerTimeLimits(min_seconds=60, max_seconds=3600, step_seconds=60),
    ),
    AirFryerCookModes.REHEAT: AirFryerModeConfig(
        api_mode='Reheat',
        recipe_id=16,
        recipe_name='Reheat',
        cook_time=300,
        temp_c=AirFryerTempLimits(min_temp=40, max_temp=205, step=5),
        temp_f=AirFryerTempLimits(min_temp=105, max_temp=400, step=5),
        default_temp_c=165,
        default_temp_f=330,
        time_limits=AirFryerTimeLimits(min_seconds=60, max_seconds=3600, step_seconds=60),
    ),
    AirFryerCookModes.DRY: AirFryerModeConfig(
        api_mode='Dry',
        recipe_id=21,
        recipe_name='Dry',
        cook_time=21600,
        temp_c=AirFryerTempLimits(min_temp=35, max_temp=95, step=5),
        temp_f=AirFryerTempLimits(min_temp=100, max_temp=200, step=5),
        default_temp_c=55,
        default_temp_f=130,
        time_limits=AirFryerTimeLimits(
            min_seconds=1800, max_seconds=86400, step_seconds=1800
        ),
    ),
    AirFryerCookModes.PROOF: AirFryerModeConfig(
        api_mode='Proof',
        recipe_id=27,
        recipe_name='Proof',
        cook_time=3600,
        temp_c=AirFryerTempLimits(min_temp=30, max_temp=45, step=1),
        temp_f=AirFryerTempLimits(min_temp=90, max_temp=115, step=1),
        default_temp_c=30,
        default_temp_f=90,
        time_limits=AirFryerTimeLimits(
            min_seconds=900, max_seconds=43200, step_seconds=900
        ),
    ),
}


air_fryer_modules: list[AirFryerMap] = [
    AirFryerMap(
        class_name='VeSyncAirFryer158',
        module=vesynckitchen,
        dev_types=['CS137-AF/CS158-AF', 'CS158-AF', 'CS137-AF'],
        device_alias='Air Fryer',
        model_display='CS158/159/168/169-AF Series',
        model_name='Smart/Pro/Pro Gen 2 5.8 Qt. Air Fryer',
        setup_entry='CS158-AF',
        temp_unit=TemperatureUnits.FAHRENHEIT,
        features=[AirFryerFeatures.PREHEAT, AirFryerFeatures.RESUMABLE],
        cook_modes=_CS158_COOK_MODES,
        default_preset=AirFryerPresets.custom,
        default_cook_mode=AirFryerCookModes.CUSTOM,
        time_units=TimeUnits.MINUTES,
        status_map=MappingProxyType(
            {
                'heating': AirFryerCookStatus.HEATING,
                'cooking': AirFryerCookStatus.COOKING,
                'cookStop': AirFryerCookStatus.COOK_STOP,
                'preheatStop': AirFryerCookStatus.PREHEAT_STOP,
                'preheatEnd': AirFryerCookStatus.PREHEAT_END,
                'pullOut': AirFryerCookStatus.PULL_OUT,
                'appointing': AirFryerCookStatus.APPOINTING,
                'standby': AirFryerCookStatus.STANDBY,
            }
        ),
    ),
    AirFryerMap(
        class_name='VeSyncTurboBlazeFryer',
        module=vesynckitchen,
        dev_types=['CAF-DC601S-WUSR', 'CAF-DC601S-WUS'],
        setup_entry='CAF-DC601S',
        device_alias='TurboBlaze Air Fryer',
        model_display='CAF-DC601S Series',
        model_name='TurboBlaze 6 Qt. Air Fryer',
        temp_unit=TemperatureUnits.FAHRENHEIT,
        features=[AirFryerFeatures.PREHEAT],
        cook_modes=_DC601S_COOK_MODES,
        default_cook_mode=AirFryerCookModes.AIRFRY,
        default_preset=AirFryerPresets.air_fry,
        time_units=TimeUnits.SECONDS,
        status_map=MappingProxyType(
            {
                'ready': AirFryerCookStatus.READY,
                'cooking': AirFryerCookStatus.COOKING,
                'heating': AirFryerCookStatus.HEATING,
                'cookStop': AirFryerCookStatus.COOK_STOP,
                'pullOut': AirFryerCookStatus.PULL_OUT,
                'cookEnd': AirFryerCookStatus.COOK_END,
            }
        ),
    ),
    AirFryerMap(
        # Cosori Dual Blaze US variant (single-chamber model with dual heating
        # elements). Uses the same bypassV2 protocol as TurboBlaze (startCook /
        # endCook / getAirfryerStatus). The Dual Blaze has no preheat function.
        class_name='VeSyncDualBlazeFryer',
        module=vesynckitchen,
        dev_types=['CAF-P583S-KUS'],
        setup_entry='CAF-P583S',
        device_alias='Dual Blaze Air Fryer',
        model_display='CAF-P583S Series',
        model_name='Dual Blaze 6.8 Qt. Air Fryer',
        temp_unit=TemperatureUnits.FAHRENHEIT,
        features=[],
        # APK i61.C114381v presets; one captured startCook (Broil) verifies the
        # request shape for all of them (maintainer, 2026-11-03).
        cook_modes=_P583S_COOK_MODES,
        default_cook_mode=AirFryerCookModes.AIRFRY,
        default_preset=AirFryerPresets.air_fry,
        time_units=TimeUnits.SECONDS,
        status_map=MappingProxyType(
            {
                'standby': AirFryerCookStatus.STANDBY,
                'ready': AirFryerCookStatus.READY,
                'cooking': AirFryerCookStatus.COOKING,
                'heating': AirFryerCookStatus.HEATING,
                'preheating': AirFryerCookStatus.HEATING,
                'cookStop': AirFryerCookStatus.COOK_STOP,
                'pullOut': AirFryerCookStatus.PULL_OUT,
                'cookEnd': AirFryerCookStatus.COOK_END,
                'keeping': AirFryerCookStatus.COOKING,
            }
        ),
    ),
    AirFryerMap(
        # Cosori Dual Blaze EU variant — Celsius. Same bypassV2 protocol as the
        # US variant above; only the declared temperature unit (and the setup
        # entry) differ.
        class_name='VeSyncDualBlazeFryer',
        module=vesynckitchen,
        dev_types=['CAF-P583S-KEU'],
        setup_entry='CAF-P583S-KEU',
        device_alias='Dual Blaze Air Fryer',
        model_display='CAF-P583S Series',
        model_name='Dual Blaze 6.8 Qt. Air Fryer',
        temp_unit=TemperatureUnits.CELSIUS,
        features=[],
        # APK i61.C114382w presets (identical to the US i61.C114381v).
        cook_modes=_P583S_COOK_MODES,
        default_cook_mode=AirFryerCookModes.AIRFRY,
        default_preset=AirFryerPresets.air_fry,
        time_units=TimeUnits.SECONDS,
        status_map=MappingProxyType(
            {
                'standby': AirFryerCookStatus.STANDBY,
                'ready': AirFryerCookStatus.READY,
                'cooking': AirFryerCookStatus.COOKING,
                'heating': AirFryerCookStatus.HEATING,
                'preheating': AirFryerCookStatus.HEATING,
                'cookStop': AirFryerCookStatus.COOK_STOP,
                'pullOut': AirFryerCookStatus.PULL_OUT,
                'cookEnd': AirFryerCookStatus.COOK_END,
                'keeping': AirFryerCookStatus.COOKING,
            }
        ),
    ),
    AirFryerMap(
        # APK i61.C67928f0 (TF101S) presets; one captured startMultiCook
        # verifies the request shape for all of them (maintainer, 2026-11-03).
        class_name='VeSyncDualAirFryer',
        module=vesynckitchen,
        dev_types=['CAF-TF101S-AEU', 'CAF-TF101S'],
        setup_entry='CAF-TF101S',
        device_alias='Dual Air Fryer',
        model_display='CAF-TF101S Series',
        model_name='Cosori Dual Air Fryer',
        temp_unit=TemperatureUnits.CELSIUS,
        features=[AirFryerFeatures.DUAL_CHAMBER, AirFryerFeatures.WHOLE_CHAMBER],
        cook_modes=_TF101S_COOK_MODES,
        default_cook_mode=AirFryerCookModes.AIRFRY,
        default_preset=AirFryerPresets.air_fry,
        time_units=TimeUnits.SECONDS,
        status_map=_DUAL_STATUS_MAP,
    ),
    AirFryerMap(
        # APK i61.C67932h0 (TF102SEUConfig): the TF101S presets without Dry.
        # No TF102S capture; the dual request and status shapes are verified
        # by the TF101S captures.
        class_name='VeSyncDualAirFryer',
        module=vesynckitchen,
        dev_types=['CAF-TF102S'],
        setup_entry='CAF-TF102S',
        device_alias='Dual Air Fryer',
        model_display='CAF-TF102S Series',
        model_name='Cosori Dual Air Fryer',
        temp_unit=TemperatureUnits.CELSIUS,
        features=[AirFryerFeatures.DUAL_CHAMBER, AirFryerFeatures.WHOLE_CHAMBER],
        cook_modes=_TF10X_COOK_MODES,
        default_cook_mode=AirFryerCookModes.AIRFRY,
        default_preset=AirFryerPresets.air_fry,
        time_units=TimeUnits.SECONDS,
        status_map=_DUAL_STATUS_MAP,
    ),
    AirFryerMap(
        # APK i61.C114379l (DC111SEUConfig): upper (1) and lower (2) chambers,
        # no whole-basket mode. Same multi-chamber API as the TF101S, but its
        # cook configs send shakeTime 0: PR #536 tested it on hardware, the
        # capture shows code 0, and APK C42441q1.s1 sets it.
        class_name='VeSyncDualAirFryer',
        module=vesynckitchen,
        dev_types=['CAF-DC111S-AEU'],
        setup_entry='CAF-DC111S-AEU',
        device_alias='Turbo Tower Pro Air Fryer',
        model_display='CAF-DC111S-AEU',
        model_name='Turbo Tower Pro Smart Air Fryer',
        temp_unit=TemperatureUnits.CELSIUS,
        features=[
            AirFryerFeatures.DUAL_CHAMBER,
            AirFryerFeatures.CHAMBER_MODES,
            AirFryerFeatures.COOK_CONFIG_SHAKE_TIME,
            AirFryerFeatures.RESUMABLE,
            AirFryerFeatures.READY_START,
        ],
        cook_modes=_DC111S_COOK_MODES,
        default_cook_mode=AirFryerCookModes.AIRFRY,
        default_preset=AirFryerPresets.air_fry,
        time_units=TimeUnits.SECONDS,
        status_map=_DUAL_STATUS_MAP,
    ),
]
"""List of ['AirFryerMap'][pyvesync.device_map.AirFryerMap] configuration
for air fryer devices."""


full_device_list = [
    *fan_modules,
    *purifier_modules,
    *humidifier_modules,
    *air_fryer_modules,
    *thermostat_modules,
]
"""List of all device configuration objects."""


def get_device_config(device_type: str) -> DeviceMapTemplate | None:
    """Get general device details from device type to create instance.

    Args:
        device_type (str): Device type to match from device list API call.

    Returns:
        DeviceMapTemplate | None: DeviceMapTemplate object or None if not found.
    """
    all_modules: list[T_MAPS] = [
        outlet_modules,
        switch_modules,
        bulb_modules,
        fan_modules,
        purifier_modules,
        humidifier_modules,
        air_fryer_modules,
        thermostat_modules,
    ]
    for module in chain(*all_modules):
        if device_type in module.dev_types:
            return module
    if device_type.count('-') > 1:
        device_type = '-'.join(device_type.split('-')[:-1])
        for module in chain(*all_modules):
            if any(device_type.lower() in dev.lower() for dev in module.dev_types):
                return module
    return None


def get_fan(device_type: str) -> FanMap | None:
    """Get fan device details from device type.

    Args:
        device_type (str): Device type to match from device list API call.

    Returns:
        FanMap | None: FanMap object or None if not found.
    """
    for module in fan_modules:
        if device_type in module.dev_types:
            return module
    # Try to match with a more generic device type
    if device_type.count('-') > 1:
        device_type = '-'.join(device_type.split('-')[:-1])
        for module in fan_modules:
            if any(device_type.lower() in dev.lower() for dev in module.dev_types):
                return module
    return None


def get_purifier(device_type: str) -> PurifierMap | None:
    """Get purifier device details from device type.

    Args:
        device_type (str): Device type to match from device list API call.

    Returns:
        PurifierMap | None: PurifierMap object or None if not found.
    """
    for module in purifier_modules:
        if device_type in module.dev_types:
            return module
    if device_type.count('-') > 1:
        device_type = '-'.join(device_type.split('-')[:-1])
        for module in purifier_modules:
            if any(device_type.lower() in dev.lower() for dev in module.dev_types):
                return module
    return None


def get_humidifier(device_type: str) -> HumidifierMap | None:
    """Get humidifier device details from device type.

    Args:
        device_type (str): Device type to match from device list API call.

    Returns:
        HumidifierMap | None: HumidifierMap object or None if not found.
    """
    for module in humidifier_modules:
        if device_type in module.dev_types:
            return module
    if device_type.count('-') > 1:
        device_type = '-'.join(device_type.split('-')[:-1])
        for module in humidifier_modules:
            if any(device_type.lower() in dev.lower() for dev in module.dev_types):
                return module
    return None


def get_outlet(device_type: str) -> OutletMap | None:
    """Get outlet device details from device type.

    Args:
        device_type (str): Device type to match from device list API call.

    Returns:
        OutletMap | None: OutletMap object or None if not found.
    """
    for module in outlet_modules:
        if device_type in module.dev_types:
            return module
    if device_type.count('-') > 1:
        device_type = '-'.join(device_type.split('-')[:-1])
        for module in outlet_modules:
            if any(device_type.lower() in dev.lower() for dev in module.dev_types):
                return module
    return None


def get_switch(device_type: str) -> SwitchMap | None:
    """Get switch device details from device type.

    Args:
        device_type (str): Device type to match from device list API call.

    Returns:
        SwitchMap | None: SwitchMap object or None if not found.
    """
    for module in switch_modules:
        if device_type in module.dev_types:
            return module
    if device_type.count('-') > 1:
        device_type = '-'.join(device_type.split('-')[:-1])
        for module in switch_modules:
            if any(device_type.lower() in dev.lower() for dev in module.dev_types):
                return module
    return None


def get_bulb(device_type: str) -> BulbMap | None:
    """Get bulb device details from device type.

    Args:
        device_type (str): Device type to match from device list API call.

    Returns:
        BulbMap | None: BulbMap object or None if not found.
    """
    for module in bulb_modules:
        if device_type in module.dev_types:
            return module
    if device_type.count('-') > 1:
        device_type = '-'.join(device_type.split('-')[:-1])
        for module in bulb_modules:
            if any(device_type.lower() in dev.lower() for dev in module.dev_types):
                return module
    return None


def get_air_fryer(device_type: str) -> AirFryerMap | None:
    """Get air fryer device details from device type.

    Args:
        device_type (str): Device type to match from device list API call.

    Returns:
        AirFryerMap | None: AirFryerMap object or None if not found.
    """
    for module in air_fryer_modules:
        if device_type in module.dev_types:
            return module
    if device_type.count('-') > 1:
        device_type = '-'.join(device_type.split('-')[:-1])
        for module in air_fryer_modules:
            if any(device_type.lower() in dev.lower() for dev in module.dev_types):
                return module
    return None


def get_thermostat(device_type: str) -> ThermostatMap | None:
    """Get the device map for a thermostat.

    Args:
        device_type (str): The device type to match.

    Returns:
        ThermostatMap | None: The matching thermostat map or None if not found.
    """
    for module in thermostat_modules:
        if device_type in module.dev_types:
            return module
    if device_type.count('-') > 1:
        device_type = '-'.join(device_type.split('-')[:-1])
        for module in thermostat_modules:
            if any(device_type.lower() in dev.lower() for dev in module.dev_types):
                return module
    return None
