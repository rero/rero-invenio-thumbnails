# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module tests."""

import contextlib
import json
import os
import re
import tempfile
import time
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from rero_invenio_thumbnails import REROInvenioThumbnails, __version__
from rero_invenio_thumbnails.api import PROVIDERS, get_thumbnail_url
from rero_invenio_thumbnails.contrib.files.api import FilesProvider

try:
    from invenio_cache import current_cache
except Exception:
    current_cache = None


def _safe_cache_delete(isbn):
    """Safely delete cache entry for an ISBN without raising exceptions."""
    if current_cache is None:
        return
    with contextlib.suppress(Exception):
        cache_key = f"rero_thumbnails_{isbn}"
        current_cache.delete(cache_key)


@pytest.fixture
def client(app):
    """Create a test client with blueprint registered."""
    return app.test_client()


def test_version():
    """Test version import."""
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = REROInvenioThumbnails()
    assert "rero-invenio-thumbnails" not in app.extensions
    ext.init_app(app)
    assert "rero-invenio-thumbnails" in app.extensions


def test_get_thumbnail_url_with_files_provider(app):
    """Test get_thumbnail_url using Files provider."""
    with patch("rero_invenio_thumbnails.api.PROVIDERS") as mock_providers:
        _safe_cache_delete("9780134685991")
        app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

        mock_instance = MagicMock()
        mock_instance.get_thumbnail_url.return_value = ("https://example.com/thumbnails9780134685991", "files")
        mock_provider_class = MagicMock(return_value=mock_instance)
        mock_providers.__getitem__.return_value = mock_provider_class

        url, provider_name = get_thumbnail_url("9780134685991")

        assert url is not None
        assert "9780134685991" in url
        assert provider_name == "files"
        mock_providers.__getitem__.assert_called_with("files")
        mock_provider_class.assert_called_once()


def test_get_thumbnail_url_multiple_providers_first_success(app):
    """Test get_thumbnail_url with multiple providers - first succeeds."""
    with patch("rero_invenio_thumbnails.api.PROVIDERS") as mock_providers:
        _safe_cache_delete("9780134685991")
        app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files", "open library"]

        mock_files_instance = MagicMock()
        mock_files_instance.get_thumbnail_url.return_value = ("https://example.com/thumb", "files")
        mock_files_class = MagicMock(return_value=mock_files_instance)

        mock_openlibrary_instance = MagicMock()
        mock_openlibrary_class = MagicMock(return_value=mock_openlibrary_instance)

        def get_provider(key):
            if key == "files":
                return mock_files_class
            if key == "open library":
                return mock_openlibrary_class
            return MagicMock()

        mock_providers.__getitem__.side_effect = get_provider

        url, provider_name = get_thumbnail_url("9780134685991")

        assert url == "https://example.com/thumb"
        assert provider_name == "files"
        mock_files_class.assert_called_once()
        mock_openlibrary_class.assert_not_called()


def test_get_thumbnail_url_provider_returns_none(app):
    """Test get_thumbnail_url when provider returns None."""
    with patch("rero_invenio_thumbnails.api.PROVIDERS") as mock_providers:
        _safe_cache_delete("9780134685991")
        app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

        mock_instance = MagicMock()
        mock_instance.get_thumbnail_url.return_value = (None, "files")
        mock_provider_class = MagicMock(return_value=mock_instance)
        mock_providers.__getitem__.return_value = mock_provider_class

        url, provider_name = get_thumbnail_url("9780134685991")

        assert url is None
        assert provider_name is None


def test_get_thumbnail_url_no_providers_configured(app):
    """Test get_thumbnail_url with no providers configured."""
    _safe_cache_delete("9780134685991")
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = []

    assert get_thumbnail_url("9780134685991") == (None, None)


def test_get_thumbnail_url_default_config(app):
    """Test get_thumbnail_url with default configuration."""
    # Explicitly set empty providers to ensure deterministic behavior
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = []
    _safe_cache_delete("9780134685991")

    assert get_thumbnail_url("9780134685991") == (None, None)


