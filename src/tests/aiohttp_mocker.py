import re
from http import HTTPStatus
from types import TracebackType
from collections import namedtuple
from unittest import mock
from urllib.parse import parse_qs
from yarl import URL
from orjson import dumps, loads
from aiohttp import (
    ClientConnectionError,
    ClientResponseError,
    StreamReader
    )
from multidict import CIMultiDict


RETYPE = type(re.compile(""))

REQUEST_INFO = namedtuple("REQUEST_INFO", ["url", "method", "headers", "real_url"])


def mock_stream(data) -> StreamReader:
    """Mock a stream with data."""
    protocol = mock.Mock(_reading_paused=False)
    stream = StreamReader(protocol, limit=2**16)
    stream.feed_data(data)
    stream.feed_eof()
    return stream


class AiohttpMockSession:
    """MockAiohttpsession."""
    def __init__(self, url, method, response, status, headers=None):
        self.url = URL(url)
        self.method = method
        self.response_bytes = response
        self.status = status
        self._headers = CIMultiDict(headers or {})

    @property
    def headers(self):
        """Return content_type."""
        return self._headers

    async def __aenter__(self):
        return AiohttpClientMockResponse(
            method=self.method,
            url=self.url,
            status=self.status,
            response=self.response_bytes
        )

    async def __aexit__(self, *args):
        pass


class AiohttpClientMockResponse:
    """Mock Aiohttp client response.

    Adapted from home-assistant/core/tests/test_util/aiohttp.py
    """
    def __init__(
        self,
        method,
        url: URL,
        status=HTTPStatus.OK,
        response=None,
        json=None,
        text=None,
        cookies=None,
        exc=None,
        headers=None,
        side_effect=None,
        closing=None,
    ) -> None:
        """Initialize a fake response.

        Args:
            method: str: HTTP method
            url: URL: URL of the response
            status: HTTPStatus: HTTP status code
            response: bytes: Response content
            json: dict: JSON response content
            text: str: Text response content
            cookies: dict: Cookies to set
            exc: Exception: Exception to raise
            headers: dict: Headers to set
            side_effect: Exception: Exception to raise when read
            closing: bool: Simulate closing connection
        """
        if json is not None:
            text = dumps(json)
        if isinstance(text, str):
            response = text.encode("utf-8")
        if response is None:
            response = b""

        self.charset = "utf-8"
        self.method = method
        self._url = url
        self.status = status
        self._response = response
        self.exc = exc
        self.side_effect = side_effect
        self.closing = closing
        self._headers = CIMultiDict(headers or {})
        self._cookies = {}

        if cookies:
            for name, data in cookies.items():
                cookie = mock.MagicMock()
                cookie.value = data
                self._cookies[name] = cookie

    def match_request(self, method, url, params=None):
        """Test if response answers request."""
        if method.lower() != self.method.lower():
            return False

        # regular expression matching
        if isinstance(self._url, RETYPE):
            return self._url.search(str(url)) is not None

        if (
            self._url.scheme != url.scheme
            or self._url.host != url.host
            or self._url.path != url.path
        ):
            return False

        # Ensure all query components in matcher are present in the request
        request_qs = parse_qs(url.query_string)
        matcher_qs = parse_qs(self._url.query_string)
        for key, vals in matcher_qs.items():
            for val in vals:
                try:
                    request_qs.get(key, []).remove(val)
                except ValueError:
                    return False

        return True

    @property
    def request_info(self):
        """Return request info."""
        return REQUEST_INFO(
            url=self.url,
            method=self.method,
            headers=self.headers,
            real_url=self.url)

    @property
    def headers(self):
        """Return content_type."""
        return self._headers

    @property
    def cookies(self):
        """Return dict of cookies."""
        return self._cookies

    @property
    def url(self):
        """Return yarl of URL."""
        return self._url

    @property
    def content_type(self):
        """Return yarl of URL."""
        return self._headers.get("content-type")

    @property
    def content(self):
        """Return content."""
        return mock_stream(self.response)

    async def read(self):
        """Return mock response."""
        return self.response

    async def text(self, encoding="utf-8", errors="strict"):
        """Return mock response as a string."""
        return self.response.decode(encoding, errors=errors)

    async def json(self, encoding="utf-8", content_type=None, loads=loads):
        """Return mock response as a json."""
        return loads(self.response.decode(encoding))

    def release(self):
        """Mock release."""

    def raise_for_status(self):
        """Raise error if status is 400 or higher."""
        if self.status >= 400:
            request_info = mock.Mock(real_url="http://example.com")
            raise ClientResponseError(
                request_info=request_info,
                history=None,  # type: ignore
                status=self.status,
                headers=self.headers,
            )

    def close(self):
        """Mock close."""

    async def wait_for_close(self):
        """Wait until all requests are done.

        Do nothing as we are mocking.
        """

    @property
    def response(self):
        """Property method to expose the response to other read methods."""
        if self.closing:
            raise ClientConnectionError("Connection closed")
        return self._response

    async def __aenter__(self):
        """Enter the context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the context manager."""
