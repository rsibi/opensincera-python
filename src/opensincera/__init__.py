from importlib.metadata import version as _version

from opensincera.errors import (
    AuthError,
    NotFoundError,
    OpenSinceraError,
    RateLimitError,
    ServerError,
)

__all__ = [
    "AuthError",
    "NotFoundError",
    "OpenSinceraError",
    "RateLimitError",
    "ServerError",
    "__version__",
]

__version__ = _version("opensincera-python")
