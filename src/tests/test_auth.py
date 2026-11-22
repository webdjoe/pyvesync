"""Tests for login, re-login and stored credentials.

Covers `VeSyncAuth` (region mapping, credentials, the token file, the two-step
login, cross-region login, `reauthenticate()`) and how
`VeSync.async_call_api()` logs in again after the API rejects a token (#558).

Every test uses `TestApiFunc`, which patches `aiohttp.ClientSession`. Tests
that call the API script the HTTP responses with `respond()` and assert on the
requests that were sent, so the real `async_call_api()` runs in between.
"""

import asyncio
import copy
import logging
from pathlib import Path
from unittest.mock import patch

import orjson
import pytest
from yarl import URL

from pyvesync import VeSync
from pyvesync.const import (
    API_BASE_URL_EU,
    API_BASE_URL_US,
    MAX_API_REAUTH_RETRIES,
    REAUTH_WINDOW_SECONDS,
)
from pyvesync.models.vesync_models import (
    RequestGetTokenModel,
    RequestLoginTokenModel,
    ResponseDeviceDetailsModel,
)
from pyvesync.utils.errors import (
    VeSyncAPIResponseError,
    VeSyncInvalidCredentialsError,
    VeSyncLoginError,
    VeSyncServerError,
    VeSyncTokenError,
)

import call_json
from aiohttp_mocker import AiohttpMockSession
from base_test_cases import TestApiFunc
from defaults import TestDefaults

AUTH_PATH = '/globalPlatform/api/accountAuth/v1/authByPWDOrOTM'
LOGIN_PATH = '/user/api/accountManage/v1/loginByAuthorizeCode4Vesync'
DEVICES_PATH = '/cloud/v1/deviceManaged/devices'
DEVICE_PATH = '/cloud/v2/deviceManaged/bypassV2'
LEGACY_PATH = '/v1/device/sample-cid/detail'

US_HOST = URL(API_BASE_URL_US).host
EU_HOST = URL(API_BASE_URL_EU).host

OLD_TOKEN = TestDefaults.token
NEW_TOKEN = 'new_tk'

LOGIN_RESPONSES = call_json.LoginResponses
SUCCESS = call_json.response_body(0, 'Success')
TOKEN_ERROR = call_json.response_body(-11001000, 'Token expired')
# Not raised by raise_api_errors(), so it reaches the checks in auth.py.
UNKNOWN_ERROR_CODE = -1

# Request fields that differ on every run.
VARIABLE_FIELDS = {
    'traceId': TestDefaults.trace_id,
    'terminalId': TestDefaults.terminal_id,
    'appID': TestDefaults.app_id,
}


def response(body: dict | None) -> AiohttpMockSession:
    """HTTP 200 response with `body` as JSON, or an empty body for None."""
    return AiohttpMockSession(
        url=API_BASE_URL_US,
        method='post',
        status=200,
        response=b'' if body is None else orjson.dumps(body),
    )


def login_success(token: str = NEW_TOKEN) -> dict:
    """Token exchange response that issues `token`."""
    resp: dict = copy.deepcopy(LOGIN_RESPONSES.LOGIN_RESPONSE_SUCCESS)
    resp['result'] = {**resp['result'], 'token': token}
    return resp


def cross_region() -> dict:
    """Token exchange response telling a US login that the account is in EU."""
    resp: dict = copy.deepcopy(LOGIN_RESPONSES.LOGIN_RESPONSE_CROSS_REGION)
    resp['result'] = {**resp['result'], 'countryCode': 'DE', 'currentRegion': 'EU'}
    return resp


def exchange_error(code: int) -> dict:
    """Token exchange response with an error code."""
    return {
        'traceId': TestDefaults.trace_id,
        'code': code,
        'msg': 'Login failed',
        'result': {
            'accountID': TestDefaults.account_id,
            'acceptLanguage': 'en',
            'countryCode': 'US',
            'token': '',
        },
    }


def device_body(token: str = OLD_TOKEN) -> dict:
    """Body of a device request built while `token` was current."""
    return {
        'method': 'bypassV2',
        'token': token,
        'accountID': TestDefaults.account_id,
        'cid': 'sample-cid',
    }


