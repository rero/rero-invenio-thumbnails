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

"""Thumbnails BNF (Bibliothèque nationale de France)."""

from contextlib import suppress
from xml.etree import ElementTree

import requests

from rero_invenio_thumbnails.modules.api import BaseProvider
from rero_invenio_thumbnails.modules.utils import (
    clean_isbn,
    fetch_with_retries,
    handle_provider_errors,
    validate_image_content,
)


class BnfProvider(BaseProvider):
    """Thumbnail provider for BNF (Bibliothèque nationale de France).

    This provider fetches book cover images from the French National Library's
    catalogue service using ARK identifiers. The service provides access to
    covers of documents published or distributed in France and received by
    the BnF under legal deposit (since 2010).
    """

    def __init__(self):
        """Initialize the BNF provider.

        Examples:
            >>> # Default provider (front cover)
            >>> provider = BnfProvider()
        """
        self.app_name = "NE"  # Required by BNF API
        self.cover_page = 1  # Cover page to retrieve (1=front cover, 4=back cover).
        self.base_url = "http://catalogue.bnf.fr/couverture"

    def isbn_to_ark(self, isbn):
        """Convert ISBN to ARK identifier using BNF SRU API.

        This method queries the BNF catalog via the SRU API to retrieve the ARK
        identifier associated with an ISBN. The ARK is extracted directly from
        the MARC record's id attribute in the XML response.

        :param isbn: The ISBN to convert (ISBN-10 or ISBN-13, with or without hyphens/spaces).
        :returns: str or None - The ARK identifier if found, None otherwise.

        Examples:
            >>> provider = BnfProvider()
            >>> ark_id = provider.isbn_to_ark("978-2-07-036028-4")
            >>> print(ark_id)
            ark:/12148/cb450989938
            >>> # Works with clean ISBN too
            >>> ark_id = provider.isbn_to_ark("9782070360284")

        Note:
            - Uses BNF's SRU (Search/Retrieve via URL) API with UNIMARC XML format.
            - ISBN is automatically cleaned (hyphens and spaces removed) before query.
            - Extracts ARK identifier from the <mxc:record id> attribute.
            - Returns None if no matching record is found or on API errors.
        """
        with suppress(Exception):
            # Clean ISBN (remove hyphens and spaces)
            clean_isbn_value = clean_isbn(isbn)

            # Query BNF SRU API for ISBN
            sru_url = f"https://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.isbn%20all%20%22{clean_isbn_value}%22&recordSchema=unimarcxchange&maximumRecords=1"
            response = fetch_with_retries(sru_url, timeout=10)

            if response.status_code != requests.codes.ok:
                return None

            # Parse XML response to extract ARK identifier
            root = ElementTree.fromstring(response.content)

            # Define namespace for SRU and MARC XML
            namespaces = {"srw": "http://www.loc.gov/zing/srw/", "mxc": "info:lc/xmlns/marcxchange-v2"}

            # Find the MARC record with id attribute containing ARK
            if (marc_record := root.find(".//mxc:record[@id]", namespaces)) is not None and (
                ark_id := marc_record.get("id")
            ):
                return ark_id

            return None

        return None

    @handle_provider_errors("BNF")
    def get_thumbnail_url(self, isbn):
        """Retrieve the cover URL for a book from BNF.

        This method uses the BNF catalogue API to retrieve book cover images
        by first converting the ISBN to an ARK identifier via the SRU API,
        then constructing the cover image URL with the required parameters.

        :param isbn: The ISBN of the document (ISBN-10 or ISBN-13, with or without hyphens/spaces).
        :returns: tuple - (url, provider_name) where url is the direct URL to the book
            cover image if found (None otherwise), and provider_name is "bnf".

        Examples:
            >>> provider = BnfProvider()
            >>> # Using ISBN with hyphens
            >>> url, provider = provider.get_thumbnail_url("978-2-07-036028-4")
            >>> print(url, provider)
            http://catalogue.bnf.fr/couverture?appName=NE&idArk=ark:/12148/cb450989938&couverture=1 bnf
            >>> # Using clean ISBN
            >>> url, provider = provider.get_thumbnail_url("9782070360284")

        Note:
            - Uses the official BNF catalogue API (no authentication required).
            - ISBN is automatically cleaned and converted to ARK identifier via SRU API.
            - Returns (None, "bnf") if ISBN cannot be converted to ARK or cover doesn't exist.
            - The service returns JPEG or PNG images.
            - Validates image content (size and dimensions) before returning URL.
        """
        # Clean ISBN (remove hyphens and spaces)
        clean_isbn_value = clean_isbn(isbn)

        # Try to convert ISBN to ARK
        ark_id = self.isbn_to_ark(clean_isbn_value)
        if not ark_id:
            # If conversion fails, return None
            return None, "bnf"

        # Construct URL with required BNF API parameters
        url = f"{self.base_url}?appName={self.app_name}&idArk={ark_id}&couverture={self.cover_page}"
        response = fetch_with_retries(url, timeout=10)
        status_code = response.status_code

        if (
            status_code == requests.codes.ok
            and (response.headers.get("Content-Type", "")).startswith("image/")
            and validate_image_content(response.content, "BNF", clean_isbn_value)
        ):
            return url, "bnf"

        return None, "bnf"
