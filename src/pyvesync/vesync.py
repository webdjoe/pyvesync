"""VeSync API Device Libary."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import MISSING, fields
from pathlib import Path
from typing import TYPE_CHECKING, Self

from aiohttp import ClientResponse, ClientSession
from aiohttp.client_exceptions import ClientResponseError
from mashumaro.mixins.orjson import DataClassORJSONMixin

from pyvesync.auth import VeSyncAuth
from pyvesync.const import (
    DEFAULT_REGION,
    DEFAULT_TZ,
    MAX_API_REAUTH_RETRIES,
    REGION_API_MAP,
    STATUS_OK,
)
from pyvesync.device_container import DeviceContainer
from pyvesync.models.vesync_models import (
    FirmwareDeviceItemModel,
    RequestDeviceListModel,
    RequestFirmwareModel,
    ResponseDeviceListModel,
    ResponseFirmwareModel,
)
from pyvesync.utils.errors import (
    ErrorCodes,
    ErrorTypes,
    VeSyncAPIResponseError,
    VeSyncAPIStatusCodeError,
    VeSyncError,
    VeSyncServerError,
    VeSyncTokenError,
    raise_api_errors,
)
from pyvesync.utils.helpers import Helpers
from pyvesync.utils.logs import LibraryLogger

if TYPE_CHECKING:
    from pyvesync.base_devices import VeSyncBaseDevice

logger = logging.getLogger(__name__)


class VeSync:  # pylint: disable=function-redefined
    """VeSync Manager Class."""

    __slots__ = (
        '__weakref__',
        '_api_attempts',
        '_auth',
        '_close_session',
        '_debug',
        '_device_container',
        '_redact',
        '_verbose',
        'enabled',
        'in_process',
        'language',
        'session',
        'time_zone',
    )

    def __init__(
        self,
        username: str,
        password: str,
        country_code: str = DEFAULT_REGION,
        session: ClientSession | None = None,
        time_zone: str = DEFAULT_TZ,
        redact: bool = True,
    ) -> None:
        """Initialize VeSync Manager.

        This class is used as the manager for all VeSync objects, all methods and
        API calls are performed from this class. Time zone, debug and redact are
        optional. Time zone must be a string of an IANA time zone format. Once
        class is instantiated, call `await manager.login()` to log in to VeSync servers,
        which returns `True` if successful. Once logged in, call
        `await manager.get_devices()` to retrieve devices. Then `await `manager.update()`
        to update all devices or `await manager.devices[0].update()` to
        update a single device.

        Args:
            username (str): VeSync account username (usually email address)
            password (str): VeSync account password
            country_code (str): VeSync account country in ISO 3166 Alpha-2 format.
                By default, the account region is detected automatically at the login step
                If your account country is different from the default `US`,
                a second login attempt may be necessary - in this case
                you should specify the country directly to speed up the login process.
            session (ClientSession): aiohttp client session for
                API calls, by default None
            time_zone (str): Time zone for device from IANA database, by default
                DEFAULT_TZ. This is automatically set to the time zone of the
                VeSync account during login.
            redact (bool): Enable redaction of sensitive information, by default True.

        Attributes:
            session (ClientSession):  Client session for API calls
            devices (DeviceContainer): Container for all VeSync devices,
                has functionality of a mutable set. See
                [`DeviceContainer`][pyvesync.device_container.DeviceContainer] for
                more information
            auth (VeSyncAuth): Authentication manager
            time_zone (str): Time zone for VeSync account pulled from API
            enabled (bool): True if logged in to VeSync, False if not

        Note:
            This class is a context manager, use `async with VeSync() as manager:`
            to manage the session context. The session will be closed when exiting
            if no session is passed in.

            The `manager.devices` attribute is a DeviceContainer object that contains
            all VeSync devices. The `manager.devices` object has the functionality of
            a set, and can be iterated over to access devices. See :obj:`DeviceContainer`
            for more information.

            If using a context manager is not convenient, `manager.__aenter__()` and
            `manager.__aexit__()` can be called directly.

            Either username/password or token/account_id must be provided for
            authentication.

        See Also:
            :obj:`DeviceContainer`
                Container object to store VeSync devices
            :obj:`DeviceState`
                Object to store device state information
        """
        self.session = session
        self._api_attempts = 0
        self._close_session = False
        self.redact = redact
        self._verbose: bool = False
        self.time_zone: str = time_zone
        self.language: str = 'en'
        self.enabled = False
        self.in_process = False
        self._device_container: DeviceContainer = DeviceContainer()

        # Initialize authentication manager
        self._auth = VeSyncAuth(
            manager=self,
            username=username,
            password=password,
            country_code=country_code,
        )

    @property
    def devices(self) -> DeviceContainer:
        """Return VeSync device container.

        See Also:
            The pyvesync.device_container.DeviceContainer object
            for methods and properties.
        """
        return self._device_container

    @property
    def auth(self) -> VeSyncAuth:
        """Return VeSync authentication manager."""
        return self._auth

    @property
    def country_code(self) -> str:
        """Return country code."""
        return self._auth.country_code

    @property
    def current_region(self) -> str:
        """Return current region."""
        return self._auth.current_region

    @property
    def token(self) -> str:
        """Return authentication token.

        Returns:
            str: Authentication token.

        Raises:
            AttributeError: If token is not set.
        """
        return self._auth.token

    @property
    def account_id(self) -> str:
        """Return account ID.

        Returns:
            str: Account ID.

        Raises:
            AttributeError: If account ID is not set.
        """
        return self._auth.account_id

    @property
    def debug(self) -> bool:
        """Return debug flag."""
        return LibraryLogger.debug_enabled

    def check_debug(self) -> bool:
        """Check if debug logging is enabled - should be called minimally."""
        return LibraryLogger.check_debug()

    @property
    def redact(self) -> bool:
        """Return debug flag."""
        return self._redact

    @redact.setter
    def redact(self, new_flag: bool) -> None:
        """Set debug flag."""
        if new_flag:
            LibraryLogger.shouldredact = True
        elif new_flag is False:
            LibraryLogger.shouldredact = False
        self._redact = new_flag

    def output_credentials_json(self) -> str | None:
        """Output current authentication credentials as a JSON string."""
        return self.auth.output_credentials_json()

    def output_credentials_dict(self) -> dict[str, str] | None:
        """Output current authentication credentials as a dictionary."""
        return self.auth.output_credentials_dict()

    async def save_credentials(self, filename: str | Path | None) -> None:
        """Save authentication credentials to a file.

        Args:
            filename (str | Path | None): The name of the file to save credentials to.
                If None, no action is taken.
        """
        if filename is not None:
            await self.auth.save_credentials_to_file(filename)

    async def load_credentials_from_file(
        self, filename: str | Path | None = None
    ) -> bool:
        """Load authentication credentials from a file.

        Args:
            filename (str | Path | None): The name of the file to load credentials from.
                If None, no action is taken.

        Returns:
            bool: True if credentials were loaded successfully, False otherwise.
        """
        return await self.auth.load_credentials_from_file(filename)

    def set_credentials(
        self, token: str, account_id: str, country_code: str, region: str
    ) -> None:
        """Set authentication credentials.

        Args:
            token (str): Authentication token.
            account_id (str): Account ID.
            country_code (str): Country code in ISO 3166 Alpha-2 format.
            region (str): Current region code.
        """
        self._auth.set_credentials(token, account_id, country_code, region)

    def log_to_file(self, filename: str | Path, stdout: bool = True) -> None:
        """Log to file and enable debug logging.

        Args:
            filename (str | Path): The name of the file to log to.
            stdout (bool): Whether to also log to stdout, by default True.
        """
        LibraryLogger.configure_file_logging(filename, level=logging.DEBUG, stdout=stdout)
        logger.debug('Logging to file: %s', filename)

    def process_devices(self, dev_list_resp: ResponseDeviceListModel) -> bool:
        """Instantiate Device Objects.

        Internal method run by `get_devices()` to instantiate device objects.

        """
        current_device_count = len(self._device_container)
        if current_device_count > 0:
            self._device_container.remove_stale_devices(dev_list_resp)
        new_device_count = len(self._device_container)

        if new_device_count != current_device_count:
            logger.debug(
                'Removed %s devices', str(current_device_count - new_device_count)
            )

        current_device_count = new_device_count
        self._device_container.add_new_devices(dev_list_resp, self)
        new_device_count = len(self._device_container)
        if new_device_count != current_device_count:
            logger.debug('Added %s devices', str(new_device_count - current_device_count))
        return True

    async def get_devices(self) -> bool:
        """Return tuple listing outlets, switches, and fans of devices.

        This is also called by `VeSync.update()`

        Raises:
            VeSyncAPIResponseError: If API response is invalid.
            VeSyncServerError: If server returns an error.
        """
        self.in_process = True
        proc_return = False

        if not self.auth.is_authenticated or (
            not self.auth.token or not self.auth.account_id
        ):
            logger.info("Not logged in to VeSync, can't get devices")
            return False

        request_model = RequestDeviceListModel(
            token=self.auth.token, accountID=self.auth.account_id, timeZone=self.time_zone
        )
        logger.debug('Requesting device list from VeSync')
        response_dict, _ = await self.async_call_api(
            '/cloud/v1/deviceManaged/devices',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=request_model.to_dict(),
        )

        if response_dict is None:
            raise VeSyncAPIResponseError(
                'Error receiving response to device list request'
            )

        response = ResponseDeviceListModel.from_dict(response_dict)

        if response.code == 0:
            proc_return = self.process_devices(response)
        else:
            error_info = ErrorCodes.get_error_info(response.code)
            if response.msg is not None:
                error_info.message = f'{error_info.message} ({response.msg})'
            if error_info.error_type == ErrorTypes.SERVER_ERROR:
                raise VeSyncServerError(error_info.message)
            raise VeSyncAPIResponseError(
                'Error receiving response to device list request'
            )

        self.in_process = False

        return proc_return

    async def login(self) -> bool:  # pylint: disable=W9006 # pylint mult docstring raises
        """Log into VeSync server.

        Username and password are provided when class is instantiated.

        Returns:
            True if login successful, False otherwise

        Raises:
            VeSyncLoginError: If login fails, for example due to invalid username
                or password.
            VeSyncAPIResponseError: If API response is invalid.
            VeSyncServerError: If server returns an error.
        """
        self.enabled = False
        success = await self._auth.login()
        if success:
            self.enabled = True
        return success

    async def update(self) -> None:
        """Fetch updated information about devices and new device list.

        Pulls devices list from VeSync and instantiates any new devices. Devices
        are stored in the instance attributes `outlets`, `switches`, `fans`, and
        `bulbs`. The `_device_list` attribute is a dictionary of these attributes.
        """
        if not self.enabled:
            logger.error('Not logged in to VeSync')
            return
        await self.get_devices()

        await self.update_all_devices()

    async def update_all_devices(self) -> None:
        """Run `get_details()` for each device and update state."""
        logger.debug('Start updating the device details one by one')
        if len(self._device_container) == 0:
            logger.error('No devices to update')
            return
        update_tasks: list[asyncio.Task] = [
            asyncio.create_task(device.update()) for device in self._device_container
        ]
        done, _ = await asyncio.wait(update_tasks, return_when=asyncio.ALL_COMPLETED)
        for task in done:
            exc = task.exception()
            if exc is not None and isinstance(exc, VeSyncError):
                logger.error('Error updating device: %s', exc)

    async def __aenter__(self) -> Self:
        """Asynchronous context manager enter."""
        return self

    async def __aexit__(self, *exec_info: object) -> None:
        """Asynchronous context manager exit."""
        if self.session and self._close_session:
            logger.debug('Closing session, exiting context manager')
            await self.session.close()
            return
        logger.debug('Session not closed, exiting context manager')

    async def _reauthenticate(self) -> bool:
        """Re-authenticate using stored username and password.

        Returns:
            True if re-authentication successful, False otherwise
        """
        self.enabled = False
        self._api_attempts += 1
        if self._api_attempts >= MAX_API_REAUTH_RETRIES:
            logger.error('Max API re-authentication attempts reached')
            raise VeSyncTokenError
        success = await self.auth.reauthenticate()
        if success:
            self.enabled = True
            self._api_attempts = 0
            return True
        return await self.auth.reauthenticate()

    async def async_call_api(
        self,
        api: str,
        method: str,
        json_object: dict | None | DataClassORJSONMixin = None,
        headers: dict | None = None,
        device: VeSyncBaseDevice | None = None,
    ) -> tuple[dict | None, int]:
        """Make API calls by passing endpoint, header and body.

        api argument is appended to `API_BASE_URL`.
        Raises VeSyncRateLimitError if API returns a rate limit error.

        Args:
            api (str): Endpoint to call with `API_BASE_URL`.
            method (str): HTTP method to use.
            json_object (dict | RequestBaseModel): JSON object to send in body.
            headers (dict): Headers to send with request.
            device (VeSyncBaseDevice | None): Device making the request, if any.

        Returns:
            tuple[dict | None, int]: Response and status code. Attempts to parse
                response as JSON, if not possible returns None.

        Raises:
            VeSyncAPIStatusCodeError: If API returns an error status code.
            VeSyncRateLimitError: If API returns a rate limit error.
            VeSyncServerError: If API returns a server error.
            VeSyncTokenError: If API returns an authentication error.
            ClientResponseError: If API returns a client response error.

        Note:
            Future releases will require the `json_object` argument to be a dataclass,
            instead of dictionary.
        """
        self.check_debug()
        if self.session is None:
            self.session = ClientSession()
            self._close_session = True
        response = None
        status_code = None
        if isinstance(json_object, DataClassORJSONMixin):
            req_dict = json_object.to_dict()
        elif isinstance(json_object, dict):
            req_dict = json_object
        else:
            req_dict = None
        try:
            async with self.session.request(
                method,
                url=self._api_base_url_for_current_region() + api,
                json=req_dict,
                headers=headers,
                raise_for_status=False,
            ) as response:
                resp_bytes = await response.read()

                LibraryLogger.log_api_call(
                    logger, response, resp_bytes, headers, req_dict
                )
                resp_dict, status_code = await self._api_response_wrapper(
                    response, api, req_dict, device=device
                )

        except ClientResponseError as e:
            LibraryLogger.log_api_exception(logger, exception=e, request_body=req_dict)
            raise
        return resp_dict, status_code

    async def _api_response_wrapper(
        self,
        response: ClientResponse,
        endpoint: str,
        request_body: dict | None,
        device: VeSyncBaseDevice | None = None,
    ) -> tuple[dict | None, int]:
        """Internal wrapper used by async_call_api."""
        if response.status != STATUS_OK:
            LibraryLogger.log_api_status_error(
                logger,
                status_code=response.status,
                response=response,
            )
            raise VeSyncAPIStatusCodeError(str(response.status))
        resp_bytes = await response.read()
        resp_dict = LibraryLogger.try_json_loads(resp_bytes)
        if isinstance(resp_dict, dict):
            error_info = ErrorCodes.get_error_info(resp_dict.get('code'))
            if error_info.error_type == ErrorTypes.TOKEN_ERROR:
                self.enabled = False
                if await self._reauthenticate():
                    return await self.async_call_api(
                        endpoint, 'post', request_body, device=device
                    )
                raise VeSyncTokenError(resp_dict.get('msg'))
            if resp_dict.get('msg') is not None:
                error_info.message = f'{error_info.message} ({resp_dict["msg"]})'
            raise_api_errors(error_info)

        return resp_dict, response.status

    def _api_base_url_for_current_region(self) -> str:
        """Retrieve the API base url for the current region.

        At this point, only two different URLs exist: One for `EU` region
        (for all EU countries), and one for all others
        (currently `US`, `CA`, `MX`, `JP` - also used as a fallback).

        If `API_BASE_URL` is set, it will take precedence over the determined URL.
        """
        return REGION_API_MAP[self.current_region]

    def _update_fw_version(self, info_list: list[FirmwareDeviceItemModel]) -> bool:
        """Update device firmware versions from API response."""
        if not info_list:
            logger.info('No devices found in firmware response')
            return False
        update_dict = {}
        for device in info_list:
            if not device.firmUpdateInfos:
                if device.code != 0:
                    logger.info(
                        'Device %s has error code %s with message: %s',
                        device.deviceName,
                        device.code,
                        device.msg,
                    )
                else:
                    logger.debug(
                        'Device %s has no firmware updates available', device.deviceName
                    )
                continue
            for update_info in device.firmUpdateInfos:
                update_dict[device.deviceCid] = (
                    update_info.currentVersion,
                    update_info.latestVersion,
                )
                if update_info.isMainFw is True:
                    break
        for device_obj in self._device_container:
            if device_obj.cid in update_dict:
                device_obj.latest_firm_version = update_dict[device_obj.cid][1]
                device_obj.current_firm_version = update_dict[device_obj.cid][0]
        return True

    async def check_firmware(self) -> bool:
        """Check for firmware updates for all devices.

        This method will check for firmware updates for all devices in the
        device container. It will call the `get_firmware_update()` method on
        each device and log the results.
        """
        if len(self._device_container) == 0:
            logger.warning('No devices to check for firmware updates')
            return False
        body_fields = [
            field.name
            for field in fields(RequestFirmwareModel)
            if field.default_factory is MISSING and field.default is MISSING
        ]
        body = Helpers.get_class_attributes(self, body_fields)
        body['cidList'] = [device.cid for device in self._device_container]
        resp_dict, _ = await self.async_call_api(
            '/cloud/v2/deviceManaged/getFirmwareUpdateInfoList',
            'post',
            json_object=RequestFirmwareModel(**body),
        )
        if resp_dict is None:
            raise VeSyncAPIResponseError(
                'Error receiving response to firmware update request'
            )
        resp_model = ResponseFirmwareModel.from_dict(resp_dict)
        if resp_model.code != 0:
            error_info = ErrorCodes.get_error_info(resp_model.code)
            resp_message = resp_model.msg
            if resp_message is not None:
                error_info.message = f'{error_info.message} ({resp_message})'
            logger.warning('Error in firmware update response: %s', error_info.message)
            return False
        info_list = resp_model.result.cidFwInfoList
        return self._update_fw_version(info_list)
