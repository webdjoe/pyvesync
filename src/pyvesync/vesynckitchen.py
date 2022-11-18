"""VeSync Kitchen Devices."""
import json
import logging
import time
from typing import Optional, Union
from dataclasses import dataclass
from pyvesync.vesyncbasedevice import VeSyncBaseDevice
from pyvesync.helpers import Helpers as helpers

logger = logging.getLogger(__name__)


kitchen_features: dict = {
    'CS137-AF/CS158-AF': {
        'module': 'VeSyncAirFryer158',
        'features': [],
    }
}

kitchen_modules: dict = {k: v['module'] for k, v in kitchen_features.items()}


RECIPE_ID = 1
RECIPE_TYPE = 3
CUSTOM_RECIPE = 'Manual Cook'
COOK_MODE = 'custom'


@dataclass(init=False, eq=False, repr=False)
class FryerStatus:
    """Dataclass for air fryer status."""

    ready_start: bool = False
    preheat: bool = False
    cook_status: Optional[str] = None
    current_temp: Optional[int] = None
    cook_set_temp: Optional[int] = None
    cook_set_time: Optional[int] = None
    cook_last_time: Optional[int] = None
    last_timestamp: Optional[int] = None
    preheat_set_time: Optional[int] = None
    preheat_last_time: Optional[int] = None
    _temp_unit: Optional[str] = None

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
    def temp_unit(self) -> Optional[str]:
        """Return temperature unit."""
        return self._temp_unit

    @temp_unit.setter
    def temp_unit(self, temp_unit: str):
        """Set temperature unit."""
        if temp_unit.lower() in ['f', 'fahrenheit']:
            self._temp_unit = 'fahrenheit'
        elif temp_unit.lower() in ['c', 'celsius']:
            self._temp_unit = 'celsius'
        else:
            raise ValueError(f'Invalid temperature unit - {temp_unit}')

    @property
    def remaining_time(self):
        """Return minutes remaining if cooking/heating."""
        if self.cook_status == 'cooking' and self.last_timestamp is not None:
            remaining = self.cook_last_time - (int(time.time())
                                               - self.last_timestamp) // 60
        elif self.cook_status == 'heating' and self.last_timestamp is not None:
            remaining = self.preheat_last_time - (int(time.time())
                                                  - self.last_timestamp) // 60
        elif self.cook_status == 'cookStop' and self.last_timestamp is not None:
            remaining = self.cook_last_time
        elif self.cook_status == 'preheatStop' and self.last_timestamp is not None:
            remaining = self.preheat_last_time
        else:
            return None
        return remaining if remaining > 0 else 0

    @property
    def is_running(self) -> bool:
        """Return if cooking or heating."""
        return (self.cook_status in ['cooking', 'heating']) \
            and (self.remaining_time > 0)

    @property
    def is_cooking(self) -> bool:
        """Return if cooking."""
        return self.cook_status == 'cooking' and self.remaining_time > 0

    @property
    def is_heating(self) -> bool:
        """Return if heating."""
        return self.cook_status == 'heating' and self.remaining_time > 0

    @property
    def in_session(self) -> bool:
        """Return if in session."""
        return self.cook_status is not None

    def status_request(self, json_cmd: dict):
        """Set status from jsonCmd of API call."""
        if not isinstance(json_cmd, dict):
            return
        self.preheat = False
        preheat = json_cmd.get('preheat')
        cook = json_cmd.get('cookMode')
        if isinstance(preheat, dict):
            self.cook_last_time = None
            if preheat.get('preheatStatus') == 'stop':
                self.preheat = True
                self.cook_status = 'preheatStop'
                self.last_timestamp = None
            elif preheat.get('preheatStatus') == 'heating':
                self.cook_status = 'heating'
                self.last_timestamp = int(time.time())
                self.preheat_set_time = preheat.get('preheatSetTime',
                                                    self.preheat_set_time)
                self.preheat_last_time = self.preheat_set_time
                self.cook_set_temp = preheat.get('targetTemp', self.cook_set_temp)
                self.cook_set_time = preheat.get('cookSetTime')
            elif preheat.get('preheatStatus') == 'end':
                self.set_standby()

        elif isinstance(cook, dict):
            self.clear_preheat()
            if cook.get('cookStatus') == 'stop':
                self.cook_status = 'cookStop'
                self.last_timestamp = None
            elif cook.get('cookStatus') == 'cooking':
                self.cook_status = 'cooking'
                self.last_timestamp = int(time.time())
                self.cook_set_time = cook.get('cookSetTime', self.cook_set_time)
                self.cook_last_time = cook.get('cookLastTime', self.cook_last_time)
                self.cook_set_temp = cook.get('cookSetTemp', self.cook_set_temp)
                self.current_temp = cook.get('currentTemp', self.current_temp)
                self.temp_unit = cook.get('tempUnit', self.temp_unit)
            elif cook.get('cookStatus') == 'end':
                self.set_standby()

    def clear_preheat(self):
        """Clear preheat status."""
        self.preheat = False
        self.preheat_set_time = None
        self.preheat_last_time = None

    def set_standby(self):
        """Clear cooking status."""
        self.cook_status = 'standby'
        self.clear_preheat()
        self.cook_last_time = None
        self.cook_set_time = None
        self.cook_set_temp = None
        self.last_timestamp = None

    def status_response(self, return_status: dict) -> None:
        """Set status of Air Fryer Based on API Response."""
        self.cook_status = return_status.get('cookStatus')
        if self.cook_status == 'standby':
            self.set_standby()

        #  If drawer is pulled out, set standby if resp does not contain other details
        if self.cook_status == 'pullOut':
            self.last_timestamp = None
            if 'currentTemp' not in return_status or 'tempUnit' not in return_status:
                self.set_standby()
                return

        #  Set preheat if appropriate
        if self.cook_status in ['heating', 'preheatStop']:
            self.preheat = True

        self.current_temp = return_status.get('curentTemp')
        self.cook_set_temp = return_status.get('targetTemp',
                                               return_status.get('cookSetTemp'))
        self.temp_unit = return_status.get('tempUnit', self.temp_unit)  # Always keep set
        self.preheat_set_time = return_status.get('preheatSetTime')
        self.preheat_last_time = return_status.get('preheatLastTime')

        #  Set last_time timestamp if cooking
        if self.cook_status in ['cooking', 'heating']:
            self.last_timestamp = int(time.time())

        #  If Cooking, clear preheat status
        if self.cook_status in ['cooking', 'cookStop']:
            self.clear_preheat()


