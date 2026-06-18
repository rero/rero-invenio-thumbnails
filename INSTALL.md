<!--
SPDX-FileCopyrightText: Fondation RERO+
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Installation

This package provides a lightweight Invenio extension to retrieve and serve
book thumbnails from multiple providers (local files, Open Library, Google
Books).

## Prerequisites

- Python >=3.12, <3.13
- Redis (optional, for caching) if you want to enable `invenio_cache`

## Quick install

Install from PyPI:

```bash
pip install rero-invenio-thumbnails
```

Or install in editable mode for development:

```bash
pip install -e .
```

## Configuration

Add the extension and configure the available providers and files directory
in your Flask/Invenio configuration:

```python
RERO_INVENIO_THUMBNAILS_PROVIDERS = [
    "files",
    "google books",
    "google api",
    "amazon",
    "bnf",
    "internet archive",
    "open library",
]

# Directory used by FilesProvider
RERO_INVENIO_THUMBNAILS_FILES_DIR = "/path/to/thumbnails"
RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE = 3600
```

> **DNB / MVB licence requirement**: The `dnb` provider is **not** enabled by
> default. Its cover images are sourced from VLB (Verzeichnis Lieferbarer
> Bücher, operated by MVB GmbH) and are subject to copyright. To enable it,
> add `"dnb"` to your instance-specific `RERO_INVENIO_THUMBNAILS_PROVIDERS`
> list. A valid data licence agreement with MVB is required.
> Contact: kundenservice@mvb-online.de

## Application integration

In your application factory or initialization code, register the extension
and its blueprint:

```python
from rero_invenio_thumbnails import REROInvenioThumbnails

ext = REROInvenioThumbnails()
ext.init_app(app)
```

## Testing

Run the test-suite using the project's uv-based tooling:

```bash
uv sync
uv run poe run_tests
```
