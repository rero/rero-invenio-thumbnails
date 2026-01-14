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


def _safe_cache_delete_image(isbn, width=None, height=None):
    """Safely delete image cache entry for an ISBN without raising exceptions."""
    if current_cache is None:
        return
    with contextlib.suppress(Exception):
        import hashlib

        cache_key = f"{isbn}_{width or 0}x{height or 0}" if width or height else isbn
        key_hash = hashlib.md5(cache_key.encode()).hexdigest()
        cache_key_full = f"rero_thumbnail_img_{key_hash}"
        current_cache.delete(cache_key_full)


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

    def test_get_thumbnail_url_with_amazon_provider(self, app):
        """Test get_thumbnail_url using Amazon provider."""
        with app.app_context(), patch("rero_invenio_thumbnails.api.PROVIDERS") as mock_providers:
            # Clear cache before test
            _safe_cache_delete("9780134685991")

            # Setup configuration
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["amazon"]

            mock_instance = MagicMock()
            mock_instance.get_thumbnail_url.return_value = (
                "https://images-na.ssl-images-amazon.com/images/P/0134685997.08._SCLZZZZZZZ_.jpg"
            )
            mock_provider_class = MagicMock(return_value=mock_instance)
            mock_providers.__getitem__.return_value = mock_provider_class

            # Test
            url = get_thumbnail_url("9780134685991")

            # Assertions
            assert url is not None
            assert "amazon" in url
            mock_providers.__getitem__.assert_called_with("amazon")
            mock_provider_class.assert_called_once()
            mock_instance.get_thumbnail_url.assert_called_once_with("9780134685991")

    def test_get_thumbnail_url_with_files_provider(self, app):
        """Test get_thumbnail_url using Files provider."""
        with app.app_context(), patch("rero_invenio_thumbnails.api.PROVIDERS") as mock_providers:
            # Clear cache before test
            _safe_cache_delete("9780134685991")

            # Setup configuration
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            mock_instance = MagicMock()
            mock_instance.get_thumbnail_url.return_value = "https://example.com/thumbnails9780134685991"
            mock_provider_class = MagicMock(return_value=mock_instance)
            mock_providers.__getitem__.return_value = mock_provider_class

            # Test
            url = get_thumbnail_url("9780134685991")

            # Assertions
            assert url is not None
            assert "9780134685991" in url
            mock_providers.__getitem__.assert_called_with("files")
            mock_provider_class.assert_called_once()

    def test_get_thumbnail_url_multiple_providers_first_success(self, app):
        """Test get_thumbnail_url with multiple providers - first succeeds."""
        with app.app_context(), patch("rero_invenio_thumbnails.api.PROVIDERS") as mock_providers:
            # Clear cache before test
            _safe_cache_delete("9780134685991")

            # Setup configuration
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files", "amazon", "open library"]

            # Mock first provider to succeed
            mock_files_instance = MagicMock()
            mock_files_instance.get_thumbnail_url.return_value = "https://example.com/thumb"
            mock_files_class = MagicMock(return_value=mock_files_instance)

            # Mock second provider to track if called
            mock_amazon_instance = MagicMock()
            mock_amazon_class = MagicMock(return_value=mock_amazon_instance)

            # Configure mock to return different provider based on key
            def get_provider(key):
                if key == "files":
                    return mock_files_class
                if key == "amazon":
                    return mock_amazon_class
                return MagicMock()

            mock_providers.__getitem__.side_effect = get_provider

            # Test
            url = get_thumbnail_url("9780134685991")

            # Assertions - should return first provider's result
            assert url == "https://example.com/thumb"
            mock_files_class.assert_called_once()
            # Amazon provider should not be called
            mock_amazon_class.assert_not_called()

    def test_get_thumbnail_url_provider_returns_none(self, app):
        """Test get_thumbnail_url when provider returns None."""
        with app.app_context(), patch("rero_invenio_thumbnails.api.PROVIDERS") as mock_providers:
            # Clear cache before test
            _safe_cache_delete("9780134685991")

            # Setup configuration
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["amazon"]

            # Mock the provider to return None
            mock_instance = MagicMock()
            mock_instance.get_thumbnail_url.return_value = None
            mock_provider_class = MagicMock(return_value=mock_instance)
            mock_providers.__getitem__.return_value = mock_provider_class

            # Test
            url = get_thumbnail_url("9780134685991")

            # Assertions
            assert url is None

    def test_get_thumbnail_url_no_providers_configured(self, app):
        """Test get_thumbnail_url with no providers configured."""
        with app.app_context():
            # Clear cache before test
            _safe_cache_delete("9780134685991")

            # Setup configuration with empty provider list
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = []

            # Test
            url = get_thumbnail_url("9780134685991")

            # Assertions
            assert url is None

    def test_get_thumbnail_url_default_config(self, app):
        """Test get_thumbnail_url with default configuration."""
        with app.app_context():
            # Clear cache before test
            _safe_cache_delete("9780134685991")

            # Don't set any providers config, use default
            # Test
            url = get_thumbnail_url("9780134685991")

            # Assertions - should return None with empty default
            assert url is None

    def test_get_thumbnail_url_with_cached_none_result(self, app):
        """Test get_thumbnail_url when cached None result exists."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/nonexistent"

            # First call will cache None
            url1 = get_thumbnail_url("9999999999999")
            assert url1 is None

            # Second call should return cached None
            url2 = get_thumbnail_url("9999999999999")
            assert url2 is None

    def test_get_thumbnail_url_with_cached_none_and_uncached_call(self, app):
        """Test get_thumbnail_url with cached=False when None is cached."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/nonexistent"

            # First call caches None
            url1 = get_thumbnail_url("8888888888888", cached=True)
            assert url1 is None

            # Call with cached=False should bypass cache
            url2 = get_thumbnail_url("8888888888888", cached=False)
            assert url2 is None


