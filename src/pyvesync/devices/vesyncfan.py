"""Module for VeSync Fans (Not Purifiers or Humidifiers)."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from pyvesync.utils.helpers import Helpers, Timer
from pyvesync.base_devices.fan_base import VeSyncFanBase
from pyvesync.models.base_models import DefaultValues
from pyvesync.const import DeviceStatus, ConnectionStatus
from pyvesync.models.fan_models import (
    TowerFanResult,
    RequestFanStatus,
    ResponseFanBase
    )

if TYPE_CHECKING:
    from pyvesync.device_map import FanMap
    from pyvesync import VeSync
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel

logger = logging.getLogger(__name__)


class VeSyncTowerFan(VeSyncFanBase):
    """Levoit Tower Fan Device Class."""

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: FanMap,
    ) -> None:
        """Initialize the VeSync Base API V2 Fan Class."""
        super().__init__(details, manager, feature_map)
        self.request_keys = [
            "acceptLanguage",
            "appVersion",
            "phoneBrand",
            "phoneOS",
            "accountId",
            "cid",
            "configModule",
            "debugMode",
            "traceId",
            "timeZone",
            "token",
            "userCountryCode",
            "deviceId",
            "configModel",
        ]

    def _build_request(
            self, payload_method: str, data: dict | None = None, method: str = 'bypassV2'
            ) -> RequestFanStatus:
        """Build API request body for air purifier."""
        body = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        body.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        body.update(Helpers.get_class_attributes(self, self.request_keys))
        body['method'] = method
        body['payload'] = {
            "method": payload_method,
            "source": "APP",
            "data": data or {}
        }
        return RequestFanStatus.from_dict(body)

    def _set_fan_state(self, res: TowerFanResult) -> None:
        """Set fan state attributes from API response."""
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = DeviceStatus.from_int(res.powerSwitch)
        self.state.mode = res.workMode
        self.state.fan_level = res.fanSpeedLevel
        self.state.fan_set_level = res.manualSpeedLevel
        self.state.humidity = res.humidity
        self.state.temperature = res.temperature
        self.state.thermal_comfort = res.thermalComfort

        self.state.mute_status = DeviceStatus.from_int(res.muteState)
        self.state.mute_set_state = DeviceStatus.from_int(res.muteSwitch)
        self.state.oscillation_status = DeviceStatus.from_int(res.oscillationState)
        self.state.oscillation_set_state = DeviceStatus.from_int(res.oscillationSwitch)
        self.state.display_status = DeviceStatus.from_int(res.screenState)
        self.state.display_set_state = DeviceStatus.from_int(res.screenSwitch)
        self.state.displaying_type = DeviceStatus.from_int(res.displayingType)

        if res.timerRemain is not None and res.timerRemain > 0:
            if self.state.device_status == DeviceStatus.ON:
                self.state.timer = Timer(res.timerRemain, action="off")
            else:
                self.state.timer = Timer(res.timerRemain, action="on")
        if res.sleepPreference is None:
            return
        self.state.sleep_preference_type = DeviceStatus.from_int(
            res.sleepPreference.sleepPreferenceType
            )
        self.state.sleep_fallasleep_remain = DeviceStatus.from_int(
            res.sleepPreference.fallAsleepRemain
            )
        self.state.sleep_oscillation_switch = DeviceStatus.from_int(
            res.sleepPreference.oscillationSwitch
            )
        self.state.sleep_change_fan_level = DeviceStatus.from_int(
            res.sleepPreference.autoChangeFanLevelSwitch
            )

    async def get_details(self) -> None:
        body = self._build_request('getTowerFanStatus')
        headers = Helpers.req_header_bypass()
        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
        if r is None:
            return

        r_model = ResponseFanBase.from_dict(r)
        result = r_model.result.result

        if result is None or not isinstance(result, TowerFanResult):
            logger.debug('No result dict from purifier')
            return

        self._set_fan_state(result)

    async def set_fan_speed(self, speed: int | None = None) -> bool:
        """Set Levoit Tower Fan speed level."""
        if speed is None:
            new_speed = Helpers.bump_level(self.state.fan_level, self.fan_levels)
        else:
            new_speed = speed

        if new_speed not in self.fan_levels:
            logger.debug('Invalid fan speed level used - %s', speed)
            return False

        payload_data = {
            "manualSpeedLevel": speed,
            "levelType": "wind",
            "levelIdx": 0
        }
        body = self._build_request('setLevel', payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_fan_speed", self, r_bytes)
        if r is None:
            return False

        self.state.fan_level = speed
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mode(self, mode: str) -> bool:
        if mode.lower() == DeviceStatus.OFF:
            logger.warning('Deprecated - Use `turn_off` method to turn off device')
            return await self.turn_off()

        if mode.lower() not in self.modes:
            logger.debug('Invalid purifier mode used - %s',
                         mode)
            return False

        payload_data = {
            "workMode": mode
        }
        body = self._build_request('setTowerFanStatus', payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_mode", self, r_bytes)
        if r is None:
            return False

        self.state.mode = mode
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_oscillation(self, toggle: bool) -> bool:
        """Toggle oscillation on/off.

        Parameters:
            toggle : bool
                True to turn oscillation on, False to turn off

        Returns:
            bool : True if successful, False if not
        """
        payload_data = {
            "oscillationSwitch": int(toggle)
        }
        body = self._build_request('setOscillationSwitch', payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "toggle_oscillation", self, r_bytes)
        if r is None:
            return False

        self.state.oscillation_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_mute(self, toggle: bool) -> bool:
        """Toggle mute on/off.

        Parameters:
            toggle : bool
                True to turn mute on, False to turn off

        Returns:
            bool : True if successful, False if not
        """
        payload_data = {
            "muteSwitch": int(toggle)
        }
        body = self._build_request('setMuteSwitch', payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "toggle_mute", self, r_bytes)
        if r is None:
            return False

        self.state.mute_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_display(self, toggle: bool) -> bool:
        payload_data = {
            "screenSwitch": int(toggle)
        }
        body = self._build_request('setDisplay', payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "toggle_display", self, r_bytes)
        if r is None:
            return False

        self.state.display_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_displaying_type(self, toggle: bool) -> bool:
        """Set displaying type on/off - Unknown functionality."""
        payload_data = {
            "displayingType": int(toggle)
        }
        body = self._build_request('setDisplayingType', payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "toggle_displaying_type", self, r_bytes)
        if r is None:
            return False

        self.state.displaying_type = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True
