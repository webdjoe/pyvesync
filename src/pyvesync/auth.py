"""VeSync Authentication Module."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import orjson
from mashumaro.exceptions import MissingField, UnserializableDataError

from pyvesync.const import DEFAULT_REGION, NON_EU_COUNTRY_CODES
from pyvesync.models.vesync_models import (
    RequestGetTokenModel,
    RequestLoginTokenModel,
    RespGetTokenResultModel,
    RespLoginTokenResultModel,
    ResponseLoginModel,
)
from pyvesync.utils.errors import (
    ErrorCodes,
    ErrorTypes,
    VeSyncAPIResponseError,
    VeSyncLoginError,
    VeSyncServerError,
)

if TYPE_CHECKING:
    from pyvesync.vesync import VeSync

logger = logging.getLogger(__name__)


class VeSyncAuth:
    """VeSync Authentication Manager.

    Handles login, token management, and persistent storage of authentication
    credentials for VeSync API access.
    """

    __slots__ = (
        '_account_id',
        '_country_code',
        '_current_region',
        '_password',
        '_token',
        '_token_file_path',
        '_username',
        'manager',
    )

    def __init__(
        self,
        manager: VeSync,
        username: str,
        password: str,
        country_code: str = DEFAULT_REGION,
    ) -> None:
        """Initialize VeSync Authentication Manager.

        Args:
            manager: VeSync manager instance for API calls
            username: VeSync account username (email)
            password: VeSync account password
            country_code: Country code in ISO 3166 Alpha-2 format

        Note:
            Either username/password or token/account_id must be provided.
            If token_file_path is provided, credentials will be saved/loaded
            automatically.
        """
        self.manager = manager
        self._username = username
        self._password = password
        self._token: str | None = None
        self._account_id: str | None = None
        self._country_code = country_code.upper()
        self._current_region = self._country_code_to_region()
        self._token_file_path: Path | None = None

    def _country_code_to_region(self) -> str:
        """Convert country code to region string for API use."""
        if self._country_code in NON_EU_COUNTRY_CODES:
            return 'US'
        return 'EU'

    @property
    def token(self) -> str:
        """Return VeSync API token."""
        if self._token is None:
            raise AttributeError(
                'Token not set, run VeSync.login or VeSync.set_token method'
            )
        return self._token

    @property
    def account_id(self) -> str:
        """Return VeSync account ID."""
        if self._account_id is None:
            raise AttributeError(
                'Account ID not set, run VeSync.login or VeSync.set_token method'
            )
        return self._account_id

    @property
    def country_code(self) -> str:
        """Return country code."""
        return self._country_code

    @country_code.setter
    def country_code(self, value: str) -> None:
        """Set country code."""
        self._country_code = value.upper()

    @property
    def current_region(self) -> str:
        """Return current region."""
        return self._current_region

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self._token is not None and self._account_id is not None

    def set_credentials(
        self,
        token: str,
        account_id: str,
        country_code: str,
        region: str,
    ) -> None:
        """Set authentication credentials.

        Args:
            token: Authentication token
            account_id: Account ID
            country_code: Country code in ISO 3166 Alpha-2 format
            region: Current region code
        """
        self._token = token
        self._account_id = account_id
        self._country_code = country_code.upper()
        self._current_region = region

    async def reauthenticate(self) -> bool:
        """Re-authenticate using stored username and password.

        Returns:
            True if re-authentication successful, False otherwise
        """
        self.clear_credentials()
        return await self.login()

    async def load_credentials_from_file(
        self, file_path: str | Path | None = None
    ) -> bool:
        """Load credentials from token file if path is set.

        If no path is provided, it will try to load from the users home directory and
        then the current working directory.
        """
        locations = [Path.home() / '.vesync_auth', Path.cwd() / '.vesync_auth']
        file_path_object: Path | None = None
        if file_path is None:
            for location in locations:
                if location.exists():
                    file_path_object = location
                    break
        elif isinstance(file_path, str):
            file_path_object = Path(file_path)
        else:
            file_path_object = Path(file_path)
        if not file_path_object or not file_path_object.exists():
            logger.debug('Credentials file not found: %s', file_path_object)
            return False
        try:
            data = await asyncio.to_thread(
                Path(file_path_object).read_text, encoding='utf-8'
            )
            data = orjson.loads(data)
            self._token = data['token']
            self._account_id = data['account_id']
            self._country_code = data['country_code'].upper()
            self._current_region = data['current_region'].upper()
            logger.debug('Credentials loaded from file: %s', file_path)
        except orjson.JSONDecodeError as exc:
            logger.warning('Failed to load credentials from file: %s', exc)
            return False
        if self._token is None or self._account_id is None:
            logger.debug('Incomplete credentials in token file')
            self.manager.enabled = False
            return False
        self.manager.enabled = True
        return True

    def output_credentials_dict(self) -> dict[str, str] | None:
        """Output current credentials as a dictionary."""
        if not self.is_authenticated:
            logger.debug('No credentials to output, not authenticated')
            return None
        return {
            'token': self._token or '',
            'account_id': self._account_id or '',
            'country_code': self._country_code,
            'current_region': self._current_region,
        }

    def output_credentials_json(self) -> str | None:
        """Output current authentication credentials as a JSON string."""
        if not self.is_authenticated:
            logger.debug('No credentials to output, not authenticated')
            return None
        credentials = self.output_credentials_dict()
        if credentials is None:
            return None
        try:
            return orjson.dumps(credentials).decode('utf-8')
        except orjson.JSONEncodeError as exc:
            logger.warning('Failed to serialize credentials: %s', exc)
            return None

    async def save_credentials_to_file(self, file_path: str | Path | None = None) -> None:
        """Save authentication credentials to file."""
        if file_path is not None:
            file_path_object = Path(file_path)
        elif self._token_file_path is not None:
            file_path_object = self._token_file_path
        else:
            logger.debug('No token file path set, saving to default location')
            file_path_object = Path.home() / '.vesync_auth'
        if not self.is_authenticated:
            logger.debug('No credentials to save, not authenticated')
            return
        credentials = {
            'token': self._token,
            'account_id': self._account_id,
            'country_code': self._country_code,
        }
        try:
            data = orjson.dumps(credentials).decode('utf-8')
            await asyncio.to_thread(file_path_object.write_text, data, encoding='utf-8')
            logger.debug('Credentials saved to file: %s', file_path_object)
        except (orjson.JSONEncodeError, OSError) as exc:
            logger.warning('Failed to save credentials to file: %s', exc)

    def clear_credentials(self) -> None:
        """Clear all stored credentials."""
        self._token = None
        self._account_id = None

        # Remove token file if it exists
        if self._token_file_path and self._token_file_path.exists():
            try:
                self._token_file_path.unlink()
                logger.debug('Token file deleted: %s', self._token_file_path)
            except OSError as exc:
                logger.warning('Failed to delete token file: %s', exc)

    async def login(self) -> bool:
        """Log into VeSync server using username/password or existing token.

        Returns:
            True if login successful, False otherwise

        Raises:
            VeSyncLoginError: If login fails due to invalid credentials
            VeSyncAPIResponseError: If API response is invalid
            VeSyncServerError: If server returns an error
        """
        # Attempt username/password login
        if self._username and self._password:
            return await self._login_with_credentials()

        raise VeSyncLoginError(
            'No valid authentication method available. '
            'Provide either username/password or valid token/account_id.'
        )

    async def _login_with_credentials(self) -> bool:
        """Login using username and password.

        Returns:
            True if login successful

        Raises:
            VeSyncLoginError: If login fails
            VeSyncAPIResponseError: If API response is invalid
        """
        if not isinstance(self._username, str) or len(self._username) == 0:
            raise VeSyncLoginError('Username must be a non-empty string')

        if not isinstance(self._password, str) or len(self._password) == 0:
            raise VeSyncLoginError('Password must be a non-empty string')

        try:
            # Step 1: Get authorization code
            auth_code = await self._get_authorization_code()

            # Step 2: Exchange authorization code for token
            await self._exchange_authorization_code(auth_code)
            logger.debug('Login successful for user: %s', self._username)
        except (VeSyncLoginError, VeSyncAPIResponseError, VeSyncServerError):
            raise
        except Exception as exc:
            msg = f'Unexpected error during login: {exc}'
            raise VeSyncLoginError(msg) from exc
        return True

    async def _get_authorization_code(self) -> str:
        """Get authorization code using username and password.

        Returns:
            Authorization code

        Raises:
            VeSyncAPIResponseError: If API response is invalid
            VeSyncLoginError: If authentication fails
        """
        request_auth = RequestGetTokenModel(
            email=self._username,  # type: ignore[arg-type]
            method='authByPWDOrOTM',
            password=self._password,  # type: ignore[arg-type]
        )

        resp_dict, _ = await self.manager.async_call_api(
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

            msg = f'Authentication failed - {error_info.message}'
            raise VeSyncLoginError(msg)

        try:
            response_model = ResponseLoginModel.from_dict(resp_dict)
        except UnserializableDataError as exc:
            logger.debug('Error parsing auth response: %s', exc)
            raise VeSyncAPIResponseError('Error parsing authentication response') from exc
        except MissingField as exc:
            logger.debug('Error parsing auth response: %s', exc)
            raise VeSyncAPIResponseError('Error parsing authentication response') from exc

        result = response_model.result
        if not isinstance(result, RespGetTokenResultModel):
            raise VeSyncAPIResponseError('Invalid authentication response format')
        self._account_id = result.accountID
        return result.authorizeCode

    async def _exchange_authorization_code(
        self,
        auth_code: str,
        region_change_token: str | None = None,
    ) -> None:
        """Exchange authorization code for access token.

        Args:
            auth_code: Authorization code from first auth step
            region_change_token: Token for region change (retry scenario)

        Raises:
            VeSyncLoginError: If login fails
            VeSyncAPIResponseError: If API response is invalid
        """
        request_login = RequestLoginTokenModel(
            method='loginByAuthorizeCode4Vesync',
            authorizeCode=auth_code,
            bizToken=region_change_token,
            userCountryCode=self._country_code,
            regionChange='lastRegion' if region_change_token else None,
        )

        resp_dict, _ = await self.manager.async_call_api(
            '/user/api/accountManage/v1/loginByAuthorizeCode4Vesync',
            'post',
            json_object=request_login,
        )

        if resp_dict is None:
            raise VeSyncAPIResponseError('Error receiving response to login request')

        try:
            response_model = ResponseLoginModel.from_dict(resp_dict)

            if not isinstance(response_model.result, RespLoginTokenResultModel):
                raise VeSyncAPIResponseError('Invalid login response format')

            if response_model.code != 0:
                error_info = ErrorCodes.get_error_info(resp_dict.get('code'))

                # Handle cross region error by retrying with new region
                if error_info.error_type == ErrorTypes.CROSS_REGION:
                    result = response_model.result
                    self._country_code = result.countryCode
                    self._current_region = result.currentRegion
                    logger.debug(
                        'Cross-region error, retrying with country: %s',
                        self._country_code,
                    )
                    return await self._exchange_authorization_code(
                        auth_code, region_change_token=result.bizToken
                    )

                resp_message = resp_dict.get('msg')
                if resp_message is not None:
                    error_info.message = f'{error_info.message} ({resp_message})'

                msg = f'Login failed - {error_info.message}'

                # Raise appropriate exception based on error type
                if error_info.error_type == ErrorTypes.SERVER_ERROR:
                    raise VeSyncServerError(msg)
                raise VeSyncLoginError(msg)

            result = response_model.result
            self._token = result.token
            self._account_id = result.accountID
            self._country_code = result.countryCode

        except (MissingField, UnserializableDataError) as exc:
            logger.debug('Error parsing login response: %s', exc)
            raise VeSyncAPIResponseError('Error parsing login response') from exc

    def __repr__(self) -> str:
        """Return string representation of VeSyncAuth."""
        return (
            f'VeSyncAuth(username={self._username!r}, '
            f'country_code={self._country_code!r}, '
            f'authenticated={self.is_authenticated})'
        )
