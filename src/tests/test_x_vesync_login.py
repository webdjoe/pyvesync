"""Test VeSync login method."""
# from aiohttp.web_response import Response
from unittest.mock import MagicMock
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


TOKEN_ERROR_CODE = -11001000
TOKEN_ERROR_RESP = call_json.response_body(TOKEN_ERROR_CODE, "Token expired")

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

request_login_token_model = RequestLoginTokenModel(
    authorizeCode=TestDefaults.authorization_code,
    method='loginByAuthorizeCode4Vesync',
    userCountryCode=TestDefaults.country_code,
    traceId=TestDefaults.trace_id,
    terminalId=TestDefaults.terminal_id,
)
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

response_login_token_model = ResponseLoginModel.from_dict(LOGIN_RESPONSES.LOGIN_RESPONSE_SUCCESS)


class TestLoginModels(TestBase):
    """Test VeSync login response models."""

    def test_login_success(self):
        """Test login response model."""
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

    def _build_token_request(self):
        request_get_token_model = RequestGetTokenModel(
            email=TestDefaults.email,
            password=TestDefaults.password,
            method='authByPWDOrOTM',
            userCountryCode=TestDefaults.country_code,
            traceId=TestDefaults.trace_id,
            terminalId=TestDefaults.terminal_id,
            appID=TestDefaults.app_id,
        )
        return request_get_token_model

    def test_token_expired(self):
        """Test login with expired token."""
        token_error_response = orjson.dumps(TOKEN_ERROR_RESP)
        get_token_endpoint = LOGIN_ENDPOINT
        login_token_endpoint = LOGIN_TOKEN_ENDPOINT
        final_response = call_json.DeviceList.device_list_response()
        first_final_endpoint = '/cloud/v1/deviceManaged/devices'
        get_token_response = orjson.dumps(LOGIN_RESPONSES.GET_TOKEN_RESPONSE_SUCCESS)
        login_token_response = orjson.dumps(LOGIN_RESPONSES.LOGIN_RESPONSE_SUCCESS)
        self.mock_api.return_value = MagicMock()
        self.mock_api.return_value.request.side_effect = [
            AiohttpMockSession(
                method='post',
                url=US_BASE_URL + first_final_endpoint,
                status=200,
                response=token_error_response,
            ),
            AiohttpMockSession(
                method='post',
                url=US_BASE_URL + get_token_endpoint,
                status=200,
                response=get_token_response,
            ),
            AiohttpMockSession(
                method='post',
                url=US_BASE_URL + login_token_endpoint,
                status=200,
                response=login_token_response,
            ),
            AiohttpMockSession(
                method='post',
                url=US_BASE_URL + first_final_endpoint,
                status=200,
                response=orjson.dumps(final_response),
            ),
        ]
        self.run_in_loop(self.manager.get_devices)
        assert len(self.mock_api.mock_calls) == 5  # Includes __init__ call
        call_list = self.mock_api.mock_calls
        assert call_list[1].args[0] == 'post'
        assert call_list[1].kwargs['url'] == US_BASE_URL + first_final_endpoint
        assert call_list[2].args[0] == 'post'
        assert call_list[2].kwargs['url'] == US_BASE_URL + get_token_endpoint
        assert call_list[3].args[0] == 'post'
        assert call_list[3].kwargs['url'] == US_BASE_URL + login_token_endpoint
        assert call_list[4].args[0] == 'post'
        assert call_list[4].kwargs['url'] == US_BASE_URL + first_final_endpoint
