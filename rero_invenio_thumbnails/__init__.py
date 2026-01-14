# RERO Thumbnails
# Copyright (C) 2026 RERO.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""RERO Invenio Thumbnails extension.

This module provides a Flask/Invenio extension to retrieve and serve book
thumbnails from multiple external providers with caching support.

Features:
    - Multiple thumbnail providers (Files, OpenLibrary, GoogleBooks, etc.)
    - Chainable provider pattern (first match wins)
    - Redis caching integration via invenio_cache
    - HTTP blueprint endpoint for thumbnail serving
    - Retry/backoff support for external provider queries
    - Comprehensive error handling and logging

Usage:
    >>> from rero_invenio_thumbnails import REROInvenioThumbnails
    >>> ext = REROInvenioThumbnails(app)
    >>> # Or: ext = REROInvenioThumbnails(); ext.init_app(app)

Configuration:
    RERO_INVENIO_THUMBNAILS_PROVIDERS: List of provider names in priority order
    RERO_INVENIO_THUMBNAILS_FILES_DIR: Path to local thumbnail directory
    RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE: Cache expiration time in seconds
"""

from importlib.metadata import PackageNotFoundError, version

from .api import get_thumbnail_url
from .ext import REROInvenioThumbnails
from .modules.bnf.api import BnfProvider
from .modules.dnb.api import DnbProvider
from .modules.files.api import FilesProvider
from .modules.google_api.api import GoogleApiProvider
from .modules.google_books.api import GoogleBooksProvider
from .modules.open_library.api import OpenLibraryProvider

try:
    __version__ = version("rero-invenio-thumbnails")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = (
    "BnfProvider",
    "DnbProvider",
    "FilesProvider",
    "GoogleApiProvider",
    "GoogleBooksProvider",
    "OpenLibraryProvider",
    "REROInvenioThumbnails",
    "__version__",
    "get_thumbnail_url",
)
