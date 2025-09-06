"""Test VeSync login method."""
# from aiohttp.web_response import Response
import pytest
import orjson

from pyvesync.utils.errors import VeSyncLoginError
from pyvesync import const
from pyvesync.utils.helpers import Helpers
from pyvesync.models.vesync_models import (
    ResponseLoginModel,
    RequestLoginTokenModel,
    RequestGetTokenModel,
)

from aiohttp_mocker import AiohttpMockSession
from base_test_cases import TestApiFunc, TestBase
import call_json
from defaults import TestDefaults


US_BASE_URL = const.API_BASE_URL_US
EU_BASE_URL = const.API_BASE_URL_EU

DEFAULT_ENDPOINT = '/endpoint'


INVALID_PASSWORD_ERROR = -11201000
INVALID_PASSWORD_RESP = {'code': INVALID_PASSWORD_ERROR, 'msg': 'success'}


LOGIN_RET_BODY = {
    "traceId": TestDefaults.trace_id,
    "code": 0,
    "msg": "",
    "stacktrace": None,
    "result": {
        "accountID": TestDefaults.account_id,
        "avatarIcon": "",
        "acceptLanguage": "en",
        "gdprStatus": True,
        "nickName": "nick",
        "userType": "1",
        "token": TestDefaults.token,
        "countryCode": TestDefaults.country_code,
    },
}

LOGIN_REQUESTS = call_json.LoginRequests
LOGIN_RESPONSES = call_json.LoginResponses
LOGIN_ENDPOINT = '/globalPlatform/api/accountAuth/v1/authByPWDOrOTM'
LOGIN_TOKEN_ENDPOINT = '/user/api/accountManage/v1/loginByAuthorizeCode4Vesync'

VARIABLE_FIELDS = {
    'traceId': TestDefaults.trace_id,
    'appId': TestDefaults.app_id,
    'terminalId': TestDefaults.terminal_id,
}


class TestLoginModels(TestBase):
    """Test VeSync login response models."""

    def test_login_success(self):
        """Test login response model."""
        request_get_token_model = RequestGetTokenModel(
            email=TestDefaults.email,
            password=TestDefaults.password,
            method='authByPWDOrOTM',
            userCountryCode=TestDefaults.country_code,
            traceId=TestDefaults.trace_id,
            terminalId=TestDefaults.terminal_id,
            appID=TestDefaults.app_id,
        )
        response_get_token_model = ResponseLoginModel.from_dict(LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS)
        request_login_token_model = RequestLoginTokenModel(
            authorizeCode=TestDefaults.authorization_code,
            method='loginByAuthorizeCode4Vesync',
            userCountryCode=TestDefaults.country_code,
            traceId=TestDefaults.trace_id,
            terminalId=TestDefaults.terminal_id,
        )
        response_login_token_model = ResponseLoginModel.from_dict(LOGIN_RESPONSES.LOGIN_RESPONSE_SUCCESS)
        self.mock_api.side_effect = [
            (response_get_token_model.to_dict(), 200),
            (response_login_token_model.to_dict(), 200)
        ]
        self.run_in_loop(self.manager.login)
        assert self.mock_api.call_count == 2
        assert request_get_token_model.email == TestDefaults.email
        assert request_get_token_model.password == Helpers.hash_password(TestDefaults.password)
        assert self.manager.token == TestDefaults.token
        assert self.manager.account_id == TestDefaults.account_id
        call_list = self.mock_api.call_args_list
        assert call_list[0].args[0] == LOGIN_ENDPOINT
        assert call_list[0].args[1] == 'post'
        assert call_list[1].args[0] == LOGIN_TOKEN_ENDPOINT
        assert call_list[1].args[1] == 'post'
        get_token_kwargs = call_list[0].kwargs['json_object']
        get_token_kwargs.appID = TestDefaults.app_id
        get_token_kwargs.terminalId = TestDefaults.terminal_id
        get_token_kwargs.traceId = TestDefaults.trace_id
        assert get_token_kwargs == request_get_token_model
        login_token_kwargs = call_list[1].kwargs['json_object']
        login_token_kwargs.terminalId = TestDefaults.terminal_id
        login_token_kwargs.traceId = TestDefaults.trace_id
        assert login_token_kwargs == request_login_token_model


class TestLogin(TestApiFunc):
    """Test VeSync login class."""
    def test_invalid_password(self):
        """Test login with invalid user/password."""
        self.mock_api.return_value.request.return_value = AiohttpMockSession(
            method='post',
            url=US_BASE_URL + self.default_endpoint,
            status=200,
            response=orjson.dumps(INVALID_PASSWORD_RESP),
        )
        with pytest.raises(VeSyncLoginError):
            self.run_in_loop(self.manager.login)
