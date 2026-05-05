"""Tests for the synchronous HTTP client in `opensincera._client`.

Uses respx to mock httpx without making real network calls.
"""

import httpx
import pytest
import respx

from opensincera import Client
from opensincera.errors import (
    AuthError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
)
from tests.test_models import SAMPLE_PUBLISHER

_API_BASE = "https://open.sincera.io/api"


@pytest.fixture
def client() -> Client:
    return Client(api_key="test-token", max_retry_attempts=3, timeout=5.0)


@respx.mock
def test_get_publisher_by_domain_returns_publisher(client: Client) -> None:
    route = respx.get(f"{_API_BASE}/publishers", params={"domain": "businessinsider.com"}).mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    pub = client.get_publisher_by_domain("businessinsider.com")
    assert route.called
    assert pub.publisher_id == 1
    assert pub.name == "Business Insider"


@respx.mock
def test_get_publisher_by_id_sends_id_query_param(client: Client) -> None:
    route = respx.get(f"{_API_BASE}/publishers", params={"id": "1"}).mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    pub = client.get_publisher_by_id(1)
    assert route.called
    assert pub.publisher_id == 1


@respx.mock
def test_request_includes_bearer_token(client: Client) -> None:
    route = respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    client.get_publisher_by_domain("nytimes.com")
    sent = route.calls[0].request
    assert sent.headers["Authorization"] == "Bearer test-token"


@respx.mock
def test_401_raises_auth_error(client: Client) -> None:
    respx.get(f"{_API_BASE}/publishers").mock(return_value=httpx.Response(401))
    with pytest.raises(AuthError):
        client.get_publisher_by_domain("any.com")


@respx.mock
def test_404_raises_not_found_error(client: Client) -> None:
    respx.get(f"{_API_BASE}/publishers").mock(return_value=httpx.Response(404))
    with pytest.raises(NotFoundError):
        client.get_publisher_by_domain("nonexistent.com")


@respx.mock
def test_500_raises_server_error(client: Client) -> None:
    respx.get(f"{_API_BASE}/publishers").mock(return_value=httpx.Response(500))
    with pytest.raises(ServerError):
        client.get_publisher_by_domain("any.com")


@respx.mock
def test_503_also_raises_server_error(client: Client) -> None:
    respx.get(f"{_API_BASE}/publishers").mock(return_value=httpx.Response(503))
    with pytest.raises(ServerError):
        client.get_publisher_by_domain("any.com")


@respx.mock
def test_timeout_raises_timeout_error(client: Client) -> None:
    respx.get(f"{_API_BASE}/publishers").mock(side_effect=httpx.TimeoutException("timed out"))
    with pytest.raises(TimeoutError):
        client.get_publisher_by_domain("any.com")


@respx.mock
def test_429_then_200_retries_and_succeeds(client: Client) -> None:
    route = respx.get(f"{_API_BASE}/publishers").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json=SAMPLE_PUBLISHER),
        ],
    )
    pub = client.get_publisher_by_domain("any.com")
    assert route.call_count == 2
    assert pub.publisher_id == 1


@respx.mock
def test_429_exhausted_raises_rate_limit_error(client: Client) -> None:
    route = respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "0"}),
    )
    with pytest.raises(RateLimitError) as exc_info:
        client.get_publisher_by_domain("any.com")
    assert route.call_count == 3  # max_retry_attempts
    assert exc_info.value.retry_after == 0.0


@respx.mock
def test_retry_after_value_is_passed_to_sleep(
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr(
        "opensincera._client.time.sleep",
        lambda s: sleep_calls.append(s),
    )
    respx.get(f"{_API_BASE}/publishers").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "2"}),
            httpx.Response(200, json=SAMPLE_PUBLISHER),
        ],
    )
    client.get_publisher_by_domain("any.com")
    assert sleep_calls == [2.0]


@respx.mock
def test_429_without_retry_after_uses_exponential_backoff(
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr(
        "opensincera._client.time.sleep",
        lambda s: sleep_calls.append(s),
    )
    respx.get(f"{_API_BASE}/publishers").mock(
        side_effect=[
            httpx.Response(429),  # no Retry-After header
            httpx.Response(429),
            httpx.Response(200, json=SAMPLE_PUBLISHER),
        ],
    )
    client.get_publisher_by_domain("any.com")
    # Two retries -> two sleeps; both should be > 0 and the second >= the first
    # (capped exponential backoff).
    assert len(sleep_calls) == 2
    assert sleep_calls[0] > 0
    assert sleep_calls[1] >= sleep_calls[0]
