"""Device and module mappings for VeSync devices.

This module contains mappings for VeSync devices to their respective modules
and classes. The mappings are used to create instances of the appropriate
device class based on the device type and define features and modes.

The AirFryerMap, OutletMap, SwitchMap, BulbMap, FanMap, HumidifierMap, and PurifierMap
dataclasses are used to define the mappings for each product type with the assocated
module, class, features and other device specific configuration. The `get_device_details`
function is used to get the device detail from the device type to instantiate the device
object. The individual `get_<device>_config` functions are used to get the device details
for the specific to the device type. Both functions return the same data, the individual
functions are used to satisfy type checking in the individual devices.

Attributes:
    ProductTypes: Enum: General device types enum.
    DeviceMapTemplate: dataclass: Template for DeviceModules mapping.
    OutletMap: dataclass: Template for Outlet device mapping.
    SwitchMap: dataclass: Template for Switch device mapping.
    BulbMap: dataclass: Template for Bulb device mapping.
    FanMap: dataclass: Template for Fan device mapping.
    HumidifierMap: dataclass: Template for Humidifier device mapping.
    PurifierMap: dataclass: Template for Purifier device mapping.
    KitchenMap: dataclass: Template for Kitchen Thermometer device mapping.
    outlet_modules: list[OutletMap]: List of Outlet device mappings.
    switch_modules: list[SwitchMap]: List of Switch device mappings.
    bulb_modules: list[BulbMap]: List of Bulb device mappings.
    fan_modules: list[FanMap]: List of Fan device mappings.
    purifier_modules: list[PurifierMap]: List of Purifier device mappings.
    humdifier_modules: list[HumidifierMap]: List of Humidifier device mappings.

Note:
    To add devices, add the device mapping to the appropriate `*_modules` list,
    ensuring all required fields are present.
"""
from itertools import chain
# from types import ModuleType
from types import ModuleType
from typing import Union, TypeVar
from dataclasses import dataclass, field
from pyvesync.devices import vesyncbulb
from pyvesync.devices import vesyncoutlet
from pyvesync.devices import vesyncswitch
from pyvesync.devices import vesyncfan, vesynchumidifier, vesyncpurifier
from pyvesync.devices import vesynckitchen
from pyvesync.const import (
    ColorMode,
    PurifierModes,
    HumidifierModes,
    BulbFeatures,
    OutletFeatures,
    ProductTypes,
    SwitchFeatures,
    HumidifierFeatures,
    PurifierFeatures,
    NightlightModes,
    PurifierAutoPreference,
    FanSleepPreference,
    FanModes,
)

T_MAPS = Union[
    list["OutletMap"],
    list["SwitchMap"],
    list["BulbMap"],
    list["FanMap"],
    list["HumidifierMap"],
    list["PurifierMap"],
    list["AirFryerMap"],
    ]

T_DEV_DETAILS = TypeVar("T_DEV_DETAILS")


@dataclass(kw_only=True)
class DeviceMapTemplate:
    """Template for DeviceModules mapping."""

    dev_types: list[str]
    class_name: str
    product_type: str
    module: ModuleType
    device_alias: str | None = None
    features: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class OutletMap(DeviceMapTemplate):
    """Template for DeviceModules mapping."""
    product_type: str = ProductTypes.OUTLET
    module: ModuleType = vesyncoutlet


@dataclass(kw_only=True)
class SwitchMap(DeviceMapTemplate):
    """Template for DeviceModules mapping."""
    product_type: str = ProductTypes.SWITCH
    module: ModuleType = vesyncswitch


@dataclass(kw_only=True)
class BulbMap(DeviceMapTemplate):
    """Template for DeviceModules mapping."""
    color_model: str | None = None
    product_type: str = ProductTypes.BULB
    module: ModuleType = vesyncbulb
    color_modes: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class FanMap(DeviceMapTemplate):
    """Template for DeviceModules mapping."""
    product_type: str = ProductTypes.FAN
    module: ModuleType = vesyncfan
    fan_levels: list[int] = field(default_factory=list)
    modes: list[str] = field(default_factory=list)
    sleep_preferences: list[str] = field(default_factory=list)
    set_mode_method: str = ""


