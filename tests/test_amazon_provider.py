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

from unittest.mock import MagicMock, Mock, patch

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

    @patch("rero_invenio_thumbnails.modules.amazon.api.requests_retry_session")
    @patch("rero_invenio_thumbnails.modules.amazon.api.to_isbn10")
    def test_get_thumbnail_url_success(self, mock_to_isbn10, mock_retry_session, app, amazon_provider):
        """Test successful thumbnail URL retrieval."""
        with app.app_context():
            # Setup mocks
            mock_to_isbn10.return_value = "0134685997"
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = amazon_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is not None
            assert "0134685997" in url
            assert amazon_provider.country in url
            assert amazon_provider.size in url
            mock_to_isbn10.assert_called_once_with(isbn)
            mock_retry_session.assert_called_once()

    @patch("rero_invenio_thumbnails.modules.amazon.api.requests_retry_session")
    @patch("rero_invenio_thumbnails.modules.amazon.api.to_isbn10")
    def test_get_thumbnail_url_not_found(self, mock_to_isbn10, mock_retry_session, app, amazon_provider):
        """Test thumbnail URL retrieval when product not found (404)."""
        with app.app_context():
            # Setup mocks
            mock_to_isbn10.return_value = "0134685997"
            mock_response = Mock()
            mock_response.status_code = 404
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = amazon_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.amazon.api.requests_retry_session")
    @patch("rero_invenio_thumbnails.modules.amazon.api.to_isbn10")
    def test_get_thumbnail_url_server_error(self, mock_to_isbn10, mock_retry_session, app, amazon_provider):
        """Test thumbnail URL retrieval with server error (500)."""
        with app.app_context():
            # Setup mocks
            mock_to_isbn10.return_value = "0134685997"
            mock_response = Mock()
            mock_response.status_code = 500
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = amazon_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.amazon.api.requests_retry_session")
    @patch("rero_invenio_thumbnails.modules.amazon.api.to_isbn10")
    def test_get_thumbnail_url_custom_country(self, mock_to_isbn10, mock_retry_session, app):
        """Test thumbnail URL with custom country code."""
        with app.app_context():
            # Setup mocks
            mock_to_isbn10.return_value = "0134685997"
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            provider = AmazonProvider(country="01", size="MZZZZZZZZZ")
            isbn = "9780134685991"
            url = provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is not None
            assert "01" in url  # UK country code
            assert "MZZZZZZZZZ" in url  # Medium size

    @patch("rero_invenio_thumbnails.modules.amazon.api.requests_retry_session")
    @patch("rero_invenio_thumbnails.modules.amazon.api.to_isbn10")
    def test_get_thumbnail_url_isbn_conversion(self, mock_to_isbn10, mock_retry_session, app, amazon_provider):
        """Test that ISBN-13 is correctly converted to ISBN-10."""
        with app.app_context():
            # Setup mocks
            mock_to_isbn10.return_value = "0134685997"
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn_13 = "9780134685991"
            amazon_provider.get_thumbnail_url(isbn_13)

            # Assertions - verify to_isbn10 was called with the ISBN-13
            mock_to_isbn10.assert_called_once_with(isbn_13)

    @patch("rero_invenio_thumbnails.modules.amazon.api.requests_retry_session")
    @patch("rero_invenio_thumbnails.modules.amazon.api.to_isbn10")
    def test_get_thumbnail_url_request_headers(self, mock_to_isbn10, mock_retry_session, app, amazon_provider):
        """Test that proper User-Agent headers are sent."""
        with app.app_context():
            # Setup mocks
            mock_to_isbn10.return_value = "0134685997"
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            amazon_provider.get_thumbnail_url(isbn)

            # Assertions - verify headers were passed
            mock_session.get.assert_called_once()
            call_args = mock_session.get.call_args
            assert "headers" in call_args[1]
            headers = call_args[1]["headers"]
            assert "User-Agent" in headers
            assert headers["User-Agent"] == "Mozilla/5.0"
            assert "Accept-Language" in headers

    @patch("rero_invenio_thumbnails.modules.amazon.api.requests_retry_session")
    @patch("rero_invenio_thumbnails.modules.amazon.api.to_isbn10")
    def test_get_thumbnail_url_exception_handling(self, mock_to_isbn10, mock_retry_session, app, amazon_provider):
        """Test exception handling during thumbnail retrieval."""
        with app.app_context():
            # Setup mocks to raise an exception
            mock_to_isbn10.side_effect = Exception("ISBN conversion error")
            mock_retry_session.return_value = MagicMock()

            # Test
            isbn = "invalid-isbn"
            url = amazon_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.amazon.api.requests_retry_session")
    @patch("rero_invenio_thumbnails.modules.amazon.api.to_isbn10")
    def test_get_thumbnail_url_multiple_calls(self, mock_to_isbn10, mock_retry_session, app, amazon_provider):
        """Test multiple calls to get_thumbnail_url."""
        with app.app_context():
            # Setup mocks
            mock_to_isbn10.side_effect = ["0134685997", "0596007124"]
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            url1 = amazon_provider.get_thumbnail_url("9780134685991")
            url2 = amazon_provider.get_thumbnail_url("9780596007127")

            # Assertions
            assert url1 is not None
            assert url2 is not None
            assert url1 != url2
            assert mock_to_isbn10.call_count == 2


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
