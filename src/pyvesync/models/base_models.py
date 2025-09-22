"""Base data models for API requests and response.

These models are used to define the structure of the requests and
responses from the API. They use Mashumaro for serialization and
deserialization. The `DataClassConfigMixin` class sets default options
for `orjson` and `Mashumaro`.

Note:
    Dataclasses should follow the naming convention of
    Request/Response + API Name. Internal models can have any descriptive
    name.


All models should inherit `ResponseBaseModel` or `RequestBaseModel`. Use
[pyvesync.const][pyvesync.const] to set default values and import here.

Attributes are inherited from the [const][pyvesync.const] module for
default values.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import ClassVar

import orjson
from mashumaro.config import BaseConfig
from mashumaro.mixins.orjson import DataClassORJSONMixin

from pyvesync.const import (
    APP_ID,
    APP_VERSION,
    BYPASS_HEADER_UA,
    CLIENT_TYPE,
    DEFAULT_LANGUAGE,
    DEFAULT_REGION,
    DEFAULT_TZ,
    MOBILE_ID,
    PHONE_BRAND,
    PHONE_OS,
    TERMINAL_ID,
    USER_TYPE,
)

RequestHeaders = {
    'User-Agent': BYPASS_HEADER_UA,
    'Content-Type': 'application/json; charset=UTF-8',
}


class BaseModelConfig(BaseConfig):
    """Base config for dataclasses."""

    orjson_options = orjson.OPT_NON_STR_KEYS


@dataclass
class RequestBaseModel(DataClassORJSONMixin):
    """Base request model for API requests.

    Forbids extra keys in the request JSON.
    """

    class Config(BaseModelConfig):
        """orjson config for dataclasses."""

        forbid_extra_keys = True
        orjson_options = orjson.OPT_NON_STR_KEYS


@dataclass
class ResponseBaseModel(DataClassORJSONMixin):
    """Base response model for API responses.

    Allows extra keys in the response model and
    non-string keys in the JSON.
    """

    class Config(BaseConfig):
        """Config for dataclasses."""

        orjson_options = orjson.OPT_NON_STR_KEYS
        forbid_extra_keys = False


@dataclass
class DefaultValues:
    """Default request fields.

    Attributes for the default values of the request fields
    and static methods for preparing calculated fields.
    """

    _call_number: ClassVar[int] = 0
    userType: str = USER_TYPE
    appVersion: str = APP_VERSION
    clientType: str = CLIENT_TYPE
    appId: str = APP_ID
    phoneBrand: str = PHONE_BRAND
    phoneOS: str = PHONE_OS
    mobileId: str = MOBILE_ID
    deviceRegion: str = DEFAULT_REGION
    countryCode: str = DEFAULT_REGION
    userCountryCode: str = DEFAULT_REGION
    acceptLanguage: str = DEFAULT_LANGUAGE
    timeZone: str = DEFAULT_TZ
    terminalId: str = TERMINAL_ID
    debugMode: bool = False

    @staticmethod
    def traceId() -> str:
        """Trace ID CSRF token."""
        return str(int(time()))

    @staticmethod
    def newTraceId() -> str:
        """Generate a new trace ID."""
        DefaultValues._call_number += 1
        return f'APP{TERMINAL_ID[-5:-1]}{int(time())}-{DefaultValues._call_number:0>5}'


@dataclass
class ResponseCodeModel(ResponseBaseModel):
    """Model for the 'result' field in response."""

    traceId: str
    code: int
    msg: str | None