def test_get_thumbnail_url_with_cached_none_result(app):
    """Test get_thumbnail_url when cached None result exists."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]
    app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/nonexistent"

    result1 = get_thumbnail_url("9999999999999")
    assert result1 == (None, None)

    result2 = get_thumbnail_url("9999999999999")
    assert result2 == (None, None)


def test_get_thumbnail_url_with_cached_none_and_uncached_call(app):
    """Test get_thumbnail_url with cached=False when None is cached."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]
    app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/nonexistent"

    result1 = get_thumbnail_url("8888888888888", cached=True)
    assert result1 == (None, None)

    result2 = get_thumbnail_url("8888888888888", cached=False)
    assert result2 == (None, None)


def test_get_thumbnail_url_with_pipe_in_url(app):
    """Test that URLs containing pipe characters are cached correctly."""
    mock_provider = MagicMock()
    test_url = "https://example.com/image.jpg?param=value%7Cother|literal"
    mock_provider.get_thumbnail_url.return_value = (test_url, "test provider")

    original_providers = PROVIDERS.copy()
    PROVIDERS["test"] = lambda: mock_provider
    try:
        app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["test"]
        _safe_cache_delete("1234567890123")

        url1, provider1 = get_thumbnail_url("1234567890123")
        assert url1 == test_url
        assert provider1 == "test provider"

        url2, provider2 = get_thumbnail_url("1234567890123")
        assert url2 == test_url
        assert provider2 == "test provider"

        assert mock_provider.get_thumbnail_url.call_count == 1
    finally:
        PROVIDERS.clear()
        PROVIDERS.update(original_providers)


def test_endpoint_blueprint_registration(app):
    """Test that blueprint is properly registered."""
    assert "api_thumbnails" in app.blueprints

    rules = [rule for rule in app.url_map.iter_rules() if "thumbnails" in rule.rule]
    assert len(rules) > 0
    assert any("/thumbnails-url/<isbn>" in rule.rule for rule in rules)


def test_endpoint_get_thumbnail_url_success(app, client):
    """Test successful thumbnail URL retrieval via /thumbnails-url endpoint."""
    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get_url:
        mock_get_url.return_value = ("https://example.com/thumbnail.jpg", "open library")

        response = client.get("/thumbnails-url/9780134685991")

        assert response.status_code == 200
        data = response.get_json()
        assert data["url"] == "https://example.com/thumbnail.jpg"
        assert data["isbn"] == "9780134685991"


def test_endpoint_get_thumbnail_url_not_found(app, client):
    """Test thumbnail URL not found via /thumbnails-url endpoint."""
    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get_url:
        mock_get_url.return_value = (None, "open library")

        response = client.get("/thumbnails-url/9999999999999")

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Thumbnail not found"
        assert data["isbn"] == "9999999999999"


def test_endpoint_get_thumbnail_url_with_cached_parameter(app, client):
    """Test thumbnail URL endpoint with cached parameter."""
    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get_url:
        mock_get_url.return_value = ("https://example.com/thumbnail.jpg", "files")

        response = client.get("/thumbnails-url/9780134685991?cached=false")

        assert response.status_code == 200
        mock_get_url.assert_called_once_with("9780134685991", cached=False)


def test_endpoint_get_thumbnail_url_exception_handling(app, client):
    """Test thumbnail URL endpoint exception handling."""
    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get_url:
        mock_get_url.side_effect = Exception("Unexpected error")

        response = client.get("/thumbnails-url/9780134685991")

        assert response.status_code == 500
        data = response.get_json()
        assert data["error"] == "Server error"
        assert data["isbn"] == "9780134685991"


def test_extension_initialization_with_blueprint(app):
    """Test extension initialization registers blueprint."""
    assert "rero-invenio-thumbnails" in app.extensions
    assert "api_thumbnails" in app.blueprints


def test_extension_validates_provider_configuration(caplog):
    """Test that extension logs error for non-existent providers in configuration."""
    app = Flask(__name__)
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = [
        "files",  # Valid provider
        "nonexistent_provider",  # Invalid provider
        "another_invalid",  # Another invalid provider
    ]

    # Initialize extension
    ext = REROInvenioThumbnails()
    ext.init_app(app)

    # Check that errors were logged for invalid providers
    assert any(
        "nonexistent_provider" in record.message and "does not exist in the provider registry" in record.message
        for record in caplog.records
    )
    assert any(
        "another_invalid" in record.message and "does not exist in the provider registry" in record.message
        for record in caplog.records
    )
    # Verify that the error level was used
    error_records = [record for record in caplog.records if record.levelname == "ERROR"]
    assert len(error_records) >= 2


