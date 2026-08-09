"""VeSync Humidifier Devices."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import orjson
from typing_extensions import deprecated

from pyvesync.base_devices.humidifier_base import BreathingLampState, VeSyncHumidifier
from pyvesync.const import (
    RGB_FULL_BRIGHTNESS,
    RGB_STALE_DATA_TIMEOUT,
    ConnectionStatus,
    DeviceStatus,
    DryingModes,
)
from pyvesync.models import humidifier_models as models
from pyvesync.models.bypass_models import (
    ResultV2GetTimer,
    ResultV2GetTimerV2,
    ResultV2SetTimer,
)
from pyvesync.utils.colors import RGBNightlightColor
from pyvesync.utils.device_mixins import BypassV2Mixin, process_bypassv2_result
from pyvesync.utils.helpers import Helpers, Timer, Validators

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.device_map import HumidifierMap
    from pyvesync.models.vesync_models import ResponseDeviceDetailsModel


logger = logging.getLogger(__name__)


class VeSyncHumid200300S(BypassV2Mixin, VeSyncHumidifier):
    """300S Humidifier Class.

    Primary class for VeSync humidifier devices.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The manager object for API calls.
        feature_map (HumidifierMap): The feature map for the device.

    Attributes:
        state (HumidifierState): The state of the humidifier.
        last_response (ResponseInfo): Last response info from API call.
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
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        mist_levels (list): List of mist levels.
        mist_modes (list): List of mist modes.
        target_minmax (tuple): Tuple of target min and max values.
        warm_mist_levels (list): List of warm mist levels.
    """

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: HumidifierMap,
    ) -> None:
        """Initialize 200S/300S Humidifier class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, resp_model: models.ClassicLVHumidResult) -> None:
        """Set state from get_details API model."""
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.device_status = DeviceStatus.from_bool(resp_model.enabled)
        self.state.mode = self._reverse_mist_modes.get(resp_model.mode)
        self.state.humidity = resp_model.humidity
        self.state.mist_virtual_level = resp_model.mist_virtual_level or 0
        self.state.mist_level = resp_model.mist_level or 0
        self.state.water_lacks = resp_model.water_lacks
        self.state.humidity_high = resp_model.humidity_high
        self.state.water_tank_lifted = resp_model.water_tank_lifted
        self.state.auto_stop_target_reached = resp_model.automatic_stop_reach_target
        if self.supports_nightlight and resp_model.night_light_brightness is not None:
            self.state.nightlight_brightness = resp_model.night_light_brightness
            self.state.nightlight_status = (
                DeviceStatus.ON
                if resp_model.night_light_brightness > 0
                else DeviceStatus.OFF
            )
        self.state.display_status = DeviceStatus.from_bool(resp_model.display)
        if self.supports_warm_mist and resp_model.warm_level is not None:
            self.state.warm_mist_level = resp_model.warm_level
            self.state.warm_mist_enabled = resp_model.warm_enabled
        if self.supports_rgb_nightlight and resp_model.rgbNightLight is not None:
            self._set_rgb_nightlight_state(resp_model.rgbNightLight)

        config = resp_model.configuration
        if config is not None:
            self.state.auto_target_humidity = config.auto_target_humidity
            self.state.automatic_stop_config = config.automatic_stop
            self.state.display_set_status = DeviceStatus.from_bool(config.display)

    def _set_rgb_nightlight_state(self, rgb: models.RGBNightLight) -> None:
        # Skip updating RGB nightlight state if we recently set it. The
        # VeSync API returns stale data for several minutes after setting
        # values, so we ignore updates briefly after a set command.
        if (
            self.state.rgb_nightlight_set_time is not None
            and (time.time() - self.state.rgb_nightlight_set_time)
            < RGB_STALE_DATA_TIMEOUT
        ):
            return

        self.state.rgb_nightlight_status = rgb.action
        self.state.rgb_nightlight_brightness = rgb.brightness
        self.state.rgb_nightlight_color_mode = rgb.colorMode
        # The API uses brightness-adjusted RGB values. Store the base color
        # at full brightness so that changing only brightness doesn't drift.
        brightness_adjusted = (
            rgb.brightness is not None and 0 < rgb.brightness < RGB_FULL_BRIGHTNESS
        )
        if brightness_adjusted:
            base_r, base_g, base_b = RGBNightlightColor.normalize_to_full_brightness(
                rgb.red, rgb.green, rgb.blue
            )
            self.state.rgb_nightlight_red = base_r
            self.state.rgb_nightlight_green = base_g
            self.state.rgb_nightlight_blue = base_b
        else:
            self.state.rgb_nightlight_red = rgb.red
            self.state.rgb_nightlight_green = rgb.green
            self.state.rgb_nightlight_blue = rgb.blue
        # Clear the set time since we've now received valid data from API
        self.state.rgb_nightlight_set_time = None

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv2_api('getHumidifierStatus')
        r_model = process_bypassv2_result(
            self, logger, 'get_details', r_dict, models.ClassicLVHumidResult
        )
        if r_model is None:
            return
        self._set_state(r_model)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status == DeviceStatus.ON

        payload_data = {'enabled': toggle, 'id': 0}
        r_dict = await self.call_bypassv2_api('setSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_switch', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def get_timer(self) -> Timer | None:
        r_dict = await self.call_bypassv2_api('getTimer')
        result_model = process_bypassv2_result(
            self, logger, 'get_timer', r_dict, ResultV2GetTimer
        )
        if result_model is None:
            return None
        if not result_model.timers:
            logger.debug('No timers found')
            return None
        timer = result_model.timers[0]
        self.state.timer = Timer(
            timer_duration=timer.total,
            action=timer.action,
            id=timer.id,
        )
        return self.state.timer

    async def clear_timer(self) -> bool:
        if self.state.timer is None:
            logger.debug('No timer to clear, run get_timer() first.')
            return False
        payload = {
            'id': self.state.timer.id,
        }
        r_dict = await self.call_bypassv2_api('delTimer', payload)
        r = Helpers.process_dev_response(logger, 'clear_timer', self, r_dict)
        if r is None:
            return False
        self.state.timer = None
        return True

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        if action is None:
            action = (
                DeviceStatus.OFF
                if self.state.device_status == DeviceStatus.ON
                else DeviceStatus.ON
            )
        payload_data = {
            'action': str(action),
            'total': duration,
        }
        r_dict = await self.call_bypassv2_api('addTimer', payload_data)
        r = process_bypassv2_result(self, logger, 'set_timer', r_dict, ResultV2SetTimer)
        if r is None:
            return False

        self.state.timer = Timer(
            timer_duration=duration, action=action, id=r.id, remaining=0
        )
        return True

    @deprecated('Use turn_on_automatic_stop() instead.')
    async def automatic_stop_on(self) -> bool:
        """Turn 200S/300S Humidifier automatic stop on."""
        return await self.toggle_automatic_stop(True)

    @deprecated('Use turn_off_automatic_stop() instead.')
    async def automatic_stop_off(self) -> bool:
        """Turn 200S/300S Humidifier automatic stop on."""
        return await self.toggle_automatic_stop(False)

    @deprecated('Use toggle_automatic_stop(toggle: bool) instead.')
    async def set_automatic_stop(self, mode: bool) -> bool:
        """Set 200S/300S Humidifier to automatic stop."""
        return await self.toggle_automatic_stop(mode)

    async def toggle_automatic_stop(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.automatic_stop_config is not True

        payload_data = {'enabled': toggle}
        r_dict = await self.call_bypassv2_api('setAutomaticStop', payload_data)
        r = Helpers.process_dev_response(logger, 'set_automatic_stop', self, r_dict)
        if r is None:
            return False

        self.state.automatic_stop_config = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    @deprecated('Use toggle_display(toggle: bool) instead.')
    async def set_display(self, toggle: bool) -> bool:
        """Deprecated method to toggle display on/off.

        Use toggle_display(toggle: bool) instead.
        """
        return await self.toggle_display(toggle)

    async def toggle_display(self, toggle: bool) -> bool:
        payload_data = {'state': toggle}
        r_dict = await self.call_bypassv2_api('setDisplay', payload_data)
        r = Helpers.process_dev_response(logger, 'set_display', self, r_dict)
        if r is None:
            return False
        self.state.display_set_status = DeviceStatus.from_bool(toggle)
        self.state.display_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_humidity(self, humidity: int) -> bool:
        if not Validators.validate_range(humidity, *self.target_minmax):
            logger.warning(
                'Invalid humidity, must be between %s and %s', *self.target_minmax
            )
            return False

        payload_data = {'target_humidity': humidity}
        r_dict = await self.call_bypassv2_api('setTargetHumidity', payload_data)
        r = Helpers.process_dev_response(logger, 'set_humidity', self, r_dict)
        if r is None:
            return False
        self.state.auto_target_humidity = humidity
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_nightlight_brightness(self, brightness: int) -> bool:
        if not self.supports_nightlight:
            logger.warning(
                '%s is a %s does not have a nightlight or it is not supported.',
                self.device_name,
                self.device_type,
            )
            return False

        if not Validators.validate_zero_to_hundred(brightness):
            logger.warning('Brightness value must be set between 0 and 100')
            return False

        payload_data = {'night_light_brightness': brightness}
        r_dict = await self.call_bypassv2_api('setNightLightBrightness', payload_data)
        r = Helpers.process_dev_response(
            logger, 'set_night_light_brightness', self, r_dict
        )
        if r is None:
            return False
        self.state.nightlight_brightness = brightness
        self.state.nightlight_status = (
            DeviceStatus.ON if brightness > 0 else DeviceStatus.OFF
        )
        return True

    async def toggle_nightlight(self, toggle: bool | None = None) -> bool:
        if not self.supports_nightlight:
            logger.warning(
                '%s is a %s does not have a nightlight or it is not supported.',
                self.device_name,
                self.device_type,
            )
            return False

        if toggle is None:
            toggle = self.state.nightlight_status != DeviceStatus.ON
        brightness = 100 if toggle else 0
        return await self.set_nightlight_brightness(brightness)

    async def set_rgb_nightlight(  # noqa: C901, PLR0912
        self,
        power: bool | None = None,
        brightness: int | None = None,
        red: int | None = None,
        green: int | None = None,
        blue: int | None = None,
    ) -> bool:
        """Set RGB nightlight state and color.

        Args:
            power: Turn nightlight on (True) or off (False).
            brightness: Brightness level (0-100); values below 40 are raised to
                the device minimum of 40. Out-of-range values are rejected.
            red: Red color value (0-255).
            green: Green color value (0-255).
            blue: Blue color value (0-255).

        Returns:
            bool: Success of request.
        """
        if not self.supports_rgb_nightlight:
            logger.warning('RGB Nightlight is not supported for %s', self.device_name)
            return False

        # API requires all fields, so use current state for any not provided.
        if power is not None:
            action = 'on' if power else 'off'
        else:
            action = self.state.rgb_nightlight_status or 'on'
        turning_off = action == 'off'

        # Coalesce with `is None` so a legitimately stored 0 channel survives.
        if brightness is None:
            brightness = (
                self.state.rgb_nightlight_brightness
                if self.state.rgb_nightlight_brightness is not None
                else 40
            )
        if red is None:
            red = (
                self.state.rgb_nightlight_red
                if self.state.rgb_nightlight_red is not None
                else 255
            )
        if green is None:
            green = (
                self.state.rgb_nightlight_green
                if self.state.rgb_nightlight_green is not None
                else 255
            )
        if blue is None:
            blue = (
                self.state.rgb_nightlight_blue
                if self.state.rgb_nightlight_blue is not None
                else 255
            )
        color_mode = self.state.rgb_nightlight_color_mode or 'color'

        # Validate and reject rather than silently clamping bad input.
        if not Validators.validate_range(brightness, 0, 100):
            logger.warning('Brightness must be between 0 and 100')
            return False
        if not Validators.validate_rgb(red, green, blue):
            logger.warning('RGB values must be between 0 and 255')
            return False

        # Device minimum brightness is 40 per the VeSync app.
        brightness = max(40, brightness)

        # Calculate colorSliderLocation from the base RGB color (full brightness).
        color_slider_location = RGBNightlightColor.rgb_to_color_slider_location(
            red, green, blue
        )

        # The VeSync app sends brightness-adjusted RGB, not raw color + brightness.
        # From decompiled app: yv/p.java method b() and RGBNightLightView.java
        if brightness != RGB_FULL_BRIGHTNESS:
            adj_red, adj_green, adj_blue = RGBNightlightColor.apply_brightness_to_rgb(
                red, green, blue, brightness
            )
        else:
            adj_red, adj_green, adj_blue = red, green, blue

        payload_data: dict[str, int | str] = {
            'action': action,
            'brightness': brightness,
            'red': adj_red,
            'green': adj_green,
            'blue': adj_blue,
            'colorMode': color_mode,
            'speed': 0,
            'colorSliderLocation': color_slider_location,
        }

        r_dict = await self.call_bypassv2_api('setLightStatus', payload_data)
        r = Helpers.process_dev_response(logger, 'set_rgb_nightlight', self, r_dict)
        if r is None:
            return False

        # process_dev_response already set connection_status; update local state
        # and record the timestamp used to ignore stale API responses briefly.
        self.state.rgb_nightlight_status = action
        # An off command must not overwrite the stored color/brightness so the
        # previous setting is restored on the next power-on.
        if not turning_off:
            self.state.rgb_nightlight_brightness = brightness
            self.state.rgb_nightlight_red = red
            self.state.rgb_nightlight_green = green
            self.state.rgb_nightlight_blue = blue
            self.state.rgb_nightlight_color_mode = color_mode
        self.state.rgb_nightlight_set_time = time.time()

        return True

    async def set_mode(self, mode: str) -> bool:
        if mode not in self.mist_modes:
            logger.warning('Invalid humidity mode used - %s', mode)
            logger.info(
                'Proper modes for this device are - %s',
                orjson.dumps(
                    self.mist_modes, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
                ),
            )
            return False

        payload_data = {'mode': self.mist_modes[mode]}
        r_dict = await self.call_bypassv2_api('setHumidityMode', payload_data)
        r = Helpers.process_dev_response(logger, 'set_humidity_mode', self, r_dict)
        if r is None:
            return False

        self.state.mode = mode
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_warm_level(self, warm_level: int) -> bool:
        if not self.supports_warm_mist:
            logger.debug(
                '%s is a %s does not have a mist warmer',
                self.device_name,
                self.device_type,
            )
            return False

        if warm_level not in self.warm_mist_levels:
            logger.warning('warm_level value must be - %s', str(self.warm_mist_levels))
            return False

        payload_data = {'type': 'warm', 'level': warm_level, 'id': 0}
        r_dict = await self.call_bypassv2_api('setVirtualLevel', payload_data)
        r = Helpers.process_dev_response(logger, 'set_warm_level', self, r_dict)
        if r is None:
            return False

        self.state.warm_mist_level = warm_level
        self.state.warm_mist_enabled = True
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mist_level(self, level: int) -> bool:
        if level not in self.mist_levels:
            logger.warning(
                'Humidifier mist level must be between %s and %s',
                self.mist_levels[0],
                self.mist_levels[-1],
            )
            return False

        payload_data = {'id': 0, 'level': level, 'type': 'mist'}
        r_dict = await self.call_bypassv2_api('setVirtualLevel', payload_data)
        r = Helpers.process_dev_response(logger, 'set_mist_level', self, r_dict)
        if r is None:
            return False

        self.state.mist_virtual_level = level
        self.state.mist_level = level
        self.state.connection_status = ConnectionStatus.ONLINE
        return True


class VeSyncHumid200S(VeSyncHumid200300S):
    """Levoit Classic 200S Specific class.

    Overrides the `toggle_display(toggle: bool)` method of the
    VeSyncHumid200300S class.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The manager object for API calls.
        feature_map (HumidifierMap): The feature map for the device.

    Attributes:
        state (HumidifierState): The state of the humidifier.
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
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        mist_levels (list): List of mist levels.
        mist_modes (list): List of mist modes.
        target_minmax (tuple): Tuple of target min and max values.
        warm_mist_levels (list): List of warm mist levels.
    """

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: HumidifierMap,
    ) -> None:
        """Initialize levoit 200S device class.

        This overrides the `toggle_display(toggle: bool)` method of the
        VeSyncHumid200300S class.
        """
        super().__init__(details, manager, feature_map)

    async def toggle_display(self, toggle: bool) -> bool:
        payload_data = {'enabled': toggle, 'id': 0}
        r_dict = await self.call_bypassv2_api('setIndicatorLightSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_display', self, r_dict)
        if r is None:
            return False

        self.state.display_set_status = DeviceStatus.from_bool(toggle)
        self.state.display_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True


class VeSyncSuperior6000S(BypassV2Mixin, VeSyncHumidifier):
    """Superior 6000S Humidifier.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The manager object for API calls.
        feature_map (HumidifierMap): The feature map for the device.

    Attributes:
        state (HumidifierState): The state of the humidifier.
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
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        mist_levels (list): List of mist levels.
        mist_modes (list): List of mist modes.
        target_minmax (tuple): Tuple of target min and max values.
        warm_mist_levels (list): List of warm mist levels.
    """

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: HumidifierMap,
    ) -> None:
        """Initialize Superior 6000S Humidifier class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, resp_model: models.Superior6000SResult) -> None:
        """Set state from Superior 6000S API result model."""
        self.state.device_status = DeviceStatus.from_int(resp_model.powerSwitch)
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.mode = self._reverse_mist_modes.get(resp_model.workMode)
        if self.state.mode is None:
            logger.warning('Unknown mist mode received: %s', resp_model.workMode)

        self.state.auto_target_humidity = resp_model.targetHumidity
        self.state.humidity = resp_model.humidity
        self.state.mist_level = resp_model.mistLevel
        self.state.mist_virtual_level = resp_model.virtualLevel
        self.state.water_lacks = bool(resp_model.waterLacksState)
        self.state.water_tank_lifted = bool(resp_model.waterTankLifted)
        self.state.automatic_stop_config = bool(resp_model.autoStopSwitch)
        self.state.auto_stop_target_reached = bool(resp_model.autoStopState)
        self.state.display_set_status = DeviceStatus.from_int(resp_model.screenState)
        self.state.display_status = DeviceStatus.from_int(resp_model.screenState)
        self.state.auto_preference = resp_model.autoPreference
        self.state.filter_life = resp_model.filterLifePercent
        self.state.child_lock = bool(resp_model.childLockSwitch)
        self.state.temperature = (
            resp_model.temperature / 10
        )  # Fahrenheit but without decimals

        drying_mode = resp_model.dryingMode
        if drying_mode is not None:
            self.state.drying_mode_status = DryingModes.from_int(drying_mode.dryingState)
            self.state.drying_mode_auto_switch = DeviceStatus.from_int(
                drying_mode.autoDryingSwitch
            )
            self.state.drying_mode_level = drying_mode.dryingLevel
            self.state.drying_mode_time_remain = drying_mode.dryingRemain
        if resp_model.timerRemain > 0:
            self.state.timer = Timer(
                resp_model.timerRemain,
                DeviceStatus.from_bool(self.state.device_status != DeviceStatus.ON),
            )

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv2_api('getHumidifierStatus')
        r_model = process_bypassv2_result(
            self, logger, 'get_details', r_dict, models.Superior6000SResult
        )
        if r_model is None:
            return

        self._set_state(r_model)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON

        payload_data = {'powerSwitch': int(toggle), 'switchIdx': 0}
        r_dict = await self.call_bypassv2_api('setSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_switch', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_automatic_stop(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.automatic_stop_config is not True

        payload_data = {'autoStopSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setAutoStopSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_automatic_stop', self, r_dict)
        if r is None:
            return False

        self.state.automatic_stop_config = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_drying_mode(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.drying_mode_status != DeviceStatus.ON

        payload_data = {'autoDryingSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setDryingMode', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_drying_mode', self, r_dict)
        if r is None:
            return False

        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.drying_mode_auto_switch = DeviceStatus.from_bool(toggle)
        return True

    async def toggle_display(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.display_set_status != DeviceStatus.ON

        payload_data = {'screenSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setDisplay', payload_data)
        r = Helpers.process_dev_response(logger, 'set_display', self, r_dict)
        if r is None:
            return False

        self.state.display_set_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_humidity(self, humidity: int) -> bool:
        if not Validators.validate_range(humidity, *self.target_minmax):
            logger.warning('Humidity value must be set between 30 and 80')
            return False

        payload_data = {'targetHumidity': humidity}
        r_dict = await self.call_bypassv2_api('setTargetHumidity', payload_data)
        r = Helpers.process_dev_response(logger, 'set_humidity', self, r_dict)
        if r is None:
            return False

        self.state.auto_target_humidity = humidity
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mode(self, mode: str) -> bool:
        if mode not in self.mist_modes:
            logger.warning('Invalid humidity mode used - %s', mode)
            logger.info(
                'Proper modes for this device are - %s',
                orjson.dumps(
                    self.mist_modes, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
                ),
            )
            return False

        payload_data = {'workMode': self.mist_modes[mode]}
        r_dict = await self.call_bypassv2_api('setHumidityMode', payload_data)

        r = Helpers.process_dev_response(logger, 'set_humidity_mode', self, r_dict)
        if r is None:
            return False

        self.state.mode = mode
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mist_level(self, level: int) -> bool:
        if level not in self.mist_levels:
            logger.warning('Humidifier mist level must be between 0 and 9')
            return False

        payload_data = {'levelIdx': 0, 'virtualLevel': level, 'levelType': 'mist'}
        r_dict = await self.call_bypassv2_api('setVirtualLevel', payload_data)
        r = Helpers.process_dev_response(logger, 'set_mist_level', self, r_dict)
        if r is None:
            return False

        self.state.mist_level = level
        self.state.mist_virtual_level = level
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_child_lock(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.child_lock is True

        payload_data = {'childLockSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setChildLock', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_child_lock', self, r_dict)
        if r is None:
            return False

        self.state.child_lock = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True


class VeSyncHumid1000S(VeSyncHumid200300S):
    """Levoit OasisMist 1000S Specific class.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The manager object for API calls.
        feature_map (HumidifierMap): The feature map for the device.

    Attributes:
        state (HumidifierState): The state of the humidifier.
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
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        mist_levels (list): List of mist levels.
        mist_modes (list): List of mist modes.
        target_minmax (tuple): Tuple of target min and max values.
        warm_mist_levels (list): List of warm mist levels.
    """

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: HumidifierMap,
    ) -> None:
        """Initialize levoit 1000S device class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, resp_model: models.InnerHumidifierBaseResult) -> None:
        """Set state of Levoit 1000S from API result model."""
        if not isinstance(resp_model, models.Levoit1000SResult):
            return
        self.state.device_status = DeviceStatus.from_int(resp_model.powerSwitch)
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.mode = self._reverse_mist_modes.get(resp_model.workMode)
        self.state.humidity = resp_model.humidity
        self.state.auto_target_humidity = resp_model.targetHumidity
        self.state.mist_level = resp_model.mistLevel
        self.state.mist_virtual_level = resp_model.virtualLevel
        self.state.water_lacks = bool(resp_model.waterLacksState)
        self.state.water_tank_lifted = bool(resp_model.waterTankLifted)
        self.state.automatic_stop_config = bool(resp_model.autoStopSwitch)
        self.state.auto_stop_target_reached = bool(resp_model.autoStopState)
        self.state.display_set_status = DeviceStatus.from_int(resp_model.screenSwitch)
        self.state.display_status = DeviceStatus.from_int(resp_model.screenState)
        if resp_model.nightLight is not None:
            self.state.nightlight_brightness = resp_model.nightLight.brightness
            self.state.nightlight_status = DeviceStatus.from_int(
                resp_model.nightLight.nightLightSwitch
            )

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv2_api('getHumidifierStatus')
        r_model = process_bypassv2_result(
            self, logger, 'get_details', r_dict, models.Levoit1000SResult
        )
        if r_model is None:
            return

        self._set_state(r_model)

    @deprecated('Use toggle_display() instead.')
    async def set_display(self, toggle: bool) -> bool:
        """Toggle display on/off.

        This is a deprecated method, please use toggle_display() instead.
        """
        return await self.toggle_switch(toggle)

    async def toggle_display(self, toggle: bool) -> bool:
        payload_data = {'screenSwitch': int(toggle)}
        body = self._build_request('setDisplay', payload_data)
        headers = Helpers.req_header_bypass()

        r_dict, _ = await self.manager.async_call_api(
            '/cloud/v2/deviceManaged/bypassV2',
            method='post',
            headers=headers,
            json_object=body.to_dict(),
        )
        r = Helpers.process_dev_response(logger, 'set_display', self, r_dict)
        if r is None:
            return False
        self.state.display_set_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mode(self, mode: str) -> bool:
        if mode not in self.mist_modes:
            logger.warning('Invalid humidity mode used - %s', mode)
            logger.info(
                'Proper modes for this device are - %s',
                orjson.dumps(
                    self.mist_modes, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
                ),
            )
            return False

        payload_data = {'workMode': self.mist_modes[mode]}
        r_dict = await self.call_bypassv2_api('setHumidityMode', payload_data)
        r = Helpers.process_dev_response(logger, 'set_mode', self, r_dict)
        if r is None:
            return False

        self.state.mode = mode

        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mist_level(self, level: int) -> bool:
        if level not in self.mist_levels:
            logger.warning('Humidifier mist level out of range')
            return False

        payload_data = {'levelIdx': 0, 'virtualLevel': level, 'levelType': 'mist'}
        r_dict = await self.call_bypassv2_api('virtualLevel', payload_data)
        r = Helpers.process_dev_response(logger, 'set_mist_level', self, r_dict)
        if r is None:
            return False

        self.state.mist_level = level
        self.state.mist_virtual_level = level
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON

        payload_data = {'powerSwitch': int(toggle), 'switchIdx': 0}
        r_dict = await self.call_bypassv2_api('setSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_switch', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_humidity(self, humidity: int) -> bool:
        if not Validators.validate_range(humidity, *self.target_minmax):
            logger.warning(
                'Humidity value must be set between %s and %s',
                self.target_minmax[0],
                self.target_minmax[1],
            )
            return False

        payload_data = {'targetHumidity': humidity}
        r_dict = await self.call_bypassv2_api('setTargetHumidity', payload_data)
        r = Helpers.process_dev_response(logger, 'set_humidity', self, r_dict)
        if r is None:
            return False

        self.state.auto_target_humidity = humidity
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_automatic_stop(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.automatic_stop_config is not True

        payload_data = {'autoStopSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setAutoStopSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'set_automatic_stop', self, r_dict)

        if r is None:
            return False
        self.state.automatic_stop_config = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_nightlight(self, toggle: bool | None = None) -> bool:
        if not self.supports_nightlight:
            logger.warning(
                '%s is a %s does not have a nightlight or it is not supported.',
                self.device_name,
                self.device_type,
            )
            return False

        if toggle is None:
            toggle = self.state.nightlight_status != DeviceStatus.ON

        payload_data = {'nightLightSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setNightLightStatus', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_nightlight', self, r_dict)
        if r is None:
            return False

        self.state.nightlight_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_nightlight_brightness(self, brightness: int) -> bool:
        if not self.supports_nightlight:
            logger.warning(
                '%s is a %s does not have a nightlight or it is not supported.',
                self.device_name,
                self.device_type,
            )
            return False

        if not Validators.validate_zero_to_hundred(brightness):
            logger.warning('Brightness value must be set between 0 and 100')
            return False

        payload_data = {
            'brightness': brightness,
            'nightLightSwitch': 1 if brightness > 0 else 0,
        }
        r_dict = await self.call_bypassv2_api('setLightStatus', payload_data)
        r = Helpers.process_dev_response(
            logger, 'set_night_light_brightness', self, r_dict
        )
        if r is None:
            return False

        self.state.nightlight_brightness = brightness
        self.state.nightlight_status = (
            DeviceStatus.ON if brightness > 0 else DeviceStatus.OFF
        )
        self.state.connection_status = ConnectionStatus.ONLINE
        return True


class VeSyncSproutHumid(BypassV2Mixin, VeSyncHumidifier):
    """VeSync Sprout Humidifier class.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The manager object for API calls.
        feature_map (HumidifierMap): The feature map for the device.

    Attributes:
        state (HumidifierState): The state of the humidifier.
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
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
    """

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: HumidifierMap,
    ) -> None:
        """Initialize Sprout Humidifier class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, resp_model: models.SproutHumidifierResult) -> None:
        """Set state from Sprout Humidifier API result model."""
        self.state.device_status = DeviceStatus.from_int(resp_model.powerSwitch)
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.humidity = resp_model.humidity
        self.state.auto_target_humidity = resp_model.targetHumidity
        self.state.mist_virtual_level = resp_model.virtualLevel
        self.state.mist_level = resp_model.mistLevel
        self.state.mode = self._reverse_mist_modes.get(resp_model.workMode)
        self.state.water_lacks = bool(resp_model.waterLacksState)
        self.state.water_tank_lifted = bool(resp_model.waterTankLifted)
        self.state.automatic_stop_config = bool(resp_model.autoStopSwitch)
        self.state.auto_stop_target_reached = bool(resp_model.autoStopState)
        self.state.display_set_status = DeviceStatus.from_int(resp_model.screenSwitch)
        self.state.display_status = DeviceStatus.from_int(resp_model.screenState)
        self.state.auto_preference = resp_model.autoPreference
        self.state.water_lacks_drying_switch = DeviceStatus.from_int(
            resp_model.waterShortageDryingSwitch
        )
        self.state.child_lock = bool(resp_model.childLockSwitch)
        self.state.filter_life = resp_model.filterLifePercent
        self.state.hepa_filter_life = resp_model.hepaFilterLifePercent
        self.state.temperature = (
            resp_model.temperature / 10
        )  # Response needs to be divided by 10
        if resp_model.breathingLamp is not None:
            self.state.breathing_lamp = BreathingLampState.from_model(
                resp_model.breathingLamp
            )
        if resp_model.nightLight is not None:
            self.state.nightlight_brightness = resp_model.nightLight.brightness
            self.state.nightlight_status = DeviceStatus.from_int(
                resp_model.nightLight.nightLightSwitch
            )
            self.state.nightlight_color_temp = resp_model.nightLight.colorTemperature
        if resp_model.dryingMode is not None:
            drying_mode = resp_model.dryingMode
            self.state.drying_mode_status = DryingModes.from_int(drying_mode.dryingState)
            self.state.drying_mode_auto_switch = DeviceStatus.from_int(
                drying_mode.autoDryingSwitch
            )
            self.state.drying_mode_time_remain = drying_mode.dryingRemain
            self.state.drying_mode_level = drying_mode.dryingLevel

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv2_api('getHumidifierStatus')
        r_model = process_bypassv2_result(
            self, logger, 'get_details', r_dict, models.SproutHumidifierResult
        )
        if r_model is None:
            return
        self._set_state(r_model)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON

        payload_data = {'powerSwitch': int(toggle), 'switchIdx': 0}
        r_dict = await self.call_bypassv2_api('setSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_switch', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mode(self, mode: str) -> bool:
        if mode not in self.mist_modes:
            logger.warning('Invalid humidity mode used - %s', mode)
            logger.info(
                'Proper modes for this device are - %s',
                orjson.dumps(
                    self.mist_modes, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
                ),
            )
            return False
        payload_data = {'workMode': self.mist_modes[mode]}
        r_dict = await self.call_bypassv2_api('setHumidityMode', payload_data)
        r = Helpers.process_dev_response(logger, 'set_mode', self, r_dict)
        if r is None:
            return False
        self.state.mode = mode
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_display(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.display_set_status != DeviceStatus.ON

        payload_data = {'screenSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setDisplay', payload_data)
        r = Helpers.process_dev_response(logger, 'set_display', self, r_dict)
        if r is None:
            return False

        self.state.display_set_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.display_status = DeviceStatus.from_bool(toggle)
        return True

    async def set_mist_level(self, level: int) -> bool:
        if level not in self.mist_levels:
            logger.warning('Humidifier mist level out of range')
            return False

        payload_data = {'levelIdx': 0, 'virtualLevel': level, 'levelType': 'mist'}
        r_dict = await self.call_bypassv2_api('setVirtualLevel', payload_data)
        r = Helpers.process_dev_response(logger, 'set_mist_level', self, r_dict)
        if r is None:
            return False

        self.state.mist_level = level
        self.state.mist_virtual_level = level
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_humidity(self, humidity: int) -> bool:
        if not Validators.validate_range(humidity, *self.target_minmax):
            logger.warning(
                'Humidity value must be set between %s and %s',
                self.target_minmax[0],
                self.target_minmax[1],
            )
            return False

        payload_data = {'targetHumidity': humidity}
        r_dict = await self.call_bypassv2_api('setTargetHumidity', payload_data)
        r = Helpers.process_dev_response(logger, 'set_humidity', self, r_dict)
        if r is None:
            return False

        self.state.auto_target_humidity = humidity
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_drying_mode(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.drying_mode_status != DeviceStatus.ON

        payload_data = {'autoDryingSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setDryingMode', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_drying_mode', self, r_dict)
        if r is None:
            return False

        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.drying_mode_auto_switch = DeviceStatus.from_bool(toggle)
        return True

    async def toggle_child_lock(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.child_lock is True

        payload_data = {'childLockSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setChildLock', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_child_lock', self, r_dict)
        if r is None:
            return False

        self.state.child_lock = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def _set_nightlight_state(
        self,
        toggle: bool,
        brightness: int | None = None,
        color_temp: int | None = None,
    ) -> bool:
        if brightness is not None and not Validators.validate_zero_to_hundred(brightness):
            logger.warning('Brightness value must be set between 0 and 100')
            return False

        if color_temp is not None and not Validators.validate_range(
            color_temp, 2000, 3500
        ):
            logger.warning('Color temperature must be set between 2000K and 3500K')
            return False

        if self.state.nightlight_color_temp is None:
            self.state.nightlight_color_temp = 3500  # Default color temp if not set

        sent_brightness = brightness or self.state.nightlight_brightness or 100
        payload_data = {
            'brightness': sent_brightness,
            'colorTemperature': color_temp or self.state.nightlight_color_temp,
            'nightLightSwitch': int(toggle),
        }
        r_dict = await self.call_bypassv2_api('setLightStatus', payload_data)
        r = Helpers.process_dev_response(logger, 'set_night_light_state', self, r_dict)
        if r is None:
            return False

        self.state.nightlight_brightness = sent_brightness
        self.state.nightlight_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_nightlight_brightness(self, brightness: int) -> bool:
        if not self.supports_nightlight_brightness:
            logger.warning(
                '%s is a %s does not have a nightlight or it is not supported.',
                self.device_name,
                self.device_type,
            )
            return False

        if not Validators.validate_zero_to_hundred(brightness):
            logger.warning('Brightness value must be set between 0 and 100')
            return False

        toggle = brightness > 0
        return await self._set_nightlight_state(toggle, brightness=brightness)

    async def toggle_nightlight(self, toggle: bool | None = None) -> bool:
        if not self.supports_nightlight:
            logger.warning(
                '%s is a %s does not have a nightlight or it is not supported.',
                self.device_name,
                self.device_type,
            )
            return False

        if toggle is None:
            toggle = self.state.nightlight_status != DeviceStatus.ON
        return await self._set_nightlight_state(toggle)

    async def toggle_automatic_stop(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.automatic_stop_config is not True

        payload_data = {'autoStopSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setAutoStopSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_automatic_stop', self, r_dict)
        if r is None:
            return False

        self.state.automatic_stop_config = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True


class VeSyncLV600S(BypassV2Mixin, VeSyncHumidifier):
    """LV600S (LUH-A603S) Humidifier with warm mist support.

    This class handles the newer LV600S models that use the new API format
    with powerSwitch, workMode, etc. and include warm mist functionality.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The manager object for API calls.
        feature_map (HumidifierMap): The feature map for the device.

    Attributes:
        state (HumidifierState): The state of the humidifier.
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
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        mist_levels (list): List of mist levels.
        mist_modes (list): List of mist modes.
        target_minmax (tuple): Tuple of target min and max values.
        warm_mist_levels (list): List of warm mist levels.
    """

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: HumidifierMap,
    ) -> None:
        """Initialize LV600S Humidifier class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, resp_model: models.LV600SResult) -> None:
        """Set state from LV600S API result model."""
        self.state.device_status = DeviceStatus.from_int(resp_model.powerSwitch)
        self.state.connection_status = ConnectionStatus.ONLINE
        self.state.mode = self._reverse_mist_modes.get(resp_model.workMode)
        if self.state.mode is None:
            logger.warning('Unknown mist mode received: %s', resp_model.workMode)

        self.state.auto_target_humidity = resp_model.targetHumidity
        self.state.humidity = resp_model.humidity
        self.state.mist_level = resp_model.mistLevel
        self.state.mist_virtual_level = resp_model.virtualLevel
        self.state.water_lacks = bool(resp_model.waterLacksState)
        self.state.water_tank_lifted = bool(resp_model.waterTankLifted)
        self.state.automatic_stop_config = bool(resp_model.autoStopSwitch)
        self.state.auto_stop_target_reached = bool(resp_model.autoStopState)
        self.state.display_set_status = DeviceStatus.from_int(resp_model.screenSwitch)
        self.state.display_status = DeviceStatus.from_int(resp_model.screenState)
        # Warm mist support
        self.state.warm_mist_enabled = resp_model.warmPower
        self.state.warm_mist_level = resp_model.warmLevel

        if resp_model.timerRemain > 0:
            self.state.timer = Timer(
                resp_model.timerRemain,
                DeviceStatus.from_bool(self.state.device_status != DeviceStatus.ON),
            )

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv2_api('getHumidifierStatus')
        r_model = process_bypassv2_result(
            self, logger, 'get_details', r_dict, models.LV600SResult
        )
        if r_model is None:
            return

        self._set_state(r_model)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON

        payload_data = {'powerSwitch': int(toggle), 'switchIdx': 0}
        r_dict = await self.call_bypassv2_api('setSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_switch', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_humidity(self, humidity: int) -> bool:
        if not Validators.validate_range(humidity, *self.target_minmax):
            logger.warning(
                'Humidity value must be set between %s and %s',
                self.target_minmax[0],
                self.target_minmax[1],
            )
            return False

        payload_data = {'targetHumidity': humidity}
        r_dict = await self.call_bypassv2_api('setTargetHumidity', payload_data)
        r = Helpers.process_dev_response(logger, 'set_humidity', self, r_dict)
        if r is None:
            return False

        self.state.auto_target_humidity = humidity
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mode(self, mode: str) -> bool:
        if mode not in self.mist_modes:
            logger.warning('Invalid humidity mode used - %s', mode)
            logger.info(
                'Proper modes for this device are - %s',
                orjson.dumps(
                    self.mist_modes, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
                ),
            )
            return False

        payload_data = {'workMode': self.mist_modes[mode]}
        r_dict = await self.call_bypassv2_api('setHumidityMode', payload_data)

        r = Helpers.process_dev_response(logger, 'set_mode', self, r_dict)
        if r is None:
            return False

        self.state.mode = mode
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mist_level(self, level: int) -> bool:
        if level not in self.mist_levels:
            logger.warning('Humidifier mist level must be between 1 and 9')
            return False

        payload_data = {'levelIdx': 0, 'virtualLevel': level, 'levelType': 'mist'}
        r_dict = await self.call_bypassv2_api('setVirtualLevel', payload_data)
        r = Helpers.process_dev_response(logger, 'set_mist_level', self, r_dict)
        if r is None:
            return False

        self.state.mist_level = level
        self.state.mist_virtual_level = level
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_warm_level(self, warm_level: int) -> bool:
        """Set warm mist level (0 = off, 1-3 = warm levels)."""
        if not self.supports_warm_mist:
            logger.debug(
                '%s is a %s does not have a mist warmer',
                self.device_name,
                self.device_type,
            )
            return False

        if warm_level not in self.warm_mist_levels:
            logger.warning('Warm mist level must be one of %s', self.warm_mist_levels)
            return False

        payload_data = {
            'levelIdx': 0,
            'levelType': 'warm',
            'mistLevel': 0,
            'warmLevel': warm_level,
        }
        r_dict = await self.call_bypassv2_api('setLevel', payload_data)
        r = Helpers.process_dev_response(logger, 'set_warm_level', self, r_dict)
        if r is None:
            return False

        self.state.warm_mist_level = warm_level
        self.state.warm_mist_enabled = warm_level > 0
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_display(self, toggle: bool | None = None) -> bool:
        """Toggle display on/off."""
        if toggle is None:
            toggle = self.state.display_set_status != DeviceStatus.ON

        payload_data = {'screenSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setDisplay', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_display', self, r_dict)
        if r is None:
            return False

        self.state.display_set_status = DeviceStatus.from_bool(toggle)
        self.state.display_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def get_timer(self) -> Timer | None:
        """Get timer for humidifier using V2 API."""
        r_dict = await self.call_bypassv2_api('getTimerV2', {})
        result_model = process_bypassv2_result(
            self, logger, 'get_timer', r_dict, ResultV2GetTimerV2
        )
        if result_model is None:
            return None
        if not result_model.timers:
            logger.debug('No timers found')
            return None
        timer = result_model.timers[0]
        action = DeviceStatus.OFF
        if timer.startAct:
            action = DeviceStatus.ON if timer.startAct[0].act == 1 else DeviceStatus.OFF
        self.state.timer = Timer(
            timer_duration=timer.total,
            action=action,
            id=timer.id,
            remaining=timer.remain,
        )
        return self.state.timer

    async def clear_timer(self) -> bool:
        """Clear timer for humidifier using V2 API."""
        timer_id = self.state.timer.id if self.state.timer else 1
        payload = {'id': timer_id}
        r_dict = await self.call_bypassv2_api('delTimerV2', payload)
        r = Helpers.process_dev_response(logger, 'clear_timer', self, r_dict)
        if r is None:
            return False
        self.state.timer = None
        return True

    async def set_timer(self, duration: int, action: str | None = None) -> bool:
        """Set timer for humidifier using V2 API.

        Args:
            duration: Timer duration in seconds.
            action: Action when timer expires. Defaults to toggle current state.
        """
        if action is None:
            action = (
                DeviceStatus.OFF
                if self.state.device_status == DeviceStatus.ON
                else DeviceStatus.ON
            )
        act_val = 1 if action == DeviceStatus.ON else 0

        payload_data = {
            'startAct': [{'type': 'powerSwitch', 'num': 0, 'act': act_val}],
            'total': duration,
        }
        r_dict = await self.call_bypassv2_api('addTimerV2', payload_data)
        result_model = process_bypassv2_result(
            self, logger, 'set_timer', r_dict, ResultV2SetTimer
        )
        if result_model is None:
            return False

        self.state.timer = Timer(
            timer_duration=duration,
            action=action,
            id=result_model.id,
            remaining=duration,
        )
        return True


class NeoClassic650s(BypassV2Mixin, VeSyncHumidifier):
    """NeoClassic 650s Humidifier.

    Args:
        details (ResponseDeviceDetailsModel): The device details.
        manager (VeSync): The manager object for API calls.
        feature_map (HumidifierMap): The feature map for the device.

    Attributes:
        state (HumidifierState): The state of the humidifier.
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
        pid (str): Product ID of device, pulled by some devices on update.
        sub_device_no (int): Sub-device number of device.
        product_type (str): Product type of device.
        features (dict): Features of device.
        mist_levels (list): List of mist levels.
        mist_modes (list): List of mist modes.
        target_minmax (tuple): Tuple of target min and max values.
        warm_mist_levels (list): List of warm mist levels.
    """

    __slots__ = ()

    def __init__(
        self,
        details: ResponseDeviceDetailsModel,
        manager: VeSync,
        feature_map: HumidifierMap,
    ) -> None:
        """Initialize NeoClassic 650s Humidifier class."""
        super().__init__(details, manager, feature_map)

    def _set_state(self, resp_model: models.NeoClassic650sResult) -> None:
        """Set state from NeoClassic 650s API result model."""
        # ** errorCode
        # ** errorCodes
        # ** lampSwitch
        # ** scheduleCount
        # ** timerRemain
        # ** totalWorkTime
        # ** powerSwitch
        self.state.device_status = DeviceStatus.from_int(resp_model.powerSwitch)
        self.state.connection_status = ConnectionStatus.ONLINE
        # ** workMode
        self.state.mode = self._reverse_mist_modes.get(resp_model.workMode)
        if self.state.mode is None:
            logger.warning('Unknown mist mode received: %s', resp_model.workMode)

        # ** targetHumidity
        self.state.auto_target_humidity = resp_model.targetHumidity
        # ** humidity
        self.state.humidity = resp_model.humidity
        # ** mistLevel
        self.state.mist_level = resp_model.mistLevel
        # ** virtualLevel
        self.state.mist_virtual_level = resp_model.virtualLevel
        # ** waterLacksState
        self.state.water_lacks = bool(resp_model.waterLacksState)
        # ** waterTankLifted
        self.state.water_tank_lifted = bool(resp_model.waterTankLifted)

        # ** autoStopState
        # ** autoStopSwitch
        self.state.automatic_stop_config = bool(resp_model.autoStopSwitch)
        self.state.auto_stop_target_reached = bool(resp_model.autoStopState)

        # ** screenSwitch
        self.state.display_set_status = DeviceStatus.from_int(resp_model.screenSwitch)
        # ** screenState
        self.state.display_status = DeviceStatus.from_int(resp_model.screenState)

        # ** autoPreference
        self.state.auto_preference = resp_model.autoPreference

        # ** nightLight
        if resp_model.nightLight is not None:
            self.state.nightlight_brightness = resp_model.nightLight.brightness
            self.state.nightlight_status = DeviceStatus.from_int(
                resp_model.nightLight.nightLightSwitch
            )
            self.state.nightlight_color_temp = resp_model.nightLight.colorTemperature
        # ** temperature
        self.state.temperature = (
            resp_model.temperature / 10
        )  # Fahrenheit but without decimals

    async def get_details(self) -> None:
        r_dict = await self.call_bypassv2_api('getHumidifierStatus')
        r_model = process_bypassv2_result(
            self, logger, 'get_details', r_dict, models.NeoClassic650sResult
        )
        if r_model is None:
            return

        self._set_state(r_model)

    async def toggle_switch(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.device_status != DeviceStatus.ON

        payload_data = {'powerSwitch': int(toggle), 'switchIdx': 0}
        r_dict = await self.call_bypassv2_api('setSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_switch', self, r_dict)
        if r is None:
            return False

        self.state.device_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_automatic_stop(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.automatic_stop_config is not True

        payload_data = {'autoStopSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setAutoStopSwitch', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_automatic_stop', self, r_dict)
        if r is None:
            return False

        self.state.automatic_stop_config = toggle
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_display(self, toggle: bool | None = None) -> bool:
        if toggle is None:
            toggle = self.state.display_set_status != DeviceStatus.ON

        payload_data = {'screenSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setDisplay', payload_data)
        r = Helpers.process_dev_response(logger, 'set_display', self, r_dict)
        if r is None:
            return False

        self.state.display_set_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_humidity(self, humidity: int) -> bool:
        if not Validators.validate_range(humidity, *self.target_minmax):
            logger.warning(
                'Invalid humidity, must be between %s and %s', *self.target_minmax
            )
            return False

        payload_data = {'targetHumidity': humidity}
        r_dict = await self.call_bypassv2_api('setTargetHumidity', payload_data)
        r = Helpers.process_dev_response(logger, 'set_humidity', self, r_dict)
        if r is None:
            return False

        self.state.auto_target_humidity = humidity
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mode(self, mode: str) -> bool:
        if mode not in self.mist_modes:
            logger.warning('Invalid humidity mode used - %s', mode)
            logger.info(
                'Proper modes for this device are - %s',
                orjson.dumps(
                    self.mist_modes,
                    option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS,
                ),
            )
            return False

        payload_data = {'workMode': self.mist_modes[mode]}
        r_dict = await self.call_bypassv2_api('setHumidityMode', payload_data)

        r = Helpers.process_dev_response(logger, 'set_humidity_mode', self, r_dict)
        if r is None:
            return False

        self.state.mode = mode
        self.state.device_status = DeviceStatus.ON
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_mist_level(self, level: int) -> bool:
        if level not in self.mist_levels:
            logger.warning(
                'Humidifier mist level, must be between %s and %s', *self.mist_levels
            )
            return False

        payload_data = {'levelIdx': 0, 'virtualLevel': level, 'levelType': 'mist'}
        r_dict = await self.call_bypassv2_api('setVirtualLevel', payload_data)
        r = Helpers.process_dev_response(logger, 'set_mist_level', self, r_dict)
        if r is None:
            return False

        self.state.mist_level = level
        self.state.mist_virtual_level = level
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def toggle_nightlight(self, toggle: bool | None = None) -> bool:
        if not self.supports_nightlight:
            logger.warning(
                '%s is a %s does not have a nightlight or it is not supported.',
                self.device_name,
                self.device_type,
            )
            return False

        if toggle is None:
            toggle = self.state.nightlight_status != DeviceStatus.ON

        payload_data = {'nightLightSwitch': int(toggle)}
        r_dict = await self.call_bypassv2_api('setNightLightStatus', payload_data)
        r = Helpers.process_dev_response(logger, 'toggle_nightlight', self, r_dict)
        if r is None:
            return False

        self.state.nightlight_status = DeviceStatus.from_bool(toggle)
        self.state.connection_status = ConnectionStatus.ONLINE
        return True

    async def set_nightlight_brightness(self, brightness: int) -> bool:
        if not self.supports_nightlight:
            logger.warning(
                '%s is a %s does not have a nightlight or it is not supported.',
                self.device_name,
                self.device_type,
            )
            return False

        if not Validators.validate_zero_to_hundred(brightness):
            logger.warning('Brightness value must be set between 0 and 100')
            return False

        payload_data = {
            'brightness': brightness,
            'nightLightSwitch': 1 if brightness > 0 else 0,
        }
        r_dict = await self.call_bypassv2_api('setLightStatus', payload_data)
        r = Helpers.process_dev_response(
            logger, 'set_night_light_brightness', self, r_dict
        )
        if r is None:
            return False

        self.state.nightlight_brightness = brightness
        self.state.nightlight_status = (
            DeviceStatus.ON if brightness > 0 else DeviceStatus.OFF
        )
        self.state.connection_status = ConnectionStatus.ONLINE
        return True
