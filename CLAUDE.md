# Repo conventions for future agentic sessions

Quick orientation for Claude (and humans) working in this repo. The full roadmap lives in `PLAN.md` (gitignored, local-only) — this file captures what's load-bearing across sessions.

## What this is

`opensincera-python` — Python client, CLI (v0.1), and MCP server (v0.2) for The Trade Desk's OpenSincera advertising-metadata API. Unofficial; the distribution is `opensincera-python` while the import name stays `opensincera`.

## Local commands

```bash
uv sync --all-groups           # install runtime + dev deps
uv run pre-commit install      # one-time after clone
uv run pytest                  # tests
uv run ruff check .            # lint
uv run ruff format .           # apply formatting
uv run pre-commit run --all-files
```

## Toolchain

- **uv** — env + packaging. `uv_build` backend with a `module-name` override (distribution `opensincera-python`, import `opensincera`).
- **pytest** — tests live in `tests/`.
- **ruff** — lint + format. Ruleset `E F I B UP SIM RUF N`, line length 100, target Python 3.11.
- **pre-commit** — ruff plus hygiene hooks (trailing whitespace, EOF, TOML/YAML validity, merge-conflict guard).
- **GitHub Actions** — CI runs pre-commit + pytest on every push to `main` and PR.
- **Dependabot** — weekly bumps for `pip` + `github-actions`, patch/minor grouped.

## Deliberately *not* in the toolchain

- **mypy** — re-add at M1 when `_client.py` + `_models.py` land. Until then, type hints in source are for IDE help only, with no enforcement.
- gitleaks, CodeQL, Codecov, pip-audit, SECURITY.md, branch protection — all cut as overkill at this size. Revisit if a real failure mode shows up.

## Conventions

- **Commits:** Conventional Commits style (`feat:`, `fix:`, `chore:`, `docs:`, `ci:`). Habit, not enforced.
- **No co-author trailers:** never append `Co-Authored-By: Claude ...` (or any AI co-author) to commit messages.
- **TDD:** for production code in `src/`, write the failing test first. Throwaway scaffolding is exempt — currently the `__main__.py` placeholder, which gets replaced at M2.
- **Public API:** what `src/opensincera/__init__.py` re-exports via `__all__`. Underscore-prefixed modules (`_client.py`, `_models.py`, ...) are implementation detail.
- **Logging:** library code uses `logging.getLogger(__name__)`. Never `print` from inside the library; the CLI entry point is the only place stdout/stderr writes are appropriate.
- **Versioning:** SemVer; `__version__` reads from installed distribution metadata via `importlib.metadata`.

## Gitignored / local-only files

- `PLAN.md` — private roadmap. Do not commit.
- `.envrc` — direnv config holding `OPENSINCERA_API_KEY`. Do not commit.
- `.claude/settings.local.json` — local Claude Code settings.
