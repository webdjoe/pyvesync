"""Test VeSync login method."""
import pytest
import orjson

from pyvesync.utils.errors import VesyncLoginError
from pyvesync import const
from pyvesync.models.vesync_models import ResponseLoginModel

from aiohttp_mocker import AiohttpMockSession
from base_test_cases import TestApiFunc
from defaults import Defaults


API_URL = const.API_BASE_URL
DEFAULT_ENDPOINT = '/endpoint'


INVALID_PASSWORD_ERROR = -11201000
INVALID_PASSWORD_RESP = {'code': INVALID_PASSWORD_ERROR, 'msg': 'success'}


LOGIN_RET_BODY = {
    "traceId": Defaults.trace_id,
    "code": 0,
    "msg": "",
    "stacktrace": None,
    "result": {
        "accountID": Defaults.account_id,
        "avatarIcon": "",
        "acceptLanguage": "en",
        "gdprStatus": True,
        "nickName": "nick",
        "userType": "1",
        "token": Defaults.token,
        "countryCode": Defaults.country_code,
    },
}

LOGIN_ENDPOINT = '/cloud/v1/user/login'


class TestLogin(TestApiFunc):
    """Test VeSync login class."""
    def test_invalid_password(self):
        """Test login with invalid user/password."""
        self.mock_api.return_value.request.return_value = AiohttpMockSession(
            method='post',
            url=API_URL + self.default_endpoint,
            status=200,
            response=orjson.dumps(INVALID_PASSWORD_RESP),
        )
        with pytest.raises(VesyncLoginError):
            self.run_in_loop(self.manager.login)

    def test_good_login_response(self):
        """Test successful login."""
        self.mock_api.return_value.request.return_value = AiohttpMockSession(
            method='post',
            url=API_URL + LOGIN_ENDPOINT,
            status=200,
            response=orjson.dumps(LOGIN_RET_BODY),
        )

        login = self.run_in_loop(self.manager.login)
        assert login is True
        assert self.manager.token == Defaults.token
        assert self.manager.account_id == Defaults.account_id
        assert self.manager.enabled is True

    def test_login_response_model(self):
        """Test login response model."""
        self.mock_api.return_value.request.return_value = AiohttpMockSession(
            method='post',
            url=API_URL + LOGIN_ENDPOINT,
            status=200,
            response=orjson.dumps(LOGIN_RET_BODY),
        )

        login = self.run_in_loop(self.manager.login)
        assert isinstance(login, ResponseLoginModel)
        assert login.result.accountID == Defaults.account_id
        assert login.result.token == Defaults.token
