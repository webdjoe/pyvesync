"""VeSync Kitchen Devices.

The Cosori 3.7 and 5.8 Quart Air Fryer has several methods and properties that can be
used to monitor and control the device.

To maintain consistency of state, the update() method is called after each of the methods
that change the state of the device.

There is also an instance attribute that can be set `VeSyncAirFryer158.refresh_interval`
that will set the interval in seconds that the state of the air fryer should be updated
before a method that changes state is called. This is an additional API call but is
necessary to maintain state, especially when trying to `pause` or `resume` the device.
Defaults to 60 seconds but can be set via:

```python
# Change to 120 seconds before status is updated between calls
VeSyncAirFryer158.refresh_interval = 120

# Set status update before every call
VeSyncAirFryer158.refresh_interval = 0

# Disable status update before every call
VeSyncAirFryer158.refresh_interval = -1
```

"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, TypeVar

from typing_extensions import deprecated

from pyvesync.base_devices import FryerState, VeSyncFryer
from pyvesync.const import AIRFRYER_PID_MAP, ConnectionStatus, DeviceStatus, TemperatureUnits, AirFryerCookModes, AirFryerCookStatus, AirFryerFeatures, AirFryerPresets
from pyvesync.models.fryer_models import Fryer158CookingReturnStatus, Fryer158RequestModel, Fryer158Result
from pyvesync.utils.device_mixins import BypassV1Mixin, process_bypassv1_result
from pyvesync.utils.errors import VeSyncError
from pyvesync.utils.helpers import Helpers
from pyvesync.utils.logs import LibraryLogger

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import AirFryerMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel

T = TypeVar('T')

logger = logging.getLogger(__name__)


# Status refresh interval in seconds
# API calls outside of interval are automatically refreshed
# Set VeSyncAirFryer158.refresh_interval to 0 to refresh every call
# Set to None or -1 to disable auto-refresh
REFRESH_INTERVAL = 60

RECIPE_ID = 1
RECIPE_TYPE = 3
CUSTOM_RECIPE = 'Manual Cook'
COOK_MODE = 'custom'


# class AirFryer158138State(FryerState):
#     """Dataclass for air fryer status.

#     Attributes:
#         active_time (int): Active time of device, defaults to None.
#         connection_status (str): Connection status of device.
#         device (VeSyncBaseDevice): Device object.
#         device_status (str): Device status.
#         features (dict): Features of device.
#         last_update_ts (int): Last update timestamp of device, defaults to None.
#         ready_start (bool): Ready start status of device, defaults to False.
#         preheat (bool): Preheat status of device, defaults to False.
#         cook_status (str): Cooking status of device, defaults to None.
#         current_temp (int): Current temperature of device, defaults to None.
#         cook_set_temp (int): Cooking set temperature of device, defaults to None.
#         last_timestamp (int): Last timestamp of device, defaults to None.
#         preheat_set_time (int): Preheat set time of device, defaults to None.
#         preheat_last_time (int): Preheat last time of device, defaults to None.
#         _temp_unit (str): Temperature unit of device, defaults to None.
#     """

#     __slots__ = ()

#     def __init__(
#         self,
#         device: VeSyncAirFryer158,
#         details: ResponseDeviceDetailsModel,
#         feature_map: AirFryerMap,
#     ) -> None:
#         """Init the Air Fryer 158 class."""
#         super().__init__(device, details, feature_map)
#         self.device: VeSyncFryer = device
#         self.features: list[str] = feature_map.features
#         self.min_temp_f: int = feature_map.temperature_range_f[0]
#         self.max_temp_f: int = feature_map.temperature_range_f[1]
#         self.min_temp_c: int = feature_map.temperature_range_c[0]
#         self.max_temp_c: int = feature_map.temperature_range_c[1]
#         self.ready_start: bool = False
#         self.preheat: bool = False
#         self.cook_status: str | None = None
#         self.current_temp: int | None = None
#         self.cook_set_temp: int | None = None
#         self.cook_set_time: int | None = None
#         self.cook_last_time: int | None = None
#         self.last_timestamp: int | None = None
#         self.preheat_set_time: int | None = None
#         self.preheat_last_time: int | None = None
#         self._temp_unit: str | None = None

