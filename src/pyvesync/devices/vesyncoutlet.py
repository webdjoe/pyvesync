"""Etekcity Outlets."""

from __future__ import annotations

import calendar
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from typing_extensions import deprecated

from pyvesync.base_devices.outlet_base import VeSyncOutlet
from pyvesync.const import (
    ENERGY_HISTORY_OFFSET_WHOGPLUG,
    STATUS_OK,
    ConnectionStatus,
    DeviceStatus,
    EnergyIntervals,
)
from pyvesync.models.base_models import DefaultValues, RequestHeaders
from pyvesync.models.bypass_models import (
    BypassV2InnerResult,
    RequestBypassV1,
    TimerModels,
)
from pyvesync.models.outlet_models import (
    Request15ADetails,
    Request15ANightlight,
    Request15AStatus,
    RequestESW03Status,
    RequestOutdoorStatus,
    RequestWHOGYearlyEnergy,
    Response7AOutlet,
    Response15ADetails,
    ResponseBSDGO1OutletResult,
    ResponseEnergyResult,
    ResponseESW03Details,
    ResponseOutdoorDetails,
    ResponseWHOGResult,
    ResultESW10Details,
    Timer7AItem,
)
from pyvesync.utils.device_mixins import (
    BypassV1Mixin,
    BypassV2Mixin,
    process_bypassv1_result,
    process_bypassv2_result,
)
from pyvesync.utils.helpers import Helpers, Timer
from pyvesync.utils.logs import LibraryLogger

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import OutletMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel

logger = logging.getLogger(__name__)


