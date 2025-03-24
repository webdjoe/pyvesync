"""Mixins for Devices that have similar API requests.

The `BypassV2Mixin` and `BypassV1Mixin` classes are used to send API requests to the
Bypass V2 and Bypass V1 endpoints, respectively. The `BypassV2Mixin` class is used for
devices that use the `/cloud/v2/deviceManaged/bypassV2` endpoint, while the
`BypassV1Mixin` class is used for devices that use the
`/cloud/v1/deviceManaged/{endpoint}` path.
"""

from typing import TYPE_CHECKING, ClassVar

from pyvesync.models.base_models import DefaultValues
from pyvesync.models.bypass_models import RequestBypassV2, RequestBypassV1
from pyvesync.utils.helpers import Helpers

if TYPE_CHECKING:
    from pyvesync import VeSync


class BypassV2Mixin:
    """Mixin for bypass V2 API.

    Overrides the `_build_request` method and `request_keys` attribute for devices
    that use the Bypass V2 API- /cloud/v2/deviceManaged/bypassV2.
    """

    if TYPE_CHECKING:
        manager: VeSync

    endpoint: ClassVar[str] = "/cloud/v2/deviceManaged/bypassV2"

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
    ) -> RequestBypassV2:
        """Build API request body Bypass V2 endpoint.

        Args:
            payload_method (str): The method to use in the payload dict.
            data (dict | None): The data dict inside the payload value.
            method (str): The method to use in the outer body, defaults to bypassV2.
        """
        body = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        body.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        body.update(Helpers.get_class_attributes(self, self.request_keys))
        body["method"] = method
        body["payload"] = {"method": payload_method, "source": "APP", "data": data or {}}
        return RequestBypassV2.from_dict(body)

    async def call_bypassv2_api(
        self,
        payload_method: str,
        data: dict | None = None,
        method: str = "bypassV2",
        endpoint: str | None = None,
    ) -> bytes | None:
        """Send ByPass V2 API request.

        This uses the `_build_request` method to send API requests to the Bypass V2 API.

        Args:
            payload_method (str): The method to use in the payload dict.
            data (dict | None): The data to send in the request.
            method (str): The method to use in the outer body.
            endpoint (str | None): The last part of the API url, defaults to
                `bypassV2`, e.g. `/cloud/v2/deviceManaged/bypassV2`.

        Returns:
            bytes: The response from the API request.
        """
        request = self._build_request(payload_method, data, method)
        if endpoint is None:
            endpoint = self.endpoint
        resp_bytes, _ = await self.manager.async_call_api(
            endpoint, "post", request, Helpers.req_header_bypass()
        )

        return resp_bytes


class BypassV1Mixin:
    """Mixin for bypass V1 API.

    Overrides the `_build_request` method and `request_keys` attribute for devices
    that use the Bypass V1 API- /cloud/v1/deviceManaged/bypass. The primary method to
    call is `call_bypassv1_api`, which is a wrapper for calling the API. The `bypass`
    endpoint can also be overridden.
    """

    if TYPE_CHECKING:
        manager: VeSync

    path_base: ClassVar[str] = "/cloud/v1/deviceManaged/"

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
        "uuid",
        "configModel",
        "deviceId",
    ]

    def _build_request(
        self,
        request_model: type[RequestBypassV1],
        update_dict: dict | None = None,
        method: str = "bypass"
    ) -> RequestBypassV1:
        """Build API request body for the Bypass V1 endpoint.

        Args:
            request_model (type[RequestBypassV1]): The request model to use.
            update_dict (dict | None): Additional keys to add on.
            method (str): The method to use in the outer body, defaults to bypass.

        Returns:
            RequestBypassV1: The request body for the Bypass V1 endpoint, the correct
            model is determined from the RequestBypassV1 discriminator.
        """
        body = Helpers.get_class_attributes(DefaultValues, self.request_keys)
        body.update(Helpers.get_class_attributes(self.manager, self.request_keys))
        body.update(Helpers.get_class_attributes(self, self.request_keys))
        body["method"] = method
        body.update(update_dict or {})
        return request_model.from_dict(body)

    async def call_bypassv1_api(
        self,
        request_model: type[RequestBypassV1],
        update_dict: dict | None = None,
        method: str = "bypass",
        endpoint: str = "bypass",
    ) -> bytes | None:
        """Send ByPass V2 API request.

        This uses the `_build_request` method to send API requests to the Bypass V1 API.
        The endpoint can be overridden with the `endpoint` argument.

        Args:
            request_model (type[RequestBypassV1]): The request model to use.
            update_dict (dict): Additional keys to add on.
            method (str): The method to use in the outer body.
            endpoint (str | None): The last part of the url path, defaults to
                `bypass`, e.g. `/cloud/v1/deviceManaged/bypass`.

        Returns:
            bytes: The response from the API request.
        """
        request = self._build_request(request_model, update_dict, method)
        url_path = self.path_base + endpoint
        resp_bytes, _ = await self.manager.async_call_api(
            url_path, "post", request, Helpers.req_header_bypass()
        )

        return resp_bytes
