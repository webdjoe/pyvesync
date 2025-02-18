#!/usr/bin/env python3
"""library_logger.py.

This module provides enumerations.

"""
from enum import Enum
from logging import getLogger

_LOGGER = getLogger(__name__)


class EDeviceFamily(str, Enum):
    """Enumeration of supported VeSync devices families."""

    BULB = 'bulb'
    FAN = 'fan'
    KITCHEN = 'kitchen'
    OUTLET = 'outlet'
    SWITCH = 'switch'
    NOT_SUPPORTED = 'not supported'


class EConfig(str, Enum):
    """Enumeration of supported devices configuration keys."""

    CLASS = 'module'
    COLOR_MODEL = 'color_model'
    FEATURES = 'features'
    LEVELS = 'levels'
    MIST_LEVELS = 'mist_levels'
    MIST_MODES = 'mist_modes'
    MIST_LEVELS_WARM = 'warm_mist_levels'
    MODELS = 'models'
    MODES = 'modes'


class ColorMode(str, Enum):
    """Enumeration of known color modes."""

    NONE = ''
    WHITE = 'white'
    COLOR = 'color'
    HSV = 'hsv'
    RGB = 'rgb'

    @classmethod
    def get(cls, name: str):
        """Return the ColorMode for the given name."""
        try:
            return cls[name]
        except Exception:
            _LOGGER.error("No ColorMode for - %s", name)
            return ColorMode.NONE