def test_end_to_end_thumbnail_serving(app):
    """Test end-to-end thumbnail URL retrieval through blueprint."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]
    client = app.test_client()

    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get_url:
        mock_get_url.return_value = ("https://example.com/thumbnail.jpg", "open library")

        response = client.get("/thumbnails-url/9780134685991")

        assert response.status_code == 200
        data = response.get_json()
        assert data["url"] == "https://example.com/thumbnail.jpg"


def test_files_provider_fallback_localhost(app):
    """Test FilesProvider fallback to localhost when SERVER_NAME not set."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        test_isbn = "9780134685991"
        test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
        with open(test_file, "wb") as f:
            f.write(b"test")

        url, provider_name = get_thumbnail_url(test_isbn)
        assert url == "http://localhost/thumbnails/9780134685991"
        assert provider_name == "files"


def test_open_library_non_image_content_type(app, requests_mock):
    """Test OpenLibraryProvider rejects non-image content types."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]
    requests_mock.get(re.compile(r".*"), status_code=200, headers={"Content-Type": "text/html"}, text="")
    _safe_cache_delete("9780134685991")

    assert get_thumbnail_url("9780134685991") == (None, None)


def test_open_library_request_exception(app, requests_mock):
    """Test OpenLibraryProvider handles request exceptions."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]
    requests_mock.get(re.compile(r".*"), exc=Exception("Connection error"))
    _safe_cache_delete("9780134685991")

    assert get_thumbnail_url("9780134685991") == (None, None)


def test_files_provider_missing_thumbnail(app):
    """Test FilesProvider when thumbnail file doesn't exist."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

        assert get_thumbnail_url("9999999999999") == (None, None)


def test_endpoint_server_error_on_file_access(app, client):
    """Test endpoint error handling when FilesProvider throws exception."""
    _safe_cache_delete("9780134685991")
    app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/invalid/nonexistent/path"
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

    response = client.get("/thumbnails-url/9780134685991")

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Thumbnail not found"


def test_google_api_provider_http_error(app, requests_mock):
    """Test GoogleApiProvider handles HTTP errors."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["google api"]
    requests_mock.get(re.compile(r".*"), exc=Exception("HTTP Error"))
    _safe_cache_delete("9780134685991")

    assert get_thumbnail_url("9780134685991") == (None, None)


def test_google_books_provider_empty_response(app, requests_mock):
    """Test GoogleBooksProvider handles empty JSON response."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["google books"]
    requests_mock.get(re.compile(r".*"), status_code=200, text="")
    _safe_cache_delete("9780134685991")

    assert get_thumbnail_url("9780134685991") == (None, None)


def test_files_provider_exception(app):
    """Test FilesProvider handles exceptions in get_thumbnail_url."""
    provider = FilesProvider()
    app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/invalid/path"

    url, provider_name = provider.get_thumbnail_url("9780134685991")
    assert url is None
    assert provider_name == "files"


def test_cache_integration_with_none_result(app):
    """Test that None results are cached to avoid repeated queries."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = []
    _safe_cache_delete("9780134685991")

    url1 = get_thumbnail_url("9780134685991")
    assert url1 == (None, None)

    if current_cache is not None:
        cache_key = "rero_thumbnails_9780134685991"
        cached_value = current_cache.get(cache_key)
        assert cached_value is not None, "Expected value to be cached"
        data = json.loads(cached_value)
        assert data == {"url": None, "provider": None}


def test_google_books_provider_malformed_jsonp(app, requests_mock):
    """Test GoogleBooksProvider handles malformed JSONP response."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["google books"]
    _safe_cache_delete("9780134685991")
    requests_mock.get(re.compile(r".*"), status_code=200, text="notjsoncallback({invalid json})")

    assert get_thumbnail_url("9780134685991") == (None, None)


def test_open_library_provider_404_status(app, requests_mock):
    """Test Open Library provider returns None for 404 status."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]
    # Mock OpenLibrary HTTP request to return 404
    requests_mock.get(re.compile(r".*openlibrary\.org.*"), status_code=404)
    _safe_cache_delete("9780134685991")

    assert get_thumbnail_url("9780134685991") == (None, None)


