"""VeSync API Device Libary."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import MISSING, fields
from pathlib import Path
from typing import Self

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientResponseError
from mashumaro.exceptions import MissingField, UnserializableDataError
from mashumaro.mixins.orjson import DataClassORJSONMixin

from pyvesync.const import (
    API_BASE_URL_EU,
    API_BASE_URL_US,
    DEFAULT_REGION,
    DEFAULT_TZ,
    NON_EU_REGIONS,
    STATUS_OK,
)
from pyvesync.device_container import DeviceContainer, DeviceContainerInstance
from pyvesync.models.vesync_models import (
    FirmwareDeviceItemModel,
    RequestDeviceListModel,
    RequestFirmwareModel,
    RequestGetTokenModel,
    RequestLoginTokenModel,
    RespGetTokenResultModel,
    RespLoginTokenResultModel,
    ResponseDeviceListModel,
    ResponseFirmwareModel,
    ResponseLoginModel,
)
from pyvesync.utils.errors import (
    ErrorCodes,
    ErrorTypes,
    VeSyncAPIResponseError,
    VeSyncAPIStatusCodeError,
    VeSyncError,
    VeSyncLoginError,
    VeSyncServerError,
    raise_api_errors,
)
from pyvesync.utils.helpers import Helpers
from pyvesync.utils.logs import LibraryLogger

logger = logging.getLogger(__name__)


class VeSync:  # pylint: disable=function-redefined
    """VeSync Manager Class."""

    __slots__ = (
        '__weakref__',
        '_account_id',
        '_close_session',
        '_debug',
        '_device_container',
        '_redact',
        '_token',
        '_verbose',
        'country_code',
        'enabled',
        'in_process',
        'language',
        'password',
        'session',
        'time_zone',
        'username',
    )

    def __init__(  # noqa: PLR0913
        self,
        username: str,
        password: str,
        country_code: str = DEFAULT_REGION,
        session: ClientSession | None = None,
        time_zone: str = DEFAULT_TZ,
        debug: bool = False,
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
            debug (bool): Enable debug logging, by default False.
            redact (bool): Enable redaction of sensitive information, by default True.

        Attributes:
            session (ClientSession):  Client session for API calls
            devices (DeviceContainer): Container for all VeSync devices,
                has functionality of a mutable set. See
                [`DeviceContainer`][pyvesync.device_container.DeviceContainer] for
                more information
            token (str): VeSync API token
            account_id (str): VeSync account ID
            country_code (str): Country code for VeSync account pulled from API
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

        See Also:
            :obj:`DeviceContainer`
                Container object to store VeSync devices
            :obj:`DeviceState`
                Object to store device state information
        """
        self.session = session
        self._close_session = False
        self._debug = debug
        self.redact = redact
        self.username: str = username
        self.password: str = password
        self._token: str | None = None
        self._account_id: str | None = None
        self.country_code: str = country_code.upper()
        self._verbose: bool = False
        self.time_zone: str = time_zone
        self.language: str = 'en'
        self.enabled = False
        self.in_process = False
        self._device_container: DeviceContainer = DeviceContainerInstance

    @property
    def devices(self) -> DeviceContainer:
        """Return VeSync device container.

        See Also:
            The pyvesync.device_container.DeviceContainer object
            for methods and properties.
        """
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
            LibraryLogger.debug = True
            LibraryLogger.configure_logger(logging.DEBUG)
        else:
            LibraryLogger.debug = False
            LibraryLogger.configure_logger(logging.WARNING)
        self._debug = new_flag

    @property
    def verbose(self) -> bool:
        """Enable verbose logging."""
        return LibraryLogger.verbose

    @verbose.setter
    def verbose(self, new_flag: bool) -> None:
        """Set verbose logging."""
        if new_flag:
            LibraryLogger.verbose = True
            LibraryLogger.configure_logger(logging.DEBUG)
        else:
            LibraryLogger.verbose = False
        self._verbose = new_flag

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

    def log_to_file(self, filename: str | Path, std_out: bool = True) -> None:
        """Log to file and enable debug logging.

        Args:
            filename (str | Path): The name of the file to log to.
            std_out (bool): If False, logs will not print to std out.
        """
        self.debug = True
        LibraryLogger.configure_logger(logging.DEBUG, file_name=filename, std_out=std_out)
        logger.debug('Logging to file: %s', filename)

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
            logger.debug('Added %s devices', str(new_device_count - current_device_count))
        return True

    async def get_devices(self) -> bool:
        """Return tuple listing outlets, switches, and fans of devices.

        This is also called by `VeSync.update()`

        Raises:
            VeSyncAPIResponseError: If API response is invalid.
            VeSyncServerError: If server returns an error.
        """
        if not self.enabled:
            return False

        self.in_process = True
        proc_return = False
        request_model = RequestDeviceListModel(
            token=self.token, accountID=self.account_id, timeZone=self.time_zone
        )
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
            resp_message = response.msg
            info_msg = f'{error_info.message} ({resp_message})'
            if error_info.error_type == ErrorTypes.SERVER_ERROR:
                raise VeSyncServerError(info_msg)
            raise VeSyncAPIResponseError(
                'Error receiving response to device list request'
            )

        self.in_process = False

        return proc_return

    async def login(self) -> None:  # pylint: disable=W9006 # pylint mult docstring raises
        """Log into VeSync server.

        Username and password are provided when class is instantiated.

        Raises:
            VeSyncLoginError: If login fails, for example due to invalid username
                or password.
            VeSyncAPIResponseError: If API response is invalid.
            VeSyncServerError: If server returns an error.
        """
        if (
            not isinstance(self.username, str)
            or len(self.username) == 0
            or not isinstance(self.password, str)
            or len(self.password) == 0
        ):
            raise VeSyncLoginError('Username and password must be specified')

        request_auth = RequestGetTokenModel(
            email=self.username,
            method='authByPWDOrOTM',
            password=self.password,
        )
        resp_dict, _ = await self.async_call_api(
            '/globalPlatform/api/accountAuth/v1/authByPWDOrOTM',
            'post',
            json_object=request_auth,
        )
        if resp_dict is None:
            raise VeSyncAPIResponseError('Error receiving response to auth request')

        if resp_dict.get('code') != 0:
            error_info = ErrorCodes.get_error_info(resp_dict.get('code'))
            resp_message = resp_dict.get('msg')
            if resp_message is not None:
                error_info.message = f'{error_info.message} ({resp_message})'

            msg = f'Error receiving response to auth request - {error_info.message}'
            raise VeSyncAPIResponseError(msg)

        try:
            response_model = ResponseLoginModel.from_dict(resp_dict)
        except Exception as exc:
            logger.debug('Error parsing auth response: %s', exc)
            raise VeSyncAPIResponseError(
                'Error receiving response to auth request'
            ) from exc

        result = response_model.result
        if not isinstance(result, RespGetTokenResultModel):
            raise VeSyncAPIResponseError(
                'Error receiving response to login request -'
                ' result is not IntRespAuthResultModel'
            )

        return await self._login_token(auth_code=result.authorizeCode)

    async def _login_token(
        self,
        auth_code: str | None = None,
        region_change_token: str | None = None,
    ) -> None:  # pylint: disable=W9006 # pylint mult docstring raises
        """Exchanges the authorization code for a token.

        This completes the login process. If the initial call fails with
        `"login trigger cross region error."`, the region is adjusted and
        another attempt is made.

        Args:
            auth_code (str): Auth code to use for logging in.
            region_change_token (str): "bizToken" to use when calling this endpoint
                for a second time with a different region.

        Raises:
            VeSyncLoginError: If login fails, for example due to invalid username
                or password.
            VeSyncAPIResponseError: If API response is invalid.
            VeSyncServerError: If server returns an error.
        """
        request_login = RequestLoginTokenModel(
            method='loginByAuthorizeCode4Vesync',
            authorizeCode=auth_code,
            bizToken=region_change_token,
            userCountryCode=self.country_code,
            regionChange='last_region' if region_change_token else None,
        )
        resp_dict, _ = await self.async_call_api(
            '/user/api/accountManage/v1/loginByAuthorizeCode4Vesync',
            'post',
            json_object=request_login,
        )
        if resp_dict is None:
            raise VeSyncAPIResponseError('Error receiving response to login request')
        try:
            response_model = ResponseLoginModel.from_dict(resp_dict)
            if not isinstance(response_model.result, RespLoginTokenResultModel):
                raise VeSyncAPIResponseError(
                    'Error receiving response to login request -'
                    'result is not RespLoginTokenResultModel'
                )
            if response_model.code != 0:
                error_info = ErrorCodes.get_error_info(resp_dict.get('code'))

                # Handle cross region error by retrying login with new region
                if error_info.error_type == ErrorTypes.CROSS_REGION:
                    result = response_model.result
                    self.country_code = result.countryCode
                    return await self._login_token(region_change_token=result.bizToken)
                resp_message = resp_dict.get('msg')
                if resp_message is not None:
                    error_info.message = f'{error_info.message} ({resp_message})'
                msg = f'Error receiving response to login request - {error_info.message}'
                raise VeSyncLoginError(msg)

            result = response_model.result
            if not isinstance(result, RespLoginTokenResultModel):
                raise VeSyncAPIResponseError(
                    'Error receiving response to login request -'
                    ' result is not RespLoginTokenResultModel'
                )

            self._token = result.token
            self._account_id = result.accountID
            self.country_code = result.countryCode
            self.enabled = True
            logger.debug('Login successful')

        except (MissingField, UnserializableDataError) as exc:
            logger.debug('Error parsing login response: %s', exc)
            raise VeSyncAPIResponseError(
                'Error receiving response to login request'
            ) from exc

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
        update_tasks = [
            asyncio.create_task(device.update()) for device in self._device_container
        ]
        done, _ = await asyncio.wait(update_tasks, return_when=asyncio.ALL_COMPLETED)
        for task in done:
            exc = task.exception()
            if exc is not None and isinstance(exc, VeSyncError):
                logger.debug('Error updating device: %s', exc)

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

    async def async_call_api(
        self,
        api: str,
        method: str,
        json_object: dict | None | DataClassORJSONMixin = None,
        headers: dict | None = None,
    ) -> tuple[dict | None, int | None]:
        """Make API calls by passing endpoint, header and body.

        api argument is appended to `API_BASE_URL`.
        Raises VeSyncRateLimitError if API returns a rate limit error.

        Args:
            api (str): Endpoint to call with `API_BASE_URL`.
            method (str): HTTP method to use.
            json_object (dict | RequestBaseModel): JSON object to send in body.
            headers (dict): Headers to send with request.

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
                status_code = response.status
                resp_bytes = await response.read()
                if status_code != STATUS_OK:
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
                    error_info = ErrorCodes.get_error_info(resp_dict.get('code'))
                    if resp_dict.get('msg') is not None:
                        error_info.message = f'{error_info.message} ({resp_dict["msg"]})'
                        raise_api_errors(error_info)

                return resp_dict, status_code

        except ClientResponseError as e:
            LibraryLogger.log_api_exception(logger, exception=e, request_body=req_dict)
            raise

    def _api_base_url_for_current_region(self) -> str:
        """Retrieve the API base url for the current region.

        At this point, only two different URLs exist: One for `EU` region
        (for all EU countries), and one for all others
        (currently `US`, `CA`, `MX`, `JP` - also used as a fallback).

        If `API_BASE_URL` is set, it will take precedence over the determined URL.
        """
        if self.country_code in NON_EU_REGIONS:
            return API_BASE_URL_US
        return API_BASE_URL_EU

    def _update_fw_version(self, info_list: list[FirmwareDeviceItemModel]) -> bool:
        """Update device firmware versions from API response."""
        if not info_list:
            logger.debug('No devices found in firmware response')
            return False
        update_dict = {}
        for device in info_list:
            if not device.firmUpdateInfos:
                if device.code != 0:
                    logger.debug(
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
            logger.debug('No devices to check for firmware updates')
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
            logger.debug('Error in firmware update response: %s', error_info.message)
            return False
        info_list = resp_model.result.cidFwInfoList
        return self._update_fw_version(info_list)
