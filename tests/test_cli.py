"""Tests for the Typer CLI in `opensincera._cli`.

CLI behavior is exercised end-to-end via Typer's CliRunner with the HTTP
layer mocked by respx, so these tests verify argument parsing, exit codes,
output, and dispatch — not Client internals (those live in test_client.py).
"""

import json

import httpx
import pytest
import respx
from typer.testing import CliRunner

from opensincera import __version__
from opensincera._cli import app
from tests.test_models import SAMPLE_PUBLISHER

_API_BASE = "https://open.sincera.io/api"

runner = CliRunner()


def test_version_flag_prints_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


@respx.mock
def test_get_domain_outputs_publisher_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers", params={"domain": "businessinsider.com"}).mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(app, ["get", "businessinsider.com"])
    assert result.exit_code == 0
    assert "Business Insider" in result.stdout
    assert '"publisher_id": 1' in result.stdout


@respx.mock
def test_get_by_id_outputs_publisher_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers", params={"id": "1"}).mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(app, ["get", "--id", "1"])
    assert result.exit_code == 0
    assert "Business Insider" in result.stdout


def test_missing_api_key_exits_non_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENSINCERA_API_KEY", raising=False)
    result = runner.invoke(app, ["get", "anything.com"])
    assert result.exit_code != 0
    combined = result.stdout + (result.stderr or "")
    assert "OPENSINCERA_API_KEY" in combined


@respx.mock
def test_auth_error_exits_non_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "bad-token")
    respx.get(f"{_API_BASE}/publishers").mock(return_value=httpx.Response(401))
    result = runner.invoke(app, ["get", "anything.com"])
    assert result.exit_code != 0


def test_neither_domain_nor_id_is_a_usage_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    result = runner.invoke(app, ["get"])
    assert result.exit_code != 0


def test_both_domain_and_id_is_a_usage_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    result = runner.invoke(app, ["get", "x.com", "--id", "1"])
    assert result.exit_code != 0