class VeSyncOutlet7A(VeSyncOutlet):
    """Etekcity 7A Round Outlet Class.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The VeSync manager.
        feature_map (OutletMap): The feature map for the device.

    Attributes:
        state (OutletState): The state of the outlet.
        last_response (ResponseInfo): Last response from API call.
        device_status (str): Device status.
        connection_status (str): Connection status.
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

    __slots__ = ()

    def __init__(
        self, details: ResponseDeviceDetailsModel, manager: VeSync, feature_map: OutletMap
    ) -> None:
        """Initialize Etekcity 7A round outlet class."""
        super().__init__(details, manager, feature_map)

    def _build_headers(self) -> dict:
        """Build 7A Outlet Request Headers."""
        headers = RequestHeaders.copy()
        headers.update(
            {
                'tz': self.manager.time_zone,
                'tk': self.manager.token,
                'accountid': self.manager.account_id,
            }
        )
        return headers

    async def get_details(self) -> None:
        r_dict, _ = await self.manager.async_call_api(
            '/v1/device/' + self.cid + '/detail',
            'get',
            headers=self._build_headers(),
        )

        if not isinstance(r_dict, dict):
            LibraryLogger.error_device_response_content(
                logger,
                self,
                'get_details',
                'Response is not valid JSON',
            )
            return

        if 'error' in r_dict:
            _ = Helpers.process_dev_response(logger, 'get_details', self, r_dict)
            return
        self.state.update_ts()
        resp_model = Response7AOutlet.from_dict(r_dict)
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = resp_model.deviceStatus
        self.state.active_time = resp_model.activeTime
        self.state.energy = resp_model.energy
        self.state.power = self.parse_energy_detail(resp_model.power)
        self.state.voltage = self.parse_energy_detail(resp_model.voltage)

    @staticmethod
    def parse_energy_detail(energy: str | float) -> float:
        """Parse energy details to be compatible with new and old firmware."""
        try:
            if isinstance(energy, str) and ':' in energy:
                power = round(float(Helpers.calculate_hex(energy)), 2)
            else:
                power = float(energy)
        except ValueError:
            logger.warning('Error parsing power response - %s', energy)
            power = 0
        return power

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_str = DeviceStatus.ON if toggle else DeviceStatus.OFF
        r_dict, status_code = await self.manager.async_call_api(
            f'/v1/wifi-switch-1.3/{self.cid}/status/{toggle_str}',
            'put',
            headers=Helpers.req_legacy_headers(self.manager),
        )

        if status_code != STATUS_OK:
            LibraryLogger.error_device_response_content(
                logger,
                self,
                'toggle_switch',
                'Response code is not 200',
            )
            return False

        if isinstance(r_dict, dict) and 'error' in r_dict:
            _ = Helpers.process_dev_response(logger, 'get_details', self, r_dict)
            return False

        self.state.update_ts()
        self.state.device_status = toggle_str
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def get_timer(self) -> None:
        r_dict, status_code = await self.manager.async_call_api(
            f'/v2/device/{self.cid}/timer',
            'get',
            headers=Helpers.req_legacy_headers(self.manager),
        )
        if not r_dict or status_code != STATUS_OK:
            logger.debug('No timer set.')
            self.state.timer = None
            return
        if isinstance(r_dict, list) and len(r_dict) > 0:
            timer_model = Helpers.model_maker(logger, Timer7AItem, 'get_timer', r_dict[0])
            if timer_model is None:
                self.state.timer = None
                return
            self.state.timer = Timer(
                timer_duration=int(timer_model.counterTimer),
                id=int(timer_model.timerID),
                action=timer_model.action,
            )
            if timer_model.timerStatus == 'off':
                self.state.timer.pause()
            return
        self.state.timer = None

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        if action is None:
            action = (
                DeviceStatus.ON
                if self.state.device_status == DeviceStatus.OFF
                else DeviceStatus.OFF
            )
        if not isinstance(action, str) or action not in [
            DeviceStatus.ON,
            DeviceStatus.OFF,
        ]:
            logger.error('Invalid action for timer - %s', action)
            return False
        update_dict = {
            'action': action,
            'counterTimer': duration,
            'timerStatus': 'start',
            'conflictAwayIds': [],
            'conflictScheduleIds': [],
            'conflictTimerIds': [],
        }
        r_dict, status_code = await self.manager.async_call_api(
            f'/v2/device/{self.cid}/timer',
            'post',
            headers=Helpers.req_legacy_headers(self.manager),
            json_object=update_dict,
        )
        if status_code != STATUS_OK or not isinstance(r_dict, dict):
            logger.warning('Failed to set timer for %s.', self.device_name)
            return False

        if 'error' in r_dict:
            logger.warning('Error in response: %s', r_dict['error'])
            return False

        result_model = Helpers.model_maker(
            logger, TimerModels.ResultV1SetTimer, 'set_timer', r_dict, self
        )
        if result_model is None:
            logger.warning('Failed to set timer.')
            return False
        if result_model.timerID == '':
            logger.warning('Unable to set timer.')
            if result_model.conflictTimerIds:
                logger.warning(
                    'Conflicting timer IDs - %s', result_model.conflictTimerIds
                )
            return False
        self.state.timer = Timer(duration, action, int(result_model.timerID))
        return True

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            logger.debug('No timer set, nothing to clear, run get_timer().')
            return False
        _, status_code = await self.manager.async_call_api(
            f'/v2/device/{self.cid}/timer/{self.state.timer.id}',
            'delete',
            headers=Helpers.req_legacy_headers(self.manager),
        )
        if status_code != STATUS_OK:
            return False
        self.state.timer = None
        return True


class VeSyncOutlet10A(BypassV1Mixin, VeSyncOutlet):
    """Etekcity 10A ESW01 and ESW03 Round Outlets.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The VeSync manager.
        feature_map (OutletMap): The feature map for the device.

    Attributes:
        state (OutletState): The state of the outlet.
        last_response (ResponseInfo): Last response from API call.
        device_status (str): Device status.
        connection_status (str): Connection status.
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

    __slots__ = ()

    def __init__(
        self, details: ResponseDeviceDetailsModel, manager: VeSync, feature_map: OutletMap
    ) -> None:
        """Initialize 10A outlet class."""
        super().__init__(details, manager, feature_map)

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv1_api(
            RequestBypassV1, method='deviceDetail', endpoint='deviceDetail'
        )
        r = process_bypassv1_result(
            self, logger, 'get_details', r_dict, ResponseESW03Details
        )
        if r is None:
            return

        self.state.device_status = DeviceStatus(r.deviceStatus)
        self.state.connection_status = ConnectionStatus(r.connectionStatus)
        self.state.energy = r.energy or 0
        self.state.power = r.power or 0
        self.state.voltage = r.voltage or 0

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_str = DeviceStatus.ON if toggle else DeviceStatus.OFF
        update_dict = {'status': toggle_str.value}
        response = await self.call_bypassv1_api(
            RequestESW03Status,
            update_dict=update_dict,
            method='deviceStatus',
            endpoint='deviceStatus',
        )
        r_dict = Helpers.process_dev_response(logger, 'toggle_switch', self, response)
        if r_dict is None:
            return False

        self.state.device_status = toggle_str
        self.state.connection_status = ConnectionStatus.ONLINE
        return True