def normalized(body: dict) -> dict:
    """Request body with the per-run fields replaced by test defaults."""
    return {key: VARIABLE_FIELDS.get(key, value) for key, value in body.items()}


class DelayedResponse(AiohttpMockSession):
    """Response that yields to the event loop first, so concurrent calls overlap."""

    async def __aenter__(self):
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        return await super().__aenter__()


class AuthTestCase(TestApiFunc):
    """`TestApiFunc` with helpers to script responses and read sent requests."""

    @property
    def session(self):
        """The mocked `ClientSession` instance."""
        return self.mock_api.return_value

    def respond(self, *bodies: dict | None) -> None:
        """Answer the next requests with `bodies`, in order."""
        self.session.request.side_effect = [response(body) for body in bodies]

    @property
    def requests(self) -> list[dict]:
        """Requests sent so far."""
        sent = []
        for call in self.session.request.call_args_list:
            url = URL(call.kwargs['url'])
            sent.append({
                'method': call.args[0],
                'host': url.host,
                'path': url.path,
                'json': call.kwargs['json'],
                'headers': call.kwargs['headers'],
            })
        return sent

    def paths(self) -> list[str]:
        """Paths of the requests sent so far."""
        return [request['path'] for request in self.requests]

    def problems(self) -> list[str]:
        """Messages logged at WARNING or above so far."""
        return [
            record.getMessage()
            for record in self.caplog.records
            if record.levelno >= logging.WARNING
        ]

    def relogin_failures(self) -> list[str]:
        """INFO messages about failed re-logins logged so far."""
        return [
            record.getMessage()
            for record in self.caplog.records
            if record.levelno == logging.INFO
            and record.getMessage().startswith('Re-login failed')
        ]


# ---------------------------------------------------------------------------
# Credentials and the token file
# ---------------------------------------------------------------------------


class TestCredentials(AuthTestCase):
    """Region mapping and in-memory credentials."""

    @pytest.mark.parametrize(
        ('country_code', 'stored_code', 'region'),
        [(None, 'US', 'US'), ('DE', 'DE', 'EU'), ('JP', 'JP', 'US'), ('ca', 'CA', 'US')],
    )
    def test_region_from_country_code(self, country_code, stored_code, region):
        """The country code is uppercased and mapped to the US or EU region."""
        kwargs = {} if country_code is None else {'country_code': country_code}
        manager = VeSync('user', 'pass', **kwargs)
        assert manager.auth.country_code == stored_code
        assert manager.auth.current_region == region

    def test_country_code_setter_uppercases(self):
        """Setting the country code uppercases it."""
        self.manager.auth.country_code = 'mx'
        assert self.manager.auth.country_code == 'MX'

    def test_new_manager_has_no_credentials(self):
        """Before login there is no token or account ID to read or output."""
        auth = VeSync('user', 'pass').auth
        assert auth.is_authenticated is False
        with pytest.raises(AttributeError, match='Token not set'):
            _ = auth.token
        with pytest.raises(AttributeError, match='Account ID not set'):
            _ = auth.account_id
        assert auth.output_credentials_dict() is None
        assert auth.output_credentials_json() is None

    def test_repr(self):
        """repr shows the username and whether the manager is authenticated."""
        text = repr(VeSync('user@test.com', 'pass').auth)
        assert 'user@test.com' in text
        assert 'authenticated=False' in text

    def test_set_and_clear_credentials(self):
        """set_credentials stores every field, clear_credentials removes them."""
        auth = self.manager.auth
        auth.set_credentials(
            token='tk_123', account_id='acct_456', country_code='de', region='EU'
        )
        assert auth.is_authenticated is True
        assert auth.token == 'tk_123'
        assert auth.account_id == 'acct_456'
        assert auth.country_code == 'DE'
        assert auth.current_region == 'EU'

        auth.clear_credentials()
        assert auth.is_authenticated is False

    def test_output_credentials(self):
        """Credentials are output as a dict and as JSON."""
        auth = self.manager.auth
        auth.set_credentials('tk_abc', 'acct_xyz', 'US', 'US')
        expected = {
            'token': 'tk_abc',
            'account_id': 'acct_xyz',
            'country_code': 'US',
            'current_region': 'US',
        }
        assert auth.output_credentials_dict() == expected
        json_str = auth.output_credentials_json()
        assert json_str is not None
        assert orjson.loads(json_str) == expected


