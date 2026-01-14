"""Tests to improve code coverage for edge cases and error handling."""

import os
import tempfile
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from rero_invenio_thumbnails.modules.files.api import FilesProvider
from rero_invenio_thumbnails.modules.utils import fetch_with_retries, validate_image_content


class TestUtilsCoverage:
    """Test coverage for utils.py edge cases."""

    def test_validate_image_content_empty_content(self):
        """Test validate_image_content with empty content."""
        assert validate_image_content(b"", "test_provider", "1234567890") is False
        assert validate_image_content(None, "test_provider", "1234567890") is False

    def test_validate_image_content_invalid_image_data(self):
        """Test validate_image_content with invalid image data."""
        assert validate_image_content(b"not an image", "test_provider", "1234567890") is False

    def test_validate_image_content_small_dimensions(self):
        """Test validate_image_content with small dimensions."""
        # Create a 5x5 image (below minimum of 10x10)
        img = Image.new("RGB", (5, 5), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        content = img_bytes.getvalue()

        assert validate_image_content(content, "test_provider", "1234567890", min_dimension=10) is False

    def test_validate_image_content_valid_image(self):
        """Test validate_image_content with valid image."""
        img = Image.new("RGB", (100, 100), color="blue")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        content = img_bytes.getvalue()

        assert validate_image_content(content, "test_provider", "1234567890") is True

    def test_validate_image_content_outside_app_context(self):
        """Test validate_image_content outside Flask app context."""
        # This tests the exception handling when current_app is not available
        img = Image.new("RGB", (5, 5), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        content = img_bytes.getvalue()

        # Should still return False, but handle the logging exception gracefully
        assert validate_image_content(content, "test_provider", "1234567890") is False

    def test_fetch_with_retries_disabled_in_tests(self, app):
        """Test that retries are disabled during tests."""
        with app.app_context(), patch("requests.get") as mock_get:
            # Retries should be disabled in pytest environment
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            fetch_with_retries("http://example.com/test")

            # Should call directly without retry wrapper
            mock_get.assert_called_once()

    def test_fetch_with_retries_with_config(self, app):
        """Test fetch_with_retries respects Flask config."""
        with app.app_context(), patch("requests.get") as mock_get:
            app.config["RERO_INVENIO_THUMBNAILS_RETRY_ENABLED"] = False

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            fetch_with_retries("http://example.com/test")

            mock_get.assert_called_once()


class TestFilesProviderCoverage:
    """Test coverage for FilesProvider edge cases."""

    def test_get_thumbnail_path_exception_handling(self, app):
        """Test exception handling in get_thumbnail_path."""
        with app.app_context():
            provider = FilesProvider()

            # Configure with invalid directory to trigger exception path
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = None

            result = provider.get_thumbnail_path("9780134685991")
            assert result is None

    def test_get_thumbnail_url_with_rero_ils_url(self, app):
        """Test get_thumbnail_url with RERO_ILS_URL configured."""
        with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_isbn = "9780134685991"
            test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
            with open(test_file, "wb") as file:
                file.write(b"test image")

            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
            app.config["RERO_ILS_URL"] = "https://example.com"

            # Create provider after config is set
            provider = FilesProvider()

            url, provider_name = provider.get_thumbnail_url(test_isbn)
            assert url == "https://example.com/thumbnails/9780134685991"
            assert provider_name == "files"

    def test_get_thumbnail_url_exception_handling(self, app):
        """Test exception handling in get_thumbnail_url."""
        with app.app_context():
            provider = FilesProvider()

            # Configure with None to trigger exception
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = None

            result = provider.get_thumbnail_url("9780134685991")
            assert result == (None, "files")


class TestApiCoverage:
    """Test coverage for api.py edge cases."""

    def test_get_thumbnail_url_invalid_provider(self, app):
        """Test get_thumbnail_url with invalid provider name raises KeyError."""
        from rero_invenio_thumbnails.api import get_thumbnail_url

        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["nonexistent_provider"]

            # Should raise KeyError for invalid provider
            with pytest.raises(KeyError):
                get_thumbnail_url("9780134685991")