@dataclass(kw_only=True)
class HumidifierMap(DeviceMapTemplate):
    """Template for DeviceModules mapping."""

    mist_modes: dict[str, str] = field(default_factory=dict)
    mist_levels: list[int | str] = field(default_factory=list)
    product_type: str = ProductTypes.HUMIDIFIER
    module: ModuleType = vesynchumidifier
    target_minmax: tuple[int, int] = (30, 80)
    warm_mist_levels: list[int | str] = field(default_factory=list)


@dataclass(kw_only=True)
class PurifierMap(DeviceMapTemplate):
    """Template for DeviceModules mapping."""

    product_type: str = ProductTypes.PURIFIER
    module: ModuleType = vesyncpurifier
    fan_levels: list[int] = field(default_factory=list)
    modes: list[str] = field(default_factory=list)
    nightlight_modes: list[str] = field(default_factory=list)
    auto_preferences: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class AirFryerMap(DeviceMapTemplate):
    """Template for DeviceModules mapping."""

    product_type: str = ProductTypes.KITCHEN_THERMOMETER
    module: ModuleType = vesynckitchen


outlet_modules = [
    OutletMap(
        dev_types=["wifi-switch-1.3"],
        class_name="VeSyncOutlet7A",
        features=[OutletFeatures.ENERGY_MONITOR],
    ),
    OutletMap(
        dev_types=["ESW03-USA"],
        class_name="VeSyncOutlet10A",
        features=[OutletFeatures.ENERGY_MONITOR],
    ),
    OutletMap(
        dev_types=["ESW01-EU"],
        class_name="VeSyncOutlet10A",
        features=[OutletFeatures.ENERGY_MONITOR],
    ),
    OutletMap(
        dev_types=["ESW15-USA"],
        class_name="VeSyncOutlet15A",
        features=[OutletFeatures.ENERGY_MONITOR, OutletFeatures.NIGHTLIGHT],
    ),
    OutletMap(
        dev_types=["ESO15-TB"],
        class_name="VeSyncOutdoorPlug",
        features=[OutletFeatures.ENERGY_MONITOR],
    ),
    OutletMap(
        dev_types=["BSDOG01"],
        class_name="VeSyncOutletBSDGO1",
        features=[OutletFeatures.ONOFF],
    ),
]


switch_modules = [
    SwitchMap(
        dev_types=["ESWL01"],
        class_name="VeSyncWallSwitch",
        device_alias="Wall Switch",
        features=[SwitchFeatures.ONOFF],
    ),
    SwitchMap(
        dev_types=["ESWD16"],
        class_name="VeSyncDimmerSwitch",
        features=[
            SwitchFeatures.DIMMABLE,
            SwitchFeatures.INDICATOR_LIGHT,
            SwitchFeatures.BACKLIGHT_RGB,
        ],
        device_alias="Dimmer Switch",
    ),
    SwitchMap(
        dev_types=["ESWL03"],
        class_name="VeSyncWallSwitch",
        device_alias="Three-Way Wall Switch",
        features=[SwitchFeatures.ONOFF],
    ),
]

