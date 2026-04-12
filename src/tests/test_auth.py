"""Tests for VeSyncAuth authentication module.

Tests cover:
- Initialization and properties (region mapping, credentials state)
- Credential management (set, clear, output)
- File-based credential persistence (save, load)
- Login flow (get_authorization_code -> exchange for token)
- Re-authentication
- Error handling (bad responses, missing fields, cross-region)
"""

import logging
from pathlib import Path

import orjson
import pytest

from pyvesync import VeSync
from pyvesync.utils.errors import (
    VeSyncAPIResponseError,
    VeSyncLoginError,
    VeSyncServerError,
)

from base_test_cases import TestBase
from defaults import TestDefaults
import call_json

logger = logging.getLogger(__name__)

LOGIN_RESPONSES = call_json.LoginResponses


# ---------------------------------------------------------------------------
# Initialization & Properties
# ---------------------------------------------------------------------------


class TestAuthInit(TestBase):
    """Test VeSyncAuth initialization and property accessors."""

    def test_default_region_us(self):
        """US country code maps to US region."""
        assert self.manager.auth._country_code == 'US'
        assert self.manager.auth.current_region == 'US'

    def test_region_eu(self):
        """Non-US/CA/MX/JP country codes map to EU region."""
        manager = VeSync('user', 'pass', country_code='DE')
        assert manager.auth.current_region == 'EU'

    def test_region_jp(self):
        """JP country code maps to US region."""
        manager = VeSync('user', 'pass', country_code='JP')
        assert manager.auth.current_region == 'US'

    def test_country_code_uppercased(self):
        """Country code is stored uppercased."""
        manager = VeSync('user', 'pass', country_code='ca')
        assert manager.auth.country_code == 'CA'

    def test_country_code_setter_uppercases(self):
        """Country code setter uppercases value."""
        self.manager.auth.country_code = 'mx'
        assert self.manager.auth.country_code == 'MX'

    def test_not_authenticated_initially(self):
        """Auth is not authenticated before login."""
        manager = VeSync('user', 'pass')
        assert manager.auth.is_authenticated is False

    def test_token_raises_before_login(self):
        """Accessing token before login raises AttributeError."""
        manager = VeSync('user', 'pass')
        with pytest.raises(AttributeError, match='Token not set'):
            _ = manager.auth.token

    def test_account_id_raises_before_login(self):
        """Accessing account_id before login raises AttributeError."""
        manager = VeSync('user', 'pass')
        with pytest.raises(AttributeError, match='Account ID not set'):
            _ = manager.auth.account_id

    def test_repr(self):
        """Test __repr__ output."""
        manager = VeSync('user@test.com', 'pass')
        r = repr(manager.auth)
        assert 'user@test.com' in r
        assert 'authenticated=False' in r


# ---------------------------------------------------------------------------
# Credential Management
# ---------------------------------------------------------------------------


class TestCredentialManagement(TestBase):
    """Test set_credentials, clear_credentials, and output methods."""

    def test_set_credentials(self):
        """set_credentials sets all fields and marks authenticated."""
        auth = self.manager.auth
        auth.set_credentials(
            token='tk_123',
            account_id='acct_456',
            country_code='de',
            region='EU',
        )
        assert auth.is_authenticated is True
        assert auth.token == 'tk_123'
        assert auth.account_id == 'acct_456'
        assert auth.country_code == 'DE'
        assert auth.current_region == 'EU'

    def test_clear_credentials(self):
        """clear_credentials resets token and account_id."""
        auth = self.manager.auth
        auth.set_credentials('tk', 'acct', 'US', 'US')
        assert auth.is_authenticated is True
        auth.clear_credentials()
        assert auth.is_authenticated is False

    def test_output_credentials_dict_authenticated(self):
        """output_credentials_dict returns dict when authenticated."""
        auth = self.manager.auth
        auth.set_credentials('tk_abc', 'acct_xyz', 'US', 'US')
        result = auth.output_credentials_dict()
        assert result == {
            'token': 'tk_abc',
            'account_id': 'acct_xyz',
            'country_code': 'US',
            'current_region': 'US',
        }

    def test_output_credentials_dict_not_authenticated(self):
        """output_credentials_dict returns None when not authenticated."""
        manager = VeSync('user', 'pass')
        assert manager.auth.output_credentials_dict() is None

    def test_output_credentials_json_authenticated(self):
        """output_credentials_json returns JSON string when authenticated."""
        auth = self.manager.auth
        auth.set_credentials('tk', 'acct', 'US', 'US')
        json_str = auth.output_credentials_json()
        assert json_str is not None
        parsed = orjson.loads(json_str)
        assert parsed['token'] == 'tk'
        assert parsed['account_id'] == 'acct'

    def test_output_credentials_json_not_authenticated(self):
        """output_credentials_json returns None when not authenticated."""
        manager = VeSync('user', 'pass')
        assert manager.auth.output_credentials_json() is None


