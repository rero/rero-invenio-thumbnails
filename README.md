<!--
SPDX-FileCopyrightText: Fondation RERO+
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# rero-invenio-thumbnails

[![CI](https://github.com/rero/rero-invenio-thumbnails/workflows/CI/badge.svg)](https://github.com/rero/rero-invenio-thumbnails/actions?query=workflow%3ACI)
[![GitHub tag](https://img.shields.io/github/tag/rero/rero-invenio-thumbnails.svg)](https://github.com/rero/rero-invenio-thumbnails/releases)
[![PyPI downloads](https://img.shields.io/pypi/dm/rero-invenio-thumbnails.svg)](https://pypi.python.org/pypi/rero-invenio-thumbnails)
[![License](https://img.shields.io/github/license/rero/rero-invenio-thumbnails.svg)](https://github.com/rero/rero-invenio-thumbnails/blob/staging/LICENSE)
[![Coveralls](https://coveralls.io/repos/github/rero/rero-invenio-thumbnails/badge.svg?branch=staging)](https://coveralls.io/github/rero/rero-invenio-thumbnails?branch=staging)
[![uv managed](https://img.shields.io/badge/uv-managed-FF6F00?logo=data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%2016%2016%22%3E%3Cpath%20fill=%22%23FFFFFF%22%20d=%22M8%200L0%208v8h16V8L8%200z%22/%3E%3C/svg%3E)](https://github.com/astral-sh/uv)

RERO Invenio extension to discover book thumbnail URLs from multiple providers.

## Features

- **Multiple Providers**: Chainable providers query external services in order and return the first available thumbnail URL
- **Built-in Providers**: FilesProvider (local files), GoogleBooksProvider, GoogleApiProvider, AmazonProvider, DnbProvider, BnfProvider, InternetArchiveProvider, OpenLibraryProvider
- **Plugin Architecture**: Extensible via entry points - register custom providers without modifying core code
- **Smart Caching**: Redis-based caching with configurable TTL
- **RESTful API**: JSON endpoint for thumbnail URL retrieval

## Custom Providers

You can register custom thumbnail providers via entry points. Create a provider
that inherits from `BaseProvider`:

```python
from rero_invenio_thumbnails.contrib.api import BaseProvider


class MyCustomProvider(BaseProvider):
    def get_thumbnail_url(self, isbn):
        # Your implementation here
        url = f"https://example.com/covers/{isbn}.jpg"
        return (url, "custom")
```

Register it in your `pyproject.toml`:

```toml
[project.entry-points."rero_invenio_thumbnails.providers"]
custom = "my_package.providers:MyCustomProvider"
```

Then reference it in your configuration:

```python
RERO_INVENIO_THUMBNAILS_PROVIDERS = ["custom", "files", "open library"]
```

## Quick start

Install:

```bash
pip install rero-invenio-thumbnails
```

Configure the providers and files dir in your application config:

```python
# Provider configuration (optional - if not set, all discovered providers are used)
RERO_INVENIO_THUMBNAILS_PROVIDERS = [
    "files",
    "google books",
    "google api",
    "amazon",
    "bnf",
    "internet archive",
    "open library",
]

# Files provider configuration
RERO_INVENIO_THUMBNAILS_FILES_DIR = "/path/to/thumbnails"

# Cache configuration
RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE = 3600
```

> **DNB / MVB license requirement**: The `dnb` provider is **not** enabled by
> default. Its cover images are sourced from VLB (Verzeichnis Lieferbarer
> Bücher, operated by MVB GmbH) and are subject to copyright. To enable it,
> add `"dnb"` to your instance-specific `RERO_INVENIO_THUMBNAILS_PROVIDERS`
> list. A valid data licence agreement with MVB is required.
> Contact: kundenservice@mvb-online.de

Initialize the extension:

```python
from rero_invenio_thumbnails import REROInvenioThumbnails

ext = REROInvenioThumbnails()
ext.init_app(app)
```

## API

Get a thumbnail URL for an ISBN:

```python
from rero_invenio_thumbnails.api import get_thumbnail_url

# Returns a tuple: (url, provider_name)
url, provider = get_thumbnail_url("9780134685991")
print(f"Found thumbnail at {url} from {provider}")
```

## HTTP Endpoints

**GET /thumbnails-url/\<isbn\>** - Returns JSON with thumbnail URL

Returns JSON containing the thumbnail URL and provider name if found, or 404 if no thumbnail is available:

```json
{
    "url": "https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg",
    "isbn": "9780134685991",
    "provider": "open library"
}
```

Example:

```bash
curl http://localhost/thumbnails-url/9780134685991
```

**GET /thumbnails/\<isbn\>** - Serves the actual thumbnail image file

Returns the thumbnail image file directly from local storage with appropriate MIME type (image/jpeg or image/png).
Supports client-side caching with ETag and Last-Modified headers, along with conditional requests
(If-None-Match, If-Modified-Since) returning 304 Not Modified when appropriate. Returns 404 if the file is not found.

Example:

```bash
# First request - returns 200 with ETag and Last-Modified headers
curl -v http://localhost/thumbnails/9780134685991 -o thumbnail.jpg

# Subsequent requests can use conditional headers for efficient caching
curl -H "If-None-Match: \"abc123...\"" http://localhost/thumbnails/9780134685991
```

## Testing

Run the test-suite using the project's uv-based tooling:

```bash
uv sync
uv run poe run_tests
```

## Contributing

Contributions are welcome. Please follow the repository [CONTRIBUTING.md](CONTRIBUTING.md) and
open pull requests against the `staging` branch.
