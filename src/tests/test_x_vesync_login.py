"""Test VeSync login method."""

import asyncio
import logging
import pytest
from unittest.mock import patch
import orjson
import pyvesync
from pyvesync.vesync import VeSync
from pyvesync.helpers import Helpers as Helpers
from pyvesync.logs import VesyncLoginError

login_test_vals = [
    ('sam@mail.com', 'pass', 'America/New_York', 'full corret'),
    ('sam@mail.com', 'pass', 'invalidtz!', 'invalid tz'),
    ('sam@mail.com', 'pass', None, 'none tz'),
    ('sam@mail.com', 'pass', '', 'empty tz'),
    ('sam@mail.com', None, None, 'none tz pass'),
    ('sam@mail.com', '', '', 'empty pass'),
]


@pytest.mark.parametrize('email, password, timezone, testid', login_test_vals)
def test_vesync_init(email, password, timezone, testid):
    """Testing only input validation."""
    v_inst = VeSync(email, password, timezone)
    assert isinstance(v_inst, VeSync)
    assert v_inst.username == email
    assert v_inst.password == password

    if testid == 'full correct':
        assert v_inst.time_zone == timezone
    elif testid in ('invalid tz', 'none tz', 'non tz pass', 'empty tz'):
        assert v_inst.time_zone == pyvesync.helpers.DEFAULT_TZ


login_bad_call = [
    ('sam@mail.com', 'pass', 'correct'),
    ('sam@mail.com', '', 'empty pass'),
    ('sam@mail.com', None, 'none pass'),
    ('', 'pass', 'empty email'),
    (None, 'pass', 'none email'),
]


class TestLogin(object):
    """Test VeSync login class."""

    @pytest.fixture()
    def api_mock(self, caplog):
        """Mock call_api and initialize VeSync device."""
        self.mock_api_call = patch('pyvesync.vesync.VeSync.async_call_api')
        self.mock_api = self.mock_api_call.start()
        self.loop = asyncio.new_event_loop()
        self.mock_api.return_value.ok = True
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    async def run_coro(self, coro):
        """Run a coroutine in the event loop."""
        return await coro

    def run_in_loop(self, func, *args, **kwargs):
        """Run a function in the event loop."""
        return self.loop.run_until_complete(self.run_coro(func(*args, **kwargs)))

    @pytest.mark.parametrize('email, password, testid', login_bad_call)
    def test_bad_login(self, api_mock, email, password, testid):
        """Test failed login."""
        full_return = (orjson.dumps({'code': -11201000}), 200)
        self.mock_api.return_value = full_return
        vesync_obj = VeSync(email, password)
        with pytest.raises(VesyncLoginError):
            self.run_in_loop(vesync_obj.login)
        if testid == 'correct':
            jd = Helpers.req_body(vesync_obj, 'login')
            self.mock_api.assert_called_with('/cloud/v1/user/login', 'post',
                                             json_object=jd)
        else:
            assert not self.mock_api.called

    def test_good_login(self, api_mock):
        """Test successful login."""
        resp_dict, status = (
            {'code': 0, 'result': {'accountID': 'sam_actid', 'token': 'sam_token'}},
            200,
        )
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        vesync_obj = VeSync('sam@mail.com', 'pass')
        login = self.run_in_loop(vesync_obj.login)
        assert login is True
        jd = Helpers.req_body(vesync_obj, 'login')
        self.mock_api.assert_called_with('/cloud/v1/user/login', 'post', json_object=jd)
        assert vesync_obj.token == 'sam_token'
        assert vesync_obj.account_id == 'sam_actid'
