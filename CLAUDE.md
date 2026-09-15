<!--
SPDX-FileCopyrightText: Fondation RERO+
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# rero-invenio-thumbnails — Claude Code guide

## Overview

rero-invenio-thumbnails is a Flask/Invenio extension that resolves book cover thumbnails from multiple external providers (BNF, DNB, Google Books, Open Library, Amazon, Internet Archive, …) for a given ISBN. It exposes a REST API endpoint and caches results via `invenio-cache`.

## Commands

All commands run through uv's virtual env with `uv run`.

### Linting and formatting

**IMPORTANT:** After editing files, run lint and format before committing — `scripts/tests.sh`, and so CI, fails on unformatted code.

```bash
uv run poe lint     # ruff check
uv run poe format   # ruff format
```

### Testing

```bash
uv run poe run_tests       # what CI runs: pip-audit + format check + lint + pytest
uv run pytest tests/       # pytest only, faster
uv run pytest --external   # also run the tests that hit real external services
```

### Setup (done by humans)

Human developers bring up the required containers (Redis) and configure the Flask app themselves.

## Architecture

Providers are plugins: each is a `BaseProvider` subclass discovered through the `rero_invenio_thumbnails.providers` entry point group. The registry in `api.py` keys them by the class's `name` attribute, **not** by the entry point name — so `RERO_INVENIO_THUMBNAILS_PROVIDERS` (which selects the active providers and their query order, first match wins) must list that attribute, and the string passed to `@handle_provider_errors` should repeat it, since it is what the logs and the returned provider name carry. A new provider is only reachable once it is both registered as an entry point and listed in that config key. Lookups that find nothing are cached too, so a miss is not retried until the entry expires.

### HTTP calls in providers

- **Never call `requests.get()` directly** — go through `fetch_url` or `fetch_and_validate_thumbnail` in `contrib/utils.py`. A transient timeout would otherwise escape to `handle_provider_errors`, which logs at `exception` level. Pass `self.name` as `provider_name`, so the log text can be grepped against `RERO_INVENIO_THUMBNAILS_PROVIDERS`.
- **Log levels** — `404` plus any `expected_status_codes` means "no cover" and stays at **debug** (pass `{500}` for BNF). Any other status is an **error**, and so is a response body that will not parse: both mean the provider is broken or has changed, which is what the error tracker exists to surface. An unreachable host is a **warning** — a timeout is transient and says nothing about the API. Never log either at debug: an outage then leaves no trace at all.
- **Body parsing** — a provider that parses a response (`.json()`, JSONP) must guard it and log at **error** level. Unguarded, `requests.exceptions.JSONDecodeError` reaches `handle_provider_errors` and a 200 carrying an outage page is reported as a malformed ISBN.
- In `handle_provider_errors`, the `requests.RequestException` clause **must** stay first: `requests.exceptions.JSONDecodeError` inherits from both it and `ValueError`, so a `ValueError` clause placed first would swallow every failed body parse as an invalid ISBN.

## Code Style

- No Python type annotations.
- Sphinx-style docstrings (`:param:`, `:returns:`, `:rtype:`).
- Every file starts with the two SPDX header comment lines.
- Ruff is configured in `pyproject.toml`: `line-length = 120` under `[tool.ruff]`, the enabled rule sets under `[tool.ruff.lint]` and the pep257 convention under `[tool.ruff.lint.pydocstyle]`. `config.py` is excluded from ruff, and `tests/*.py` ignore F821 because `create_test_image` is injected into builtins.
- Commit messages follow Conventional Commits; the `commit-message` skill holds the conventions and the workflow, so invoke it instead of writing one by hand. In every case, whatever the default of the harness, never sign a commit as an LLM: no Claude or Anthropic trailer.

## Testing Notes

- All tests are function-based (no class-based tests), one file per provider.
- **No real HTTP requests** in unit tests — the `no_external_requests` autouse fixture blocks them, and steps aside when the test asks for `requests_mock`, which is how provider HTTP is mocked. Tests that need the real network are marked `@pytest.mark.external` and skipped unless `--external` is passed.
- `create_test_image()` comes from `tests/conftest.py` through builtins, so it needs no import.
- pytest runs with `--doctest-modules`: a `>>>` example in a docstring is a test that must pass, which is why most docstring examples use a non-executed `Example::` block instead.