class TestCredentialFile(AuthTestCase):
    """Saving credentials to and loading them from the token file."""

    @pytest.mark.parametrize('path_type', [str, Path])
    def test_save_and_load_round_trip(self, tmp_path, path_type):
        """Saved credentials load into a new manager and enable it."""
        self.manager.auth.set_credentials('tk_save', 'acct_save', 'CA', 'US')
        file_path = path_type(tmp_path / '.vesync_auth')
        self.run_in_loop(self.manager.auth.save_credentials_to_file, file_path)

        manager = VeSync('user', 'pass')
        assert self.run_in_loop(manager.auth.load_credentials_from_file, file_path)
        assert manager.auth.token == 'tk_save'
        assert manager.auth.account_id == 'acct_save'
        assert manager.auth.country_code == 'CA'
        assert manager.enabled is True

    @pytest.mark.parametrize(
        'contents',
        [None, 'not json', '{"token": "tk"}'],
        ids=['missing file', 'invalid json', 'missing keys'],
    )
    def test_load_bad_file_returns_false(self, tmp_path, contents):
        """A missing, unreadable or incomplete token file is not loaded."""
        file_path = tmp_path / '.vesync_auth'
        if contents is not None:
            file_path.write_text(contents, encoding='utf-8')
        auth = VeSync('user', 'pass').auth
        assert self.run_in_loop(auth.load_credentials_from_file, file_path) is False
        assert auth.is_authenticated is False

    def test_save_without_credentials_writes_nothing(self, tmp_path):
        """Nothing is written before login."""
        file_path = tmp_path / '.vesync_auth'
        self.run_in_loop(VeSync('user', 'pass').auth.save_credentials_to_file, file_path)
        assert not file_path.exists()

    def test_clear_credentials_deletes_the_file(self, tmp_path):
        """credentials_saved follows the file, and clearing deletes it."""
        auth = self.manager.auth
        assert auth.credentials_saved is False
        file_path = tmp_path / '.vesync_auth'
        self.run_in_loop(auth.save_credentials_to_file, file_path)
        auth._token_file_path = file_path
        assert auth.credentials_saved is True

        auth.clear_credentials()
        assert not file_path.exists()
        assert auth.credentials_saved is False


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class TestLogin(AuthTestCase):
    """The two-step login: authByPWDOrOTM, then loginByAuthorizeCode4Vesync."""

    def test_login_sends_both_requests_and_stores_credentials(self):
        """Login sends the expected requests and stores the issued token."""
        self.manager.auth.clear_credentials()
        self.manager.enabled = False
        self.respond(
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            LOGIN_RESPONSES.LOGIN_RESPONSE_SUCCESS,
        )

        assert self.run_in_loop(self.manager.login) is True

        auth_request, exchange_request = self.requests
        assert [(r['method'], r['host']) for r in self.requests] == [('post', US_HOST)] * 2
        assert self.paths() == [AUTH_PATH, LOGIN_PATH]
        assert normalized(auth_request['json']) == RequestGetTokenModel(
            email=TestDefaults.email,
            password=TestDefaults.password,
            method='authByPWDOrOTM',
            userCountryCode=TestDefaults.country_code,
            traceId=TestDefaults.trace_id,
            terminalId=TestDefaults.terminal_id,
            appID=TestDefaults.app_id,
        ).to_dict()
        assert normalized(exchange_request['json']) == RequestLoginTokenModel(
            authorizeCode=TestDefaults.authorization_code,
            method='loginByAuthorizeCode4Vesync',
            userCountryCode=TestDefaults.country_code,
            traceId=TestDefaults.trace_id,
            terminalId=TestDefaults.terminal_id,
        ).to_dict()
        assert self.manager.token == TestDefaults.token
        assert self.manager.account_id == TestDefaults.account_id
        assert self.manager.enabled is True

    def test_login_without_username_and_password_raises(self):
        """Login needs a username and password."""
        manager = VeSync('', '')
        with pytest.raises(VeSyncLoginError, match='No valid authentication'):
            self.run_in_loop(manager.auth.login)

    @pytest.mark.parametrize(
        ('responses', 'error', 'match'),
        [
            (
                [{'code': -11201000, 'msg': 'success'}],
                VeSyncInvalidCredentialsError,
                None,
            ),
            (
                [call_json.response_body(UNKNOWN_ERROR_CODE, 'Bad request')],
                VeSyncLoginError,
                'Authentication failed',
            ),
            ([None], VeSyncAPIResponseError, 'Error receiving response'),
            ([TOKEN_ERROR], VeSyncLoginError, None),
            (
                [
                    LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
                    exchange_error(UNKNOWN_ERROR_CODE),
                ],
                VeSyncLoginError,
                'Login failed',
            ),
            (
                [LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS, TOKEN_ERROR],
                VeSyncLoginError,
                None,
            ),
            (
                [LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS, exchange_error(-11102000)],
                VeSyncServerError,
                None,
            ),
            (
                [LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS, None],
                VeSyncAPIResponseError,
                'Error receiving response',
            ),
        ],
        ids=[
            'wrong password',
            'auth error code',
            'auth empty response',
            'auth token error',
            'exchange error code',
            'exchange token error',
            'exchange server error',
            'exchange empty response',
        ],
    )
    def test_login_error_raises_without_retrying(self, responses, error, match):
        """Each failed login step raises, and no request is retried.

        A token error on a login request must not start another login: the
        login requests carry no token. login() holds the re-login lock, so a
        re-login started from inside it would never finish.
        """
        self.respond(*responses)
        with pytest.raises(error, match=match):
            self.run_in_loop(self.manager.login)
        assert len(self.requests) == len(responses)

    def test_login_in_wrong_region_moves_to_the_account_region(self):
        """An EU account logging in as US repeats the exchange on the EU host."""
        self.respond(
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            cross_region(),
            login_success(),
        )

        assert self.run_in_loop(self.manager.login) is True

        assert self.paths() == [AUTH_PATH, LOGIN_PATH, LOGIN_PATH]
        assert [r['host'] for r in self.requests] == [US_HOST, US_HOST, EU_HOST]
        retry = self.requests[2]['json']
        assert retry['bizToken'] == TestDefaults.biz_token
        assert retry['regionChange'] == 'lastRegion'
        assert self.manager.auth.current_region == 'EU'
        assert self.manager.token == NEW_TOKEN


