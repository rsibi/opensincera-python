# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- `Publisher` no longer raises `ValidationError` when the API returns `null` for fields like `categories`, `avg_ad_refresh`, or any refresh-rate inside `device_level_metrics` (real responses do this for many publishers — the docs' example happened to be fully populated). Only `publisher_id`, `name`, and `domain` are now strictly required; everything else defaults to `None`.
- `Client` now wraps `pydantic.ValidationError` as `OpenSinceraError` so callers don't have to catch a non-library exception type for schema-drift failures.

### Added
- `opensincera.__version__` exposed via `importlib.metadata`.
- Exception hierarchy under `opensincera.errors` (also re-exported at the package top level): `OpenSinceraError` (base), `AuthError` (401), `NotFoundError` (404), `RateLimitError` (429, with `retry_after`), `ServerError` (5xx), `TimeoutError` (wraps `httpx.TimeoutException`).
- Pydantic v2 response models — `opensincera.Publisher` and `opensincera.DeviceMetrics` — covering the full schema documented for `GET /publishers?id=` / `?domain=`. Models accept unknown fields silently so future API additions don't break clients.
- Synchronous HTTP client `opensincera.Client` with `get_publisher_by_domain(domain)` and `get_publisher_by_id(publisher_id)`. Honors `Retry-After` on `429` with capped exponential-backoff fallback (default 3 attempts; `max_retry_attempts` configurable). Usable as a context manager.
- `opensincera` CLI (Typer-based): `opensincera get <domain>` and `opensincera get --id <id>` print the publisher. Reads the API key from the `OPENSINCERA_API_KEY` environment variable. `--version` and shell-completion install via `--install-completion` ship for free.
- `--format json|csv|table` flag on `opensincera get` plus a TTY-aware default (TABLE on a TTY, JSON when piped). Tables are Rich-rendered; CSV serializes nested fields as compact JSON in their cells.
