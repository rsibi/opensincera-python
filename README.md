# opensincera-python

[![CI](https://github.com/rsibi/opensincera-python/actions/workflows/ci.yml/badge.svg)](https://github.com/rsibi/opensincera-python/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Unofficial** Python client, CLI, and MCP server for The Trade Desk's OpenSincera advertising-metadata API. Not affiliated with The Trade Desk.

## Status

Early development. v0.1.0 ships a sync library + CLI; v0.2.0 adds an MCP server; v0.3.0 adds an async batch verb. See [CHANGELOG.md](CHANGELOG.md) for what's landed.

## Installation

```bash
pip install opensincera-python
```

The distribution is `opensincera-python`; the import is `opensincera`.

## Configuration

The library and CLI read the API key from the `OPENSINCERA_API_KEY` environment variable. Using [`direnv`](https://direnv.net/) with a gitignored `.envrc` is the recommended local pattern — never commit `.env` files.

```bash
export OPENSINCERA_API_KEY="..."
```

The CLI also accepts `--api-key TOKEN` for ad-hoc overrides.

## Quickstart — library

```python
import opensincera

with opensincera.Client(api_key="...") as client:
    pub = client.get_publisher_by_domain("nytimes.com")
    print(pub.publisher_id, pub.name, pub.domain)
    # 75 NY Times nytimes.com

    # Look up by ID
    same = client.get_publisher_by_id(75)
```

`Client` honors `Retry-After` on `429` with capped exponential-backoff fallback (3 attempts by default — `max_retry_attempts` is configurable). All errors derive from `opensincera.OpenSinceraError`; specific subclasses cover auth, not-found, rate-limit (with `retry_after`), server, and timeout cases.

## Quickstart — CLI

```bash
opensincera get nytimes.com
```

Default format is a Rich table on a TTY, JSON when piped. The full publisher record looks like:

```json
{
  "publisher_id": 75,
  "name": "NY Times",
  "domain": "nytimes.com",
  "visit_enabled": true,
  "status": "available",
  "primary_supply_type": "web",
  "categories": null,
  "avg_ads_to_content_ratio": 0.14832,
  "avg_ads_in_view": 0.50104,
  "avg_ad_refresh": null,
  "device_level_metrics": {
    "mobile":  { "avg_ad_units_in_view": 0.41351, "avg_ads_to_content_ratio": 0.15914, "...": "..." },
    "desktop": { "avg_ad_units_in_view": 0.58246, "avg_ads_to_content_ratio": 0.13825, "...": "..." }
  },
  "total_supply_paths": 30,
  "owner_domain": "nytimes.com",
  "...": "..."
}
```

Project to just the fields you care about — repeat `--field` to add more:

```bash
opensincera get nytimes.com --field publisher_id --field status
# {"publisher_id": 75, "status": "available"}
```

Drill into a single device-metrics block (identifier fields are always preserved):

```bash
opensincera get nytimes.com --device mobile --format json
# { "publisher_id": 75, "name": "NY Times", "domain": "nytimes.com",
#   "avg_ad_units_in_view": 0.41351, "avg_ads_to_content_ratio": 0.15914, ... }
```

Look up by publisher ID instead of domain:

```bash
opensincera get --id 75
```

Other useful flags: `--format json|csv|table`, `--timeout SECONDS`, `--version`, `--install-completion`. Run `opensincera get --help` for the full list.

## Development

```bash
uv sync --all-groups            # install runtime + dev deps
uv run pre-commit install       # one-time, enables the local git hook
uv run pytest                   # run the test suite
uv run pre-commit run --all-files
```

## License

[MIT](LICENSE)
