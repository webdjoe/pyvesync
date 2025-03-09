"""Etekcity Outlets."""

from __future__ import annotations
import logging
from datetime import datetime as dt, timedelta
from zoneinfo import ZoneInfo
from typing import TYPE_CHECKING
from deprecated import deprecated

from pyvesync.base_devices.outlet_base_device import VeSyncOutlet
from pyvesync.data_models.outlet_models import Response7AOutlet
from pyvesync.helper_utils.helpers import Helpers
from pyvesync.helper_utils.logs import LibraryLogger
from pyvesync.data_models.base_models import RequestHeaders, DefaultValues
from pyvesync.const import DeviceStatus, ConnectionStatus, NightlightModes
from pyvesync.data_models.outlet_models import (
    ResponseEnergyHistory,
    Response10ADetails,
    ResponseEnergyResult,
    Response15ADetails,
    Request15AEnergy,
    ResponseOutdoorDetails,
    ResponseBSDGO1Details,
    )

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.data_models.device_list_models import ResponseDeviceDetailsModel
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
        """Initilize Etekcity 7A round outlet class."""
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

    def _build_energy_request(self, method: str) -> Request15AEnergy:
        """Build energy request for 7A Outlets."""
        request_keys = ["acceptLanguage", "accountID", "appVersion", "phoneBrand",
                        "phoneOS", "timeZone", "token", "traceId", "userCountryCode",
                        "debugMode", "homeTimeZone", "uuid"]
        body = Helpers.get_class_attributes(DefaultValues, request_keys)
        body.update(Helpers.get_class_attributes(self.manager, request_keys))
        body.update(Helpers.get_class_attributes(self, request_keys))
        body['method'] = method
        return Request15AEnergy.from_dict(body)

    async def get_details(self) -> None:
        """Get 7A outlet details."""
        r_bytes, _ = await self.manager.async_call_api(
            '/v1/device/' + self.cid + '/detail',
            'get',
            headers=self._build_headers(),
        )

        r = Helpers.try_json_loads(r_bytes)

        if not isinstance(r, dict):
            LibraryLogger.log_device_api_response_error(
                logger, self.device_name, self.device_type,
                'get_details', "Response is not valid JSON"
            )
            return

        if 'error' in r:
            r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
            return
        self.state.update_ts()
        resp_model = Response7AOutlet.from_dict(r)
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

    async def get_weekly_energy(self) -> None:
        """Get 7A outlet weekly energy info and buld weekly energy dict."""
        body = self._build_energy_request('getLastWeekEnergy')
        headers = Helpers.req_header_bypass()
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/device/getLastWeekEnergy',
            'post',
            headers=headers,
            json_object=body.to_dict(),
        )

        r = Helpers.process_dev_response(
            logger, "get_weekly_energy", self, r_bytes
            )
        if r is None:
            return
        response = ResponseEnergyHistory.from_dict(r)
        self.state.weekly_history = response.result

    async def get_monthly_energy(self) -> None:
        """Get 7A outlet monthly energy info and buld monthly energy dict."""
        body = self._build_energy_request('getLastMonthEnergy')
        headers = Helpers.req_header_bypass()
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/device/getLastMonthEnergy',
            'post',
            headers=headers,
            json_object=body.to_dict(),
        )

        r = Helpers.process_dev_response(
            logger, "get_monthly_energy", self, r_bytes
            )
        if r is None:
            return
        response = ResponseEnergyHistory.from_dict(r)
        self.state.monthly_history = response.result

    async def get_yearly_energy(self) -> None:
        """Get 7A outlet yearly energy info and build yearly energy dict."""
        body = self._build_energy_request('getLastYearEnergy')
        headers = Helpers.req_header_bypass()
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/device/getLastYearEnergy',
            'post',
            headers=headers,
            json_object=body.to_dict(),
        )

        r = Helpers.process_dev_response(
            logger, "get_yearly_energy", self, r_bytes
            )
        if r is None:
            return
        response = ResponseEnergyHistory.from_dict(r)
        self.state.yearly_history = response.result

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Toggle 7A outlet power - return True if successful."""
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_str = DeviceStatus.ON if toggle else DeviceStatus.OFF
        r_bytes, status_code = await self.manager.async_call_api(
            f'/v1/wifi-switch-1.3/{self.cid}/status/{toggle_str}',
            'put',
            headers=Helpers.req_headers(self.manager),
        )

        if status_code != 200:
            LibraryLogger.log_device_api_response_error(
                logger, self.device_name, self.device_type,
                'toggle_switch', "Response code is not 200"
            )

        r = Helpers.try_json_loads(r_bytes)

        if isinstance(r, dict) and 'error' in r:
            r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
            return False

        self.state.update_ts()
        self.state.device_status = toggle_str
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def turn_on(self) -> bool:
        """Turn 7A outlet on - return True if successful."""
        return await self.toggle_switch(True)

    async def turn_off(self) -> bool:
        """Turn 7A outlet off - return True if successful."""
        return await self.toggle_switch(False)


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
        """Buil auth headers for 10A Outlet."""
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

    def _build_energy_request(self, method: str) -> dict:
        """Build 10A Outlet Request for energy."""
        energy_keys = ['traceID', 'token', 'accountID', 'timeZone', 'acceptLanguage',
                       'appVersion', 'phoneBrand', 'phoneOS', 'uuid']
        body = Helpers.get_class_attributes(DefaultValues, energy_keys)
        body.update(Helpers.get_class_attributes(self.manager, energy_keys))
        body.update(Helpers.get_class_attributes(self, energy_keys))
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
        """Get 10A outlet details."""
        body = self._build_detail_request('devicedetail')

        r_bytes, _ = await self.manager.async_call_api(
            '/10a/v1/device/devicedetail',
            'post',
            headers=Helpers.req_headers(self.manager),
            json_object=body,
        )
        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        resp_model = Response10ADetails.from_dict(r)

        self.state.device_status = resp_model.deviceStatus or "off"
        self.state.connection_status = resp_model.connectionStatus or "offline"
        self.state.energy = resp_model.energy or 0
        self.state.power = resp_model.power or 0
        self.state.voltage = resp_model.voltage or 0

    def _parse_energy_history(self, energy_response: dict) -> ResponseEnergyResult:
        """Converts a list of float values into a list of dictionaries with timestamps.

        Args:
            energy_response (dict): Response dictionary for 10A outlet energy

        Returns:
            ResponseEnergyResult: Energy response data model
        """
        if 'data' not in energy_response:
            return ResponseEnergyResult.from_dict(energy_response)
        data = energy_response['data']
        now = dt.now(tz=ZoneInfo(self.manager.time_zone)).replace(
            microsecond=0,
            second=0,
            minute=0,
            hour=0,
            tzinfo=ZoneInfo(self.manager.time_zone)
            )
        length = len(data)
        result = []

        if length == 7:
            for i in range(length):
                timestamp = now - timedelta(days=(length - i))
                result.append({
                    "timestamp": int(timestamp.isoformat()),
                    "value": data[i],
                    "money": 0
                })

        elif length == 12:
            for i in range(length):
                year = (now.year if now.month > i else now.year - 1)
                month = (now.month - i) % 12 or 12
                cur_date = dt(
                    year, month, 1, 0, 0, 0, tzinfo=ZoneInfo(self.manager.time_zone)
                    )
                result.append(
                    {"timestamp": int(cur_date.isoformat()), "value": data[i], "money": 0}
                    )

        else:
            for i in range(length):
                timestamp = now - timedelta(days=(length - i))
                result.append({
                    "timestamp": int(timestamp.isoformat()),
                    "value": data[i],
                    "money": 0
                    })

        energy_response['energyInfos'] = result
        del energy_response['data']

        return ResponseEnergyResult.from_dict(energy_response)

    async def get_weekly_energy(self) -> None:
        """Get 10A outlet weekly energy info and populate energy dict."""
        body = self._build_energy_request('energyweek')
        headers = self._build_headers()

        r_bytes, _ = await self.manager.async_call_api(
            '/10a/v1/device/energyweek',
            'post',
            headers=headers,
            json_object=body,
        )
        response = Helpers.process_dev_response(
            logger, "get_weekly_energy", self, r_bytes
            )
        if response is None:
            return

        energy_history = self._parse_energy_history(response)

        self.state.weekly_history = energy_history

    async def get_monthly_energy(self) -> None:
        """Get 10A outlet monthly energy info and populate energy dict."""
        body = self._build_energy_request('energymonth')
        headers = self._build_headers()
        r_bytes, _ = await self.manager.async_call_api(
            '/10a/v1/device/energymonth',
            'post',
            headers=headers,
            json_object=body,
        )
        response = Helpers.process_dev_response(
            logger, "get_monthly_energy", self, r_bytes
        )
        if response is None:
            return

        energy_history = self._parse_energy_history(response)

        self.state.monthly_history = energy_history

    async def get_yearly_energy(self) -> None:
        """Get 10A outlet yearly energy info and populate energy dict."""
        body = self._build_energy_request('energyyear')
        headers = self._build_headers()

        r_bytes, _ = await self.manager.async_call_api(
            '/10a/v1/device/energyyear',
            'post',
            headers=headers,
            json_object=body,
        )
        response = Helpers.process_dev_response(
            logger, "get_yearly_energy", self, r_bytes
        )
        if response is None:
            return

        energy_history = self._parse_energy_history(response)

        self.state.yearly_history = energy_history

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_str = DeviceStatus.ON if toggle else DeviceStatus.OFF
        # body = Helpers.req_body(self.manager, 'devicestatus')
        # body['uuid'] = self.uuid
        # body['status'] = toggle_str
        body = self._build_status_request(toggle_str)
        headers = self._build_headers()

        r_bytes, _ = await self.manager.async_call_api(
            '/10a/v1/device/devicestatus',
            'put',
            headers=headers,
            json_object=body,
        )
        response = Helpers.process_dev_response(logger, "toggle_switch", self, r_bytes)
        if response is None:
            return False

        self.state.device_status = toggle_str
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def turn_on(self) -> bool:
        """Turn 10A outlet on - return True if successful."""
        return await self.toggle_switch(True)

    async def turn_off(self) -> bool:
        """Turn 10A outlet off - return True if successful."""
        return await self.toggle_switch(False)


class VeSyncOutlet15A(VeSyncOutlet):
    """Class for Etekcity 15A Rectangular Outlets."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: OutletMap) -> None:
        """Initialize 15A rectangular outlets."""
        super().__init__(details, manager, feature_map)
        self.request_keys = [
            "acceptLanguage",
            "accountID",
            "appVersion",
            "cid",
            "configModule",
            "debugMode",
            "phoneBrand",
            "phoneOS",
            "timeZone",
            "token",
            "traceId",
            "userCountryCode",
            "uuid",
        ]

    def _build_request(self, method: str) -> dict:
        """Build 15A Outlet Request."""
        body = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        body.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        body.update(Helpers.get_class_attributes(self, self.request_keys))
        body['deviceId'] = self.cid
        body['configModel'] = self.config_module
        body['method'] = method
        return body

    def _build_energy_request(self, method: str) -> Request15AEnergy:
        """Build request for energy API calls."""
        request_keys = ["acceptLanguage", "accountID", "appVersion", "phoneBrand",
                        "phoneOS", "timeZone", "token", "traceId", "userCountryCode",
                        "debugMode", "homeTimeZone", "uuid"]
        body = Helpers.get_class_attributes(DefaultValues, request_keys)
        body.update(Helpers.get_class_attributes(self.manager, request_keys))
        body.update(Helpers.get_class_attributes(self, request_keys))
        body['method'] = method
        return Request15AEnergy.from_dict(body)

    async def get_details(self) -> None:
        """Get 15A outlet details."""
        body = self._build_request('deviceDetail')

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/deviceDetail',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=body,
        )

        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
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

    # async def get_config(self) -> None:
    #     """Get 15A outlet configuration info."""
    #     body = Helpers.req_body(self.manager, 'devicedetail')
    #     body['method'] = 'configurations'
    #     body['uuid'] = self.uuid

    #     r_bytes, _ = await self.manager.async_call_api(
    #         '/15a/v1/device/configurations',
    #         'post',
    #         headers=Helpers.req_headers(self.manager),
    #         json_object=body,
    #     )
    #     r = Helpers.process_dev_response(logger, "get_config", self, r_bytes)
    #     if r is None:
    #         return

    #     self.config = Helpers.build_config_dict(r)

    async def get_weekly_energy(self) -> None:
        """Get 15A outlet weekly energy info and populate energy dict."""
        body = self._build_energy_request('getLastWeekEnergy')
        headers = Helpers.req_header_bypass()
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/device/getLastWeekEnergy',
            'post',
            headers=headers,
            json_object=body.to_dict(),
        )
        response = Helpers.process_dev_response(
            logger, "get_weekly_energy", self, r_bytes
        )
        if response is None:
            return
        resp_model = ResponseEnergyHistory.from_dict(response)
        self.state.weekly_history = resp_model.result

    async def get_monthly_energy(self) -> None:
        """Get 15A outlet monthly energy info and populate energy dict."""
        body = self._build_energy_request('getLastMonthEnergy')
        headers = Helpers.req_header_bypass()
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/device/getLastMonthEnergy',
            'post',
            headers=headers,
            json_object=body.to_dict(),
        )
        response = Helpers.process_dev_response(
            logger, "get_monthly_energy", self, r_bytes
        )
        if response is None:
            return
        resp_model = ResponseEnergyHistory.from_dict(response)
        self.state.monthly_history = resp_model.result

    async def get_yearly_energy(self) -> None:
        """Get 15A outlet yearly energy info and populate energy dict."""
        body = self._build_energy_request('getLastYearEnergy')
        headers = Helpers.req_header_bypass()
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/device/getLastYearEnergy',
            'post',
            headers=headers,
            json_object=body.to_dict(),
        )
        response = Helpers.process_dev_response(
            logger, "get_weekly_energy", self, r_bytes
        )
        if response is None:
            return
        resp_model = ResponseEnergyHistory.from_dict(response)
        self.state.yearly_history = resp_model.result

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_str = DeviceStatus.ON if toggle else DeviceStatus.OFF
        body = self._build_request('deviceStatus')
        body['status'] = toggle_str

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/deviceStatus',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=body,
        )
        response = Helpers.process_dev_response(logger, "toggle_switch", self, r_bytes)
        if response is None:
            return False

        self.state.device_status = toggle_str
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def turn_on(self) -> bool:
        """Turn 15A outlet on - return True if successful."""
        return await self.toggle_switch(True)

    async def turn_off(self) -> bool:
        """Turn 15A outlet off - return True if successful."""
        return await self.toggle_switch(False)

    async def set_nightlight_state(self, mode: str) -> bool:
        """Set nightlight state for 15A Outlets."""
        if mode.lower() not in NightlightModes:
            logger.error("Invalid nightlight mode - %s", mode)
            return False
        mode = mode.lower()
        body = self._build_request('outletNightLightCtl')
        body['mode'] = mode

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/outletNightLightCtl',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=body,
        )

        response = Helpers.process_dev_response(
            logger, "set_nightlight_state", self, r_bytes
            )
        if response is None:
            return False

        self.state.nightlight_status = mode
        self.state.connection_status = ConnectionStatus.ONLINE
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


