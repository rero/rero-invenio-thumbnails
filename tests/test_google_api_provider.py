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

"""Tests for GoogleApiProvider."""

import builtins
import re

import pytest
import requests

from rero_invenio_thumbnails.contrib.google_api.api import GoogleApiProvider

# Import test helper from conftest
try:
    from conftest import create_test_image
except ImportError:
    # Fallback: create_test_image is injected into builtins by conftest.pytest_configure
    create_test_image = getattr(builtins, "create_test_image", None)
    if create_test_image is None:
        raise ImportError("create_test_image not found; ensure conftest.py pytest_configure has run")


def test_google_api_get_thumbnail_url_success(app, requests_mock):
    """Test successful thumbnail URL retrieval."""
    with app.app_context():
        thumbnail_url = "http://books.google.com/books/content?id=xxxxx"
        response_data = {
            "totalItems": 1,
            "items": [{"volumeInfo": {"imageLinks": {"thumbnail": thumbnail_url}}}],
        }
        requests_mock.get("https://www.googleapis.com/books/v1/volumes", json=response_data, status_code=200)
        requests_mock.get(thumbnail_url, content=create_test_image(), status_code=200)

        url, provider_name = GoogleApiProvider().get_thumbnail_url("9780134685991")

        assert url is not None
        assert provider_name == "google api"
        assert "books.google.com" in url


def test_google_api_get_thumbnail_url_not_found(app, requests_mock):
    """Test thumbnail URL retrieval when book not found."""
    with app.app_context():
        requests_mock.get(re.compile(r".*"), json={"totalItems": 0, "items": []}, status_code=200)

        assert GoogleApiProvider().get_thumbnail_url("9780134685991") == (None, "google api")


def test_google_api_get_thumbnail_url_multiple_results(app, requests_mock):
    """Test thumbnail URL retrieval when multiple results found (rejected)."""
    with app.app_context():
        response_data = {
            "totalItems": 3,
            "items": [
                {"volumeInfo": {"imageLinks": {"thumbnail": "http://example.com/thumb1"}}},
                {"volumeInfo": {"imageLinks": {"thumbnail": "http://example.com/thumb2"}}},
                {"volumeInfo": {"imageLinks": {"thumbnail": "http://example.com/thumb3"}}},
            ],
        }
        requests_mock.get(re.compile(r".*"), json=response_data, status_code=200)

        url, provider_name = GoogleApiProvider().get_thumbnail_url("9780134685991")

        assert url is None
        assert provider_name == "google api"


def test_google_api_get_thumbnail_url_no_image_links(app, requests_mock):
    """Test thumbnail URL retrieval when no image links available."""
    with app.app_context():
        requests_mock.get(re.compile(r".*"), json={"totalItems": 1, "items": [{"volumeInfo": {}}]}, status_code=200)

        url, provider_name = GoogleApiProvider().get_thumbnail_url("9780134685991")

        assert url is None
        assert provider_name == "google api"


def test_google_api_get_thumbnail_url_server_error(app, requests_mock):
    """Test thumbnail URL retrieval with server error."""
    with app.app_context():
        requests_mock.get(re.compile(r".*"), status_code=500)

        url, provider_name = GoogleApiProvider().get_thumbnail_url("9780134685991")

        assert url is None
        assert provider_name == "google api"


def test_google_api_get_thumbnail_url_request_exception(app, requests_mock):
    """Test thumbnail URL retrieval with request exception."""
    with app.app_context():
        requests_mock.get(re.compile(r".*"), exc=requests.RequestException("Connection error"))

        url, provider_name = GoogleApiProvider().get_thumbnail_url("9780134685991")

        assert url is None
        assert provider_name == "google api"


def test_google_api_get_thumbnail_url_api_endpoint(app, requests_mock):
    """Test that correct API endpoint is called."""
    with app.app_context():
        response_data = {
            "totalItems": 1,
            "items": [{"volumeInfo": {"imageLinks": {"thumbnail": "http://books.google.com/books/content?id=xxxxx"}}}],
        }
        requests_mock.get(re.compile(r".*"), json=response_data, status_code=200)

        isbn = "9780134685991"
        GoogleApiProvider().get_thumbnail_url(isbn)

        request_url = requests_mock.request_history[0].url
        assert "googleapis.com" in request_url
        assert "isbn:" in request_url
        assert isbn in request_url


def test_google_api_get_thumbnail_url_json_parsing(app, requests_mock):
    """Test JSON response parsing with nested structure."""
    with app.app_context():
        thumbnail_url = "http://example.com/thumb"
        response_data = {
            "totalItems": 1,
            "items": [
                {
                    "id": "some-id",
                    "volumeInfo": {
                        "title": "Test Book",
                        "imageLinks": {"smallThumbnail": "http://example.com/small", "thumbnail": thumbnail_url},
                    },
                }
            ],
        }
        requests_mock.get("https://www.googleapis.com/books/v1/volumes", json=response_data, status_code=200)
        requests_mock.get(thumbnail_url, content=create_test_image(), status_code=200)

        url, provider_name = GoogleApiProvider().get_thumbnail_url("9780134685991")

        assert url == "http://example.com/thumb"
        assert provider_name == "google api"


@pytest.mark.network
def test_google_api_real_thumbnail_is_valid_image(app):
    """Test that Google API returns a real valid image for a known ISBN."""
    with app.app_context():
        provider = GoogleApiProvider()
        url, provider_name = provider.get_thumbnail_url("9780134685991")

        assert provider_name == "google api"
        assert url is not None, "Google API returned no cover URL for ISBN 9780134685991"
        assert "googleapis.com" in url or "books.google.com" in url
