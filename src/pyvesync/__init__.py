"""VeSync API Library."""

# pylint: skip-file
# flake8: noqa
from .vesync import VeSync
from .vesyncoutlet import (VeSyncOutlet10A, VeSyncOutlet15A, VeSyncOutlet7A,
                           VeSyncOutdoorPlug)
from .vesyncswitch import VeSyncWallSwitch
from .vesyncfan import VeSyncAir131
from .vesyncbulb import VeSyncBulbESL100
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)5s - %(message)s'
)
