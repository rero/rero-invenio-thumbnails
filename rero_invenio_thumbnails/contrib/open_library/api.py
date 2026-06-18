# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Thumbnails OpenLibrary."""

from rero_invenio_thumbnails.contrib.api import BaseProvider
from rero_invenio_thumbnails.contrib.utils import (
    clean_isbn,
    fetch_and_validate_thumbnail,
    handle_provider_errors,
)


class OpenLibraryProvider(BaseProvider):
    """Thumbnail provider for Open Library book covers.

    This provider fetches book cover images from Open Library, a free and
    open-source library catalog that aggregates book cover data.
    """

    name = "open library"

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

    @handle_provider_errors("open library")
    def get_thumbnail_url(self, isbn):
        r"""Retrieve the cover URL for a book from Open Library.

        This method uses the Open Library Covers API to retrieve book cover
        images by ISBN. It requests the large cover format (-L.jpg).

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13 format).
        :returns: tuple - (url, provider_name) where url is the direct URL to the book
            cover image if found (None otherwise), and provider_name is \"open library\".

        Example::

            provider = OpenLibraryProvider()
            url, name = provider.get_thumbnail_url("9780134685991")
            # url == "https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg?default=false"

        Note:
            - Uses the public Open Library Covers API (no authentication required).
            - Covers are provided under Creative Commons licenses.
            - The "default=false" parameter prevents returning placeholder images.
        """
        # Clean ISBN (remove hyphens and spaces)
        clean_isbn_value = clean_isbn(isbn)
        url = f"{self.base_url}/b/isbn/{clean_isbn_value}-{self.size}.jpg?default=false"

        # Fetch and validate the thumbnail
        if fetch_and_validate_thumbnail(url, self.name, clean_isbn_value):
            return url, self.name

        return None, self.name
