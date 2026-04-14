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

"""Tests for GoogleBooksProvider."""

import builtins
import json
import re

import pytest
import requests

from rero_invenio_thumbnails.contrib.google_books.api import GoogleBooksProvider

# Import test helper from conftest
try:
    from conftest import create_test_image
except ImportError:
    # Fallback: create_test_image is injected into builtins by conftest.pytest_configure
    create_test_image = getattr(builtins, "create_test_image", None)
    if create_test_image is None:
        raise ImportError("create_test_image not found; ensure conftest.py pytest_configure has run")


def test_google_books_get_thumbnail_url_success(app, requests_mock):
    """Test successful thumbnail URL retrieval."""
    thumbnail_url = "https://books.google.com/books/about/book"
    response_data = {"9780134685991": {"thumbnail_url": thumbnail_url}}
    response_text = f"book({json.dumps(response_data)})"
    requests_mock.get("https://books.google.com/books", text=response_text, status_code=200)
    requests_mock.get(thumbnail_url, content=create_test_image(), status_code=200)

    url, provider_name = GoogleBooksProvider().get_thumbnail_url("9780134685991")

    assert url is not None
    assert provider_name == "google books"
    assert "books.google.com" in url


def test_google_books_get_thumbnail_url_not_found(app, requests_mock):
    """Test thumbnail URL retrieval when book not found."""
    response_text = f"book({json.dumps({})})"
    requests_mock.get(re.compile(r".*"), text=response_text, status_code=200)

    url, provider_name = GoogleBooksProvider().get_thumbnail_url("9780134685991")

    assert url is None
    assert provider_name == "google books"


def test_google_books_get_thumbnail_url_no_preview(app, requests_mock):
    """Test thumbnail URL retrieval when no preview available."""
    response_data = {"9780134685991": {"title": "Test Book"}}
    response_text = f"book({json.dumps(response_data)})"
    requests_mock.get(re.compile(r".*"), text=response_text, status_code=200)

    url, provider_name = GoogleBooksProvider().get_thumbnail_url("9780134685991")

    assert url is None
    assert provider_name == "google books"


def test_google_books_get_thumbnail_url_server_error(app, requests_mock):
    """Test thumbnail URL retrieval with server error."""
    requests_mock.get(re.compile(r".*"), status_code=500)

    url, provider_name = GoogleBooksProvider().get_thumbnail_url("9780134685991")

    assert url is None
    assert provider_name == "google books"


def test_google_books_get_thumbnail_url_jsonp_parsing(app, requests_mock):
    """Test JSONP response parsing."""
    thumbnail_url = "https://books.google.com/books/about/test"
    response_data = {
        "9780134685991": {
            "thumbnail_url": thumbnail_url,
            "info_url": "https://books.google.com/books?id=test",
        }
    }
    response_text = f"book({json.dumps(response_data)})"
    requests_mock.get("https://books.google.com/books", text=response_text, status_code=200)
    requests_mock.get(thumbnail_url, content=create_test_image(), status_code=200)

    url, provider_name = GoogleBooksProvider().get_thumbnail_url("9780134685991")

    assert url == "https://books.google.com/books/about/test"
    assert provider_name == "google books"


def test_google_books_get_thumbnail_url_api_endpoint(app, requests_mock):
    """Test that correct API endpoint is called."""
    response_text = f"book({json.dumps({})})"
    requests_mock.get(re.compile(r".*"), text=response_text, status_code=200)

    isbn = "9780134685991"
    GoogleBooksProvider().get_thumbnail_url(isbn)

    assert len(requests_mock.request_history) > 0
    request_url = requests_mock.request_history[0].url
    assert "books.google.com" in request_url
    assert "jscmd=viewapi" in request_url
    assert "callback=book" in request_url
    assert isbn in request_url


def test_google_books_get_thumbnail_url_request_exception(app, requests_mock):
    """Test thumbnail URL retrieval with request exception."""
    requests_mock.get(re.compile(r".*"), exc=requests.RequestException("Connection error"))

    url, provider_name = GoogleBooksProvider().get_thumbnail_url("9780134685991")

    assert url is None
    assert provider_name == "google books"


def test_google_books_get_thumbnail_url_json_decode_error(app, requests_mock):
    """Test thumbnail URL retrieval with malformed JSON."""
    requests_mock.get(re.compile(r".*"), text="book(invalid json)", status_code=200)

    url, provider_name = GoogleBooksProvider().get_thumbnail_url("9780134685991")

    assert url is None
    assert provider_name == "google books"


def test_google_books_get_thumbnail_url_multiple_isbns(app, requests_mock):
    """Test thumbnail URL retrieval with multiple ISBN responses."""
    url1 = "https://books.google.com/books/about/book1"
    url2 = "https://books.google.com/books/about/book2"
    response_data = {
        "9780134685991": {"thumbnail_url": url1},
        "9780596007124": {"thumbnail_url": url2},
    }
    response_text = f"book({json.dumps(response_data)})"
    requests_mock.get("https://books.google.com/books", text=response_text, status_code=200)
    requests_mock.get(url1, content=create_test_image(), status_code=200)
    requests_mock.get(url2, content=create_test_image(), status_code=200)

    url, provider_name = GoogleBooksProvider().get_thumbnail_url("9780134685991")

    assert url == "https://books.google.com/books/about/book1"
    assert provider_name == "google books"


def test_google_books_get_thumbnail_url_unexpected_format(app, requests_mock):
    """Test thumbnail URL retrieval with unexpected JSONP format (no parentheses)."""
    requests_mock.get(re.compile(r".*"), text="invalid response without parentheses", status_code=200)

    url, provider_name = GoogleBooksProvider().get_thumbnail_url("9780134685991")

    assert url is None
    assert provider_name == "google books"


def test_google_books_get_thumbnail_url_generic_exception(app, requests_mock):
    """Test thumbnail URL retrieval with generic exception."""
    requests_mock.get(re.compile(r".*"), exc=RuntimeError("Unexpected error"))

    url, provider_name = GoogleBooksProvider().get_thumbnail_url("9780134685991")

    assert url is None
    assert provider_name == "google books"


@pytest.mark.external
def test_google_books_real_thumbnail_url_returned(app):
    """Test that Google Books returns a thumbnail URL for a known ISBN."""
    provider = GoogleBooksProvider()
    url, provider_name = provider.get_thumbnail_url("9780134685991")

    assert provider_name == "google books"
    assert url is not None, "Google Books returned no cover URL for ISBN 9780134685991"
    assert "books.google.com" in url
