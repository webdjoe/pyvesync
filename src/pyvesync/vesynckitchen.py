"""VeSync Kitchen Devices."""
import json
import logging
import time
import sys
from functools import wraps
from typing import Optional, Union
from dataclasses import dataclass
from .vesyncbasedevice import VeSyncBaseDevice
from .helpers import (
    Helpers, EConfig, EDeviceFamily,
    ERR_REQ_TIMEOUTS, DEVICE_CONFIGS_T,
    build_model_dict
)

logger = logging.getLogger(__name__)

module_kitchen = sys.modules[__name__]

# --8<-- [start:kitchen_configs]
kitchen_configs: DEVICE_CONFIGS_T = {
    'Cosori3758L': {
        EConfig.CLASS: 'VeSyncAirFryer158',
        EConfig.MODELS: ['CS137-AF/CS158-AF', 'CS158-AF', 'CS137-AF', 'CS358-AF'],
        EConfig.FEATURES: [],
    }
}
# --8<-- [end:kitchen_configs]

kitchen_classes = build_model_dict(kitchen_configs, EConfig.CLASS)
kitchen_features = build_model_dict(kitchen_configs, EConfig.FEATURES)

__all__: list = [
    *kitchen_classes.values(),
    'kitchen_classes', 'kitchen_classes', 'FryerStatus', 'VeSyncKitchen'
]


# Status refresh interval in seconds
# API calls outside of interval are automatically refreshed
# Set VeSyncAirFryer158.refresh_interval to 0 to refresh every call
# Set to None or -1 to disable auto-refresh
REFRESH_INTERVAL = 60

RECIPE_ID = 1
RECIPE_TYPE = 3
CUSTOM_RECIPE = 'Manual Cook'
COOK_MODE = 'custom'


