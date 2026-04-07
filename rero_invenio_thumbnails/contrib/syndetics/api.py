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

"""Thumbnails Syndetics."""

from rero_invenio_thumbnails.contrib.api import BaseProvider
from rero_invenio_thumbnails.contrib.utils import (
    clean_isbn,
    fetch_and_validate_thumbnail,
    handle_provider_errors,
)


class SyndeticsProvider(BaseProvider):
    """Thumbnail provider for Syndetics book covers.

    This provider fetches book cover images from the Syndetics service using
    a direct ISBN-based URL. No authentication is required for the free tier.
    When no cover exists, Syndetics returns an HTML page instead of an image,
    which is rejected by image content validation.
    """

    name = "syndetics"

    def __init__(self):
        """Initialize the Syndetics provider.

        Examples:
            >>> provider = SyndeticsProvider()
        """
        self.base_url = "https://www.syndetics.com/index.aspx"
        # Available sizes: SC.GIF (small), MC.GIF (medium), LC.GIF (large)
        self.size = "LC.GIF"

    @handle_provider_errors("Syndetics")
    def get_thumbnail_url(self, isbn):
        """Retrieve the cover URL for a book from Syndetics.

        Constructs a direct cover URL using the ISBN and fetches it. Syndetics
        returns a JPEG image when a cover is available, or an HTML fallback
        page when no cover exists — the HTML response fails image validation.

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13, with or without hyphens).
        :returns: tuple - (url, provider_name) where url is the direct cover URL
            if a valid image is found (None otherwise), and provider_name is "syndetics".

        Example::

            provider = SyndeticsProvider()
            url, name = provider.get_thumbnail_url("978-2-07-061275-8")
            # url == "https://www.syndetics.com/index.aspx?isbn=9782070612758/LC.GIF"

        Note:
            - No authentication required (free public tier).
            - Returns (None, "syndetics") if no cover exists or response is not an image.
            - An optional ``client=`` parameter can be added for authenticated access
              with higher coverage, configurable via ``RERO_INVENIO_THUMBNAILS_SYNDETICS_CLIENT``.
        """
        clean_isbn_value = clean_isbn(isbn)

        from flask import current_app

        client = current_app.config.get("RERO_INVENIO_THUMBNAILS_SYNDETICS_CLIENT", "")
        client_param = f"&client={client}" if client else ""
        url = f"{self.base_url}?isbn={clean_isbn_value}/{self.size}{client_param}"

        if fetch_and_validate_thumbnail(url, "Syndetics", clean_isbn_value):
            return url, self.name

        return None, self.name
