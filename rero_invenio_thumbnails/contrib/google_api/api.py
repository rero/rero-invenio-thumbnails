# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Thumbnails GoogleApi."""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests
from flask import current_app

from rero_invenio_thumbnails.contrib.api import BaseProvider
from rero_invenio_thumbnails.contrib.utils import (
    clean_isbn,
    fetch_and_validate_thumbnail,
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

        Example::

            provider = GoogleApiProvider()
            url, name = provider.get_thumbnail_url("9780134685991")
            # url == "https://books.google.com/books/content?id=..."

        Note:
            - Requires internet connectivity to access Google Books API.
            - The API returns a thumbnail URL if exactly one book is found.
            - No authentication key is required for basic searches.
        """
        # Clean ISBN (remove hyphens and spaces)
        clean_isbn_value = clean_isbn(isbn)
        url = f"{self.base_url}?q=isbn:{clean_isbn_value}"
        timeout = current_app.config.get("RERO_INVENIO_THUMBNAILS_HTTP_TIMEOUT", (2, 10))
        response = requests.get(url, timeout=timeout)
        if response.status_code != requests.codes.ok:
            current_app.logger.debug(
                f"HTTP {response.status_code} fetching thumbnail from {self.name} for ISBN {clean_isbn_value}: {url}"
            )
            return None, self.name
        data = response.json()
        # Only accept exactly one result to avoid ambiguity
        if data.get("totalItems") == 1 and data.get("items"):
            item = data["items"][0]
            if thumbnail_url := item.get("volumeInfo", {}).get("imageLinks", {}).get("thumbnail"):
                thumbnail_url = _remove_edge_curl(thumbnail_url)
                if fetch_and_validate_thumbnail(thumbnail_url, self.name, clean_isbn_value):
                    return thumbnail_url, self.name
        return None, self.name


def _remove_edge_curl(url):
    """Remove the edge=curl parameter from a Google Books thumbnail URL."""
    parsed = urlparse(url)
    params = {k: v for k, v in parse_qs(parsed.query, keep_blank_values=True).items() if k != "edge"}
    return urlunparse(parsed._replace(query=urlencode(params, doseq=True)))
