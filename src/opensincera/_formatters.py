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


_IDENTIFIER_FIELDS: tuple[str, ...] = ("publisher_id", "name", "domain")


def prepare_record(
    publisher: Publisher,
    *,
    device: str | None = None,
    fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Return the dict to render, applying ``--device`` and ``--field`` rules.

    With ``device`` set, the result starts as the identifier fields plus the
    flattened metrics for that device block. With ``fields`` set, the result
    is filtered to those keys (in the order given). When both are set, the
    identifier fields are always preserved regardless of ``fields``.
    """
    data = publisher.model_dump(mode="json")
    if device is not None:
        identifiers = {k: data[k] for k in _IDENTIFIER_FIELDS if k in data}
        device_block = (data.get("device_level_metrics") or {}).get(device) or {}
        data = {**identifiers, **device_block}
    if fields:
        if device is not None:
            preserved = {k: data[k] for k in _IDENTIFIER_FIELDS if k in data}
            projected = {k: data[k] for k in fields if k in data and k not in preserved}
            data = {**preserved, **projected}
        else:
            data = {k: data[k] for k in fields if k in data}
    return data


def render_publisher(
    publisher: Publisher,
    fmt: OutputFormat,
    *,
    out: IO[str],
) -> None:
    """Render `publisher` to `out` in the chosen format."""
    render_record(prepare_record(publisher), fmt, out=out)


def render_record(
    record: dict[str, Any],
    fmt: OutputFormat,
    *,
    out: IO[str],
) -> None:
    """Render a pre-projected dict to `out` in the chosen format."""
    if fmt is OutputFormat.JSON:
        _render_json(record, out)
    elif fmt is OutputFormat.CSV:
        _render_csv(record, out)
    elif fmt is OutputFormat.TABLE:
        _render_table(record, out)


def _render_json(record: dict[str, Any], out: IO[str]) -> None:
    out.write(json.dumps(record, indent=2, default=str))
    out.write("\n")


def _render_csv(record: dict[str, Any], out: IO[str]) -> None:
    row = {key: _csv_cell(value) for key, value in record.items()}
    writer = csv.DictWriter(out, fieldnames=list(row.keys()))
    writer.writeheader()
    writer.writerow(row)


def _render_table(record: dict[str, Any], out: IO[str]) -> None:
    console = Console(file=out, force_terminal=False)
    table = Table(show_header=True, header_style="bold")
    table.add_column("Field")
    table.add_column("Value", overflow="fold")
    for key, value in record.items():
        table.add_row(key, _csv_cell(value))
    console.print(table)


def _csv_cell(value: Any) -> str:
    if isinstance(value, dict | list):
        return json.dumps(value, separators=(",", ":"))
    return str(value)
