"""Output renderers for the opensincera CLI.

Three formats are supported:

- `JSON` — pretty-printed, machine-readable; the default when stdout is not a TTY.
- `TABLE` — Rich-rendered "field / value" two-column table; the default on a TTY.
- `CSV` — single header row + single data row. Nested fields (e.g. dicts/lists)
  are serialized as compact JSON strings so the output remains a valid CSV row.

The `auto_format()` helper picks between TABLE and JSON based on TTY-ness.
"""

from __future__ import annotations

import csv
import json
from enum import StrEnum
from typing import IO, Any

from rich.console import Console
from rich.table import Table

from opensincera._models import Publisher


class OutputFormat(StrEnum):
    """Output format selectable via the CLI's ``--format`` flag."""

    JSON = "json"
    CSV = "csv"
    TABLE = "table"


def auto_format(*, stdout_is_tty: bool) -> OutputFormat:
    """Return the default format for the current environment."""
    return OutputFormat.TABLE if stdout_is_tty else OutputFormat.JSON


def render_publisher(
    publisher: Publisher,
    fmt: OutputFormat,
    *,
    out: IO[str],
) -> None:
    """Render `publisher` to `out` in the chosen format."""
    if fmt is OutputFormat.JSON:
        _render_json(publisher, out)
    elif fmt is OutputFormat.CSV:
        _render_csv(publisher, out)
    elif fmt is OutputFormat.TABLE:
        _render_table(publisher, out)


def _render_json(publisher: Publisher, out: IO[str]) -> None:
    out.write(publisher.model_dump_json(indent=2))
    out.write("\n")


def _render_csv(publisher: Publisher, out: IO[str]) -> None:
    data = publisher.model_dump(mode="json")
    row = {key: _csv_cell(value) for key, value in data.items()}
    writer = csv.DictWriter(out, fieldnames=list(row.keys()))
    writer.writeheader()
    writer.writerow(row)


def _render_table(publisher: Publisher, out: IO[str]) -> None:
    console = Console(file=out, force_terminal=False)
    table = Table(show_header=True, header_style="bold")
    table.add_column("Field")
    table.add_column("Value", overflow="fold")
    for key, value in publisher.model_dump(mode="json").items():
        table.add_row(key, _csv_cell(value))
    console.print(table)


def _csv_cell(value: Any) -> str:
    if isinstance(value, dict | list):
        return json.dumps(value, separators=(",", ":"))
    return str(value)
