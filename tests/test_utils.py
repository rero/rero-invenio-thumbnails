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

"""Tests to improve code coverage for edge cases and error handling."""

import os
import tempfile
from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image

from rero_invenio_thumbnails.api import get_thumbnail_url
from rero_invenio_thumbnails.contrib.files.api import FilesProvider
from rero_invenio_thumbnails.contrib.utils import fetch_with_retries, validate_image_content


def test_validate_image_content_empty_content():
    """Test validate_image_content with empty content."""
    assert validate_image_content(b"", "test_provider", "1234567890") is False
    assert validate_image_content(None, "test_provider", "1234567890") is False


def test_validate_image_content_invalid_image_data():
    """Test validate_image_content with invalid image data."""
    assert validate_image_content(b"not an image", "test_provider", "1234567890") is False


def test_validate_image_content_small_dimensions():
    """Test validate_image_content with small dimensions."""
    img = Image.new("RGB", (5, 5), color="red")
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    assert validate_image_content(img_bytes.getvalue(), "test_provider", "1234567890", min_dimension=10) is False


def test_validate_image_content_valid_image():
    """Test validate_image_content with valid image."""
    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    assert validate_image_content(img_bytes.getvalue(), "test_provider", "1234567890") is True


def test_validate_image_content_outside_app_context():
    """Test validate_image_content behavior when called outside Flask app context.

    Verifies that the function handles missing Flask app context gracefully
    by using default configuration values and continuing image validation.
    """
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    assert validate_image_content(img_bytes.getvalue(), "test_provider", "1234567890") is True


def test_fetch_with_retries_disabled_in_tests(app):
    """Test that retries are disabled during tests."""
    with app.app_context(), patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        fetch_with_retries("http://example.com/test")

        mock_get.assert_called_once()


def test_fetch_with_retries_with_config(app):
    """Test fetch_with_retries respects Flask config."""
    with app.app_context(), patch("requests.get") as mock_get:
        app.config["RERO_INVENIO_THUMBNAILS_RETRY_ENABLED"] = False

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        fetch_with_retries("http://example.com/test")

        mock_get.assert_called_once()


def test_files_get_thumbnail_path_exception_handling(app):
    """Test exception handling in get_thumbnail_path."""
    with app.app_context():
        provider = FilesProvider()
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = None

        assert provider.get_thumbnail_path("9780134685991") is None


def test_files_get_thumbnail_url_with_rero_invenio_thumbnails_url(app):
    """Test get_thumbnail_url with RERO_INVENIO_THUMBNAILS_URL configured."""
    with app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
        test_isbn = "9780134685991"
        test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
        with open(test_file, "wb") as f:
            f.write(b"test image")

        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        app.config["RERO_INVENIO_THUMBNAILS_URL"] = "https://example.com"

        url, provider_name = FilesProvider().get_thumbnail_url(test_isbn)
        assert url == "https://example.com/thumbnails/9780134685991"
        assert provider_name == "files"


def test_files_get_thumbnail_url_exception_handling(app):
    """Test exception handling in get_thumbnail_url."""
    with app.app_context():
        provider = FilesProvider()
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = None

        assert provider.get_thumbnail_url("9780134685991") == (None, "files")


def test_get_thumbnail_url_invalid_provider(app):
    """Test get_thumbnail_url with invalid provider name returns None gracefully."""
    with app.app_context():
        app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["nonexistent_provider"]

        url, provider = get_thumbnail_url("9780134685991")
        assert url is None
        assert provider == "nonexistent_provider"
