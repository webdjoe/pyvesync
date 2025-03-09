"""Mixins for Devices that have consistent API requests."""
from typing import TYPE_CHECKING, ClassVar

from pyvesync.data_models.base_models import DefaultValues
from pyvesync.data_models.purifier_models import RequestPurifierStatus
from pyvesync.helper_utils.helpers import Helpers

if TYPE_CHECKING:
    from pyvesync import VeSync


class BypassV2Mixin:
    """Mixin for bypass V2 API.

    Overrides the `_build_request` method and `request_keys` attribute for devices
    that use the Bypass V2 API- /cloud/v2/deviceManaged/bypassV2.
    """
    if TYPE_CHECKING:
        manager: VeSync

    __slots__ = ()
    request_keys: ClassVar[list[str]] = [
        "acceptLanguage",
        "appVersion",
        "phoneBrand",
        "phoneOS",
        "accountID",
        "cid",
        "configModule",
        "debugMode",
        "traceId",
        "timeZone",
        "token",
        "userCountryCode",
        "configModel",
        "deviceId",
        ]

    def _build_request(
        self, payload_method: str, data: dict | None = None, method: str = "bypassV2"
    ) -> RequestPurifierStatus:
        """Build API request body for air purifier."""
        body = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        body.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        body.update(Helpers.get_class_attributes(self, self.request_keys))
        body["method"] = method
        body["payload"] = {"method": payload_method, "source": "APP", "data": data or {}}
        return RequestPurifierStatus.from_dict(body)
