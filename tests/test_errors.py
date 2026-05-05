import pytest

from opensincera.errors import (
    AuthError,
    NotFoundError,
    OpenSinceraError,
    RateLimitError,
    ServerError,
    TimeoutError,
)


class TestOpenSinceraError:
    def test_is_an_exception(self) -> None:
        assert issubclass(OpenSinceraError, Exception)

    def test_message_stringifies(self) -> None:
        err = OpenSinceraError("publisher exploded")
        assert str(err) == "publisher exploded"

    def test_carries_status_code(self) -> None:
        err = OpenSinceraError("nope", status_code=418)
        assert err.status_code == 418

    def test_status_code_defaults_to_none(self) -> None:
        err = OpenSinceraError("nope")
        assert err.status_code is None


@pytest.mark.parametrize(
    "subclass",
    [AuthError, NotFoundError, RateLimitError, ServerError, TimeoutError],
)
def test_specific_errors_inherit_from_base(
    subclass: type[OpenSinceraError],
) -> None:
    assert issubclass(subclass, OpenSinceraError)


def test_specific_error_caught_as_base() -> None:
    with pytest.raises(OpenSinceraError):
        raise AuthError("bad token", status_code=401)


class TestRateLimitError:
    def test_status_code_defaults_to_429(self) -> None:
        err = RateLimitError("slow down")
        assert err.status_code == 429

    def test_carries_retry_after(self) -> None:
        err = RateLimitError("slow down", retry_after=2.5)
        assert err.retry_after == 2.5

    def test_retry_after_defaults_to_none(self) -> None:
        err = RateLimitError("slow down")
        assert err.retry_after is None
