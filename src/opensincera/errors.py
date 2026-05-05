"""Exception hierarchy for the opensincera library.

All errors raised by the library inherit from `OpenSinceraError`, so callers
can either catch the base class to handle anything from this library or catch
specific subclasses (`AuthError`, `NotFoundError`, `RateLimitError`,
`ServerError`) to react to particular HTTP failure modes.
"""

from __future__ import annotations


class OpenSinceraError(Exception):
    """Base class for every error raised by opensincera."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuthError(OpenSinceraError):
    """Invalid or missing API token (HTTP 401)."""


class NotFoundError(OpenSinceraError):
    """Resource not found (HTTP 404) — e.g., unknown publisher id or domain."""


class RateLimitError(OpenSinceraError):
    """Rate limit exceeded (HTTP 429).

    `retry_after` mirrors the server's `Retry-After` header in seconds when
    one was provided; it is `None` if the server didn't supply a value.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = 429,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code)
        self.retry_after = retry_after


class ServerError(OpenSinceraError):
    """Server-side error (any HTTP 5xx)."""


class TimeoutError(OpenSinceraError):
    """Request to OpenSincera timed out before a response was received.

    Wraps `httpx.TimeoutException` so callers can catch every library failure
    via `OpenSinceraError` without importing httpx. Intentionally shadows
    Python's builtin `TimeoutError`; access via `opensincera.TimeoutError` or
    `opensincera.errors.TimeoutError` to disambiguate.
    """
