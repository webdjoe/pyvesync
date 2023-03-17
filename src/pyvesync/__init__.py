"""VeSync API Library."""

# pylint: skip-file
# flake8: noqa
from .vesync import VeSync
import logging


logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)5s - %(message)s'
)
