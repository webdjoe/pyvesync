"""VeSync Cosori air fryers.

- ``VeSyncAirFryer158``: CS137/CS158 (Bypass V1 API, times in minutes).
- ``VeSyncTurboBlazeFryer``: CAF-DC601S (bypassV2 ``startCook``).
- ``VeSyncDualBlazeFryer``: CAF-P583S (bypassV2 ``startCook``).
- ``VeSyncDualAirFryer``: CAF-TF101S / CAF-TF102S (bypassV2
  ``startMultiCook``, two chambers).

A successful command sets the chamber state locally from the request; it does
not call ``update()``. Call ``update()`` to read what the device reports. The
CS137/CS158 ``end()``, ``stop()``, ``resume()`` and ``cook_from_preheat()``
choose their command from the last known state.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING

from typing_extensions import deprecated

from pyvesync.base_devices import VeSyncFryer
from pyvesync.const import (
    AIRFRYER_PID_MAP,
    BYPASSV2_SUB_DEVICE_PAYLOAD,
    AirFryerChamber,
    AirFryerCookStatus,
    AirFryerFeatures,
    AirFryerPresetRecipe,
    AirFryerSyncType,
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
    from pyvesync.device_map import AirFryerMap
    from pyvesync.models.base_models import RequestBaseModel
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel

logger = logging.getLogger(__name__)


class VeSyncAirFryer158(VeSyncFryer):
    """Cosori CS137/CS158 air fryer (Bypass V1 API).

    The API counts time in whole minutes, so times are truncated to the minute
    when sent (under 60 seconds is sent as 0). This is the only fryer class
    that implements ``stop()``, ``resume()`` and ``cook_from_preheat()``. They
    and ``end()`` choose the cook or preheat command from the last known
    state, so call ``update()`` first if the fryer may have changed state.

    Args:
        details (ResponseDeviceDetailsModel): Device details.
        manager (VeSync): Manager class.
        feature_map (AirFryerMap): Device feature map.

    Attributes:
        pid (str): Product ID from ``AIRFRYER_PID_MAP``, by config module.
        request_keys (tuple[str, ...]): Keys copied into every request body.
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
        self.ready_start = False
        if self.config_module not in AIRFRYER_PID_MAP:
            msg = (
                'Report this error as an issue - '
                f'{self.config_module} not found in PID map for {self.device_type}'
            )
            raise VeSyncError(msg)
        self.pid = AIRFRYER_PID_MAP[self.config_module]

    @deprecated('There is no on/off function for Air Fryers.')
    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Do nothing; air fryers have no on/off command.

        No request is sent.

        Returns:
            bool: ``toggle``, or ``not is_on`` when ``toggle`` is None.
        """
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
            models.Fryer158RequestModel: The request body built from
            ``request_model``.
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
        """Send a Cosori 158 API request.

        This uses the `_build_158_request` method to send API requests
        to the Cosori 158 API.

        Args:
            request_model (type[models.Fryer158RequestModel]): The request model to use.
            update_dict (dict | None): Additional keys to add on.
            method (str): The method to use in the outer body.
            endpoint (str): The last part of the url path, defaults to
                `bypass`, e.g. `/cloud/v1/deviceManaged/bypass`.

        Returns:
            dict | None: The response JSON, or None if there was no valid
            response.
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
        # readyStart False starts the cook at once; True waits for the start button.
        cook_base['readyStart'] = False
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
        preheat_time: int,
        cook_temp: int,
        recipe: AirFryerPresetRecipe | None = None,
    ) -> dict[str, int | str | bool]:
        """Internal command to build preheat API command.

        Both times are in the device's API time units.
        """
        preheat_mode = self._build_base_request(cook_time, recipe)
        preheat_mode['targetTemp'] = cook_temp
        preheat_mode['preheatSetTime'] = preheat_time
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
            # Preheat and pull-out-during-preheat states report targetTemp only.
            cook_temp=return_status.cookSetTemp
            if return_status.cookSetTemp is not None
            else return_status.targetTemp,
            cook_mode=return_status.mode,
            preheat_set_time=return_status.preheatSetTime,
            preheat_last_time=return_status.preheatLastTime,
            current_temp=return_status.current_temp,
            recipe=return_status.customRecipe,
        )

    async def end(
        self, chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1
    ) -> bool:
        if self._validate_chamber(chamber) is None:
            return False
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

    async def stop(
        self, chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1
    ) -> bool:
        if self._validate_chamber(chamber) is None:
            return False
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

    async def resume(
        self, chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1
    ) -> bool:
        if self._validate_chamber(chamber) is None:
            return False
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
        chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1,
    ) -> bool:
        if self._validate_chamber(chamber) is None:
            return False
        target_temp = self.prepare_recipe_temperature(recipe)
        if target_temp is None:
            return False
        recipe = replace(recipe, target_temp=target_temp, temp_unit=self.temp_unit.code)
        cook_time = self.convert_time_for_api(recipe.cook_time)
        preheat_time = (
            self.convert_time_for_api(recipe.preheat_time)
            if recipe.preheat_time is not None
            else None
        )
        if preheat_time is not None and preheat_time > 0:
            cook_status = AirFryerCookStatus.HEATING
            preheat_req = self._build_preheat_request(
                cook_time=cook_time,
                preheat_time=preheat_time,
                cook_temp=recipe.target_temp,
                recipe=recipe,
            )
            cmd = {'preheat': preheat_req}
        else:
            cook_status = AirFryerCookStatus.COOKING
            cook_req = self._build_cook_request(
                cook_time=cook_time, cook_temp=recipe.target_temp, recipe=recipe
            )
            cmd = {'cookMode': cook_req}
        json_cmd = {'jsonCmd': cmd}
        resp = await self.call_158_api(models.Fryer158RequestModel, update_dict=json_cmd)
        r = Helpers.process_dev_response(logger, 'set_mode_from_recipe', self, resp)
        if r is None:
            return False
        self.state.set_state(
            cook_status=cook_status,
            cook_time=cook_time,
            cook_last_time=cook_time,
            cook_temp=recipe.target_temp,
            cook_mode=recipe.cook_mode,
            preheat_set_time=preheat_time,
            preheat_last_time=preheat_time,
        )
        return True

    async def set_mode(
        self,
        cook_time: int,
        cook_temp: int,
        *,
        temp_unit: TemperatureUnits | str | None = None,
        preheat_time: int | None = None,
        cook_mode: str | None = None,
        chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1,
    ) -> bool:
        unit = self._resolve_temp_unit(temp_unit)
        if unit is None:
            return False
        recipe = self._recipe_for_set_mode(
            cook_time, cook_temp, cook_mode, preheat_time, temp_unit=unit
        )
        if recipe is None:
            return False
        return await self.set_mode_from_recipe(recipe, chamber=chamber)

    async def cook_from_preheat(
        self, chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1
    ) -> bool:
        if self._validate_chamber(chamber) is None:
            return False
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
    """Cosori TurboBlaze air fryer (CAF-DC601S, bypassV2 ``startCook``).

    Single chamber; times are in seconds. A preheat is sent only when the
    device map has the ``PREHEAT`` feature, otherwise ``preheat_time`` is
    dropped with a debug log. ``stop()``, ``resume()`` and
    ``cook_from_preheat()`` are not implemented and return False. The reported
    ``currentTemp`` is in Celsius and is converted to ``temp_unit``. A local
    ``set_mode()`` does not set ``state.recipe``.
    """

    __slots__ = ()

    def _payload_update(self) -> dict | None:
        """Return extra payload keys sent on every request, if any."""
        return None

    def _cook_request_dict(
        self, recipe: AirFryerPresetRecipe
    ) -> dict[str, int | str | bool | dict]:
        """Build the startCook data values from a recipe."""
        cook_req: dict[str, int | str | bool | dict] = {}
        cook_req['accountId'] = self.manager.account_id
        if recipe.preheat_time is not None and recipe.preheat_time > 0:
            cook_req['hasPreheat'] = int(True)
        cook_req['hasWarm'] = False
        cook_req['mode'] = recipe.cook_mode
        # readyStart False starts the cook at once; True waits for the start button.
        cook_req['readyStart'] = False
        cook_req['recipeId'] = recipe.recipe_id
        cook_req['recipeName'] = recipe.recipe_name
        cook_req['recipeType'] = recipe.recipe_type
        cook_req['tempUnit'] = self.temp_unit.code
        cook_req['startAct'] = {
            'cookSetTime': self.convert_time_for_api(recipe.cook_time),
            'cookTemp': recipe.target_temp,
            'preheatTemp': recipe.target_temp if recipe.preheat_time else 0,
            'shakeTime': 0,
        }
        return cook_req

    def _build_cook_request(self, recipe: AirFryerPresetRecipe) -> RequestBaseModel:
        return models.FryerTurboBlazeRequestData.from_dict(
            self._cook_request_dict(recipe)
        )

    async def get_details(self) -> None:
        resp = await self.call_bypassv2_api(
            payload_method='getAirfryerStatus',
            payload_update=self._payload_update(),
        )
        resp_model = process_bypassv2_result(
            self,
            logger,
            'get_details',
            resp,
            models.FryerTurboBlazeDetailResult,
        )

        if resp_model is None:
            self.state.set_standby()
            return

        # Standby responses report the unit too (P583S-KUS capture).
        if resp_model.tempUnit:
            self.temp_unit = resp_model.tempUnit

        if (
            resp_model.cookStatus == AirFryerCookStatus.STANDBY.value
            or not resp_model.stepArray
        ):
            self.state.set_standby()
            return

        if resp_model.stepIndex >= len(resp_model.stepArray):
            logger.warning(
                'stepIndex %s out of range for %s steps on %s',
                resp_model.stepIndex,
                len(resp_model.stepArray),
                self.device_name,
            )
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
            # preheatSetTime is 0 when the cook has no preheat step.
            preheat_set_time=resp_model.preheatSetTime or None,
            preheat_last_time=resp_model.preheatLastTime,
            current_temp=_current_temp,
            recipe=cook_step.recipeName or None,
            total_last_time=resp_model.totalTimeRemaining,
        )

    async def end(
        self, chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1
    ) -> bool:
        if self._validate_chamber(chamber) is None:
            return False
        payload_method = 'endCook'
        resp = await self.call_bypassv2_api(
            payload_method=payload_method,
            payload_update=self._payload_update(),
        )
        r = Helpers.process_dev_response(logger, 'end', self, resp)
        if r is None:
            return False
        self.state.set_standby()
        return True

    async def set_mode_from_recipe(
        self,
        recipe: AirFryerPresetRecipe,
        *,
        chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1,
    ) -> bool:
        if self._validate_chamber(chamber) is None:
            return False
        target_temp = self.prepare_recipe_temperature(recipe)
        if target_temp is None:
            return False
        recipe = replace(recipe, target_temp=target_temp, temp_unit=self.temp_unit.code)
        if recipe.preheat_time and AirFryerFeatures.PREHEAT not in self.features:
            logger.debug('Preheat not supported for %s, ignoring', self.device_name)
            recipe = replace(recipe, preheat_time=None)
        payload_method = 'startCook'
        data = self._build_cook_request(recipe)
        resp = await self.call_bypassv2_api(
            payload_method=payload_method,
            data=data.to_dict(),
            payload_update=self._payload_update(),
        )
        r = Helpers.process_dev_response(logger, 'set_mode_from_recipe', self, resp)
        if r is None:
            return False
        cook_time = self.convert_time_for_api(recipe.cook_time)
        preheat_time = (
            self.convert_time_for_api(recipe.preheat_time)
            if recipe.preheat_time
            else None
        )
        self.state.set_state(
            # A program with preheat runs the preheat phase first.
            cook_status=AirFryerCookStatus.HEATING
            if preheat_time
            else AirFryerCookStatus.COOKING,
            cook_time=cook_time,
            cook_last_time=cook_time,
            cook_temp=recipe.target_temp,
            cook_mode=recipe.cook_mode,
            preheat_set_time=preheat_time,
            preheat_last_time=preheat_time,
        )
        return True

    async def set_mode(
        self,
        cook_time: int,
        cook_temp: int,
        *,
        temp_unit: TemperatureUnits | str | None = None,
        preheat_time: int | None = None,
        cook_mode: str | None = None,
        chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1,
    ) -> bool:
        unit = self._resolve_temp_unit(temp_unit)
        if unit is None:
            return False
        recipe = self._recipe_for_set_mode(
            cook_time, cook_temp, cook_mode, preheat_time, temp_unit=unit
        )
        if recipe is None:
            return False
        return await self.set_mode_from_recipe(recipe, chamber=chamber)


