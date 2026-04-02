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

from contextlib import suppress
from xml.etree import ElementTree

import requests

from rero_invenio_thumbnails.contrib.api import BaseProvider
from rero_invenio_thumbnails.contrib.utils import (
    clean_isbn,
    fetch_and_validate_thumbnail,
    fetch_with_retries,
    handle_provider_errors,
)


class DnbProvider(BaseProvider):
    """Thumbnail provider for DNB (Deutsche Nationalbibliothek).

    This provider fetches book cover images from the German National Library's
    catalogue service using their SRU (Search/Retrieve via URL) interface.
    Cover image URLs are extracted from MARC21-XML metadata records.

    The DNB provides bibliographic data for publications received under German
    legal deposit and other collections of the German National Library.
    """

    name = "dnb"

    def __init__(self):
        """Initialize the DNB provider.

        Examples:
            >>> # Default provider
            >>> provider = DnbProvider()
        """
        self.base_url = "https://portal.dnb.de/opac/mvb/cover"
        self.sru_base_url = "https://services.dnb.de/sru/dnb"

    @handle_provider_errors("DNB")
    def get_thumbnail_url(self, isbn):
        """Retrieve thumbnail URL for an ISBN from DNB.

        This method queries the DNB SRU interface to find bibliographic records
        matching the ISBN and extracts cover image URLs from the MARC21-XML
        response. The cover URL is typically found in MARC field 856 (Electronic
        Location and Access) with specific indicators for cover images.

        :param isbn: The ISBN to search for (ISBN-10 or ISBN-13)
        :returns: tuple - (url, provider_name) where url is the cover image URL
            if found (None otherwise), and provider_name is "dnb".

        Example::

            provider = DnbProvider()
            url, name = provider.get_thumbnail_url("9783161484100")
            # url == "https://portal.dnb.de/opac/mvb/cover?isbn=9783161484100"

        Note:
            The DNB may not have cover images for all publications. Availability
            depends on whether the publisher provided cover metadata to the DNB.
        """
        isbn = clean_isbn(isbn)
        if not isbn:
            return None, self.name

        # Build DNB SRU query URL
        # Format: https://services.dnb.de/sru/dnb?version=1.1&operation=searchRetrieve&query=isbn=<ISBN>&recordSchema=MARC21-xml&maximumRecords=1
        url = f"{self.sru_base_url}?version=1.1&operation=searchRetrieve&query=isbn={isbn}&recordSchema=MARC21-xml&maximumRecords=1"

        response = fetch_with_retries(url, timeout=10)  # DNB API is slower
        if not response or response.status_code != requests.codes.ok:
            return None, self.name

        # Parse XML response
        with suppress(ElementTree.ParseError, Exception):
            root = ElementTree.fromstring(response.content)

            # Define XML namespaces used in DNB SRU response
            namespaces = {
                "srw": "http://www.loc.gov/zing/srw/",
                "marc": "http://www.loc.gov/MARC21/slim",
            }

            # Find all records in the response
            records = root.findall(".//srw:record", namespaces)
            if not records:
                return None, self.name

            # Search for cover URL in MARC field 856
            # Field 856 is "Electronic Location and Access"
            # We look for URLs with specific indicators for cover images
            for record in records:
                datafields = record.findall(".//marc:datafield[@tag='856']", namespaces)

                for datafield in datafields:
                    # Check for subfield 'u' which contains the URL
                    url_subfield = datafield.find("marc:subfield[@code='u']", namespaces)
                    if url_subfield is not None and url_subfield.text:
                        url = url_subfield.text.strip()

                        # Check if it's a cover/thumbnail URL
                        # DNB cover URLs typically contain 'cover' or 'thumbnail' in the path
                        if any(
                            keyword in url.lower() for keyword in ["cover", "thumbnail", "bild"]
                        ) and fetch_and_validate_thumbnail(url, "DNB", isbn, timeout=10):  # DNB API is slower
                            return url, self.name

                        # Also check subfield 'x' for notes/descriptions
                        note_subfield = datafield.find("marc:subfield[@code='x']", namespaces)
                        if note_subfield is not None and note_subfield.text:
                            note = note_subfield.text.lower()
                            if any(
                                keyword in note for keyword in ["cover", "umschlag", "thumbnail"]
                            ) and fetch_and_validate_thumbnail(url, "DNB", isbn, timeout=10):  # DNB API is slower
                                return url, self.name

                # Alternative: Check MARC field 020 for ISBN with cover URL extensions
                # Some DNB records include cover URLs constructed from ISBN
                isbn_fields = record.findall(".//marc:datafield[@tag='020']", namespaces)
                for isbn_field in isbn_fields:
                    isbn_subfield = isbn_field.find("marc:subfield[@code='a']", namespaces)
                    if isbn_subfield is not None:
                        # Construct DNB cover URL from ISBN
                        # Format: https://portal.dnb.de/opac/mvb/cover?isbn=<ISBN>
                        constructed_url = f"{self.base_url}?isbn={isbn}"
                        # Validate the constructed URL returns a real image
                        if fetch_and_validate_thumbnail(constructed_url, "DNB", isbn, timeout=10):  # DNB API is slower
                            return constructed_url, self.name

        return None, self.name