class VeSyncAirFryer158(VeSyncBaseDevice):
    """Cosori Air Fryer Class."""

    def __init__(self, details, manager):
        """Init the VeSync Air Fryer 158 class."""
        super().__init__(details, manager)
        self.fryer_status = FryerStatus()

        if self.pid is None:
            self.get_pid()
        self.fryer_status.temp_unit = self.get_temp_unit()
        self.ready_start = self.get_remote_cook_mode()

    def get_body(self, method: str = None) -> dict:
        """Return body of api calls."""
        body = {
            **helpers.req_body(self.manager, 'bypass'),
            'cid': self.cid,
            'userCountryCode': self.manager.country_code,
            'debugMode': False
        }
        if method is not None:
            body['method'] = method
        return body

    def get_status_body(self, cmd_dict: dict) -> dict:
        """Return body of api calls."""
        body = self.get_body()
        body.update({
            'uuid': self.uuid,
            'configModule': self.config_module,
            'jsonCmd': cmd_dict,
            'pid': self.pid,
            'accountID': self.manager.account_id
            }
        )
        return body

    def get_temp_unit(self):
        """Get Air Fryer Configuration."""
        body = self.get_body('configurationsV2')

        r, _ = helpers.call_api('/cloud/v2/deviceManaged/configurationsV2', 'post',
                                json_object=body)
        if not isinstance(r, dict) or r.get('code') != 0 \
                or not isinstance(r.get('result'), dict):
            logger.debug('Failed to get config for %s', self.device_name)
            return
        result = r.get('result')
        if result is not None:
            return result.get('airFryerInfo', {}).get('workTempUnit', 'f')

    def get_remote_cook_mode(self):
        """Get the cook mode."""
        body = self.get_body('getRemoteCookMode158')
        r, _ = helpers.call_api('/cloud/v1/deviceManaged/getRemoteCookMode158',
                                'post',
                                json_object=body)
        if not isinstance(r, dict) or r.get('code') != 0 \
                or not isinstance(r.get('result'), dict):
            return False
        return r.get('result', {}).get('cookMode')

    @property
    def temp_unit(self) -> Optional[str]:
        """Return temp unit."""
        return self.fryer_status.temp_unit

    @property
    def current_temp(self) -> Optional[int]:
        """Return current temperature."""
        return self.fryer_status.current_temp

    @property
    def cook_set_temp(self) -> Optional[int]:
        """Return set temperature."""
        return self.fryer_status.cook_set_temp

    @property
    def preheat(self) -> bool:
        """Return preheat status."""
        return self.fryer_status.preheat

    @property
    def cook_last_time(self) -> Optional[int]:
        """Return cook last time."""
        return self.fryer_status.cook_last_time

    @property
    def cook_set_time(self) -> Optional[int]:
        """Return cook set time."""
        return self.fryer_status.cook_set_time

    @property
    def preheat_last_time(self) -> Optional[int]:
        """Return preheat last time."""
        if self.preheat is True:
            return self.fryer_status.preheat_last_time
        logger.debug("Air fryer not preheating")
        return None

    @property
    def preheat_set_time(self) -> Optional[int]:
        """Return preheat set time."""
        if self.preheat is True:
            return self.fryer_status.preheat_set_time
        logger.debug("Air fryer not preheating")
        return None

    @property
    def cook_status(self) -> Optional[str]:
        """Return the cook status."""
        return self.fryer_status.cook_status

    @property
    def is_cooking(self) -> bool:
        """Return True if air fryer is heating."""
        return self.fryer_status.is_cooking

    @property
    def is_heating(self) -> bool:
        """Return True if air fryer is preheating."""
        return self.fryer_status.is_heating

    @property
    def is_running(self):
        """Return True if cooking or preheating finished."""
        return self.fryer_status.is_running

    @property
    def remaining_time(self) -> Optional[int]:
        """Return time remaining in minutes or None if not cooking/heating."""
        return self.fryer_status.remaining_time

    def get_details(self):
        """Get Air Fryer Status and Details."""
        cmd = {'getStatus': 'status'}
        req_body = self.get_status_body(cmd)
        url = '/cloud/v1/deviceManaged/bypass'
        resp, _ = helpers.call_api(url, 'post', json_object=req_body)

        if resp is None:
            logger.debug('Failed to get details for %s', self.device_name)
            return False
        if resp.get('code') == -11300030:
            logger.debug('%s is offline', self.device_name)
            self.fryer_status.set_standby()
            self.fryer_status.cook_status = 'offline'
            return False
        if resp.get('code') != 0:
            logger.debug('Failed to get details for %s \n with code: %s and message: %s',
                         self.device_name, str(resp.get("code", 0)), resp.get("msg", ''))
            return False
        return_status = resp.get('result', {}).get('returnStatus')
        if return_status is None:
            return False
        self.fryer_status.status_response(return_status)
        return True

    def end(self):
        """End the cooking process."""
        if self.preheat is False \
                and self.fryer_status.cook_status in ['cookStop', 'cooking']:
            cmd = {
                'cookMode': {
                    'cookStatus': 'end'
                }
            }
        elif self.preheat is False \
                and self.fryer_status.cook_status in ['preheatStop', 'heating']:
            cmd = {
                'preheat': {
                    'cookStatus': 'end'
                }
            }
        else:
            logger.debug('Cannot end %s as it is not cooking or preheating',
                         self.device_name)
            return False

        if self._status_api(cmd) is True:
            self.fryer_status.set_standby()
            return True
        return False

    def pause(self) -> bool:
        """Pause the cooking process."""
        if self.cook_status not in ['cooking', 'heating']:
            logger.debug('Cannot pause %s as it is not cooking or preheating',
                         self.device_name)
            return False
        if self.preheat is True:
            cmd = {
                'preheat': {
                    'preheatStatus': 'stop'
                }
            }
        else:
            cmd = {
                'cookMode': {
                    'cookStatus': 'pause'
                }
            }
        if self._status_api(cmd) is True:
            if self.preheat is True:
                self.fryer_status.cook_status = 'preheatStop'
            else:
                self.fryer_status.cook_status = 'cookStop'
            return True
        return False

    def _validate_temp(self, set_temp: int) -> bool:
        """Temperature validation."""
        if self.fryer_status.temp_unit == 'fahrenheight':
            if set_temp < 200 or set_temp > 400:
                logger.debug('Invalid temperature %s for %s', set_temp, self.device_name)
                return False
        if self.fryer_status.temp_unit == 'celsius':
            if set_temp < 75 or set_temp > 205:
                logger.debug('Invalid temperature %s for %s', set_temp, self.device_name)
                return False
        return True

    def cook(self, set_temp: int, set_time: int) -> bool:
        """Set cook time and temperature in Minutes."""
        if self._validate_temp(set_temp) is False:
            return False
        return self._set_cook(set_temp, set_time)

    def resume(self) -> bool:
        """Resume paused preheat or cook."""
        if self.cook_status not in ['preheatStop', 'cookStop']:
            logger.debug('Cannot resume %s as it is not paused', self.device_name)
            return False
        if self.preheat is True:
            cmd = {
                'preheat': {
                    'preheatStatus': 'heating'
                }
            }
        else:
            cmd = {
                'cookMode': {
                    'cookStatus': 'cooking'
                }
            }
        if self._status_api(cmd) is True:
            if self.preheat is True:
                self.fryer_status.cook_status = 'heating'
            else:
                self.fryer_status.cook_status = 'cooking'
            return True
        return False

    def set_preheat(self, target_temp: int, cook_time: int) -> bool:
        """Set preheat mode with cooking time."""
        if self.cook_status not in ['standby', 'cookEnd', 'preheatEnd']:
            logger.debug('Cannot set preheat for %s as it is not in standby',
                         self.device_name)
            return False
        if self._validate_temp(target_temp) is False:
            return False
        cmd = self._cmd_api_dict
        cmd['preheatSetTime'] = 5
        cmd['preheatStatus'] = 'heating'
        cmd['targetTemp'] = target_temp
        cmd['cookSetTime'] = cook_time
        json_cmd = {
            'preheat': cmd
        }
        return self._status_api(json_cmd)

    def cook_from_preheat(self) -> bool:
        """Start Cook when preheat has ended."""
        if self.preheat is False or self.cook_status != 'preheatEnd':
            logger.debug('Cannot start cook from preheat for %s', self.device_name)
            return False
        return self._set_cook(status='cooking')

    def update(self):
        """Update the device details."""
        self.get_details()

    @staticmethod
    def fryer_code_check(code: Union[str, int]) -> Optional[str]:
        """Return the code description."""
        if isinstance(code, str):
            try:
                code = int(code)
            except ValueError:
                return None
        if code == 11903000:
            return 'Error pausing, air fryer is not cooking.'
        if code == 11902000:
            return 'Error setting cook mode, air fryer is already cooking'
        if str(abs(code))[0:5] == 11300:
            return 'Air fryer is offline'
        return None

    @property
    def _cmd_api_base(self) -> dict:
        """Return Base api dictionary for setting status."""
        return {
            "mode": COOK_MODE,
            "accountId": self.manager.account_id,
        }

    @property
    def _cmd_api_dict(self) -> dict:
        """Return API dictionary for setting status."""
        cmd = self._cmd_api_base
        cmd.update({
            "appointmentTs": 0,
            "recipeId": RECIPE_ID,
            "readyStart": self.ready_start,
            "recipeType": RECIPE_TYPE,
            "customRecipe": CUSTOM_RECIPE,
        })
        return cmd

    def _set_cook(self, set_temp: int = None, set_time: int = None,
                  status: str = 'cooking') -> bool:
        if set_temp is not None and set_time is not None:
            set_cmd = self._cmd_api_dict

            set_cmd['cookSetTime'] = set_time
            set_cmd['cookSetTemp'] = set_temp
        else:
            set_cmd = self._cmd_api_base
        set_cmd['cookStatus'] = status
        cmd = {'cookMode': set_cmd}
        return self._status_api(cmd)

    def _status_api(self, json_cmd: dict):
        """Set API status with jsonCmd."""
        body = self.get_status_body(json_cmd)
        url = '/cloud/v1/deviceManaged/bypass'
        resp, _ = helpers.call_api(url, 'post', json_object=body)
        if resp is None:
            logger.debug('Failed to set status for %s - No response from API',
                         self.device_name)
            return False

        if resp.get('code') != 0 and resp.get('code') is not None:
            debug_msg = self.fryer_code_check(resp.get('code'))
            logger.debug('Failed to set status for %s \n Code: %s and message: %s \n'
                         ' %s', self.device_name, resp.get("code"),
                         resp.get("msg"), debug_msg)
            return False
        self.fryer_status.status_request(json_cmd)
        return True

    def displayJSON(self) -> str:
        """Display JSON of device details."""
        sup = super().displayJSON()
        sup_dict = json.loads(sup)
        sup_dict['cook_status'] = self.cook_status
        sup_dict['temp_unit'] = self.temp_unit

        if self.cook_status not in ['standby', 'cookEnd', 'preheatEnd']:
            status_dict = {
                'preheat': self.preheat,
                'current_temp': self.current_temp,
                'cook_set_temp': self.cook_set_temp,
                'cook_set_time': self.cook_set_time,
                'cook_last_time': self.cook_last_time
            }
            if self.preheat is True:
                preheat_dict = {
                    'preheat_last_time': self.preheat_last_time,
                    'preheat_set_time': self.preheat_set_time
                }
                status_dict.update(preheat_dict)
            sup_dict.update(status_dict)
        return json.dumps(sup_dict, indent=4)
