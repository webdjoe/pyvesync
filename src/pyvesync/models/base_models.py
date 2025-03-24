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
[pyvesync.const](pyvesync.const) to set default values and import here.

Attributes are inherited from the [const](pyvesync.const) module for
default values.
"""
from __future__ import annotations
from time import time
from dataclasses import dataclass
import orjson
from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.config import BaseConfig
from pyvesync.const import (
    USER_TYPE,
    APP_VERSION,
    PHONE_BRAND,
    PHONE_OS,
    MOBILE_ID,
    DEFAULT_REGION,
    DEFAULT_LANGUAGE,
    DEFAULT_TZ,
    BYPASS_HEADER_UA,
    )


RequestHeaders = {
    "User-Agent": BYPASS_HEADER_UA,
    "Content-Type": "application/json; charset=UTF-8",
}


@dataclass
class RequestBaseModel(DataClassORJSONMixin):
    """Base request model for API requests.

    Forbids extra keys in the request JSON.
    """

    class Config(BaseConfig):
        """orjson config for dataclasses."""
        orjson_options = orjson.OPT_NON_STR_KEYS
        forbid_extra_keys = True


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
    userType: str = USER_TYPE
    appVersion: str = APP_VERSION
    phoneBrand: str = PHONE_BRAND
    phoneOS: str = PHONE_OS
    mobileId: str = MOBILE_ID
    deviceRegion: str = DEFAULT_REGION
    countryCode: str = DEFAULT_REGION
    userCountryCode: str = DEFAULT_REGION
    acceptLanguage: str = DEFAULT_LANGUAGE
    timeZone: str = DEFAULT_TZ
    debugMode: bool = False

    @staticmethod
    def traceId() -> str:
        """Trace ID CSRF token."""
        return str(int(time()))


@dataclass
class ResponseCodeModel(ResponseBaseModel):
    """Model for the 'result' field in response."""
    traceId: str
    code: int
    msg: str | None