# ---------------------------------------------------------------------------
# File-based Credential Persistence
# ---------------------------------------------------------------------------


class TestCredentialFile(TestBase):
    """Test save/load credentials to/from file."""

    def test_save_and_load_credentials(self, tmp_path):
        """Save credentials to file and load them back."""
        auth = self.manager.auth
        auth.set_credentials('tk_save', 'acct_save', 'US', 'US')

        file_path = tmp_path / '.vesync_auth'
        self.run_in_loop(auth.save_credentials_to_file, file_path)
        assert file_path.exists()

        # Load into a fresh manager
        manager2 = VeSync('user', 'pass')
        success = self.loop.run_until_complete(
            manager2.auth.load_credentials_from_file(file_path)
        )
        assert success is True
        assert manager2.auth.token == 'tk_save'
        assert manager2.auth.account_id == 'acct_save'
        assert manager2.auth.country_code == 'US'
        assert manager2.enabled is True

    def test_load_nonexistent_file(self, tmp_path):
        """Loading from a nonexistent file returns False."""
        auth = self.manager.auth
        result = self.loop.run_until_complete(
            auth.load_credentials_from_file(tmp_path / 'missing_file')
        )
        assert result is False

    def test_load_invalid_json(self, tmp_path):
        """Loading a file with invalid JSON returns False."""
        file_path = tmp_path / '.vesync_auth'
        file_path.write_text('not json', encoding='utf-8')

        auth = self.manager.auth
        result = self.loop.run_until_complete(
            auth.load_credentials_from_file(file_path)
        )
        assert result is False

    def test_load_missing_keys(self, tmp_path):
        """Loading a file with missing keys returns False."""
        file_path = tmp_path / '.vesync_auth'
        file_path.write_text(
            orjson.dumps({'token': 'tk'}).decode('utf-8'),
            encoding='utf-8',
        )
        auth = self.manager.auth
        result = self.loop.run_until_complete(
            auth.load_credentials_from_file(file_path)
        )
        assert result is False

    def test_save_not_authenticated(self, tmp_path):
        """Saving credentials when not authenticated does nothing."""
        manager = VeSync('user', 'pass')
        file_path = tmp_path / '.vesync_auth'
        self.loop.run_until_complete(
            manager.auth.save_credentials_to_file(file_path)
        )
        assert not file_path.exists()

    def test_clear_credentials_deletes_file(self, tmp_path):
        """clear_credentials deletes the token file."""
        auth = self.manager.auth
        auth.set_credentials('tk', 'acct', 'US', 'US')

        file_path = tmp_path / '.vesync_auth'
        self.loop.run_until_complete(auth.save_credentials_to_file(file_path))
        assert file_path.exists()

        # Set the token file path (load sets this, but we saved directly)
        auth._token_file_path = file_path
        auth.clear_credentials()
        assert not file_path.exists()

    def test_credentials_saved_property(self, tmp_path):
        """credentials_saved reflects whether a token file exists."""
        auth = self.manager.auth
        assert auth.credentials_saved is False

        auth.set_credentials('tk', 'acct', 'US', 'US')
        file_path = tmp_path / '.vesync_auth'
        self.loop.run_until_complete(auth.save_credentials_to_file(file_path))
        auth._token_file_path = file_path
        assert auth.credentials_saved is True

    def test_load_with_path_object(self, tmp_path):
        """Loading credentials accepts a Path object."""
        auth = self.manager.auth
        auth.set_credentials('tk_path', 'acct_path', 'CA', 'US')

        file_path = tmp_path / '.vesync_auth'
        self.loop.run_until_complete(auth.save_credentials_to_file(file_path))

        manager2 = VeSync('user', 'pass')
        success = self.loop.run_until_complete(
            manager2.auth.load_credentials_from_file(Path(file_path))
        )
        assert success is True
        assert manager2.auth.token == 'tk_path'


# ---------------------------------------------------------------------------
# Login Flow
# ---------------------------------------------------------------------------


