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

from rero_invenio_thumbnails.modules.utils import requests_retry_session


class OpenLibraryProvider:
    """Thumbnail provider for Open Library book covers.

    This provider fetches book cover images from Open Library, a free and
    open-source library catalog that aggregates book cover data.
    """

    def get_thumbnail_url(self, isbn):
        """Retrieve the cover URL for a book from Open Library.

        This method uses the Open Library Covers API to retrieve book cover
        images by ISBN. It requests the large cover format (-L.jpg).

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13 format).
        :returns: str or None - The direct URL to the book cover image if found,
            None if not found or request fails.

        Examples:
            >>> provider = OpenLibraryProvider()
            >>> url = provider.get_thumbnail_url("9780134685991")
            >>> print(url)
            https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg

        Note:
            - Uses the public Open Library Covers API (no authentication required).
            - Covers are provided under Creative Commons licenses.
            - The "default=false" parameter prevents returning placeholder images.
        """
        try:
            url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
            response = requests_retry_session().get(url, timeout=5)
            status_code = response.status_code
            if status_code == requests.codes.ok:
                # Optionally verify content-type is an image
                content_type = response.headers.get("Content-Type", "")
                if content_type.startswith("image/"):
                    return url
                current_app.logger.debug(f"Open Library returned non-image content for ISBN {isbn}: {content_type}")
                return None
            current_app.logger.debug(f"ISBN not found Open Library {isbn}: {status_code}")
        except requests.RequestException as e:
            current_app.logger.error(f"Request error retrieving thumbnail for ISBN {isbn} from Open Library: {e!s}")
        except Exception as e:
            current_app.logger.error(f"Unexpected error in OpenLibraryProvider for ISBN {isbn}: {e!s}")

        return None
