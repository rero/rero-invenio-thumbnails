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

"""Thumbnails BNF (Bibliothèque nationale de France)."""

from importlib.metadata import version as _pkg_version

from rero_invenio_thumbnails.contrib.api import BaseProvider
from rero_invenio_thumbnails.contrib.utils import (
    clean_isbn,
    fetch_and_validate_thumbnail,
    handle_provider_errors,
)


class BnfProvider(BaseProvider):
    """Thumbnail provider for BNF (Bibliothèque nationale de France).

    Uses the openapi.bnf.fr cover service.

    Covers documents published or distributed in France and received by
    the BnF under legal deposit (since 2010).
    """

    name = "bnf"

    def __init__(self):
        """Initialize the BNF provider.

        Examples:
            >>> provider = BnfProvider()
        """
        self.base_url = "https://openapi.bnf.fr/couverture/image/image/recupererImage"
        self.cover_page = 1  # 1 = front cover, 4 = back cover
        # BNF API blocks the default python-requests User-Agent.
        self.headers = {
            "User-Agent": (
                f"rero-invenio-thumbnails/{_pkg_version('rero-invenio-thumbnails')}"
                " (+https://github.com/rero/rero-invenio-thumbnails)"
            )
        }

    @handle_provider_errors("BNF")
    def get_thumbnail_url(self, isbn):
        """Retrieve the cover URL for a book from BNF.

        Queries the BNF openapi cover service.

        :param isbn: ISBN-10 or ISBN-13, with or without hyphens/spaces.
        :returns: tuple — ``(url, "bnf")`` where *url* is the image URL or None.

        Example::

            provider = BnfProvider()
            url, name = provider.get_thumbnail_url("978-2-07-036028-4")
            # url == "https://openapi.bnf.fr/couverture/image/image/recupererImage?ISBN=9782070360284&couverture=1"
        """
        clean_isbn_value = clean_isbn(isbn)
        url = f"{self.base_url}?ISBN={clean_isbn_value}&couverture={self.cover_page}"

        if fetch_and_validate_thumbnail(
            url, "BNF", clean_isbn_value, timeout=(2, 10), headers=self.headers, expected_status_codes={500}
        ):
            return url, self.name
        return None, self.name