class TestLoginFlow(TestBase):
    """Test login flow with mocked async_call_api."""

    def test_login_success(self):
        """Successful two-step login sets token and account_id."""
        self.mock_api.side_effect = [
            (LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS, 200),
            (LOGIN_RESPONSES.LOGIN_RESPONSE_SUCCESS, 200),
        ]
        result = self.run_in_loop(self.manager.auth.login)
        assert result is True
        assert self.manager.auth.is_authenticated is True
        assert self.manager.auth.token == TestDefaults.token
        assert self.manager.auth.account_id == TestDefaults.account_id

    def test_login_no_credentials(self):
        """Login without username/password raises VeSyncLoginError."""
        manager = VeSync('', '')
        manager.auth._token = None
        manager.auth._account_id = None
        with pytest.raises(VeSyncLoginError, match='No valid authentication'):
            self.loop.run_until_complete(manager.auth.login())

    def test_login_auth_error_code(self):
        """Non-zero code in auth response raises VeSyncLoginError."""
        error_resp = {
            'traceId': TestDefaults.trace_id,
            'code': -11201000,
            'msg': 'Invalid password',
            'result': None,
        }
        self.mock_api.return_value = (error_resp, 200)
        with pytest.raises(VeSyncLoginError, match='Authentication failed'):
            self.run_in_loop(self.manager.auth.login)

    def test_login_none_response(self):
        """None API response raises VeSyncAPIResponseError."""
        self.mock_api.return_value = (None, 200)
        with pytest.raises(
            VeSyncAPIResponseError, match='Error receiving response'
        ):
            self.run_in_loop(self.manager.auth.login)

    def test_login_exchange_error_code(self):
        """Non-zero code in exchange response raises VeSyncLoginError."""
        login_error_resp = {
            'traceId': TestDefaults.trace_id,
            'code': -11201000,
            'msg': 'Login failed',
            'result': {
                'accountID': TestDefaults.account_id,
                'acceptLanguage': 'en',
                'countryCode': 'US',
                'token': '',
            },
        }
        self.mock_api.side_effect = [
            (LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS, 200),
            (login_error_resp, 200),
        ]
        with pytest.raises(VeSyncLoginError, match='Login failed'):
            self.run_in_loop(self.manager.auth.login)

    def test_login_exchange_none_response(self):
        """None response in exchange step raises VeSyncAPIResponseError."""
        self.mock_api.side_effect = [
            (LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS, 200),
            (None, 200),
        ]
        with pytest.raises(
            VeSyncAPIResponseError, match='Error receiving response'
        ):
            self.run_in_loop(self.manager.auth.login)

    def test_login_cross_region(self):
        """Cross-region error triggers retry with new region."""
        cross_region_resp = LOGIN_RESPONSES.LOGIN_RESPONSE_CROSS_REGION
        success_resp = LOGIN_RESPONSES.LOGIN_RESPONSE_SUCCESS
        self.mock_api.side_effect = [
            (LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS, 200),
            (cross_region_resp, 200),
            (success_resp, 200),
        ]
        result = self.run_in_loop(self.manager.auth.login)
        assert result is True
        assert self.mock_api.call_count == 3

    def test_login_server_error_in_exchange(self):
        """Server error code in exchange raises VeSyncServerError."""
        server_error_resp = {
            'traceId': TestDefaults.trace_id,
            'code': -11102000,
            'msg': 'Server error',
            'result': {
                'accountID': TestDefaults.account_id,
                'acceptLanguage': 'en',
                'countryCode': 'US',
                'token': '',
            },
        }
        self.mock_api.side_effect = [
            (LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS, 200),
            (server_error_resp, 200),
        ]
        with pytest.raises(VeSyncServerError):
            self.run_in_loop(self.manager.auth.login)


# ---------------------------------------------------------------------------
# Re-authentication
# ---------------------------------------------------------------------------


class TestReauthentication(TestBase):
    """Test reauthenticate method."""

    def test_reauthenticate_success(self):
        """Reauthenticate clears and re-establishes credentials."""
        auth = self.manager.auth
        auth.set_credentials('old_tk', 'old_acct', 'US', 'US')
        assert auth.is_authenticated is True

        self.mock_api.side_effect = [
            (LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS, 200),
            (LOGIN_RESPONSES.LOGIN_RESPONSE_SUCCESS, 200),
        ]
        result = self.run_in_loop(auth.reauthenticate)
        assert result is True
        assert auth.token == TestDefaults.token

    def test_reauthenticate_saves_to_file(self, tmp_path):
        """Reauthenticate re-saves credentials when file existed."""
        auth = self.manager.auth
        auth.set_credentials('tk', 'acct', 'US', 'US')
        file_path = tmp_path / '.vesync_auth'
        self.loop.run_until_complete(auth.save_credentials_to_file(file_path))
        auth._token_file_path = file_path

        self.mock_api.side_effect = [
            (LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS, 200),
            (LOGIN_RESPONSES.LOGIN_RESPONSE_SUCCESS, 200),
        ]
        self.run_in_loop(auth.reauthenticate)

        # File should be re-created with new credentials
        assert file_path.exists()
        data = orjson.loads(file_path.read_text(encoding='utf-8'))
        assert data['token'] == TestDefaults.token

    def test_reauthenticate_login_failure_raises(self):
        """Reauthenticate propagates login errors."""
        auth = self.manager.auth
        auth.set_credentials('tk', 'acct', 'US', 'US')

        self.mock_api.return_value = (None, 200)
        with pytest.raises(VeSyncAPIResponseError):
            self.run_in_loop(auth.reauthenticate)
        assert auth.is_authenticated is False
