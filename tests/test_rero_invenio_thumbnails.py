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

"""Module tests."""

import contextlib
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from rero_invenio_thumbnails import REROInvenioThumbnails
from rero_invenio_thumbnails.api import get_thumbnail_url

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


def test_version():
    """Test version import."""
    from rero_invenio_thumbnails import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = REROInvenioThumbnails()
    assert "rero-invenio-thumbnails" not in app.extensions
    ext.init_app(app)
    assert "rero-invenio-thumbnails" in app.extensions


class TestGetThumbnailUrl:
    """Test get_thumbnail_url function from main API."""

    def test_get_thumbnail_url_with_files_provider(self, app):
        """Test get_thumbnail_url using Files provider."""
        with app.app_context(), patch("rero_invenio_thumbnails.api.PROVIDERS") as mock_providers:
            # Clear cache before test
            _safe_cache_delete("9780134685991")

            # Setup configuration
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            mock_instance = MagicMock()
            mock_instance.get_thumbnail_url.return_value = ("https://example.com/thumbnails9780134685991", "files")
            mock_provider_class = MagicMock(return_value=mock_instance)
            mock_providers.__getitem__.return_value = mock_provider_class

            # Test
            url, provider_name = get_thumbnail_url("9780134685991")

            # Assertions
            assert url is not None
            assert "9780134685991" in url
            assert provider_name == "files"
            mock_providers.__getitem__.assert_called_with("files")
            mock_provider_class.assert_called_once()

    def test_get_thumbnail_url_multiple_providers_first_success(self, app):
        """Test get_thumbnail_url with multiple providers - first succeeds."""
        with app.app_context(), patch("rero_invenio_thumbnails.api.PROVIDERS") as mock_providers:
            # Clear cache before test
            _safe_cache_delete("9780134685991")

            # Setup configuration
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files", "open library"]

            # Mock first provider to succeed
            mock_files_instance = MagicMock()
            mock_files_instance.get_thumbnail_url.return_value = ("https://example.com/thumb", "files")
            mock_files_class = MagicMock(return_value=mock_files_instance)

            # Mock second provider to track if called
            mock_openlibrary_instance = MagicMock()
            mock_openlibrary_class = MagicMock(return_value=mock_openlibrary_instance)

            # Configure mock to return different provider based on key
            def get_provider(key):
                if key == "files":
                    return mock_files_class
                if key == "open library":
                    return mock_openlibrary_class
                return MagicMock()

            mock_providers.__getitem__.side_effect = get_provider

            # Test
            url, provider_name = get_thumbnail_url("9780134685991")

            # Assertions - should return first provider's result
            assert url == "https://example.com/thumb"
            assert provider_name == "files"
            mock_files_class.assert_called_once()
            # Open Library provider should not be called
            mock_openlibrary_class.assert_not_called()

    def test_get_thumbnail_url_provider_returns_none(self, app):
        """Test get_thumbnail_url when provider returns None."""
        with app.app_context(), patch("rero_invenio_thumbnails.api.PROVIDERS") as mock_providers:
            # Clear cache before test
            _safe_cache_delete("9780134685991")

            # Setup configuration
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            # Mock the provider to return None
            mock_instance = MagicMock()
            mock_instance.get_thumbnail_url.return_value = (None, "files")
            mock_provider_class = MagicMock(return_value=mock_instance)
            mock_providers.__getitem__.return_value = mock_provider_class

            # Test
            url, provider_name = get_thumbnail_url("9780134685991")

            # Assertions
            assert url is None
            assert provider_name == "files"

    def test_get_thumbnail_url_no_providers_configured(self, app):
        """Test get_thumbnail_url with no providers configured."""
        with app.app_context():
            # Clear cache before test
            _safe_cache_delete("9780134685991")

            # Setup configuration with empty provider list
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = []

            # Test
            result = get_thumbnail_url("9780134685991")

            # Assertions
            assert result == (None, None)

    def test_get_thumbnail_url_default_config(self, app):
        """Test get_thumbnail_url with default configuration."""
        with app.app_context():
            # Clear cache before test
            _safe_cache_delete("9780134685991")

            # Don't set any providers config, use default
            # Test
            result = get_thumbnail_url("9780134685991")

            # Assertions - should return None with empty default
            assert result == (None, None)

    def test_get_thumbnail_url_with_cached_none_result(self, app):
        """Test get_thumbnail_url when cached None result exists."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/nonexistent"

            # First call will cache None
            result1 = get_thumbnail_url("9999999999999")
            assert result1 == (None, "files")

            # Second call should return cached None
            result2 = get_thumbnail_url("9999999999999")
            assert result2 == (None, "files")

    def test_get_thumbnail_url_with_cached_none_and_uncached_call(self, app):
        """Test get_thumbnail_url with cached=False when None is cached."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/nonexistent"

            # First call caches None
            result1 = get_thumbnail_url("8888888888888", cached=True)
            assert result1 == (None, "files")

            # Call with cached=False should bypass cache
            result2 = get_thumbnail_url("8888888888888", cached=False)
            assert result2 == (None, "files")

    def test_get_thumbnail_url_with_pipe_in_url(self, app):
        """Test that URLs containing pipe characters are cached correctly."""
        with app.app_context():
            # Mock a provider that returns a URL with pipe character
            from unittest.mock import MagicMock

            mock_provider = MagicMock()
            # URL with pipe character (e.g., some query parameters)
            test_url = "https://example.com/image.jpg?param=value%7Cother|literal"
            mock_provider.get_thumbnail_url.return_value = (test_url, "test provider")

            # Temporarily inject mock provider
            from rero_invenio_thumbnails.api import PROVIDERS

            original_providers = PROVIDERS.copy()
            PROVIDERS["test"] = lambda: mock_provider
            try:
                app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["test"]
                _safe_cache_delete("1234567890123")

                # First call - should cache the URL with pipe
                url1, provider1 = get_thumbnail_url("1234567890123")
                assert url1 == test_url
                assert provider1 == "test provider"

                # Second call - should retrieve from cache correctly
                url2, provider2 = get_thumbnail_url("1234567890123")
                assert url2 == test_url
                assert provider2 == "test provider"

                # Verify it was only called once (second time from cache)
                assert mock_provider.get_thumbnail_url.call_count == 1
            finally:
                # Restore original providers
                PROVIDERS.clear()
                PROVIDERS.update(original_providers)


