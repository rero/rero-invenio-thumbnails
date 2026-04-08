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

"""Thumbnails DNB (Deutsche Nationalbibliothek)."""

from rero_invenio_thumbnails.contrib.api import BaseProvider
from rero_invenio_thumbnails.contrib.utils import (
    clean_isbn,
    fetch_and_validate_thumbnail,
    handle_provider_errors,
)


class DnbProvider(BaseProvider):
    """Thumbnail provider for DNB (Deutsche Nationalbibliothek).

    Fetches cover images directly from the DNB/MVB cover service
    (``portal.dnb.de/opac/mvb/cover``) using the ISBN.

    .. warning::

        Cover images served by this endpoint are sourced from **VLB**
        (Verzeichnis Lieferbarer Bücher, operated by MVB GmbH) and are
        subject to copyright.  They are **not** freely reusable.  Use of
        this provider requires a valid data licence agreement with MVB.
        Contact: kundenservice@mvb-online.de

        DNB bibliographic *metadata* is freely available under CC0, but
        cover images are not part of that licence.

    Example::

        provider = DnbProvider()
        url, name = provider.get_thumbnail_url("9783161484100")
        # url == "https://portal.dnb.de/opac/mvb/cover?isbn=9783161484100"
    """

    name = "dnb"

    def __init__(self):
        """Initialize the DNB provider.

        Examples:
            >>> provider = DnbProvider()
        """
        self.base_url = "https://portal.dnb.de/opac/mvb/cover"

    @handle_provider_errors("DNB")
    def get_thumbnail_url(self, isbn):
        """Retrieve the cover URL for a book from DNB/MVB.

        Constructs the cover URL directly from the ISBN and validates
        that the endpoint returns a real image.

        :param isbn: ISBN-10 or ISBN-13, with or without hyphens/spaces.
        :returns: tuple — ``(url, "dnb")`` where *url* is the image URL or None.

        Example::

            provider = DnbProvider()
            url, name = provider.get_thumbnail_url("9783161484100")
            # url == "https://portal.dnb.de/opac/mvb/cover?isbn=9783161484100"
        """
        clean = clean_isbn(isbn)
        if not clean:
            return None, self.name

        url = f"{self.base_url}?isbn={clean}"
        if fetch_and_validate_thumbnail(url, "DNB", clean, timeout=10):
            return url, self.name
        return None, self.name
