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
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Thumbnails GoogleApi."""

import requests

from rero_invenio_thumbnails.contrib.api import BaseProvider
from rero_invenio_thumbnails.contrib.utils import (
    clean_isbn,
    fetch_and_validate_thumbnail,
    fetch_with_retries,
    handle_provider_errors,
)


class GoogleApiProvider(BaseProvider):
    """Thumbnail provider using Google Books API.

    This provider fetches book cover thumbnails using the Google Books API,
    which provides access to a large database of book metadata and images.
    """

    name = "google api"

    def __init__(self):
        """Initialize the Google API provider.

        Examples:
            >>> # Default provider
            >>> provider = GoogleApiProvider()
        """
        self.base_url = "https://www.googleapis.com/books/v1/volumes"

    @handle_provider_errors("Google API")
    def get_thumbnail_url(self, isbn):
        r"""Retrieve the thumbnail URL for a book from Google Books API.

        This method queries the Google Books API by ISBN to retrieve book metadata
        including the thumbnail image link.

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13 format).
        :returns: tuple - (url, provider_name) where url is the thumbnail URL from
            Google Books if found (None otherwise), and provider_name is \"google api\".

        Examples:
            >>> provider = GoogleApiProvider()  # doctest: +SKIP
            >>> url, provider = provider.get_thumbnail_url("9780134685991")  # doctest: +SKIP
            >>> print(url, provider)  # doctest: +SKIP
            https://books.google.com/books/content?id=... google api

        Note:
            - Requires internet connectivity to access Google Books API.
            - The API returns a thumbnail URL if exactly one book is found.
            - No authentication key is required for basic searches.
        """
        # Clean ISBN (remove hyphens and spaces)
        clean_isbn_value = clean_isbn(isbn)
        url = f"{self.base_url}?q=isbn:{clean_isbn_value}"
        response = fetch_with_retries(url)
        if response.status_code == requests.codes.ok:
            data = response.json()
            # Only accept exactly one result to avoid ambiguity
            if data.get("totalItems") == 1 and data.get("items"):
                item = data["items"][0]
                if (
                    thumbnail_url := item.get("volumeInfo", {}).get("imageLinks", {}).get("thumbnail")
                ) and fetch_and_validate_thumbnail(thumbnail_url, "Google API", clean_isbn_value):
                    return thumbnail_url, self.name
        return None, self.name