class VeSyncOutdoorPlug(VeSyncOutlet):
    """Class to hold Etekcity outdoor outlets."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: OutletMap) -> None:
        """Initialize Etekcity Outdoor Plug class."""
        super().__init__(details, manager, feature_map)
        self.request_keys = [
            "acceptLanguage",
            "accountID",
            "appVersion",
            "cid",
            "configModule",
            "debugMode",
            "phoneBrand",
            "phoneOS",
            "timeZone",
            "token",
            "traceId",
            "userCountryCode",
            "uuid",
        ]

    def _build_request(self, method: str) -> dict:
        """Build 15A Outlet Request."""
        body = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        body.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        body.update(Helpers.get_class_attributes(self, self.request_keys))
        body['deviceId'] = self.cid
        body['configModel'] = self.config_module
        body['method'] = method
        return body

    def _build_energy_request(self, method: str) -> Request15AEnergy:
        """Build request for energy API calls."""
        request_keys = ["acceptLanguage", "accountID", "appVersion", "phoneBrand",
                        "phoneOS", "timeZone", "token", "traceId", "userCountryCode",
                        "debugMode", "homeTimeZone", "uuid"]
        body = Helpers.get_class_attributes(DefaultValues, request_keys)
        body.update(Helpers.get_class_attributes(self.manager, request_keys))
        body.update(Helpers.get_class_attributes(self, request_keys))
        body['method'] = method
        return Request15AEnergy.from_dict(body)

    async def get_details(self) -> None:
        """Get details for outdoor outlet."""
        body = self._build_request('deviceDetail')
        headers = Helpers.req_header_bypass()
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/deviceDetail',
            'post',
            headers=headers,
            json_object=body,
        )
        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
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

    async def get_weekly_energy(self) -> None:
        """Get outdoor outlet weekly energy info and populate energy dict."""
        body = self._build_energy_request('getLastWeekEnergy')
        header = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/device/getLastWeekEnergy',
            'post',
            headers=header,
            json_object=body.to_dict(),
        )
        response = Helpers.process_dev_response(
            logger, "get_weekly_energy", self, r_bytes
        )
        if response is None:
            return

        resp_model = ResponseEnergyHistory.from_dict(response)
        self.state.weekly_history = resp_model.result

    async def get_monthly_energy(self) -> None:
        """Get outdoor outlet monthly energy info and populate energy dict."""
        body = self._build_energy_request('getLastMonthEnergy')
        header = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/device/getLastMonthEnergy',
            'post',
            headers=header,
            json_object=body.to_dict(),
        )
        response = Helpers.process_dev_response(
            logger, "get_monthly_energy", self, r_bytes
        )
        if response is None:
            return

        resp_model = ResponseEnergyHistory.from_dict(response)
        self.state.monthly_history = resp_model.result

    async def get_yearly_energy(self) -> None:
        """Get outdoor outlet yearly energy info and populate energy dict."""
        body = self._build_energy_request('getLastYearEnergy')
        header = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/device/getLastYearEnergy',
            'post',
            headers=header,
            json_object=body.to_dict(),
        )
        response = Helpers.process_dev_response(
            logger, "get_yearly_energy", self, r_bytes
        )
        if response is None:
            return

        resp_model = ResponseEnergyHistory.from_dict(response)
        self.state.yearly_history = resp_model.result

    @deprecated(reason="Use toggle_switch(toggle: bool | None) instead")
    async def toggle(self, status: str) -> bool:
        """Toggle power for outdoor outlet."""
        toggle = status != DeviceStatus.ON
        return await self.toggle_switch(toggle)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        status = DeviceStatus.ON if toggle else DeviceStatus.OFF
        body = self._build_request('deviceStatus')
        body['switchNo'] = self.sub_device_no
        body['status'] = status
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v1/deviceManaged/deviceStatus',
            'post',
            headers=headers,
            json_object=body,
        )
        response = Helpers.process_dev_response(logger, "toggle", self, r_bytes)
        if response is None:
            return False

        self.state.device_status = status
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def turn_on(self) -> bool:
        """Turn on outlet."""
        return await self.toggle_switch(True)

    async def turn_off(self) -> bool:
        """Turn off outlet."""
        return await self.toggle_switch(False)


class VeSyncOutletBSDGO1(VeSyncOutlet):
    """VeSync BSDGO1 smart plug."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: OutletMap) -> None:
        """Initialize BSDGO1 smart plug class."""
        super().__init__(details, manager, feature_map)
        self.request_keys = [
            "acceptLanguage",
            "accountID",
            "appVersion",
            "cid",
            "configModule",
            "deviceRegion",
            "phoneBrand",
            "phoneOS",
            "timeZone",
            "token",
            "traceId",
        ]

    def _build_request(
            self, method: str = "bypassV2", payload: dict | None = None
            ) -> dict:
        """Build request for BSDG01 Smart Plug."""
        body = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        body.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        body.update(Helpers.get_class_attributes(self, self.request_keys))
        body['payload'] = payload or {}
        body['method'] = method
        return body

    async def get_details(self) -> None:
        """Get BSDGO1 device details."""
        payload = {
            'method': 'getProperty',
            'source': 'APP',
            'data': {}
        }
        body = self._build_request(payload=payload)

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=body,
        )
        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        resp_model = ResponseBSDGO1Details.from_dict(r)
        device_state = resp_model.result.powerSwitch_1
        str_status = DeviceStatus.ON if device_state == 1 else DeviceStatus.OFF
        self.state.device_status = str_status
        self.state.connection_status = resp_model.result.connectionStatus
        self.state.active_time = resp_model.result.active_time

    async def turn_on(self) -> bool:
        """Turn BSDGO1 outlet on."""
        return await self.toggle_switch(True)

    async def turn_off(self) -> bool:
        """Turn BSDGO1 outlet off."""
        return await self.toggle_switch(False)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON
        toggle_int = 1 if toggle else 0

        payload = {
            'data': {'powerSwitch_1': toggle_int},
            'method': 'setProperty',
            'source': 'APP'
        }
        body = self._build_request(payload=payload)

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=body,
        )
        r = Helpers.process_dev_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.ON if toggle else DeviceStatus.OFF
        return True

    @deprecated(reason="Use toggle_switch(toggle: bool | None) instead")
    async def _set_power(self, power: bool) -> bool:
        """Set power state of BSDGO1 outlet."""
        return await self.toggle_switch(power)