class TestReauthenticate(AuthTestCase):
    """VeSyncAuth.reauthenticate()."""

    def test_reauthenticate_keeps_credentials_until_login_succeeds(self):
        """Requests built while the login runs still find the old token."""
        auth = self.manager.auth
        responses = iter([
            response(LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS),
            response(login_success()),
        ])
        authenticated_during_login = []

        def serve(*args, **kwargs):
            authenticated_during_login.append(auth.is_authenticated)
            return next(responses)

        self.session.request.side_effect = serve

        assert self.run_in_loop(auth.reauthenticate) is True
        assert authenticated_during_login == [True, True]
        assert auth.token == NEW_TOKEN

    def test_reauthenticate_saves_the_new_token_to_the_file(self, tmp_path):
        """If credentials were saved, the new token is written to the file."""
        auth = self.manager.auth
        file_path = tmp_path / '.vesync_auth'
        self.run_in_loop(auth.save_credentials_to_file, file_path)
        auth._token_file_path = file_path
        self.respond(LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS, login_success())

        self.run_in_loop(auth.reauthenticate)

        data = orjson.loads(file_path.read_text(encoding='utf-8'))
        assert data['token'] == NEW_TOKEN

    def test_failed_reauthenticate_keeps_the_old_credentials(self):
        """If the login fails, the old token stays so requests can still be built."""
        self.respond(None)
        with pytest.raises(VeSyncAPIResponseError):
            self.run_in_loop(self.manager.auth.reauthenticate)
        assert self.manager.auth.token == OLD_TOKEN


# ---------------------------------------------------------------------------
# Re-login after a rejected token (async_call_api)
# ---------------------------------------------------------------------------


