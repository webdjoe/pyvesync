"""Mixins for Devices that have similar API requests.

The `BypassV2Mixin` and `BypassV1Mixin` classes are used to send API requests to the
Bypass V2 and Bypass V1 endpoints, respectively. The `BypassV2Mixin` class is used for
devices that use the `/cloud/v2/deviceManaged/bypassV2` endpoint, while the
`BypassV1Mixin` class is used for devices that use the
`/cloud/v1/deviceManaged/{endpoint}` path.
"""

from __future__ import annotations

from logging import Logger
from typing import TYPE_CHECKING, ClassVar, TypeVar

from mashumaro.mixins.orjson import DataClassORJSONMixin

from pyvesync.const import ConnectionStatus
from pyvesync.models.base_models import DefaultValues
from pyvesync.models.bypass_models import (
    RequestBypassV1,
    RequestBypassV2,
)
from pyvesync.utils.errors import ErrorCodes, ErrorTypes, raise_api_errors
from pyvesync.utils.helpers import Helpers
from pyvesync.utils.logs import LibraryLogger

if TYPE_CHECKING:
    from pyvesync import VeSync
    from pyvesync.base_devices import VeSyncBaseDevice
    from pyvesync.utils.errors import ResponseInfo

T_MODEL = TypeVar('T_MODEL', bound=DataClassORJSONMixin)

BYPASS_V1_PATH = '/cloud/v1/deviceManaged/'
BYPASS_V2_BASE = '/cloud/v2/deviceManaged/'


def process_bypassv1_result(
    device: VeSyncBaseDevice,
    logger: Logger,
    method: str,
    resp_dict: dict | None,
    model: type[T_MODEL],
) -> T_MODEL | None:
    """Process the Bypass V1 API response.

    This will gracefully handle errors in the response and error codes,
    logging them as needed. The return value is the built model.

    Args:
        device (VeSyncBaseDevice): The device object.
        logger (Logger): The logger to use for logging.
        method (str): The method used in the payload.
        resp_dict (dict | str): The api response.
        model (type[T_MODEL]): The model to use for the response.

    Returns:
        dict: The response data
    """
    if not isinstance(resp_dict, dict) or 'code' not in resp_dict:
        LibraryLogger.log_device_api_response_error(
            logger,
            device.device_name,
            device.device_type,
            method,
            'Error decoding JSON response',
        )
        return None

    error_info = ErrorCodes.get_error_info(resp_dict['code'])
    device.last_response = error_info
    device.last_response.response_data = resp_dict
    if error_info.error_type != ErrorTypes.SUCCESS:
        _handle_bypass_error(logger, device, method, error_info, resp_dict['code'])
        return None
    result = resp_dict.get('result')
    if not isinstance(result, dict):
        return None
    return Helpers.model_maker(logger, model, method, result, device)


def _handle_bypass_error(
    logger: Logger,
    device: VeSyncBaseDevice,
    method: str,
    error_info: ResponseInfo,
    code: int,
) -> None:
    """Process the outer result error code.

    Internal method for handling the error code in the response field
    used by the `process_bypassv1_result` and `process_bypassv2_result` method.

    Args:
        logger (Logger): The logger to use for logging.
        device (VeSyncBaseDevice): The device object.
        method (str): The method used in the payload.
        error_info (ResponseInfo): The error info object.
        code (int): The error code.

    Note:
        This will raise the appropriate exception based on the error code. See
        `pyvesync.utils.errors.ErrorCodes` for more information
        about the error codes and their meanings.
    """
    raise_api_errors(error_info)
    LibraryLogger.log_device_return_code(
        logger,
        method,
        device.device_name,
        device.product_type,
        code,
        error_info.message,
    )
    device.state.connection_status = ConnectionStatus.from_bool(error_info.device_online)


def _get_inner_result(
    device: VeSyncBaseDevice,
    logger: Logger,
    method: str,
    resp_dict: dict,
) -> dict | None:
    """Process the code in the result field of Bypass V2."""
    try:
        outer_result = resp_dict['result']
        inner_result = outer_result['result']
        code = int(outer_result['code'])
    except (ValueError, TypeError, KeyError):
        LibraryLogger.log_device_api_response_error(
            logger,
            device.device_name,
            device.device_type,
            method,
            'Error processing bypass V2 API response result.',
        )
        return None

    if code != 0:
        error_info = ErrorCodes.get_error_info(code)
        error_msg = f'{error_info.message}'
        if inner_result.get('msg') is not None:
            error_info.message = f'{error_info.message} - {inner_result["msg"]}'
        LibraryLogger.log_device_return_code(
            logger,
            method,
            device.device_name,
            device.product_type,
            code,
            error_msg,
        )
        device.last_response = error_info
        return None
    return inner_result


