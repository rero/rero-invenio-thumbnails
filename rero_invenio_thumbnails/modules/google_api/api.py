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

"""Thumbnails GoogleApi."""

import requests
from flask import current_app

from rero_invenio_thumbnails.modules.utils import requests_retry_session


class GoogleApiProvider:
    """Thumbnail provider using Google Books API.

    This provider fetches book cover thumbnails using the Google Books API,
    which provides access to a large database of book metadata and images.
    """

    def get_thumbnail_url(self, isbn):
        """Retrieve the thumbnail URL for a book from Google Books API.

        This method queries the Google Books API by ISBN to retrieve book metadata
        including the thumbnail image link.

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13 format).
        :returns: str or None - The URL of the book thumbnail from Google Books if found,
            None if not found or request fails.

        Examples:
            >>> provider = GoogleApiProvider()
            >>> url = provider.get_thumbnail_url("9780134685991")
            >>> print(url)
            http://books.google.com/books/content?id=...

        Note:
            - Requires internet connectivity to access Google Books API.
            - The API returns a thumbnail URL if exactly one book is found.
            - No authentication key is required for basic searches.
        """
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        try:
            response = requests_retry_session().get(url)
            status_code = response.status_code
            if status_code == requests.codes.ok:
                data = response.json()
                # Only accept exactly one result to avoid ambiguity
                if data.get("totalItems") == 1 and data.get("items"):
                    item = data["items"][0]
                    return item.get("volumeInfo", {}).get("imageLinks", {}).get("thumbnail")
                return None
            current_app.logger.debug(f"ISBN not found Google Api {isbn}: {status_code}")
        except requests.RequestException as e:
            current_app.logger.error(f"Request error retrieving thumbnail for ISBN {isbn} from Google API: {e!s}")
        except ValueError as e:
            current_app.logger.error(f"Error parsing JSON from Google API for ISBN {isbn}: {e!s}")
        except Exception as e:
            current_app.logger.error(f"Unexpected error in GoogleApiProvider for ISBN {isbn}: {e!s}")

        return None
