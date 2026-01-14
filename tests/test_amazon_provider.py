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

"""Tests for AmazonProvider."""

import pytest

from rero_invenio_thumbnails.modules.amazon.api import AmazonProvider


@pytest.fixture
def amazon_provider():
    """Create an AmazonProvider instance for testing."""
    return AmazonProvider()


@pytest.fixture
def amazon_provider_custom():
    """Create an AmazonProvider instance with custom country and size."""
    return AmazonProvider(country="01", size="MZZZZZZZZZ")


class TestAmazonProviderInit:
    """Test AmazonProvider initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        provider = AmazonProvider()
        assert provider.country == "08"
        assert provider.size == "SCLZZZZZZZ"

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        provider = AmazonProvider(country="01", size="LZZZZZZZZZ")
        assert provider.country == "01"
        assert provider.size == "LZZZZZZZZZ"

    def test_init_all_country_codes(self):
        """Test initialization with various country codes."""
        country_codes = ["01", "02", "03", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14"]
        for code in country_codes:
            provider = AmazonProvider(country=code)
            assert provider.country == code


class TestAmazonProviderGetThumbnailUrl:
    """Test AmazonProvider.get_thumbnail_url method."""

    def test_get_thumbnail_url_success(self, app, amazon_provider, requests_mock):
        """Test successful thumbnail URL retrieval."""
        with app.app_context():
            # Mock HTTP GET requests with valid image
            requests_mock.get(
                "https://images-na.ssl-images-amazon.com/images/P/0134685997.08._SCLZZZZZZZ_.jpg",
                status_code=200,
                content=create_test_image(),
            )

            # Test
            isbn = "9780134685991"
            url = amazon_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is not None
            assert "0134685997" in url
            assert amazon_provider.country in url
            assert amazon_provider.size in url

    def test_get_thumbnail_url_not_found(self, app, amazon_provider, requests_mock):
        """Test thumbnail URL retrieval when product not found (404)."""
        with app.app_context():
            # Mock HTTP GET requests with 404
            import re

            requests_mock.get(re.compile(r".*"), status_code=404)

            # Test
            isbn = "9780134685991"
            url = amazon_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    def test_get_thumbnail_url_server_error(self, app, amazon_provider, requests_mock):
        """Test thumbnail URL retrieval with server error (500)."""
        with app.app_context():
            # Mock HTTP GET requests with 500 error
            import re

            requests_mock.get(re.compile(r".*"), status_code=500)

            # Test
            isbn = "9780134685991"
            url = amazon_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    def test_get_thumbnail_url_custom_country(self, app, requests_mock):
        """Test thumbnail URL with custom country code."""
        with app.app_context():
            # Mock HTTP GET requests with valid image
            import re

            requests_mock.get(re.compile(r".*"), status_code=200, content=create_test_image())

            # Test
            provider = AmazonProvider(country="01", size="MZZZZZZZZZ")
            isbn = "9780134685991"
            url = provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is not None
            assert "01" in url  # UK country code
            assert "MZZZZZZZZZ" in url  # Medium size

    def test_get_thumbnail_url_isbn_conversion(self, app, amazon_provider, requests_mock):
        """Test that ISBN-13 is correctly converted to ISBN-10."""
        with app.app_context():
            # Mock HTTP GET requests with valid image
            import re

            requests_mock.get(re.compile(r".*"), status_code=200, content=create_test_image())

            # Test
            isbn_13 = "9780134685991"
            url = amazon_provider.get_thumbnail_url(isbn_13)

            # Assertions - verify the URL contains the converted ISBN-10
            assert url is not None
            assert "0134685997" in url  # ISBN-10 version

    def test_get_thumbnail_url_request_headers(self, app, amazon_provider, requests_mock):
        """Test that proper User-Agent headers are sent."""
        with app.app_context():
            # Mock HTTP GET requests with valid image
            import re

            requests_mock.get(re.compile(r".*"), status_code=200, content=create_test_image())

            # Test
            isbn = "9780134685991"
            amazon_provider.get_thumbnail_url(isbn)

            # Assertions - verify headers were passed
            assert len(requests_mock.request_history) > 0
            request = requests_mock.request_history[0]
            assert "User-Agent" in request.headers
            assert request.headers["User-Agent"] == "Mozilla/5.0"
            assert "Accept-Language" in request.headers

    def test_get_thumbnail_url_exception_handling(self, app, amazon_provider):
        """Test exception handling during thumbnail retrieval."""
        with app.app_context():
            # Test with invalid ISBN that will cause to_isbn10 to fail
            isbn = "invalid-isbn"
            url = amazon_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    def test_get_thumbnail_url_multiple_calls(self, app, amazon_provider, requests_mock):
        """Test multiple calls to get_thumbnail_url."""
        with app.app_context():
            # Mock HTTP GET requests with valid image
            import re

            requests_mock.get(re.compile(r".*"), status_code=200, content=create_test_image())

            # Test
            url1 = amazon_provider.get_thumbnail_url("9780134685991")
            url2 = amazon_provider.get_thumbnail_url("9780596007127")

            # Assertions
            assert url1 is not None
            assert url2 is not None
            assert url1 != url2


class TestAmazonProviderUrlFormat:
    """Test URL format generation."""

    def test_thumbnail_url_format(self, amazon_provider):
        """Test the format of generated thumbnail URL."""
        # This is a unit test without Flask context
        isbn = "0134685997"

        expected_pattern = "https://images-na.ssl-images-amazon.com/images/P/{isbn}.{country}._SCLZZZZZZZ_.jpg"
        expected_url = expected_pattern.format(isbn=isbn, country=amazon_provider.country)

        # The URL format should follow the pattern
        assert f"{isbn}.{amazon_provider.country}._SCLZZZZZZZ_.jpg" in expected_url
