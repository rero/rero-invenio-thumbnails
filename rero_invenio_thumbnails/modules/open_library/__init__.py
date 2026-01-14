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

"""Open Library book covers API thumbnail provider module.

This module provides thumbnail retrieval functionality from Open Library's Covers API.
Open Library is a free, open-source library catalog that aggregates book cover data
from multiple sources and provides public access without authentication.

The provider uses the Open Library Covers API, which offers direct ISBN-based access
to book cover images with configurable sizes. It includes content-type validation
and dimension checks to ensure quality images are returned.

Key Features:
    - No authentication required (public API)
    - Configurable thumbnail sizes (S, M, L)
    - Direct ISBN access without search
    - ISBN cleaning (removes hyphens and spaces)
    - Content-type validation (image/* only)
    - Image dimension validation
    - Automatic retry with exponential backoff
    - Creative Commons licensed covers

Example:
    >>> from rero_invenio_thumbnails.modules.open_library.api import OpenLibraryProvider
    >>>
    >>> # Default large size
    >>> provider = OpenLibraryProvider()
    >>> url = provider.get_thumbnail_url('978-0-13-468599-1')
    >>> print(url)
    https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg?default=false
    >>>
    >>> # Small size for thumbnails
    >>> provider_small = OpenLibraryProvider(size='S')
    >>> url = provider_small.get_thumbnail_url('9780134685991')
    >>> print(url)
    https://covers.openlibrary.org/b/isbn/9780134685991-S.jpg?default=false

Configuration:
    size: Cover size code
        - 'S': Small (~80x120px) - suitable for thumbnails in lists
        - 'M': Medium (~180x270px) - suitable for detail pages
        - 'L': Large (~500x750px) - full-size cover image (default)

API Documentation:
    - Open Library Covers API: https://openlibrary.org/dev/docs/api/covers
    - URL format: https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg
    - Parameter default=false prevents placeholder images

License:
    Book covers are provided under various Creative Commons licenses.
    See Open Library for specific cover licensing information.

Note:
    - Returns None if cover not available
    - Rejects non-image content types (text/html, etc.)
    - Validates image dimensions to filter placeholders
    - Reliable and fast public API
    - No rate limiting for reasonable usage
"""