#     @property
#     def is_resumable(self) -> bool:
#         """Return if cook is resumable."""
#         if self.cook_status in ['cookStop', 'preheatStop']:
#             if self.cook_set_time is not None:
#                 return self.cook_set_time > 0
#             if self.preheat_set_time is not None:
#                 return self.preheat_set_time > 0
#         return False

#     @property
#     def temp_unit(self) -> str | None:
#         """Return temperature unit."""
#         return self._temp_unit

#     @temp_unit.setter
#     def temp_unit(self, temp_unit: str) -> None:
#         """Set temperature unit."""
#         if temp_unit.lower() in ['f', 'fahrenheit', 'fahrenheight']:  # API TYPO
#             self._temp_unit = 'fahrenheit'
#         elif temp_unit.lower() in ['c', 'celsius']:
#             self._temp_unit = 'celsius'
#         else:
#             msg = f'Invalid temperature unit - {temp_unit}'
#             raise ValueError(msg)

#     @property
#     def preheat_time_remaining(self) -> int:
#         """Return preheat time remaining."""
#         if self.preheat is False or self.cook_status == 'preheatEnd':
#             return 0
#         if self.cook_status in ['pullOut', 'preheatStop']:
#             if self.preheat_last_time is None:
#                 return 0
#             return int(self.preheat_last_time)
#         if self.preheat_last_time is not None and self.last_timestamp is not None:
#             return int(
#                 max(
#                     (
#                         self.preheat_last_time * 60
#                         - (int(time.time()) - self.last_timestamp)
#                     )
#                     // 60,
#                     0,
#                 )
#             )
#         return 0

#     @property
#     def cook_time_remaining(self) -> int:
#         """Returns the amount of time remaining if cooking."""
#         if self.preheat is True or self.cook_status == 'cookEnd':
#             return 0
#         if self.cook_status in ['pullOut', 'cookStop']:
#             if self.cook_last_time is None:
#                 return 0
#             return int(max(self.cook_last_time, 0))
#         if self.cook_last_time is not None and self.last_timestamp is not None:
#             return int(
#                 max(
#                     (self.cook_last_time * 60 - (int(time.time()) - self.last_timestamp))
#                     // 60,
#                     0,
#                 )
#             )
#         return 0

#     @property
#     def remaining_time(self) -> int:
#         """Return minutes remaining if cooking/heating."""
#         if self.preheat is True:
#             return self.preheat_time_remaining
#         return self.cook_time_remaining

#     @property
#     def is_running(self) -> bool:
#         """Return if cooking or heating."""
#         return self.cook_status in ('cooking', 'heating') and self.remaining_time > 0

#     @property
#     def is_cooking(self) -> bool:
#         """Return if cooking."""
#         return self.cook_status == 'cooking' and self.remaining_time > 0

#     @property
#     def is_heating(self) -> bool:
#         """Return if heating."""
#         return self.cook_status == 'heating' and self.remaining_time > 0

#     def status_request(self, json_cmd: dict) -> None:
#         """Set status from jsonCmd of API call."""
#         self.last_timestamp = None
#         if not isinstance(json_cmd, dict):
#             return
#         self.preheat = False

#         preheat_cmd = json_cmd.get('preheat')
#         if isinstance(preheat_cmd, dict):
#             self.preheat = True
#             preheat_status = preheat_cmd.get('preheatStatus')
#             if preheat_status == 'stop':
#                 self.cook_status = 'preheatStop'
#                 return
#             if preheat_status == 'heating':
#                 self.cook_status = 'heating'
#                 self.last_timestamp = int(time.time())
#                 self.preheat_set_time = preheat_cmd.get(
#                     'preheatSetTime', self.preheat_set_time
#                 )
#                 preheat_set_time = preheat_cmd.get('preheatSetTime')
#                 if preheat_set_time is not None:
#                     self.preheat_last_time = preheat_set_time
#                 self.cook_set_temp = preheat_cmd.get('targetTemp', self.cook_set_temp)
#                 self.cook_set_time = preheat_cmd.get('cookSetTime', self.cook_set_time)
#                 self.cook_last_time = None
#                 return
#             if preheat_status == 'end':
#                 self.cook_status = 'preheatEnd'
#                 self.preheat_last_time = 0
#             return

