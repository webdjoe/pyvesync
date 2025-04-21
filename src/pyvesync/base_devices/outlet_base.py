"""Base Devices for Outlets."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from pyvesync.const import OutletFeatures, IntFlag, StrFlag
from pyvesync.utils.helpers import Helpers
from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseToggleDevice, DeviceState
from pyvesync.models.outlet_models import RequestEnergyHistory, ResponseEnergyHistory
from pyvesync.models.base_models import DefaultValues

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import OutletMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
    from pyvesync.models.outlet_models import ResponseEnergyResult

logger = logging.getLogger(__name__)


class OutletState(DeviceState):
    """Base state class for Outlets.

    This class holds all of the state information for the outlet devices. The state
    instance is stored in the `state` attribute of the outlet device. This is only
    for holding state information and does not contain any methods for controlling
    the device or retrieving information from the API.

    Args:
        device (VeSyncOutlet): The device object.
        details (ResponseDeviceDetailsModel): The device details.
        feature_map (OutletMap): The feature map for the device.

    Attributes:
        active_time (int): Active time of device, defaults to None.
        connection_status (str): Connection status of device.
        device (VeSyncBaseDevice): Device object.
        device_status (str): Device status.
        features (dict): Features of device.
        last_update_ts (int): Last update timestamp of device, defaults to None.
        energy (float): Energy usage in kWh.
        monthly_history (ResponseEnergyResult): Monthly energy history.
        nightlight_automode (str): Nightlight automode status.
        nightlight_brightness (int): Nightlight brightness level.
        nightlight_status (str): Nightlight status.
        power (float): Power usage in Watts.
        voltage (float): Voltage in Volts.
        weekly_history (ResponseEnergyResult): Weekly energy history.
        yearly_history (ResponseEnergyResult): Yearly energy history.

    Methods:
        update_ts: Update last update timestamp.
        to_dict: Dump state to JSON.
        to_json: Dump state to JSON string.
        to_jsonb: Dump state to JSON bytes.
        as_tuple: Convert state to tuple of (name, value) tuples.
    """

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
        self._exclude_serialization = [
            "weakly_history",
            "monthly_history",
            "yearly_history",
        ]
        self.device: VeSyncOutlet = device
        self.features: list[str] = feature_map.features
        self.active_time: int = 0
        self.power: float = IntFlag.NOT_SUPPORTED
        self.energy: float = IntFlag.NOT_SUPPORTED
        self.voltage: float = IntFlag.NOT_SUPPORTED
        self.nightlight_status: str | None = StrFlag.NOT_SUPPORTED
        self.nightlight_brightness: int | None = IntFlag.NOT_SUPPORTED
        self.nightlight_automode: str | None = StrFlag.NOT_SUPPORTED
        self.weekly_history: ResponseEnergyResult | None = None
        self.monthly_history: ResponseEnergyResult | None = None
        self.yearly_history: ResponseEnergyResult | None = None

    def annual_history_to_json(self) -> None | str:
        """Dump annual history."""
        if not self.device.supports_energy:
            logger.info("Device does not support energy monitoring.")
            return None
        if self.yearly_history is None:
            logger.info("No yearly history available, run device.get_yearly_history().")
            return None
        return self.yearly_history.to_json()

    def monthly_history_to_json(self) -> None | str:
        """Dump monthly history."""
        if not self.device.supports_energy:
            logger.info("Device does not support energy monitoring.")
            return None
        if self.monthly_history is None:
            logger.info("No monthly history available, run device.get_monthly_history().")
            return None
        return self.monthly_history.to_json()

    def weekly_history_to_json(self) -> None | str:
        """Dump weekly history."""
        if not self.device.supports_energy:
            logger.info("Device does not support energy monitoring.")
            return None
        if self.weekly_history is None:
            logger.info("No weekly history available, run device.get_weekly_history().")
            return None
        return self.weekly_history.to_json()


class VeSyncOutlet(VeSyncBaseToggleDevice):
    """Base class for Etekcity Outlets.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The VeSync manager.
        feature_map (OutletMap): The feature map for the device.

    Attributes:
        state (OutletState): The state of the outlet.
        details (dict): The details of the outlet.
        energy (dict): The energy usage of the outlet.
        update_energy_ts (int): The timestamp for the last energy update.
    """

    # __metaclass__ = ABCMeta

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: OutletMap) -> None:
        """Initialize VeSync Outlet base class."""
        super().__init__(details, manager, feature_map)
        self.state: OutletState = OutletState(self, details, feature_map)
        self.nightlight_modes = feature_map.nightlight_modes

    def _build_energy_request(self, method: str) -> RequestEnergyHistory:
        """Build energy request post."""
        request_keys = ["acceptLanguage", "accountID", "appVersion", "phoneBrand",
                        "phoneOS", "timeZone", "token", "traceId", "userCountryCode",
                        "debugMode", "homeTimeZone", "uuid"]
        body = Helpers.get_class_attributes(DefaultValues, request_keys)
        body.update(Helpers.get_class_attributes(self.manager, request_keys))
        body.update(Helpers.get_class_attributes(self, request_keys))
        body['method'] = method
        return RequestEnergyHistory.from_dict(body)

    async def _get_energy_history(self, history_interval: str) -> None:
        """Internal function to pull energy history.

        Args:
            history_interval (str): The interval for the energy history,
                options are 'getLastWeekEnergy', 'getLastMonthEnergy', 'getLastYearEnergy'

        Note:
            Builds the state.<history_interval>_history attribute.
        """
        if not self.supports_energy:
            logger.debug("Device does not support energy monitoring.")
            return
        history_intervals = [
            'getLastWeekEnergy', 'getLastMonthEnergy', 'getLastYearEnergy'
            ]
        if history_interval not in history_intervals:
            logger.debug("Invalid history interval: %s", history_interval)
            return
        body = self._build_energy_request(history_interval)
        headers = Helpers.req_header_bypass()
        r_bytes, _ = await self.manager.async_call_api(
            f'/cloud/v1/device/{history_interval}',
            'post',
            headers=headers,
            json_object=body.to_dict(),
        )

        r = Helpers.process_dev_response(
            logger, history_interval, self, r_bytes
            )
        if r is None:
            return
        response = ResponseEnergyHistory.from_dict(r)
        match history_interval:
            case 'getLastWeekEnergy':
                self.state.weekly_history = response.result
            case 'getLastMonthEnergy':
                self.state.monthly_history = response.result
            case 'getLastYearEnergy':
                self.state.yearly_history = response.result

    @property
    def supports_nightlight(self) -> bool:
        """Return True if device supports nightlight.

        Returns:
            bool: True if device supports nightlight, False otherwise.
        """
        return OutletFeatures.NIGHTLIGHT in self.features

    @property
    def supports_energy(self) -> bool:
        """Return True if device supports energy.

        Returns:
            bool: True if device supports energy, False otherwise.
        """
        return OutletFeatures.ENERGY_MONITOR in self.features

    async def get_weekly_energy(self) -> None:
        """Build weekly energy history dictionary.

        The data is stored in the `device.state.weekly_history` attribute
        as a `ResponseEnergyResult` object.
        """
        await self._get_energy_history('getLastWeekEnergy')

    async def get_monthly_energy(self) -> None:
        """Build Monthly Energy History Dictionary.

        The data is stored in the `device.state.monthly_history` attribute
        as a `ResponseEnergyResult` object.
        """
        await self._get_energy_history('getLastMonthEnergy')

    async def get_yearly_energy(self) -> None:
        """Build Yearly Energy Dictionary.

        The data is stored in the `device.state.yearly_history` attribute
        as a `ResponseEnergyResult` object.
        """
        await self._get_energy_history('getLastYearEnergy')

    async def update_energy(self) -> None:
        """Build weekly, monthly and yearly dictionaries."""
        if self.supports_energy:
            await self.get_weekly_energy()
            await self.get_monthly_energy()
            await self.get_yearly_energy()
