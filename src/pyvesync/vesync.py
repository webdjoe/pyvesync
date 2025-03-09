"""VeSync API Device Libary."""

from __future__ import annotations
import logging
import asyncio
from typing import Self
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientResponseError
import orjson

from pyvesync.helper_utils.helpers import Helpers
from pyvesync.const import API_BASE_URL, DEFAULT_REGION
from pyvesync.device_container import DeviceContainer
from pyvesync.data_models.login_models import RequestLoginModel, ResponseLoginModel
from pyvesync.data_models.base_models import RequestBaseModel
from pyvesync.helper_utils.logs import LibraryLogger
from pyvesync.data_models.device_list_models import (
    RequestDeviceListModel,
    ResponseDeviceListModel
    )
from pyvesync.helper_utils.errors import (
    ErrorCodes,
    ErrorTypes,
    VeSyncAPIResponseError,
    VeSyncAPIStatusCodeError,
    VeSyncError,
    VeSyncRateLimitError,
    VeSyncServerError,
    VesyncLoginError,
    VeSyncTokenError,
    )


logger = logging.getLogger(__name__)

API_RATE_LIMIT: int = 30
DEFAULT_TZ: str = 'America/New_York'

DEFAULT_ENER_UP_INT: int = 21600


class VeSync:  # pylint: disable=function-redefined
    """VeSync Manager Class."""

    def __init__(self,
                 username: str,
                 password: str,
                 session: ClientSession | None = None,
                 time_zone: str = DEFAULT_TZ,
                 debug: bool = False,
                 redact: bool = True) -> None:
        """Initialize VeSync Manager.

        This class is used as the manager for all VeSync objects, all methods and
        API calls are performed from this class. Time zone, debug and redact are
        optional. Time zone must be a string of an IANA time zone format. Once
        class is instantiated, call `await manager.login()` to log in to VeSync servers,
        which returns `True` if successful. Once logged in, call
        `await manager.get_devices()` to retrieve devices. Then `await `manager.update()`
        to update all devices or `await manager.devices[0].update()` to
        update a single device.

        Parameters:
            username : str
                VeSync account username (usually email address)
            password : str
                VeSync account password
            session : ClientSession, optional
                aiohttp client session for API calls, by default None
            time_zone : str, optional
                Time zone for device from IANA database, by default DEFAULT_TZ
            debug : bool, optional
                THIS IS DEPRECATED, to debug set instance property `manager.debug=False`
            redact : bool, optional
                Redact sensitive information in logs, by default True

        Attributes:
            session : ClientSession
                Client session for API calls
            devices : DeviceContainer
                Container for all VeSync devices, has functionality of set
            token : str
                VeSync API token
            account_id : str
                VeSync account ID
            enabled : bool
                True if logged in to VeSync, False if not

        Notes:
            This class is a context manager, use `async with VeSync() as manager:`
            to manage the session context. The session will be closed when exiting
            if no session is passed in.

            The `manager.devices` attribute is a DeviceContainer object that contains
            all VeSync devices. The `manager.devices` object has the functionality of
            a set, and can be iterated over to access devices. See :obj:`DeviceContainer`
            for more information.

            If using a context manager is not convenient, `manager.__aenter__()` and
            `manager.__aexit__()` can be called directly.
        """
        self.session = session
        self._close_session = False
        self._debug = debug
        self._redact = redact
        if redact:
            self.redact = redact
        self.username: str = username
        self.password: str = password
        self._token: str | None = None
        self._account_id: str | None = None
        self.country_code: str = DEFAULT_REGION
        self.time_zone: str = time_zone

        self.enabled = False
        self.in_process = False
        self._energy_check = True
        self._device_container: DeviceContainer = DeviceContainer()

    @property
    def devices(self) -> DeviceContainer:
        """Return VeSync device container."""
        return self._device_container

    @property
    def token(self) -> str:
        """Return VeSync API token."""
        if self._token is None:
            raise AttributeError('Token not set, run login() method')
        return self._token

    @property
    def account_id(self) -> str:
        """Return VeSync account ID."""
        if self._account_id is None:
            raise AttributeError('Account ID not set, run login() method')
        return self._account_id

    @property
    def debug(self) -> bool:
        """Return debug flag."""
        return self._debug

    @debug.setter
    def debug(self, new_flag: bool) -> None:
        """Set debug flag."""
        if new_flag:
            LibraryLogger.configure_logger(logging.DEBUG)
        else:
            LibraryLogger.configure_logger(logging.WARNING)
        self._debug = new_flag

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

    def process_devices(self, dev_list_resp: ResponseDeviceListModel) -> bool:
        """Instantiate Device Objects.

        Internal method run by `get_devices()` to instantiate device objects.

        """
        current_device_count = len(self._device_container)

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
            logger.debug(
                'Added %s devices', str(new_device_count - current_device_count)
                )
        return True

    async def get_devices(self) -> bool:
        """Return tuple listing outlets, switches, and fans of devices.

        This is an internal method called by `update()`

        Raises:
            VeSyncAPIResponseError: If API response is invalid.
            VeSyncServerError: If server returns an error.
        """
        if not self.enabled:
            return False

        self.in_process = True
        proc_return = False
        request_model = RequestDeviceListModel(
            token=self.token,
            accountID=self.account_id,
            timeZone=self.time_zone
        )
        response_bytes, _ = await self.async_call_api(
            '/cloud/v1/deviceManaged/devices',
            'post',
            headers=Helpers.req_header_bypass(),
            json_object=request_model.to_dict(),
        )

        if response_bytes is None or not LibraryLogger.is_json(response_bytes):
            raise VeSyncAPIResponseError(
                'Error receiving response to device list request')

        response = ResponseDeviceListModel.from_json(response_bytes)

        if response.code == 0:
            proc_return = self.process_devices(response)
        else:
            error_info = ErrorCodes.get_error_info(response.code)
            resp_message = response.msg
            info_msg = f'{error_info.message} ({resp_message})'
            if error_info.error_type == ErrorTypes.SERVER_ERROR:
                raise VeSyncServerError(info_msg)
            raise VeSyncAPIResponseError(
                'Error receiving response to device list request')

        self.in_process = False

        return proc_return

    async def login(self) -> bool:  # pylint: disable=W9006 # pylint mult docstring raises
        """Log into VeSync server.

        Username and password are provided when class is instantiated.

        Returns:
            True if login successful, False if not.

        Raises:
            VeSyncLoginError: If login fails due to invalid username or password.
            VeSyncAPIResponseError: If API response is invalid.
            VeSyncServerError: If server returns an error.
        """
        if not isinstance(self.username, str) or len(self.username) == 0 \
                or not isinstance(self.password, str) or len(self.password) == 0:
            raise VesyncLoginError('Username and password must be specified')
        request_login = RequestLoginModel(
            email=self.username,
            method='login',
            password=self.password,
        )
        resp_bytes, _ = await self.async_call_api(
            '/cloud/v1/user/login', 'post',
            json_object=request_login.to_dict()
        )
        if resp_bytes is None or not LibraryLogger.is_json(resp_bytes):
            raise VeSyncAPIResponseError('Error receiving response to login request')
        response = orjson.loads(resp_bytes)
        if response.get('code') == 0:
            response_model = ResponseLoginModel.from_json(resp_bytes)
            result = response_model.result
            self._token = result.token
            self._account_id = result.accountID
            self.country_code = result.countryCode
            self.enabled = True
            logger.debug('Login successful')
            return True

        error_info = ErrorCodes.get_error_info(response.get("code"))
        resp_message = response.get('msg')
        info_msg = f'{error_info.message} ({resp_message})'
        if error_info.error_type == ErrorTypes.AUTHENTICATION:
            raise VesyncLoginError(info_msg)
        if error_info.error_type == ErrorTypes.SERVER_ERROR:
            raise VeSyncServerError(info_msg)
        raise VeSyncAPIResponseError('Error receiving response to login request')

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
        update_tasks = [device.update() for device in self._device_container]
        for update_coro in asyncio.as_completed(update_tasks):
            try:
                await update_coro
            except VeSyncError as exc:
                logger.debug('Error updating device: %s', exc)

    async def __aenter__(self) -> Self:
        """Asynchronous context manager enter."""
        return self

    async def __aexit__(self, *exec_info: object) -> None:
        """Asynchronous context manager exit."""
        if self.session and self._close_session:
            logger.debug("Closing session, exiting context manager")
            await self.session.close()
            return
        logger.debug("Session not closed, exiting context manager")

    async def async_call_api(
        self,
        api: str,
        method: str,
        json_object: dict | None | RequestBaseModel = None,
        headers: dict | None = None,
    ) -> tuple[bytes | None, int | None]:
        """Make API calls by passing endpoint, header and body.

        api argument is appended to https://smartapi.vesync.com url.
        Raises VeSyncRateLimitError if API returns a rate limit error.

        Args:
            api (str): Endpoint to call with https://smartapi.vesync.com.
            method (str): HTTP method to use.
            json_object (dict): JSON object to send in body.
            headers (dict): Headers to send with request.

        Returns:
            tuple: Response and status code.

        Raises:
            VeSyncAPIStatusCodeError: If API returns an error status code.
            VeSyncRateLimitError: If API returns a rate limit error.
            VeSyncServerError: If API returns a server error.
            VeSyncTokenError: If API returns an authentication error.
            ClientResponseError: If API returns a client response error.
        """
        if self.session is None:
            self.session = ClientSession()
            self._close_session = True
        response = None
        status_code = None

        try:
            async with self.session.request(
                method,
                url=API_BASE_URL + api,
                json=json_object,
                headers=headers,
                raise_for_status=False,
            ) as response:
                if isinstance(json_object, RequestBaseModel):
                    req_dict = json_object.to_dict()
                elif isinstance(json_object, dict):
                    req_dict = json_object
                else:
                    req_dict = {}
                status_code = response.status
                resp_bytes = await response.read()
                if status_code != 200:
                    LibraryLogger.log_api_status_error(
                        logger,
                        request_body=req_dict,
                        response=response,
                        response_bytes=resp_bytes,
                    )
                    raise VeSyncAPIStatusCodeError(str(status_code))

                LibraryLogger.log_api_call(logger, response, resp_bytes, req_dict)
                resp_dict = Helpers.try_json_loads(resp_bytes)
                if isinstance(resp_dict, dict):
                    resp_code = ErrorCodes.get_error_info(resp_dict.get("code"))
                    match resp_code.error_type:
                        case ErrorTypes.RATE_LIMIT:
                            logger.error("Rate limit error in API call to %s", api)
                            raise VeSyncRateLimitError
                        case ErrorTypes.SERVER_ERROR:
                            logger.error("Server error in API call to %s", api)
                            raise VeSyncServerError(resp_code.message)
                        case ErrorTypes.TOKEN_ERROR:
                            logger.error("Token error in API call to %s", api)
                            raise VeSyncTokenError
                        case _:
                            pass
                return resp_bytes, status_code

        except ClientResponseError as e:
            LibraryLogger.log_api_exception(logger, exception=e, request_body=req_dict)
            raise
