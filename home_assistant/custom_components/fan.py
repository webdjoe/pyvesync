"""Support for Etekcity VeSync fans"""
import logging
from homeassistant.components.fan import (FanEntity, SUPPORT_SET_SPEED)

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

FAN_SPEEDS = ["auto", "low", "medium", "high"]


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the VeSync fan platform."""

    if discovery_info is None:
        return

    fans = []

    manager = hass.data[DOMAIN]['manager']

    if manager.fans is not None and manager.fans:
        if len(manager.fans) == 1:
            count_string = "fan"
        else:
            count_string = "fans"

        for fan in manager.fans:
            fans.append(VeSyncFanHA(fan))
            _LOGGER.info("Added a VeSync fan named '%s'",
                         fan.device_name)
    else:
        _LOGGER.info("No VeSync fans found")

    add_entities(fans)


class VeSyncFanHA(FanEntity):
    """Representation of a VeSync fan."""

    def __init__(self, fan):
        """Initialize the VeSync fan device."""
        self.smartfan = fan

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    @property
    def is_on(self):
        """Return True if device is on"""
        return self.smartfan.device_status == "on"

    @property
    def speed(self):
        """Return the current speed."""
        if self.smartfan.mode == "auto":
            return "auto"
        if self.smartfan.mode == "manual":
            current_level = self.smartfan.fan_level
            if current_level is not None:
                return FAN_SPEEDS[current_level]
        return None

    @property
    def speed_list(self):
        """Get the list of available speeds"""
        return FAN_SPEEDS

    @property
    def unique_info(self):
        """Return the ID of this fan."""
        return self.smartfan.uuid

    @property
    def name(self):
        """Return the name of the fan."""
        return self.smartfan.device_name

    @property
    def device_state_attributes(self):
        """Return the state attributes of the fan."""
        attr = {}
        attr['mode'] = self.smartfan.mode
        attr['active_time'] = self.smartfan.active_time
        attr['filter_life'] = self.smartfan.filter_life
        attr['air_quality'] = self.smartfan.air_quality
        attr['screen_status'] = self.smartfan.screen_status
        return attr

    def set_speed(self, speed):
        if speed is None or speed == "auto":
            self.smartfan.auto_mode()
        else:
            self.smartfan.manual_mode()
            self.smartfan.change_fan_speed(FAN_SPEEDS.index(speed))

    def turn_on(self, speed, **kwargs):
        self.smartfan.turn_on()
        if speed is None or speed == "auto":
            self.smartfan.auto_mode()
        else:
            self.smartfan.manual_mode()
            self.smartfan.change_fan_speed(FAN_SPEEDS.index(speed))

    def turn_off(self, **kwargs):
        self.smartfan.turn_off()

    def update(self):
        self.smartfan.update()