@respx.mock
def test_default_output_is_json_in_non_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """CliRunner's stdout isn't a TTY, so auto-format should pick JSON."""
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(app, ["get", "businessinsider.com"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["publisher_id"] == 1


@respx.mock
def test_format_csv_emits_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(app, ["get", "businessinsider.com", "--format", "csv"])
    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    assert lines[0].startswith("publisher_id,")
    assert "Business Insider" in lines[1]


@respx.mock
def test_format_table_includes_publisher_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(app, ["get", "businessinsider.com", "--format", "table"])
    assert result.exit_code == 0
    assert "Business Insider" in result.stdout
    assert "publisher_id" in result.stdout


@respx.mock
def test_api_key_flag_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "env-token")
    route = respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(
        app,
        ["get", "businessinsider.com", "--api-key", "flag-token"],
    )
    assert result.exit_code == 0
    assert route.called
    assert route.calls.last.request.headers["authorization"] == "Bearer flag-token"


@respx.mock
def test_api_key_flag_works_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENSINCERA_API_KEY", raising=False)
    route = respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(
        app,
        ["get", "businessinsider.com", "--api-key", "flag-token"],
    )
    assert result.exit_code == 0
    assert route.called
    assert route.calls.last.request.headers["authorization"] == "Bearer flag-token"


@respx.mock
def test_field_single_projects_one_key_in_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(
        app,
        ["get", "businessinsider.com", "--format", "json", "--field", "publisher_id"],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed == {"publisher_id": 1}


@respx.mock
def test_field_repeated_projects_multiple_in_listed_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(
        app,
        [
            "get",
            "businessinsider.com",
            "--format",
            "json",
            "--field",
            "status",
            "--field",
            "publisher_id",
        ],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert list(parsed.keys()) == ["status", "publisher_id"]
    assert parsed == {"status": "available", "publisher_id": 1}


@respx.mock
def test_field_projection_in_csv_format(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(
        app,
        [
            "get",
            "businessinsider.com",
            "--format",
            "csv",
            "--field",
            "publisher_id",
            "--field",
            "name",
        ],
    )
    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    assert lines[0] == "publisher_id,name"
    assert lines[1] == "1,Business Insider"


@respx.mock
def test_field_unknown_is_silently_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(
        app,
        [
            "get",
            "businessinsider.com",
            "--format",
            "json",
            "--field",
            "publisher_id",
            "--field",
            "no_such_field",
        ],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed == {"publisher_id": 1}


@respx.mock
def test_device_mobile_flattens_metrics_with_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(
        app,
        ["get", "businessinsider.com", "--format", "json", "--device", "mobile"],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["publisher_id"] == 1
    assert parsed["name"] == "Business Insider"
    assert parsed["domain"] == "businessinsider.com"
    assert parsed["average_refresh_rate"] == 53.704
    assert parsed["max_refresh_rate"] == 295.0
    assert "device_level_metrics" not in parsed
    # Non-identifier top-level fields should not leak through.
    assert "categories" not in parsed
    assert "avg_ads_to_content_ratio" in parsed
    assert parsed["avg_ads_to_content_ratio"] == 0.21721


@respx.mock
def test_device_desktop_picks_desktop_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(
        app,
        ["get", "businessinsider.com", "--format", "json", "--device", "desktop"],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["average_refresh_rate"] == 56.25
    assert parsed["max_refresh_rate"] == 205.0


def test_device_invalid_value_is_usage_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    result = runner.invoke(
        app,
        ["get", "businessinsider.com", "--device", "tablet"],
    )
    assert result.exit_code != 0


@respx.mock
def test_device_with_no_metrics_returns_identifiers_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    sparse = {
        "publisher_id": 99,
        "name": "Tiny Pub",
        "domain": "tiny.example",
    }
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=sparse),
    )
    result = runner.invoke(
        app,
        ["get", "tiny.example", "--format", "json", "--device", "mobile"],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed == {
        "publisher_id": 99,
        "name": "Tiny Pub",
        "domain": "tiny.example",
    }


@respx.mock
def test_device_and_field_compose_with_identifiers_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`--device mobile --field max_refresh_rate` keeps identifiers + the projected metric."""
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(
        app,
        [
            "get",
            "businessinsider.com",
            "--format",
            "json",
            "--device",
            "mobile",
            "--field",
            "max_refresh_rate",
        ],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed == {
        "publisher_id": 1,
        "name": "Business Insider",
        "domain": "businessinsider.com",
        "max_refresh_rate": 295.0,
    }


@respx.mock
def test_device_field_naming_identifier_keeps_only_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`--field publisher_id --device mobile`: top-level identifiers are always preserved."""
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    result = runner.invoke(
        app,
        [
            "get",
            "businessinsider.com",
            "--format",
            "json",
            "--device",
            "mobile",
            "--field",
            "publisher_id",
        ],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed == {
        "publisher_id": 1,
        "name": "Business Insider",
        "domain": "businessinsider.com",
    }


@respx.mock
def test_timeout_flag_propagates_to_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """--timeout SECONDS must be passed through to the underlying Client."""
    monkeypatch.setenv("OPENSINCERA_API_KEY", "test-token")
    respx.get(f"{_API_BASE}/publishers").mock(
        return_value=httpx.Response(200, json=SAMPLE_PUBLISHER),
    )
    captured: dict[str, float] = {}

    from opensincera import _cli as cli_module

    real_client = cli_module.Client

    def spy(*args: object, **kwargs: object) -> object:
        captured["timeout"] = kwargs.get("timeout")  # type: ignore[assignment]
        return real_client(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(cli_module, "Client", spy)
    result = runner.invoke(app, ["get", "businessinsider.com", "--timeout", "2.5"])
    assert result.exit_code == 0
    assert captured["timeout"] == 2.5
