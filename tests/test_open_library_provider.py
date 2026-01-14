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

import re

import pytest
import requests

from rero_invenio_thumbnails.modules.open_library.api import OpenLibraryProvider

# Import create_test_image utility from conftest
from .conftest import create_test_image


@pytest.fixture
def open_library_provider():
    """Create an OpenLibraryProvider instance for testing."""
    return OpenLibraryProvider()


class TestOpenLibraryProviderGetThumbnailUrl:
    """Test OpenLibraryProvider.get_thumbnail_url method."""

    def test_get_thumbnail_url_success(self, app, open_library_provider, requests_mock):
        """Test successful thumbnail URL retrieval."""
        with app.app_context():
            # Mock HTTP GET requests with image content
            requests_mock.get(
                re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=create_test_image()
            )

            # Test
            isbn = "9780134685991"
            url, provider_name = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is not None
            assert provider_name == "open library"
            assert "covers.openlibrary.org" in url
            assert isbn in url
            assert "-L.jpg" in url
            assert "default=false" in url

    def test_get_thumbnail_url_not_found(self, app, open_library_provider, requests_mock):
        """Test thumbnail URL retrieval when book not found (404)."""
        with app.app_context():
            # Mock HTTP GET requests with 404
            requests_mock.get(re.compile(r".*"), status_code=404)

            # Test
            isbn = "9780134685991"
            url, provider_name = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "open library"

    def test_get_thumbnail_url_server_error(self, app, open_library_provider, requests_mock):
        """Test thumbnail URL retrieval with server error."""
        with app.app_context():
            # Mock HTTP GET requests with 500 error
            requests_mock.get(re.compile(r".*"), status_code=500)

            # Test
            isbn = "9780134685991"
            url, provider_name = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "open library"

    def test_get_thumbnail_url_format(self, app, open_library_provider, requests_mock):
        """Test thumbnail URL format."""
        with app.app_context():
            # Mock HTTP GET requests with valid image
            requests_mock.get(
                re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=create_test_image()
            )

            # Test
            isbn = "9780134685991"
            url, provider_name = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            expected_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
            assert url == expected_url
            assert provider_name == "open library"

    def test_get_thumbnail_url_isbn10(self, app, open_library_provider, requests_mock):
        """Test thumbnail URL with ISBN-10."""
        with app.app_context():
            # Mock HTTP GET requests with valid image
            requests_mock.get(
                re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=create_test_image()
            )

            # Test
            isbn = "0134685997"  # ISBN-10
            url, provider_name = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is not None
            assert provider_name == "open library"
            assert isbn in url

    def test_get_thumbnail_url_api_endpoint(self, app, open_library_provider, requests_mock):
        """Test that correct API endpoint is called."""
        with app.app_context():
            # Mock HTTP GET requests with valid image
            requests_mock.get(
                re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=create_test_image()
            )

            # Test
            isbn = "9780134685991"
            open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert len(requests_mock.request_history) > 0
            request_url = requests_mock.request_history[0].url
            assert "covers.openlibrary.org" in request_url
            assert "/b/isbn/" in request_url
            assert "-L.jpg" in request_url
            assert isbn in request_url

    def test_get_thumbnail_url_request_exception(self, app, open_library_provider, requests_mock):
        """Test thumbnail URL retrieval with request exception."""
        with app.app_context():
            # Mock HTTP GET requests to raise exception
            requests_mock.get(re.compile(r".*"), exc=requests.RequestException("Connection error"))

            # Test
            isbn = "9780134685991"
            url, provider_name = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert url is None
            assert provider_name == "open library"

    def test_get_thumbnail_url_multiple_calls(self, app, open_library_provider, requests_mock):
        """Test multiple consecutive calls."""
        with app.app_context():
            # Mock HTTP GET requests with valid image
            requests_mock.get(
                re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=create_test_image()
            )

            # Test
            isbns = ["9780134685991", "9780596007124", "9781491954936"]
            results = [open_library_provider.get_thumbnail_url(isbn) for isbn in isbns]
            urls = [r[0] for r in results]
            provider_names = [r[1] for r in results]

            # Assertions
            assert all(url is not None for url in urls)
            assert all(pn == "open library" for pn in provider_names)
            assert len(set(urls)) == 3  # All unique
            for url, isbn in zip(urls, isbns):
                assert isbn in url

    def test_get_thumbnail_url_default_parameter(self, app, open_library_provider, requests_mock):
        """Test that default=false parameter is included."""
        with app.app_context():
            # Mock HTTP GET requests with valid image
            requests_mock.get(
                re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=create_test_image()
            )

            # Test
            isbn = "9780134685991"
            url, provider_name = open_library_provider.get_thumbnail_url(isbn)

            # Assertions
            assert "default=false" in url
            assert provider_name == "open library"

    def test_get_thumbnail_url_different_status_codes(self, app, open_library_provider, requests_mock):
        """Test handling of different HTTP status codes."""
        with app.app_context():
            # Test various status codes
            status_codes = [200, 201, 204, 400, 401, 403, 404, 500, 502, 503]

            for status_code in status_codes:
                # Register mock for this status code
                headers = {"Content-Type": "image/jpeg"} if status_code == 200 else {}
                content = create_test_image() if status_code == 200 else b""
                requests_mock.get(re.compile(r".*"), status_code=status_code, headers=headers, content=content)

                # Test
                isbn = "9780134685991"
                url, provider_name = open_library_provider.get_thumbnail_url(isbn)

                # Assertions
                if status_code == 200:
                    assert url is not None
                else:
                    assert url is None
                assert provider_name == "open library"
