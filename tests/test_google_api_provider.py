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

import re

import pytest
import requests

from rero_invenio_thumbnails.modules.google_api.api import GoogleApiProvider


@pytest.fixture
def google_api_provider():
    """Create a GoogleApiProvider instance for testing."""
    return GoogleApiProvider()


class TestGoogleApiProviderGetThumbnailUrl:
    """Test GoogleApiProvider.get_thumbnail_url method."""

    def test_get_thumbnail_url_success(self, app, google_api_provider, requests_mock):
        """Test successful thumbnail URL retrieval."""
        with app.app_context():
            # Setup API response
            thumbnail_url = "http://books.google.com/books/content?id=xxxxx"
            response_data = {
                "totalItems": 1,
                "items": [{"volumeInfo": {"imageLinks": {"thumbnail": thumbnail_url}}}],
            }
            requests_mock.get("https://www.googleapis.com/books/v1/volumes", json=response_data, status_code=200)
            # Mock the thumbnail image validation
            requests_mock.get(thumbnail_url, content=create_test_image(), status_code=200)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is not None
            assert provider_name == "google api"
            assert "books.google.com" in url

    def test_get_thumbnail_url_not_found(self, app, google_api_provider, requests_mock):
        """Test thumbnail URL retrieval when book not found."""
        with app.app_context():
            # Setup response with no results
            response_data = {"totalItems": 0, "items": []}
            requests_mock.get(re.compile(r".*"), json=response_data, status_code=200)

            # Test
            isbn = "9780134685991"
            url = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url == (None, "google api")

    def test_get_thumbnail_url_multiple_results(self, app, google_api_provider, requests_mock):
        """Test thumbnail URL retrieval when multiple results found."""
        with app.app_context():
            # Setup response with multiple results
            response_data = {
                "totalItems": 3,
                "items": [
                    {"volumeInfo": {"imageLinks": {"thumbnail": "http://example.com/thumb1"}}},
                    {"volumeInfo": {"imageLinks": {"thumbnail": "http://example.com/thumb2"}}},
                    {"volumeInfo": {"imageLinks": {"thumbnail": "http://example.com/thumb3"}}},
                ],
            }
            requests_mock.get(re.compile(r".*"), json=response_data, status_code=200)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "google api"

    def test_get_thumbnail_url_no_image_links(self, app, google_api_provider, requests_mock):
        """Test thumbnail URL retrieval when no image links available."""
        with app.app_context():
            # Setup response with no image links
            response_data = {"totalItems": 1, "items": [{"volumeInfo": {}}]}
            requests_mock.get(re.compile(r".*"), json=response_data, status_code=200)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "google api"

    def test_get_thumbnail_url_server_error(self, app, google_api_provider, requests_mock):
        """Test thumbnail URL retrieval with server error."""
        with app.app_context():
            # Setup response with 500 error
            requests_mock.get(re.compile(r".*"), status_code=500)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "google api"

    def test_get_thumbnail_url_request_exception(self, app, google_api_provider, requests_mock):
        """Test thumbnail URL retrieval with request exception."""
        with app.app_context():
            # Setup exception
            requests_mock.get(re.compile(r".*"), exc=requests.RequestException("Connection error"))

            # Test
            isbn = "9780134685991"
            url, provider_name = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "google api"

    def test_get_thumbnail_url_api_endpoint(self, app, google_api_provider, requests_mock):
        """Test that correct API endpoint is called."""
        with app.app_context():
            # Setup response
            response_data = {
                "totalItems": 1,
                "items": [
                    {"volumeInfo": {"imageLinks": {"thumbnail": "http://books.google.com/books/content?id=xxxxx"}}}
                ],
            }
            requests_mock.get(re.compile(r".*"), json=response_data, status_code=200)

            # Test
            isbn = "9780134685991"
            google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert len(requests_mock.request_history) > 0
            request_url = requests_mock.request_history[0].url
            assert "googleapis.com" in request_url
            assert "isbn:" in request_url
            assert isbn in request_url

    def test_get_thumbnail_url_json_parsing(self, app, google_api_provider, requests_mock):
        """Test JSON response parsing."""
        with app.app_context():
            # Setup response with nested structure
            thumbnail_url = "http://example.com/thumb"
            response_data = {
                "totalItems": 1,
                "items": [
                    {
                        "id": "some-id",
                        "volumeInfo": {
                            "title": "Test Book",
                            "imageLinks": {
                                "smallThumbnail": "http://example.com/small",
                                "thumbnail": thumbnail_url,
                            },
                        },
                    }
                ],
            }
            requests_mock.get("https://www.googleapis.com/books/v1/volumes", json=response_data, status_code=200)
            # Mock the thumbnail image validation
            requests_mock.get(thumbnail_url, content=create_test_image(), status_code=200)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_api_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url == "http://example.com/thumb"
            assert provider_name == "google api"
            assert provider_name == "google api"
