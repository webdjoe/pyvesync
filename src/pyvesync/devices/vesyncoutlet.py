"""Etekcity Outlets."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from deprecated import deprecated

from pyvesync.utils.helpers import Helpers, Timer
from pyvesync.utils.logs import LibraryLogger

from pyvesync.const import DeviceStatus, ConnectionStatus, NightlightModes
from pyvesync.base_devices.outlet_base import VeSyncOutlet
from pyvesync.models.base_models import RequestHeaders, DefaultValues
from pyvesync.utils.device_mixins import (
    BypassV1Mixin,
    process_bypassv1_result,
    BypassV2Mixin,
    process_bypassv2_results,
)
from pyvesync.models.outlet_models import Response7AOutlet
from pyvesync.models.bypass_models import TimerModels
from pyvesync.models.outlet_models import (
    Response10ADetails,
    Request15ADetails,
    Request15ANightlight,
    Response15ADetails,
    ResponseOutdoorDetails,
    ResponseBSDGO1OutletResult,
    Request15AStatus,
    RequestOutdoorStatus,
    Timer7AItem,
    )

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
    from pyvesync.device_map import OutletMap

logger = logging.getLogger(__name__)

outlet_config = {
    'wifi-switch-1.3': {
        'module': 'VeSyncOutlet7A'},
    'ESW03-USA': {
        'module': 'VeSyncOutlet10A'},
    'ESW01-EU': {
        'module': 'VeSyncOutlet10A'},
    'ESW15-USA': {
        'module': 'VeSyncOutlet15A'},
    'ESO15-TB': {
        'module': 'VeSyncOutdoorPlug'},
    'BSDOG01': {
        'module': 'VeSyncOutletBSDGO1'},
}

outlet_modules = {k: v['module'] for k, v in outlet_config.items()}

__all__ = [*outlet_modules.values(), 'outlet_modules']  # noqa: PLE0604


class VeSyncOutlet7A(VeSyncOutlet):
    """Etekcity 7A Round Outlet Class."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: OutletMap) -> None:
        """Initialize Etekcity 7A round outlet class."""
        super().__init__(details, manager, feature_map)

    def _build_headers(self) -> dict:
        """Build 7A Outlet Request Headers."""
        headers = RequestHeaders.copy()
        headers.update({
            "tz": self.manager.time_zone,
            'tk': self.manager.token,
            'accountid': self.manager.account_id,
        })
        return headers

    async def get_details(self) -> None:
        r_dict, _ = await self.manager.async_call_api(
            '/v1/device/' + self.cid + '/detail',
            'get',
            headers=self._build_headers(),
        )

        if not isinstance(r_dict, dict):
            LibraryLogger.log_device_api_response_error(
                logger, self.device_name, self.device_type,
                'get_details', "Response is not valid JSON"
            )
            return

        if 'error' in r_dict:
            _ = Helpers.process_dev_response(logger, "get_details", self, r_dict)
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
            logger.debug('Error parsing power response - %s', energy)
            power = 0
        return power

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_str = DeviceStatus.ON if toggle else DeviceStatus.OFF
        r_dict, status_code = await self.manager.async_call_api(
            f'/v1/wifi-switch-1.3/{self.cid}/status/{toggle_str}',
            'put',
            headers=Helpers.req_headers(self.manager),
        )

        if status_code != 200:
            LibraryLogger.log_device_api_response_error(
                logger, self.device_name, self.device_type,
                'toggle_switch', "Response code is not 200"
            )

        if isinstance(r_dict, dict) and 'error' in r_dict:
            _ = Helpers.process_dev_response(logger, "get_details", self, r_dict)
            return False

        self.state.update_ts()
        self.state.device_status = toggle_str
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def get_timer(self) -> None:
        r_dict, status_code = await self.manager.async_call_api(
            f"/v2/device/{self.cid}/timer",
            "get",
            headers=Helpers.req_headers(self.manager),
        )
        if not r_dict or status_code != 200:
            logger.debug("No timer set.")
            self.state.timer = None
            return
        if isinstance(r_dict, list) and len(r_dict) > 0:
            timer = r_dict[0]
            timer_model = Timer7AItem.from_dict(timer)
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
        if action not in [DeviceStatus.ON, DeviceStatus.OFF]:
            logger.error("Invalid action for timer - %s", action)
            return False
        update_dict = {
            'action': action,
            'counterTimer': duration,
            "timerStatus": "start",
            'conflictAwayIds': [],
            'conflictScheduleIds': [],
            'conflictTimerIds': [],
        }
        r_dict, status_code = await self.manager.async_call_api(
            f"/v2/device/{self.cid}/timer",
            "post",
            headers=Helpers.req_headers(self.manager),
            json_object=update_dict,
        )
        if status_code != 200:
            logger.debug("Failed to set timer.")
            return False
        # r = Helpers.process_dev_response(logger, "set_timer", self, r_dict)

        if not isinstance(r_dict, dict):
            return False

        if 'error' in r_dict:
            logger.debug("Error in response: %s", r_dict['error'])
            return False
        result_model = TimerModels.ResultV1SetTimer.from_dict(r_dict)
        if result_model.timerID == '':
            logger.debug("Unable to set timer.")
            if result_model.conflictTimerIds:
                logger.debug("Conflicting timer IDs - %s", result_model.conflictTimerIds)
            return False
        self.state.timer = Timer(duration, action, int(result_model.timerID))
        return True

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            logger.debug("No timer set, nothing to clear, run get_timer().")
            return False
        _, status_code = await self.manager.async_call_api(
            f"/v2/device/{self.cid}/timer/{self.state.timer.id}",
            "delete",
            headers=Helpers.req_headers(self.manager),
        )
        if status_code != 200:
            return False
        self.state.timer = None
        return True