def check_status(func):
    """Check interval between updates."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        seconds_elapsed = int(time.time()) - self.last_update
        logger.debug("Seconds elapsed between updates: %s", seconds_elapsed)
        refresh = False
        if self.refresh_interval is None:
            refresh = bool(seconds_elapsed > REFRESH_INTERVAL)
        elif self.refresh_interval == 0:
            refresh = True
        elif self.refresh_interval > 0:
            refresh = bool(seconds_elapsed > self.refresh_interval)
        if refresh is True:
            logger.debug("Updating status, %s seconds elapsed", seconds_elapsed)
            self.update()
        return func(self, *args, **kwargs)
    return wrapper


@dataclass(init=False, eq=False, repr=False)
class FryerStatus:
    """Dataclass for air fryer status."""

    ready_start: bool = False
    preheat: bool = False
    cook_status: str = ''
    current_temp: Optional[int] = None
    cook_set_temp: Optional[int] = None
    cook_set_time: Optional[int] = None
    cook_last_time: Optional[int] = None
    last_timestamp: Optional[int] = None
    preheat_set_time: Optional[int] = None
    preheat_last_time: Optional[int] = None
    _temp_unit: str = '°C'

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
    def temp_unit(self) -> str:
        """Return temperature unit."""
        return self._temp_unit

    @temp_unit.setter
    def temp_unit(self, temp_unit: str):
        """Set temperature unit."""
        if temp_unit.lower() in ['f', 'fahrenheit']:
            self._temp_unit = '°F'
        elif temp_unit.lower() in ['c', 'celsius']:
            self._temp_unit = '°C'
        else:
            self._temp_unit = '°C'
            raise ValueError(f'Invalid temperature unit - {temp_unit}')

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
            return int(max((self.preheat_last_time -
                            (int(time.time()) - self.last_timestamp)) // 60, 0))
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
            return int(max((self.cook_last_time -
                            (int(time.time()) - self.last_timestamp)) // 60, 0))
        return 0

    @property
    def remaining_time(self):
        """Return minutes remaining if cooking/heating."""
        if self.preheat is True:
            return self.preheat_time_remaining
        return self.cook_time_remaining

    @property
    def is_running(self) -> bool:
        """Return if cooking or heating."""
        return bool(self.cook_status in ['cooking', 'heating']) and \
            bool(self.remaining_time > 0)

    @property
    def is_cooking(self) -> bool:
        """Return if cooking."""
        return self.cook_status == 'cooking' and self.remaining_time > 0

    @property
    def is_heating(self) -> bool:
        """Return if heating."""
        return self.cook_status == 'heating' and self.remaining_time > 0

    def status_request(self, json_cmd: dict) -> None:  # pylint: disable=R1260
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
                self.preheat_set_time = preheat.get('preheatSetTime',
                                                    self.preheat_set_time)
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
                self.temp_unit = cook.get('tempUnit', self.temp_unit)
            elif cook.get('cookStatus') == 'end':
                self.set_standby()
                self.cook_status = 'cookEnd'

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
        self.current_temp = None
        self.cook_set_time = None
        self.cook_set_temp = None
        self.last_timestamp = None

    def status_response(self, return_status: dict) -> None:
        """Set status of Air Fryer Based on API Response."""
        self.last_timestamp = None
        self.preheat = False
        self.cook_status = return_status.get('cookStatus', '')
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
        if return_status.get('preheatLastTime') is not None or \
                self.cook_status in ['heating', 'preheatStop', 'preheatEnd']:
            self.preheat = True

        self.cook_set_time = return_status.get('cookSetTime', self.cook_set_time)
        self.cook_last_time = return_status.get('cookLastTime')
        self.current_temp = return_status.get('curentTemp')
        self.cook_set_temp = return_status.get('targetTemp',
                                               return_status.get('cookSetTemp'))
        self.temp_unit = return_status.get('tempUnit', self.temp_unit)  # Always keep set
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


class VeSyncKitchen(VeSyncBaseDevice):
    """(Abstract) base class for all kitchen devices."""

    device_family = EDeviceFamily.KITCHEN
    fryer_status: FryerStatus
    last_update: int = 0
    refresh_interval: float = 0

    def __init__(self, details, manager):
        """Init the VeSync Air Fryer 158 class."""
        super().__init__(details, manager, kitchen_features, EDeviceFamily.KITCHEN)
        self.fryer_status = FryerStatus()
        self.refresh_interval = 0
        self.last_update = int(time.time())


class VeSyncAirFryer158(VeSyncKitchen):
    """Cosori Air Fryer Class."""

    ready_start: bool = False

    def __init__(self, details, manager):
        """Init the VeSync Air Fryer 158 class."""
        super().__init__(details, manager)

        if self.pid is None:
            self.get_pid()
        self.fryer_status.temp_unit = self.get_temp_unit()
        self.ready_start = self.get_remote_cook_mode()

    def get_body(self, method:  Optional[str] = None) -> dict:
        """Return body of api calls."""
        inner = self.manager.req_body_bypass_v1()
        body = {
            **inner,
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

        r = self.manager.post_device_managed_v2(body)
        if not isinstance(r, dict) \
                or r.get('code') != 0 \
                or not isinstance(r.get('result'), dict):
            logger.debug('Failed to get config for %s', self.device_name)
            return
        result = r.get('result')
        if result is not None:
            return result.get('airFryerInfo', {}).get('workTempUnit', 'f')

    def get_remote_cook_mode(self):
        """Get the cook mode."""
        body = self.get_body('getRemoteCookMode158')
        r = self.call_api_v1('getRemoteCookMode158', body)
        if not isinstance(r, dict) or r.get('code') != 0 \
                or not isinstance(r.get('result'), dict):
            return False
        return r.get('result', {}).get('readyStart', False)

    @property
    def temp_unit(self) -> str:
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
        return None

    @property
    def preheat_set_time(self) -> Optional[int]:
        """Return preheat set time."""
        if self.preheat is True:
            return self.fryer_status.preheat_set_time
        return None

    @property
    def cook_status(self) -> str:
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
        body = self.get_status_body(cmd)
        r = Helpers.call_api('/cloud/v1/deviceManaged/bypass', 'post', json_object=body)

        if r is None:
            logger.debug('Failed to get details for %s', self.device_name)
            return False
        if r.get('code') in ERR_REQ_TIMEOUTS:
            logger.debug('%s is offline', self.device_name)
            self.fryer_status.set_standby()
            self.fryer_status.cook_status = 'offline'
            return False
        if r.get('code') != 0:
            logger.debug('Failed to get details for %s \n with code: %s and message: %s',
                         self.device_name, str(r.get("code", 0)), r.get("msg", ''))
            return False
        return_status = r.get('result', {}).get('returnStatus')
        if return_status is None:
            return False
        self.fryer_status.status_response(return_status)
        return True

    @check_status
    def end(self):
        """End the cooking process."""
        if self.preheat is False \
                and self.fryer_status.cook_status in ['cookStop', 'cooking']:
            cmd = {
                'cookMode': {
                    'cookStatus': 'end'
                }
            }
        elif self.preheat is True \
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

    @check_status
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
                    'cookStatus': 'stop'
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
        if self.fryer_status.temp_unit == 'fahrenheit':
            if set_temp < 200 or set_temp > 400:
                logger.debug('Invalid temperature %s for %s', set_temp, self.device_name)
                return False
        if self.fryer_status.temp_unit == 'celsius':
            if set_temp < 75 or set_temp > 205:
                logger.debug('Invalid temperature %s for %s', set_temp, self.device_name)
                return False
        return True

    @check_status
    def cook(self, set_temp: int, set_time: int) -> bool:
        """Set cook time and temperature in Minutes."""
        if self._validate_temp(set_temp) is False:
            return False
        return self._set_cook(set_temp, set_time)

    @check_status
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

    @check_status
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

    # @check_status
    def cook_from_preheat(self) -> bool:
        """Start Cook when preheat has ended."""
        if self.preheat is False or self.cook_status != 'preheatEnd':
            logger.debug('Cannot start cook from preheat for %s', self.device_name)
            return False
        return self._set_cook(status='cooking')

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

    def _set_cook(self, set_temp: Optional[int] = None,
                  set_time: Optional[int] = None, status: str = 'cooking') -> bool:
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
        r = Helpers.call_api('/cloud/v1/deviceManaged/bypass', 'post', json_object=body)
        if r is None:
            logger.debug('Failed to set status for %s - No response from API',
                         self.device_name)
            return False

        if r.get('code') != 0 and r.get('code') is not None:
            debug_msg = self.fryer_code_check(r.get('code', ''))
            logger.debug('Failed to set status for %s \n Code: %s and message: %s \n'
                         ' %s', self.device_name, r.get("code"),
                         r.get("msg"), debug_msg)
            return False
        self.last_update = int(time.time())
        self.fryer_status.status_request(json_cmd)
        self.update()
        return True

    def display(self) -> None:
        """Return formatted device info to stdout."""
        super().display()
        disp = [
            ('cook_status', self.cook_status, ''),
            ('temp_unit', self.temp_unit, ''),
        ]
        if self.cook_status not in ['standby', 'cookEnd', 'preheatEnd']:
            disp += [
                ('preheat', str(self.preheat), ''),
                ('current_temp', str(self.current_temp), self.temp_unit),
                ('cook_set_temp', str(self.cook_set_temp), self.temp_unit),
                ('cook_set_time', str(self.cook_set_time), ''),
                ('cook_last_time', str(self.cook_last_time), ''),
            ]
            if self.preheat is True:
                disp += [
                    ('preheat_last_time', str(self.preheat_last_time), ''),
                    ('preheat_set_time', str(self.preheat_set_time), ''),
                ]
        for line in disp:
            print(f"{line[0]+': ':.<30} {' '.join(line[1:])}")

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


def factory(module: str, details: dict, manager) -> Optional[VeSyncKitchen]:
    """Create VeSync kitchen device instance from the given module/model name."""
    try:
        class_name = kitchen_classes[module]
        kitchen = getattr(module_kitchen, class_name)
        return kitchen(details, manager)
    except Exception:
        return None