class TestRejectedToken(AuthTestCase):
    """async_call_api() logs in again once and resends with the new token."""

    def test_retry_sends_the_new_token(self):
        """A rejected device-list request is resent with the new token."""
        self.respond(
            TOKEN_ERROR,
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            login_success(),
            call_json.DeviceList.device_list_response(),
        )

        self.run_in_loop(self.manager.get_devices)

        assert self.paths() == [DEVICES_PATH, AUTH_PATH, LOGIN_PATH, DEVICES_PATH]
        first, retry = self.requests[0]['json'], self.requests[3]['json']
        assert first['token'] == OLD_TOKEN
        assert retry == {**first, 'token': NEW_TOKEN}

    def test_device_requests_use_the_token_from_each_relogin(self):
        """A real device builds each request with the current token.

        Over two token expiries, each expiry causes one login, and requests
        between them are sent once with the token that login issued.
        """
        device_config = call_json.DeviceList.device_list_item(
            call_json.ALL_DEVICE_MAP_DICT['Core300S']
        )
        self.manager.devices.add_device_from_model(
            ResponseDeviceDetailsModel.from_dict(device_config), self.manager
        )
        purifier = self.manager.devices.air_purifiers[0]
        self.respond(
            TOKEN_ERROR,  # first expiry
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            login_success('tk_1'),
            SUCCESS,
            SUCCESS,  # sent once with tk_1
            TOKEN_ERROR,  # second expiry
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            login_success('tk_2'),
            SUCCESS,
        )

        for _ in range(3):
            self.run_in_loop(purifier.call_bypassv2_api, 'getPurifierStatus')

        device_tokens = [
            r['json']['token'] for r in self.requests if r['path'] == DEVICE_PATH
        ]
        assert device_tokens == [OLD_TOKEN, 'tk_1', 'tk_1', 'tk_1', 'tk_2']
        assert self.paths().count(LOGIN_PATH) == 2
        assert self.mock_api.call_count == 1  # one ClientSession for every request

    def test_retry_keeps_method_and_headers(self):
        """A rejected GET is resent as a GET with its headers and the new `tk`."""
        headers = {
            'accept-language': 'en',
            'accountId': TestDefaults.account_id,
            'tk': OLD_TOKEN,
            'tz': 'America/New_York',
        }
        self.respond(
            TOKEN_ERROR,
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            login_success(),
            SUCCESS,
        )

        resp, _ = self.run_in_loop(
            self.manager.async_call_api, LEGACY_PATH, 'get', headers=headers
        )

        assert resp == SUCCESS
        retry = self.requests[3]
        assert retry['method'] == 'get'
        assert retry['headers'] == {**headers, 'tk': NEW_TOKEN}
        assert headers['tk'] == OLD_TOKEN  # the caller's dict is not changed

    def test_rejected_retry_raises_without_another_login(self):
        """If the retry is rejected too, the call raises instead of looping."""
        self.respond(
            TOKEN_ERROR,
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            login_success(),
            TOKEN_ERROR,
        )

        with pytest.raises(VeSyncTokenError):
            self.run_in_loop(
                self.manager.async_call_api, DEVICE_PATH, 'post', device_body()
            )

        assert self.paths() == [DEVICE_PATH, AUTH_PATH, LOGIN_PATH, DEVICE_PATH]
        assert len(self.problems()) == 1

    def test_rejected_retries_after_one_login_log_one_line(self):
        """Retries rejected after the same login are logged once together."""

        def serve(method, url, json=None, headers=None, raise_for_status=False):
            path = URL(url).path
            if path == AUTH_PATH:
                body = LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS
            elif path == LOGIN_PATH:
                body = login_success()
            else:
                body = TOKEN_ERROR
            return DelayedResponse(
                url=url, method=method, status=200, response=orjson.dumps(body)
            )

        self.session.request.side_effect = serve

        async def call_all():
            return await asyncio.gather(
                *(
                    self.manager.async_call_api(DEVICE_PATH, 'post', device_body())
                    for _ in range(3)
                ),
                return_exceptions=True,
            )

        results = self.run_in_loop(call_all)

        assert all(isinstance(r, VeSyncTokenError) for r in results)
        assert self.paths().count(LOGIN_PATH) == 1
        assert len(self.problems()) == 1
        assert 'new token' in self.problems()[0]

    def test_rejected_retry_after_explicit_login_is_logged(self):
        """A rejected retry with the token from login() gets its own line.

        The request was built before login(), so it retries with the new token
        without another re-login.
        """
        self.respond(
            TOKEN_ERROR,
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            login_success(),
            TOKEN_ERROR,  # retry rejected: logged
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,  # explicit login()
            login_success('tk_login'),
            TOKEN_ERROR,  # stale request
            TOKEN_ERROR,  # retry with tk_login rejected: logged again
        )

        def call():
            return self.manager.async_call_api(DEVICE_PATH, 'post', device_body())

        with pytest.raises(VeSyncTokenError):
            self.run_in_loop(call)
        assert self.run_in_loop(self.manager.login) is True
        with pytest.raises(VeSyncTokenError):
            self.run_in_loop(call)

        assert self.requests[-1]['json']['token'] == 'tk_login'
        assert self.paths().count(LOGIN_PATH) == 2
        assert len(self.problems()) == 2

    def test_relogins_are_capped_per_window(self):
        """After the cap, calls raise without logging in, until the window passes.

        Reaching the cap is logged once, however many calls it fails.
        """
        rejected_relogin = [
            TOKEN_ERROR,
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            login_success(),
            TOKEN_ERROR,
        ]
        self.respond(
            *rejected_relogin * MAX_API_REAUTH_RETRIES,
            TOKEN_ERROR,  # cap reached: no login
            TOKEN_ERROR,  # still capped: no login, no second log line
            TOKEN_ERROR,  # window passed: login is allowed again
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            login_success('final_tk'),
            SUCCESS,
        )
        now = 1000.0

        def call():
            body = device_body(self.manager.auth.token)
            return self.manager.async_call_api(DEVICE_PATH, 'post', body)

        with patch('pyvesync.vesync.monotonic', side_effect=lambda: now):
            for _ in range(MAX_API_REAUTH_RETRIES + 2):
                with pytest.raises(VeSyncTokenError):
                    self.run_in_loop(call)
            assert self.paths().count(LOGIN_PATH) == MAX_API_REAUTH_RETRIES
            assert self.caplog.text.count('Re-login limit reached') == 1

            now += REAUTH_WINDOW_SECONDS + 1
            resp, _ = self.run_in_loop(call)

        assert resp == SUCCESS
        assert self.paths().count(LOGIN_PATH) == MAX_API_REAUTH_RETRIES + 1

    @pytest.mark.parametrize(
        'issued_token', [NEW_TOKEN, OLD_TOKEN], ids=['new token', 'same token']
    )
    def test_concurrent_rejections_share_one_login(self, issued_token):
        """Requests rejected at the same time cause a single login.

        The waiting requests retry even if the login returns the token they were
        rejected with.
        """
        logged_in = False

        def serve(method, url, json=None, headers=None, raise_for_status=False):
            nonlocal logged_in
            path = URL(url).path
            if path == AUTH_PATH:
                body = LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS
            elif path == LOGIN_PATH:
                logged_in = True
                body = login_success(issued_token)
            elif logged_in and json['token'] == issued_token:
                body = SUCCESS
            else:
                body = TOKEN_ERROR
            return DelayedResponse(
                url=url, method=method, status=200, response=orjson.dumps(body)
            )

        self.session.request.side_effect = serve

        async def call_all():
            return await asyncio.gather(*(
                self.manager.async_call_api(DEVICE_PATH, 'post', device_body())
                for _ in range(5)
            ))

        results = self.run_in_loop(call_all)

        assert [resp for resp, _ in results] == [SUCCESS] * 5
        assert self.paths().count(LOGIN_PATH) == 1
        assert self.manager.enabled is True

    def test_concurrent_rejections_share_one_failed_login(self):
        """If the shared login fails, the waiting requests don't try their own.

        Every request raises VeSyncTokenError; the one that ran the login has
        the login error as its cause. The failure is logged once.
        """
        self.caplog.set_level(logging.INFO, logger='pyvesync')

        def serve(method, url, json=None, headers=None, raise_for_status=False):
            # Every token is rejected, and the auth step returns no response.
            body = None if URL(url).path == AUTH_PATH else TOKEN_ERROR
            return DelayedResponse(
                url=url,
                method=method,
                status=200,
                response=b'' if body is None else orjson.dumps(body),
            )

        self.session.request.side_effect = serve

        async def call_all():
            return await asyncio.gather(
                *(
                    self.manager.async_call_api(DEVICE_PATH, 'post', device_body())
                    for _ in range(5)
                ),
                return_exceptions=True,
            )

        results = self.run_in_loop(call_all)

        assert self.paths().count(AUTH_PATH) == 1
        assert all(isinstance(r, VeSyncTokenError) for r in results)
        causes = [r.__cause__ for r in results if r.__cause__ is not None]
        assert len(causes) == 1
        assert isinstance(causes[0], VeSyncAPIResponseError)
        assert len(self.relogin_failures()) == 1
        assert self.problems() == []

    @pytest.mark.parametrize(
        'code', [-11201000, -11202000], ids=['wrong password', 'unknown account']
    )
    def test_invalid_credentials_stop_relogin_until_login(self, code):
        """A rejected username or password stops automatic re-login.

        Later rejected calls raise without logging in, until an explicit
        login() succeeds.
        """
        self.respond(
            TOKEN_ERROR,
            call_json.response_body(code, 'Invalid credentials'),
            TOKEN_ERROR,  # stopped: no login
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,  # explicit login()
            login_success(),
            TOKEN_ERROR,  # re-login works again
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            login_success('tk_after'),
            SUCCESS,
        )

        def call():
            body = device_body(self.manager.token)
            return self.manager.async_call_api(DEVICE_PATH, 'post', body)

        for _ in range(2):
            with pytest.raises(VeSyncInvalidCredentialsError):
                self.run_in_loop(call)
        assert self.paths().count(AUTH_PATH) == 1
        assert self.manager.enabled is False

        assert self.run_in_loop(self.manager.login) is True
        resp, _ = self.run_in_loop(call)

        assert resp == SUCCESS
        assert self.paths().count(AUTH_PATH) == 3
        assert self.manager.enabled is True

    def test_login_and_relogin_do_not_overlap(self):
        """A request rejected during login() retries with its token.

        Without that, the re-login could finish after login() and stop
        re-login, or disable the manager, although login() succeeded.
        """
        auth_requests = 0

        def serve(method, url, json=None, headers=None, raise_for_status=False):
            nonlocal auth_requests
            path = URL(url).path
            if path == AUTH_PATH:
                auth_requests += 1
                body = (
                    LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS
                    if auth_requests == 1
                    else call_json.response_body(-11201000, 'Invalid credentials')
                )
            elif path == LOGIN_PATH:
                body = login_success()
            else:
                body = SUCCESS if json['token'] == NEW_TOKEN else TOKEN_ERROR
            return DelayedResponse(
                url=url, method=method, status=200, response=orjson.dumps(body)
            )

        self.session.request.side_effect = serve

        async def call_and_login():
            return await asyncio.gather(
                self.manager.async_call_api(DEVICE_PATH, 'post', device_body()),
                self.manager.login(),
            )

        (resp, _), logged_in = self.run_in_loop(call_and_login)

        assert logged_in is True
        assert resp == SUCCESS
        assert auth_requests == 1
        assert self.manager.enabled is True
        assert self.manager.token == NEW_TOKEN

    def test_failed_relogin_for_other_reasons_is_retried(self):
        """A server error during re-login doesn't stop the next call's re-login.

        The next request is built from the manager's token, as a device does,
        so the old token must still be there after the failed login.
        """
        self.respond(
            TOKEN_ERROR,
            call_json.response_body(-11102000, 'Server error'),
            TOKEN_ERROR,
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            login_success(),
            SUCCESS,
        )

        def call():
            body = device_body(self.manager.token)
            return self.manager.async_call_api(DEVICE_PATH, 'post', body)

        with pytest.raises(VeSyncTokenError) as excinfo:
            self.run_in_loop(call)
        assert isinstance(excinfo.value.__cause__, VeSyncServerError)
        assert self.manager.enabled is True
        resp, _ = self.run_in_loop(call)

        assert resp == SUCCESS
        assert self.paths().count(AUTH_PATH) == 2
        assert self.manager.enabled is True

    @pytest.mark.parametrize(
        ('code', 'raises'),
        [(-11201000, True), (-11102000, False)],
        ids=['wrong password', 'server error'],
    )
    def test_update_all_devices_raises_only_for_rejected_credentials(
        self, code, raises
    ):
        """Rejected credentials reach the caller of update_all_devices().

        Other device errors are swallowed, as before. Two devices are rejected
        at once and share one login, which is logged in a single line.
        """
        self.caplog.set_level(logging.INFO, logger='pyvesync')
        for model in ('Core300S', 'Core400S'):
            device_config = call_json.DeviceList.device_list_item(
                call_json.ALL_DEVICE_MAP_DICT[model]
            )
            self.manager.devices.add_device_from_model(
                ResponseDeviceDetailsModel.from_dict(device_config), self.manager
            )

        def serve(method, url, json=None, headers=None, raise_for_status=False):
            if URL(url).path == AUTH_PATH:
                body = call_json.response_body(code, 'Login failed')
            else:
                body = TOKEN_ERROR
            return DelayedResponse(
                url=url, method=method, status=200, response=orjson.dumps(body)
            )

        self.session.request.side_effect = serve

        if raises:
            with pytest.raises(VeSyncInvalidCredentialsError):
                self.run_in_loop(self.manager.update_all_devices)
        else:
            self.run_in_loop(self.manager.update_all_devices)
        assert self.paths().count(AUTH_PATH) == 1
        if raises:
            assert len(self.problems()) == 1
            assert self.problems()[0].startswith('Username or password rejected')
        else:
            # A failed re-login is INFO; only the final failures are errors.
            assert len(self.relogin_failures()) == 1
            assert self.problems() == []

    def test_credentials_code_in_device_response_is_not_raised(self):
        """An auth code in a device response doesn't stop re-login or raise.

        Only a rejected re-login reaches the caller of update_all_devices(), so
        an application doesn't ask for new credentials because of one device.
        """
        device_config = call_json.DeviceList.device_list_item(
            call_json.ALL_DEVICE_MAP_DICT['Core300S']
        )
        self.manager.devices.add_device_from_model(
            ResponseDeviceDetailsModel.from_dict(device_config), self.manager
        )
        self.respond(call_json.response_body(-11201000, 'Invalid credentials'))

        self.run_in_loop(self.manager.update_all_devices)

        assert self.paths() == [DEVICE_PATH]
        assert self.manager.enabled is True
        assert len(self.problems()) == 1
        assert self.problems()[0].startswith('Error updating device')

    def test_update_raises_after_relogin_stopped(self):
        """update() raises instead of returning while re-login is stopped."""
        self.respond(
            TOKEN_ERROR,
            call_json.response_body(-11201000, 'Invalid credentials'),
        )
        with pytest.raises(VeSyncInvalidCredentialsError):
            self.run_in_loop(
                self.manager.async_call_api, DEVICE_PATH, 'post', device_body()
            )
        sent = len(self.requests)

        logged = len(self.problems())
        with pytest.raises(VeSyncInvalidCredentialsError, match='login\\(\\)'):
            self.run_in_loop(self.manager.update)
        assert len(self.requests) == sent
        assert len(self.problems()) == logged == 1

    def test_relogin_across_regions_retries_on_the_new_host(self):
        """If the login moves the account to EU, the retry goes to the EU host."""
        self.respond(
            TOKEN_ERROR,
            LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS,
            cross_region(),
            login_success(),
            SUCCESS,
        )

        resp, _ = self.run_in_loop(
            self.manager.async_call_api, DEVICE_PATH, 'post', device_body()
        )

        assert resp == SUCCESS
        assert [(r['host'], r['path']) for r in self.requests] == [
            (US_HOST, DEVICE_PATH),
            (US_HOST, AUTH_PATH),
            (US_HOST, LOGIN_PATH),
            (EU_HOST, LOGIN_PATH),
            (EU_HOST, DEVICE_PATH),
        ]
        assert self.requests[4]['json']['token'] == NEW_TOKEN
        assert self.manager.auth.current_region == 'EU'
