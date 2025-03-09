"""Base data models for API requests and response.

These models are used to define the structure of the requests and
responses from the API. They use Mashumaro for serialization and
deserialization. The `DataClassConfigMixin` class sets default options
for `orjson` and `Mashumaro`.

Attributes:
    DefaultValues: Class with the default values for request fields. Any
        default values should be included in this class and defined in the
        `const` module.
    RequestBaseModel: Base request model that is configured to
        allow extra keys. Inherits from `DataClassORJSONMixin` to use
        `orjson` for serialization and deserialization.
    ResponseBaseModel: Mixin that is configured to allow non-string values
        and extra keys. Only the required fields should be defined in
        the dataclass. Inherits from `DataClassORJSONMixin` to use `orjson`
        for serialization and deserialization.
    ResponseCodeModel: Defines the standard response fields for the API:
        "traceId", "code" and "msg" fields.

Notes:
    Dataclasses should follow the naming convention of
    Request/Response + <API Name> + Model. Internal models should be
    named starting with Internal + <API Name>.

    `VeSyncFieldInstanceMixin` is used to populate fields from the VeSync instance
    by passing manager as a keyword argument.

    All models should inherit `ResponseBaseModel` or `RequestBaseModel`. Use
    `pyvesync.data_models.base_models.DefaultValues` to set default values.

    Default values are set in `pyvesync.const` and should be imported from there.
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
    """Base request model for API requests."""

    class Config(BaseConfig):
        """orjson config for dataclasses."""
        orjson_options = orjson.OPT_NON_STR_KEYS
        forbid_extra_keys = True


@dataclass
class ResponseBaseModel(DataClassORJSONMixin):
    """Base response model for API responses."""

    class Config(BaseConfig):
        """orjson config for dataclasses."""
        orjson_options = orjson.OPT_NON_STR_KEYS
        forbid_extra_keys = False


@dataclass
class DefaultValues:
    """Calculated request fields."""
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
