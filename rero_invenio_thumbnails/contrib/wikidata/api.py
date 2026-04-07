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

"""Thumbnails Wikidata / Wikimedia Commons."""

from importlib.metadata import version as _pkg_version
from urllib.parse import unquote, urlencode

import requests
from flask import current_app

from rero_invenio_thumbnails.contrib.api import BaseProvider
from rero_invenio_thumbnails.contrib.utils import (
    clean_isbn,
    fetch_and_validate_thumbnail,
    fetch_with_retries,
    handle_provider_errors,
)

# SPARQL query to resolve an ISBN to a Wikimedia Commons cover image filename.
# Tries three paths through the Wikidata book data model:
#   1. Edition has P18 directly
#   2. Edition → P629 (edition of) → work has P18
#   3. Work → P747 (has edition) → edition has P212 matching ISBN + work has P18
# ISBN-13 (P212) is stored with hyphens in Wikidata, so REPLACE strips them.
_SPARQL_QUERY = """\
SELECT ?image WHERE {{
  {{
    ?edition wdt:P212 ?isbn13 .
    FILTER(REPLACE(?isbn13, "-", "") = "{isbn}")
    ?edition wdt:P18 ?image .
  }} UNION {{
    ?edition wdt:P212 ?isbn13 .
    FILTER(REPLACE(?isbn13, "-", "") = "{isbn}")
    ?edition wdt:P629 ?work .
    ?work wdt:P18 ?image .
  }} UNION {{
    ?work wdt:P747 ?edition .
    ?edition wdt:P212 ?isbn13 .
    FILTER(REPLACE(?isbn13, "-", "") = "{isbn}")
    ?work wdt:P18 ?image .
  }}
}} LIMIT 1"""


