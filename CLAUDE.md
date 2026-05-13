# rero-invenio-thumbnails — Claude Code guide

## Overview

rero-invenio-thumbnails is a Flask/Invenio extension that resolves book cover thumbnails from multiple external providers (BNF, DNB, Google Books, Open Library, Amazon, Internet Archive, …) for a given ISBN. It exposes a REST API endpoint and caches results via `invenio-cache`.

**Stack**: Python 3.12–3.14, Flask (Invenio), Redis (cache)
**Package manager**: `uv` with `poethepoet` for task running

## Commands

All commands run through uv's virtual env with `uv run`.

### Linting and formatting

**IMPORTANT:** After editing files, run lint and format before committing.

```bash
uv run poe lint     # ruff check
uv run poe format   # ruff format
```

### Testing

```bash
uv run poe run_tests       # full suite (pip-audit + format + lint + pytest)
uv run pytest tests/       # pytest only (faster, no audit/format step)
uv run pytest tests/test_bnf_provider.py                    # single file
uv run pytest tests/test_bnf_provider.py::test_bnf_init     # single test
uv run pytest --external   # include tests that hit real external services
```

Tests also run against doctests in the source (`--doctest-modules`).

### Setup (done by humans)

Human developers bring up the required containers (Redis) and configure the Flask app themselves.

## Architecture

### Provider system

Providers are registered as Python entry points under `rero_invenio_thumbnails.providers` in `pyproject.toml`. At runtime `REROInvenioThumbnails.init_app` loads them dynamically; `RERO_INVENIO_THUMBNAILS_PROVIDERS` in the app config controls which providers are active and their query order (first match wins).

```text
rero_invenio_thumbnails/
├── api.py                    # get_thumbnail_url() — iterates providers, handles cache
├── config.py                 # All RERO_INVENIO_THUMBNAILS_* config keys
├── ext.py                    # Invenio extension, loads providers from entry points
├── views.py                  # Flask blueprint — /api/thumbnails/<isbn> endpoint
└── contrib/
    ├── api.py                # BaseProvider abstract class
    ├── utils.py              # clean_isbn, fetch_and_validate_thumbnail, validate_image_content, clean_all_cache
    ├── bnf/api.py            # BNF (openapi.bnf.fr)
    ├── dnb/api.py            # DNB via MVB cover URL (requires paid licence — disabled by default)
    ├── files/api.py          # Local filesystem fallback
    ├── google_api/api.py     # Google Books API (requires API key)
    ├── google_books/api.py   # Google Books scrape
    ├── internet_archive/     # Internet Archive Open Library covers
    ├── open_library/api.py   # Open Library
    └── amazon/api.py         # Amazon product images
```

### Adding a new provider

1. Create `rero_invenio_thumbnails/contrib/<name>/api.py` with a class inheriting `BaseProvider`.
2. Implement `get_thumbnail_url(self, isbn) -> tuple[str | None, str]` decorated with `@handle_provider_errors("<Name>")`.
3. Register it as an entry point in `pyproject.toml` under `[project.entry-points."rero_invenio_thumbnails.providers"]`.
4. Add the provider name to `RERO_INVENIO_THUMBNAILS_PROVIDERS` in `config.py` if it should be on by default.

### Key utilities (`contrib/utils.py`)

- **`clean_isbn(isbn)`** — strips hyphens and spaces.
- **`fetch_and_validate_thumbnail(url, provider_name, isbn, *, timeout, headers, expected_status_codes)`** — fetches the URL, validates the HTTP status and image content (dimensions ≥ `RERO_INVENIO_THUMBNAILS_MIN_IMAGE_DIMENSION`). Pass `expected_status_codes={500}` for providers like BNF that return 500 when no cover exists — those are silenced at debug level instead of logged as errors.
- **`handle_provider_errors(provider_name)`** — decorator that catches `ValueError`, `requests.RequestException`, and unexpected exceptions and returns `(None, provider_name.lower())`.
- **`validate_image_content(content, ...)`** — checks PIL can open the bytes and that both dimensions meet the minimum.
- **`clean_all_cache()`** — deletes all `rero_thumbnails_*` keys from the Redis cache via `scan_iter`.

## Code Style

- No Python type annotations.
- Sphinx-style docstrings (`:param:`, `:returns:`, `:rtype:`).
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org).
- Line length: 120 characters (enforced by ruff).

## Testing Notes

- All tests are function-based (no class-based tests).
- One test file per provider: `tests/test_<provider>_provider.py`.
- Shared fixtures and helpers in `tests/conftest.py`. `create_test_image()` is injected into builtins and available in all test files without importing.
- **No real HTTP requests** in unit tests — the `no_external_requests` autouse fixture blocks them. Use `requests_mock` for HTTP interactions.
- Tests that need the real network are marked `@pytest.mark.external` and skipped by default; run with `--external` to enable them.
- DNB is excluded from the default provider list (requires a paid MVB licence) — keep tests for it mocked.
