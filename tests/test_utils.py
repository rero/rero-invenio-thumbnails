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

"""Tests to improve code coverage for edge cases and error handling."""

import os
import tempfile
from io import BytesIO
from unittest.mock import MagicMock, patch

from invenio_cache import current_cache
from PIL import Image

from rero_invenio_thumbnails.api import get_thumbnail_url
from rero_invenio_thumbnails.contrib.files.api import FilesProvider
from rero_invenio_thumbnails.contrib.utils import clean_all_cache, handle_provider_errors, validate_image_content


def test_validate_image_content_empty_content(app):
    """Test validate_image_content with empty content."""
    assert validate_image_content(b"", "test_provider", "1234567890") is False
    assert validate_image_content(None, "test_provider", "1234567890") is False


def test_validate_image_content_invalid_image_data(app):
    """Test validate_image_content with invalid image data."""
    assert validate_image_content(b"not an image", "test_provider", "1234567890") is False


def test_validate_image_content_small_dimensions(app):
    """Test validate_image_content with small dimensions."""
    img = Image.new("RGB", (5, 5), color="red")
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    assert validate_image_content(img_bytes.getvalue(), "test_provider", "1234567890") is False


def test_validate_image_content_valid_image(app):
    """Test validate_image_content with valid image."""
    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    assert validate_image_content(img_bytes.getvalue(), "test_provider", "1234567890") is True


def test_files_get_thumbnail_path_exception_handling(app):
    """Test exception handling in get_thumbnail_path."""
    provider = FilesProvider()
    app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = None

    assert provider.get_thumbnail_path("9780134685991") is None


def test_files_get_thumbnail_url_with_rero_invenio_thumbnails_url(app):
    """Test get_thumbnail_url with RERO_INVENIO_THUMBNAILS_URL configured."""
    with tempfile.TemporaryDirectory() as temp_dir:
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
    provider = FilesProvider()
    app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = None

    assert provider.get_thumbnail_url("9780134685991") == (None, "files")


def test_get_thumbnail_url_invalid_provider(app):
    """Test get_thumbnail_url with invalid provider name returns None gracefully."""
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = ["nonexistent_provider"]

    url, provider = get_thumbnail_url("9780134685991")
    assert url is None
    assert provider is None


def test_handle_provider_errors_value_error(app):
    """Test handle_provider_errors catches ValueError and returns (None, provider_lower)."""

    class MockProvider:
        @handle_provider_errors("TestProvider")
        def get_thumbnail_url(self, isbn):
            raise ValueError("invalid isbn format")

    url, name = MockProvider().get_thumbnail_url("bad-isbn")
    assert url is None
    assert name == "testprovider"


def test_validate_image_content_memory_error(app):
    """Test validate_image_content handles MemoryError raised by PIL."""
    with patch("PIL.Image.open", side_effect=MemoryError("out of memory")):
        assert validate_image_content(b"some content", "test_provider", "1234567890") is False


def test_clean_all_cache_no_redis_client(app):
    """Test clean_all_cache returns 0 when the cache backend has no Redis client."""
    # SimpleCache has no _write_client or _client, so the function warns and returns 0.
    result = clean_all_cache()
    assert result == 0


def test_clean_all_cache_with_redis_client(app):
    """Test clean_all_cache deletes matching keys via the Redis client."""
    mock_client = MagicMock()
    mock_client.scan_iter.return_value = [b"rero_thumbnails_key1", b"rero_thumbnails_key2"]
    mock_client.delete.return_value = 2

    with patch.object(current_cache.cache, "_write_client", mock_client, create=True):
        result = clean_all_cache()

    assert result == 2
    mock_client.delete.assert_called_once_with(b"rero_thumbnails_key1", b"rero_thumbnails_key2")


def test_clean_all_cache_large_batch(app):
    """Test clean_all_cache flushes intermediate batches when > 1000 keys are found."""
    mock_client = MagicMock()
    keys = [f"rero_thumbnails_key{i}".encode() for i in range(1001)]
    mock_client.scan_iter.return_value = keys
    mock_client.delete.side_effect = [1000, 1]

    with patch.object(current_cache.cache, "_write_client", mock_client, create=True):
        result = clean_all_cache()

    assert result == 1001
    assert mock_client.delete.call_count == 2
