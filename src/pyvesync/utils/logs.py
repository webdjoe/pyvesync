"""library_logger.py.

This module provides a custom logger for libraries. It automatically
captures the caller's module and class name in the log records, and it
provides helper methods for logging API calls and other specially formatted
messages.

Usage:
    from library_logger import LibraryLogger

    # Use `LibraryLogger.log_api_call` to log API calls.
    LibraryLogger.log_api_call(logger, response)

    # Use `LibraryLogger.log_api_exception` to log API exceptions.
    LibraryLogger.log_api_exception(logger, request_dict, exception)
"""

from __future__ import annotations

import logging
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import orjson
from mashumaro.exceptions import InvalidFieldValue, MissingField, UnserializableField
from multidict import CIMultiDictProxy

if TYPE_CHECKING:
    from aiohttp import ClientResponse
    from aiohttp.client_exceptions import ClientResponseError

    from pyvesync.base_devices.vesyncbasedevice import VeSyncBaseDevice


class LibraryLogger:
    """Library Logging Interface.

    LibraryLogger provides a logging interface that automatically adds context
    (module and class name) and offers helper methods for structured logging,
    such as API call logs.

    Attributes:
        debug (bool): Class attribute to enable or disable debug logging,
            prints API requests & responses that return an error.
        shouldredact (bool): Class attribute whether to redact
            sensitive information from logs.
        verbose (bool): Class attribute to print all request & response content.

    Examples:
        Logging an API call:
        >>> LibraryLogger.log_api_call(logger, response)
            2025-02-01 12:34:56 - DEBUG - my_library - ========API CALL========
            API CALL to endpoint: /api/v1/resource
            Method: POST
            Request Headers:
            {
                REQUEST HEADERS
            }
            Request Body:
                {
                    "key": "value"
                }
            Response Body:
                {
                    RESPONSE BODY
                }

        Logging an API exception:
        >>> LibraryLogger.log_api_exception(logger, request_dict, exception)
            2025-02-01 12:34:56 - DEBUG - pyvesync -
            Error in API CALL to endpoint: /api/v1/resource
            Response Status: 500
            Exception: <Exception>
            Method: POST
            Request Headers:
                {
                    REQUEST HEADERS
                }
            Request Body:
                {
                    "key": "value"
                }
    """

    shouldredact = True
    """Class attribute to determine if sensitive information should be redacted."""
    verbose = False
    """Class attribute to print all request & response content."""
    debug_enabled = False
    """Class attribute to cache status of debug logging to avoid expensive calls."""

    @classmethod
    def check_debug(cls) -> bool:
        """Check if debug logging is enabled."""
        cls.debug_enabled = logging.getLogger('pyvesync').isEnabledFor(logging.DEBUG)
        return cls.debug_enabled

    @classmethod
    def redactor(cls, stringvalue: str) -> str:
        """Redact sensitive strings from debug output.

        This method searches for specific sensitive keys in the input string and replaces
        their values with '##_REDACTED_##'. The keys that are redacted include:

        - token
        - authorizeCode
        - password
        - email
        - tk
        - accountId
        - authKey
        - uuid
        - cid

        Args:
            stringvalue (str): The input string potentially containing
                sensitive information.

        Returns:
            str: The redacted string with sensitive information replaced
                by '##_REDACTED_##'.
        """
        if cls.shouldredact:
            stringvalue = re.sub(
                (
                    r'(?i)'
                    r'((?<=token":\s")|'
                    r'(?<=password":\s")|'
                    r'(?<=email":\s")|'
                    r'(?<=tk":\s")|'
                    r'(?<=accountId":\s")|'
                    r'(?<=accountID":\s")|'
                    r'(?<=authKey":\s")|'
                    r'(?<=uuid":\s")|'
                    r'(?<=cid":\s")|'
                    r'(?<=token\s)|'
                    r'(?<=authorizeCode\s)|'
                    r'(?<=account_id\s))'
                    r'[^"\s]+'
                ),
                '##_REDACTED_##',
                stringvalue,
            )
        return stringvalue

    @staticmethod
    def is_json(data: str | bytes | None) -> bool:
        """Check if the data is JSON formatted."""
        if data is None:
            return False
        if isinstance(data, str):
            data = data.encode('utf-8')
        try:
            orjson.loads(data)
        except orjson.JSONDecodeError:
            return False
        return True

    @staticmethod
    def try_json_loads(data: str | bytes | None) -> dict | None:
        """Try to load JSON data.

        Gracefully handle errors and return None if loading fails.

        Args:
            data (str | bytes | None): JSON data to load.

        Returns:
            dict | None: Parsed JSON data or None if loading fails.
        """
        if data is None:
            return None
        try:
            return orjson.loads(data)
        except (orjson.JSONDecodeError, TypeError):
            return None

    @classmethod
    def api_printer(cls, api: Mapping | bytes | str | None) -> str | None:
        """Print the API dictionary in a readable format."""
        if api is None or len(api) == 0:
            return None
        try:
            if isinstance(api, bytes):
                api_dict = orjson.loads(api)
            elif isinstance(api, str):
                api_dict = orjson.loads(api.encode('utf-8'))
            elif isinstance(api, (dict, CIMultiDictProxy)):
                api_dict = dict(api)
            else:
                return None
            dump = orjson.dumps(
                dict(api_dict), option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS
            )
            return cls.redactor(dump.decode('utf-8'))

        except (orjson.JSONDecodeError, orjson.JSONEncodeError):
            if isinstance(api, bytes):
                return api.decode('utf-8')
            return str(api)

    @staticmethod
    def set_log_level(level: str | int = logging.WARNING) -> None:
        """Set log level for logger to INFO."""
        # Test default log levels if int or str
        logging.getLogger().setLevel(level)

    @staticmethod
    def configure_file_logging(
        log_file: str | Path,
        *,
        level: str | int = logging.INFO,
        stdout: bool = True,
        propagate: bool = False,
    ) -> None:
        """Configure logging for pyvesync library.

        Args:
            log_file (str | Path | None): The name of the file to log to. If None,
                logs will only be printed to the console.
            level (str | int): The log level to set the logger to, can be
                in form of enum `logging.DEBUG` or string `DEBUG`.
            stdout (bool): If True, log messages will also be printed to stdout.
            propagate (bool): If True, log messages will propagate to the root logger.

        Note:
            This method configures the pyvesync base logger and sets
            propagation of log messages to the root logger based on the
            `propagate` parameter.
        """
        logger = logging.getLogger('pyvesync')
        logger.setLevel(level)
        logger.propagate = propagate

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path.resolve())
        stream_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        if stdout:
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

    @classmethod
    def error_device_response_code(
        cls,
        logger: logging.Logger,
        device: VeSyncBaseDevice,
        method_name: str,
        code: int | str,
        msg: str,
    ) -> None:
        """Log an error response from a device API call.

        Use this log message to indicate that a device API call
        returned a response with an error.

        Args:
            logger (logging.Logger): module logger
            device (VeSyncBaseDevice): device instance
            method_name (str): device method name
            code (int | str): error code returned
            msg (str): error message
        """
        logger.error(
            '%s (%s) - %s %s returned error code %s in response with msg: %s',
            device.product_type,
            device.device_type,
            device.device_name,
            method_name,
            str(code),
            msg,
        )

    @classmethod
    def error_mashumaro_response(
        cls,
        logger: logging.Logger,
        method_name: str,
        resp_dict: dict,
        exc: MissingField | InvalidFieldValue | UnserializableField,
        device: VeSyncBaseDevice | None = None,
    ) -> None:
        """Log an error parsing API response.

        Use this log message to indicate that the API response
        is not in the expected format.

        Args:
            logger (logging.Logger): module logger
            method_name (str): device name
            resp_dict (dict): API response dictionary
            exc (MissingField | InvalidFieldValue | UnserializableField): mashumaro
                exception caught
            device (VeSyncBaseDevice | None): device if a device method was called
        """
        if not cls.debug_enabled:
            if device is not None:
                logger.error(
                    'Error parsing %s %s %s response with data model %s',
                    device.product_type,
                    device.device_name,
                    method_name,
                    exc.holder_class_name,
                )
            else:
                logger.error(
                    'Error parsing %s response with data model %s',
                    method_name,
                    exc.holder_class_name,
                )
        msg = f'Error parsing {method_name} response data model {exc.holder_class_name}. '
        if isinstance(exc, MissingField):
            msg += f'Missing field: {exc.field_name} of type {exc.field_type_name}'
        elif isinstance(exc, InvalidFieldValue):
            msg += f'Invalid field value: {exc.field_name} of type {exc.field_type_name}'
        elif isinstance(exc, UnserializableField):
            msg += f'Unserializable field: {exc.field_name} of type {exc.field_type_name}'
        msg += (
            '\n\n Please report this issue tohttps://github.com/webdjoe/pyvesync/issues'
        )
        logger.warning(msg)
        if not cls.debug_enabled:
            return
        msg = ''
        if is_dataclass(exc.holder_class):
            holder = exc.holder_class
            field_tuple = fields(holder)
            resp_f = sorted(resp_dict.keys())
            field_f = sorted([f.name for f in field_tuple])
            dif = set(field_f) - set(resp_f)
            if dif:
                msg += '\n\n-------------------------------------'
                msg += '\n Expected Fields:'
                msg += f'\n({", ".join(field_f)})'
                msg += '\n Response Fields:'
                msg += f'\n({", ".join(resp_f)})'
                msg += '\n Missing Fields:'
                msg += f'\n({", ".join(dif)})'

        msg += '\n\n Full Response:'
        msg += f'\n{orjson.dumps(resp_dict, option=orjson.OPT_INDENT_2).decode("utf-8")}'
        msg += '\n\n---------------------------------'
        msg += '\n\n Exception:'
        msg += f'\n{exc.__traceback__}'
        logger.debug(msg)

    @classmethod
    def error_device_response_content(
        cls,
        logger: logging.Logger,
        device: VeSyncBaseDevice,
        method: str,
        msg: str | None = None,
    ) -> None:
        """Log an error parsing API response.

        Use this log message to indicate that the API response
        is not in the expected format.

        Args:
            logger (logging.Logger): module logger
            device (VeSyncBaseDevice): device instance
            method (str): method that caused the error
            msg (str | None, optional): optional description of error
        """
        logger.error(
            '%s (%s - %s) returned an invalid response format in %s method: %s',
            device.device_name,
            device.product_type,
            device.device_type,
            method,
            msg if msg is not None else '',
        )

    @classmethod
    def log_device_return_code(
        cls,
        logger: logging.Logger,
        method: str,
        device_name: str,
        device_type: str,
        code: int,
        message: str = '',
    ) -> None:
        """Log return code from device API call.

        When API responds with JSON, if the code key is not 0,
        it indicates an error has occured.

        Args:
            logger (logging.Logger): module logger instance
            method (str): method that caused the error
            device_name (str): device name
            device_type (str): device type
            code (int): api response code
            message (str): api response message
        """
        try:
            code_str = str(code)
        except (TypeError, ValueError):
            code_str = 'UNKNOWN'
        if code == 0:
            logger.debug(
                '%s for %s API from %s returned code: %s, message: %s',
                device_name,
                device_type,
                method,
                code_str,
                message,
            )
        else:
            logger.warning(
                '%s for %s API from %s returned error code: %s, message: %s',
                device_name,
                device_type,
                method,
                code_str,
                message,
            )

    @staticmethod
    def _resolve_base_caller_of_async_call() -> str:  # noqa: C901
        """Resolve the frame that invoked VeSync.async_call_api."""
        try:
            pkg_root = 'pyvesync'

            # Start from the caller of log_api_call
            f = sys._getframe(1)  # noqa: SLF001  # pylint: disable=protected-access

            # Find the frame for async_call_api in pyvesync.vesync
            async_frame = None
            while f:
                mod_name = f.f_globals.get('__name__', '')
                func_name = f.f_code.co_name
                if func_name == 'async_call_api' and (
                    mod_name == f'{pkg_root}.vesync' or mod_name.endswith('.vesync')
                ):
                    async_frame = f
                    break
                f = f.f_back  # type: ignore[assignment]

            # The "base caller" is the immediate caller of async_call_api
            target = async_frame.f_back if async_frame else None
            if not target:
                return 'unknown'

            # Skip any frames inside our logging util if present
            while target and target.f_globals.get('__name__', '').startswith(
                f'{pkg_root}.utils.logs'
            ):
                target = target.f_back
            if not target:
                return 'unknown'

            # Build a readable identifier
            func_name = target.f_code.co_name
            mod_name = target.f_globals.get('__name__', '')

            # Prefer class context if available
            cls_name = None
            if 'self' in target.f_locals and target.f_locals['self'] is not None:
                cls = type(target.f_locals['self'])
                cls_name = getattr(cls, '__name__', None)
                mod_name = getattr(cls, '__module__', mod_name)
            elif 'cls' in target.f_locals and target.f_locals['cls'] is not None:
                cls = target.f_locals['cls']
                cls_name = getattr(cls, '__name__', None)
                mod_name = getattr(cls, '__module__', mod_name)

            # Normalize module for compactness: strip root package
            human_mod = mod_name
            if human_mod.startswith(f'{pkg_root}.'):
                human_mod = human_mod[len(pkg_root) + 1 :]  # noqa: E203, RUF100

            if cls_name:
                return f'{cls_name}.{func_name} [{human_mod}]'

        except Exception:  # noqa: BLE001
            return 'unknown'
        return f'{human_mod}.{func_name}'

    @classmethod
    def log_api_call(
        cls,
        logger: logging.Logger,
        response: ClientResponse,
        response_body: bytes | None = None,
        request_headers: dict | None = None,
        request_body: str | dict | None = None,
    ) -> None:
        """Log API calls in debug mode.

        Logs an API call with a specific format that includes the endpoint,
        JSON-formatted headers, request body (if any) and response body.

        Args:
            logger (logging.Logger): The logger instance to use.
            response (aiohttp.ClientResponse): Requests response object from the API call.
            response_body (bytes, optional): The response body to log.
            request_headers (dict, optional): The request headers to log.
            request_body (dict | str, optional): The request body to log.

        Notes:
            This is a method used for the logging of API calls when the debug
            flag is enabled. The method logs the endpoint, method, request headers,
            request body (if any), response headers, and response body (if any).
        """
        if cls.debug_enabled is False:
            return
        # Build the log message parts.

        # Emit a dedicated debug line for the base caller
        parts = ['==================API CALL==================']
        try:
            base_caller = cls._resolve_base_caller_of_async_call()
            # Keep message simple to avoid breaking existing structured logs
            parts.append(f'Caller: {base_caller}')
        except Exception:  # noqa: BLE001,S110
            pass

        parts.append(f'API CALL to endpoint: {response.url.path}')
        parts.append(f'Host: {response.url.host}')
        parts.append(f'Full URL: {response.url}')
        parts.append(f'Response Status: {response.status}')
        parts.append(f'Method: {response.method}')
        parts.append('---------------Request-----------------')

        if request_headers:
            parts.append(
                f'Request Headers: {os.linesep} {cls.api_printer(request_headers)}'
            )
        if request_body is not None:
            request_body = cls.api_printer(request_body)
            parts.append(f'Request Body: {os.linesep} {request_body}')

        parts.append('---------------Response-----------------')
        response_headers = cls.api_printer(response.headers)
        if response_headers:
            parts.append(f'Response Headers: {os.linesep} {response_headers}')

        response_dict = cls.try_json_loads(response_body)
        if response_dict is not None:
            response_str = cls.api_printer(response_dict)
            parts.append(f'Response Body: {os.linesep} {response_str}')
        elif isinstance(response_body, bytes) and len(response_body) > 0:
            response_str = response_body.decode('utf-8')
            parts.append(f'Error parsing response body: {os.linesep} {response_str}')

        full_message = os.linesep.join(parts)
        logger.debug(full_message)

    @classmethod
    def log_api_status_error(
        cls,
        logger: logging.Logger,
        *,
        status_code: int,
        response: ClientResponse,
    ) -> None:
        """Log API response with non-200 status codes.

        Args:
            logger (logging.Logger): The logger instance to use.
            status_code (int): KW only, The HTTP status code to log.
            response (aiohttp.ClientResponse): KW only, dictionary
                containing the request information.
        """
        # Build the log message parts.
        msg = (
            f'Status Code {status_code} error in {response.method}'
            f' API CALL to endpoint: {response.url.path}'
        )
        logger.error(msg)

    @classmethod
    def log_api_exception(
        cls,
        logger: logging.Logger,
        *,
        exception: ClientResponseError,
        request_body: dict | None,
    ) -> None:
        """Log asyncio response exceptions.

        Logs an API call with a specific format that includes the endpoint,
        JSON-formatted headers, request body (if any) and response body.

        Args:
            logger (logging.Logger): The logger instance to use.
            exception (ClientResponseError): KW only, The request body to log.
            request_body (dict | None): KW only, The request body.
        """
        # Build the log message parts.
        parts = [
            f'asyncio error in API CALL to endpoint: {exception.request_info.url.path}'
        ]
        parts.append(f'Exception Raised: {exception}')
        req_headers = cls.api_printer(exception.request_info.headers)
        if req_headers is not None:
            parts.append(f'Request Headers: {os.linesep} {req_headers}')

        req_body = cls.api_printer(request_body)
        if req_body is not None:
            parts.append(f'Request Body: {os.linesep} {req_body}')

        full_message = os.linesep.join(parts)
        logger.error(full_message)
