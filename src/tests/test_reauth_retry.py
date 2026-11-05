"""Tests for the re-login and retry that follows a rejected token.

A rejected token must cause exactly one re-login and one retry, and the retry
must carry the new credentials and the original headers.
"""

import asyncio

import orjson
import pytest

from pyvesync import VeSync
from pyvesync.utils.errors import VeSyncTokenError

TOKEN_EXPIRED = {'code': -11001000, 'msg': 'token expired'}
SUCCESS = {'code': 0, 'result': {}}
ENDPOINT = '/cloud/v2/deviceManaged/bypassV2'
OLD_TOKEN = 'old-token'
NEW_TOKEN = 'new-token'
NEW_ACCOUNT = 'new-account'


class FakeResponse:
    """Minimal aiohttp response for async_call_api."""

    status = 200

    def __init__(self, body: dict) -> None:
        self._body = orjson.dumps(body)

    async def read(self) -> bytes:
        return self._body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False


class FakeSession:
    """Session that rejects any request still carrying the old token."""

    def __init__(self, *, always_reject: bool = False) -> None:
        self.always_reject = always_reject
        self.requests: list[dict] = []

    def request(self, method, url, json=None, headers=None, **kwargs):
        del method, url, kwargs
        self.requests.append({'json': json, 'headers': headers})
        sent = {(json or {}).get('token'), (headers or {}).get('tk')}
        if self.always_reject or OLD_TOKEN in sent:
            return FakeResponse(TOKEN_EXPIRED)
        return FakeResponse(SUCCESS)

    async def close(self) -> None:
        return None


def make_manager(session: FakeSession):
    """Return a manager with old credentials, a re-login log and a fake re-login."""
    manager = VeSync('user@example.com', 'password', session=session)
    manager.set_credentials(OLD_TOKEN, 'old-account', 'US', 'US')
    logins: list[int] = []

    async def fake_reauthenticate(self) -> bool:
        logins.append(1)
        self.set_credentials(NEW_TOKEN, NEW_ACCOUNT, 'US', 'US')
        return True

    return manager, logins, fake_reauthenticate


@pytest.fixture(name='patch_reauth')
def patch_reauth_fixture(monkeypatch):
    """Replace VeSyncAuth.reauthenticate for the duration of a test."""

    def apply(manager: VeSync, replacement) -> None:
        monkeypatch.setattr(type(manager.auth), 'reauthenticate', replacement)

    return apply


def test_rejected_token_retries_once_with_new_credentials(patch_reauth):
    session = FakeSession()
    manager, logins, fake_reauthenticate = make_manager(session)
    patch_reauth(manager, fake_reauthenticate)
    body = {'token': manager.token, 'accountID': manager.account_id, 'method': 'bypassV2'}
    headers = {'User-Agent': 'okhttp/3.12.1'}

    response, status = asyncio.run(
        manager.async_call_api(ENDPOINT, 'post', json_object=body, headers=headers)
    )

    assert (response, status) == (SUCCESS, 200)
    assert len(logins) == 1
    assert len(session.requests) == 2
    retry = session.requests[1]
    assert retry['json']['token'] == NEW_TOKEN
    assert retry['json']['accountID'] == NEW_ACCOUNT
    assert retry['json']['method'] == 'bypassV2'
    assert retry['headers'] == headers
    # The caller's dict is left as it was built.
    assert body['token'] == OLD_TOKEN


def test_credentials_in_headers_are_refreshed(patch_reauth):
    session = FakeSession()
    manager, logins, fake_reauthenticate = make_manager(session)
    patch_reauth(manager, fake_reauthenticate)
    headers = {'tk': manager.token, 'accountId': manager.account_id, 'tz': 'UTC'}

    response, _ = asyncio.run(
        manager.async_call_api(ENDPOINT, 'post', json_object={}, headers=headers)
    )

    assert response == SUCCESS
    assert len(logins) == 1
    assert session.requests[1]['headers'] == {
        'tk': NEW_TOKEN,
        'accountId': NEW_ACCOUNT,
        'tz': 'UTC',
    }


def test_token_rejected_after_retry_raises_without_another_login(patch_reauth):
    session = FakeSession(always_reject=True)
    manager, logins, fake_reauthenticate = make_manager(session)
    patch_reauth(manager, fake_reauthenticate)
    body = {'token': manager.token, 'accountID': manager.account_id}

    with pytest.raises(VeSyncTokenError):
        asyncio.run(manager.async_call_api(ENDPOINT, 'post', json_object=body))

    assert len(logins) == 1
    assert len(session.requests) == 2
