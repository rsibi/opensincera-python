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
