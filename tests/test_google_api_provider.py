# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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


def test_google_api_removes_edge_curl(app, requests_mock):
    """Test that edge=curl is stripped from the returned thumbnail URL."""
    raw_url = "http://books.google.com/books/content?id=xxxxx&edge=curl&source=gbs_api"
    clean_url = "http://books.google.com/books/content?id=xxxxx&source=gbs_api"
    response_data = {
        "totalItems": 1,
        "items": [{"volumeInfo": {"imageLinks": {"thumbnail": raw_url}}}],
    }
    requests_mock.get("https://www.googleapis.com/books/v1/volumes", json=response_data, status_code=200)
    requests_mock.get(clean_url, content=create_test_image(), status_code=200)

    url, _provider_name = GoogleApiProvider().get_thumbnail_url("9780134685991")

    assert url == clean_url
    assert "edge" not in url


def test_google_api_get_thumbnail_url_not_found(app, requests_mock):
    """Test thumbnail URL retrieval when book not found."""
    requests_mock.get(re.compile(r".*"), json={"totalItems": 0, "items": []}, status_code=200)

    assert GoogleApiProvider().get_thumbnail_url("9780134685991") == (None, "google api")


def test_google_api_get_thumbnail_url_multiple_results(app, requests_mock):
    """Test thumbnail URL retrieval when multiple results found (rejected)."""
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
    requests_mock.get(re.compile(r".*"), json={"totalItems": 1, "items": [{"volumeInfo": {}}]}, status_code=200)

    url, provider_name = GoogleApiProvider().get_thumbnail_url("9780134685991")

    assert url is None
    assert provider_name == "google api"


def test_google_api_get_thumbnail_url_server_error(app, requests_mock):
    """Test thumbnail URL retrieval with server error."""
    requests_mock.get(re.compile(r".*"), status_code=500)

    url, provider_name = GoogleApiProvider().get_thumbnail_url("9780134685991")

    assert url is None
    assert provider_name == "google api"


def test_google_api_get_thumbnail_url_request_exception(app, requests_mock):
    """Test thumbnail URL retrieval with request exception."""
    requests_mock.get(re.compile(r".*"), exc=requests.RequestException("Connection error"))

    url, provider_name = GoogleApiProvider().get_thumbnail_url("9780134685991")

    assert url is None
    assert provider_name == "google api"


def test_google_api_get_thumbnail_url_api_endpoint(app, requests_mock):
    """Test that correct API endpoint is called."""
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


@pytest.mark.external
def test_google_api_returns_thumbnail_url_for_known_isbn(app):
    """Test that Google API returns a thumbnail URL for a known ISBN."""
    provider = GoogleApiProvider()
    url, provider_name = provider.get_thumbnail_url("9780134685991")

    assert provider_name == "google api"
    assert url is not None, "Google API returned no cover URL for ISBN 9780134685991"
    assert "googleapis.com" in url or "books.google.com" in url
