"""Request Models for Bypass V2 Endpoints."""
from __future__ import annotations
from dataclasses import dataclass

from pyvesync.data_models.base_models import RequestBaseModel


@dataclass
class RequestBypassV2(RequestBaseModel):
    """Bypass V2 Status Request Dict."""
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
    """Bypass V2 Payload Request Dict."""
    data: dict
    method: str
    source: str = "APP"
