# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Thumbnails Amazon."""

from urllib.parse import urljoin

from isbnlib import to_isbn10

from rero_invenio_thumbnails.contrib.api import BaseProvider
from rero_invenio_thumbnails.contrib.utils import (
    clean_isbn,
    fetch_and_validate_thumbnail,
    handle_provider_errors,
)


class AmazonProvider(BaseProvider):
    """Thumbnail provider for Amazon book cover images.

    Fetches book cover images from Amazon's image CDN using the book's ASIN,
    which for books is equivalent to its ISBN-10. ISBN-13 values are converted
    to ISBN-10 automatically. Books with a 979-prefix ISBN-13 (no ISBN-10
    equivalent) are not supported.

    Amazon returns a 43-byte transparent GIF placeholder for unknown ASINs,
    which is rejected by the image validator (below the 50x50 px minimum).
    """

    name = "amazon"

    def __init__(self):
        """Initialize the Amazon provider.

        Examples:
            >>> provider = AmazonProvider()
        """
        self.base_url = "https://images-na.ssl-images-amazon.com/images/P/"

    @handle_provider_errors("Amazon")
    def get_thumbnail_url(self, isbn):
        """Retrieve the cover URL for a book from Amazon.

        Converts the ISBN to an ASIN (ISBN-10), constructs the cover image URL,
        and validates the response is a real image (not a placeholder GIF).

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13, with or without hyphens).
        :returns: tuple - (url, provider_name) where url is the cover image URL
            if a valid image is found (None otherwise), and provider_name is "amazon".

        Example::

            provider = AmazonProvider()
            url, name = provider.get_thumbnail_url("978-2-07-061275-8")
            # url == "https://images-na.ssl-images-amazon.com/images/P/2070612759.01.LZZZZZZZ.jpg"

        Note:
            - No authentication required.
            - ISBN-13 values with a 979 prefix cannot be looked up (no ASIN equivalent).
            - Returns (None, "amazon") if no cover is found or the ISBN cannot be
              converted to an ASIN.
        """
        clean_isbn_value = clean_isbn(isbn)
        asin = to_isbn10(clean_isbn_value)
        if not asin:
            return None, self.name

        url = urljoin(self.base_url, f"{asin}.01.LZZZZZZZ.jpg")
        if fetch_and_validate_thumbnail(url, "Amazon", clean_isbn_value):
            return url, self.name
        return None, self.name
