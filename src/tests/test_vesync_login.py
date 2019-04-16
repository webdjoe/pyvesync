import pytest
from unittest.mock import Mock, patch, mock_open, call
import unittest
import pyvesync
from pyvesync.vesync import (VeSync,
                             VeSyncSwitch,
                             VeSyncSwitch15A,
                             VeSyncSwitch7A,
                             VeSyncSwitch10A,
                             VeSyncSwitchInWall)
import os
import responses
import requests
import logging

login_test_vals = [
    ('sam@mail.com', 'pass', 'America/New_York', 'full corret'),
    ('sam@mail.com', 'pass', 'invalidtz!', 'invalid tz'),
    ('sam@mail.com', 'pass', None, 'none tz'),
    ('sam@mail.com', 'pass', '', 'empty tz'),
    ('sam@mail.com', None, None, 'none tz pass'),
    ('sam@mail.com', '', '', 'empty pass')
]


@pytest.mark.parametrize(
    'email, password, timezone, testid', login_test_vals
)
def test_login_vals(email, password, timezone, testid):
    """Testing only input validation"""
    v_inst = VeSync(email, password, timezone)
    assert isinstance(v_inst, VeSync)
    assert v_inst.username == email
    assert v_inst.password == password

    if testid == 'full correct':
        assert v_inst.time_zone == timezone
    elif testid in ('invalid tz', 'none tz', 'non tz pass', 'empty tz'):
        assert v_inst.time_zone == pyvesync.vesync.DEFAULT_TZ


login_bad_call = [
    ('sam@mail.com', 'pass', 'correct'),
    ('sam@mail.com', '', 'empty pass'),
    ('sam@mail.com', None, 'none pass'),
    ('', 'pass', 'empty email'),
    (None, 'pass', 'none email'),
]


class TestLogin(object):

    @pytest.fixture()
    def api_mock(self, caplog):
        self.mock_api_call = patch('pyvesync.vesync.requests.post')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospec()
        self.mock_api.return_value.ok = True
        self.mock_api.return_value.status_code = 200
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    @pytest.mark.parametrize(
        'email, password, testid', login_bad_call)
    def test_bad_login(self, api_mock, email, password, testid):

        full_return = {'code': 455}
        self.mock_api.return_value.json.return_value = full_return
        vesync_obj = VeSync(email, password)
        assert vesync_obj.login() is False
        if testid == 'correct':
            hash_pass = vesync_obj.hash_password('pass')
            body = {'email': vesync_obj.username, 'password': hash_pass}
            jd = vesync_obj.get_body('login')
            jd.update(body)
            self.mock_api.assert_called_with(
                'https://smartapi.vesync.com/cloud/v1/user/login',
                json=jd, headers=None, timeout=pyvesync.vesync.API_TIMEOUT
                )
        else:
            assert not self.mock_api.called

    def test_good_login(self, api_mock):
        full_return = {'code': 0,
                       'result': {'accountID': 'sam_actid',
                                  'token': 'sam_token'}}
        self.mock_api.return_value.json.return_value = full_return
        vesync_obj = VeSync('sam@mail.com', 'pass')
        assert vesync_obj.login() is True
        hash_pass = vesync_obj.hash_password('pass')
        body = {'email': vesync_obj.username, 'password': hash_pass}
        jd = vesync_obj.get_body('login')
        jd.update(body)
        self.mock_api.assert_called_with(
            'https://smartapi.vesync.com/cloud/v1/user/login',
            json=jd, headers=None, timeout=pyvesync.vesync.API_TIMEOUT
        )
        assert vesync_obj.tk == 'sam_token'
        assert vesync_obj.account_id == 'sam_actid'


#can also patch call_api, I think patching requests is better to
#show call_api is functioning properly
@pytest.mark.parametrize(
    'email, password, testid', login_bad_call)
def test_login(email, password, testid):
    with patch('pyvesync.vesync.VeSync.call_api', autospec=True) as mock_api:
        mock_api.return_value.ok = True
        mock_api.return_value = ({'code': 455, 'msg': 'sdasd'}, 200)
        vesync_obj = VeSync(email, password)
        vesync_login = vesync_obj.login()
        assert vesync_login is False
        if testid == 'correct':
            hash_pass = vesync_obj.hash_password(password)
            body = {'email': vesync_obj.username, 'password': hash_pass}
            jd = vesync_obj.get_body('login')
            jd.update(body)
            mock_api.assert_called_with(
                vesync_obj, '/cloud/v1/user/login', 'post', json=jd
            )
        else:
            assert not mock_api.called