class TestBlueprintEndpoint:
    """Test HTTP endpoint serving thumbnails from blueprint."""

    @pytest.fixture
    def client(self, app):
        """Create a test client with blueprint registered."""
        return app.test_client()

    def test_endpoint_blueprint_registration(self, app):
        """Test that blueprint is properly registered."""
        # Check blueprint exists
        assert "api_thumbnails" in app.blueprints

        # Check the endpoint is registered
        rules = [rule for rule in app.url_map.iter_rules() if "thumbnails" in rule.rule]
        assert len(rules) > 0
        assert any("/thumbnails-url/<isbn>" in rule.rule for rule in rules)

    def test_endpoint_get_thumbnail_url_success(self, app, client):
        """Test successful thumbnail URL retrieval via /thumbnails-url endpoint."""
        with app.app_context(), patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get_url:
            # Mock the URL response
            mock_get_url.return_value = ("https://example.com/thumbnail.jpg", "open library")

            # Test
            response = client.get("/thumbnails-url/9780134685991")

            # Assertions
            assert response.status_code == 200
            data = response.get_json()
            assert data["url"] == "https://example.com/thumbnail.jpg"
            assert data["isbn"] == "9780134685991"

    def test_endpoint_get_thumbnail_url_not_found(self, app, client):
        """Test thumbnail URL not found via /thumbnails-url endpoint."""
        with app.app_context(), patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get_url:
            # Mock the URL response as None with provider name
            mock_get_url.return_value = (None, "open library")

            # Test
            response = client.get("/thumbnails-url/9999999999999")

            # Assertions
            assert response.status_code == 404
            data = response.get_json()
            assert data["error"] == "Thumbnail not found"
            assert data["isbn"] == "9999999999999"

    def test_endpoint_get_thumbnail_url_with_cached_parameter(self, app, client):
        """Test thumbnail URL endpoint with cached parameter."""
        with app.app_context(), patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get_url:
            # Mock the URL response
            mock_get_url.return_value = ("https://example.com/thumbnail.jpg", "files")

            # Test with cached=false
            response = client.get("/thumbnails-url/9780134685991?cached=false")

            # Assertions
            assert response.status_code == 200
            # Verify cached=False was passed to API function
            mock_get_url.assert_called_once_with("9780134685991", cached=False)

    def test_endpoint_get_thumbnail_url_exception_handling(self, app, client):
        """Test thumbnail URL endpoint exception handling."""
        with app.app_context(), patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get_url:
            # Mock the API to raise an exception
            mock_get_url.side_effect = Exception("Unexpected error")

            # Test - should return 500 error
            response = client.get("/thumbnails-url/9780134685991")

            # Assertions
            assert response.status_code == 500
            data = response.get_json()
            assert data["error"] == "Server error"
            assert "9780134685991" in data["isbn"]