#         cook_cmd = json_cmd.get('cookMode')
#         if not isinstance(cook_cmd, dict):
#             return

#         self.clear_preheat()
#         cook_status = cook_cmd.get('cookStatus')
#         if cook_status == 'stop':
#             self.cook_status = 'cookStop'
#             return
#         if cook_status == 'cooking':
#             self.cook_status = 'cooking'
#             self.last_timestamp = int(time.time())
#             self.cook_set_time = cook_cmd.get('cookSetTime', self.cook_set_time)
#             self.cook_set_temp = cook_cmd.get('cookSetTemp', self.cook_set_temp)
#             self.current_temp = cook_cmd.get('currentTemp', self.current_temp)
#             self.temp_unit = cook_cmd.get(
#                 'tempUnit',
#                 self.temp_unit,  # type: ignore[assignment]
#             )
#             return
#         if cook_status == 'end':
#             self.set_standby()
#             self.cook_status = 'cookEnd'

#     def clear_preheat(self) -> None:
#         """Clear preheat status."""
#         self.preheat = False
#         self.preheat_set_time = None
#         self.preheat_last_time = None

#     def set_standby(self) -> None:
#         """Clear cooking status."""
#         self.cook_status = 'standby'
#         self.clear_preheat()
#         self.cook_last_time = None
#         self.current_temp = None
#         self.cook_set_time = None
#         self.cook_set_temp = None
#         self.last_timestamp = None

#     def status_response(self, return_status: dict) -> None:
#         """Set status of Air Fryer Based on API Response."""
#         self.last_timestamp = None
#         self.preheat = False
#         self.cook_status = return_status.get('cookStatus')
#         if self.cook_status == 'standby':
#             self.set_standby()
#             return

#         #  If drawer is pulled out, set standby if resp does not contain other details
#         if self.cook_status == 'pullOut':
#             self.last_timestamp = None
#             if 'currentTemp' not in return_status or 'tempUnit' not in return_status:
#                 self.set_standby()
#                 self.cook_status = 'pullOut'
#                 return
#         if return_status.get('preheatLastTime') is not None or self.cook_status in [
#             'heating',
#             'preheatStop',
#             'preheatEnd',
#         ]:
#             self.preheat = True

#         self.cook_set_time = return_status.get('cookSetTime', self.cook_set_time)
#         self.cook_last_time = return_status.get('cookLastTime')
#         self.current_temp = return_status.get('curentTemp')
#         self.cook_set_temp = return_status.get(
#             'targetTemp', return_status.get('cookSetTemp')
#         )
#         self.temp_unit = return_status.get(
#             'tempUnit',
#             self.temp_unit,  # type: ignore[assignment]
#         )
#         self.preheat_set_time = return_status.get('preheatSetTime')
#         self.preheat_last_time = return_status.get('preheatLastTime')

#         #  Set last_time timestamp if cooking
#         if self.cook_status in ['cooking', 'heating']:
#             self.last_timestamp = int(time.time())

#         if self.cook_status == 'preheatEnd':
#             self.preheat_last_time = 0
#             self.cook_last_time = None
#         if self.cook_status == 'cookEnd':
#             self.cook_last_time = 0

#         #  If Cooking, clear preheat status
#         if self.cook_status in ['cooking', 'cookStop', 'cookEnd']:
#             self.clear_preheat()


