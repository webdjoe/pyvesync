"""Login request and response models.

Dataclasses should follow the naming convention of Request/Response + <API Name> + Model.
Internal models should be named starting with IntResp/IntReq<API Name>Model.

Attributes:
    ResponseLoginResultModel: Model for the 'result' field in login response.
    ResponseLoginModel: Model for the login response.
    RequestLoginModel: Model for the login request.

Notes:
    All models should inherit `ResponseBaseModel` or `RequestBaseModel`. Use
    `pyvesync.data_models.base_models.DefaultValues` to set default values. There
    should be no repeating keys set in the child models.

"""
from dataclasses import dataclass, field
import hashlib

from pyvesync.data_models.base_models import (
    ResponseCodeModel,
    ResponseBaseModel,
    RequestBaseModel,
    DefaultValues,
    )


@dataclass
class RequestLoginModel(RequestBaseModel):
    """Request model for login."""
    # Arguments to set
    email: str
    method: str
    password: str
    # default values
    acceptLanguage: str = DefaultValues.acceptLanguage
    appVersion: str = DefaultValues.appVersion
    timeZone: str = DefaultValues.timeZone
    phoneBrand: str = DefaultValues.phoneBrand
    phoneOS: str = DefaultValues.phoneOS
    traceId: str = field(default_factory=DefaultValues.traceId)
    # Non-default constants
    userType: str = '1'
    devToken: str = ''

    def __post_init__(self) -> None:
        """Set the method field."""
        self.password = self.hash_password(self.password)

    @staticmethod
    def hash_password(string: str) -> str:
        """Encode password."""
        return hashlib.md5(string.encode('utf-8')).hexdigest()


@dataclass
class IntRespLoginResultModel(ResponseBaseModel):
    """Model for the 'result' field in login response containing token and account ID.

    This class is inherited by the `ResponseLoginModel` class.
    """
    accountID: str
    acceptLanguage: str
    countryCode: str
    token: str


@dataclass
class ResponseLoginModel(ResponseCodeModel):
    """Model for the login response.

    Inherits from `BaseResultModel`. The `BaseResultModel` class provides the
    defaults "code" and "msg" fields for the response.

    Attributes:
        result: ResponseLoginResultModel
            The inner model for the 'result' field in the login response.

    Examples:
        ```python
        a = {
            "code": 0,
            "msg": "success",
            "stacktrace": null,
            "module": null,
            "traceId": "123456",
            "result": {
                "accountID": "123456",
                "acceptLanguage": "en",
                "countryCode": "US",
                }
        }
        b = ResponseLoginModel.from_dict(a)
        account_id = b.result.accountId
        token = b.result.token
        ```
    """
    result: IntRespLoginResultModel
    stacktrace: str | None
    module: str | None
