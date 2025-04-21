#!/usr/bin/env python3
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

import logging
import os
import re
from collections.abc import Mapping

import orjson
from aiohttp import ClientResponse
from aiohttp.client_exceptions import ClientResponseError
from multidict import CIMultiDictProxy


class LibraryLogger:
    """Library Logging Interface.

    LibraryLogger provides a logging interface that automatically adds context
    (module and class name) and offers helper methods for structured logging,
    such as API call logs.

    Attributes:
        shouldredact (bool): Class attribute whether to redact
            sensitive information from logs.

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

    debug = False
    shouldredact = False

    @classmethod
    def redactor(cls, stringvalue: str) -> str:
        """Redact sensitive strings from debug output.

        This method searches for specific sensitive keys in the input string and replaces
        their values with '##_REDACTED_##'. The keys that are redacted include:

        - token
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
                    r"(?i)"
                    r'((?<=token":\s")|'
                    r'(?<=password":\s")|'
                    r'(?<=email":\s")|'
                    r'(?<=tk":\s")|'
                    r'(?<=accountId":\s")|'
                    r'(?<=authKey":\s")|'
                    r'(?<=uuid":\s")|'
                    r'(?<=cid":\s")|'
                    r"(?<=token\s)|"
                    r"(?<=account_id\s))"
                    r'[^"\s]+'
                ),
                "##_REDACTED_##",
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

    @classmethod
    def api_printer(cls, api: Mapping | bytes | str | None) -> str | None:
        """Print the API dictionary in a readable format."""
        if api is None or len(api) == 0:
            return None
        try:
            if isinstance(api, bytes):
                api_dict = orjson.loads(api)
            elif isinstance(api, str):
                api_dict = orjson.loads(api.encode("utf-8"))
            elif isinstance(api, (dict, CIMultiDictProxy)):
                api_dict = dict(api)
            else:
                return None
            dump = orjson.dumps(dict(api_dict),
                                option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS)
            return cls.redactor(dump.decode("utf-8"))

        except (orjson.JSONDecodeError, orjson.JSONEncodeError):
            if isinstance(api, bytes):
                return api.decode("utf-8")
            return str(api)

    @staticmethod
    def set_log_level(level: str | int = logging.WARNING) -> None:
        """Set log level for logger to INFO."""
        # Test default log levels if int or str
        logging.getLogger().setLevel(level)

    @staticmethod
    def configure_logger(
        level: str | int = logging.INFO
    ) -> None:
        """Configure pyvesync library logger with a specific log level.

        Args:
            level (str, int): The log level to set the logger to, can be
                in form of enum `logging.DEBUG` or string `DEBUG`.

        Note:
            This method configures the pyvesync base logger and prevents
            propagation of log messages to the root logger to avoid duplicate
            messages.
        """
        root_logger = logging.getLogger()
        if root_logger.handlers:
            for handler in root_logger.handlers:
                root_logger.removeHandler(handler)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        for log_name, logger in root_logger.manager.loggerDict.items():
            if isinstance(logger, logging.Logger) and log_name.startswith('pyvesync'):
                logger.setLevel(level)

    @classmethod
    def log_vs_api_response_error(
        cls,
        logger: logging.Logger,
        method_name: str,
        msg: str | None = None,
    ) -> None:
        """Log an error parsing API response.

        Use this log message to indicate that the API response
        is not in the expected format.

        Args:
            logger (logging.Logger): module logger
            method_name (str): device name
            msg (str | None, optional): optional description of error
        """
        if cls.debug is False:
            return
        logger.debug(
            "%s API returned an unexpected response format: %s",
            method_name,
            msg if msg is not None else "",
        )

    @classmethod
    def log_device_api_response_error(
        cls,
        logger: logging.Logger,
        device_name: str,
        device_type: str,
        method: str,
        msg: str | None = None,
    ) -> None:
        """Log an error parsing API response.

        Use this log message to indicate that the API response
        is not in the expected format.

        Args:
            logger (logging.Logger): module logger
            device_name (str): device name
            device_type (str): device type
            method (str): method that caused the error
            msg (str | None, optional): optional description of error
        """
        if cls.debug is False:
            return
        logger.debug(
            "%s for %s API returned an unexpected response format in %s: %s",
            device_name,
            device_type,
            method,
            msg if msg is not None else "",
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
        if cls.debug is False:
            return
        try:
            code_str = str(code)
        except (TypeError, ValueError):
            code_str = "UNKNOWN"
        logger.debug("%s for %s API from %s returned code: %s, message: %s",
                     device_name, device_type, method, code_str, message)

    @classmethod
    def log_api_call(
        cls,
        logger: logging.Logger,
        response: ClientResponse,
        response_body: bytes | None = None,
        request_body: str | dict | None = None,
    ) -> None:
        """Log API calls in debug mode.

        Logs an API call with a specific format that includes the endpoint,
        JSON-formatted headers, request body (if any) and response body.

        Args:
            logger (logging.Logger): The logger instance to use.
            response (aiohttp.ClientResponse): Requests response object from the API call.
            response_body (bytes, optional): The response body to log.
            request_body (dict | str, optional): The request body to log.

        Notes:
            This is a method used for the logging of API calls when the debug
            flag is enabled. The method logs the endpoint, method, request headers,
            request body (if any), response headers, and response body (if any).
        """
        if cls.debug is False:
            return
        # Build the log message parts.
        parts = ["========API CALL========"]
        endpoint = response.url.path
        parts.append(f"API CALL to endpoint: {endpoint}")
        parts.append(f"Response Status: {response.status}")
        parts.append(f"Method: {response.method}")

        request_headers = cls.api_printer(response.request_info.headers)
        if request_headers:
            parts.append(f"Request Headers: {os.linesep} {request_headers}")

        if request_body is not None:
            request_body = cls.api_printer(request_body)
            parts.append(f"Request Body: {os.linesep} {request_body}")

        response_headers = cls.api_printer(response.headers)
        if response_headers:
            parts.append(f"Response Headers: {os.linesep} {response_headers}")

        if cls.is_json(response_body):
            response_str = cls.api_printer(response_body)
            parts.append(f"Response Body: {os.linesep} {response_str}")
        else:
            if isinstance(response_body, bytes):
                response_str = response_body.decode("utf-8")
            parts.append(f"Response Body: {os.linesep} {response_str}")

        full_message = os.linesep.join(parts)
        logger.debug(full_message)

    @classmethod
    def log_api_status_error(
        cls,
        logger: logging.Logger,
        *,
        request_body: dict | None,
        response: ClientResponse,
        response_bytes: bytes | None,
    ) -> None:
        """Log API exceptions in debug mode.

        Logs an API call with a specific format that includes the endpoint,
        JSON-formatted headers, request body (if any) and response body.

        Args:
            logger (logging.Logger): The logger instance to use.
            request_body (dict | None): KW only, The request body to log.
            response (aiohttp.ClientResponse): KW only, dictionary
                containing the request information.
            response_bytes (bytes | None): KW only, The response body to log.
        """
        if cls.debug is False:
            return
        # Build the log message parts.
        parts = [f"Error in API CALL to endpoint: {response.url.path}"]
        parts.append(f"Response Status: {response.status}")
        req_headers = cls.api_printer(response.request_info.headers)
        if req_headers is not None:
            parts.append(f"Request Headers: {os.linesep} {req_headers}")

        req_body = cls.api_printer(request_body)
        if req_body is not None:
            parts.append(f"Request Body: {os.linesep} {req_body}")

        resp_headers = cls.api_printer(response.headers)
        if resp_headers is not None:
            parts.append(f"Response Headers: {os.linesep} {resp_headers}")

        resp_body = cls.api_printer(response_bytes)
        if resp_body is not None:
            parts.append(f"Request Body: {os.linesep} {request_body}")

        full_message = os.linesep.join(parts)
        logger.debug(full_message)

    @classmethod
    def log_api_exception(
        cls,
        logger: logging.Logger,
        *,
        exception: ClientResponseError,
        request_body: dict | None
    ) -> None:
        """Log API exceptions in debug mode.

        Logs an API call with a specific format that includes the endpoint,
        JSON-formatted headers, request body (if any) and response body.

        Args:
            logger (logging.Logger): The logger instance to use.
            exception (ClientResponseError): KW only, The request body to log.
            request_body (dict | None): KW only, The request body.
        """
        if cls.debug is False:
            return
        # Build the log message parts.
        parts = [f"Error in API CALL to endpoint: {exception.request_info.url.path}"]
        parts.append(f"Exception Raised: {exception}")
        req_headers = cls.api_printer(exception.request_info.headers)
        if req_headers is not None:
            parts.append(f"Request Headers: {os.linesep} {req_headers}")

        req_body = cls.api_printer(request_body)
        if req_body is not None:
            parts.append(f"Request Body: {os.linesep} {req_body}")

        full_message = os.linesep.join(parts)
        logger.debug(full_message)