class WikidataProvider(BaseProvider):
    """Thumbnail provider for Wikidata / Wikimedia Commons.

    This provider resolves an ISBN to a cover image via the Wikidata SPARQL
    endpoint (property P18), then fetches a rendered thumbnail from the
    Wikimedia Commons imageinfo API. It handles SVG, TIFF and other formats
    by requesting a JPEG-rendered version at a configurable width.
    """

    name = "wikidata"

    def __init__(self):
        """Initialize the Wikidata provider.

        Examples:
            >>> provider = WikidataProvider()
        """
        self.sparql_url = "https://query.wikidata.org/sparql"
        self.commons_api_url = "https://commons.wikimedia.org/w/api.php"
        # Thumbnail width in pixels for the Commons imageinfo API response.
        self.thumb_width = 300
        # Both Wikidata and Commons require a descriptive User-Agent.
        self.headers = {
            "User-Agent": (
                f"rero-invenio-thumbnails/{_pkg_version('rero-invenio-thumbnails')}"
                " (+https://github.com/rero/rero-invenio-thumbnails)"
            ),
            "Accept": "application/sparql-results+json",
        }

    @property
    def _fetch_headers(self):
        """Return headers for plain HTTP requests (no SPARQL Accept header)."""
        return {k: v for k, v in self.headers.items() if k != "Accept"}

    def isbn_to_commons_filename(self, isbn):
        """Resolve an ISBN to a Wikimedia Commons image filename via Wikidata SPARQL.

        Queries the Wikidata SPARQL endpoint to find a cover image (P18) associated
        with the given ISBN. Searches edition items (P212), their parent works (P629),
        and works that list editions via P747.

        :param isbn: Cleaned ISBN-13 or ISBN-10 (digits only, no hyphens).
        :returns: str or None - The Commons filename (URL-decoded) if found, else None.

        Example::

            provider = WikidataProvider()
            filename = provider.isbn_to_commons_filename("9782957688708")
            # filename == "The bipolar transistor, the concept and the applications book cover.svg"
        """
        try:
            query = _SPARQL_QUERY.format(isbn=isbn)
            url = f"{self.sparql_url}?{urlencode({'query': query, 'format': 'json'})}"
            response = fetch_with_retries(url, headers=self.headers, timeout=15)

            if response.status_code != requests.codes.ok:
                return None

            bindings = response.json().get("results", {}).get("bindings", [])
            if not bindings:
                return None

            # image value is like:
            # http://commons.wikimedia.org/wiki/Special:FilePath/Filename.jpg
            image_uri = bindings[0]["image"]["value"]
            return unquote(image_uri.split("Special:FilePath/")[-1])

        except requests.RequestException as exc:
            current_app.logger.warning(f"Wikidata SPARQL request failed for ISBN {isbn}: {exc}")
        except (KeyError, ValueError) as exc:
            current_app.logger.warning(f"Wikidata SPARQL parse error for ISBN {isbn}: {exc}")
        return None

    def commons_filename_to_thumb_url(self, filename):
        """Resolve a Wikimedia Commons filename to a rendered thumbnail URL.

        Uses the Commons imageinfo API to obtain a JPEG/PNG thumbnail at
        ``self.thumb_width`` pixels, regardless of the source file format
        (handles SVG, TIFF, etc.).

        :param filename: The Commons filename (URL-decoded, spaces allowed).
        :returns: str or None - The direct thumbnail URL, or None on failure.

        Example::

            provider = WikidataProvider()
            url = provider.commons_filename_to_thumb_url(
                "The bipolar transistor, the concept and the applications book cover.svg"
            )
            # url == "https://upload.wikimedia.org/wikipedia/commons/thumb/..."
        """
        try:
            params = {
                "action": "query",
                "titles": f"File:{filename}",
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": self.thumb_width,
                "format": "json",
            }
            url = f"{self.commons_api_url}?{urlencode(params)}"
            response = fetch_with_retries(url, headers=self._fetch_headers, timeout=10)

            if response.status_code != requests.codes.ok:
                return None

            pages = response.json().get("query", {}).get("pages", {})
            page = next(iter(pages.values()), {})
            imageinfo = page.get("imageinfo", [])
            return imageinfo[0].get("thumburl") if imageinfo else None

        except requests.RequestException as exc:
            current_app.logger.warning(f"Commons imageinfo request failed for {filename!r}: {exc}")
        except (KeyError, ValueError) as exc:
            current_app.logger.warning(f"Commons imageinfo parse error for {filename!r}: {exc}")
        return None

    @handle_provider_errors("Wikidata")
    def get_thumbnail_url(self, isbn):
        """Retrieve the cover URL for a book from Wikidata / Wikimedia Commons.

        Resolves an ISBN to a cover image in two steps:
            1. SPARQL query to find a Commons image filename via Wikidata P18.
            2. Commons imageinfo API to get a rendered thumbnail URL.

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13, with or without hyphens).
        :returns: tuple - (url, provider_name) where url is the thumbnail URL if found
            (None otherwise), and provider_name is "wikidata".

        Example::

            provider = WikidataProvider()
            url, name = provider.get_thumbnail_url("978-2-9576887-0-8")
            # url == "https://upload.wikimedia.org/wikipedia/commons/thumb/..."

        Note:
            - No authentication required.
            - Coverage depends on Wikidata community contributions.
            - Images are under various free licenses (CC0, CC-BY, CC-BY-SA, etc.).
            - A descriptive User-Agent is sent to all three endpoints (SPARQL,
              Commons imageinfo API, and upload.wikimedia.org), all of which
              block the default python-requests User-Agent.
            - Returns (None, "wikidata") if no cover is found or on API errors.
        """
        clean_isbn_value = clean_isbn(isbn)

        filename = self.isbn_to_commons_filename(clean_isbn_value)
        if not filename:
            return None, self.name

        thumb_url = self.commons_filename_to_thumb_url(filename)
        if not thumb_url:
            return None, self.name

        if fetch_and_validate_thumbnail(thumb_url, "Wikidata", clean_isbn_value, headers=self._fetch_headers):
            return thumb_url, self.name

        return None, self.name