# Bulb Device Definition
# Format: BulbMap(
#     dev_types=["<device_type>"],
#     class_name="<class_name>",
#     features=["<feature>"],
#     color_model="<color_model>",
#     device_alias="<device_alias>")
bulb_modules = [
    BulbMap(
        dev_types=["ESL100"],
        class_name="VeSyncBulbESL100",
        features=[SwitchFeatures.DIMMABLE],
        color_model=None,
        device_alias="Dimmable Bright White Bulb",
        color_modes=[ColorMode.WHITE],
    ),
    BulbMap(
        dev_types=["ESL100CW"],
        class_name="VeSyncBulbESL100CW",
        features=[BulbFeatures.DIMMABLE, BulbFeatures.COLOR_TEMP],
        color_model=None,
        device_alias="Dimmable Tunable White Bulb",
        color_modes=[ColorMode.WHITE],
    ),
    BulbMap(
        dev_types=["XYD0001"],
        class_name="VeSyncBulbValcenoA19MC",
        features=[
            BulbFeatures.DIMMABLE,
            BulbFeatures.MULTICOLOR,
            BulbFeatures.COLOR_TEMP,
        ],
        color_model=ColorMode.HSV,
        device_alias="Valceno Dimmable RGB Bulb",
        color_modes=[ColorMode.WHITE, ColorMode.COLOR],
    ),
    BulbMap(
        dev_types=["ESL100MC"],
        class_name="VeSyncBulbESL100MC",
        features=[
            BulbFeatures.COLOR_TEMP,
            BulbFeatures.MULTICOLOR,
            BulbFeatures.DIMMABLE,
        ],
        color_model=ColorMode.RGB,
        device_alias="Etekcity Dimmable RGB Bulb",
        color_modes=[ColorMode.WHITE, ColorMode.COLOR],
    ),
]

humdifier_modules: list[HumidifierMap] = [
    HumidifierMap(
        class_name="VeSyncHumid200300S",
        dev_types=["Classic300S", "LUH-A601S-WUSB", "LUH-A601S-AUSW"],
        features=[HumidifierFeatures.NIGHTLIGHT],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
            },
        mist_levels=list(range(1, 10)),
        device_alias="Classic 300S",
    ),
    HumidifierMap(
        class_name="VeSyncHumid200S",
        dev_types=["Classic200S"],
        features=[],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.MANUAL: 'manual',
            },
        mist_levels=list(range(1, 10)),
        device_alias="Classic 200S",
    ),
    HumidifierMap(
        class_name="VeSyncHumid200300S",
        dev_types=["Dual200S", "LUH-D301S-WUSR", "LUH-D301S-WJP", "LUH-D301S-WEU"],
        features=[],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.MANUAL: 'manual',
            },
        mist_levels=list(range(1, 3)),
        device_alias="Dual 200S",
    ),
    HumidifierMap(
        class_name="VeSyncHumid200300S",
        dev_types=[
            "LUH-A602S-WUSR",
            "LUH-A602S-WUS",
            "LUH-A602S-WEUR",
            "LUH-A602S-WEU",
            "LUH-A602S-WJP",
            "LUH-A602S-WUSC",
        ],
        features=[HumidifierFeatures.WARM_MIST, HumidifierFeatures.NIGHTLIGHT],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
            },
        mist_levels=list(range(1, 10)),
        warm_mist_levels=[0, 1, 2, 3],
        device_alias="LV600S",
    ),
    HumidifierMap(
        class_name="VeSyncHumid200300S",
        dev_types=["LUH-O451S-WEU"],
        features=[HumidifierFeatures.WARM_MIST, HumidifierFeatures.NIGHTLIGHT],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
            },
        mist_levels=list(range(1, 10)),
        warm_mist_levels=list(range(4)),
        device_alias="OasisMist 450S EU",
    ),
    HumidifierMap(
        class_name="VeSyncHumid200300S",
        dev_types=["LUH-O451S-WUS", "LUH-O451S-WUSR", "LUH-O601S-WUS", "LUH-O601S-KUS"],
        features=[HumidifierFeatures.WARM_MIST],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
            HumidifierModes.HUMIDITY: 'humidity',
        },
        mist_levels=list(range(1, 10)),
        warm_mist_levels=list(range(4)),
        device_alias="OasisMist 450S",
    ),
    HumidifierMap(
        class_name="VeSyncHumid1000S",
        dev_types=["LUH-M101S-WUS", "LUH-M101S-WEUR", "LUH-M101S-WUSR"],
        features=[],
        mist_modes={
            HumidifierModes.AUTO: 'auto',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.MANUAL: 'manual',
            },
        mist_levels=list(range(1, 10)),
        device_alias="Oasismist 1000S",
    ),
    HumidifierMap(
        class_name="VeSyncSuperior6000S",
        dev_types=["LEH-S601S-WUS", "LEH-S601S-WUSR", "LEH-S601S-WEUR"],
        features=[],
        mist_modes={
            HumidifierModes.AUTO: 'autoPro',
            HumidifierModes.SLEEP: 'sleep',
            HumidifierModes.HUMIDITY: 'humidity',
            HumidifierModes.MANUAL: 'manual',
            HumidifierModes.AUTOPRO: 'autoPro',
            },
        mist_levels=list(range(1, 10)),
        device_alias="Superior 6000S",
    ),
]


