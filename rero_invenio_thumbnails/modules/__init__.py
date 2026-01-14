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

"""Thumbnail provider modules package.

This package contains implementations of various thumbnail providers that retrieve
book cover images from different sources. Each provider implements a consistent
interface for fetching thumbnail URLs using ISBN numbers.

The providers follow a common pattern:
1. Accept ISBN input (ISBN-10 or ISBN-13, with or without hyphens)
2. Clean and validate the ISBN
3. Query the respective API or storage system
4. Validate the returned image
5. Return the thumbnail URL or None if not found

Available Providers:
    amazon: Amazon product images provider
        - Uses Amazon's image servers
        - Converts ISBN-13 to ISBN-10
        - Supports multiple regional domains

    bnf: Bibliothèque nationale de France provider
        - Uses BNF catalogue API
        - Converts ISBN to ARK identifiers
        - Covers for French publications since 2010

    files: Local file storage provider
        - Searches local file system
        - Supports JPG, PNG, JPEG formats
        - Integration with Invenio Files

    google_api: Google Books API provider
        - Uses Google Books volumes API
        - Requires unique ISBN match
        - No authentication needed

    google_books: Google Books preview API provider
        - Uses Google Books viewapi endpoint
        - JSONP callback format
        - Public access without authentication

    open_library: Open Library covers API provider
        - Free and open-source
        - Configurable sizes (S, M, L)
        - Creative Commons licensed covers

    utils: Shared utility functions
        - clean_isbn(): Remove hyphens and spaces from ISBN
        - fetch_with_retries(): HTTP requests with retry logic
        - validate_image_content(): Image validation (format, dimensions)
        - handle_provider_errors(): Standardized error handling decorator

Provider Interface:
    All provider classes implement the following interface pattern:

        class ProviderName:
            def __init__(self, **config):
                # Initialize provider with configuration
                pass

            def get_thumbnail_url(self, isbn: str) -> str | None:
                # Retrieve thumbnail URL for ISBN
                # :param isbn: ISBN-10 or ISBN-13 (with or without hyphens)
                # :returns: Thumbnail URL if found, None otherwise
                pass

Usage Pattern:
    >>> from rero_invenio_thumbnails.modules.amazon.api import AmazonProvider
    >>> from rero_invenio_thumbnails.modules.open_library.api import OpenLibraryProvider
    >>>
    >>> # Try multiple providers in sequence
    >>> isbn = '978-0-13-468599-1'
    >>> providers = [AmazonProvider(), OpenLibraryProvider()]
    >>>
    >>> for provider in providers:
    >>>     if url := provider.get_thumbnail_url(isbn):
    >>>         print(f"Found: {url}")
    >>>         break
    >>> else:
    >>>     print("No thumbnail found")

Error Handling:
    All providers use the @handle_provider_errors decorator which:
    - Catches and logs ValueError for invalid ISBN formats
    - Catches and logs RequestException for network errors
    - Catches and logs all other exceptions
    - Returns None on any error for graceful fallback

Retry Logic:
    HTTP requests use fetch_with_retries() with:
    - Exponential backoff between retries
    - Configurable retry attempts (default: 5)
    - Disabled during testing for performance
    - Handles transient network failures

Image Validation:
    All providers validate images using validate_image_content():
    - Checks for non-empty content
    - Validates image format with PIL
    - Verifies minimum dimensions (10x10px default)
    - Filters out placeholder images

Configuration:
    Provider behavior can be configured via Flask configuration:
    - RERO_INVENIO_THUMBNAILS_RETRY_ATTEMPTS
    - RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MULTIPLIER
    - RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MIN
    - RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MAX
    - RERO_INVENIO_THUMBNAILS_FILES_DIR (for files provider)

Note:
    Providers should be used through the main API (rero_invenio_thumbnails.api)
    rather than directly, to benefit from caching and provider chaining.
"""
