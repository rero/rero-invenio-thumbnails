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

"""Tests for GoogleBooksProvider."""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from rero_invenio_thumbnails.modules.google_books.api import GoogleBooksProvider


@pytest.fixture
def google_books_provider():
    """Create a GoogleBooksProvider instance for testing."""
    return GoogleBooksProvider()


class TestGoogleBooksProviderGetThumbnailUrl:
    """Test GoogleBooksProvider.get_thumbnail_url method."""

    @patch("rero_invenio_thumbnails.modules.google_books.api.requests_retry_session")
    def test_get_thumbnail_url_success(self, mock_retry_session, app, google_books_provider):
        """Test successful thumbnail URL retrieval."""
        with app.app_context():
            # Setup mocks
            response_data = {"9780134685991": {"preview_url": "https://books.google.com/books/about/book"}}
            response_text = f"book({json.dumps(response_data)})"

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = response_text
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is not None
            assert "books.google.com" in url
            mock_retry_session.assert_called_once()

    @patch("rero_invenio_thumbnails.modules.google_books.api.requests_retry_session")
    def test_get_thumbnail_url_not_found(self, mock_retry_session, app, google_books_provider):
        """Test thumbnail URL retrieval when book not found."""
        with app.app_context():
            # Setup mocks
            response_data = {}
            response_text = f"book({json.dumps(response_data)})"

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = response_text
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.google_books.api.requests_retry_session")
    def test_get_thumbnail_url_no_preview(self, mock_retry_session, app, google_books_provider):
        """Test thumbnail URL retrieval when no preview available."""
        with app.app_context():
            # Setup mocks - book exists but no preview_url
            response_data = {"9780134685991": {"title": "Test Book"}}
            response_text = f"book({json.dumps(response_data)})"

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = response_text
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.google_books.api.requests_retry_session")
    def test_get_thumbnail_url_server_error(self, mock_retry_session, app, google_books_provider):
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
            url = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.google_books.api.requests_retry_session")
    def test_get_thumbnail_url_jsonp_parsing(self, mock_retry_session, app, google_books_provider):
        """Test JSONP response parsing."""
        with app.app_context():
            # Setup mocks with JSONP format
            response_data = {
                "9780134685991": {
                    "preview_url": "https://books.google.com/books/about/test",
                    "info_url": "https://books.google.com/books?id=test",
                }
            }
            response_text = f"book({json.dumps(response_data)})"

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = response_text
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url == "https://books.google.com/books/about/test"

    @patch("rero_invenio_thumbnails.modules.google_books.api.requests_retry_session")
    def test_get_thumbnail_url_api_endpoint(self, mock_retry_session, app, google_books_provider):
        """Test that correct API endpoint is called."""
        with app.app_context():
            # Setup mocks
            response_data = {}
            response_text = f"book({json.dumps(response_data)})"

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = response_text
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            call_args = mock_session.get.call_args[0][0]
            assert "books.google.com" in call_args
            assert "jscmd=viewapi" in call_args
            assert "callback=book" in call_args
            assert isbn in call_args

    @patch("rero_invenio_thumbnails.modules.google_books.api.requests_retry_session")
    def test_get_thumbnail_url_request_exception(self, mock_retry_session, app, google_books_provider):
        """Test thumbnail URL retrieval with request exception."""
        with app.app_context():
            # Setup mocks to raise exception
            mock_session = MagicMock()
            mock_session.get.side_effect = requests.RequestException("Connection error")
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.google_books.api.requests_retry_session")
    def test_get_thumbnail_url_json_decode_error(self, mock_retry_session, app, google_books_provider):
        """Test thumbnail URL retrieval with malformed JSON."""
        with app.app_context():
            # Setup mocks with invalid JSON
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "book(invalid json)"
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.google_books.api.requests_retry_session")
    def test_get_thumbnail_url_multiple_isbns(self, mock_retry_session, app, google_books_provider):
        """Test thumbnail URL retrieval with multiple ISBN responses."""
        with app.app_context():
            # Setup mocks
            response_data = {
                "9780134685991": {"preview_url": "https://books.google.com/books/about/book1"},
                "9780596007124": {"preview_url": "https://books.google.com/books/about/book2"},
            }
            response_text = f"book({json.dumps(response_data)})"

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = response_text
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url == "https://books.google.com/books/about/book1"

    @patch("rero_invenio_thumbnails.modules.google_books.api.requests_retry_session")
    def test_get_thumbnail_url_unexpected_format(self, mock_retry_session, app, google_books_provider):
        """Test thumbnail URL retrieval with unexpected JSONP format (no parentheses)."""
        with app.app_context():
            # Setup mocks with response missing JSONP parentheses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "invalid response without parentheses"
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.google_books.api.requests_retry_session")
    def test_get_thumbnail_url_generic_exception(self, mock_retry_session, app, google_books_provider):
        """Test thumbnail URL retrieval with generic exception."""
        with app.app_context():
            # Setup mocks to raise a generic exception (not RequestException)
            mock_session = MagicMock()
            mock_session.get.side_effect = RuntimeError("Unexpected error")
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