class VeSyncOutlet10A(VeSyncOutlet):
    """Etekcity 10A Round Outlets."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: OutletMap) -> None:
        """Initialize 10A outlet class."""
        super().__init__(details, manager, feature_map)
        self.request_keys = [
            "acceptLanguage",
            "appVersion",
            "accountId",
            "mobileId",
            "phoneBrand",
            "phoneOS",
            "timeZone",
            "token",
            "traceId",
            "uuid",
        ]

    def _build_headers(self) -> dict:
        """Build auth headers for 10A Outlet."""
        headers = RequestHeaders.copy()
        headers.update({
            "tz": self.manager.time_zone,
            'tk': self.manager.token,
            'accountid': self.manager.account_id,
        })
        return headers

    def _build_detail_request(self, method: str) -> dict:
        """Build 10A Outlet Request."""
        body = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        body.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        body.update(Helpers.get_class_attributes(self, self.request_keys))
        body['method'] = method
        return body

    def _build_status_request(self, status: str) -> dict:
        """Build 10A Outlet Request to set status."""
        status_keys = ['accountID', 'token', 'timeZone', 'uuid']
        body = Helpers.get_class_attributes(self.manager, status_keys)
        body.update(Helpers.get_class_attributes(self, status_keys))
        body['status'] = status
        return body

    async def get_details(self) -> None:
        body = self._build_detail_request('devicedetail')

        r_dict, _ = await self.manager.async_call_api(
            '/10a/v1/device/devicedetail',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        r = Helpers.process_dev_response(logger, "get_details", self, r_dict)
        if r is None:
            return

        resp_model = Response10ADetails.from_dict(r)

        self.state.device_status = resp_model.deviceStatus or "off"
        self.state.connection_status = resp_model.connectionStatus or "offline"
        self.state.energy = resp_model.energy or 0
        self.state.power = resp_model.power or 0
        self.state.voltage = resp_model.voltage or 0

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_str = DeviceStatus.ON if toggle else DeviceStatus.OFF
        body = self._build_status_request(toggle_str)
        headers = self._build_headers()

        r_dict, _ = await self.manager.async_call_api(
            '/10a/v1/device/devicestatus',
            'put',
            headers=headers,
            json_object=body,
        )
        response = Helpers.process_dev_response(logger, "toggle_switch", self, r_dict)
        if response is None:
            return False

        self.state.device_status = toggle_str
        self.state.connection_status = ConnectionStatus.ONLINE
        return True


class VeSyncOutlet15A(BypassV1Mixin, VeSyncOutlet):
    """Class for Etekcity 15A Rectangular Outlets."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: OutletMap) -> None:
        """Initialize 15A rectangular outlets."""
        super().__init__(details, manager, feature_map)

    async def get_details(self) -> None:

        r_dict = await self.call_bypassv1_api(
            Request15ADetails,
            method='deviceDetail',
            endpoint='deviceDetail'
        )

        r = Helpers.process_dev_response(logger, "get_details", self, r_dict)
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
            endpoint='deviceStatus'
        )
        response = Helpers.process_dev_response(logger, "toggle_switch", self, r_dict)
        if response is None:
            return False

        self.state.device_status = toggle_str
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_nightlight_state(self, mode: str) -> bool:
        """Set nightlight state for 15A Outlets."""
        if mode.lower() not in self.nightlight_modes:
            logger.error("Invalid nightlight mode - %s", mode)
            return False
        mode = mode.lower()
        r_dict = await self.call_bypassv1_api(
            Request15ANightlight,
            update_dict={'mode': mode},
            method='outletNightLightCtl',
            endpoint='outletNightLightCtl'
        )

        response = Helpers.process_dev_response(
            logger, "set_nightlight_state", self, r_dict
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
            Request15ADetails,
            method=method,
            endpoint=endpoint
        )

        r = process_bypassv1_result(self, logger, "get_timer", r_dict)
        if r is None:
            return
        result_model = TimerModels.ResultV1GetTimer.from_dict(r)
        timers = result_model.timers
        if not isinstance(timers, list) or len(timers) == 0:
            self.state.timer = None
            return
        timer = timers[0]
        if not isinstance(timer, TimerModels.TimerItemV1):
            logger.debug("Invalid timer model - %s", timer)
            return
        self.state.timer = Timer(
            timer_duration=int(timer.counterTimer),
            id=int(timer.timerID),
            action=timer.action,
        )

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        if action not in [DeviceStatus.ON, DeviceStatus.OFF]:
            logger.error("Invalid action for timer - %s", action)
            return False
        update_dict = {
            'action': action,
            'counterTime': str(duration),
        }
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1SetTime,
            update_dict=update_dict,
            method='addTimer',
            endpoint='timer/addTimer'
        )
        result = process_bypassv1_result(self, logger, "set_timer", r_dict)
        if result is None:
            return False
        result_model = TimerModels.ResultV1SetTimer.from_dict(result)
        self.state.timer = Timer(duration, action, int(result_model.timerID))
        return True

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            logger.debug("No timer set, nothing to clear, run get_timer().")
            return False
        if self.state.timer.time_remaining == 0:
            logger.debug("Timer already ended.")
            self.state.timer = None
            return True
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1ClearTimer,
            {'timerId': str(self.state.timer.id)},
            method='deleteTimer',
            endpoint='timer/deleteTimer'
        )
        r_dict = Helpers.process_dev_response(
            logger, "clear_timer", self, r_dict
        )
        if r_dict is None:
            if self.last_response is not None and \
                    self.last_response.name == 'TIMER_NOT_EXISTS':
                self.state.timer = None
            return False
        self.state.timer = None
        return True

    async def turn_on_nightlight(self) -> bool:
        """Turn on nightlight."""
        return await self.set_nightlight_state(NightlightModes.ON)

    async def set_nightlight_auto(self) -> bool:
        """Set auto mode on nightlight."""
        return await self.set_nightlight_state(NightlightModes.AUTO)

    async def turn_off_nightlight(self) -> bool:
        """Turn Off Nightlight."""
        return await self.set_nightlight_state(NightlightModes.OFF)