class VeSyncOutlet15A(BypassV1Mixin, VeSyncOutlet):
    """Class for Etekcity 15A Rectangular Outlets.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The VeSync manager.
        feature_map (OutletMap): The feature map for the device.

    Attributes:
        state (OutletState): The state of the outlet.
        last_response (ResponseInfo): Last response from API call.
        device_status (str): Device status.
        connection_status (str): Connection status.
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

    __slots__ = ()

    def __init__(
        self, details: ResponseDeviceDetailsModel, manager: VeSync, feature_map: OutletMap
    ) -> None:
        """Initialize 15A rectangular outlets."""
        super().__init__(details, manager, feature_map)

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv1_api(
            Request15ADetails, method='deviceDetail', endpoint='deviceDetail'
        )

        r = Helpers.process_dev_response(logger, 'get_details', self, r_dict)
        if r is None:
            return

        resp_model = Response15ADetails.from_dict(r)
        result = resp_model.result
        self.state.device_status = result.deviceStatus
        self.state.connection_status = result.connectionStatus
        self.state.nightlight_status = result.nightLightStatus
        self.state.nightlight_brightness = result.nightLightBrightness
        self.state.nightlight_automode = result.nightLightAutoMode
        self.state.active_time = result.activeTime
        self.state.power = result.power or 0
        self.state.voltage = result.voltage or 0
        self.state.energy = result.energy or 0

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_str = DeviceStatus.ON if toggle else DeviceStatus.OFF
        r_dict = await self.call_bypassv1_api(
            Request15AStatus,
            update_dict={'status': toggle_str},
            method='deviceStatus',
            endpoint='deviceStatus',
        )
        response = Helpers.process_dev_response(logger, 'toggle_switch', self, r_dict)
        if response is None:
            return False

        self.state.device_status = toggle_str
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_nightlight_state(self, mode: str) -> bool:
        """Set nightlight state for 15A Outlets."""
        if mode.lower() not in self.nightlight_modes:
            logger.error('Invalid nightlight mode - %s', mode)
            return False
        mode = mode.lower()
        r_dict = await self.call_bypassv1_api(
            Request15ANightlight,
            update_dict={'mode': mode},
            method='outletNightLightCtl',
            endpoint='outletNightLightCtl',
        )

        response = Helpers.process_dev_response(
            logger, 'set_nightlight_state', self, r_dict
        )
        if response is None:
            return False

        self.state.nightlight_status = mode
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def get_timer(self) -> None:
        method = 'getTimers'
        endpoint = f'/timer/{method}'
        r_dict = await self.call_bypassv1_api(
            Request15ADetails, method=method, endpoint=endpoint
        )
        result_model = process_bypassv1_result(
            self, logger, 'get_timer', r_dict, TimerModels.ResultV1GetTimer
        )
        if result_model is None:
            return
        timers = result_model.timers
        if not isinstance(timers, list) or len(timers) == 0:
            self.state.timer = None
            return
        timer = timers[0]
        if not isinstance(timer, TimerModels.TimerItemV1):
            logger.warning('Invalid timer model - %s', timer)
            return
        self.state.timer = Timer(
            timer_duration=int(timer.counterTimer),
            id=int(timer.timerID),
            action=timer.action,
        )

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        if action is None:
            action = (
                DeviceStatus.ON
                if self.state.device_status == DeviceStatus.OFF
                else DeviceStatus.OFF
            )
        if not isinstance(action, str) or action not in [
            DeviceStatus.ON,
            DeviceStatus.OFF,
        ]:
            logger.error('Invalid action for timer - %s', action)
            return False
        update_dict = {
            'action': action,
            'counterTime': str(duration),
        }
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1SetTime,
            update_dict=update_dict,
            method='addTimer',
            endpoint='timer/addTimer',
        )
        result_model = process_bypassv1_result(
            self, logger, 'set_timer', r_dict, TimerModels.ResultV1SetTimer
        )
        if result_model is None:
            return False
        self.state.timer = Timer(duration, action, int(result_model.timerID))
        return True

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            logger.debug('No timer set, nothing to clear, run get_timer().')
            return False
        if self.state.timer.time_remaining == 0:
            logger.debug('Timer already ended.')
            self.state.timer = None
            return True
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1ClearTimer,
            {'timerId': str(self.state.timer.id)},
            method='deleteTimer',
            endpoint='timer/deleteTimer',
        )
        r_dict = Helpers.process_dev_response(logger, 'clear_timer', self, r_dict)
        if r_dict is None:
            if (
                self.last_response is not None
                and self.last_response.name == 'TIMER_NOT_EXISTS'
            ):
                self.state.timer = None
            return False
        self.state.timer = None
        return True


class VeSyncOutdoorPlug(BypassV1Mixin, VeSyncOutlet):
    """Class to hold Etekcity outdoor outlets.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The VeSync manager.
        feature_map (OutletMap): The feature map for the device.

    Attributes:
        state (OutletState): The state of the outlet.
        last_response (ResponseInfo): Last response from API call.
        device_status (str): Device status.
        connection_status (str): Connection status.
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

    __slots__ = ()

    def __init__(
        self, details: ResponseDeviceDetailsModel, manager: VeSync, feature_map: OutletMap
    ) -> None:
        """Initialize Etekcity Outdoor Plug class."""
        super().__init__(details, manager, feature_map)

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv1_api(
            Request15ADetails, method='deviceDetail', endpoint='deviceDetail'
        )
        r = Helpers.process_dev_response(logger, 'get_details', self, r_dict)
        if r is None:
            return

        resp_model = ResponseOutdoorDetails.from_dict(r)
        self.state.connection_status = resp_model.result.connectionStatus
        self.state.energy = resp_model.result.energy
        self.state.power = resp_model.result.power
        self.state.voltage = resp_model.result.voltage
        self.state.active_time = resp_model.result.activeTime
        for outlet in resp_model.result.subDevices:
            if not isinstance(self.sub_device_no, float):
                continue
            if int(self.sub_device_no) == int(outlet.subDeviceNo):
                self.state.device_status = outlet.subDeviceStatus

    @deprecated('Use toggle_switch(toggle: bool | None) instead')
    async def toggle(self, status: str) -> bool:
        """Deprecated - use toggle_switch()."""
        toggle = status != DeviceStatus.ON
        return await self.toggle_switch(toggle)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        status = DeviceStatus.ON if toggle else DeviceStatus.OFF

        r_dict = await self.call_bypassv1_api(
            RequestOutdoorStatus,
            update_dict={'switchNo': self.sub_device_no, 'status': status},
            method='deviceStatus',
            endpoint='deviceStatus',
        )

        response = Helpers.process_dev_response(logger, 'toggle', self, r_dict)
        if response is None:
            return False

        self.state.device_status = status
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def get_timer(self) -> None:
        method = 'getTimers'
        endpoint = f'/timer/{method}'
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1GetTimer,
            {'switchNo': self.sub_device_no},
            method=method,
            endpoint=endpoint,
        )
        result_model = process_bypassv1_result(
            self, logger, 'get_timer', r_dict, TimerModels.ResultV1GetTimer
        )
        if result_model is None:
            return
        timers = result_model.timers
        if not isinstance(timers, list) or len(timers) == 0:
            self.state.timer = None
            return
        if len(timers) > 1:
            logger.debug(
                (
                    (
                        'Multiple timers found - %s, this method '
                        'will only return the most recent timer created.'
                    ),
                ),
                timers,
            )
        timer = timers[0]
        if not isinstance(timer, TimerModels.TimerItemV1):
            logger.warning('Invalid timer model - %s', timer)
            return
        self.state.timer = Timer(
            timer_duration=int(timer.counterTimer),
            id=int(timer.timerID),
            action=timer.action,
        )

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        if action is None:
            action = (
                DeviceStatus.ON
                if self.state.device_status == DeviceStatus.OFF
                else DeviceStatus.OFF
            )
        if not isinstance(action, str) or action not in [
            DeviceStatus.ON,
            DeviceStatus.OFF,
        ]:
            logger.error('Invalid action for timer - %s', action)
            return False
        update_dict = {
            'action': action,
            'counterTime': str(duration),
            'switchNo': self.sub_device_no,
        }
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1SetTime,
            update_dict=update_dict,
            method='addTimer',
            endpoint='timer/addTimer',
        )
        result_model = process_bypassv1_result(
            self, logger, 'set_timer', r_dict, TimerModels.ResultV1SetTimer
        )
        if result_model is None:
            return False
        self.state.timer = Timer(duration, action, int(result_model.timerID))
        return True

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            logger.debug('No timer set, nothing to clear, run get_timer().')
            return False
        if self.state.timer.time_remaining == 0:
            logger.debug('Timer already ended.')
            self.state.timer = None
            return True
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1ClearTimer,
            {'timerId': str(self.state.timer.id)},
            method='deleteTimer',
            endpoint='timer/deleteTimer',
        )
        r_dict = Helpers.process_dev_response(logger, 'clear_timer', self, r_dict)
        if r_dict is None:
            return False
        self.state.timer = None
        return True