def test_http_cache_headers_on_url_response(app, client):
    """Test that URL responses include cache control headers."""
    app.config["RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE"] = 86400
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get:
        mock_get.return_value = ("https://example.com/image.jpg", "open library")

        response = client.get("/thumbnails-url/9780134685991")
        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert "max-age=86400" in response.headers["Cache-Control"]


def test_serve_thumbnail_success(app, client):
    """Test serving a thumbnail image file successfully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        test_isbn = "9780134685991"
        test_image_path = os.path.join(temp_dir, f"{test_isbn}.jpg")
        with open(test_image_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        response = client.get(f"/thumbnails/{test_isbn}")
        assert response.status_code == 200
        assert response.mimetype == "image/jpeg"
        assert "Cache-Control" in response.headers


def test_serve_thumbnail_png_format(app, client):
    """Test serving a PNG thumbnail."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        test_isbn = "9780134685992"
        test_image_path = os.path.join(temp_dir, f"{test_isbn}.png")
        with open(test_image_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")

        response = client.get(f"/thumbnails/{test_isbn}")
        assert response.status_code == 200
        assert response.mimetype == "image/png"


def test_serve_thumbnail_not_found(app, client):
    """Test 404 response when thumbnail file doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        test_isbn = "9999999999999"

        response = client.get(f"/thumbnails/{test_isbn}")
        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Thumbnail not found"
        assert data["isbn"] == test_isbn


def test_serve_thumbnail_no_directory(app, client):
    """Test 404 response when files directory doesn't exist."""
    app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/nonexistent/directory"
    test_isbn = "9780134685991"

    response = client.get(f"/thumbnails/{test_isbn}")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Thumbnail not found"


def test_serve_thumbnail_cache_headers(app, client):
    """Test cache headers on image responses."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE"] = 3600
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        test_isbn = "9780134685991"
        test_image_path = os.path.join(temp_dir, f"{test_isbn}.jpg")
        with open(test_image_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        response = client.get(f"/thumbnails/{test_isbn}")
        assert response.status_code == 200
        assert "Cache-Control" in response.headers
        assert "max-age=3600" in response.headers["Cache-Control"]


def test_serve_thumbnail_etag_support(app, client):
    """Test ETag generation and validation for client-side caching."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        test_isbn = "9780134685991"
        test_image_path = os.path.join(temp_dir, f"{test_isbn}.jpg")
        with open(test_image_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        response = client.get(f"/thumbnails/{test_isbn}")
        assert response.status_code == 200
        assert "ETag" in response.headers
        assert "Last-Modified" in response.headers
        etag = response.headers["ETag"]

        response = client.get(f"/thumbnails/{test_isbn}", headers={"If-None-Match": etag})
        assert response.status_code == 304
        assert response.headers["ETag"] == etag


def test_serve_thumbnail_if_modified_since(app, client):
    """Test If-Modified-Since header for conditional requests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        test_isbn = "9780134685991"
        test_image_path = os.path.join(temp_dir, f"{test_isbn}.jpg")
        with open(test_image_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        response = client.get(f"/thumbnails/{test_isbn}")
        assert response.status_code == 200
        last_modified = response.headers["Last-Modified"]

        response = client.get(f"/thumbnails/{test_isbn}", headers={"If-Modified-Since": last_modified})
        assert response.status_code == 304


def test_serve_thumbnail_etag_different_after_modification(app, client):
    """Test that ETag changes when file is modified."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        test_isbn = "9780134685991"
        test_image_path = os.path.join(temp_dir, f"{test_isbn}.jpg")

        with open(test_image_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        response = client.get(f"/thumbnails/{test_isbn}")
        assert response.status_code == 200
        etag1 = response.headers["ETag"]

        # Use 1.1s sleep to account for filesystems with 1-second timestamp granularity
        time.sleep(1.1)
        with open(test_image_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00")

        response = client.get(f"/thumbnails/{test_isbn}")
        assert response.status_code == 200
        etag2 = response.headers["ETag"]
        assert etag1 != etag2


def test_serve_thumbnail_invalid_if_modified_since(app, client):
    """Test handling of invalid If-Modified-Since header."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        test_isbn = "9780134685991"
        test_image_path = os.path.join(temp_dir, f"{test_isbn}.jpg")
        with open(test_image_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        response = client.get(f"/thumbnails/{test_isbn}", headers={"If-Modified-Since": "invalid-date"})
        assert response.status_code == 200
        assert "ETag" in response.headers
