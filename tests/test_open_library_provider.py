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

import builtins
import re

import pytest
import requests

from rero_invenio_thumbnails.contrib.open_library.api import OpenLibraryProvider

# Import test helper from conftest
try:
    from conftest import create_test_image
except ImportError:
    # Fallback: create_test_image is injected into builtins by conftest.pytest_configure
    create_test_image = getattr(builtins, "create_test_image", None)
    if create_test_image is None:
        raise ImportError("create_test_image not found; ensure conftest.py pytest_configure has run")


def test_open_library_get_thumbnail_url_success(app, requests_mock):
    """Test successful thumbnail URL retrieval."""
    with app.app_context():
        requests_mock.get(
            re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=create_test_image()
        )

        url, provider_name = OpenLibraryProvider().get_thumbnail_url("9780134685991")

        assert url is not None
        assert provider_name == "open library"
        assert "covers.openlibrary.org" in url
        assert "9780134685991" in url
        assert "-L.jpg" in url
        assert "default=false" in url


def test_open_library_get_thumbnail_url_not_found(app, requests_mock):
    """Test thumbnail URL retrieval when book not found (404)."""
    with app.app_context():
        requests_mock.get(re.compile(r".*"), status_code=404)

        url, provider_name = OpenLibraryProvider().get_thumbnail_url("9780134685991")

        assert url is None
        assert provider_name == "open library"


def test_open_library_get_thumbnail_url_server_error(app, requests_mock):
    """Test thumbnail URL retrieval with server error."""
    with app.app_context():
        requests_mock.get(re.compile(r".*"), status_code=500)

        url, provider_name = OpenLibraryProvider().get_thumbnail_url("9780134685991")

        assert url is None
        assert provider_name == "open library"


def test_open_library_get_thumbnail_url_format(app, requests_mock):
    """Test thumbnail URL format."""
    with app.app_context():
        requests_mock.get(
            re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=create_test_image()
        )

        isbn = "9780134685991"
        url, provider_name = OpenLibraryProvider().get_thumbnail_url(isbn)

        assert url == f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
        assert provider_name == "open library"


def test_open_library_get_thumbnail_url_isbn10(app, requests_mock):
    """Test thumbnail URL with ISBN-10."""
    with app.app_context():
        requests_mock.get(
            re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=create_test_image()
        )

        isbn = "0134685997"
        url, provider_name = OpenLibraryProvider().get_thumbnail_url(isbn)

        assert url is not None
        assert provider_name == "open library"
        assert isbn in url


def test_open_library_get_thumbnail_url_api_endpoint(app, requests_mock):
    """Test that correct API endpoint is called."""
    with app.app_context():
        requests_mock.get(
            re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=create_test_image()
        )

        isbn = "9780134685991"
        OpenLibraryProvider().get_thumbnail_url(isbn)

        assert len(requests_mock.request_history) > 0
        request_url = requests_mock.request_history[0].url
        assert "covers.openlibrary.org" in request_url
        assert "/b/isbn/" in request_url
        assert "-L.jpg" in request_url
        assert isbn in request_url


def test_open_library_get_thumbnail_url_request_exception(app, requests_mock):
    """Test thumbnail URL retrieval with request exception."""
    with app.app_context():
        requests_mock.get(re.compile(r".*"), exc=requests.RequestException("Connection error"))

        url, provider_name = OpenLibraryProvider().get_thumbnail_url("9780134685991")

        assert url is None
        assert provider_name == "open library"


def test_open_library_get_thumbnail_url_multiple_calls(app, requests_mock):
    """Test multiple consecutive calls."""
    with app.app_context():
        requests_mock.get(
            re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=create_test_image()
        )

        provider = OpenLibraryProvider()
        isbns = ["9780134685991", "9780596007124", "9781491954936"]
        results = [provider.get_thumbnail_url(isbn) for isbn in isbns]
        urls = [r[0] for r in results]
        provider_names = [r[1] for r in results]

        assert all(url is not None for url in urls)
        assert all(pn == "open library" for pn in provider_names)
        assert len(set(urls)) == 3
        for url, isbn in zip(urls, isbns):
            assert isbn in url


def test_open_library_get_thumbnail_url_default_parameter(app, requests_mock):
    """Test that default=false parameter is included."""
    with app.app_context():
        requests_mock.get(
            re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=create_test_image()
        )

        url, provider_name = OpenLibraryProvider().get_thumbnail_url("9780134685991")

        assert "default=false" in url
        assert provider_name == "open library"


@pytest.mark.parametrize(
    "status_code,expect_url",
    [
        (200, True),
        (201, False),
        (204, False),
        (400, False),
        (401, False),
        (403, False),
        (404, False),
        (500, False),
        (502, False),
        (503, False),
    ],
)
def test_open_library_get_thumbnail_url_different_status_codes(app, requests_mock, status_code, expect_url):
    """Test handling of different HTTP status codes."""
    with app.app_context():
        headers = {"Content-Type": "image/jpeg"} if status_code == 200 else {}
        content = create_test_image() if status_code == 200 else b""
        requests_mock.get(re.compile(r".*"), status_code=status_code, headers=headers, content=content)

        url, provider_name = OpenLibraryProvider().get_thumbnail_url("9780134685991")

        if expect_url:
            assert url is not None
        else:
            assert url is None
        assert provider_name == "open library"
