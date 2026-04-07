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

"""Thumbnails Internet Archive."""

from importlib.metadata import version as _pkg_version
from urllib.parse import urlencode

import requests
from flask import current_app

from rero_invenio_thumbnails.contrib.api import BaseProvider
from rero_invenio_thumbnails.contrib.utils import (
    clean_isbn,
    fetch_and_validate_thumbnail,
    fetch_with_retries,
    handle_provider_errors,
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
        try:
            response = fetch_with_retries(url, headers=self.headers)
            if response.status_code != requests.codes.ok:
                return None
            docs = response.json().get("response", {}).get("docs", [])
            if docs:
                return docs[0].get("identifier")
        except requests.RequestException as exc:
            current_app.logger.warning(f"Internet Archive search failed for ISBN {isbn}: {exc}")
        except (ValueError, KeyError) as exc:
            current_app.logger.warning(f"Internet Archive response parse error for ISBN {isbn}: {exc}")
        return None

    @handle_provider_errors("Internet Archive")
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
            - Returns (None, "internet archive") if no matching item exists
              or the cover image fails validation.
        """
        clean_isbn_value = clean_isbn(isbn)
        ocaid = self.isbn_to_ocaid(clean_isbn_value)
        if not ocaid:
            return None, self.name

        url = f"https://archive.org/services/img/{ocaid}"
        if fetch_and_validate_thumbnail(url, "Internet Archive", clean_isbn_value, headers=self.headers):
            return url, self.name

        return None, self.name