class VeSyncOutletWHOGPlug(BypassV2Mixin, VeSyncOutlet):
    """VeSync WHOG smart plug.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The VeSync manager.
        feature_map (OutletMap): The feature map for the device.

    Attributes:
        state (OutletState): The state of the outlet.
        last_response (ResponseInfo): Last response from API call.
        device_status (str): Device status.
        connection_status (str): Connection status.
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

    __slots__ = ()

    def __init__(
        self, details: ResponseDeviceDetailsModel, manager: VeSync, feature_map: OutletMap
    ) -> None:
        """Initialize BSDGO1 smart plug class."""
        super().__init__(details, manager, feature_map)

    async def _bypass_v1_api_helper(
        self,
        request_model: type[RequestBypassV1],
        update_dict: dict | None = None,
        method: str = 'bypass',
    ) -> dict | None:
        """Send ByPass V1 API request.

        This uses the `_build_request` method to send API requests to the Bypass V1 API.

        Args:
            request_model (type[RequestBypassV1]): The request model to use.
            update_dict (dict): Additional keys to add on.
            method (str): The method to use in the outer body.

        Returns:
            bytes: The response from the API request.
        """
        keys = BypassV1Mixin.request_keys
        body = Helpers.get_class_attributes(DefaultValues, keys)
        body.update(Helpers.get_class_attributes(self.manager, keys))
        body.update(Helpers.get_class_attributes(self, keys))
        body['method'] = method
        body.update(update_dict or {})
        model_instance = request_model.from_dict(body)
        url_path = '/cloud/v1/outlet/getELECConsumePerMonthLastYear'
        resp_dict, _ = await self.manager.async_call_api(
            url_path, 'post', model_instance, Helpers.req_header_bypass()
        )

        return resp_dict

    def _set_state(self, resp_model: BypassV2InnerResult) -> None:
        """Set the state of the WHOGPLUG outlet from the response model."""
        if not isinstance(resp_model, ResponseWHOGResult):
            logger.debug('Invalid response model for _set_state: %s', type(resp_model))
            return
        self.state.device_status = DeviceStatus.from_int(resp_model.enabled)
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.voltage = resp_model.voltage
        self.state.power = resp_model.power
        self.state.energy = resp_model.energy
        self.state.current = resp_model.current
        self.state.voltageUpperThreshold = resp_model.highestVoltage
        self.state.protectionStatus = 'on' if resp_model.voltagePtStatus else 'off'

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv2_api('getOutletStatus')

        resp_model = process_bypassv2_result(
            self, logger, 'get_details', r_dict, ResponseWHOGResult
        )
        if resp_model is None:
            logger.debug('Error getting %s details', self.device_name)
            self.state.connection_status = ConnectionStatus.OFFLINE
            return

        self._set_state(resp_model)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_int = int(toggle)
        r_dict = await self.call_bypassv2_api(
            'setProperty',
            data={'powerSwitch_1': toggle_int},
            payload_update={'subDeviceNo': 0},
        )
        r = Helpers.process_dev_response(logger, 'toggle_switch', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.ON if toggle else DeviceStatus.OFF
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def _get_energy_history(self, history_interval: str | EnergyIntervals) -> None:
        """Get energy history for BSDGO1 outlet."""
        if history_interval not in self._energy_intervals:
            logger.error('Invalid energy history interval - %s', history_interval)
            return
        if not isinstance(history_interval, EnergyIntervals):
            history_interval = EnergyIntervals(history_interval)

        if history_interval == EnergyIntervals.YEAR:
            await self.get_yearly_energy()

        offset = ENERGY_HISTORY_OFFSET_WHOGPLUG[history_interval]
        current_ts = int(datetime.now().timestamp())
        start_ts = current_ts - offset
        payload_data = {
            'fromDay': start_ts,
            'toDay': current_ts,
        }
        r_dict = await self.call_bypassv2_api('getEnergyHistory', data=payload_data)
        result_model = process_bypassv2_result(
            self, logger, '_get_energy_history', r_dict, ResponseEnergyResult
        )
        if result_model is None:
            return
        match history_interval:
            case EnergyIntervals.WEEK:
                self.state.weekly_history = result_model
            case EnergyIntervals.MONTH:
                self.state.monthly_history = result_model
        logger.debug('Energy history for %s updated', self.device_name)

    async def get_yearly_energy(self) -> None:
        """Get yearly energy for WHOG outlet."""
        r_dict = await self._bypass_v1_api_helper(
            RequestWHOGYearlyEnergy, method='getELECConsumePerMonthLastYear'
        )
        r_dict = Helpers.process_dev_response(logger, 'get_yearly_energy', self, r_dict)
        if r_dict is None:
            return
        if not isinstance(r_dict.get('result', {}).get('ELECConsumeList'), list):
            logger.debug('Error in last year energy response for %s', self.device_name)
            return

        self.state.yearly_history = ResponseEnergyResult.from_dict(
            self._process_yearly_model(r_dict['result'])
        )
        logger.debug('Last year energy for %s updated', self.device_name)

    def _process_yearly_model(
        self, result_dict: dict[str, list[dict[str, str]]]
    ) -> dict[str, list[dict]]:
        """Process yearly WHOG energy model from response dict."""

        def end_of_month_utc_timestamp(year: int, month: int) -> int:
            # Last day number in the month
            last_day = calendar.monthrange(year, month)[1]
            # 23:59:59 on the last day, in UTC
            dt = datetime(year, month, last_day, 23, 59, 59, tzinfo=UTC)
            return int(dt.timestamp())

        out: dict[str, list[dict]] = {'energyInfos': []}
        for item in result_dict.get('ELECConsumeList', []):
            ym = item['month']
            year, month = map(int, ym.split('-'))
            ts = end_of_month_utc_timestamp(year, month)
            out['energyInfos'].append(
                {
                    'timestamp': ts,
                    'energyKWH': item['ELECConsume'],
                }
            )
        return out


class VeSyncBSDOGPlug(VeSyncOutletWHOGPlug):
    """VeSync BSDOG01/WYZYOG smart plugs.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The VeSync manager.
        feature_map (OutletMap): The feature map for the device.

    Attributes:
        state (OutletState): The state of the outlet.
        last_response (ResponseInfo): Last response from API call.
        device_status (str): Device status.
        connection_status (str): Connection status.
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

    __slots__ = ()

    def __init__(
        self, details: ResponseDeviceDetailsModel, manager: VeSync, feature_map: OutletMap
    ) -> None:
        """Initialize BSDOG smart plug class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, resp_model: BypassV2InnerResult) -> None:
        """Set the state of the BSDOG outlet from the response model."""
        if not isinstance(resp_model, ResponseBSDGO1OutletResult):
            logger.debug('Invalid response model for _set_state: %s', type(resp_model))
            return
        self.state.device_status = DeviceStatus.from_int(resp_model.powerSwitch_1)
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.voltage = resp_model.realTimeVoltage
        self.state.power = resp_model.realTimePower
        self.state.energy = resp_model.electricalEnergy
        self.state.voltageUpperThreshold = resp_model.voltageUpperThreshold
        self.state.protectionStatus = resp_model.protectionStatus
        self.state.currentUpperThreshold = resp_model.currentUpperThreshold

    async def get_details(self) -> None:
        payload_data = {
            'properties': [
                'powerSwitch_1',
                'realTimeVoltage',
                'realTimePower',
                'electricalEnergy',
                'protectionStatus',
                'voltageUpperThreshold',
                'currentUpperThreshold',
                'scheduleNum',
            ]
        }

        r_dict = await self.call_bypassv2_api('getProperty', data=payload_data)

        resp_model = process_bypassv2_result(
            self, logger, 'get_details', r_dict, ResponseBSDGO1OutletResult
        )
        if resp_model is None:
            logger.debug('Error getting %s details', self.device_name)
            self.state.connection_status = ConnectionStatus.OFFLINE
            return

        self._set_state(resp_model)


class VeSyncESW10USA(BypassV2Mixin, VeSyncOutlet):
    """VeSync ESW10 USA outlet.

    Note that this device does not support energy monitoring.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The VeSync manager.
        feature_map (OutletMap): The feature map for the device.

    Attributes:
        state (OutletState): The state of the outlet.
        last_response (ResponseInfo): Last response from API call.
        device_status (str): Device status.
        connection_status (str): Connection status.
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

    __slots__ = ()

    def __init__(
        self, details: ResponseDeviceDetailsModel, manager: VeSync, feature_map: OutletMap
    ) -> None:
        """Initialize ESW10 USA outlet."""
        super().__init__(details, manager, feature_map)

    async def get_details(self) -> None:
        payload_data = {
            'id': 0,
        }
        payload_method = 'getSwitch'
        r_dict = await self.call_bypassv2_api(payload_method, payload_data)
        result = process_bypassv2_result(
            self, logger, 'get_details', r_dict, ResultESW10Details
        )
        if not isinstance(result, dict) or not isinstance(result.get('enabled'), bool):
            logger.warning('Error getting %s details', self.device_name)
            self.state.connection_status = ConnectionStatus.OFFLINE
            return
        self.state.device_status = DeviceStatus.from_bool(result.enabled)
        self.state.connection_status = ConnectionStatus.ONLINE

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        payload_data = {
            'id': 0,
            'enabled': toggle,
        }
        payload_method = 'setSwitch'
        r_dict = await self.call_bypassv2_api(payload_method, payload_data)
        result = Helpers.process_dev_response(logger, 'toggle_switch', self, r_dict)
        if not isinstance(result, dict):
            logger.warning('Error toggling %s switch', self.device_name)
            return False
        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def get_timer(self) -> Timer | None:
        r_dict = await self.call_bypassv2_api('getTimer')
        result_model = process_bypassv2_result(
            self, logger, 'get_timer', r_dict, TimerModels.ResultV2GetTimer
        )
        if result_model is None:
            return None
        timers = result_model.timers
        if not timers:
            self.state.timer = None
            return None
        if len(timers) > 1:
            logger.debug(
                (
                    'Multiple timers found - %s, this method '
                    'will only return the most recent timer created.'
                ),
                timers,
            )
        timer = timers[0]
        self.state.timer = Timer(
            timer_duration=int(timer.remain),
            id=int(timer.id),
            action=timer.action,
        )
        return self.state.timer

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        if action is None:
            action = (
                DeviceStatus.ON
                if self.state.device_status == DeviceStatus.OFF
                else DeviceStatus.OFF
            )
        if action not in [DeviceStatus.ON, DeviceStatus.OFF]:
            logger.error('Invalid action for timer - %s', action)
            return False
        payload_data = {'action': action, 'total': duration}
        r_dict = await self.call_bypassv2_api(
            payload_method='addTimer',
            data=payload_data,
        )
        result_model = process_bypassv2_result(
            self, logger, 'set_timer', r_dict, TimerModels.ResultV2SetTimer
        )
        if result_model is None:
            return False
        if result_model.id is None:
            logger.warning('Unable to set timer.')
            return False
        self.state.timer = Timer(duration, action, int(result_model.id))
        return True

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            logger.debug('No timer set, nothing to clear, run get_timer().')
            return False
        if self.state.timer.time_remaining == 0:
            logger.debug('Timer already ended.')
            self.state.timer = None
            return True
        r_dict = await self.call_bypassv2_api(
            payload_method='delTimer', data={'id': self.state.timer.id}
        )
        r_dict = Helpers.process_dev_response(logger, 'clear_timer', self, r_dict)
        if r_dict is None:
            return False
        self.state.timer = None
        return True