purifier_modules: list[PurifierMap] = [
    PurifierMap(
        class_name="VeSyncAirBypass",
        dev_types=["Core200S", "LAP-C201S-AUSR", "LAP-C202S-WUSR"],
        modes=[PurifierModes.SLEEP, PurifierModes.MANUAL],
        features=[PurifierFeatures.RESET_FILTER, PurifierFeatures.NIGHTLIGHT],
        fan_levels=list(range(1, 4)),
        nightlight_modes=[NightlightModes.ON, NightlightModes.OFF, NightlightModes.DIM],
        device_alias="Core 200S",
    ),
    PurifierMap(
        class_name="VeSyncAirBypass",
        dev_types=["Core300S", "LAP-C301S-WJP", "LAP-C302S-WUSB", "LAP-C301S-WAAA"],
        modes=[PurifierModes.SLEEP, PurifierModes.MANUAL, PurifierModes.AUTO],
        features=[PurifierFeatures.AIR_QUALITY],
        fan_levels=list(range(1, 5)),
        device_alias="Core 300S",
    ),
    PurifierMap(
        class_name="VeSyncAirBypass",
        dev_types=["Core400S", "LAP-C401S-WJP", "LAP-C401S-WUSR", "LAP-C401S-WAAA"],
        modes=[PurifierModes.SLEEP, PurifierModes.MANUAL, PurifierModes.AUTO],
        features=[PurifierFeatures.AIR_QUALITY],
        fan_levels=list(range(1, 5)),
        device_alias="Core 400S",
        auto_preferences=[
            PurifierAutoPreference.DEFAULT,
            PurifierAutoPreference.EFFICIENT,
            PurifierAutoPreference.QUIET
            ]
    ),
    PurifierMap(
        class_name="VeSyncAirBypass",
        dev_types=["Core600S", "LAP-C601S-WUS", "LAP-C601S-WUSR", "LAP-C601S-WEU"],
        modes=[PurifierModes.SLEEP, PurifierModes.MANUAL, PurifierModes.AUTO],
        features=[PurifierFeatures.AIR_QUALITY],
        fan_levels=list(range(1, 5)),
        device_alias="Core 600S",
    ),
    PurifierMap(
        class_name="VeSyncAir131",
        dev_types=["LV-PUR131S", "LV-RH131S"],
        modes=[PurifierModes.SLEEP, PurifierModes.MANUAL, PurifierModes.AUTO],
        features=[PurifierFeatures.AIR_QUALITY],
        fan_levels=list(range(1, 3)),
        device_alias="LV-PUR131S",
    ),
    PurifierMap(
        class_name="VeSyncAirBaseV2",
        dev_types=[
            "LAP-V102S-AASR",
            "LAP-V102S-WUS",
            "LAP-V102S-WEU",
            "LAP-V102S-AUSR",
            "LAP-V102S-WJP",
        ],
        modes=[
            PurifierModes.SLEEP,
            PurifierModes.MANUAL,
            PurifierModes.AUTO,
            PurifierModes.PET,
        ],
        features=[PurifierFeatures.AIR_QUALITY],
        fan_levels=list(range(1, 5)),
        device_alias="Vital 100S",
        auto_preferences=[
            PurifierAutoPreference.DEFAULT,
            PurifierAutoPreference.EFFICIENT,
            PurifierAutoPreference.QUIET
            ]
    ),
    PurifierMap(
        class_name="VeSyncAirBaseV2",
        dev_types=[
            "LAP-V201S-AASR",
            "LAP-V201S-WJP",
            "LAP-V201S-WEU",
            "LAP-V201S-WUS",
            "LAP-V201-AUSR",
            "LAP-V201S-AUSR",
            "LAP-V201S-AEUR",
        ],
        modes=[
            PurifierModes.SLEEP,
            PurifierModes.MANUAL,
            PurifierModes.AUTO,
            PurifierModes.PET,
        ],
        features=[PurifierFeatures.AIR_QUALITY],
        fan_levels=list(range(1, 5)),
        device_alias="Vital 200S",
        auto_preferences=[
            PurifierAutoPreference.DEFAULT,
            PurifierAutoPreference.EFFICIENT,
            PurifierAutoPreference.QUIET
            ]
    ),
    PurifierMap(
        class_name="VeSyncAirBaseV2",
        dev_types=[
            "LAP-EL551S-AUS",
            "LAP-EL551S-AEUR",
            "LAP-EL551S-WEU",
            "LAP-EL551S-WUS",
        ],
        modes=[
            PurifierModes.SLEEP,
            PurifierModes.MANUAL,
            PurifierModes.AUTO,
            PurifierModes.TURBO,
        ],
        features=[PurifierFeatures.AIR_QUALITY, PurifierFeatures.FAN_ROTATE],
        fan_levels=list(range(1, 4)),
        device_alias="Everest Air",
        auto_preferences=[
            PurifierAutoPreference.DEFAULT,
            PurifierAutoPreference.EFFICIENT,
            PurifierAutoPreference.QUIET
            ]
    ),
]


