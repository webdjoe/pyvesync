"""Base Devices for Outlets."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyvesync.base_devices.vesyncbasedevice import DeviceState, VeSyncBaseToggleDevice
from pyvesync.const import NightlightModes, OutletFeatures
from pyvesync.models.base_models import DefaultValues
from pyvesync.models.outlet_models import RequestEnergyHistory, ResponseEnergyHistory
from pyvesync.utils.helpers import Helpers

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import OutletMap
    from pyvesync.models.outlet_models import ResponseEnergyResult
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel

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
        device (VeSyncOutlet): Device object.
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

    Note:
        Not all attributes are available on all devices. Some attributes may be None or
        not supported depending on the device type and features. The attributes are set
        based on the device features and the API response.
    """

    __slots__ = (
        'energy',
        'monthly_history',
        'nightlight_automode',
        'nightlight_brightness',
        'nightlight_status',
        'power',
        'voltage',
        'weekly_history',
        'yearly_history',
    )

    def __init__(
        self,
        device: VeSyncOutlet,
        details: ResponseDeviceDetailsModel,
        feature_map: OutletMap,
    ) -> None:
        """Initialize VeSync Switch State."""
        super().__init__(device, details, feature_map)
        self._exclude_serialization = [
            'weakly_history',
            'monthly_history',
            'yearly_history',
        ]
        self.device: VeSyncOutlet = device
        self.features: list[str] = feature_map.features
        self.active_time: int | None = 0
        self.power: float | None = None
        self.energy: float | None = None
        self.voltage: float | None = None
        self.nightlight_status: str | None = None
        self.nightlight_brightness: int | None = None
        self.nightlight_automode: str | None = None
        self.weekly_history: ResponseEnergyResult | None = None
        self.monthly_history: ResponseEnergyResult | None = None
        self.yearly_history: ResponseEnergyResult | None = None

    def annual_history_to_json(self) -> None | str:
        """Dump annual history."""
        if not self.device.supports_energy:
            logger.info('Device does not support energy monitoring.')
            return None
        if self.yearly_history is None:
            logger.info('No yearly history available, run device.get_yearly_history().')
            return None
        return self.yearly_history.to_json()

    def monthly_history_to_json(self) -> None | str:
        """Dump monthly history."""
        if not self.device.supports_energy:
            logger.info('Device does not support energy monitoring.')
            return None
        if self.monthly_history is None:
            logger.info('No monthly history available, run device.get_monthly_history().')
            return None
        return self.monthly_history.to_json()

    def weekly_history_to_json(self) -> None | str:
        """Dump weekly history."""
        if not self.device.supports_energy:
            logger.info('Device does not support energy monitoring.')
            return None
        if self.weekly_history is None:
            logger.info('No weekly history available, run device.get_weekly_history().')
            return None
        return self.weekly_history.to_json()


class VeSyncOutlet(VeSyncBaseToggleDevice):
    """Base class for Etekcity Outlets.

    State is stored in the `state` attribute of the device.
    This is only for holding state information and does not
    contain any methods for controlling the device or retrieving
    information from the API.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The VeSync manager.
        feature_map (OutletMap): The feature map for the device.

    Attributes:
        state (OutletState): The state of the outlet.
        last_response (ResponseInfo): Last response from API call.
        manager (VeSync): Manager object for API calls.
        device_name (str): Name of device.
        device_image (str): URL for device image.
        cid (str): Device ID.
        connection_type (str): Connection type of device.
        device_type (str): Type of device.
        type (str): Type of device.
        uuid (str): UUID of device, not always present.
        config_module (str): Configuration module of device.
        mac_id (str): MAC ID of device.
        current_firm_version (str): Current firmware version of device.
        device_region (str): Region of device. (US, EU, etc.)
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
    """

    def __init__(
        self, details: ResponseDeviceDetailsModel, manager: VeSync, feature_map: OutletMap
    ) -> None:
        """Initialize VeSync Outlet base class."""
        super().__init__(details, manager, feature_map)
        self.state: OutletState = OutletState(self, details, feature_map)
        self.nightlight_modes = feature_map.nightlight_modes

    def _build_energy_request(self, method: str) -> RequestEnergyHistory:
        """Build energy request post."""
        request_keys = [
            'acceptLanguage',
            'accountID',
            'appVersion',
            'phoneBrand',
            'phoneOS',
            'timeZone',
            'token',
            'traceId',
            'userCountryCode',
            'debugMode',
            'homeTimeZone',
            'uuid',
        ]
        body = Helpers.get_class_attributes(DefaultValues, request_keys)
        body.update(Helpers.get_class_attributes(self.manager, request_keys))
        body.update(Helpers.get_class_attributes(self, request_keys))
        body['method'] = method
        return RequestEnergyHistory.from_dict(body)

    async def _get_energy_history(self, history_interval: str) -> None:
        """Pull energy history from API.

        Args:
            history_interval (str): The interval for the energy history,
                options are 'getLastWeekEnergy', 'getLastMonthEnergy', 'getLastYearEnergy'

        Note:
            Builds the state.<history_interval>_history attribute.
        """
        if not self.supports_energy:
            logger.debug('Device does not support energy monitoring.')
            return
        history_intervals = [
            'getLastWeekEnergy',
            'getLastMonthEnergy',
            'getLastYearEnergy',
        ]
        if history_interval not in history_intervals:
            logger.debug('Invalid history interval: %s', history_interval)
            return
        body = self._build_energy_request(history_interval)
        headers = Helpers.req_header_bypass()
        r_bytes, _ = await self.manager.async_call_api(
            f'/cloud/v1/device/{history_interval}',
            'post',
            headers=headers,
            json_object=body.to_dict(),
        )

        r = Helpers.process_dev_response(logger, history_interval, self, r_bytes)
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

    async def set_nightlight_state(self, mode: str) -> bool:
        """Set nightlight mode.

        Available nightlight states are found in the `device.nightlight_modes` attribute.

        Args:
            mode (str): Nightlight mode to set.

        Returns:
            bool: True if nightlight mode set successfully, False otherwise.
        """
        del mode  # unused
        if not self.supports_nightlight:
            logger.debug('Device does not support nightlight.')
        else:
            logger.debug('Nightlight mode not configured for %s', self.device_name)
        return False

    async def turn_on_nightlight(self) -> bool:
        """Turn on nightlight if supported."""
        if not self.supports_nightlight:
            logger.debug('Device does not support nightlight.')
            return False
        return await self.set_nightlight_state(NightlightModes.ON)

    async def turn_off_nightlight(self) -> bool:
        """Turn off nightlight if supported."""
        if not self.supports_nightlight:
            logger.debug('Device does not support nightlight.')
            return False
        return await self.set_nightlight_state(NightlightModes.OFF)

    async def set_nightlight_auto(self) -> bool:
        """Set nightlight to auto mode."""
        if not self.supports_nightlight:
            logger.debug('Device does not support nightlight.')
            return False
        return await self.set_nightlight_state(NightlightModes.AUTO)
