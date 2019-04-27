from .vesync import VeSync
from .vesyncoutlet import VeSyncOutlet10A, VeSyncOutlet15A, VeSyncOutlet7A
from .vesyncswitch import VeSyncWallSwitch
from .vesyncfan import VeSyncAir131

import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)5s - %(message)s'
)
