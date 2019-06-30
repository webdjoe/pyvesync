"""Etekcity VeSync integration."""
import logging
import voluptuous as vol
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_TIME_ZONE)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery


_LOGGER = logging.getLogger(__name__)

DOMAIN = 'vesync'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_TIME_ZONE): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up the VeSync component."""
    from pyvesync.vesync import VeSync

    conf = config[DOMAIN]

    manager = VeSync(conf.get(CONF_USERNAME), conf.get(CONF_PASSWORD),
                     time_zone=conf.get(CONF_TIME_ZONE))

    if not manager.login():
        _LOGGER.error("Unable to login to VeSync")
        return

    manager.update()

    hass.data[DOMAIN] = {
        'manager': manager
    }

    discovery.load_platform(hass, 'switch', DOMAIN, {}, config)
    discovery.load_platform(hass, 'fan', DOMAIN, {}, config)

    return True
