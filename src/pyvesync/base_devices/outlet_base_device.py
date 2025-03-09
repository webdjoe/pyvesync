"""Base Devices for Outlets."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from pyvesync.const import OutletFeatures
from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseToggleDevice, DeviceState

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import OutletMap
    from pyvesync.data_models.device_list_models import ResponseDeviceDetailsModel
    from pyvesync.data_models.outlet_models import ResponseEnergyResult

logger = logging.getLogger(__name__)


class OutletState(DeviceState):
    """Base state class for Outlets."""

    __slots__ = (
        "energy",
        "monthly_history",
        "nightlight_automode",
        "nightlight_brightness",
        "nightlight_status",
        "power",
        "voltage",
        "weekly_history",
        "yearly_history",
    )

    def __init__(
        self,
        device: VeSyncOutlet,
        details: ResponseDeviceDetailsModel,
        feature_map: OutletMap
            ) -> None:
        """Initialize VeSync Switch State."""
        super().__init__(device, details, feature_map)
        self.device: VeSyncOutlet = device
        self.features: list[str] = feature_map.features
        self.active_time: int = 0
        self.power: float = 0
        self.energy: float = 0
        self.voltage: float = 0
        self.nightlight_status: str | None = None
        self.nightlight_brightness: int | None = None
        self.nightlight_automode: str | None = None
        self.weekly_history: ResponseEnergyResult | None = None
        self.monthly_history: ResponseEnergyResult | None = None
        self.yearly_history: ResponseEnergyResult | None = None


class VeSyncOutlet(VeSyncBaseToggleDevice):
    """Base class for Etekcity Outlets."""

    # __metaclass__ = ABCMeta

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: OutletMap) -> None:
        """Initilize VeSync Outlet base class."""
        super().__init__(details, manager, feature_map)
        self.state: OutletState = OutletState(self, details, feature_map)
        self.details: dict = {}
        self.energy: dict = {}
        self.update_energy_ts: None | int = None

    # @abstractmethod
    # async def turn_on(self) -> bool:
    #     """Return True if device has beeeen turned on."""

    # @abstractmethod
    # async def turn_off(self) -> bool:
    #     """Return True if device has beeeen turned off."""

    # @abstractmethod
    # async def get_details(self) -> None:
    #     """Build details dictionary."""

    @property
    def supports_nightlight(self) -> bool:
        """Return True if device supports nightlight."""
        return OutletFeatures.NIGHTLIGHT in self.features

    @property
    def supports_energy(self) -> bool:
        """Return True if device supports energy."""
        return OutletFeatures.ENERGY_MONITOR in self.features

    async def get_weekly_energy(self) -> None:
        """Build weekly energy history dictionary."""

    async def get_monthly_energy(self) -> None:
        """Build Monthly Energy History Dictionary."""

    async def get_yearly_energy(self) -> None:
        """Build Yearly Energy Dictionary."""

    async def update(self) -> None:
        """Get Device Energy and Status."""
        await self.get_details()

    async def update_energy(self) -> None:
        """Build weekly, monthly and yearly dictionaries."""
        if self.supports_energy:
            await self.get_weekly_energy()
            await self.get_monthly_energy()
            await self.get_yearly_energy()

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp = [
            ('Active Time : ', self.state.active_time, ' minutes'),
            ('Power: ', self.state.power, ' Watts'),
            ('Voltage: ', self.state.voltage, ' Volts'),
        ]
        for line in disp:
            print(f'{line[0]:.<30} {line[1]} {line[2]}')

    def displayJSON(self) -> str:
        """Return JSON details for outlet."""
        return super().displayJSON()  # TODO: FIX THIS
        # sup_val = orjson.loads(sup)
        # sup_val.update(
        #     {
        #         'Active Time': str(self.active_time),
        #         'Energy': str(self.energy_today),
        #         'Power': str(self.power),
        #         'Voltage': str(self.voltage),
        #         'Energy Week': str(self.weekly_energy_total),
        #         'Energy Month': str(self.monthly_energy_total),
        #         'Energy Year': str(self.yearly_energy_total),
        #     }
        # )

        # return orjson.dumps(
        #     sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
        #     ).decode()
