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
from pyvesync.const import AIRFRYER_PID_MAP, ConnectionStatus, DeviceStatus
from pyvesync.models.base_models import DefaultValues
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


class AirFryer158138State(FryerState):
    """Dataclass for air fryer status.

    Attributes:
        active_time (int): Active time of device, defaults to None.
        connection_status (str): Connection status of device.
        device (VeSyncBaseDevice): Device object.
        device_status (str): Device status.
        features (dict): Features of device.
        last_update_ts (int): Last update timestamp of device, defaults to None.
        ready_start (bool): Ready start status of device, defaults to False.
        preheat (bool): Preheat status of device, defaults to False.
        cook_status (str): Cooking status of device, defaults to None.
        current_temp (int): Current temperature of device, defaults to None.
        cook_set_temp (int): Cooking set temperature of device, defaults to None.
        last_timestamp (int): Last timestamp of device, defaults to None.
        preheat_set_time (int): Preheat set time of device, defaults to None.
        preheat_last_time (int): Preheat last time of device, defaults to None.
        _temp_unit (str): Temperature unit of device, defaults to None.
    """

    __slots__ = (
        '_temp_unit',
        'cook_last_time',
        'cook_set_temp',
        'cook_set_time',
        'cook_status',
        'current_temp',
        'last_timestamp',
        'max_temp_c',
        'max_temp_f',
        'min_temp_c',
        'min_temp_f',
        'preheat',
        'preheat_last_time',
        'preheat_set_time',
        'ready_start',
    )

    def __init__(
        self,
        device: VeSyncAirFryer158,
        details: ResponseDeviceDetailsModel,
        feature_map: AirFryerMap,
    ) -> None:
        """Init the Air Fryer 158 class."""
        super().__init__(device, details, feature_map)
        self.device: VeSyncFryer = device
        self.features: list[str] = feature_map.features
        self.min_temp_f: int = feature_map.temperature_range_f[0]
        self.max_temp_f: int = feature_map.temperature_range_f[1]
        self.min_temp_c: int = feature_map.temperature_range_c[0]
        self.max_temp_c: int = feature_map.temperature_range_c[1]
        self.ready_start: bool = False
        self.preheat: bool = False
        self.cook_status: str | None = None
        self.current_temp: int | None = None
        self.cook_set_temp: int | None = None
        self.cook_set_time: int | None = None
        self.cook_last_time: int | None = None
        self.last_timestamp: int | None = None
        self.preheat_set_time: int | None = None
        self.preheat_last_time: int | None = None
        self._temp_unit: str | None = None

    @property
    def is_resumable(self) -> bool:
        """Return if cook is resumable."""
        if self.cook_status in ['cookStop', 'preheatStop']:
            if self.cook_set_time is not None:
                return self.cook_set_time > 0
            if self.preheat_set_time is not None:
                return self.preheat_set_time > 0
        return False

    @property
    def temp_unit(self) -> str | None:
        """Return temperature unit."""
        return self._temp_unit

    @temp_unit.setter
    def temp_unit(self, temp_unit: str) -> None:
        """Set temperature unit."""
        if temp_unit.lower() in ['f', 'fahrenheit', 'fahrenheight']:  # API TYPO
            self._temp_unit = 'fahrenheit'
        elif temp_unit.lower() in ['c', 'celsius']:
            self._temp_unit = 'celsius'
        else:
            msg = f'Invalid temperature unit - {temp_unit}'
            raise ValueError(msg)

    @property
    def preheat_time_remaining(self) -> int:
        """Return preheat time remaining."""
        if self.preheat is False or self.cook_status == 'preheatEnd':
            return 0
        if self.cook_status in ['pullOut', 'preheatStop']:
            if self.preheat_last_time is None:
                return 0
            return int(self.preheat_last_time // 60)
        if self.preheat_last_time is not None and self.last_timestamp is not None:
            return int(
                max(
                    (self.preheat_last_time - (int(time.time()) - self.last_timestamp))
                    // 60,
                    0,
                )
            )
        return 0

    @property
    def cook_time_remaining(self) -> int:
        """Returns the amount of time remaining if cooking."""
        if self.preheat is True or self.cook_status == 'cookEnd':
            return 0
        if self.cook_status in ['pullOut', 'cookStop']:
            if self.cook_last_time is None:
                return 0
            return int(max(self.cook_last_time // 60, 0))
        if self.cook_last_time is not None and self.last_timestamp is not None:
            return int(
                max(
                    (self.cook_last_time - (int(time.time()) - self.last_timestamp))
                    // 60,
                    0,
                )
            )
        return 0

    @property
    def remaining_time(self) -> int:
        """Return minutes remaining if cooking/heating."""
        if self.preheat is True:
            return self.preheat_time_remaining
        return self.cook_time_remaining

    @property
    def is_running(self) -> bool:
        """Return if cooking or heating."""
        return bool(self.cook_status in ['cooking', 'heating']) and bool(
            self.remaining_time > 0
        )

    @property
    def is_cooking(self) -> bool:
        """Return if cooking."""
        return self.cook_status == 'cooking' and self.remaining_time > 0

    @property
    def is_heating(self) -> bool:
        """Return if heating."""
        return self.cook_status == 'heating' and self.remaining_time > 0

    def status_request(self, json_cmd: dict) -> None:  # noqa: C901
        """Set status from jsonCmd of API call."""
        self.last_timestamp = None
        if not isinstance(json_cmd, dict):
            return
        self.preheat = False
        preheat = json_cmd.get('preheat')
        cook = json_cmd.get('cookMode')
        if isinstance(preheat, dict):
            self.preheat = True
            if preheat.get('preheatStatus') == 'stop':
                self.cook_status = 'preheatStop'
            elif preheat.get('preheatStatus') == 'heating':
                self.cook_status = 'heating'
                self.last_timestamp = int(time.time())
                self.preheat_set_time = preheat.get(
                    'preheatSetTime', self.preheat_set_time
                )
                if preheat.get('preheatSetTime') is not None:
                    self.preheat_last_time = preheat.get('preheatSetTime')
                self.cook_set_temp = preheat.get('targetTemp', self.cook_set_temp)
                self.cook_set_time = preheat.get('cookSetTime', self.cook_set_time)
                self.cook_last_time = None
            elif preheat.get('preheatStatus') == 'end':
                self.cook_status = 'preheatEnd'
                self.preheat_last_time = 0
        elif isinstance(cook, dict):
            self.clear_preheat()
            if cook.get('cookStatus') == 'stop':
                self.cook_status = 'cookStop'
            elif cook.get('cookStatus') == 'cooking':
                self.cook_status = 'cooking'
                self.last_timestamp = int(time.time())
                self.cook_set_time = cook.get('cookSetTime', self.cook_set_time)
                self.cook_set_temp = cook.get('cookSetTemp', self.cook_set_temp)
                self.current_temp = cook.get('currentTemp', self.current_temp)
                self.temp_unit = cook.get(
                    'tempUnit',
                    self.temp_unit,  # type: ignore[assignment]
                )
            elif cook.get('cookStatus') == 'end':
                self.set_standby()
                self.cook_status = 'cookEnd'

    def clear_preheat(self) -> None:
        """Clear preheat status."""
        self.preheat = False
        self.preheat_set_time = None
        self.preheat_last_time = None

    def set_standby(self) -> None:
        """Clear cooking status."""
        self.cook_status = 'standby'
        self.clear_preheat()
        self.cook_last_time = None
        self.current_temp = None
        self.cook_set_time = None
        self.cook_set_temp = None
        self.last_timestamp = None

    def status_response(self, return_status: dict) -> None:
        """Set status of Air Fryer Based on API Response."""
        self.last_timestamp = None
        self.preheat = False
        self.cook_status = return_status.get('cookStatus')
        if self.cook_status == 'standby':
            self.set_standby()
            return

        #  If drawer is pulled out, set standby if resp does not contain other details
        if self.cook_status == 'pullOut':
            self.last_timestamp = None
            if 'currentTemp' not in return_status or 'tempUnit' not in return_status:
                self.set_standby()
                self.cook_status = 'pullOut'
                return
        if return_status.get('preheatLastTime') is not None or self.cook_status in [
            'heating',
            'preheatStop',
            'preheatEnd',
        ]:
            self.preheat = True

        self.cook_set_time = return_status.get('cookSetTime', self.cook_set_time)
        self.cook_last_time = return_status.get('cookLastTime')
        self.current_temp = return_status.get('curentTemp')
        self.cook_set_temp = return_status.get(
            'targetTemp', return_status.get('cookSetTemp')
        )
        self.temp_unit = return_status.get(
            'tempUnit',
            self.temp_unit,  # type: ignore[assignment]
        )
        self.preheat_set_time = return_status.get('preheatSetTime')
        self.preheat_last_time = return_status.get('preheatLastTime')

        #  Set last_time timestamp if cooking
        if self.cook_status in ['cooking', 'heating']:
            self.last_timestamp = int(time.time())

        if self.cook_status == 'preheatEnd':
            self.preheat_last_time = 0
            self.cook_last_time = None
        if self.cook_status == 'cookEnd':
            self.cook_last_time = 0

        #  If Cooking, clear preheat status
        if self.cook_status in ['cooking', 'cookStop', 'cookEnd']:
            self.clear_preheat()


class VeSyncAirFryer158(VeSyncFryer):
    """Cosori Air Fryer Class.

    Args:
        details (ResponseDeviceDetailsModel): Device details.
        manager (VeSync): Manager class.
        feature_map (DeviceMapTemplate): Device feature map.

    Attributes:
        features (list[str]): List of features.
        state (AirFryer158138State): Air fryer state.
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
        'cook_temps',
        'fryer_status',
        'last_update',
        'ready_start',
        'refresh_interval',
    )

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: AirFryerMap,
    ) -> None:
        """Init the VeSync Air Fryer 158 class."""
        super().__init__(details, manager, feature_map)
        self.features: list[str] = feature_map.features
        self.state: AirFryer158138State = AirFryer158138State(self, details, feature_map)
        self.last_update: int = int(time.time())
        self.refresh_interval = 0
        self.ready_start = False
        self.cook_temps: dict[str, list[int]] | None = None
        if self.config_module not in AIRFRYER_PID_MAP:
            msg = (
                'Report this error as an issue - '
                f'{self.config_module} not found in PID map for {self}'
            )
            raise VeSyncError(msg)
        self.pid = AIRFRYER_PID_MAP[self.config_module]
        self.request_keys = [
            'acceptLanguage',
            'accountID',
            'appVersion',
            'cid',
            'configModule',
            'deviceRegion',
            'phoneBrand',
            'phoneOS',
            'timeZone',
            'token',
            'traceId',
            'userCountryCode',
            'method',
            'debugMode',
            'uuid',
            'pid',
        ]

    @deprecated('There is no on/off function for Air Fryers.')
    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Turn on or off the air fryer."""
        return toggle if toggle is not None else not self.is_on

    def _build_request(
        self,
        json_cmd: dict | None = None,
        method: str | None = None,
    ) -> dict:
        """Return body of api calls."""
        req_dict = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        req_dict.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        req_dict.update(Helpers.get_class_attributes(self, self.request_keys))
        req_dict['method'] = method or 'bypass'
        req_dict['jsonCmd'] = json_cmd or {}
        return req_dict

    def _build_status_body(self, cmd_dict: dict) -> dict:
        """Return body of api calls."""
        body = self._build_request()
        body.update(
            {
                'uuid': self.uuid,
                'configModule': self.config_module,
                'jsonCmd': cmd_dict,
                'pid': self.pid,
                'accountID': self.manager.account_id,
            }
        )
        return body

    @property
    def temp_unit(self) -> str | None:
        """Return temp unit."""
        return self.state.temp_unit

    async def get_details(self) -> None:
        """Get Air Fryer Status and Details."""
        cmd = {'getStatus': 'status'}
        req_body = self._build_request(json_cmd=cmd)
        url = '/cloud/v1/deviceManaged/bypass'
        r_dict, _ = await self.manager.async_call_api(url, 'post', json_object=req_body)
        resp = Helpers.process_dev_response(logger, 'get_details', self, r_dict)
        if resp is None:
            self.state.device_status = DeviceStatus.OFF
            self.state.connection_status = ConnectionStatus.OFFLINE
            return

        return_status = resp.get('result', {}).get('returnStatus')
        if return_status is None:
            LibraryLogger.log_device_api_response_error(
                logger,
                self.device_name,
                self.device_type,
                'get_details',
                msg='Return status not found in response',
            )
            return
        self.state.status_response(return_status)

    async def check_status(self) -> None:
        """Update status if REFRESH_INTERVAL has passed."""
        seconds_elapsed = int(time.time()) - self.last_update
        logger.debug('Seconds elapsed between updates: %s', seconds_elapsed)
        refresh = False
        if self.refresh_interval is None:
            refresh = bool(seconds_elapsed > REFRESH_INTERVAL)
        elif self.refresh_interval == 0:
            refresh = True
        elif self.refresh_interval > 0:
            refresh = bool(seconds_elapsed > self.refresh_interval)
        if refresh is True:
            logger.debug('Updating status, %s seconds elapsed', seconds_elapsed)
            await self.update()

    async def end(self) -> bool:
        """End the cooking process."""
        await self.check_status()
        if self.state.preheat is False and self.state.cook_status in [
            'cookStop',
            'cooking',
        ]:
            cmd = {'cookMode': {'cookStatus': 'end'}}
        elif self.state.preheat is True and self.state.cook_status in [
            'preheatStop',
            'heating',
        ]:
            cmd = {'preheat': {'cookStatus': 'end'}}
        else:
            logger.debug(
                'Cannot end %s as it is not cooking or preheating', self.device_name
            )
            return False

        status_api = await self._status_api(cmd)
        if status_api is False:
            return False
        self.state.set_standby()
        return True

    async def pause(self) -> bool:
        """Pause the cooking process."""
        await self.check_status()
        if self.state.cook_status not in ['cooking', 'heating']:
            logger.debug(
                'Cannot pause %s as it is not cooking or preheating', self.device_name
            )
            return False
        if self.state.preheat is True:
            cmd = {'preheat': {'preheatStatus': 'stop'}}
        else:
            cmd = {'cookMode': {'cookStatus': 'stop'}}
        status_api = await self._status_api(cmd)
        if status_api is True:
            if self.state.preheat is True:
                self.state.cook_status = 'preheatStop'
            else:
                self.state.cook_status = 'cookStop'
            return True
        return False

    def _validate_temp(self, set_temp: int) -> bool:
        """Temperature validation."""
        if self.state.temp_unit == 'fahrenheit' and (
            set_temp < self.state.min_temp_f or set_temp > self.state.max_temp_f
        ):
            logger.debug('Invalid temperature %s for %s', set_temp, self.device_name)
            return False
        if self.state.temp_unit == 'celsius' and (
            set_temp < self.state.min_temp_c or set_temp > self.state.max_temp_c
        ):
            logger.debug('Invalid temperature %s for %s', set_temp, self.device_name)
            return False
        return True

    async def cook(self, set_temp: int, set_time: int) -> bool:
        """Set cook time and temperature in Minutes."""
        await self.check_status()
        if self._validate_temp(set_temp) is False:
            return False
        return await self._set_cook(set_temp, set_time)

    async def resume(self) -> bool:
        """Resume paused preheat or cook."""
        await self.check_status()
        if self.state.cook_status not in ['preheatStop', 'cookStop']:
            logger.debug('Cannot resume %s as it is not paused', self.device_name)
            return False
        if self.state.preheat is True:
            cmd = {'preheat': {'preheatStatus': 'heating'}}
        else:
            cmd = {'cookMode': {'cookStatus': 'cooking'}}
        status_api = await self._status_api(cmd)
        if status_api is True:
            if self.state.preheat is True:
                self.state.cook_status = 'heating'
            else:
                self.state.cook_status = 'cooking'
            return True
        return False

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
        if self.state.preheat is False or self.state.cook_status != 'preheatEnd':
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
