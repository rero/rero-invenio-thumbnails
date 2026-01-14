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

"""Thumbnails GoogleBooks."""

import json
from contextlib import suppress

import requests
from flask import current_app

from rero_invenio_thumbnails.modules.utils import (
    clean_isbn,
    fetch_with_retries,
    handle_provider_errors,
    validate_image_content,
)


class GoogleBooksProvider:
    """Thumbnail provider for Google Books preview images.

    This provider fetches book preview URLs from Google Books using the
    public Books API with JSONP callback format.
    """

    @handle_provider_errors("Google Books")
    def get_thumbnail_url(self, isbn):
        """Retrieve the preview URL for a book from Google Books.

        This method queries Google Books using the viewapi endpoint to get
        book preview information including the preview URL.

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13 format).
        :returns: str or None - The preview URL from Google Books if the book is available,
            None if not found or request fails.

        Examples:
            >>> provider = GoogleBooksProvider()
            >>> url = provider.get_thumbnail_url("9780134685991")
            >>> print(url)
            https://books.google.com/books/about/...

        Note:
            - Uses JSONP callback format for cross-domain requests.
            - No API key is required for this public endpoint.
            - The preview URL may not be available for all books.
        """
        # Clean ISBN (remove hyphens and spaces)
        clean_isbn_value = clean_isbn(isbn)
        url = f"https://books.google.com/books?jscmd=viewapi&callback=book&bibkeys={clean_isbn_value}"
        response = fetch_with_retries(url, timeout=5)
        status_code = response.status_code
        if status_code == requests.codes.ok:
            # JSONP comes as: book({...});
            text = response.text.strip()
            start = text.find("(")
            end = text.rfind(")")
            if start != -1 and end != -1 and end > start:
                json_text = text[start + 1 : end]
                try:
                    data = json.loads(json_text)
                    if thumbnail_url := data.get(clean_isbn_value, {}).get("thumbnail_url"):
                        # Validate the thumbnail URL points to a real image
                        with suppress(Exception):
                            img_response = fetch_with_retries(thumbnail_url, timeout=5)
                            if img_response.status_code == requests.codes.ok and validate_image_content(
                                img_response.content, "Google Books", clean_isbn_value
                            ):
                                return thumbnail_url
                        return None
                    return None
                except ValueError:
                    current_app.logger.error(f"Error parsing JSONP response for ISBN {clean_isbn_value}")
                    return None
            current_app.logger.debug(f"Unexpected Google Books JSONP format for ISBN {clean_isbn_value}")
        return None