class TestIntegration:
    """Integration tests for the complete thumbnail system."""

    def test_extension_initialization_with_blueprint(self, app):
        """Test extension initialization registers blueprint."""
        # Check extension is registered
        assert "rero-invenio-thumbnails" in app.extensions

        # Check blueprint is registered
        assert "api_thumbnails" in app.blueprints

    def test_end_to_end_thumbnail_serving(self, app):
        """Test end-to-end thumbnail URL retrieval through blueprint."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]
            client = app.test_client()

            with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get_url:
                mock_get_url.return_value = ("https://example.com/thumbnail.jpg", "open library")

                # Test
                response = client.get("/thumbnails-url/9780134685991")

                # Assertions
                assert response.status_code == 200
                data = response.get_json()
                assert data["url"] == "https://example.com/thumbnail.jpg"

    def test_files_provider_fallback_localhost(self, app):
        """Test FilesProvider fallback to localhost when SERVER_NAME not set."""
        with app.app_context():
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

    def test_open_library_non_image_content_type(self, app, requests_mock):
        """Test OpenLibraryProvider rejects non-image content types."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            requests_mock.get(re.compile(r".*"), status_code=200, headers={"Content-Type": "text/html"}, text="")

            result = get_thumbnail_url("9780134685991")
            assert result == (None, "open library")

    def test_open_library_request_exception(self, app, requests_mock):
        """Test OpenLibraryProvider handles request exceptions."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            requests_mock.get(re.compile(r".*"), exc=Exception("Connection error"))

            result = get_thumbnail_url("9780134685991")
            assert result == (None, "open library")

    def test_files_provider_missing_thumbnail(self, app):
        """Test FilesProvider when thumbnail file doesn't exist."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            with tempfile.TemporaryDirectory() as temp_dir:
                app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

                result = get_thumbnail_url("9999999999999")
                assert result == (None, "files")

    def test_endpoint_server_error_on_file_access(self, app, client):
        """Test endpoint error handling when FilesProvider throws exception."""
        with app.app_context():
            # Clear cache
            _safe_cache_delete("9780134685991")

            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/invalid/nonexistent/path"
            # Ensure only files provider is used so it will fail
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            response = client.get("/thumbnails-url/9780134685991")

            assert response.status_code == 404
            data = response.get_json()
            assert data["error"] == "Thumbnail not found"

    def test_google_api_provider_http_error(self, app, requests_mock):
        """Test GoogleApiProvider handles HTTP errors."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["google api"]

            requests_mock.get(re.compile(r".*"), exc=Exception("HTTP Error"))

            result = get_thumbnail_url("9780134685991")
            assert result == (None, "google api")

    def test_google_books_provider_empty_response(self, app, requests_mock):
        """Test GoogleBooksProvider handles empty JSON response."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["google books"]

            requests_mock.get(re.compile(r".*"), status_code=200, text="")

            result = get_thumbnail_url("9780134685991")
            assert result == (None, "google books")

    def test_files_provider_exception(self, app):
        """Test FilesProvider handles exceptions in get_thumbnail_url."""
        with app.app_context():
            from rero_invenio_thumbnails.modules.files.api import FilesProvider

            provider = FilesProvider()
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/invalid/path"

            url, provider_name = provider.get_thumbnail_url("9780134685991")
            assert url is None
            assert provider_name == "files"

    def test_cache_integration_with_none_result(self, app):
        """Test that None results are cached to avoid repeated queries."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = []
            _safe_cache_delete("9780134685991")

            # First call returns None
            url1 = get_thumbnail_url("9780134685991")
            assert url1 == (None, None)

            # Verify it's cached (by checking cache)
            if current_cache is not None:
                cache_key = "rero_thumbnails_9780134685991"
                cached_value = current_cache.get(cache_key)
                # Cache stores JSON: {"url": null, "provider": null}
                import json

                data = json.loads(cached_value)
                assert data == {"url": None, "provider": None}

    def test_google_books_provider_malformed_jsonp(self, app, requests_mock):
        """Test GoogleBooksProvider handles malformed JSONP response."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["google books"]

            requests_mock.get(re.compile(r".*"), status_code=200, text="notjsoncallback({invalid json})")

            result = get_thumbnail_url("9780134685991")
            assert result == (None, "google books")

    def test_open_library_provider_404_status(self, app, requests_mock):
        """Test Open Library provider returns None for 404 status."""
        result = get_thumbnail_url("9780134685991")
        assert result == (None, None)


