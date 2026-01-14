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

"""Tests for OpenLibraryProvider."""

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from rero_invenio_thumbnails.modules.open_library.api import OpenLibraryProvider


@pytest.fixture
def open_library_provider():
    """Create an OpenLibraryProvider instance for testing."""
    return OpenLibraryProvider()


class TestOpenLibraryProviderGetThumbnailUrl:
    """Test OpenLibraryProvider.get_thumbnail_url method."""

    @patch("rero_invenio_thumbnails.modules.open_library.api.requests_retry_session")
    def test_get_thumbnail_url_success(self, mock_retry_session, app, open_library_provider):
        """Test successful thumbnail URL retrieval."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is not None
            assert "covers.openlibrary.org" in url
            assert isbn in url
            assert "-L.jpg" in url
            assert "default=false" in url
            mock_retry_session.assert_called_once()

    @patch("rero_invenio_thumbnails.modules.open_library.api.requests_retry_session")
    def test_get_thumbnail_url_not_found(self, mock_retry_session, app, open_library_provider):
        """Test thumbnail URL retrieval when book not found (404)."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 404
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.open_library.api.requests_retry_session")
    def test_get_thumbnail_url_server_error(self, mock_retry_session, app, open_library_provider):
        """Test thumbnail URL retrieval with server error."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 500
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.open_library.api.requests_retry_session")
    def test_get_thumbnail_url_format(self, mock_retry_session, app, open_library_provider):
        """Test thumbnail URL format."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            expected_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
            assert url == expected_url

    @patch("rero_invenio_thumbnails.modules.open_library.api.requests_retry_session")
    def test_get_thumbnail_url_isbn10(self, mock_retry_session, app, open_library_provider):
        """Test thumbnail URL with ISBN-10."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "0134685997"  # ISBN-10
            url = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is not None
            assert isbn in url

    @patch("rero_invenio_thumbnails.modules.open_library.api.requests_retry_session")
    def test_get_thumbnail_url_api_endpoint(self, mock_retry_session, app, open_library_provider):
        """Test that correct API endpoint is called."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            call_args = mock_session.get.call_args[0][0]
            assert "covers.openlibrary.org" in call_args
            assert "/b/isbn/" in call_args
            assert "-L.jpg" in call_args
            assert isbn in call_args

    @patch("rero_invenio_thumbnails.modules.open_library.api.requests_retry_session")
    def test_get_thumbnail_url_request_exception(self, mock_retry_session, app, open_library_provider):
        """Test thumbnail URL retrieval with request exception."""
        with app.app_context():
            # Setup mocks to raise exception
            mock_session = MagicMock()
            mock_session.get.side_effect = requests.RequestException("Connection error")
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.open_library.api.requests_retry_session")
    def test_get_thumbnail_url_multiple_calls(self, mock_retry_session, app, open_library_provider):
        """Test multiple consecutive calls."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbns = ["9780134685991", "9780596007124", "9781491954936"]
            urls = [open_library_provider.get_thumbnail_url(isbn) for isbn in isbns]

            # Assertions
            assert all(url is not None for url in urls)
            assert len(set(urls)) == 3  # All unique
            for url, isbn in zip(urls, isbns):
                assert isbn in url

    @patch("rero_invenio_thumbnails.modules.open_library.api.requests_retry_session")
    def test_get_thumbnail_url_default_parameter(self, mock_retry_session, app, open_library_provider):
        """Test that default=false parameter is included."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert "default=false" in url

    @patch("rero_invenio_thumbnails.modules.open_library.api.requests_retry_session")
    def test_get_thumbnail_url_different_status_codes(self, mock_retry_session, app, open_library_provider):
        """Test handling of different HTTP status codes."""
        with app.app_context():
            # Test various status codes
            status_codes = [200, 201, 204, 400, 401, 403, 404, 500, 502, 503]

            for status_code in status_codes:
                # Setup mocks
                mock_response = Mock()
                mock_response.status_code = status_code
                mock_session = MagicMock()
                mock_session.get.return_value = mock_response
                mock_retry_session.return_value = mock_session

                # Test
                isbn = "9780134685991"
                url = open_library_provider.get_thumbnail_url(isbn)

                # Assertions
                if status_code == 200:
                    assert url is not None
                else:
                    assert url is None
