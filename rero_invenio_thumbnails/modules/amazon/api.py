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

"""Thumbnails Amazon."""

import requests
from isbnlib import to_isbn10

from rero_invenio_thumbnails.modules.utils import (
    clean_isbn,
    fetch_with_retries,
    handle_provider_errors,
    validate_image_content,
)


class AmazonProvider:
    """Thumbnail provider for Amazon product images.

    This provider fetches book cover thumbnails from Amazon using ISBN numbers.
    It converts ISBN-13 to ISBN-10 format as required by Amazon's API.
    """

    def __init__(self, country="08", size="SCLZZZZZZZ"):
        """Initialize the Amazon provider.

        :param country: Amazon country code for the image URL. Defaults to "08".
            Available country codes:
            - "01": United Kingdom (amazon.co.uk)
            - "02": Germany (amazon.de)
            - "03": France (amazon.fr)
            - "05": Canada (amazon.ca)
            - "06": Japan (amazon.co.jp)
            - "07": China (amazon.cn)
            - "08": United States (amazon.com)
            - "09": Spain (amazon.es)
            - "10": Italy (amazon.it)
            - "11": Australia (amazon.com.au)
            - "12": Mexico (amazon.com.mx)
            - "13": Brazil (amazon.com.br)
            - "14": India (amazon.in)

        :param size: Amazon image size code. Defaults to "SCLZZZZZZZ".
            Available sizes:
            - "THUMBZZZZZZZ": Thumbnail (smallest, ~80x80px)
            - "TZZZZZZZZZ": Small (~110x160px)
            - "MZZZZZZZZZ": Medium (~160x240px)
            - "LZZZZZZZZZ": Large (~200x300px)
            - "SCLZZZZZZZ": Standard (recommended, ~500x500px)

        Examples:
            >>> # Default US provider
            >>> provider = AmazonProvider()
            >>> # UK provider with small size
            >>> provider_uk = AmazonProvider(country="01", size="MZZZZZZZZZ")
            >>> # German provider with large size
            >>> provider_de = AmazonProvider(country="02", size="LZZZZZZZZZ")
        """
        self.country = country
        self.size = size

    @handle_provider_errors("Amazon")
    def get_thumbnail_url(self, isbn):
        """Retrieve the thumbnail URL for a book from Amazon.

        This method converts the ISBN to ISBN-10 format (as required by Amazon),
        constructs the image URL, and verifies that the product exists on Amazon.

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13 format).
        :returns: str or None - The URL of the book cover thumbnail if the product exists
            on Amazon, None if not found or request fails.

        Examples:
            >>> provider = AmazonProvider()
            >>> url = provider.get_thumbnail_url("9780134685991")
            >>> print(url)
            https://images-na.ssl-images-amazon.com/images/P/0134685997.08._SCLZZZZZZZ_.jpg

        Note:
            - This method requires internet connectivity to verify the product.
            - Amazon may block requests without proper User-Agent headers.
            - Automatic retries are used for transient failures.
        """
        # Clean ISBN (remove hyphens and spaces) and convert to ISBN-10
        clean_isbn_value = clean_isbn(isbn)
        isbn = to_isbn10(clean_isbn_value)
        url = f"https://images-na.ssl-images-amazon.com/images/P/{isbn}.{self.country}._{self.size}_.jpg"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = fetch_with_retries(url, headers=headers, timeout=5)
        status_code = response.status_code
        if status_code == requests.codes.ok and validate_image_content(response.content, "Amazon", isbn):
            return url
        return None
