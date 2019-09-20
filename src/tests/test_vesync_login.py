"""Test VeSync login method."""

import logging
import pytest
from unittest.mock import patch
import pyvesync
from pyvesync.vesync import VeSync
from pyvesync.helpers import Helpers as helpers

login_test_vals = [('sam@mail.com', 'pass', 'America/New_York', 'full corret'),
                   ('sam@mail.com', 'pass', 'invalidtz!', 'invalid tz'),
                   ('sam@mail.com', 'pass', None, 'none tz'),
                   ('sam@mail.com', 'pass', '', 'empty tz'),
                   ('sam@mail.com', None, None, 'none tz pass'),
                   ('sam@mail.com', '', '', 'empty pass')]


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
        self.mock_api_call = patch('pyvesync.helpers.Helpers.call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospec()
        self.mock_api.return_value.ok = True
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    @pytest.mark.parametrize('email, password, testid', login_bad_call)
    def test_bad_login(self, api_mock, email, password, testid):
        """Test failed login."""
        full_return = ({'code': 455}, 200)
        self.mock_api.return_value = full_return
        vesync_obj = VeSync(email, password)
        assert vesync_obj.login() is False
        if testid == 'correct':
            jd = helpers.req_body(vesync_obj, 'login')
            self.mock_api.assert_called_with('/cloud/v1/user/login',
                                             'post',
                                             json=jd)
        else:
            assert not self.mock_api.called

    def test_good_login(self, api_mock):
        """Test successful login."""
        full_return = ({
            'code': 0,
            'result': {
                'accountID': 'sam_actid',
                'token': 'sam_token'
            }
        }, 200)
        self.mock_api.return_value = full_return
        vesync_obj = VeSync('sam@mail.com', 'pass')
        assert vesync_obj.login() is True
        jd = helpers.req_body(vesync_obj, 'login')
        self.mock_api.assert_called_with('/cloud/v1/user/login',
                                         'post',
                                         json=jd)
        assert vesync_obj.token == 'sam_token'
        assert vesync_obj.account_id == 'sam_actid'


@pytest.mark.parametrize('email, password, testid', login_bad_call)
@patch('pyvesync.helpers.requests.post')
def test_login(mock_api, email, password, testid):
    """Test multiple failed login calls."""
    return_tuple = {'code': 455, 'msg': 'sdasd'}
    mock_api.return_value.ok = True
    mock_api.return_value.json.return_value = return_tuple
    vesync_obj = VeSync(email, password)
    vesync_login = vesync_obj.login()
    assert vesync_login is False
    if testid == 'correct':
        jd = helpers.req_body(vesync_obj, 'login')
        mock_api.assert_called_with(
            'https://smartapi.vesync.com/cloud/v1/user/login',
            headers=None,
            json=jd,
            timeout=5)
    else:
        assert not mock_api.called
