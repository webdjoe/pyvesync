"""Request Models for Bypass V2 Endpoints.

API calls to bypassV2 endpoints have similar request structures. These models are used
to serialize and deserialize the JSON requests for the bypassV2 endpoints.
"""
from __future__ import annotations
from dataclasses import dataclass

from pyvesync.models.base_models import RequestBaseModel


@dataclass
class RequestBypassV2(RequestBaseModel):
    """Bypass V2 Status Request Dict.

    This is the bypassV2 request model for API calls
    that use the `configModel` and `deviceId` fields.
    """
    acceptLanguage: str
    accountID: str
    appVersion: str
    cid: str
    configModule: str
    debugMode: bool
    method: str
    phoneBrand: str
    phoneOS: str
    traceId: str
    timeZone: str
    token: str
    userCountryCode: str
    deviceId: str
    configModel: str
    payload: BypassV2RequestPayload


@dataclass
class BypassV2RequestPayload(RequestBaseModel):
    """Generic Bypass V2 Payload Request model."""
    data: dict
    method: str
    source: str = "APP"


@dataclass
class RequestBypassV1(RequestBaseModel):
    """Bypass V1 Status Request Dict.

    This is the bypassV1 request model for API calls
    that use the `configModel` and `deviceId` fields.
    """
    acceptLanguage: str
    accountID: str
    appVersion: str
    cid: str
    configModule: str
    debugMode: bool
    method: str
    phoneBrand: str
    phoneOS: str
    traceId: str
    timeZone: str
    token: str
    userCountryCode: str
    uuid: str
    deviceId: str
    configModel: str
