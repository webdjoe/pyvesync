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
import json
import os
import re
from textwrap import indent
from collections.abc import MutableMapping
from urllib.parse import urlparse
from requests import RequestException, Response
from requests.structures import CaseInsensitiveDict

_LOGGER = logging.getLogger(__name__)


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

    shouldredact = True

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
    def is_json(data: str) -> bool:
        """Check if the data is JSON formatted."""
        try:
            json.loads(data)
        except json.JSONDecodeError:
            return False
        return True

    @classmethod
    def api_printer(cls, api: MutableMapping | bytes | str | None) -> str | None:
        """Print the API dictionary in a readable format."""
        if api is None:
            return None
        try:
            if isinstance(api, bytes):
                api_dict = json.loads(api.decode("utf-8"))
            elif isinstance(api, str):
                api_dict = json.loads(api)
            elif isinstance(api, (dict, CaseInsensitiveDict)):
                api_dict = dict(api)
            else:
                return None
            dump = indent(json.dumps(dict(api_dict), indent=2), ' ')
            return cls.redactor(dump)
        except json.JSONDecodeError:
            return None

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
    def log_api_call(
        cls,
        logger: logging.Logger,
        response: Response
    ) -> None:
        """Log API calls in debug mode.

        Logs an API call with a specific format that includes the endpoint,
        JSON-formatted headers, request body (if any) and response body.

        Args:
            logger (logging.Logger): The logger instance to use.
            response (Response): Requests response object from the API call.

        Notes:
            This is a method used for the logging of API calls when the debug
            flag is enabled. The method logs the endpoint, method, request headers,
            request body (if any), response headers, and response body (if any).
        """
        # Build the log message parts.
        parts = ["========API CALL========"]
        endpoint = urlparse(response.request.url).path
        endpoint = endpoint if isinstance(endpoint, str) else str(endpoint)
        parts.append(f"API CALL to endpoint: {endpoint}")
        parts.append(f"Response Status: {response.status_code}")

        method = response.request.method
        if method:
            parts.append(f"Method: {method.upper()}")

        request_headers = cls.api_printer(response.request.headers)
        if request_headers:
            parts.append(f"Request Headers: {os.linesep} {request_headers}")

        if method and method.upper() == "POST" and response.request.body is not None:
            request_body = cls.api_printer(response.request.body)
            if request_body:
                parts.append(f"Request Body: {os.linesep} {request_body}")

        response_headers = cls.api_printer(response.headers)
        if response_headers:
            parts.append(f"Response Headers: {os.linesep} {response_headers}")

        if cls.is_json(response.text):
            response_body = cls.api_printer(response.json())
            parts.append(f"Response Body: {os.linesep} {response_body}")
        else:
            parts.append(f"Response Body: {os.linesep} {response.text}")

        full_message = os.linesep.join(parts)
        logger.debug(full_message)

    @classmethod
    def log_api_exception(
        cls,
        logger: logging.Logger,
        *,
        request_dict: dict,
        exception: Exception | RequestException | None = None,
    ) -> None:
        """Log API exceptions in debug mode.

        Logs an API call with a specific format that includes the endpoint,
        JSON-formatted headers, request body (if any) and response body.

        Args:
            logger (logging.Logger): The logger instance to use.
            request_dict (dict): Dictionary containing the request information.
            exception (Exception): The exception that occurred during the API call.

        Note:
            `request_dict` argument is a dictionary of request and response values:
            {
                "endpoint": "/api/v1/resource",
                "headers": {"Authorization": "Bearer xyz"},
                "method": "POST",
                "body": {"key": "value"},
            }
        """
        # Build the log message parts.
        parts = [f"Error in API CALL to endpoint: {request_dict['endpoint']}"]
        if request_dict.get("status_code"):
            parts.append(f"Response Status: {request_dict['status_code']}")
        if isinstance(exception, (RequestException, Exception)):
            parts.append(f"Exception: {exception}")

        parts.append(f"Method: {request_dict['method'].upper()}")

        headers = cls.api_printer(request_dict.get("headers"))
        if headers:
            parts.append(f"Request Headers: {os.linesep}"
                         f"{json.dumps(request_dict['headers'], indent=2)}")
        request_body = cls.api_printer(request_dict.get('body'))
        if request_body is not None:
            parts.append(f"Request Body: {os.linesep} {request_body}")

        full_message = os.linesep.join(parts)
        logger.debug(full_message)


class VeSyncError(Exception):
    """Base exception for VeSync errors."""


class VesyncLoginError(VeSyncError):
    """Exception raised for login authentication errors."""

    def __init__(self, msg: str) -> None:
        """Initialize the exception with a message."""
        super().__init__(msg)


class VeSyncRateLimitError(VeSyncError):
    """Exception raised for VeSync API rate limit errors."""

    def __init__(self) -> None:
        """Initialize the exception with a message."""
        super().__init__("VeSync API rate limit exceeded")


class VeSyncAPIResponseError(VeSyncError):
    """Exception raised for malformed VeSync API responses."""

    def __init__(self) -> None:
        """Initialize the exception with a message."""
        super().__init__("VeSync API response error")
