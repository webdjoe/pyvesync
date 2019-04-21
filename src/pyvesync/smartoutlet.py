from abc import ABCMeta, abstractmethod, abstractproperty, ABC
import hashlib
import logging
import time
import requests
import re
from typing import Any

from .vesyncdevice import VeSyncDevice


class VeSyncOutlet(VeSyncDevice):
    __metaclass__ = ABCMeta

    def __init__(self, details, manager):
        super().__init__(details, manager)
    
    def api_builder(self, )