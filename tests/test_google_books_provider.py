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
import re

import pytest
import requests

from rero_invenio_thumbnails.modules.google_books.api import GoogleBooksProvider


@pytest.fixture
def google_books_provider():
    """Create a GoogleBooksProvider instance for testing."""
    return GoogleBooksProvider()


class TestGoogleBooksProviderGetThumbnailUrl:
    """Test GoogleBooksProvider.get_thumbnail_url method."""

    def test_get_thumbnail_url_success(self, app, google_books_provider, requests_mock):
        """Test successful thumbnail URL retrieval."""
        with app.app_context():
            # Setup JSONP API response
            thumbnail_url = "https://books.google.com/books/about/book"
            response_data = {"9780134685991": {"thumbnail_url": thumbnail_url}}
            response_text = f"book({json.dumps(response_data)})"
            requests_mock.get("https://books.google.com/books", text=response_text, status_code=200)
            # Mock the thumbnail image validation
            requests_mock.get(thumbnail_url, content=create_test_image(), status_code=200)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is not None
            assert provider_name == "google books"
            assert "books.google.com" in url

    def test_get_thumbnail_url_not_found(self, app, google_books_provider, requests_mock):
        """Test thumbnail URL retrieval when book not found."""
        with app.app_context():
            # Setup response with empty data
            response_data = {}
            response_text = f"book({json.dumps(response_data)})"
            requests_mock.get(re.compile(r".*"), text=response_text, status_code=200)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "google books"

    def test_get_thumbnail_url_no_preview(self, app, google_books_provider, requests_mock):
        """Test thumbnail URL retrieval when no preview available."""
        with app.app_context():
            # Setup response - book exists but no preview_url
            response_data = {"9780134685991": {"title": "Test Book"}}
            response_text = f"book({json.dumps(response_data)})"
            requests_mock.get(re.compile(r".*"), text=response_text, status_code=200)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "google books"

    def test_get_thumbnail_url_server_error(self, app, google_books_provider, requests_mock):
        """Test thumbnail URL retrieval with server error."""
        with app.app_context():
            # Setup response with 500 error
            requests_mock.get(re.compile(r".*"), status_code=500)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "google books"

    def test_get_thumbnail_url_jsonp_parsing(self, app, google_books_provider, requests_mock):
        """Test JSONP response parsing."""
        with app.app_context():
            # Setup response with JSONP format
            thumbnail_url = "https://books.google.com/books/about/test"
            response_data = {
                "9780134685991": {
                    "thumbnail_url": thumbnail_url,
                    "info_url": "https://books.google.com/books?id=test",
                }
            }
            response_text = f"book({json.dumps(response_data)})"
            requests_mock.get("https://books.google.com/books", text=response_text, status_code=200)
            # Mock the thumbnail image validation
            requests_mock.get(thumbnail_url, content=create_test_image(), status_code=200)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url == "https://books.google.com/books/about/test"
            assert provider_name == "google books"

    def test_get_thumbnail_url_api_endpoint(self, app, google_books_provider, requests_mock):
        """Test that correct API endpoint is called."""
        with app.app_context():
            # Setup response
            response_data = {}
            response_text = f"book({json.dumps(response_data)})"
            requests_mock.get(re.compile(r".*"), text=response_text, status_code=200)

            # Test
            isbn = "9780134685991"
            google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert len(requests_mock.request_history) > 0
            request_url = requests_mock.request_history[0].url
            assert "books.google.com" in request_url
            assert "jscmd=viewapi" in request_url
            assert "callback=book" in request_url
            assert isbn in request_url

    def test_get_thumbnail_url_request_exception(self, app, google_books_provider, requests_mock):
        """Test thumbnail URL retrieval with request exception."""
        with app.app_context():
            # Setup exception
            requests_mock.get(re.compile(r".*"), exc=requests.RequestException("Connection error"))

            # Test
            isbn = "9780134685991"
            url, provider_name = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "google books"

    def test_get_thumbnail_url_json_decode_error(self, app, google_books_provider, requests_mock):
        """Test thumbnail URL retrieval with malformed JSON."""
        with app.app_context():
            # Setup response with invalid JSON
            requests_mock.get(re.compile(r".*"), text="book(invalid json)", status_code=200)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "google books"

    def test_get_thumbnail_url_multiple_isbns(self, app, google_books_provider, requests_mock):
        """Test thumbnail URL retrieval with multiple ISBN responses."""
        with app.app_context():
            # Setup response with multiple ISBNs
            url1 = "https://books.google.com/books/about/book1"
            url2 = "https://books.google.com/books/about/book2"
            response_data = {
                "9780134685991": {"thumbnail_url": url1},
                "9780596007124": {"thumbnail_url": url2},
            }
            response_text = f"book({json.dumps(response_data)})"
            requests_mock.get("https://books.google.com/books", text=response_text, status_code=200)
            # Mock both thumbnail URLs for image validation
            requests_mock.get(url1, content=create_test_image(), status_code=200)
            requests_mock.get(url2, content=create_test_image(), status_code=200)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url == "https://books.google.com/books/about/book1"
            assert provider_name == "google books"

    def test_get_thumbnail_url_unexpected_format(self, app, google_books_provider, requests_mock):
        """Test thumbnail URL retrieval with unexpected JSONP format (no parentheses)."""
        with app.app_context():
            # Setup response with unexpected format
            requests_mock.get(re.compile(r".*"), text="invalid response without parentheses", status_code=200)

            # Test
            isbn = "9780134685991"
            url, provider_name = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "google books"

    def test_get_thumbnail_url_generic_exception(self, app, google_books_provider, requests_mock):
        """Test thumbnail URL retrieval with generic exception."""
        with app.app_context():
            # Setup exception
            requests_mock.get(re.compile(r".*"), exc=RuntimeError("Unexpected error"))

            # Test
            isbn = "9780134685991"
            url, provider_name = google_books_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "google books"
