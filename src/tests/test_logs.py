"""Tests for redaction in LibraryLogger."""

import logging

import orjson
import pytest

from pyvesync.utils.logs import LibraryLogger

from base_test_cases import TestBase
from defaults import TestDefaults
import call_json

REDACTED = '##_REDACTED_##'

SENSITIVE_BODY = {
    'email': 'user@example.com',
    'token': 'sample_tk',
    'accountID': 'sample_id',
    'cid': 'sample_cid',
    'uuid': 'sample_uuid',
    'deviceId': 'sample_device_id',
    'terminalId': 'sample_terminal_id',
    'nickName': 'sample_nickname',
}


@pytest.fixture
def redact_on():
    """Enable redaction for one test and restore the previous setting."""
    previous = LibraryLogger.shouldredact
    LibraryLogger.shouldredact = True
    yield
    LibraryLogger.shouldredact = previous


@pytest.fixture
def redact_off():
    """Disable redaction for one test and restore the previous setting."""
    previous = LibraryLogger.shouldredact
    LibraryLogger.shouldredact = False
    yield
    LibraryLogger.shouldredact = previous


@pytest.mark.parametrize('key', list(SENSITIVE_BODY))
def test_api_printer_redacts_key(redact_on, key):
    """Each sensitive key's value is replaced in the printed request body."""
    output = LibraryLogger.api_printer(SENSITIVE_BODY)
    assert SENSITIVE_BODY[key] not in output
    assert orjson.loads(output)[key] == REDACTED


def test_api_printer_keeps_values_when_redact_off(redact_off):
    """Values are printed unchanged when redaction is disabled."""
    output = LibraryLogger.api_printer(SENSITIVE_BODY)
    assert orjson.loads(output) == SENSITIVE_BODY


def test_redact_value(redact_on):
    """A single value is replaced when redaction is enabled."""
    assert LibraryLogger.redact_value('user@example.com') == REDACTED
    assert LibraryLogger.redact_value(None) is None
    assert LibraryLogger.redact_value('') == ''


def test_redact_value_off(redact_off):
    """A single value is unchanged when redaction is disabled."""
    assert LibraryLogger.redact_value('user@example.com') == 'user@example.com'


class TestLoginLogRedaction(TestBase):
    """The account email is not logged on login when redaction is enabled."""

    def _login(self):
        self.mock_api.side_effect = [
            (call_json.LoginResponses.GET_TOKEN_RESPONSE_SUCCESS, 200),
            (call_json.LoginResponses.LOGIN_RESPONSE_SUCCESS, 200),
        ]
        self.caplog.set_level(logging.DEBUG, logger='pyvesync')
        assert self.run_in_loop(self.manager.auth.login) is True

    def test_login_email_redacted(self):
        """The login debug message hides the email when redact is on."""
        self.manager.redact = True
        try:
            self._login()
        finally:
            self.manager.redact = False
        assert TestDefaults.email not in self.caplog.text
        assert f'Login successful for user: {REDACTED}' in self.caplog.text

    def test_login_email_not_redacted(self):
        """The login debug message shows the email when redact is off."""
        self._login()
        assert f'Login successful for user: {TestDefaults.email}' in self.caplog.text
