..
        Copyright (C) 2026 RERO.

        rero-invenio-thumbnails is free software; you can redistribute it
        and/or modify it under the terms of the MIT License; see LICENSE file for
        more details.

Changes
=======

Version 0.2.0 (unreleased)
--------------------------

**Breaking Changes:**

- **API Return Format Change**: All provider methods and `get_thumbnail_url()` now return 
  a tuple `(url, provider_name)` instead of just the URL. This provides transparency about 
  which provider supplied the thumbnail.
  
  Migration example::
  
    # Old code (v0.1.0)
    url = get_thumbnail_url("9780134685991")
    
    # New code (v0.2.0+)
    url, provider = get_thumbnail_url("9780134685991")

- **HTTP Response Format**: The `/thumbnails-url/<isbn>` endpoint now includes a `provider` 
  field in the JSON response::
  
    {
      "url": "https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg",
      "isbn": "9780134685991",
      "provider": "open library"
    }

**Improvements:**

- **New endpoint**: Added `/thumbnails/<isbn>` endpoint to serve actual thumbnail image 
  files directly from local storage (in addition to the existing `/thumbnails-url/<isbn>` 
  endpoint that returns JSON with URLs)
- **Client-side caching**: The `/thumbnails/<isbn>` endpoint now supports efficient 
  client-side caching with ETag and Last-Modified headers, plus conditional requests 
  (If-None-Match, If-Modified-Since) returning 304 Not Modified responses
- Cache entries now store provider information using JSON format (prevents issues with pipe characters in URLs)
- Use `RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE` constant from config.py consistently
- BNF and DNB providers now validate image content before returning URLs
- Improved error handling with provider attribution in error tuples
- Modernized exception handling using `contextlib.suppress` where appropriate

**Bug Fixes:**

- Fixed cache serialization to handle URLs containing pipe characters (`|`) by using JSON instead of pipe-delimited strings

0.1.0 (2026-01-15)
-------------------

Initial release

- Multi-provider thumbnail URL discovery system with fallback chain
- Six thumbnail providers:
    - Files: Serve from local filesystem directory
    - Open Library: Free, community-driven book cover database
    - BNF (Bibliothèque nationale de France): French national library covers
    - DNB (Deutsche Nationalbibliothek): German national library covers via SRU
    - Google Books API: Official Google Books API integration
    - Google Books: Google Books preview service
- Plugin-based architecture via entry points for custom providers
- Redis-based caching via `invenio_cache` with configurable TTL
- Flask blueprint with `/thumbnails-url/<isbn>` endpoint returning JSON
- HTTP retry logic with exponential backoff for external providers
- Configurable retry behavior via `RERO_INVENIO_THUMBNAILS_RETRY_*` settings
- Environment variable `RERO_THUMBNAILS_DISABLE_RETRIES` to disable retries globally
- Comprehensive test suite with 120 tests and 97% code coverage
- Full Sphinx documentation with API reference and usage examples
