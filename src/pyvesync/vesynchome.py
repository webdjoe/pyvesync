"""This is a WIP, not implemented yet."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import fields
from typing import TYPE_CHECKING

from pyvesync.models.base_models import DefaultValues
from pyvesync.models.home_models import (
    IntResponseHomeListModel,
    IntResponseHomeResultModel,
    RequestHomeModel,
    ResponseHomeModel,
)
from pyvesync.utils.errors import ErrorCodes, VeSyncAPIResponseError
from pyvesync.utils.helpers import Helpers

if TYPE_CHECKING:
    from pyvesync.base_devices import VeSyncBaseDevice
    from pyvesync.models.base_models import RequestBaseModel
    from pyvesync.vesync import VeSync


_LOGGER = logging.getLogger(__name__)


class VeSyncHome:
    """Class to handle home-related operations in VeSync."""

    def __init__(self, home_id: int, name: str, nickname: str | None = None) -> None:
        """Initialize the VeSyncHome instance."""
        self.home_id: int = home_id
        self.name: str = name
        self.nickname: str | None = nickname
        self.rooms: list[VeSyncRoom] = []

    @property
    def devices(self) -> list[VeSyncBaseDevice]:
        """Return a list of all devices in the home."""
        devices = []
        for room in self.rooms:
            devices.extend(room.devices)
        return devices

    async def update_devices(self, devices: list[VeSyncBaseDevice]) -> None:
        """Update the devices in the home."""
        update_tasks = [device.update() for device in devices]
        for update_coro in asyncio.as_completed(update_tasks):
            try:
                await update_coro
            except Exception as e:  # pylint: disable=broad-except
                _LOGGER.debug('Error updating device %s', e)

    @staticmethod
    def _build_request_model(
        manager: VeSync, request_model: type[RequestBaseModel]
    ) -> RequestBaseModel:
        """Build the request model for home data."""
        req_fields = [field.name for field in fields(request_model) if field.init]
        body = Helpers.get_class_attributes(DefaultValues, req_fields)
        body.update(Helpers.get_class_attributes(manager, req_fields))
        return request_model(**body)

    @classmethod
    def _process_home_list(
        cls, home_list: list[IntResponseHomeListModel]
    ) -> list[VeSyncHome]:
        """Process the home list and return a list of VeSyncHome instances."""
        homes = []
        for home in home_list:
            if not isinstance(home, IntResponseHomeListModel):
                msg = (
                    'Invalid home list item type.'
                    f'Expected IntResponseHomeListModel, got {home}'
                )
                raise VeSyncAPIResponseError(msg)
            homes.append(VeSyncHome(home.homeId, home.homeName, home.nickname))
        return homes

    @classmethod
    async def build_homes(cls, manager: VeSync) -> bool:
        """Get home information.

        This method retrieves the home list from the VeSync API and populates
        the VeSyncHome instances in the manager. The objects are stored in
        `manager.homes` attribute as a list.

        Args:
            manager (VeSync): The VeSync instance to use for the API call.

        Returns:
            bool: True if the home list was successfully retrieved and populated.

        Raises:
            VeSyncAPIResponseError: If the API response contains an error or
                if the home list is empty.
        """
        body = cls._build_request_model(manager, RequestHomeModel)
        response, _ = await manager.async_call_api(
            '/cloud/v1/homeManaged/getHomeList', method='post', json_object=body
        )
        if response is None:
            raise VeSyncAPIResponseError(
                'Response is None, enable debugging to see more information.'
            )

        resp_model = ResponseHomeModel.from_dict(response)
        if resp_model.code != 0:
            error = ErrorCodes.get_error_info(resp_model.code)
            if resp_model.msg is not None:
                error.message = f'{resp_model.msg} ({error.message})'

            msg = f'Failed to get home list with error: {error.to_json()}'
            raise VeSyncAPIResponseError(msg)
        result = resp_model.result
        if not isinstance(result, IntResponseHomeResultModel):
            msg = (
                'Error in home list API response.'
                f'Expected IntResponseHomeResultModel, got {result}'
            )
            raise VeSyncAPIResponseError(msg)
        home_list = result.homeList
        if not home_list:
            raise VeSyncAPIResponseError('No homes found in the response.')
        for home in home_list:
            if not isinstance(home, IntResponseHomeListModel):
                msg = (
                    'Invalid home list item type.'
                    f'Expected IntResponseHomeListModel, got {home}'
                )
                raise VeSyncAPIResponseError(msg)
        return True


class VeSyncRoom:
    """Class to handle room-related operations in VeSync."""

    def __init__(self, room_id: str, name: str) -> None:
        """Initialize the VeSyncRoom instance."""
        self.room_id: str = room_id
        self.name: str = name
        self.devices: list[VeSyncBaseDevice] = []

    @staticmethod
    def _build_request_model(
        manager: VeSync, request_model: type[RequestBaseModel]
    ) -> RequestBaseModel:
        """Build the request model for room data."""
        req_fields = [field.name for field in fields(request_model) if field.init]
        body = Helpers.get_class_attributes(DefaultValues, req_fields)
        body.update(Helpers.get_class_attributes(manager, req_fields))
        return request_model(**body)