class VeSyncOutdoorPlug(BypassV1Mixin, VeSyncOutlet):
    """Class to hold Etekcity outdoor outlets."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: OutletMap) -> None:
        """Initialize Etekcity Outdoor Plug class."""
        super().__init__(details, manager, feature_map)

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv1_api(
            Request15ADetails,
            method='deviceDetail',
            endpoint='deviceDetail'
        )
        r = Helpers.process_dev_response(logger, "get_details", self, r_dict)
        if r is None:
            return

        resp_model = ResponseOutdoorDetails.from_dict(r)
        self.state.connection_status = resp_model.result.connectionStatus
        self.state.energy = resp_model.result.energy
        self.state.power = resp_model.result.power
        self.state.voltage = resp_model.result.voltage
        self.state.active_time = resp_model.result.activeTime
        for outlet in resp_model.result.subDevices:
            if int(self.sub_device_no) == int(outlet.subDeviceNo):
                self.state.device_status = outlet.subDeviceStatus

    @deprecated(reason="Use toggle_switch(toggle: bool | None) instead")
    async def toggle(self, status: str) -> bool:
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
            endpoint='deviceStatus'
        )

        response = Helpers.process_dev_response(logger, "toggle", self, r_dict)
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
            endpoint=endpoint
        )

        r = process_bypassv1_result(self, logger, "get_timer", r_dict)
        if r is None:
            return
        result_model = TimerModels.ResultV1GetTimer.from_dict(r)
        timers = result_model.timers
        if not isinstance(timers, list) or len(timers) == 0:
            self.state.timer = None
            return
        if len(timers) > 1:
            logger.debug(
                (
                    (
                        "Multiple timers found - %s, this method "
                        "will only return the most recent timer created."
                    ),
                ),
                timers,
            )
        timer = timers[0]
        if not isinstance(timer, TimerModels.TimerItemV1):
            logger.debug("Invalid timer model - %s", timer)
            return
        self.state.timer = Timer(
            timer_duration=int(timer.counterTimer),
            id=int(timer.timerID),
            action=timer.action,
        )

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        if action not in [DeviceStatus.ON, DeviceStatus.OFF]:
            logger.error("Invalid action for timer - %s", action)
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
            endpoint='timer/addTimer'
        )
        result = process_bypassv1_result(self, logger, "set_timer", r_dict)
        if result is None:
            return False
        result_model = TimerModels.ResultV1SetTimer.from_dict(result)
        self.state.timer = Timer(duration, action, int(result_model.timerID))
        return True

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            logger.debug("No timer set, nothing to clear, run get_timer().")
            return False
        if self.state.timer.time_remaining == 0:
            logger.debug("Timer already ended.")
            self.state.timer = None
            return True
        r_dict = await self.call_bypassv1_api(
            TimerModels.RequestV1ClearTimer,
            {'timerId': str(self.state.timer.id)},
            method='deleteTimer',
            endpoint='timer/deleteTimer'
        )
        r_dict = Helpers.process_dev_response(
            logger, "clear_timer", self, r_dict
        )
        if r_dict is None:
            return False
        self.state.timer = None
        return True


class VeSyncOutletBSDGO1(BypassV2Mixin, VeSyncOutlet):
    """VeSync BSDGO1 smart plug."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: OutletMap) -> None:
        """Initialize BSDGO1 smart plug class."""
        super().__init__(details, manager, feature_map)

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv2_api('getProperty')

        result = process_bypassv2_results(self, logger, 'get_details', r_dict)
        if result is None:
            return

        resp_model = ResponseBSDGO1OutletResult.from_dict(result)
        device_state = resp_model.powerSwitch_1
        str_status = DeviceStatus.ON if device_state == 1 else DeviceStatus.OFF
        self.state.device_status = str_status
        self.state.connection_status = resp_model.connectionStatus
        self.state.active_time = resp_model.active_time

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_int = 1 if toggle else 0
        r_dict = await self.call_bypassv2_api(
            "setProperty", data={"powerSwitch_1": toggle_int}
        )
        r = Helpers.process_dev_response(logger, "toggle_switch", self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.ON if toggle else DeviceStatus.OFF
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    @deprecated(reason="Use toggle_switch(toggle: bool | None) instead")
    async def _set_power(self, power: bool) -> bool:
        """Set power state of BSDGO1 outlet."""
        return await self.toggle_switch(power)
