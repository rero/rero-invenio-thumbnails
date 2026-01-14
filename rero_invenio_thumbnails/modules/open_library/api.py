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

"""Thumbnails OpenLibrary."""

import requests
from flask import current_app

from rero_invenio_thumbnails.modules.api import BaseProvider
from rero_invenio_thumbnails.modules.utils import (
    clean_isbn,
    fetch_with_retries,
    handle_provider_errors,
    validate_image_content,
)


class OpenLibraryProvider(BaseProvider):
    """Thumbnail provider for Open Library book covers.

    This provider fetches book cover images from Open Library, a free and
    open-source library catalog that aggregates book cover data.
    """

    def __init__(self):
        """Initialize the Open Library provider.

        Examples:
            >>> # Default large size provider
            >>> provider = OpenLibraryProvider()
        """
        # Available sizes:
        # - "S": Small (suitable for thumbnails in lists)
        # - "M": Medium (suitable for display on details pages)
        # - "L": Large (full-size cover image)
        self.size = "L"

        self.base_url = "https://covers.openlibrary.org"

    @handle_provider_errors("Open Library")
    def get_thumbnail_url(self, isbn):
        r"""Retrieve the cover URL for a book from Open Library.

        This method uses the Open Library Covers API to retrieve book cover
        images by ISBN. It requests the large cover format (-L.jpg).

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13 format).
        :returns: tuple - (url, provider_name) where url is the direct URL to the book
            cover image if found (None otherwise), and provider_name is \"open library\".

        Examples:
            >>> provider = OpenLibraryProvider()
            >>> url, provider = provider.get_thumbnail_url("9780134685991")
            >>> print(url, provider)
            https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg?default=false open library
            >>> # Small size example
            >>> provider_small = OpenLibraryProvider(size="S")
            >>> url_small, provider = provider_small.get_thumbnail_url("9780134685991")
            >>> print(url_small, provider)
            https://covers.openlibrary.org/b/isbn/9780134685991-S.jpg?default=false open library

        Note:
            - Uses the public Open Library Covers API (no authentication required).
            - Covers are provided under Creative Commons licenses.
            - The "default=false" parameter prevents returning placeholder images.
        """
        # Clean ISBN (remove hyphens and spaces)
        clean_isbn_value = clean_isbn(isbn)
        url = f"{self.base_url}/b/isbn/{clean_isbn_value}-{self.size}.jpg?default=false"
        response = fetch_with_retries(url, timeout=5)
        status_code = response.status_code
        if status_code == requests.codes.ok:
            # Verify content-type is an image
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                current_app.logger.debug(
                    f"Open Library returned non-image content for ISBN {clean_isbn_value}: {content_type}"
                )
                return None, "open library"
            # Validate image has real content and dimensions
            if validate_image_content(response.content, "Open Library", clean_isbn_value):
                return url, "open library"
        return None, "open library"