fan_modules: list[FanMap] = [
    FanMap(
        class_name="VeSyncTowerFan",
        dev_types=["LTF-F422S-KEU", "LTF-F422S-WUSR", "LTF-F422_WJP", "LTF-F422S-WUS"],
        modes=[
            FanModes.SLEEP,  # Alias for Advanced sleep mode
            FanModes.NORMAL,
            FanModes.MANUAL,
            FanModes.TURBO,
            FanModes.AUTO,
            FanModes.ADVANCED_SLEEP,
            ],
        set_mode_method="setTowerFanMode",
        features=["fan_speed"],
        fan_levels=list(range(1, 13)),
        device_alias="Tower Fan",
        sleep_preferences=[
            FanSleepPreference.DEFAULT,
            FanSleepPreference.ADVANCED,
            FanSleepPreference.TURBO,
            FanSleepPreference.EFFICIENT,
            FanSleepPreference.QUIET,
        ]  # Unknown sleep preferences, need to be verified
    ),
]


air_fryer_modules: list[AirFryerMap] = [
    AirFryerMap(
        class_name="VeSyncAirFryer158",
        module=vesynckitchen,
        dev_types=['CS137-AF/CS158-AF', 'CS158-AF', 'CS137-AF', 'CS358-AF'],
        device_alias="Air Fryer",
    ),
]


def get_device_config(device_type: str) -> DeviceMapTemplate | None:
    """Get general device details from device type to create instance."""
    all_modules: list[T_MAPS] = [
        outlet_modules,
        switch_modules,
        bulb_modules,
        fan_modules,
        purifier_modules,
        humdifier_modules,
        air_fryer_modules,
    ]
    for module in chain(*all_modules):
        if device_type in module.dev_types:
            return module
    return None