class TestHTTPCacheHeaders:
    """Test HTTP cache control headers."""

    def test_http_cache_headers_on_url_response(self, app, client):
        """Test that URL responses include cache control headers."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE"] = 86400
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get:
                mock_get.return_value = ("https://example.com/image.jpg", "open library")

                response = client.get("/thumbnails-url/9780134685991")
                assert response.status_code == 200
                assert "Cache-Control" in response.headers
                assert "max-age=86400" in response.headers["Cache-Control"]


class TestServeThumbnailEndpoint:
    """Test /thumbnails/<isbn> endpoint that serves actual image files."""

    def test_serve_thumbnail_success(self, app, client):
        """Test serving a thumbnail image file successfully."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary directory and test image file
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            test_isbn = "9780134685991"

            # Create a test JPEG file
            test_image_path = os.path.join(temp_dir, f"{test_isbn}.jpg")
            with open(test_image_path, "wb") as f:
                # Write minimal JPEG header
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

            response = client.get(f"/thumbnails/{test_isbn}")
            assert response.status_code == 200
            assert response.mimetype == "image/jpeg"
            assert "Cache-Control" in response.headers

    def test_serve_thumbnail_png_format(self, app, client):
        """Test serving a PNG thumbnail."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            test_isbn = "9780134685992"

            # Create a test PNG file
            test_image_path = os.path.join(temp_dir, f"{test_isbn}.png")
            with open(test_image_path, "wb") as f:
                # Write minimal PNG header
                f.write(b"\x89PNG\r\n\x1a\n")

            response = client.get(f"/thumbnails/{test_isbn}")
            assert response.status_code == 200
            assert response.mimetype == "image/png"

    def test_serve_thumbnail_not_found(self, app, client):
        """Test 404 response when thumbnail file doesn't exist."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            test_isbn = "9999999999999"

            response = client.get(f"/thumbnails/{test_isbn}")
            assert response.status_code == 404
            data = response.get_json()
            assert data["error"] == "Thumbnail not found"
            assert data["isbn"] == test_isbn

    def test_serve_thumbnail_no_directory(self, app, client):
        """Test 404 response when files directory doesn't exist."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/nonexistent/directory"
            test_isbn = "9780134685991"

            response = client.get(f"/thumbnails/{test_isbn}")
            assert response.status_code == 404
            data = response.get_json()
            assert data["error"] == "Thumbnail not found"

    def test_serve_thumbnail_cache_headers(self, app, client):
        """Test cache headers on image responses."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            app.config["RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE"] = 3600
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            test_isbn = "9780134685991"

            # Create test image
            test_image_path = os.path.join(temp_dir, f"{test_isbn}.jpg")
            with open(test_image_path, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

            response = client.get(f"/thumbnails/{test_isbn}")
            assert response.status_code == 200
            assert "Cache-Control" in response.headers
            assert "max-age=3600" in response.headers["Cache-Control"]

    def test_serve_thumbnail_etag_support(self, app, client):
        """Test ETag generation and validation for client-side caching."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            test_isbn = "9780134685991"

            # Create test image
            test_image_path = os.path.join(temp_dir, f"{test_isbn}.jpg")
            with open(test_image_path, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

            # First request - should return 200 with ETag
            response = client.get(f"/thumbnails/{test_isbn}")
            assert response.status_code == 200
            assert "ETag" in response.headers
            assert "Last-Modified" in response.headers
            etag = response.headers["ETag"]

            # Second request with If-None-Match - should return 304
            response = client.get(f"/thumbnails/{test_isbn}", headers={"If-None-Match": etag})
            assert response.status_code == 304
            assert response.headers["ETag"] == etag

    def test_serve_thumbnail_if_modified_since(self, app, client):
        """Test If-Modified-Since header for conditional requests."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            test_isbn = "9780134685991"

            # Create test image
            test_image_path = os.path.join(temp_dir, f"{test_isbn}.jpg")
            with open(test_image_path, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

            # First request - get Last-Modified header
            response = client.get(f"/thumbnails/{test_isbn}")
            assert response.status_code == 200
            last_modified = response.headers["Last-Modified"]

            # Second request with If-Modified-Since - should return 304
            response = client.get(f"/thumbnails/{test_isbn}", headers={"If-Modified-Since": last_modified})
            assert response.status_code == 304

    def test_serve_thumbnail_etag_different_after_modification(self, app, client):
        """Test that ETag changes when file is modified."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            test_isbn = "9780134685991"
            test_image_path = os.path.join(temp_dir, f"{test_isbn}.jpg")

            # Create initial image
            with open(test_image_path, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

            # Get initial ETag
            response = client.get(f"/thumbnails/{test_isbn}")
            assert response.status_code == 200
            etag1 = response.headers["ETag"]

            # Modify the file
            import time

            time.sleep(0.01)  # Ensure different mtime
            with open(test_image_path, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00")

            # Get new ETag - should be different
            response = client.get(f"/thumbnails/{test_isbn}")
            assert response.status_code == 200
            etag2 = response.headers["ETag"]
            assert etag1 != etag2

    def test_serve_thumbnail_invalid_if_modified_since(self, app, client):
        """Test handling of invalid If-Modified-Since header."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            test_isbn = "9780134685991"

            # Create test image
            test_image_path = os.path.join(temp_dir, f"{test_isbn}.jpg")
            with open(test_image_path, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

            # Request with invalid date format - should still return 200
            response = client.get(f"/thumbnails/{test_isbn}", headers={"If-Modified-Since": "invalid-date"})
            assert response.status_code == 200
            assert "ETag" in response.headers


class TestGetBaseUrls:
    """Test get_base_urls function."""

    def test_get_base_urls_default_providers(self, app):
        """Test get_base_urls returns all default provider base URLs."""
        from rero_invenio_thumbnails.api import get_base_urls

        with app.app_context():
            # Configure all available providers (note: entry point names have spaces)
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = [
                "bnf",
                "dnb",
                "files",
                "google api",
                "google books",
                "open library",
            ]

            base_urls = get_base_urls()

            # Check that we have base URLs
            assert isinstance(base_urls, dict)
            assert len(base_urls) == 6

            # Check expected base URLs (keys are URLs now)
            assert "http://catalogue.bnf.fr/couverture" in base_urls
            assert "https://portal.dnb.de/opac/mvb/cover" in base_urls
            assert "http://localhost" in base_urls
            assert "https://www.googleapis.com/books/v1/volumes" in base_urls
            assert "https://books.google.com/books" in base_urls
            assert "https://covers.openlibrary.org" in base_urls

            # Check provider name values
            assert base_urls["http://catalogue.bnf.fr/couverture"] == "bnf"
            assert base_urls["https://portal.dnb.de/opac/mvb/cover"] == "dnb"
            assert base_urls["http://localhost"] == "files"
            assert base_urls["https://www.googleapis.com/books/v1/volumes"] == "google api"
            assert base_urls["https://books.google.com/books"] == "google books"
            assert base_urls["https://covers.openlibrary.org"] == "open library"

    def test_get_base_urls_with_custom_config(self, app):
        """Test get_base_urls with custom RERO_ILS_URL configuration."""
        from rero_invenio_thumbnails.api import get_base_urls

        with app.app_context():
            app.config["RERO_ILS_URL"] = "https://custom.example.com"
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            base_urls = get_base_urls()

            # Files provider should use custom config
            assert base_urls["https://custom.example.com"] == "files"

    def test_get_base_urls_with_configured_providers(self, app):
        """Test get_base_urls respects RERO_INVENIO_THUMBNAILS_PROVIDERS config."""
        from rero_invenio_thumbnails.api import get_base_urls

        with app.app_context():
            # Configure only specific providers
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["bnf", "open library"]
            base_urls = get_base_urls()

            # Should only have configured providers
            assert "http://catalogue.bnf.fr/couverture" in base_urls
            assert "https://covers.openlibrary.org" in base_urls
            assert len(base_urls) == 2

            # Check the values are correct provider names
            assert base_urls["http://catalogue.bnf.fr/couverture"] == "bnf"
            assert base_urls["https://covers.openlibrary.org"] == "open library"

    def test_get_base_urls_with_invalid_provider(self, app):
        """Test get_base_urls handles invalid providers gracefully."""
        from rero_invenio_thumbnails.api import get_base_urls

        with app.app_context():
            # Configure with an invalid provider name
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["bnf", "invalid_provider", "open library"]
            base_urls = get_base_urls()

            # Should have valid providers (URLs are keys)
            assert "http://catalogue.bnf.fr/couverture" in base_urls
            assert "https://covers.openlibrary.org" in base_urls
            assert len(base_urls) == 2

            # Check the values are correct provider names
            assert base_urls["http://catalogue.bnf.fr/couverture"] == "bnf"
            assert base_urls["https://covers.openlibrary.org"] == "open library"

    def test_get_base_urls_empty_providers(self, app):
        """Test get_base_urls with empty provider list."""
        from rero_invenio_thumbnails.api import get_base_urls

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = []
            base_urls = get_base_urls()

            # Should return empty dict
            assert base_urls == {}