class VeSyncAirFryer158(BypassV1Mixin, VeSyncFryer):
    """Cosori Air Fryer Class.

    Args:
        details (ResponseDeviceDetailsModel): Device details.
        manager (VeSync): Manager class.
        feature_map (DeviceMapTemplate): Device feature map.

    Attributes:
        features (list[str]): List of features.
        state (FryerState): Air fryer state.
        last_update (int): Last update timestamp.
        refresh_interval (int): Refresh interval in seconds.
        cook_temps (dict[str, list[int]] | None): Cook temperatures.
        pid (str): PID for the device.
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
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
    """

    __slots__ = (
        'last_update',
        'ready_start',
        'refresh_interval',
    )

    request_keys: tuple[str, ...] = (*BypassV1Mixin.request_keys, 'pid')

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: AirFryerMap,
    ) -> None:
        """Init the VeSync Air Fryer 158 class."""
        super().__init__(details, manager, feature_map)
        self.features: list[str] = feature_map.features
        self.ready_start = True
        self.state: FryerState = FryerState(self, details, feature_map)
        if self.config_module not in AIRFRYER_PID_MAP:
            msg = (
                'Report this error as an issue - '
                f'{self.config_module} not found in PID map for {self.device_type}'
            )
            raise VeSyncError(msg)
        self.pid = AIRFRYER_PID_MAP[self.config_module]
        # self.request_keys = (
        #     'acceptLanguage',
        #     'accountID',
        #     'appVersion',
        #     'cid',
        #     'configModule',
        #     'deviceRegion',
        #     'phoneBrand',
        #     'phoneOS',
        #     'timeZone',
        #     'token',
        #     'traceId',
        #     'userCountryCode',
        #     'method',
        #     'debugMode',
        #     'uuid',
        #     'pid',
        # )

    @deprecated('There is no on/off function for Air Fryers.')
    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Turn on or off the air fryer."""
        return toggle if toggle is not None else not self.is_on

    # def _build_request(
    #     self,
    #     json_cmd: dict | None = None,
    #     method: str | None = None,
    # ) -> dict:
    #     """Return body of api calls."""
    #     req_dict = Helpers.get_defaultvalues_attributes(self.request_keys)
    #     req_dict.update(Helpers.get_manager_attributes(self.manager, self.request_keys))
    #     req_dict.update(Helpers.get_device_attributes(self, self.request_keys))
    #     req_dict['method'] = method or 'bypass'
    #     req_dict['jsonCmd'] = json_cmd or {}
    #     return req_dict

    # def _build_status_body(self, cmd_dict: dict) -> dict:
    #     """Return body of api calls."""
    #     body = self._build_request()
    #     body.update(
    #         {
    #             'uuid': self.uuid,
    #             'configModule': self.config_module,
    #             'jsonCmd': cmd_dict,
    #             'pid': self.pid,
    #             'accountID': self.manager.account_id,
    #         }
    #     )
    #     return body

    def _build_cook_request(
        self,
        cook_time: int,
        cook_temp: int,
        cook_status: str = 'cooking',
    ) -> dict[str, int | str | bool]:
        """Internal command to build cookMode API command."""
        cook_mode: dict[str, int | str | bool] = {}
        cook_mode['accountId'] = self.manager.account_id
        cook_mode['appointmentTs'] = 0
        cook_mode['cookSetTemp'] = cook_temp
        cook_mode['cookSetTime'] = cook_time
        cook_mode['cookStatus'] = cook_status
        cook_mode['customRecipe'] = 'Manual'
        cook_mode['mode'] = self.default_preset.cook_mode
        cook_mode['readyStart'] = True
        cook_mode['recipeId'] = self.default_preset.recipe_id
        cook_mode['recipeType'] = self.default_preset.recipe_type
        if self.temp_unit is not None:
            cook_mode['tempUnit'] = self.temp_unit.label
        else:
            cook_mode['tempUnit'] = 'fahrenheit'
        return cook_mode

    async def get_details(self) -> None:
        cmd = {'getStatus': 'status'}
        resp = await self.call_bypassv1_api(Fryer158RequestModel, update_dict=cmd)

        resp_model = process_bypassv1_result(
            self,
            logger,
            'get_details',
            resp,
            Fryer158Result,
        )

        if resp_model is None or resp_model.returnStatus is None:
            logger.debug('No returnStatus in get_details response for %s', self.device_name)
            self.state.set_standby()
            return None

        return_status = resp_model.returnStatus
        return self.state.set_state(
            cook_status=return_status.cookStatus,
            cook_time=return_status.cookSetTime,
            cook_temp=return_status.cookSetTemp,
            temp_unit=return_status.tempUnit,
            cook_mode=return_status.mode,
            preheat_time=return_status.preheatSetTime,
            current_temp=return_status.currentTemp,
        )

    async def end_cook(self, chamber: int = 1) -> bool:
        del chamber  # chamber not used for this air fryer
        cmd = {'cookMode': {'cookStatus': 'end'}}
        resp = await self.call_bypassv1_api(
            Fryer158RequestModel, update_dict={'jsonCmd': cmd}
        )
        if resp is None:
            logger.debug('No response from end command for %s', self.device_name)
            return False
        self.state.set_standby()
        return True

    async def end_preheat(self, chamber: int = 1) -> bool:
        del chamber  # chamber not used for this air fryer
        cmd = {'preheat': {'preheatStatus': 'end'}}
        resp = await self.call_bypassv1_api(
            Fryer158RequestModel, update_dict={'jsonCmd': cmd}
        )
        if resp is None:
            logger.debug('No response from end preheat command for %s', self.device_name)
            return False
        self.state.set_standby()
        return True

    async def end(self, chamber: int = 1) -> bool:
        del chamber  # chamber not used for this air fryer
        if self.state.is_in_cook_mode is True:
            cmd = {'cookMode': {'cookStatus': 'end'}}
        if self.state.is_in_preheat_mode is True:
            cmd = {'preheat': {'preheatStatus': 'end'}}
        else:
            logger.debug(
                'Cannot end %s as it is not cooking or preheating', self.device_name
            )
            return False
        json_cmd = {'jsonCmd': cmd}
        resp = await self.call_bypassv1_api(Fryer158RequestModel, update_dict=json_cmd)
        if resp is not None:
            self.state.set_standby()
            return True
        logger.warning('Error ending for %s', self.device_name)
        return False

    async def stop(self, chamber: int = 1) -> bool:
        del chamber  # chamber not used for this air fryer
        if self.state.is_in_preheat_mode is True:
            cmd = {'preheat': {'preheatStatus': 'stop'}}
        if self.state.is_in_cook_mode is True:
            cmd = {'cookMode': {'cookStatus': 'stop'}}
        else:
            logger.debug(
                'Cannot stop %s as it is not cooking or preheating', self.device_name
            )
            return False
        json_cmd = {'jsonCmd': cmd}
        resp = await self.call_bypassv1_api(
            Fryer158RequestModel, update_dict=json_cmd
        )
        if resp is not None:
            if self.state.is_in_preheat_mode is True:
                self.state.cook_status = AirFryerCookStatus.PREHEAT_STOP
            if self.state.is_in_cook_mode is True:
                self.state.cook_status = AirFryerCookStatus.COOK_STOP
            return True
        logger.warning('Error stopping for %s', self.device_name)
        return False

    async def resume(self, chamber: int = 1) -> bool:
        del chamber  # chamber not used for this air fryer
        if self.state.is_in_preheat_mode is True:
            cmd = {'preheat': {'preheatStatus': 'heating'}}
        if self.state.is_in_cook_mode is True:
            cmd = {'cookMode': {'cookStatus': 'cooking'}}
        else:
            logger.debug(
            'Cannot resume %s as it is not cooking or preheating', self.device_name
            )
        json_cmd = {'jsonCmd': cmd}
        resp = await self.call_bypassv1_api(
            Fryer158RequestModel, update_dict=json_cmd
        )
        if resp is not None:
            if self.state.is_in_preheat_mode is True:
                self.state.cook_status = AirFryerCookStatus.HEATING
            if self.state.is_in_cook_mode is True:
                self.state.cook_status = AirFryerCookStatus.COOKING
            return True
        logger.warning('Error resuming for %s', self.device_name)
        return False

    async def cook(self, set_temp: int, set_time: int) -> bool:
        """Set cook time and temperature in Minutes."""
        await self.check_status()
        if self._validate_temp(set_temp) is False:
            return False
        return await self._set_cook(set_temp, set_time)

    # async def resume(self) -> bool:
    #     """Resume paused preheat or cook."""
    #     await self.check_status()
    #     if self.state.cook_status not in ['preheatStop', 'cookStop']:
    #         logger.debug('Cannot resume %s as it is not paused', self.device_name)
    #         return False
    #     if self.state.is_in_preheat_mode is True:
    #         cmd = {'preheat': {'preheatStatus': 'heating'}}
    #     else:
    #         cmd = {'cookMode': {'cookStatus': 'cooking'}}
    #     status_api = await self._status_api(cmd)
    #     if status_api is True:
    #         if self.state.is_in_preheat_mode is True:
    #             self.state.cook_status = 'heating'
    #         else:
    #             self.state.cook_status = 'cooking'
    #         return True
    #     return False

    async def set_preheat(self, target_temp: int, cook_time: int) -> bool:
        """Set preheat mode with cooking time."""
        await self.check_status()
        if self.state.cook_status not in ['standby', 'cookEnd', 'preheatEnd']:
            logger.debug(
                'Cannot set preheat for %s as it is not in standby', self.device_name
            )
            return False
        if self._validate_temp(target_temp) is False:
            return False
        cmd = self._cmd_api_dict
        cmd['preheatSetTime'] = 5
        cmd['preheatStatus'] = 'heating'
        cmd['targetTemp'] = target_temp
        cmd['cookSetTime'] = cook_time
        json_cmd = {'preheat': cmd}
        return await self._status_api(json_cmd)

    async def cook_from_preheat(self) -> bool:
        """Start Cook when preheat has ended."""
        await self.check_status()
        if self.state.is_in_preheat_mode is False or self.state.cook_status != 'preheatEnd':
            logger.debug('Cannot start cook from preheat for %s', self.device_name)
            return False
        return await self._set_cook(status='cooking')

    async def update(self) -> None:
        """Update the device details."""
        await self.get_details()

    @property
    def _cmd_api_base(self) -> dict:
        """Return Base api dictionary for setting status."""
        return {
            'mode': COOK_MODE,
            'accountId': self.manager.account_id,
        }

    @property
    def _cmd_api_dict(self) -> dict:
        """Return API dictionary for setting status."""
        cmd = self._cmd_api_base
        cmd.update(
            {
                'appointmentTs': 0,
                'recipeId': RECIPE_ID,
                'readyStart': self.ready_start,
                'recipeType': RECIPE_TYPE,
                'customRecipe': CUSTOM_RECIPE,
            }
        )
        return cmd

    async def _set_cook(
        self,
        set_temp: int | None = None,
        set_time: int | None = None,
        status: str = 'cooking',
    ) -> bool:
        if set_temp is not None and set_time is not None:
            set_cmd = self._cmd_api_dict

            set_cmd['cookSetTime'] = set_time
            set_cmd['cookSetTemp'] = set_temp
        else:
            set_cmd = self._cmd_api_base
        set_cmd['cookStatus'] = status
        cmd = {'cookMode': set_cmd}
        return await self._status_api(cmd)

    async def _status_api(self, json_cmd: dict) -> bool:
        """Set API status with jsonCmd."""
        body = self._build_status_body(json_cmd)
        url = '/cloud/v1/deviceManaged/bypass'
        r_dict, _ = await self.manager.async_call_api(url, 'post', json_object=body)
        resp = Helpers.process_dev_response(logger, 'set_status', self, r_dict)
        if resp is None:
            return False

        self.last_update = int(time.time())
        self.state.status_request(json_cmd)
        await self.update()
        return True
