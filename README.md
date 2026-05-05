# opensincera-python

[![CI](https://github.com/rsibi/opensincera-python/actions/workflows/ci.yml/badge.svg)](https://github.com/rsibi/opensincera-python/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Unofficial** Python client, CLI, and MCP server for The Trade Desk's OpenSincera advertising-metadata API. Not affiliated with The Trade Desk.

## Status

Early development. v0.1.0 ships a sync library + CLI; v0.2.0 adds an MCP server; v0.3.0 adds an async batch verb. See [CHANGELOG.md](CHANGELOG.md) for what's landed.

## Installation

```bash
pip install opensincera-python  # not yet on PyPI
```

The distribution is `opensincera-python`; the import is `opensincera`.

## Quickstart

_Filled in at v0.1.0._

## Configuration

The library reads the API key from the `OPENSINCERA_API_KEY` environment variable. Using [`direnv`](https://direnv.net/) with a gitignored `.envrc` is the recommended local pattern — never commit `.env` files.

```bash
export OPENSINCERA_API_KEY="..."
```

## Development

```bash
uv sync --all-groups            # install runtime + dev deps
uv run pre-commit install       # one-time, enables the local git hook
uv run pytest                   # run the test suite
uv run pre-commit run --all-files
```

## License

[MIT](LICENSE)
