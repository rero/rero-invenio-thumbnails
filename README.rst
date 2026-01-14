..
    RERO Invenio Thumbnails
    Copyright (C) 2026 RERO.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

=========================
rero-invenio-thumbnails
=========================

.. image:: https://github.com/rero/rero-invenio-thumbnails/workflows/CI/badge.svg
        :target: https://github.com/rero/rero-invenio-thumbnails/actions?query=workflow%3ACI

.. image:: https://img.shields.io/github/tag/rero/rero-invenio-thumbnails.svg
        :target: https://github.com/rero/rero-invenio-thumbnails/releases

.. image:: https://img.shields.io/pypi/dm/rero-invenio-thumbnails.svg
        :target: https://pypi.python.org/pypi/rero-invenio-thumbnails

.. image:: https://img.shields.io/github/license/rero/rero-invenio-thumbnails.svg
        :target: https://github.com/rero/rero-invenio-thumbnails/blob/master/LICENSE

.. image:: https://coveralls.io/repos/github/rero/rero-invenio-thumbnails/badge.svg?branch=master
        :target: https://coveralls.io/github/rero/rero-invenio-thumbnails?branch=master

.. image:: https://img.shields.io/badge/uv-managed-FF6F00?logo=data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%2016%2016%22%3E%3Cpath%20fill=%22%23FFFFFF%22%20d=%22M8%200L0%208v8h16V8L8%200z%22/%3E%3C/svg%3E
        :target: https://github.com/astral-sh/uv


RERO Invenio extension to discover book thumbnail URLs from multiple
providers.

Features
--------

- **Multiple Providers**: Chainable providers query external services in order and return the first available thumbnail URL
- **Built-in Providers**: FilesProvider (local files), OpenLibraryProvider, BnfProvider, DnbProvider, GoogleBooksProvider, GoogleApiProvider
- **Plugin Architecture**: Extensible via entry points - register custom providers without modifying core code
- **Smart Caching**: Redis-based caching with configurable TTL
- **Robust HTTP Handling**: Configurable retry logic with exponential backoff for external providers
- **RESTful API**: JSON endpoint for thumbnail URL retrieval

Custom Providers
----------------

You can register custom thumbnail providers via entry points. Create a provider
that inherits from `BaseProvider`::

        from rero_invenio_thumbnails.modules.api import BaseProvider

        class MyCustomProvider(BaseProvider):
            def get_thumbnail_url(self, isbn):
                # Your implementation here
                url = f"https://example.com/covers/{isbn}.jpg"
                return (url, "custom")

Register it in your `pyproject.toml`::

        [project.entry-points."rero_invenio_thumbnails.providers"]
        custom = "my_package.providers:MyCustomProvider"

Then reference it in your configuration::

        RERO_INVENIO_THUMBNAILS_PROVIDERS = ["custom", "files", "open library"]

Quick start
-----------

Install::

        $ pip install rero-invenio-thumbnails

Configure the providers and files dir in your application config::

        # Provider configuration (optional - if not set, all discovered providers are used)
        RERO_INVENIO_THUMBNAILS_PROVIDERS = ["files", "open library", "bnf", "dnb", "google books", "google api"]

        # Files provider configuration
        RERO_INVENIO_THUMBNAILS_FILES_DIR = "/path/to/thumbnails"

        # Cache configuration
        RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE = 3600

        # Retry config (defaults shown)
        RERO_INVENIO_THUMBNAILS_RETRY_ENABLED = True
        RERO_INVENIO_THUMBNAILS_RETRY_ATTEMPTS = 5
        RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MULTIPLIER = 0.5
        RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MIN = 1
        RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MAX = 10
        # Disable retries globally via env (e.g., for tests)
        # export RERO_THUMBNAILS_DISABLE_RETRIES=true

Initialize the extension::

        from rero_invenio_thumbnails import REROInvenioThumbnails

        ext = REROInvenioThumbnails()
        ext.init_app(app)

API
---

Get a thumbnail URL for an ISBN::

        from rero_invenio_thumbnails.api import get_thumbnail_url

        # Returns a tuple: (url, provider_name)
        url, provider = get_thumbnail_url("9780134685991")
        print(f"Found thumbnail at {url} from {provider}")

HTTP Endpoints
--------------

**GET /thumbnails-url/<isbn>** - Returns JSON with thumbnail URL

Returns JSON containing the thumbnail URL and provider name if found, or 404 if no thumbnail is available::

        {
            "url": "https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg",
            "isbn": "9780134685991",
            "provider": "open library"
        }

Example::

        curl http://localhost/thumbnails-url/9780134685991

**GET /thumbnails/<isbn>** - Serves the actual thumbnail image file

Returns the thumbnail image file directly from local storage with appropriate MIME type (image/jpeg or image/png). 
Supports client-side caching with ETag and Last-Modified headers, along with conditional requests 
(If-None-Match, If-Modified-Since) returning 304 Not Modified when appropriate. Returns 404 if the file is not found.

Example::

        # First request - returns 200 with ETag and Last-Modified headers
        curl -v http://localhost/thumbnails/9780134685991 -o thumbnail.jpg

        # Subsequent requests can use conditional headers for efficient caching
        curl -H "If-None-Match: \"abc123...\"" http://localhost/thumbnails/9780134685991

Testing
-------

Run the test-suite with `pytest`::

        $ pip install -r requirements.txt
        $ pytest

Contributing
------------

Contributions are welcome. Please follow the repository `CONTRIBUTING.rst` and
open pull requests against the `master` branch.

License
-------

This project is licensed under the terms of the MIT License. See the
LICENSE file for details.

Further documentation is available at:

https://rero-invenio-thumbnails.readthedocs.io/
