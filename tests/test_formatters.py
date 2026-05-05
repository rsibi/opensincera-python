"""Tests for `opensincera._formatters` — the output renderers used by the CLI."""

import io
import json

import pytest

from opensincera._formatters import OutputFormat, auto_format, render_publisher
from opensincera._models import Publisher
from tests.test_models import SAMPLE_PUBLISHER


@pytest.fixture
def publisher() -> Publisher:
    return Publisher.model_validate(SAMPLE_PUBLISHER)


class TestAutoFormat:
    def test_picks_table_on_a_tty(self) -> None:
        assert auto_format(stdout_is_tty=True) is OutputFormat.TABLE

    def test_picks_json_when_not_a_tty(self) -> None:
        assert auto_format(stdout_is_tty=False) is OutputFormat.JSON


class TestRenderJson:
    def test_round_trips_through_json_loads(self, publisher: Publisher) -> None:
        out = io.StringIO()
        render_publisher(publisher, OutputFormat.JSON, out=out)
        parsed = json.loads(out.getvalue())
        assert parsed["publisher_id"] == 1
        assert parsed["name"] == "Business Insider"


class TestRenderCsv:
    def test_has_header_row_and_data_row(self, publisher: Publisher) -> None:
        out = io.StringIO()
        render_publisher(publisher, OutputFormat.CSV, out=out)
        lines = out.getvalue().splitlines()
        assert lines[0].startswith("publisher_id,")
        assert "Business Insider" in lines[1]

    def test_renders_nested_fields_as_json_strings(self, publisher: Publisher) -> None:
        out = io.StringIO()
        render_publisher(publisher, OutputFormat.CSV, out=out)
        body = out.getvalue()
        # device_level_metrics is a nested dict — should serialize, not crash.
        assert "device_level_metrics" in body
        assert "average_refresh_rate" in body


class TestRenderTable:
    def test_includes_publisher_name(self, publisher: Publisher) -> None:
        out = io.StringIO()
        render_publisher(publisher, OutputFormat.TABLE, out=out)
        rendered = out.getvalue()
        assert "Business Insider" in rendered
        assert "publisher_id" in rendered