def process_bypassv2_result(
    device: VeSyncBaseDevice,
    logger: Logger,
    method: str,
    resp_dict: dict | None,
    model: type[T_MODEL],
) -> T_MODEL | None:
    """Process the Bypass V1 API response.

    This will gracefully handle errors in the response and error codes,
    logging them as needed. The return dictionary is the **inner** result value of
    the API response.

    Args:
        device (VeSyncBaseDevice): The device object.
        logger (Logger): The logger to use for logging.
        method (str): The method used in the payload.
        resp_dict (dict | str): The api response.
        model (type[T_MODEL]): The model to use for the response.

    Returns:
        T_MODEL: An instance of the inner result model.
    """
    if not isinstance(resp_dict, dict) or 'code' not in resp_dict:
        LibraryLogger.log_device_api_response_error(
            logger,
            device.device_name,
            device.device_type,
            method,
            'Error decoding JSON response',
        )
        return None

    error_info = ErrorCodes.get_error_info(resp_dict['code'])
    device.last_response = error_info
    device.last_response.response_data = resp_dict
    if error_info.error_type != ErrorTypes.SUCCESS:
        _handle_bypass_error(logger, device, method, error_info, resp_dict['code'])
        return None
    result = _get_inner_result(device, logger, method, resp_dict)
    if not isinstance(result, dict):
        return None
    return Helpers.model_maker(logger, model, method, result, device)


class BypassV2Mixin:
    """Mixin for bypass V2 API.

    Overrides the `_build_request` method and `request_keys` attribute for devices
    that use the Bypass V2 API- /cloud/v2/deviceManaged/bypassV2.
    """

    if TYPE_CHECKING:
        manager: VeSync

    __slots__ = ()
    request_keys: ClassVar[list[str]] = [
        'acceptLanguage',
        'appVersion',
        'phoneBrand',
        'phoneOS',
        'accountID',
        'cid',
        'configModule',
        'debugMode',
        'traceId',
        'timeZone',
        'token',
        'userCountryCode',
        'configModel',
        'deviceId',
    ]

    def _build_request(
        self,
        payload_method: str,
        data: dict | None = None,
        method: str = 'bypassV2',
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
        body['method'] = method
        body['payload'] = {'method': payload_method, 'source': 'APP', 'data': data or {}}
        return RequestBypassV2.from_dict(body)

    async def call_bypassv2_api(
        self,
        payload_method: str,
        data: dict | None = None,
        method: str = 'bypassV2',
        endpoint: str = 'bypassV2',
    ) -> dict | None:
        """Send Bypass V2 API request.

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
        endpoint = BYPASS_V2_BASE + endpoint
        resp_dict, _ = await self.manager.async_call_api(
            endpoint, 'post', request, Helpers.req_header_bypass()
        )
        return resp_dict


class BypassV1Mixin:
    """Mixin for bypass V1 API.

    Overrides the `_build_request` method and `request_keys` attribute for devices
    that use the Bypass V1 API- /cloud/v1/deviceManaged/bypass. The primary method to
    call is `call_bypassv1_api`, which is a wrapper for setting up the request body and
    calling the API. The `bypass` endpoint can also be overridden for specific API calls.
    """

    if TYPE_CHECKING:
        manager: VeSync

    __slots__ = ()
    request_keys: ClassVar[list[str]] = [
        'acceptLanguage',
        'appVersion',
        'phoneBrand',
        'phoneOS',
        'accountID',
        'cid',
        'configModule',
        'debugMode',
        'traceId',
        'timeZone',
        'token',
        'userCountryCode',
        'uuid',
        'configModel',
        'deviceId',
    ]

    def _build_request(
        self,
        request_model: type[RequestBypassV1],
        update_dict: dict | None = None,
        method: str = 'bypass',
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
        body['method'] = method
        body.update(update_dict or {})
        return request_model.from_dict(body)

    async def call_bypassv1_api(
        self,
        request_model: type[RequestBypassV1],
        update_dict: dict | None = None,
        method: str = 'bypass',
        endpoint: str = 'bypass',
    ) -> dict | None:
        """Send ByPass V1 API request.

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
        url_path = BYPASS_V1_PATH + endpoint
        resp_dict, _ = await self.manager.async_call_api(
            url_path, 'post', request, Helpers.req_header_bypass()
        )

        return resp_dict
