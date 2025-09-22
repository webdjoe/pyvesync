"""Module for VeSync Fans (Not Purifiers or Humidifiers)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyvesync.base_devices import VeSyncFanBase
from pyvesync.const import ConnectionStatus, DeviceStatus
from pyvesync.models.bypass_models import TimerModels
from pyvesync.models.fan_models import TowerFanResult
from pyvesync.utils.device_mixins import BypassV2Mixin, process_bypassv2_result
from pyvesync.utils.helpers import Helpers, Timer

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import FanMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel

logger = logging.getLogger(__name__)


class VeSyncTowerFan(BypassV2Mixin, VeSyncFanBase):
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

    def _set_fan_state(self, res: TowerFanResult) -> None:
        """Set fan state attributes from API response."""
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = DeviceStatus.from_int(res.powerSwitch)
        self.state.mode = res.workMode
        self.state.fan_level = res.fanSpeedLevel
        self.state.fan_set_level = res.manualSpeedLevel
        self.state.temperature = res.temperature

        self.state.mute_status = DeviceStatus.from_int(res.muteState)
        self.state.mute_set_status = DeviceStatus.from_int(res.muteSwitch)
        self.state.oscillation_status = DeviceStatus.from_int(res.oscillationState)
        self.state.oscillation_set_status = DeviceStatus.from_int(res.oscillationSwitch)
        self.state.display_status = DeviceStatus.from_int(res.screenState)
        self.state.display_set_status = DeviceStatus.from_int(res.screenSwitch)
        self.state.displaying_type = DeviceStatus.from_int(res.displayingType)

        if res.timerRemain is not None and res.timerRemain > 0:
            if self.state.device_status == DeviceStatus.ON:
                self.state.timer = Timer(res.timerRemain, action='off')
            else:
                self.state.timer = Timer(res.timerRemain, action='on')
        if res.sleepPreference is None:
            return
        self.state.sleep_preference_type = res.sleepPreference.sleepPreferenceType
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
        r_dict = await self.call_bypassv2_api('getTowerFanStatus')
        result = process_bypassv2_result(
            self, logger, 'get_details', r_dict, TowerFanResult
        )
        if result is None:
            return
        self._set_fan_state(result)

    async def set_fan_speed(self, speed: int | None = None) -> bool:
        if speed is None:
            new_speed = Helpers.bump_level(self.state.fan_level, self.fan_levels)
        else:
            new_speed = speed

        if new_speed not in self.fan_levels:
            logger.debug('Invalid fan speed level used - %s', speed)
            return False

        payload_data = {'manualSpeedLevel': speed, 'levelType': 'wind', 'levelIdx': 0}
        r_dict = await self.call_bypassv2_api('setLevel', payload_data)
        r = Helpers.process_dev_response(logger, 'set_fan_speed', self, r_dict)
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
            logger.debug('Invalid purifier mode used - %s', mode)
            return False

        payload_data = {'workMode': mode}
        r_dict = await self.call_bypassv2_api('setTowerFanMode', payload_data)
        r = Helpers.process_dev_response(logger, 'set_mode', self, r_dict)
        if r is None:
            return False

        self.state.mode = mode
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status == DeviceStatus.OFF
        payload_data = {
            'powerSwitch': int(toggle),
            'switchIdx': 0,
        }
        r_dict = await self.call_bypassv2_api('setSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_switch', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_oscillation(self, toggle: bool) -> bool:
        payload_data = {'oscillationSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setOscillationSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_oscillation', self, r_dict)
        if r is None:
            return False

        self.state.oscillation_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_mute(self, toggle: bool) -> bool:
        payload_data = {'muteSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setMuteSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_mute', self, r_dict)
        if r is None:
            return False

        self.state.mute_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_display(self, toggle: bool) -> bool:
        payload_data = {'screenSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setDisplay', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_display', self, r_dict)
        if r is None:
            return False

        self.state.display_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_displaying_type(self, toggle: bool) -> bool:
        """Set displaying type on/off - Unknown functionality."""
        payload_data = {'displayingType': int(toggle)}
        r_dict = await self.call_bypassv2_api('setDisplayingType', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_displaying_type', self, r_dict)
        if r is None:
            return False

        self.state.displaying_type = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def get_timer(self) -> None:
        r_dict = await self.call_bypassv2_api('getTimer', {})
        r_model = process_bypassv2_result(
            self, logger, 'get_timer', r_dict, TimerModels.ResultV2GetTimer
        )
        if not r_model:
            logger.debug('No timer found - run get_timer()')
            return
        if r_model.timers is None or len(r_model.timers) == 0:
            logger.debug('No timer found - run get_timer()')
            return
        timer = r_model.timers[0]
        if not isinstance(timer, TimerModels.TimerItemV2):
            logger.debug('Invalid timer found for %s', self.device_name)
            return
        self.state.timer = Timer(timer.remain, timer.action, timer.id)

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        if action is None:
            action = (
                DeviceStatus.OFF
                if self.state.device_status == DeviceStatus.ON
                else DeviceStatus.ON
            )
        if action not in [DeviceStatus.ON, DeviceStatus.OFF]:
            logger.debug('Invalid action used - %s', action)
            return False
        payload_data = {
            'action': action,
            'total': duration,
        }
        r_dict = await self.call_bypassv2_api('setTimer', payload_data)
        r_model = process_bypassv2_result(
            self, logger, 'set_timer', r_dict, TimerModels.ResultV2SetTimer
        )
        if r_model is None:
            return False
        self.state.timer = Timer(duration, action, r_model.id)
        return True

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            logger.debug('No timer found for - run get_timer()')
            return False
        payload_data = {
            'id': self.state.timer.id,
        }
        r_dict = await self.call_bypassv2_api('clearTimer', payload_data)
        result = Helpers.process_dev_response(logger, 'clear_timer', self, r_dict)
        if result is None:
            return False
        self.state.timer = None
        return True
