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
    TemperatureUnits,
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
    from pyvesync.base_devices.fryer_base import FryerState
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
        cook_base['tempUnit'] = self.temp_unit.label
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
        if return_status.tempUnit is not None:
            self.temp_unit = return_status.tempUnit
        return self.state.set_state(
            cook_status=self.status_map[return_status.cookStatus],
            cook_time=return_status.cookSetTime,
            cook_last_time=return_status.cookLastTime,
            cook_temp=return_status.cookSetTemp,
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
        resp = await self.call_158_api(models.Fryer158RequestModel, update_dict=json_cmd)
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
        resp = await self.call_158_api(models.Fryer158RequestModel, update_dict=json_cmd)
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
        resp = await self.call_158_api(models.Fryer158RequestModel, update_dict=json_cmd)
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
        resp = await self.call_158_api(models.Fryer158RequestModel, update_dict=json_cmd)
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
        prepared_temp = self.prepare_temperature(cook_temp)
        if prepared_temp is None:
            return False
        cook_temp = prepared_temp
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
        resp = await self.call_158_api(models.Fryer158RequestModel, update_dict=json_cmd)
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
        cook_req['readyStart'] = False
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
        resp = await self.call_bypassv2_api(payload_method='getAirfryerStatus')
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

        if resp_model.tempUnit:
            self.temp_unit = resp_model.tempUnit

        # currentTemp from the bypassV2 getAirfryerStatus response is the
        # device's hardware sensor reading, which the firmware always
        # reports in Celsius regardless of the reported tempUnit. The
        # tempUnit field governs only the echoed cookTemp/preheatTemp
        # values. Normalize so consumers can compare cook_temp and
        # current_temp without a unit-aware crutch.
        _current_temp = resp_model.currentTemp
        if _current_temp is not None and self.temp_unit == TemperatureUnits.FAHRENHEIT:
            _current_temp = round(_current_temp * 9 / 5 + 32)

        self.state_chamber_1.set_state(
            cook_status=self.status_map[resp_model.cookStatus],
            cook_time=cook_step.cookSetTime,
            cook_last_time=cook_step.cookLastTime,
            cook_temp=cook_step.cookTemp,
            cook_mode=cook_step.mode,
            preheat_set_time=resp_model.preheatSetTime,
            preheat_last_time=resp_model.preheatLastTime,
            current_temp=_current_temp,
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
        prepared_temp = self.prepare_temperature(cook_temp)
        if prepared_temp is None:
            return False
        recipe = replace(self.default_preset)
        recipe.cook_time = self.convert_time_for_api(cook_time)
        recipe.target_temp = prepared_temp
        if preheat_time is not None:
            recipe.preheat_time = self.convert_time_for_api(preheat_time)
        return await self.set_mode_from_recipe(recipe)


class VeSyncDualAirFryer(BypassV2Mixin, VeSyncFryer):
    """Cosori Dual Air Fryer Class (CAF-TF101S).

    Supports dual-chamber cooking with three operating modes:
    - Single chamber (left or right)
    - Whole chamber (merged)
    - Sync mode (both chambers with identical settings)

    The device has no preheat, pause, or resume API. Pausing is handled
    physically by pulling the basket out, which triggers a ``cookStop``
    or ``pullOut`` state. Pushing the basket back in resumes cooking
    automatically.

    Args:
        details (ResponseDeviceDetailsModel): Device details.
        manager (VeSync): Manager class.
        feature_map (AirFryerMap): Device feature map.

    Attributes:
        state_chamber_1 (FryerState): State for chamber 1 (left) or whole.
        state_chamber_2 (FryerState): State for chamber 2 (right).
        sync_chambers (bool): Whether chambers are synced for cooking.
    """

    __slots__ = ()

    # workChamber API values
    _WC_NONE = 0
    _WC_LEFT = 1
    _WC_RIGHT = 2
    _WC_WHOLE = 3
    _WC_SYNC = 4
    _SYNC_TYPE_SYNCED = 2

    def _get_chamber_state(self, chamber: int) -> FryerState:
        """Return the FryerState for the given chamber number.

        Args:
            chamber: Chamber number (1=left, 2=right, 3=whole maps to chamber 1).
        """
        if chamber == self._WC_RIGHT:
            return self.state_chamber_2
        return self.state_chamber_1

    def _get_work_chamber(self, chamber: int) -> int:
        """Return the API workChamber value for the given chamber.

        Args:
            chamber: Chamber number (1, 2, or 3).

        Returns:
            API workChamber value (1, 2, 3, or 4 for sync).
        """
        if self.sync_chambers:
            return self._WC_SYNC
        return chamber

    def _get_sync_type(self) -> int:
        """Return the API syncType value."""
        return self._SYNC_TYPE_SYNCED if self.sync_chambers else 0

    async def get_details(self) -> None:
        """Get device details from the API.

        Polls ``getAirfryerMultiStatus`` and updates state for each chamber.
        """
        resp = await self.call_bypassv2_api(
            payload_method='getAirfryerMultiStatus',
            payload_update={'subDeviceNo': 0, 'subDeviceType': ''},
        )
        resp_model = process_bypassv2_result(
            self,
            logger,
            'get_details',
            resp,
            models.FryerDualMultiStatusResult,
        )

        if resp_model is None:
            self.state_chamber_1.set_standby()
            self.state_chamber_2.set_standby()
            return

        self.temp_unit = resp_model.tempUnit

        # Update sync state from API response
        self.sync_chambers = resp_model.syncType == self._SYNC_TYPE_SYNCED
        self.state_chamber_1.sync_chambers = self.sync_chambers
        self.state_chamber_2.sync_chambers = self.sync_chambers

        # Track which chambers were updated
        updated_chambers: set[int] = set()

        for status_item in resp_model.statusList:
            ch_num = status_item.chamber
            updated_chambers.add(ch_num)
            chamber_state = self._get_chamber_state(ch_num)

            if (
                status_item.cookStatus not in self.status_map
                or status_item.cookStatus == AirFryerCookStatus.STANDBY.value
            ):
                if status_item.cookStatus not in self.status_map:
                    logger.warning(
                        'Unknown cook status %s for %s chamber %d',
                        status_item.cookStatus,
                        self.device_name,
                        ch_num,
                    )
                chamber_state.set_standby()
                continue

            chamber_state.set_state(
                cook_status=self.status_map[status_item.cookStatus],
                cook_time=status_item.cookSetTime,
                cook_last_time=status_item.currentRemainingTime,
                cook_temp=status_item.cookTemp,
                cook_mode=status_item.mode,
                recipe=status_item.recipeName or None,
            )

        # Set any chambers not in the response to standby
        if (
            self._WC_LEFT not in updated_chambers
            and self._WC_WHOLE not in updated_chambers
        ):
            self.state_chamber_1.set_standby()
        if (
            self._WC_RIGHT not in updated_chambers
            and self._WC_WHOLE not in updated_chambers
        ):
            self.state_chamber_2.set_standby()

    async def end(self, chamber: int = 1) -> bool:
        """End the current cooking session.

        Args:
            chamber: Chamber to end (1=left, 2=right, 3=whole).
                If sync mode is active, ends both chambers.

        Returns:
            True if the command was successful.
        """
        api_chamber = self._get_work_chamber(chamber)
        resp = await self.call_bypassv2_api(
            payload_method='endCook',
            data={'chamber': api_chamber},
        )
        r = Helpers.process_dev_response(logger, 'end', self, resp)
        if r is None:
            return False

        if self.sync_chambers or api_chamber == self._WC_SYNC:
            self.state_chamber_1.set_standby()
            self.state_chamber_2.set_standby()
            self.sync_chambers = False
        elif chamber == self._WC_WHOLE:
            self.state_chamber_1.set_standby()
        else:
            self._get_chamber_state(chamber).set_standby()
        return True

    def _build_cook_configs(
        self,
        recipe: AirFryerPresetRecipe,
        chamber: int,
    ) -> list[models.FryerDualCookConfig]:
        """Build cookConfigs list for startMultiCook request.

        Args:
            recipe: The recipe to cook.
            chamber: Chamber number (1, 2, or 3 for whole).

        Returns:
            List of FryerDualCookConfig for the API request.
        """
        config_dict = {
            'cookSetTime': recipe.cook_time,
            'cookTemp': recipe.target_temp,
            'mode': recipe.cook_mode,
            'recipeId': recipe.recipe_id,
            'recipeName': recipe.recipe_name,
            'recipeType': recipe.recipe_type,
        }

        if self.sync_chambers:
            return [
                models.FryerDualCookConfig.from_dict({**config_dict, 'chamber': 1}),
                models.FryerDualCookConfig.from_dict({**config_dict, 'chamber': 2}),
            ]
        return [
            models.FryerDualCookConfig.from_dict({**config_dict, 'chamber': chamber}),
        ]

    async def set_mode_from_recipe(
        self,
        recipe: AirFryerPresetRecipe,
        *,
        chamber: int = 1,
    ) -> bool:
        """Start cooking with a preset recipe.

        Args:
            recipe: The preset recipe to use.
            chamber: Chamber to cook in (1=left, 2=right, 3=whole).
                If ``sync_chambers`` is True, both chambers cook in sync.

        Returns:
            True if the command was successful.
        """
        cook_configs = self._build_cook_configs(recipe, chamber)
        work_chamber = self._get_work_chamber(chamber)
        sync_type = self._get_sync_type()

        start_data = models.FryerDualStartCookData.from_dict(
            {
                'accountId': self.manager.account_id,
                'cookConfigs': [c.to_dict() for c in cook_configs],
                'readyStart': True,
                'syncType': sync_type,
                'tempUnit': self.temp_unit.code,
                'workChamber': work_chamber,
            }
        )

        resp = await self.call_bypassv2_api(
            payload_method='startMultiCook',
            data=start_data.to_dict(),
        )
        r = Helpers.process_dev_response(logger, 'set_mode_from_recipe', self, resp)
        if r is None:
            return False

        # Update state for affected chambers
        chambers = (
            [self.state_chamber_1, self.state_chamber_2]
            if self.sync_chambers
            else [self._get_chamber_state(chamber)]
        )
        for ch_state in chambers:
            ch_state.set_state(
                cook_status=AirFryerCookStatus.COOKING,
                cook_time=recipe.cook_time,
                cook_last_time=recipe.cook_time,
                cook_temp=recipe.target_temp,
                cook_mode=recipe.cook_mode,
                recipe=recipe.recipe_name,
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
        """Set cooking mode with manual parameters.

        Args:
            cook_time: Cooking time in seconds.
            cook_temp: Cooking temperature in the device's ``temp_unit``.
            preheat_time: Not used for this device.
            cook_mode: Cooking mode string (e.g. 'AirFry').
            chamber: Chamber number (1=left, 2=right, 3=whole).

        Returns:
            True if the command was successful.
        """
        del preheat_time  # not supported by this device
        prepared_temp = self.prepare_temperature(cook_temp)
        if prepared_temp is None:
            return False
        cook_temp = prepared_temp
        recipe = replace(self.default_preset)
        recipe.cook_time = self.convert_time_for_api(cook_time)
        recipe.target_temp = cook_temp
        if cook_mode is not None:
            recipe.cook_mode = cook_mode
        return await self.set_mode_from_recipe(recipe, chamber=chamber)
