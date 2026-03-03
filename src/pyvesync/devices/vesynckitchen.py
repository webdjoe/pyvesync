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

"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING

from typing_extensions import deprecated

from pyvesync.base_devices import VeSyncFryer
from pyvesync.const import (
    AIRFRYER_PID_MAP,
    AirFryerCookStatus,
    AirFryerPresetRecipe,
    ConnectionStatus,
)
from pyvesync.models import fryer_models as models
from pyvesync.utils.device_mixins import (
    BYPASS_V1_PATH,
    BypassV2Mixin,
    process_bypassv1_result,
    process_bypassv2_result,
)
from pyvesync.utils.errors import VeSyncError
from pyvesync.utils.helpers import Helpers

# from pyvesync.utils.logs import LibraryLogger

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import AirFryerMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel

logger = logging.getLogger(__name__)


class VeSyncAirFryer158(VeSyncFryer):
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

    request_keys: tuple[str, ...] = (
        'acceptLanguage',
        'appVersion',
        'phoneBrand',
        'phoneOS',
        'accountID',
        'cid',
        'configModule',
        'debugMode',
        'traceId',
        'timeZone',
        'token',
        'userCountryCode',
        'uuid',
        'pid',
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
        self.ready_start = True
        if self.config_module not in AIRFRYER_PID_MAP:
            msg = (
                'Report this error as an issue - '
                f'{self.config_module} not found in PID map for {self.device_type}'
            )
            raise VeSyncError(msg)
        self.pid = AIRFRYER_PID_MAP[self.config_module]

    @deprecated('There is no on/off function for Air Fryers.')
    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Turn on or off the air fryer."""
        return toggle if toggle is not None else not self.is_on

    def _build_158_request(
        self,
        request_model: type[models.Fryer158RequestModel],
        update_dict: dict | None = None,
        method: str = 'bypass',
    ) -> models.Fryer158RequestModel:
        """Build API request body for the Bypass V1 endpoint.

        Args:
            request_model (type[models.Fryer158RequestModel]): The request model to use.
            update_dict (dict | None): Additional keys to add on.
            method (str): The method to use in the outer body, defaults to bypass.

        Returns:
            models.Fryer158RequestModel: The request body for the Bypass V1 endpoint,
            the correct model is determined from the models.Fryer158RequestModel
            discriminator.
        """
        body = Helpers.get_defaultvalues_attributes(self.request_keys).copy()
        body.update(Helpers.get_manager_attributes(self.manager, self.request_keys))
        body.update(Helpers.get_device_attributes(self, self.request_keys))
        body['method'] = method
        body.update(update_dict or {})
        return request_model.from_dict(body)

    async def call_158_api(
        self,
        request_model: type[models.Fryer158RequestModel],
        update_dict: dict | None = None,
        method: str = 'bypass',
        endpoint: str = 'bypass',
    ) -> dict | None:
        """Send Cosori 158 APIrequest.

        This uses the `_build_158_request` method to send API requests
        to the Cosori 158 API.

        Args:
            request_model (type[models.Fryer158RequestModel]): The request model to use.
            update_dict (dict | None): Additional keys to add on.
            method (str): The method to use in the outer body.
            endpoint (str | None): The last part of the url path, defaults to
                `bypass`, e.g. `/cloud/v1/deviceManaged/bypass`.

        Returns:
            bytes: The response from the API request.
        """
        request = self._build_158_request(request_model, update_dict, method)
        url_path = BYPASS_V1_PATH + endpoint
        resp_dict, _ = await self.manager.async_call_api(
            url_path, 'post', request, Helpers.req_header_bypass()
        )

        return resp_dict

    def _build_base_request(
        self, cook_set_time: int, recipe: AirFryerPresetRecipe | None = None
    ) -> dict[str, int | str | bool]:
        """Build base cook or preheat request body.

        This allows a custom recipe to be passed, but defaults to manual
        cooking. The cook_set_time argument is required and will override
        the default time in the recipe.
        """
        cook_base: dict[str, int | str | bool] = {}
        cook_base['cookSetTime'] = cook_set_time
        if recipe is None:
            cook_base['recipeId'] = self.default_preset.recipe_id
            cook_base['customRecipe'] = self.default_preset.recipe_name
            cook_base['mode'] = self.default_preset.cook_mode
            cook_base['recipeType'] = self.default_preset.recipe_type
        else:
            cook_base['recipeId'] = recipe.recipe_id
            cook_base['customRecipe'] = recipe.recipe_name
            cook_base['mode'] = recipe.cook_mode
            cook_base['recipeType'] = recipe.recipe_type

        cook_base['accountId'] = self.manager.account_id
        if self.temp_unit is not None:
            cook_base['tempUnit'] = self.temp_unit.label
        else:
            cook_base['tempUnit'] = 'fahrenheit'
        cook_base['readyStart'] = True
        return cook_base

    def _build_cook_request(
        self,
        cook_time: int,
        cook_temp: int,
        recipe: AirFryerPresetRecipe | None = None,
    ) -> dict[str, int | str | bool]:
        """Internal command to build cookMode API command."""
        cook_mode = self._build_base_request(cook_time, recipe)
        cook_mode['appointmentTs'] = 0
        cook_mode['cookSetTemp'] = cook_temp
        cook_mode['cookStatus'] = self.status_map[AirFryerCookStatus.COOKING]
        return cook_mode

    def _build_preheat_request(
        self,
        cook_time: int,
        cook_temp: int,
        recipe: AirFryerPresetRecipe | None = None,
    ) -> dict[str, int | str | bool]:
        """Internal command to build preheat API command."""
        preheat_mode = self._build_base_request(cook_time, recipe)
        preheat_mode['targetTemp'] = cook_temp
        preheat_mode['preheatSetTime'] = cook_time
        preheat_mode['preheatStatus'] = self.status_map[AirFryerCookStatus.HEATING]
        return preheat_mode

# "jsonCmd": {
# 		"preheat": {
# 			"tempUnit": "fahrenheit",
# 			"accountId": "1221391",
# 			"mode": "steak",
# 			"recipeType": 3,
# 			"readyStart": false,
# 			"preheatStatus": "heating",
# 			"recipeId": 2,
# 			"customRecipe": "Steak",
# 			"cookSetTime": 10,
# 			"preheatSetTime": 5,
# 			"targetTemp": 400
# 		}
# 	},
# "cookMode": {
# 			"cookSetTime": 15,
# 			"cookSetTemp": 350,
# 			"appointmentTs": 0,
# 			"recipeId": 1,
# 			"readyStart": false,
# 			"recipeType": 3,
# 			"customRecipe": "Manual",
# 			"mode": "custom",
# 			"accountId": "1221391",
# 			"cookStatus": "cooking",
# 			"tempUnit": "fahrenheit"
# 		}

    async def get_details(self) -> None:
        cmd = {'getStatus': 'status'}
        jsoncmd = {'jsonCmd': cmd}
        resp = await self.call_158_api(models.Fryer158RequestModel, update_dict=jsoncmd)

        if not isinstance(resp, dict) or 'result' not in resp:
            logger.debug(
                'Invalid response for get_details for %s: %s', self.device_name, resp
            )
            self.state.connection_status = ConnectionStatus.OFFLINE
            self.state.set_standby()
            return None

        resp_model = process_bypassv1_result(
            self,
            logger,
            'get_details',
            resp,
            models.Fryer158Result,
        )

        if resp_model is None or resp_model.returnStatus is None:
            logger.debug(
                'No returnStatus in get_details response for %s', self.device_name
            )
            self.state.set_standby()
            return None

        return_status = resp_model.returnStatus
        if return_status.cookStatus not in self.status_map:
            logger.warning(
                'Unknown cook status %s for %s',
                return_status.cookStatus,
                self.device_name,
            )
            self.state.set_standby()
            return None
        return self.state.set_state(
            cook_status=self.status_map[return_status.cookStatus],
            cook_time=return_status.cookSetTime,
            cook_last_time=return_status.cookLastTime,
            cook_temp=return_status.cookSetTemp,
            temp_unit=return_status.tempUnit,
            cook_mode=return_status.mode,
            preheat_set_time=return_status.preheatSetTime,
            preheat_last_time=return_status.preheatLastTime,
            current_temp=return_status.currentTemp,
            recipe=return_status.customRecipe,
        )

    async def end(self, chamber: int = 1) -> bool:
        del chamber  # chamber not used for this air fryer
        if self.state.is_in_cook_mode is True:
            cmd = {'cookMode': {'cookStatus': 'end'}}
        elif self.state.is_in_preheat_mode is True:
            cmd = {'preheat': {'preheatStatus': 'end'}}
        else:
            logger.debug(
                'Cannot end %s as it is not cooking or preheating', self.device_name
            )
            return False
        json_cmd = {'jsonCmd': cmd}
        resp = await self.call_158_api(
            models.Fryer158RequestModel, update_dict=json_cmd
        )
        r = Helpers.process_dev_response(logger, 'end', self, resp)
        if r is None:
            return False
        self.state.set_standby()
        return True

    async def stop(self, chamber: int = 1) -> bool:
        del chamber  # chamber not used for this air fryer
        if self.state.is_in_preheat_mode is True:
            cmd = {'preheat': {'preheatStatus': 'stop'}}
        elif self.state.is_in_cook_mode is True:
            cmd = {'cookMode': {'cookStatus': 'stop'}}
        else:
            logger.debug(
                'Cannot stop %s as it is not cooking or preheating', self.device_name
            )
            return False
        json_cmd = {'jsonCmd': cmd}
        resp = await self.call_158_api(
            models.Fryer158RequestModel, update_dict=json_cmd
        )
        r = Helpers.process_dev_response(logger, 'stop', self, resp)
        if r is None:
            return False
        if self.state.is_in_preheat_mode is True:
            self.state.set_preheat_stop_state()
        elif self.state.is_in_cook_mode is True:
            self.state.set_cook_stop_state()
        return True

    async def resume(self, chamber: int = 1) -> bool:
        del chamber  # chamber not used for this air fryer
        if self.state.is_in_preheat_mode is True:
            cmd = {'preheat': {'preheatStatus': 'heating'}}
        elif self.state.is_in_cook_mode is True:
            cmd = {'cookMode': {'cookStatus': 'cooking'}}
        else:
            logger.debug(
                'Cannot resume %s as it is not cooking or preheating', self.device_name
            )
            return False
        json_cmd = {'jsonCmd': cmd}
        resp = await self.call_158_api(
            models.Fryer158RequestModel, update_dict=json_cmd
        )
        r = Helpers.process_dev_response(logger, 'resume', self, resp)
        if r is None:
            return False

        if self.state.is_in_preheat_mode is True:
            self.state.set_preheat_resume_state()
        elif self.state.is_in_cook_mode is True:
            self.state.cook_status = AirFryerCookStatus.COOKING
        return True

    async def set_mode_from_recipe(
        self,
        recipe: AirFryerPresetRecipe,
        *,
        chamber: int = 1,
    ) -> bool:
        del chamber  # chamber not used for this air fryer
        if recipe.preheat_time is not None and recipe.preheat_time > 0:
            cook_status = AirFryerCookStatus.HEATING
            preheat_req = self._build_preheat_request(
                cook_time=recipe.preheat_time, cook_temp=recipe.target_temp, recipe=recipe
            )
            cmd = {'preheat': preheat_req}
        else:
            cook_status = AirFryerCookStatus.COOKING
            cook_req = self._build_cook_request(
                cook_time=recipe.cook_time, cook_temp=recipe.target_temp, recipe=recipe
            )
            cmd = {'cookMode': cook_req}
        json_cmd = {'jsonCmd': cmd}
        resp = await self.call_158_api(
            models.Fryer158RequestModel, update_dict=json_cmd
        )
        r = Helpers.process_dev_response(logger, 'set_mode_from_recipe', self, resp)
        if r is None:
            return False
        self.state.set_state(
            cook_status=cook_status,
            cook_time=recipe.cook_time,
            cook_last_time=recipe.cook_time,
            cook_temp=recipe.target_temp,
            cook_mode=recipe.cook_mode,
            preheat_set_time=recipe.preheat_time,
            preheat_last_time=recipe.preheat_time,
        )
        return True

    async def set_mode(
        self,
        cook_time: int,
        cook_temp: int,
        *,
        preheat_time: int | None = None,
        cook_mode: str | None = None,
        chamber: int = 1,
    ) -> bool:
        if self.validate_temperature(cook_temp) is False:
            logger.warning('Invalid cook temperature for %s', self.device_name)
            return False
        cook_temp = self.round_temperature(cook_temp)
        cook_time = self.convert_time_for_api(cook_time)
        preset_recipe = replace(self.default_preset)
        preset_recipe.cook_time = cook_time
        preset_recipe.target_temp = cook_temp
        if cook_mode is not None:
            preset_recipe.cook_mode = cook_mode
        if preheat_time is not None:
            preset_recipe.preheat_time = self.convert_time_for_api(preheat_time)
        return await self.set_mode_from_recipe(preset_recipe, chamber=chamber)

    async def cook_from_preheat(self, chamber: int = 1) -> bool:
        del chamber  # chamber not used for this air fryer
        if self.state.cook_status != AirFryerCookStatus.PREHEAT_END:
            logger.debug('Cannot start cook from preheat for %s', self.device_name)
            return False
        cmd = {
            'cookMode': {
                'mode': self.state.cook_mode,
                'accountId': self.manager.account_id,
                'cookStatus': AirFryerCookStatus.COOKING.value,
                'tempUnit': self.temp_unit.label,
            }
        }
        json_cmd = {'jsonCmd': cmd}
        resp = await self.call_158_api(
            models.Fryer158RequestModel, update_dict=json_cmd
        )
        r = Helpers.process_dev_response(logger, 'cook_from_preheat', self, resp)
        if r is None:
            return False
        self.state.set_state(cook_status=AirFryerCookStatus.COOKING)
        return True


class VeSyncTurboBlazeFryer(BypassV2Mixin, VeSyncFryer):
    """VeSync TurboBlaze Air Fryer Class."""

    __slots__ = ()

    def _build_cook_request(
        self, recipe: AirFryerPresetRecipe
    ) -> models.FryerTurboBlazeRequestData:
        cook_req: dict[str, int | str | bool | dict] = {}
        cook_req['accountId'] = self.manager.account_id
        if recipe.preheat_time is not None and recipe.preheat_time > 0:
            cook_req['hasPreheat'] = int(True)
        cook_req['hasWarm'] = False
        cook_req['mode'] = recipe.cook_mode
        cook_req['readyStart'] = True
        cook_req['recipeId'] = recipe.recipe_id
        cook_req['recipeName'] = recipe.recipe_name
        cook_req['recipeType'] = recipe.recipe_type
        cook_req['tempUnit'] = self.temp_unit.code
        cook_req['startAct'] = {
            'cookSetTime': recipe.cook_time,
            'cookTemp': recipe.target_temp,
            'preheatTemp': recipe.target_temp if recipe.preheat_time else 0,
            'shakeTime': 0,
        }
        return models.FryerTurboBlazeRequestData.from_dict(cook_req)

    async def get_details(self) -> None:
        resp = await self.call_bypassv2_api(payload_method='getAirfyerStatus')
        resp_model = process_bypassv2_result(
            self,
            logger,
            'get_details',
            resp,
            models.FryerTurboBlazeDetailResult,
        )

        if (
            resp_model is None
            or resp_model.cookStatus == AirFryerCookStatus.STANDBY.value
            or not resp_model.stepArray
        ):
            self.state.set_standby()
            return

        cook_step = resp_model.stepArray[resp_model.stepIndex]
        if resp_model.cookStatus not in self.status_map:
            logger.warning(
                'Unknown cook status %s for %s',
                resp_model.cookStatus,
                self.device_name,
            )
            self.state.set_standby()
            return

        self.state.set_state(
            cook_status=self.status_map[resp_model.cookStatus],
            cook_time=cook_step.cookSetTime,
            cook_last_time=cook_step.cookLastTime,
            cook_temp=cook_step.cookTemp,
            temp_unit=resp_model.tempUnit,
            cook_mode=cook_step.mode,
            preheat_set_time=resp_model.preheatSetTime,
            preheat_last_time=resp_model.preheatLastTime,
            current_temp=resp_model.currentTemp,
        )

    async def end(self, chamber: int = 1) -> bool:
        del chamber  # chamber not used for this air fryer
        payload_method = 'endCook'
        resp = await self.call_bypassv2_api(payload_method=payload_method)
        r = Helpers.process_dev_response(logger, 'end', self, resp)
        if r is None:
            return False
        self.state.set_standby()
        return True

    async def set_mode_from_recipe(self, recipe: AirFryerPresetRecipe) -> bool:
        payload_method = 'startCook'
        data = self._build_cook_request(recipe)
        resp = await self.call_bypassv2_api(
            payload_method=payload_method,
            data=data.to_dict(),
        )
        r = Helpers.process_dev_response(logger, 'set_mode_from_recipe', self, resp)
        if r is None:
            self.state.set_standby()
            return False
        self.state.set_state(
            cook_status=AirFryerCookStatus.COOKING,
            cook_time=recipe.cook_time,
            cook_last_time=recipe.cook_time,
            cook_temp=recipe.target_temp,
            cook_mode=recipe.cook_mode,
            preheat_set_time=recipe.preheat_time if recipe.preheat_time else None,
            preheat_last_time=recipe.preheat_time if recipe.preheat_time else None,
        )
        return True

    async def set_mode(
        self,
        cook_time: int,
        cook_temp: int,
        *,
        preheat_time: int | None = None,
        chamber: int = 1,
    ) -> bool:
        del chamber  # chamber not used for this air fryer
        recipe = replace(self.default_preset)
        recipe.cook_time = self.convert_time_for_api(cook_time)
        recipe.target_temp = self.round_temperature(cook_temp)
        if preheat_time is not None:
            recipe.preheat_time = self.convert_time_for_api(preheat_time)
        return await self.set_mode_from_recipe(recipe)
