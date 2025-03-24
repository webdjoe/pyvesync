"""VeSync Humidifier Devices."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from typing_extensions import deprecated
import orjson

from pyvesync.base_devices.humidifier_base import VeSyncHumidifier
from pyvesync.utils.helpers import Helpers, Validators, Timer
from pyvesync.utils.logs import LibraryLogger
from pyvesync.utils.device_mixins import BypassV2Mixin
from pyvesync.const import DeviceStatus, IntFlag, ConnectionStatus
from pyvesync.models.humidifier_models import (
    ClassicLVHumidResult,
    Levoit1000SResult,
    InnerHumidifierBaseResult,
    ResponseHumidifierBase,
    Superior6000SResult,
)

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel
    from pyvesync.device_map import (
        HumidifierMap
        )


logger = logging.getLogger(__name__)


class VeSyncHumid200300S(BypassV2Mixin, VeSyncHumidifier):
    """200S/300S Humidifier Class."""

    __slots__ = ()

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: HumidifierMap) -> None:
        """Initialize 200S/300S Humidifier class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, resp_model: InnerHumidifierBaseResult) -> None:
        """Set state from get_details API model."""
        if not isinstance(resp_model, ClassicLVHumidResult):
            return
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = DeviceStatus.from_bool(resp_model.enabled)
        self.state.mode = resp_model.mode
        self.state.humidity = resp_model.humidity or IntFlag.NOT_SUPPORTED
        self.state.mist_virtual_level = resp_model.mist_virtual_level or 0
        self.state.mist_level = resp_model.mist_level or 0
        self.state.water_lacks = resp_model.water_lacks
        self.state.humidity_high = resp_model.humidity_high
        self.state.water_tank_lifted = resp_model.water_tank_lifted
        self.state.auto_stop_target_reached = resp_model.automatic_stop_reach_target
        if (
            self.supports_nightlight
            and resp_model.night_light_brightness != IntFlag.NOT_SUPPORTED
        ):
            self.state.nightlight_brightness = resp_model.night_light_brightness
            self.state.nightlight_status = (
                DeviceStatus.ON
                if resp_model.night_light_brightness > 0
                else DeviceStatus.OFF
            )
        self.state.display_status = DeviceStatus.from_bool(resp_model.display)
        if self.supports_warm_mist and resp_model.warm_level != IntFlag.NOT_SUPPORTED:
            self.state.warm_mist_level = resp_model.warm_level
            self.state.warm_mist_enabled = resp_model.warm_enabled
        config = resp_model.configuration
        if config is not None:
            self.state.auto_target_humidity = config.auto_target_humidity
            self.state.automatic_stop_config = config.automatic_stop
            self.state.display_set_status = DeviceStatus.from_bool(config.display)

    async def get_details(self) -> None:
        body = self._build_request("getHumidifierStatus")
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

        r_model = ResponseHumidifierBase.from_dict(r)
        if r_model.result.result is None:
            LibraryLogger.log_device_api_response_error(
                logger,
                self.device_name,
                self.device_type,
                'get_details',
                'Error in result dict from humidifier',
            )
            return
        self._set_state(r_model.result.result)

    async def update(self) -> None:
        await self.get_details()

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status == DeviceStatus.ON

        payload_data = {
                'enabled': toggle,
                'id': 0
        }
        body = self._build_request("setSwitch", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    @deprecated("Use turn_on_automatic_stop() instead.")
    async def automatic_stop_on(self) -> bool:
        """Turn 200S/300S Humidifier automatic stop on."""
        return await self.toggle_automatic_stop(True)

    @deprecated("Use turn_off_automatic_stop() instead.")
    async def automatic_stop_off(self) -> bool:
        """Turn 200S/300S Humidifier automatic stop on."""
        return await self.toggle_automatic_stop(False)

    @deprecated("Use toggle_automatic_stop(toggle: bool) instead.")
    async def set_automatic_stop(self, mode: bool) -> bool:
        """Set 200S/300S Humidifier to automatic stop."""
        return await self.toggle_automatic_stop(mode)

    async def toggle_automatic_stop(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.automatic_stop_config != DeviceStatus.ON

        payload_data = {
            'enabled': toggle
        }
        body = self._build_request("setAutomaticStop", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_automatic_stop", self, r_bytes)
        if r is None:
            return False
        self.state.automatic_stop_config = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    @deprecated("Use toggle_display(toggle: bool) instead.")
    async def set_display(self, toggle: bool) -> bool:
        """Deprecated method to toggle display on/off.

        Use toggle_display(toggle: bool) instead.
        """
        return await self.toggle_display(toggle)

    async def toggle_display(self, toggle: bool) -> bool:
        payload_data = {
            'state': toggle
        }
        body = self._build_request("setDisplay", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_display", self, r_bytes)
        if r is None:
            return False
        self.state.display_set_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_humidity(self, humidity: int) -> bool:
        """Set target 200S/300S Humidifier humidity.

        Args:
            humidity (int): Target humidity level.

        Returns:
            bool: Success of request.
        """
        if not Validators.validate_range(humidity, *self.target_minmax):
            logger.debug(
                "Invalid humidity, must be between &s and %s", *self.target_minmax
            )
            return False

        payload_data = {
            'target_humidity': humidity
        }
        body = self._build_request("setTargetHumidity", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_humidity", self, r_bytes)
        if r is None:
            return False
        self.state.auto_target_humidity = humidity
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_night_light_brightness(self, brightness: int) -> bool:
        """Set 200S/300S Humidifier night light brightness.

        Args:
            brightness (int): Target night light brightness.
        """
        if not self.supports_nightlight:
            logger.debug('%s is a %s does not have a nightlight',
                         self.device_name, self.device_type)
            return False

        if Validators.validate_zero_to_hundred(brightness):
            logger.debug("Brightness value must be set between 0 and 100")
            return False
        payload_data = {
            'night_light_brightness': brightness
        }
        body = self._build_request("setNightLightBrightness", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )

        r = Helpers.process_dev_response(
            logger, "set_night_light_brightness", self, r_bytes
            )
        if r is None:
            return False
        self.state.nightlight_brightness = brightness
        self.state.nightlight_status = (
            DeviceStatus.ON if brightness > 0 else DeviceStatus.OFF
        )
        return True

    @deprecated("Use set_mode(mode: str) instead.")
    async def set_humidity_mode(self, mode: str) -> bool:
        """Deprecated method to set humidifier mode.

        Use `set_mode(mode: str)` instead.
        """
        return await self.set_mode(mode)

    async def set_mode(self, mode: str) -> bool:
        if mode.lower() not in self.mist_modes:
            logger.debug('Invalid humidity mode used - %s',
                         mode)
            logger.debug(
                "Proper modes for this device are - %s",
                orjson.dumps(
                    self.mist_modes, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
                ),
            )
            return False

        payload_data = {
            'mode': self.mist_modes[mode.lower()]
        }
        body = self._build_request("setHumidityMode", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_humidity_mode", self, r_bytes)
        if r is None:
            return False

        self.state.mode = mode
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_warm_level(self, warm_level: int) -> bool:
        """Set target 600S Humidifier mist warmth."""
        if not self.supports_warm_mist:
            logger.debug('%s is a %s does not have a mist warmer',
                         self.device_name, self.device_type)
            return False

        if warm_level not in self.warm_mist_levels:
            logger.debug("warm_level value must be - %s",
                         str(self.warm_mist_levels))
            return False

        payload_data = {
            'type': 'warm',
            'level': warm_level,
            'id': 0,
        }
        body = self._build_request("setVirtualLevel", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_warm_level", self, r_bytes)
        if r is None:
            return False

        self.state.warm_mist_level = warm_level
        self.state.warm_mist_enabled = True
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mist_level(self, level: int) -> bool:
        if level not in self.mist_levels:
            logger.debug(
                "Humidifier mist level must be between %s and %s",
                self.mist_levels[0],
                self.mist_levels[-1],
            )
            return False

        payload_data = {
            'id': 0,
            'level': level,
            'type': 'mist'
        }
        body = self._build_request("setVirtualLevel", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_mist_level", self, r_bytes)
        if r is None:
            return False

        self.state.mist_virtual_level = level
        self.state.mist_level = level
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    # def display(self) -> None:
    #     """Return formatted device info to stdout."""
    #     super().display()
    #     disp = [
    #         ('Mode: ', self.details['mode'], ''),
    #         ('Humidity: ', self.details['humidity'], 'percent'),
    #         ('Mist Virtual Level: ', self.details['mist_virtual_level'], ''),
    #         ('Mist Level: ', self.details['mist_level'], ''),
    #         ('Water Lacks: ', self.details['water_lacks'], ''),
    #         ('Humidity High: ', self.details['humidity_high'], ''),
    #         ('Water Tank Lifted: ', self.details['water_tank_lifted'], ''),
    #         ('Display: ', self.details['display'], ''),
    #         ('Automatic Stop Reach Target: ',
    #             self.details['automatic_stop_reach_target'], ''),
    #         ('Auto Target Humidity: ',
    #             self.config['auto_target_humidity'], 'percent'),
    #         ('Automatic Stop: ', self.config['automatic_stop'], ''),
    #     ]
    #     if self.night_light:
    #         disp.append(('Night Light Brightness: ',
    #                      self.details.get('night_light_brightness', ''), 'percent'))
    #     if self.warm_mist_feature:
    #         disp.append(('Warm mist enabled: ',
    #                      self.details.get('warm_mist_enabled', ''), ''))
    #         disp.append(('Warm mist level: ',
    #                      self.details.get('warm_mist_level', ''), ''))
    #     for line in disp:
    #         print(f'{line[0]:.<30} {line[1]} {line[2]}')

    # def displayJSON(self) -> str:
    #     """Return air purifier status and properties in JSON output."""
    #     sup = super().displayJSON()
    #     sup_val = orjson.loads(sup)
    #     sup_val.update(
    #         {
    #             'Mode': self.details['mode'],
    #             'Humidity': str(self.details['humidity']),
    #             'Mist Virtual Level': str(
    #                 self.details['mist_virtual_level']),
    #             'Mist Level': str(self.details['mist_level']),
    #             'Water Lacks': self.details['water_lacks'],
    #             'Humidity High': self.details['humidity_high'],
    #             'Water Tank Lifted': self.details['water_tank_lifted'],
    #             'Display': self.details['display'],
    #             'Automatic Stop Reach Target': self.details[
    #                 'automatic_stop_reach_target'],
    #             'Auto Target Humidity': str(self.config[
    #                 'auto_target_humidity']),
    #             'Automatic Stop': self.config['automatic_stop'],
    #         }
    #     )
    #     if self.night_light:
    #         sup_val['Night Light Brightness'] = self.details[
    #             'night_light_brightness']
    #     if self.warm_mist_feature:
    #         sup_val['Warm mist enabled'] = self.details['warm_mist_enabled']
    #         sup_val['Warm mist level'] = self.details['warm_mist_level']
    #     return orjson.dumps(
    #         sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode()


class VeSyncHumid200S(VeSyncHumid200300S):
    """Levoit Classic 200S Specific class."""

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: HumidifierMap) -> None:
        """Initialize levoit 200S device class.

        This overrides the `toggle_display(toggle: bool)` method of the
        VeSyncHumid200300S class.
        """
        super().__init__(details, manager, feature_map)

    async def toggle_display(self, toggle: bool) -> bool:
        payload_data = {
            'enabled': toggle,
            'id': 0
        }
        body = self._build_request("setIndicatorLightSwitch", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_display", self, r_bytes)
        if r is None:
            return False
        self.state.display_set_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True


class VeSyncSuperior6000S(BypassV2Mixin, VeSyncHumidifier):
    """Superior 6000S Humidifier."""

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: HumidifierMap) -> None:
        """Initialize Superior 6000S Humidifier class."""
        super().__init__(details, manager, feature_map)
        # self._config_dict = model_features(self.device_type)
        #  Configured in parent
        # self.mist_levels = self._config_dict.get('mist_levels')
        # self.mist_modes = self._config_dict.get('mist_modes')
        # DeviceProp flattened in Response Model
        # self.connection_status = details.get('deviceProp', {}).get(
        #     'connectionStatus', None)

    # def build_api_dict(self, method: str) -> tuple[dict, dict]:
    #     """Build humidifier api call header and body.

    #     Available methods are: 'getHumidifierStatus', 'setSwitch',
    #     'setVirtualLevel', 'setTargetHumidity', 'setHumidityMode',
    #     'setDisplay', 'setDryingMode'
    #     """
    #     if method not in self._api_modes:
    #         logger.debug('Invalid mode - %s', method)
    #         raise ValueError
    #     head = Helpers.bypass_header()
    #     body = Helpers.bypass_body_v2(self.manager)
    #     body['cid'] = self.cid
    #     body['configModule'] = self.config_module
    #     body['payload'] = {
    #         'method': method,
    #         'source': 'APP'
    #     }
    #     return head, body

    # def build_humid_dict(self, dev_dict: dict[str, str]) -> None:
    #     """Build humidifier status dictionary."""
    #     self.device_status = 'off' if dev_dict.get('powerSwitch', 0) == 0 else 'on'
    #     self.mode = 'auto' if dev_dict.get('workMode', '') == 'autoPro' \
    #         else dev_dict.get('workMode', '')
    #     self.details['humidity'] = dev_dict.get('humidity', 0)
    #     self.details['target_humidity'] = dev_dict.get('targetHumidity')
    #     self.details['mist_virtual_level'] = dev_dict.get(
    #         'virtualLevel', 0)
    #     self.details['mist_level'] = dev_dict.get('mistLevel', 0)
    #     self.details['water_lacks'] = dev_dict.get('waterLacksState', False)
    #     self.details['water_tank_lifted'] = dev_dict.get(
    #         'waterTankLifted', False)
    #     self.details['filter_life_percentage'] = dev_dict.get('filterLifePercent', 0)
    #     self.details['temperature'] = dev_dict.get('temperature', 0)  # TODO: temp unit?
    #     self.details['display'] = dev_dict.get('screenSwitch')
    #     self.details['drying_mode'] = dev_dict.get('dryingMode', {})

    def _set_state(self, resp_model: Superior6000SResult) -> None:
        """Set state from Superior 6000S API result model."""
        self.state.device_status = DeviceStatus.from_int(resp_model.powerSwitch)
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.mode = resp_model.workMode
        self.state.auto_target_humidity = resp_model.targetHumidity
        self.state.mist_level = resp_model.mistLevel
        self.state.mist_virtual_level = resp_model.virtualLevel
        self.state.water_lacks = bool(resp_model.waterLacksState)
        self.state.water_tank_lifted = bool(resp_model.waterTankLifted)
        self.state.automatic_stop_config = bool(resp_model.autoStopSwitch)
        self.state.auto_stop_target_reached = bool(resp_model.autoStopState)
        self.state.display_set_status = DeviceStatus.from_int(resp_model.screenSwitch)
        self.state.display_status = DeviceStatus.from_int(resp_model.screenState)
        self.state.auto_preference = resp_model.autoPreference
        self.state.filter_life_percent = resp_model.filterLifePercent
        self.state.temperature = resp_model.temperature  # Unknown units

        drying_mode = resp_model.dryingMode
        if drying_mode is not None:
            self.state.drying_mode_status = DeviceStatus.from_int(drying_mode.dryingState)
            self.state.drying_mode_level = drying_mode.dryingLevel
            self.state.drying_mode_auto_switch = DeviceStatus.from_int(
                drying_mode.autoDryingSwitch
                )

        if resp_model.timerRemain > 0:
            self.state.timer = Timer(
                resp_model.timerRemain,
                DeviceStatus.from_bool(self.state.device_status != DeviceStatus.ON)
            )

    async def get_details(self) -> None:
        body = self._build_request("getHumidifierStatus")
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

        r_model = ResponseHumidifierBase.from_dict(r)
        if not isinstance(r_model.result.result, Superior6000SResult):
            LibraryLogger.log_device_api_response_error(
                logger,
                self.device_name,
                self.device_type,
                'get_details',
                'Error in result dict from humidifier',
            )
            return

        result = r_model.result.result
        self._set_state(result)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON

        payload_data = {
                'powerSwitch': int(toggle),
                'switchIdx': 0
            }
        body = self._build_request("setSwitch", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    @deprecated("Use toggle_drying_mode() instead.")
    async def set_drying_mode_enabled(self, mode: bool) -> bool:
        """Set drying mode on/off."""
        return await self.toggle_drying_mode(mode)

    async def toggle_drying_mode(self, toggle: bool | None = None) -> bool:
        """enable/disable drying filters after turning off."""
        if toggle is None:
            toggle = self.state.drying_mode_status != DeviceStatus.ON

        payload_data = {
            'autoDryingSwitch': int(toggle)
        }
        body = self._build_request("setDryingMode", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_drying_mode_enabled", self, r_bytes)
        if r is None:
            return False
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.drying_mode_auto_switch = DeviceStatus.from_bool(toggle)
        return True

    @deprecated("Use toggle_display() instead.")
    async def set_display_enabled(self, mode: bool) -> bool:
        """Set display on/off."""
        return await self.toggle_display(mode)

    async def toggle_display(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.display_set_status != DeviceStatus.ON

        payload_data = {
            'screenSwitch': int(toggle)
        }
        body = self._build_request("setDisplay", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_display", self, r_bytes)
        if r is None:
            return False
        self.state.display_set_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_humidity(self, humidity: int) -> bool:
        """Set target humidity for humidity mode."""
        if Validators.validate_range(humidity, *self.target_minmax):
            logger.debug("Humidity value must be set between 30 and 80")
            return False

        payload_data = {
            'targetHumidity': humidity
        }
        body = self._build_request("setTargetHumidity", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_humidity", self, r_bytes)
        if r is None:
            return False
        self.state.auto_target_humidity = humidity
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    @deprecated("Use set_mode(mode: str) instead.")
    async def set_humidity_mode(self, mode: str) -> bool:
        """Set humidifier mode."""
        return await self.set_mode(mode)

    async def set_mode(self, mode: str) -> bool:
        if mode.lower() not in self.mist_modes:
            logger.debug('Invalid humidity mode used - %s',
                         mode)
            logger.debug(
                "Proper modes for this device are - %s",
                orjson.dumps(
                    self.mist_modes, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
                ),
            )
            return False

        # head, body = self.build_api_dict('setHumidityMode')
        # if not head and not body:
        #     return False
        # body['payload']['data'] = {
        #     'workMode': 'autoPro' if mode == 'auto' else mode
        # }
        payload_data = {
            'workMode': self.mist_modes[mode.lower()]
        }
        body = self._build_request("setHumidityMode", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_humidity_mode", self, r_bytes)
        if r is None:
            return False
        self.state.mode = mode
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    @deprecated("Use turn_on_automatic_stop() instead.")
    async def automatic_stop_on(self) -> bool:
        """Set humidity mode to auto.

        Deprecated, please use turn_on_automatic_stop() instead.
        """
        return await self.set_mode('auto')

    @deprecated("Use turn_off_automatic_stop() instead.")
    async def automatic_stop_off(self) -> bool:
        """Set humidity mode to manual.

        Deprecated, please use turn_off_automatic_stop() instead.
        """
        return await self.set_mode('manual')

    async def set_mist_level(self, level: int) -> bool:
        if level not in self.mist_levels:
            logger.debug("Humidifier mist level must be between 0 and 9")
            return False

        payload_data = {
            'levelIdx': 0,
            'virtualLevel': level,
            'levelType': 'mist'
        }
        body = self._build_request("setVirtualLevel", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_mist_level", self, r_bytes)
        if r is None:
            return False
        self.state.mist_level = level
        self.state.mist_virtual_level = level
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    # def display(self) -> None:
    #     """Return formatted device info to stdout."""
    #     super().display()
    #     disp = [
    #         ('Temperature', self.temperature, ''),
    #         ('Humidity: ', self.humidity_level, 'percent'),
    #         ('Target Humidity', self.target_humidity, 'percent'),
    #         ('Mode: ', self.mode, ''),
    #         ('Mist Virtual Level: ', self.details['mist_virtual_level'], ''),
    #         ('Mist Level: ', self.details['mist_level'], ''),
    #         ('Water Lacks: ', self.water_lacks, ''),
    #         ('Water Tank Lifted: ', bool(self.details['water_tank_lifted']), ''),
    #         ('Display On: ', bool(self.details['display']), ''),
    #         ('Filter Life', self.details['filter_life_percentage'], 'percent'),
    #         ('Drying Mode Enabled', self.drying_mode_enabled, ''),
    #         ('Drying Mode State', self.drying_mode_state, ''),
    #         ('Drying Mode Level', self.drying_mode_level, ''),
    #         ('Drying Mode Time Remain', self.drying_mode_seconds_remaining, 'seconds'),
    #     ]
    #     for line in disp:
    #         print(f'{line[0]:.<30} {line[1]} {line[2]}')

    # def displayJSON(self) -> str:
    #     """Return air purifier status and properties in JSON output."""
    #     sup = super().displayJSON()
    #     sup_val = orjson.loads(sup)
    #     sup_val.update(
    #         {
    #             'Temperature': self.temperature,
    #             'Humidity': self.humidity_level,
    #             'Target Humidity': self.target_humidity,
    #             'Mode': self.mode,
    #             'Mist Virtual Level': self.mist_virtual_level,
    #             'Mist Level': self.mist_level,
    #             'Water Lacks': self.details['water_lacks'],
    #             'Water Tank Lifted': bool(self.details['water_tank_lifted']),
    #             'Display On': bool(self.details['display']),
    #             'Filter Life': self.details['filter_life_percentage'],
    #             'Drying Mode Enabled': self.drying_mode_enabled,
    #             'Drying Mode State': self.drying_mode_state,
    #             'Drying Mode Level': self.drying_mode_level,
    #             'Drying Mode Time Remaining': self.drying_mode_seconds_remaining,
    #         }
    #     )
    #     return orjson.dumps(
    #         sup_val, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS).decode()


class VeSyncHumid1000S(VeSyncHumid200300S):
    """Levoit OasisMist 1000S Specific class."""

    def __init__(self, details: ResponseDeviceDetailsModel,
                 manager: VeSync, feature_map: HumidifierMap) -> None:
        """Initialize levoit 1000S device class."""
        super().__init__(details, manager, feature_map)
        # DeviceProp flattened in ResponseDeviceListModel
        # self.connection_status = details.get('deviceProp', {}).get(
        #     'connectionStatus', None)

    def _set_state(self, resp_model: InnerHumidifierBaseResult) -> None:
        """Set state of Levoit 1000S from API result model."""
        if not isinstance(resp_model, Levoit1000SResult):
            return
        self.state.device_status = DeviceStatus.from_int(resp_model.powerSwitch)
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.mode = resp_model.workMode
        self.state.auto_target_humidity = resp_model.targetHumidity
        self.state.mist_level = resp_model.mistLevel
        self.state.mist_virtual_level = resp_model.virtualLevel
        self.state.water_lacks = bool(resp_model.waterLacksState)
        self.state.water_tank_lifted = bool(resp_model.waterTankLifted)
        self.state.automatic_stop_config = bool(resp_model.autoStopSwitch)
        self.state.auto_stop_target_reached = bool(resp_model.autoStopState)
        self.state.display_set_status = DeviceStatus.from_int(resp_model.screenSwitch)
        self.state.display_status = DeviceStatus.from_int(resp_model.screenState)

    # def build_config_dict(self, conf_dict: dict) -> None:
    #     """Build configuration dict for humidifier."""
    #     self.config['auto_target_humidity'] = conf_dict.get(
    #         'targetHumidity', 0)
    #     self.config['display'] = bool(conf_dict.get('screenSwitch', 0))
    #     self.config['automatic_stop'] = bool(conf_dict.get('autoStopSwitch', 1))

    # async def get_details(self) -> None:
    #     """Build Humidifier details dictionary."""
    #     head = Helpers.bypass_header()
    #     body = Helpers.bypass_body_v2(self.manager)
    #     body['cid'] = self.cid
    #     body['configModule'] = self.config_module
    #     body['payload'] = {
    #         'method': 'getHumidifierStatus',
    #         'source': 'APP',
    #         'data': {}
    #     }

    #     r_bytes, _ = await self.manager.async_call_api(
    #         '/cloud/v2/deviceManaged/bypassV2',
    #         method='post',
    #         headers=head,
    #         json_object=body,
    #     )
    #     r = Helpers.process_dev_response(logger, "get_details", self, r_bytes)
    #     if r is None:
    #         return

    #     outer_result = r.get('result', {})
    #     inner_result = outer_result.get('result', {})

    #     if outer_result is None or inner_result is None:
    #         LibraryLogger.log_device_api_response_error(
    #             logger,
    #             self.device_name,
    #             self.device_type,
    #             "get_details",
    #             "Error in inner result dict from humidifier",
    #         )
    #         return
    #     if outer_result.get('code') != 0:
    #         error_info = ErrorCodes.get_error_info(outer_result.get('code'))
    #         if error_info.device_online is False:
    #             self.connection_status = 'offline'
    #         LibraryLogger.log_device_return_code(
    #             logger,
    #             self.device_name,
    #             self.device_type,
    #             'get_details',
    #             outer_result.get('code'),
    #             error_info.message
    #         )
    #         return

    #     self.connection_status = 'online'
    #     self.build_humid_dict(inner_result)
    #     self.build_config_dict(inner_result.get('configuration', {}))
    #     return

    @deprecated("Use toggle_switch() instead.")
    async def set_display(self, toggle: bool) -> bool:
        """Toggle display on/off.

        This is a deprecated method, please use toggle_display() instead.
        """
        return await self.toggle_switch(toggle)

    async def toggle_display(self, toggle: bool) -> bool:
        """Toggle display on/off."""
        payload_data = {
            'screenSwitch': int(toggle)
        }
        body = self._build_request("setDisplay", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_display", self, r_bytes)
        if r is None:
            return False
        self.state.display_set_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    @deprecated("Use set_mode() instead.")
    async def set_humidity_mode(self, mode: str) -> bool:
        """Set humidifier mode - sleep, auto or manual.

        Deprecated, please use set_mode() instead.
        """
        return await self.set_mode(mode)

    async def set_mode(self, mode: str) -> bool:
        """Set humidifier mode - sleep, auto or manual."""
        if mode.lower() not in self.mist_modes:
            logger.debug("Invalid humidity mode used - %s", mode)
            logger.debug(
                "Proper modes for this device are - %s",
                orjson.dumps(
                    self.mist_modes, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
                ),
            )
            return False

        payload_data = {
            'workMode': mode.lower()
        }
        body = self._build_request("setHumidityMode", payload_data)
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

    async def set_mist_level(self, level: int) -> bool:
        """Set humidifier mist level with int."""
        if level not in self.mist_levels:
            logger.debug('Humidifier mist level out of range')
            return False

        payload_data = {
            'levelIdx': 0,
            'virtualLevel': level,
            'levelType': 'mist'
        }
        body = self._build_request('virtualLevel', payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_mist_level", self, r_bytes)
        if r is None:
            return False

        self.state.mist_level = level
        self.state.mist_virtual_level = level
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        """Toggle humidifier on/off."""
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON

        payload_data = {
                'powerSwitch': int(toggle),
                'switchIdx': 0
            }
        body = self._build_request("setSwitch", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "toggle_switch", self, r_bytes)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_humidity(self, humidity: int) -> bool:
        if Validators.validate_range(humidity, *self.target_minmax):
            logger.debug("Humidity value must be set between %s and %s",
                         self.target_minmax[0], self.target_minmax[1])
            return False

        payload_data = {
            'targetHumidity': humidity
        }
        body = self._build_request("setTargetHumidity", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_humidity", self, r_bytes)
        if r is None:
            return False
        self.state.auto_target_humidity = humidity
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    @deprecated("Use toggle_automatic_stop() instead.")
    async def set_automatic_stop(self, mode: bool) -> bool:
        return await self.toggle_automatic_stop(mode)

    async def toggle_automatic_stop(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.automatic_stop_config != DeviceStatus.ON

        payload_data = {
            'autoStopSwitch': int(toggle)
        }
        body = self._build_request("setAutoStopSwitch", payload_data)
        headers = Helpers.req_header_bypass()

        r_bytes, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, "set_automatic_stop", self, r_bytes)

        if r is None:
            return False
        self.state.automatic_stop_config = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True
