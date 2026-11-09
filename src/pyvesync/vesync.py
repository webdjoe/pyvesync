"""VeSync API Device Library."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import MISSING, fields
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING, Self

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientResponseError
from mashumaro.mixins.orjson import DataClassORJSONMixin

from pyvesync.auth import VeSyncAuth
from pyvesync.const import (
    API_TOKEN_KEYS,
    DEFAULT_REGION,
    DEFAULT_TZ,
    MAX_API_REAUTH_RETRIES,
    REAUTH_WINDOW_SECONDS,
    REGION_API_MAP,
    STATUS_OK,
    ConnectionStatus,
    ProductTypes,
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
    VeSyncInvalidCredentialsError,
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
        '_reauth_limit_logged',
        '_reauth_lock',
        '_reauth_runs',
        '_reauth_stopped',
        '_reauth_succeeded',
        '_reauth_window_start',
        '_redact',
        '_retry_rejection_logged',
        '_verbose',
        'enabled',
        'in_process',
        'language',
        'measure_unit',
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
        self._reauth_window_start = 0.0
        self._reauth_limit_logged = False
        self._retry_rejection_logged: tuple[int, str] | None = None
        self._reauth_runs = 0
        self._reauth_stopped = False
        self._reauth_succeeded = False
        self._reauth_lock = asyncio.Lock()
        self._close_session = False
        self.redact = redact
        self._verbose: bool = False
        self.time_zone: str = time_zone
        self.language: str = 'en'
        self.enabled = False
        self.in_process = False
        self.measure_unit: str | None = None
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
        await self.auth.save_credentials_to_file(filename)

    async def load_credentials_from_file(
        self, filename: str | Path | None = None
    ) -> bool:
        """Load authentication credentials from a file.

        Args:
            filename (str | Path | None): The name of the file to load credentials from.
                If None, `.vesync_auth` is searched for in the current working
                directory and then the user's home directory.

        Returns:
            bool: True if credentials were loaded successfully, False if the file was
                not found, could not be parsed or the credentials were incomplete.
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
        try:
            if not self.auth.is_authenticated or (
                not self.auth.token or not self.auth.account_id
            ):
                logger.info("Not logged in to VeSync, can't get devices")
                return False

            request_model = RequestDeviceListModel(
                token=self.auth.token,
                accountID=self.auth.account_id,
                timeZone=self.time_zone,
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

            # An error response can have no result, so check it before parsing.
            code = response_dict.get('code')
            if code != 0:
                error_info = ErrorCodes.get_error_info(code, response_dict.get('msg'))
                if error_info.error_type == ErrorTypes.SERVER_ERROR:
                    raise VeSyncServerError(error_info.message)
                msg = (
                    'Error receiving response to device list request: '
                    f'{error_info.message}'
                )
                raise VeSyncAPIResponseError(msg)

            response = Helpers.model_maker(
                logger, ResponseDeviceListModel, 'get_devices', response_dict
            )
            if response is None:
                raise VeSyncAPIResponseError('Invalid device list response')

            return self.process_devices(response)
        finally:
            self.in_process = False

    async def login(self) -> bool:  # pylint: disable=W9006 # pylint mult docstring raises
        """Log into VeSync server.

        Username and password are provided when class is instantiated. If an
        automatic re-login is running, this waits for it to finish first.

        Returns:
            True if login successful, False otherwise

        Raises:
            VeSyncLoginError: If login fails, for example due to invalid username
                or password.
            VeSyncAPIResponseError: If API response is invalid.
            VeSyncServerError: If server returns an error.
        """
        async with self._reauth_lock:
            self.enabled = False
            success = await self._auth.login()
            if success:
                self.enabled = True
                self._reauth_stopped = False
            return success

    async def update(self) -> None:
        """Fetch updated information about devices and new device list.

        Pulls devices list from VeSync and instantiates any new devices. Devices
        are stored in the instance attributes `outlets`, `switches`, `fans`, and
        `bulbs`. The `_device_list` attribute is a dictionary of these attributes.

        Raises:
            VeSyncInvalidCredentialsError: If automatic re-login stopped because
                the username or password was rejected. Call `login()` with valid
                credentials to continue.
        """
        self._raise_if_reauth_stopped()
        if not self.enabled:
            logger.error('Not logged in to VeSync')
            return
        await self.get_devices()

        await self.update_all_devices()

    async def update_all_devices(self) -> None:
        """Run `get_details()` for each device and update state.

        An error updating one device is logged and doesn't stop the others.
        Errors from logging in again are logged once where the login runs, so
        they are only logged at debug level here.

        Raises:
            VeSyncInvalidCredentialsError: If a re-login was rejected because
                of the username or password, after all devices have been
                updated. Automatic re-login has stopped, so the caller should
                ask for new credentials.
        """
        logger.debug('Start updating the device details one by one')
        if len(self._device_container) == 0:
            logger.error('No devices to update')
            return
        update_tasks: list[asyncio.Task] = [
            asyncio.create_task(device.update()) for device in self._device_container
        ]
        done, _ = await asyncio.wait(update_tasks, return_when=asyncio.ALL_COMPLETED)
        credentials_error: VeSyncInvalidCredentialsError | None = None
        for task in done:
            exc = task.exception()
            if exc is None:
                continue
            # Raised only if a re-login was rejected, not for a device response.
            if isinstance(exc, VeSyncInvalidCredentialsError) and self._reauth_stopped:
                if credentials_error is None:
                    credentials_error = exc
                logger.debug('Error updating device: %s', exc)
            elif isinstance(exc, VeSyncTokenError):
                logger.debug('Error updating device: %s', exc)
            elif isinstance(exc, VeSyncError):
                logger.error('Error updating device: %s', exc)
            else:
                logger.error('Unexpected error updating device: %s', exc, exc_info=exc)
        if credentials_error is not None:
            raise credentials_error

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

    async def _reauthenticate(self, rejected_token: str) -> None:
        """Log in again after the API rejected `rejected_token`.

        One re-login runs at a time, and requests that wait for it share its
        result: if it succeeds they return and retry with the current token, if
        it fails they raise without logging in again. At most
        `MAX_API_REAUTH_RETRIES` re-logins run within `REAUTH_WINDOW_SECONDS`;
        the count starts over once the window passes. If the API rejects the
        username or password, re-login stops until `login()` succeeds.

        Each outcome is logged once: reaching the limit (once per window), the
        stop, and each failed login. Requests that share an outcome raise
        without logging it again.

        Args:
            rejected_token (str): The token the rejected request was sent with.

        Raises:
            VeSyncTokenError: If the re-login limit for the window is reached, or
                the login failed for a reason other than the credentials. When
                this request ran the login, the login error is the cause.
            VeSyncInvalidCredentialsError: If the username or password was
                rejected, now or by an earlier re-login.
        """
        runs_before_wait = self._reauth_runs
        async with self._reauth_lock:
            # A failed login keeps the old token, so a new token means success.
            if self.auth.is_authenticated and self.auth.token != rejected_token:
                logger.debug('Token already renewed by another request')
                return
            self._raise_if_reauth_stopped()
            if self._reauth_runs != runs_before_wait:
                # The login may return the same token, so check the result.
                if self._reauth_succeeded:
                    logger.debug('Re-authenticated by another request')
                    return
                msg = 'Re-authentication by another request failed'
                raise VeSyncTokenError(msg)
            now = monotonic()
            if now - self._reauth_window_start > REAUTH_WINDOW_SECONDS:
                self._reauth_window_start = now
                self._api_attempts = 0
                self._reauth_limit_logged = False
            if self._api_attempts >= MAX_API_REAUTH_RETRIES:
                if not self._reauth_limit_logged:
                    self._reauth_limit_logged = True
                    logger.error(
                        'Re-login limit reached (%s in %s seconds); requests with '
                        'a rejected token fail until the limit resets',
                        MAX_API_REAUTH_RETRIES,
                        REAUTH_WINDOW_SECONDS,
                    )
                msg = 'Re-login limit reached'
                raise VeSyncTokenError(msg)
            self._api_attempts += 1
            self._reauth_succeeded = False
            try:
                await self.auth.reauthenticate()
            except VeSyncInvalidCredentialsError:
                # Re-raised to the caller, so no traceback in the log.
                logger.error(  # noqa: TRY400
                    'Username or password rejected; automatic re-login stopped '
                    'until login() succeeds'
                )
                self._reauth_stopped = True
                self.enabled = False
                raise
            except VeSyncError as exc:
                logger.info('Re-login failed: %s', exc)
                msg = 'Re-authentication failed'
                raise VeSyncTokenError(msg) from exc
            finally:
                self._reauth_runs += 1
            self._reauth_succeeded = True
            self.enabled = True

    def _raise_if_reauth_stopped(self) -> None:
        """Raise if automatic re-login stopped over rejected credentials.

        Raises:
            VeSyncInvalidCredentialsError: If re-login is stopped.
        """
        if self._reauth_stopped:
            msg = (
                'Automatic re-login stopped because the username or password '
                'was rejected; call login() with valid credentials'
            )
            raise VeSyncInvalidCredentialsError(msg)

    def _with_current_token(self, request_part: dict | None) -> dict | None:
        """Return a copy of a request body or headers with the current token."""
        if request_part is None:
            return None
        return {
            key: self.auth.token if key in API_TOKEN_KEYS else value
            for key, value in request_part.items()
        }

    @staticmethod
    def _request_token(body: dict | None, headers: dict | None) -> str | None:
        """Return the token a request was sent with, if it had one."""
        for part in (body, headers):
            for key in API_TOKEN_KEYS:
                token = (part or {}).get(key)
                if isinstance(token, str) and token:
                    return token
        return None

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
            If the API rejects the token a request was sent with, the manager
            logs in again and resends the request once with the new token.
            Requests without a token, such as the login requests, are not
            retried.

            Future releases will require the `json_object` argument to be a dataclass,
            instead of dictionary.
        """
        del device  # Accepted for compatibility with existing callers, not used.
        self.check_debug()
        if isinstance(json_object, DataClassORJSONMixin):
            req_dict = json_object.to_dict()
        elif isinstance(json_object, dict):
            req_dict = json_object
        else:
            req_dict = None
        try:
            return await self._send_api_request(api, method, req_dict, headers)
        except VeSyncTokenError:
            rejected_token = self._request_token(req_dict, headers)
            if rejected_token is None:
                raise
            await self._reauthenticate(rejected_token)
        # The retries that followed the same login share the run and token.
        relogin = (self._reauth_runs, self.auth.token)
        try:
            return await self._send_api_request(
                api,
                method,
                self._with_current_token(req_dict),
                self._with_current_token(headers),
            )
        except VeSyncTokenError:
            # Log once for all the retries that followed the same login. The
            # error is re-raised to the caller, so no traceback in the log.
            if self._retry_rejection_logged != relogin:
                self._retry_rejection_logged = relogin
                logger.error(  # noqa: TRY400
                    'The API rejected the new token after logging in again'
                )
            raise

    async def _send_api_request(
        self,
        api: str,
        method: str,
        req_dict: dict | None,
        headers: dict | None,
    ) -> tuple[dict | None, int]:
        """Send one request and process the response, without retrying."""
        if self.session is None:
            self.session = ClientSession()
            self._close_session = True
        try:
            async with self.session.request(
                method,
                url=self._api_base_url_for_current_region() + api,
                json=req_dict,
                headers=headers,
                raise_for_status=False,
            ) as response:
                resp_bytes = await response.read()
                resp_status = response.status

                if resp_status != STATUS_OK:
                    LibraryLogger.log_api_status_error(logger, response=response)
                    raise VeSyncAPIStatusCodeError(str(resp_status))

                LibraryLogger.log_api_call(
                    logger,
                    response=response,
                    response_body=resp_bytes,
                    request_headers=headers,
                    request_body=req_dict,
                )
                return self._api_response_wrapper(resp_bytes, resp_status)

        except ClientResponseError as e:
            LibraryLogger.log_api_exception(logger, exception=e, request_body=req_dict)
            raise

    @staticmethod
    def _api_response_wrapper(
        response_bytes: bytes | None,
        status_code: int,
    ) -> tuple[dict | None, int]:
        """Parse a response and raise for API error codes.

        Raises:
            VeSyncTokenError: If the API rejected the request's token.
        """
        resp_dict = LibraryLogger.try_json_loads(response_bytes)
        if not isinstance(resp_dict, dict):
            return None, status_code

        error_info = Helpers.parse_error_code(resp_dict)
        if error_info.error_type == ErrorTypes.TOKEN_ERROR:
            raise VeSyncTokenError(error_info.message)
        raise_api_errors(error_info)

        return resp_dict, status_code

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
        if len(self.devices) == 0:
            logger.warning('No devices to check for firmware updates')
            return False
        body_fields = tuple(
            field.name
            for field in fields(RequestFirmwareModel)
            if field.default_factory is MISSING and field.default is MISSING
        )
        body = Helpers.get_manager_attributes(self, body_fields)

        # Add cid list of devices that are online and not an air fryer
        body['cidList'] = [
            device.cid
            for device in self.devices
            if (
                device.product_type != ProductTypes.AIR_FRYER
                and device.state.connection_status == ConnectionStatus.ONLINE
            )
        ]

        if len(body['cidList']) == 0:
            logger.warning(
                'No online devices (excluding air fryers) to check firmware for'
            )
            return False

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
