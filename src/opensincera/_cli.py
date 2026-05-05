"""Typer-based CLI for the opensincera package.

Exposes a single `get` verb with two ways to specify the publisher
(`<domain>` positional or `--id <publisher_id>`). The `main()` function is
wired up as the `opensincera` console script via `[project.scripts]` in
pyproject.toml.

Output format is selectable via `--format` (json / csv / table) and
defaults to TABLE when stdout is a TTY, JSON otherwise.
"""

from __future__ import annotations

import os
import sys
from typing import Annotated

import typer

from opensincera import __version__
from opensincera._client import Client
from opensincera._formatters import OutputFormat, auto_format, render_publisher
from opensincera.errors import OpenSinceraError

_API_KEY_ENV_VAR = "OPENSINCERA_API_KEY"

app = typer.Typer(
    name="opensincera",
    help="Python CLI for The Trade Desk's OpenSincera advertising-metadata API.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit


@app.callback()
def _main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the installed version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None: ...


@app.command()
def get(
    domain: Annotated[
        str | None,
        typer.Argument(
            help="Publisher base domain, e.g. nytimes.com.",
        ),
    ] = None,
    publisher_id: Annotated[
        int | None,
        typer.Option(
            "--id",
            help="Publisher ID to look up. Mutually exclusive with DOMAIN.",
        ),
    ] = None,
    fmt: Annotated[
        OutputFormat | None,
        typer.Option(
            "--format",
            help="Output format. Defaults to TABLE on a TTY, JSON when piped.",
        ),
    ] = None,
) -> None:
    """Fetch publisher metadata by domain or by ID."""
    if (domain is None) == (publisher_id is None):
        raise typer.BadParameter("provide exactly one of DOMAIN or --id")

    api_key = os.environ.get(_API_KEY_ENV_VAR)
    if not api_key:
        typer.echo(
            f"error: {_API_KEY_ENV_VAR} environment variable is required",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        with Client(api_key=api_key) as client:
            pub = (
                client.get_publisher_by_id(publisher_id)
                if publisher_id is not None
                else client.get_publisher_by_domain(domain)  # type: ignore[arg-type]
            )
    except OpenSinceraError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    resolved = fmt or auto_format(stdout_is_tty=sys.stdout.isatty())
    render_publisher(pub, resolved, out=sys.stdout)


def main() -> None:
    app()
