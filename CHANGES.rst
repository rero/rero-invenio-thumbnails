..
        Copyright (C) 2026 RERO.

        rero-invenio-thumbnails is free software; you can redistribute it
        and/or modify it under the terms of the MIT License; see LICENSE file for
        more details.

Changes
=======

0.1.0 (2026-01-15)
-------------------

Initial release

- Add multi-provider thumbnail retrieval system
    - Providers: Files, OpenLibrary, Google Books API, Google Books preview, Amazon
    - Local `FilesProvider` for serving thumbnails from a configured directory
    - Flask blueprint endpoint to serve thumbnails: `/thumbnails/<isbn>`
    - Invenio extension with `init_app` and blueprint registration
    - Redis-based image caching via `invenio_cache` with TTL support
    - Dynamic image resizing with `width` and `height` query parameters
    - Dimension-aware caching (separate cache entries per size)
    - Optional cache control via `cached=false` parameter
    - Proportional scaling with aspect ratio preservation using PIL/Pillow
    - Retry logic for HTTP providers using exponential backoff
    - Graceful Redis connection error handling with fallback
    - Comprehensive test-suite covering providers, caching, and resizing (34 tests, 79% coverage)
    - Full reST/Sphinx docstring documentation with `:param:` format
    - Make HTTP retry/backoff configurable via application config
        (`RERO_INVENIO_THUMBNAILS_RETRY_*`) and allow disabling retries via
        the `RERO_THUMBNAILS_DISABLE_RETRIES` environment variable (useful in tests).