class VeSyncDualBlazeFryer(VeSyncTurboBlazeFryer):
    """Cosori Dual Blaze Air Fryer Class (CAF-P583S).

    Uses the TurboBlaze bypassV2 protocol with the request shape from the
    CAF-P583S-KUS capture (2025-05-21): ``startCook`` data uses ``accountID``
    (not ``accountId``) and sends ``hasLinkage`` False, and every payload
    carries ``subDeviceNo`` and ``subDeviceType``. The KEU variant has no
    capture and is assumed to match. The P583S has no preheat, so
    ``preheat_time`` is dropped with a debug log.
    """

    __slots__ = ()

    def _payload_update(self) -> dict | None:
        return dict(BYPASSV2_SUB_DEVICE_PAYLOAD)

    def _build_cook_request(self, recipe: AirFryerPresetRecipe) -> RequestBaseModel:
        cook_req = self._cook_request_dict(recipe)
        cook_req['accountID'] = cook_req.pop('accountId')
        cook_req['hasLinkage'] = False
        return models.FryerDualBlazeRequestData.from_dict(cook_req)


class VeSyncDualAirFryer(BypassV2Mixin, VeSyncFryer):
    """Cosori Dual Air Fryer Class (CAF-TF101S, CAF-TF102S).

    Chambers are selected with ``AirFryerChamber``:

    - ``CHAMBER_1`` / ``CHAMBER_2``: one chamber (left or right).
    - ``WHOLE``: the merged basket with the divider removed (TwinFry models
      only, ``WHOLE_CHAMBER`` feature).
    - ``BOTH``: both chambers with identical settings, sent as the app's Sync
      mode (``workChamber`` 4, ``syncType`` 2: both chambers finish together).

    The device has no preheat, pause, or resume API: ``preheat_time`` and a
    recipe's ``preheat_time`` are ignored, and ``stop()`` / ``resume()``
    return False. Pausing is handled physically by pulling the basket out,
    which triggers a ``cookStop`` or ``pullOut`` state. Pushing the basket
    back in resumes cooking automatically. The status has no temperature
    reading, so ``current_temp`` stays None.

    Args:
        details (ResponseDeviceDetailsModel): Device details.
        manager (VeSync): Manager class.
        feature_map (AirFryerMap): Device feature map.

    Attributes:
        state_chamber_1 (FryerState): State for chamber 1 (left) or whole.
        state_chamber_2 (FryerState): State for chamber 2 (right).
        sync_chambers (bool): Read-only. True only for the app's Sync mode
            (``syncType`` 2). Set by ``update()``; a successful
            ``set_mode()`` / ``set_mode_from_recipe()`` sets it True for
            ``BOTH`` and False for any other chamber, and ``end(BOTH)`` sets
            it False.
        work_chamber (AirFryerChamber | None): Read-only. Chamber the device
            reports as active (``workChamber``); None when idle. Set only by
            ``update()``; a local command leaves it at the last reported value.
    """

    __slots__ = ()

    def _get_sync_type(self, chamber: AirFryerChamber) -> AirFryerSyncType:
        """Return the API syncType value for a validated chamber."""
        if chamber == AirFryerChamber.BOTH:
            return AirFryerSyncType.SYNC
        return AirFryerSyncType.OFF

    def _set_reported_sync(self, value: bool) -> None:
        """Set ``sync_chambers`` on both chamber states."""
        self.state_chamber_1.sync_chambers = value
        self.state_chamber_2.sync_chambers = value

    def _set_reported_work_chamber(self, value: AirFryerChamber | None) -> None:
        """Set ``work_chamber`` on both chamber states."""
        self.state_chamber_1.work_chamber = value
        self.state_chamber_2.work_chamber = value

    async def get_details(self) -> None:
        """Get device details from the API.

        Polls ``getAirfryerMultiStatus`` and updates state for each chamber.
        """
        resp = await self.call_bypassv2_api(
            payload_method='getAirfryerMultiStatus',
            payload_update=dict(BYPASSV2_SUB_DEVICE_PAYLOAD),
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
            self._set_reported_work_chamber(None)
            return

        # process_bypassv2_result only stamps self.state (chamber 1).
        self.state_chamber_2.update_ts()
        self.temp_unit = resp_model.tempUnit

        # Update sync state and active chamber from API response
        self._set_reported_sync(resp_model.syncType == AirFryerSyncType.SYNC)
        try:
            self._set_reported_work_chamber(AirFryerChamber(resp_model.workChamber))
        except ValueError:
            if resp_model.workChamber != 0:
                logger.debug(
                    'Unknown workChamber %s for %s',
                    resp_model.workChamber,
                    self.device_name,
                )
            self._set_reported_work_chamber(None)

        # Track which chambers were updated
        updated_chambers: set[AirFryerChamber] = set()

        for status_item in resp_model.statusList:
            try:
                ch = AirFryerChamber(status_item.chamber)
                chamber_state = self.get_chamber_state(ch)
            except ValueError:
                logger.warning(
                    'Unknown chamber %s in status for %s',
                    status_item.chamber,
                    self.device_name,
                )
                continue
            updated_chambers.add(ch)

            if (
                status_item.cookStatus not in self.status_map
                or status_item.cookStatus == AirFryerCookStatus.STANDBY.value
            ):
                if status_item.cookStatus not in self.status_map:
                    logger.warning(
                        'Unknown cook status %s for %s chamber %d',
                        status_item.cookStatus,
                        self.device_name,
                        status_item.chamber,
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
                total_last_time=status_item.totalTimeRemaining,
            )

        # Set any chambers not in the response to standby. Whole-chamber
        # status is reported as a single chamber 3 item, so chamber 2 idles.
        if (
            AirFryerChamber.CHAMBER_1 not in updated_chambers
            and AirFryerChamber.WHOLE not in updated_chambers
        ):
            self.state_chamber_1.set_standby()
        if AirFryerChamber.CHAMBER_2 not in updated_chambers:
            self.state_chamber_2.set_standby()

    async def end(
        self, chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1
    ) -> bool:
        """End the current cooking session.

        Args:
            chamber (AirFryerChamber | int): Chamber to end. ``BOTH`` ends
                both chambers. During a Sync cook (``sync_chambers``), one
                chamber sends an end for that chamber only.

        Returns:
            bool: True on success, and the ended chamber state(s) are set to
            standby. False without a request for an unsupported chamber.
        """
        member = self._validate_chamber(chamber)
        if member is None:
            return False
        if self.sync_chambers and member in (
            AirFryerChamber.CHAMBER_1,
            AirFryerChamber.CHAMBER_2,
        ):
            logger.debug(
                '%s is in Sync mode; end(%s) ends one chamber, '
                'pass AirFryerChamber.BOTH to end both',
                self.device_name,
                member.name,
            )
        resp = await self.call_bypassv2_api(
            payload_method='endCook',
            data={'chamber': int(member)},
            payload_update=dict(BYPASSV2_SUB_DEVICE_PAYLOAD),
        )
        r = Helpers.process_dev_response(logger, 'end', self, resp)
        if r is None:
            return False

        if member == AirFryerChamber.BOTH:
            self.state_chamber_1.set_standby()
            self.state_chamber_2.set_standby()
            self._set_reported_sync(False)
        else:
            self.get_chamber_state(member).set_standby()
        return True

    def _build_cook_configs(
        self,
        recipe: AirFryerPresetRecipe,
        chamber: AirFryerChamber,
    ) -> list[models.FryerDualCookConfig]:
        """Build cookConfigs list for startMultiCook request.

        Args:
            recipe: The recipe to cook.
            chamber: Validated chamber. ``BOTH`` gives configs for chambers
                1 and 2.

        Returns:
            List of FryerDualCookConfig for the API request.
        """
        config_dict = {
            'cookSetTime': self.convert_time_for_api(recipe.cook_time),
            'cookTemp': recipe.target_temp,
            'mode': recipe.cook_mode,
            'recipeId': recipe.recipe_id,
            'recipeName': recipe.recipe_name,
            'recipeType': recipe.recipe_type,
        }

        if chamber == AirFryerChamber.BOTH:
            return [
                models.FryerDualCookConfig.from_dict({**config_dict, 'chamber': 1}),
                models.FryerDualCookConfig.from_dict({**config_dict, 'chamber': 2}),
            ]
        return [
            models.FryerDualCookConfig.from_dict(
                {**config_dict, 'chamber': int(chamber)}
            ),
        ]

    async def set_mode_from_recipe(
        self,
        recipe: AirFryerPresetRecipe,
        *,
        chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1,
    ) -> bool:
        """Start cooking with a preset recipe.

        Args:
            recipe: The preset recipe to use. Its ``preheat_time`` is ignored.
            chamber (AirFryerChamber | int): Chamber to cook in. ``BOTH``
                cooks both chambers in sync.

        Returns:
            True if the command was successful.
        """
        member = self._validate_chamber(chamber)
        if member is None:
            return False
        target_temp = self.prepare_recipe_temperature(recipe)
        if target_temp is None:
            return False
        recipe = replace(recipe, target_temp=target_temp, temp_unit=self.temp_unit.code)
        cook_configs = self._build_cook_configs(recipe, member)

        start_data = models.FryerDualStartCookData.from_dict(
            {
                'accountId': self.manager.account_id,
                'cookConfigs': [c.to_dict() for c in cook_configs],
                # readyStart False starts the cook at once; True waits for the
                # start button.
                'readyStart': False,
                'syncType': int(self._get_sync_type(member)),
                'tempUnit': self.temp_unit.code,
                'workChamber': int(member),
            }
        )

        resp = await self.call_bypassv2_api(
            payload_method='startMultiCook',
            data=start_data.to_dict(),
            payload_update=dict(BYPASSV2_SUB_DEVICE_PAYLOAD),
        )
        r = Helpers.process_dev_response(logger, 'set_mode_from_recipe', self, resp)
        if r is None:
            return False

        # Update state for affected chambers
        both = member == AirFryerChamber.BOTH
        chambers = (
            [self.state_chamber_1, self.state_chamber_2]
            if both
            else [self.get_chamber_state(member)]
        )
        self._set_reported_sync(both)
        cook_time = self.convert_time_for_api(recipe.cook_time)
        for ch_state in chambers:
            # readyStart is False, so the cook starts without the start button.
            ch_state.set_state(
                cook_status=AirFryerCookStatus.COOKING,
                cook_time=cook_time,
                cook_last_time=cook_time,
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
        temp_unit: TemperatureUnits | str | None = None,
        preheat_time: int | None = None,
        cook_mode: str | None = None,
        chamber: AirFryerChamber | int = AirFryerChamber.CHAMBER_1,
    ) -> bool:
        """Set cooking mode with manual parameters.

        Args:
            cook_time: Cooking time in seconds.
            cook_temp: Cooking temperature, in ``temp_unit``.
            temp_unit: Unit of ``cook_temp``; defaults to the device's
                current ``temp_unit``. An unrecognised unit string returns
                False without a request.
            preheat_time: Not used for this device.
            cook_mode: Cook mode, an ``AirFryerCookModes`` key or the API
                mode string (e.g. 'AirFry'). None uses the default preset.
            chamber (AirFryerChamber | int): Chamber to cook in. ``BOTH``
                cooks both chambers in sync.

        Returns:
            True if the command was successful.
        """
        del preheat_time  # not supported by this device
        unit = self._resolve_temp_unit(temp_unit)
        if unit is None:
            return False
        recipe = self._recipe_for_set_mode(
            cook_time, cook_temp, cook_mode, None, temp_unit=unit
        )
        if recipe is None:
            return False
        return await self.set_mode_from_recipe(recipe, chamber=chamber)
