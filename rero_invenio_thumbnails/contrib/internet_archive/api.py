# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Thumbnails Internet Archive."""

from importlib.metadata import version as _pkg_version
from urllib.parse import urlencode

from flask import current_app

from rero_invenio_thumbnails.contrib.api import BaseProvider
from rero_invenio_thumbnails.contrib.utils import (
    clean_isbn,
    fetch_url,
    handle_provider_errors,
    validate_image_content,
)


class InternetArchiveProvider(BaseProvider):
    """Thumbnail provider for Internet Archive book covers.

    This provider fetches book cover images from the Internet Archive by first
    resolving the ISBN to an Open Content Alliance identifier (OCAID) via the
    Archive's search API, then constructing a cover image URL using the OCAID.
    The provider is free and requires no authentication.
    """

    name = "internet archive"

    def __init__(self):
        """Initialize the Internet Archive provider.

        Examples:
            >>> provider = InternetArchiveProvider()
        """
        self.search_url = "https://archive.org/advancedsearch.php"
        self.headers = {
            "User-Agent": (
                f"rero-invenio-thumbnails/{_pkg_version('rero-invenio-thumbnails')}"
                " (+https://github.com/rero/rero-invenio-thumbnails)"
            )
        }

    def isbn_to_ocaid(self, isbn):
        """Resolve an ISBN to an Internet Archive OCAID via the search API.

        Queries the Internet Archive full-text search API for items matching the
        given ISBN and returns the first result's identifier (OCAID).

        :param isbn: The cleaned ISBN (no hyphens or spaces).
        :returns: str or None - The OCAID if found, None otherwise.

        Example::

            provider = InternetArchiveProvider()
            ocaid = provider.isbn_to_ocaid("9782070360284")
            # ocaid == "lepetitnicelasvil0000unse"
        """
        params = {"q": f"isbn:{isbn}", "fl[]": "identifier", "output": "json", "rows": 1}
        url = f"{self.search_url}?{urlencode(params, doseq=True)}"
        if (response := fetch_url(url, self.name, isbn, timeout=(3, 15), headers=self.headers)) is None:
            return None
        try:
            docs = response.json().get("response", {}).get("docs", [])
            return docs[0].get("identifier") if docs else None
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
            current_app.logger.error(f"{self.name} response parse error for ISBN {isbn}: {exc}")
            return None

    @handle_provider_errors("internet archive")
    def get_thumbnail_url(self, isbn):
        """Retrieve the cover URL for a book from Internet Archive.

        Resolves the ISBN to an OCAID via the search API, then constructs the
        cover image URL using the Archive's image service endpoint.

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13, with or without hyphens).
        :returns: tuple - (url, provider_name) where url is the cover image URL
            if a valid image is found (None otherwise), and provider_name is
            "internet archive".

        Example::

            provider = InternetArchiveProvider()
            url, name = provider.get_thumbnail_url("978-2-07-036028-4")
            # url == "https://archive.org/services/img/lepetitnicelasvil0000unse"

        Note:
            - No authentication required (open access).
            - Returns (None, "internet archive") if no matching item exists,
              if the service redirects to the generic notfound.png placeholder,
              or if the cover image fails validation.
        """
        clean_isbn_value = clean_isbn(isbn)
        ocaid = self.isbn_to_ocaid(clean_isbn_value)
        if not ocaid:
            return None, self.name

        url = f"https://archive.org/services/img/{ocaid}"
        response = fetch_url(url, self.name, clean_isbn_value, timeout=(3, 30), headers=self.headers)
        if response is None:
            return None, self.name

        # Reject redirect to the generic "not found" placeholder
        if "notfound" in response.url:
            return None, self.name

        if validate_image_content(response.content, self.name, clean_isbn_value):
            return url, self.name

        return None, self.name
