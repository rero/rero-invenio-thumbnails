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


RERO Invenio extension to retrieve and serve book thumbnails from multiple
providers.

Features
--------

- **Multiple Providers**: Chainable providers query external services in order and return the first available thumbnail
- **Built-in Providers**: FilesProvider (local files), OpenLibraryProvider, GoogleApiProvider, GoogleBooksProvider, AmazonProvider
- **Image Validation**: Filters out 1x1 pixel placeholders and invalid images (minimum 10x10 pixels)
- **Smart Caching**: Redis-based caching via invenio_cache with configurable TTL
- **Dynamic Resizing**: Resize images on-the-fly with width/height parameters
- **Flexible Cache Control**: Bypass cache per-request with `cached=false` parameter
- **Robust HTTP Handling**: Configurable retry logic with exponential backoff for external providers
- **Flask Blueprints**: RESTful endpoints for direct image serving and URL retrieval
- **Variable Naming Standards**: Minimum 3-letter variable names for improved code readability

Quick start
-----------

Install::

        $ pip install rero-invenio-thumbnails

Configure the providers and files dir in your application config::

        RERO_INVENIO_THUMBNAILS_PROVIDERS = ["files", "open_library", "google_api", "amazon"]
        RERO_INVENIO_THUMBNAILS_FILES_DIR = "/path/to/thumbnails"
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

        url = get_thumbnail_url("9780134685991")

Get thumbnail image data directly::

        from rero_invenio_thumbnails.api import get_thumbnail

        img_data = get_thumbnail("9780134685991")
        # Returns raw image bytes

HTTP Endpoints
--------------

**GET /thumbnails/<isbn>** - Returns raw JPEG image data

Returns the thumbnail image directly as `image/jpeg`. Supports optional query parameters:

- `width` - Desired width in pixels (maintains aspect ratio)
- `height` - Desired height in pixels (maintains aspect ratio)
- `cached` - Set to `false` to bypass cache (default: `true`)

Examples::

        # Get original thumbnail (cached)
        curl http://localhost/thumbnails/9780134685991 > cover.jpg

        # Get resized thumbnail (200px width)
        curl http://localhost/thumbnails/9780134685991?width=200 > cover_small.jpg

        # Bypass cache
        curl http://localhost/thumbnails/9780134685991?cached=false > cover_fresh.jpg

**GET /thumbnails-url/<isbn>** - Returns JSON with thumbnail URL

Returns JSON containing the thumbnail URL::

        {
            "url": "https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg",
            "isbn": "9780134685991"
        }

Image Validation
----------------

All thumbnail providers validate images to ensure quality:

- Minimum dimensions: 10x10 pixels (filters out 1x1 pixel placeholders)
- Valid image format (verified via PIL/Pillow)
- Non-empty content

This prevents serving placeholder or invalid images from external providers.

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
