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

"""Tests for GoogleApiProvider."""

from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from rero_invenio_thumbnails.modules.google_api.api import GoogleApiProvider


@pytest.fixture
def google_api_provider():
    """Create a GoogleApiProvider instance for testing."""
    return GoogleApiProvider()


class TestGoogleApiProviderGetThumbnailUrl:
    """Test GoogleApiProvider.get_thumbnail_url method."""

    @patch("rero_invenio_thumbnails.modules.google_api.api.requests_retry_session")
    def test_get_thumbnail_url_success(self, mock_retry_session, app, google_api_provider):
        """Test successful thumbnail URL retrieval."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "totalItems": 1,
                "items": [
                    {"volumeInfo": {"imageLinks": {"thumbnail": "http://books.google.com/books/content?id=xxxxx"}}}
                ],
            }
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is not None
            assert "books.google.com" in url
            mock_retry_session.assert_called_once()
            mock_session.get.assert_called_once_with(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}")

    @patch("rero_invenio_thumbnails.modules.google_api.api.requests_retry_session")
    def test_get_thumbnail_url_not_found(self, mock_retry_session, app, google_api_provider):
        """Test thumbnail URL retrieval when book not found."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"totalItems": 0, "items": []}
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.google_api.api.requests_retry_session")
    def test_get_thumbnail_url_multiple_results(self, mock_retry_session, app, google_api_provider):
        """Test thumbnail URL retrieval when multiple results found."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "totalItems": 3,
                "items": [
                    {"volumeInfo": {"imageLinks": {"thumbnail": "http://example.com/thumb1"}}},
                    {"volumeInfo": {"imageLinks": {"thumbnail": "http://example.com/thumb2"}}},
                    {"volumeInfo": {"imageLinks": {"thumbnail": "http://example.com/thumb3"}}},
                ],
            }
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.google_api.api.requests_retry_session")
    def test_get_thumbnail_url_no_image_links(self, mock_retry_session, app, google_api_provider):
        """Test thumbnail URL retrieval when no image links available."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "totalItems": 1,
                "items": [{"volumeInfo": {}}],
            }
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.google_api.api.requests_retry_session")
    def test_get_thumbnail_url_server_error(self, mock_retry_session, app, google_api_provider):
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
            url = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.google_api.api.requests_retry_session")
    def test_get_thumbnail_url_request_exception(self, mock_retry_session, app, google_api_provider):
        """Test thumbnail URL retrieval with request exception."""
        with app.app_context():
            # Setup mocks to raise exception
            mock_session = MagicMock()
            mock_session.get.side_effect = requests.RequestException("Connection error")
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None

    @patch("rero_invenio_thumbnails.modules.google_api.api.requests_retry_session")
    def test_get_thumbnail_url_api_endpoint(self, mock_retry_session, app, google_api_provider):
        """Test that correct API endpoint is called."""
        with app.app_context():
            # Setup mocks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "totalItems": 1,
                "items": [
                    {"volumeInfo": {"imageLinks": {"thumbnail": "http://books.google.com/books/content?id=xxxxx"}}}
                ],
            }
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            call_args = mock_session.get.call_args[0][0]
            assert "googleapis.com" in call_args
            assert "isbn:" in call_args
            assert isbn in call_args

    @patch("rero_invenio_thumbnails.modules.google_api.api.requests_retry_session")
    def test_get_thumbnail_url_json_parsing(self, mock_retry_session, app, google_api_provider):
        """Test JSON response parsing."""
        with app.app_context():
            # Setup mocks with nested structure
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "totalItems": 1,
                "items": [
                    {
                        "id": "some-id",
                        "volumeInfo": {
                            "title": "Test Book",
                            "imageLinks": {
                                "smallThumbnail": "http://example.com/small",
                                "thumbnail": "http://example.com/thumb",
                            },
                        },
                    }
                ],
            }
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_retry_session.return_value = mock_session

            # Test
            isbn = "9780134685991"
            url = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url == "http://example.com/thumb"
