"""Synchronous HTTP client for the OpenSincera API.

The public class is `Client`; it's re-exported as `opensincera.Client`.

Retry policy (`429 Too Many Requests`) is hand-rolled rather than pulled
from a library: we have one endpoint, one retried status code, and the
behavior is documented as load-bearing — the official docs warn that
rate-limit abuse leads to permanent suspension. Keeping the loop visible
in this file is a deliberate legibility choice.
"""

from __future__ import annotations

import time
from types import TracebackType
from typing import Final

import httpx

from opensincera._models import Publisher
from opensincera.errors import (
    AuthError,
    NotFoundError,
    OpenSinceraError,
    RateLimitError,
    ServerError,
    TimeoutError,
)

_BASE_URL: Final = "https://open.sincera.io/api"
_DEFAULT_TIMEOUT: Final = 10.0
_DEFAULT_MAX_ATTEMPTS: Final = 3
_BACKOFF_CAP_SECONDS: Final = 60.0


class Client:
    """Synchronous OpenSincera API client.

    Use as a regular object, or as a context manager to ensure the
    underlying HTTP connection pool is released:

        with Client(api_key="…") as c:
            pub = c.get_publisher_by_domain("nytimes.com")
    """

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retry_attempts: int = _DEFAULT_MAX_ATTEMPTS,
        base_url: str = _BASE_URL,
    ) -> None:
        if max_retry_attempts < 1:
            raise ValueError("max_retry_attempts must be >= 1")
        self._max_retry_attempts = max_retry_attempts
        self._http = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    def get_publisher_by_domain(self, domain: str) -> Publisher:
        """Fetch publisher metadata by its base domain (e.g. ``nytimes.com``)."""
        return self._fetch_publisher({"domain": domain})

    def get_publisher_by_id(self, publisher_id: int) -> Publisher:
        """Fetch publisher metadata by its OpenSincera publisher ID."""
        return self._fetch_publisher({"id": publisher_id})

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def _fetch_publisher(self, params: dict[str, str | int]) -> Publisher:
        response = self._request_with_retry("/publishers", params)
        return Publisher.model_validate(response.json())

    def _request_with_retry(
        self,
        path: str,
        params: dict[str, str | int],
    ) -> httpx.Response:
        for attempt in range(self._max_retry_attempts):
            try:
                response = self._http.get(path, params=params)
            except httpx.TimeoutException as exc:
                raise TimeoutError(f"Request to {path} timed out") from exc

            if response.status_code != 429:
                self._raise_for_status(response)
                return response

            wait_seconds = self._wait_for_retry(response, attempt)
            if attempt == self._max_retry_attempts - 1:
                raise RateLimitError(
                    "Rate limit exceeded; retries exhausted",
                    retry_after=wait_seconds,
                )
            time.sleep(wait_seconds)

        # Unreachable: the loop body always returns or raises.
        raise OpenSinceraError("retry loop exited unexpectedly")  # pragma: no cover

    def _wait_for_retry(self, response: httpx.Response, attempt: int) -> float:
        header = response.headers.get("Retry-After")
        if header is not None:
            try:
                return float(header)
            except ValueError:
                pass
        return min(2.0**attempt, _BACKOFF_CAP_SECONDS)

    def _raise_for_status(self, response: httpx.Response) -> None:
        status = response.status_code
        if status == 401:
            raise AuthError("Invalid or missing API token", status_code=status)
        if status == 404:
            raise NotFoundError("Resource not found", status_code=status)
        if 500 <= status < 600:
            raise ServerError(f"Server error: {status}", status_code=status)
        if not response.is_success:
            raise OpenSinceraError(
                f"Unexpected response: {status}",
                status_code=status,
            )
