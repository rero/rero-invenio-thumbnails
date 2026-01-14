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

- Chainable providers: query multiple providers in order and return the first
  available thumbnail.
- Providers included: `FilesProvider`, `OpenLibraryProvider`,
  `GoogleApiProvider`, `GoogleBooksProvider`, `AmazonProvider`.
- Local `FilesProvider` to serve thumbnails from a configured directory.
- Redis-based image caching via `invenio_cache` with configurable TTL.
- Dynamic image resizing with dimension parameters (width/height).
- Optional cache control via `cached` parameter.
- Robust HTTP handling with retry/backoff for external providers.
- Flask blueprint to serve thumbnails: `/thumbnails/<isbn>`.

Quick start
-----------

Install::

        $ pip install rero-invenio-thumbnails

Configure the providers and files dir in your application config::

        RERO_INVENIO_THUMBNAILS_PROVIDERS = ["files", "open_library", "google_api", "amazon"]
        RERO_INVENIO_THUMBNAILS_FILES_DIR = "/path/to/thumbnails"
        RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE = 3600

Initialize the extension::

        from rero_invenio_thumbnails import REROInvenioThumbnails

        ext = REROInvenioThumbnails()
        ext.init_app(app)

API
---

Use the public helper to get a thumbnail URL for an ISBN::

        from rero_invenio_thumbnails.api import get_thumbnail_url

        url = get_thumbnail_url("9780134685991")

Access thumbnails via HTTP endpoint with optional parameters::

        # Get original thumbnail (cached by default)
        GET /thumbnails/9780134685991

        # Get resized thumbnail (200px width, maintaining aspect ratio)
        GET /thumbnails/9780134685991?width=200

        # Get resized thumbnail with specific dimensions
        GET /thumbnails/9780134685991?width=200&height=300

        # Bypass cache and fetch fresh image
        GET /thumbnails/9780134685991?cached=false

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