class TestBlueprintEndpoint:
    """Test HTTP endpoint serving thumbnails from blueprint."""

    @pytest.fixture
    def client(self, app):
        """Create a test client with blueprint registered."""
        return app.test_client()

    def test_endpoint_get_thumbnail_success(self, app, client):
        """Test successful thumbnail retrieval via HTTP endpoint."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            # Clear cache before test
            test_isbn = "9780134685991"
            _safe_cache_delete_image(test_isbn)

            # Create a test thumbnail file
            test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
            with open(test_file, "wb") as f:
                f.write(b"fake image data")

            # Configure app
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            # Test
            response = client.get(f"/thumbnails/{test_isbn}")

            # Assertions
            assert response.status_code == 200
            assert response.content_type == "image/jpeg"
            assert response.data == b"fake image data"

    def test_endpoint_get_thumbnail_not_found(self, app, client):
        """Test thumbnail retrieval when file not found."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            # Clear cache before test
            _safe_cache_delete_image("nonexistent-isbn")

            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Test
            response = client.get("/thumbnails/nonexistent-isbn")

            # Assertions
            assert response.status_code == 404
            assert "text/plain" in response.content_type
            assert "nonexistent-isbn" in response.get_data(as_text=True)

    def test_endpoint_get_thumbnail_server_error(self, app, client):
        """Test thumbnail retrieval falls back to other providers when files provider fails."""
        with app.app_context():
            # Clear cache
            _safe_cache_delete_image("9780134685991")

            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/nonexistent/path"
            # Set providers to only files and ensure it falls back correctly
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            # Test - should return 404 since only provider is files and it has invalid path
            response = client.get("/thumbnails/9780134685991")

            # Assertions
            assert response.status_code == 404
            assert "text/plain" in response.content_type

    def test_endpoint_get_thumbnail_with_different_extensions(self, app, client):
        """Test thumbnail retrieval with different file extensions."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            # Test each supported extension in a separate directory with different ISBN
            extensions_and_isbns = [(".jpg", "9780134685991"), (".jpeg", "9780134685992"), (".png", "9780134685993")]
            for ext, test_isbn in extensions_and_isbns:
                with tempfile.TemporaryDirectory() as temp_dir:
                    app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

                    # Create test file
                    test_file = os.path.join(temp_dir, f"{test_isbn}{ext}")
                    with open(test_file, "wb") as f:
                        f.write(f"image data {ext}".encode())

                    # Test
                    response = client.get(f"/thumbnails/{test_isbn}")

                    # Assertions
                    assert response.status_code == 200
                    assert response.content_type == "image/jpeg"
                    assert response.data == f"image data {ext}".encode()

    def test_endpoint_get_thumbnail_different_isbns(self, app, client):
        """Test thumbnail retrieval with different ISBN formats."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            # Test with different ISBNs
            isbns = ["9780134685991", "9780596007124", "0134685997"]
            for isbn in isbns:
                # Create test file
                test_file = os.path.join(temp_dir, f"{isbn}.jpg")
                with open(test_file, "wb") as f:
                    f.write(f"image for {isbn}".encode())

                # Test
                response = client.get(f"/thumbnails/{isbn}")

                # Assertions
                assert response.status_code == 200
                assert response.content_type == "image/jpeg"
                assert response.data == f"image for {isbn}".encode()

    def test_endpoint_response_headers(self, app, client):
        """Test HTTP response headers."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_isbn = "9780134685991"
            test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
            with open(test_file, "wb") as f:
                f.write(b"fake image data")

            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            # Test
            response = client.get(f"/thumbnails/{test_isbn}")

            # Assertions
            assert response.status_code == 200
            assert response.content_type == "image/jpeg"
            assert response.data == b"fake image data"

    def test_endpoint_blueprint_registration(self, app):
        """Test that blueprint is properly registered."""
        # Check blueprint exists
        assert "api_thumbnails" in app.blueprints

        # Check the endpoint is registered
        rules = [rule for rule in app.url_map.iter_rules() if "thumbnails" in rule.rule]
        assert len(rules) > 0
        assert any("/thumbnails/<isbn>" in rule.rule for rule in rules)

    def test_endpoint_redis_caching(self, app, client):
        """Test that thumbnails are cached in Redis when resizing is involved."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            test_isbn = "9780134685991"
            _safe_cache_delete_image(test_isbn, width=100)

            # Create a test thumbnail file
            test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
            import io

            from PIL import Image

            img = Image.new("RGB", (400, 600), color="blue")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)
            test_content = img_bytes.getvalue()

            with open(test_file, "wb") as f:
                f.write(test_content)

            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            # First request with resizing - should fetch from provider and cache resized version
            response1 = client.get(f"/thumbnails/{test_isbn}?width=100")
            assert response1.status_code == 200
            data1 = response1.data

            # Delete the file to ensure second request comes from cache
            os.remove(test_file)

            # Second request - should come from Redis cache (file is gone but resized version is cached)
            response2 = client.get(f"/thumbnails/{test_isbn}?width=100")
            assert response2.status_code == 200
            assert response2.data == data1

    def test_endpoint_caching_with_dimensions(self, app, client):
        """Test that thumbnails with dimensions are cached separately."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            test_isbn = "9780134685991"
            _safe_cache_delete_image(test_isbn)
            _safe_cache_delete_image(test_isbn, width=200)
            _safe_cache_delete_image(test_isbn, height=150)

            # Create a test thumbnail file
            test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
            import io

            from PIL import Image

            img = Image.new("RGB", (400, 600), color="red")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            with open(test_file, "wb") as f:
                f.write(img_bytes.getvalue())

            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            # Request with width=200
            response1 = client.get(f"/thumbnails/{test_isbn}?width=200")
            assert response1.status_code == 200
            data1 = response1.data

            # Request with height=150 (should be different cache entry)
            response2 = client.get(f"/thumbnails/{test_isbn}?height=150")
            assert response2.status_code == 200
            data2 = response2.data

            # Different dimensions should produce different sized images
            assert len(data1) != len(data2)

            # Delete the file to ensure next request comes from cache
            os.remove(test_file)

            # Request same dimensions again - should use cache (file is gone)
            response3 = client.get(f"/thumbnails/{test_isbn}?width=200")
            assert response3.status_code == 200
            assert response3.data == data1

    def test_endpoint_cached_parameter_false(self, app, client, requests_mock):
        """Test that cached=false parameter disables caching."""
        import re

        with (
            app.app_context(),
            patch("rero_invenio_thumbnails.api.PROVIDERS") as mock_providers,
        ):
            test_isbn = "9780596007124"
            _safe_cache_delete_image(test_isbn)

            # Mock provider response with image data
            import io

            from PIL import Image

            img = Image.new("RGB", (50, 75), color="green")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)
            test_content = img_bytes.getvalue()

            # Mock the provider
            mock_provider_instance = MagicMock()
            mock_provider_instance.get_thumbnail_url.return_value = "http://example.com/image.jpg"
            # Ensure get_thumbnail_path is not present
            del mock_provider_instance.get_thumbnail_path
            mock_provider_class = MagicMock(return_value=mock_provider_instance)
            mock_providers.__getitem__.return_value = mock_provider_class

            # Mock HTTP requests
            requests_mock.get(
                re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=test_content
            )

            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            # First request with cached=false - should fetch from provider
            response1 = client.get(f"/thumbnails/{test_isbn}?cached=false")
            assert response1.status_code == 200
            assert response1.content_type == "image/jpeg"
            assert response1.data == test_content
            initial_call_count = len(requests_mock.request_history)

            # Second request with cached=false - should fetch again (not cached)
            response2 = client.get(f"/thumbnails/{test_isbn}?cached=false")
            assert response2.status_code == 200
            assert response2.content_type == "image/jpeg"
            assert response2.data == test_content
            # Should have incremented (fetched again, not from cache)
            assert len(requests_mock.request_history) == initial_call_count + 1

    def test_endpoint_get_thumbnail_exception_handling(self, app, client):
        """Test get_thumbnail endpoint exception handling."""
        with app.app_context(), patch("rero_invenio_thumbnails.views.get_thumbnail_api") as mock_get_thumb:
            # Mock the API to raise an exception
            mock_get_thumb.side_effect = Exception("Unexpected error")

            # Test - should return 500 error
            response = client.get("/thumbnails/9780134685991")

            # Assertions
            assert response.status_code == 500
            assert "text/plain" in response.content_type
            assert "9780134685991" in response.get_data(as_text=True)

    def test_endpoint_get_thumbnail_url_success(self, app, client):
        """Test successful thumbnail URL retrieval via /thumbnails-url endpoint."""
        with app.app_context(), patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get_url:
            # Mock the URL response
            mock_get_url.return_value = "https://example.com/thumbnail.jpg"

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
            # Mock the URL response as None
            mock_get_url.return_value = None

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
            mock_get_url.return_value = "https://example.com/thumbnail.jpg"

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


class TestGetThumbnailFunction:
    """Test get_thumbnail function from API."""

    def test_get_thumbnail_with_remote_url_and_resizing(self, app, requests_mock):
        """Test get_thumbnail fetching from URL with resizing."""
        import re

        from rero_invenio_thumbnails.api import get_thumbnail

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["amazon"]

            # Create a test image
            import io

            from PIL import Image

            img = Image.new("RGB", (100, 150), color="red")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            # Mock URL response
            requests_mock.get(
                re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=img_bytes.getvalue()
            )

            with patch("rero_invenio_thumbnails.api.get_thumbnail_url") as mock_get_url:
                mock_get_url.return_value = "http://example.com/image.jpg"

                # Test with resizing
                result = get_thumbnail("9780134685991", width=50)
                assert result is not None
                _img_data, provider = result
                assert provider in ("cache", "amazon", "unknown")

    def test_get_thumbnail_with_remote_url_no_resizing(self, app, requests_mock):
        """Test get_thumbnail fetching from URL without resizing."""
        import re

        from rero_invenio_thumbnails.api import get_thumbnail

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["amazon"]

            # Create a test image
            import io

            from PIL import Image

            img = Image.new("RGB", (100, 150), color="blue")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            # Mock URL response
            requests_mock.get(
                re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=img_bytes.getvalue()
            )

            with patch("rero_invenio_thumbnails.api.get_thumbnail_url") as mock_get_url:
                mock_get_url.return_value = "http://example.com/image.jpg"

                # Test without resizing
                result = get_thumbnail("9780134685991")
                assert result is not None
                _img_data, provider = result
                assert provider in ("cache", "amazon", "unknown")

    def test_get_thumbnail_with_local_file_and_resizing(self, app):
        """Test get_thumbnail with local file and resizing."""
        from rero_invenio_thumbnails.api import get_thumbnail

        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Create a test image file
            import io

            from PIL import Image

            test_isbn = "9780134685991"
            img = Image.new("RGB", (200, 300), color="green")
            test_file = f"{temp_dir}/{test_isbn}.jpg"
            img.save(test_file, format="JPEG")

            # Test with resizing
            result = get_thumbnail(test_isbn, width=100)
            assert result is not None
            img_data, provider = result
            assert provider == "files"

            # Verify the image was resized
            result_img = Image.open(io.BytesIO(img_data))
            assert result_img.width == 100

    def test_get_thumbnail_with_local_file_no_resizing(self, app):
        """Test get_thumbnail with local file without resizing."""
        from rero_invenio_thumbnails.api import get_thumbnail

        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Create a test image file
            from PIL import Image

            test_isbn = "9780134685992"
            img = Image.new("RGB", (200, 300), color="yellow")
            test_file = f"{temp_dir}/{test_isbn}.jpg"
            img.save(test_file, format="JPEG")

            # Test without resizing
            result = get_thumbnail(test_isbn)
            assert result is not None
            _img_data, provider = result
            assert provider == "files"

    def test_get_thumbnail_with_file_read_exception(self, app):
        """Test get_thumbnail when file reading fails."""
        from rero_invenio_thumbnails.api import get_thumbnail

        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Create a directory instead of a file to trigger read error
            test_isbn = "9780134685993"
            invalid_path = f"{temp_dir}/{test_isbn}.jpg"
            os.makedirs(invalid_path, exist_ok=True)

            # Should handle exception and return None, None
            result = get_thumbnail(test_isbn)
            assert result == (None, None)

    def test_get_thumbnail_with_fetch_exception(self, app, requests_mock):
        """Test get_thumbnail when URL fetch fails."""
        import re

        from rero_invenio_thumbnails.api import get_thumbnail

        with (
            app.app_context(),
            patch("rero_invenio_thumbnails.api.get_thumbnail_url") as mock_get_url,
        ):
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["amazon"]

            # Mock URL response to fail
            mock_get_url.return_value = "http://example.com/image.jpg"
            requests_mock.get(re.compile(r".*"), exc=Exception("Network error"))

            # Should handle exception
            result = get_thumbnail("9780134685994")
            assert result == (None, None)

    def test_get_thumbnail_local_file_exception_with_url_fallback(self, app, requests_mock):
        """Test get_thumbnail when local file fails but URL succeeds."""
        import re

        from rero_invenio_thumbnails.api import get_thumbnail

        with (
            app.app_context(),
            tempfile.TemporaryDirectory() as temp_dir,
            patch("rero_invenio_thumbnails.api.get_thumbnail_url") as mock_get_url,
        ):
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files", "amazon"]
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Create invalid file (directory instead of file)
            import io

            from PIL import Image

            test_isbn = "9780134685995"
            invalid_path = f"{temp_dir}/{test_isbn}.jpg"
            os.makedirs(invalid_path, exist_ok=True)

            # Mock URL fallback
            img = Image.new("RGB", (100, 100), color="orange")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            mock_get_url.return_value = "http://example.com/fallback.jpg"
            requests_mock.get(
                re.compile(r".*"), status_code=200, headers={"Content-Type": "image/jpeg"}, content=img_bytes.getvalue()
            )

            # Should handle file exception and use URL fallback
            result = get_thumbnail(test_isbn)
            assert result is not None
            _img_data, provider = result
            assert provider in ("cache", "amazon", "unknown")


class TestResizeImage:
    """Test _resize_image helper function."""

    def test_resize_image_with_zero_dimensions(self, app):
        """Test _resize_image with invalid zero dimensions."""
        from rero_invenio_thumbnails.api import _resize_image

        with app.app_context():
            # Create image with zero width (invalid)
            img = MagicMock()
            img.size = (0, 100)

            # Should return original image due to validation
            result = _resize_image(img, 50, 50)
            assert result == img

            # Test with zero height
            img.size = (100, 0)
            result = _resize_image(img, 50, 50)
            assert result == img

    def test_resize_image_with_height_only(self, app):
        """Test _resize_image with height only."""
        from rero_invenio_thumbnails.api import _resize_image

        with app.app_context():
            # Create a real test image
            from PIL import Image

            img = Image.new("RGB", (200, 100), color="purple")

            # Resize with height only
            result = _resize_image(img, None, 50)

            assert result.height == 50
            # Width should be proportional: 200 * (50 / 100) = 100
            assert result.width == 100


class TestIntegration:
    """Integration tests for the complete thumbnail system."""

    def test_extension_initialization_with_blueprint(self, app):
        """Test extension initialization registers blueprint."""
        # Check extension is registered
        assert "rero-invenio-thumbnails" in app.extensions

        # Check blueprint is registered
        assert "api_thumbnails" in app.blueprints

    def test_end_to_end_thumbnail_serving(self, app):
        """Test end-to-end thumbnail serving through blueprint."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            # Setup
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]
            client = app.test_client()

            # Create test file
            test_isbn = "9780134685991"
            test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
            test_content = b"test image content"
            with open(test_file, "wb") as f:
                f.write(test_content)

            # Test
            response = client.get(f"/thumbnails/{test_isbn}")

            # Assertions
            assert response.status_code == 200
            assert response.content_type == "image/jpeg"
            assert response.data == test_content

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

                url = get_thumbnail_url(test_isbn)
                assert url == "http://localhost/api/thumbnails/9780134685991"

    def test_open_library_non_image_content_type(self, app, requests_mock):
        """Test OpenLibraryProvider rejects non-image content types."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            requests_mock.get(re.compile(r".*"), status_code=200, headers={"Content-Type": "text/html"}, text="")

            url = get_thumbnail_url("9780134685991")
            assert url is None

    def test_open_library_request_exception(self, app, requests_mock):
        """Test OpenLibraryProvider handles request exceptions."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            requests_mock.get(re.compile(r".*"), exc=Exception("Connection error"))

            url = get_thumbnail_url("9780134685991")
            assert url is None

    def test_files_provider_missing_thumbnail(self, app):
        """Test FilesProvider when thumbnail file doesn't exist."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            with tempfile.TemporaryDirectory() as temp_dir:
                app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

                url = get_thumbnail_url("9999999999999")
                assert url is None

    def test_endpoint_server_error_on_file_access(self, app, client):
        """Test endpoint error handling when FilesProvider throws exception."""
        with app.app_context():
            # Clear cache
            _safe_cache_delete_image("9780134685991")

            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/invalid/nonexistent/path"
            # Ensure only files provider is used so it will fail
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["files"]

            response = client.get("/thumbnails/9780134685991")

            assert response.status_code == 404
            assert "text/plain" in response.content_type

    def test_amazon_provider_json_parse_error(self, app, requests_mock):
        """Test AmazonProvider handles parsing errors gracefully."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["amazon"]

            requests_mock.get(re.compile(r".*"), exc=ValueError("Invalid HTML"))

            url = get_thumbnail_url("9780134685991")
            assert url is None

    def test_google_api_provider_http_error(self, app, requests_mock):
        """Test GoogleApiProvider handles HTTP errors."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["google api"]

            requests_mock.get(re.compile(r".*"), exc=Exception("HTTP Error"))

            url = get_thumbnail_url("9780134685991")
            assert url is None

    def test_google_books_provider_empty_response(self, app, requests_mock):
        """Test GoogleBooksProvider handles empty JSON response."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["google books"]

            requests_mock.get(re.compile(r".*"), status_code=200, text="")

            url = get_thumbnail_url("9780134685991")
            assert url is None

    def test_files_provider_exception(self, app):
        """Test FilesProvider handles exceptions in get_thumbnail_url."""
        with app.app_context():
            from rero_invenio_thumbnails.modules.files.api import FilesProvider

            provider = FilesProvider()
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/invalid/path"

            url = provider.get_thumbnail_url("9780134685991")
            assert url is None

    def test_cache_integration_with_none_result(self, app):
        """Test that None results are cached to avoid repeated queries."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = []
            _safe_cache_delete("9780134685991")

            # First call returns None
            url1 = get_thumbnail_url("9780134685991")
            assert url1 is None

            # Verify it's cached (by checking cache)
            if current_cache is not None:
                cache_key = "rero_thumbnails_9780134685991"
                cached_value = current_cache.get(cache_key)
                # Cache stores b'None' for None results
                assert cached_value == b"None"

    def test_amazon_provider_timeout(self, app, requests_mock):
        """Test AmazonProvider handles request timeout."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["amazon"]

            requests_mock.get(re.compile(r".*"), exc=Exception("Timeout"))

            url = get_thumbnail_url("9780134685991")
            assert url is None

    def test_google_books_provider_malformed_jsonp(self, app, requests_mock):
        """Test GoogleBooksProvider handles malformed JSONP."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["google books"]

            requests_mock.get(re.compile(r".*"), status_code=200, text="notjsoncallback({invalid json})")

            url = get_thumbnail_url("9780134685991")
            assert url is None

    def test_open_library_provider_404_status(self, app, requests_mock):
        """Test OpenLibraryProvider handles 404 status codes."""
        import re

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            requests_mock.get(re.compile(r".*"), status_code=404)

            url = get_thumbnail_url("9780134685991")
            assert url is None


class TestFilesystemCache:
    """Test filesystem cache backend."""

    def test_filesystem_cache_url_storage(self, app, requests_mock):
        """Test that filesystem cache stores and retrieves URL correctly."""
        import re
        import tempfile
        from pathlib import Path

        with app.app_context(), tempfile.TemporaryDirectory() as tmpdir:
            app.config["RERO_INVENIO_THUMBNAILS_CACHE_TYPE"] = "filesystem"
            app.config["RERO_INVENIO_THUMBNAILS_CACHE_DIR"] = tmpdir
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            requests_mock.get(
                re.compile(r".*"),
                status_code=200,
                headers={"Content-Type": "image/jpeg"},
                content=create_test_image(),
            )

            # First call - should fetch and cache
            url1 = get_thumbnail_url("9780134685991")
            assert url1 is not None

            # Check cache file exists
            cache_dir = Path(tmpdir)
            cache_files = list(cache_dir.glob("*.cache"))
            assert len(cache_files) > 0

            # Second call - should retrieve from cache
            url2 = get_thumbnail_url("9780134685991")
            assert url1 == url2

    def test_filesystem_cache_image_storage(self, app, client, requests_mock):
        """Test that filesystem cache stores image bytes correctly."""
        import re
        import tempfile

        with app.app_context(), tempfile.TemporaryDirectory() as tmpdir:
            app.config["RERO_INVENIO_THUMBNAILS_CACHE_TYPE"] = "filesystem"
            app.config["RERO_INVENIO_THUMBNAILS_CACHE_DIR"] = tmpdir
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            # Mock the provider and image response
            with patch("rero_invenio_thumbnails.api.get_thumbnail_url") as mock_get_url:
                mock_get_url.return_value = "https://example.com/image.jpg"

                # Create a simple test image
                from io import BytesIO

                from PIL import Image

                test_img = Image.new("RGB", (100, 100), color="red")
                img_bytes = BytesIO()
                test_img.save(img_bytes, format="JPEG")
                img_bytes.seek(0)

                requests_mock.get(
                    re.compile(r".*"),
                    status_code=200,
                    headers={"Content-Type": "image/jpeg"},
                    content=img_bytes.getvalue(),
                )

                # First request - should cache
                response1 = client.get("/thumbnails/9780134685991")
                assert response1.status_code == 200

                # Second request - should use cache
                response2 = client.get("/thumbnails/9780134685991")
                assert response2.status_code == 200
                assert response1.data == response2.data

    def test_filesystem_cache_expiration(self, app, requests_mock):
        """Test that filesystem cache respects expiration."""
        import re
        import tempfile
        import time

        with app.app_context(), tempfile.TemporaryDirectory() as tmpdir:
            app.config["RERO_INVENIO_THUMBNAILS_CACHE_TYPE"] = "filesystem"
            app.config["RERO_INVENIO_THUMBNAILS_CACHE_DIR"] = tmpdir
            app.config["RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE"] = 1  # 1 second
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            requests_mock.get(
                re.compile(r".*"),
                status_code=200,
                headers={"Content-Type": "image/jpeg"},
                content=create_test_image(),
            )

            # First call - cache
            url1 = get_thumbnail_url("9780134685991")
            assert url1 is not None

            # Wait for expiration
            time.sleep(1.1)

            # Second call - should re-fetch (cache expired)
            url2 = get_thumbnail_url("9780134685991")
            assert url2 is not None

            # Verify at least 2 calls were made (initial + after expiration)
            assert requests_mock.call_count >= 2


class TestHTTPCacheHeaders:
    """Test HTTP cache control headers."""

    def test_http_cache_headers_on_image_response(self, app, client):
        """Test that image responses include cache control headers."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE"] = 3600
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            with patch("rero_invenio_thumbnails.views.get_thumbnail_api") as mock_get:
                # Create a simple test image
                from io import BytesIO

                from PIL import Image

                test_img = Image.new("RGB", (100, 100), color="blue")
                img_bytes = BytesIO()
                test_img.save(img_bytes, format="JPEG")
                img_bytes.seek(0)

                mock_get.return_value = (img_bytes.getvalue(), "open library")

                response = client.get("/thumbnails/9780134685991")
                assert response.status_code == 200
                assert "Cache-Control" in response.headers
                assert "max-age=3600" in response.headers["Cache-Control"]
                assert "public" in response.headers["Cache-Control"]
                assert response.headers.get("Vary") == "Accept-Encoding"

    def test_http_cache_headers_on_url_response(self, app, client):
        """Test that URL responses include cache control headers."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE"] = 86400
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock_get:
                mock_get.return_value = "https://example.com/image.jpg"

                response = client.get("/thumbnails-url/9780134685991")
                assert response.status_code == 200
                assert "Cache-Control" in response.headers
                assert "max-age=86400" in response.headers["Cache-Control"]

    def test_http_cache_headers_disabled(self, app, client):
        """Test that cache headers can be disabled."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE"] = 0
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["open library"]

            with patch("rero_invenio_thumbnails.views.get_thumbnail_api") as mock_get:
                from io import BytesIO

                from PIL import Image

                test_img = Image.new("RGB", (100, 100), color="green")
                img_bytes = BytesIO()
                test_img.save(img_bytes, format="JPEG")
                mock_get.return_value = (img_bytes.getvalue(), "open library")

                response = client.get("/thumbnails/9780134685991")
                assert response.status_code == 200
                assert "Cache-Control" in response.headers
                assert "no-cache" in response.headers["Cache-Control"]
                assert "no-store" in response.headers["Cache-Control"]
