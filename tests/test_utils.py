# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests to improve code coverage for edge cases and error handling."""

import os
import tempfile
from io import BytesIO
from unittest.mock import MagicMock, patch

from invenio_cache import current_cache
from PIL import Image

from rero_invenio_thumbnails.api import get_thumbnail_url
from rero_invenio_thumbnails.contrib.files.api import FilesProvider
from rero_invenio_thumbnails.contrib.utils import (
    clean_all_cache,
    fetch_and_validate_thumbnail,
    handle_provider_errors,
    validate_image_content,
)


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


# --- fetch_and_validate_thumbnail ---


def test_fetch_and_validate_thumbnail_success(app, requests_mock):
    """Test that a 200 response with a valid image returns True."""
    url = "https://example.com/cover.jpg"
    requests_mock.get(url, status_code=200, content=create_test_image())

    assert fetch_and_validate_thumbnail(url, "TestProvider", "9780000000000") is True


def test_fetch_and_validate_thumbnail_non_200_no_expected_codes(app, requests_mock):
    """Test that a non-200 status is logged and returns False when expected_status_codes is not set."""
    url = "https://example.com/cover.jpg"
    requests_mock.get(url, status_code=404)

    with patch("rero_invenio_thumbnails.contrib.utils.current_app") as mock_app:
        result = fetch_and_validate_thumbnail(url, "TestProvider", "9780000000000")

    assert result is False
    logged_messages = [call[0][0] for call in mock_app.logger.debug.call_args_list]
    assert any("HTTP 404" in msg for msg in logged_messages)


def test_fetch_and_validate_thumbnail_expected_status_silenced(app, requests_mock):
    """Test that a status code in expected_status_codes is NOT logged as an HTTP error."""
    url = "https://example.com/cover.jpg"
    requests_mock.get(url, status_code=500)

    with patch("rero_invenio_thumbnails.contrib.utils.current_app") as mock_app:
        result = fetch_and_validate_thumbnail(url, "BNF", "9780000000000", expected_status_codes={500})

    assert result is False
    # 500 is declared as expected — no debug HTTP-error log should be emitted
    logged_messages = [call[0][0] for call in mock_app.logger.debug.call_args_list]
    assert all("HTTP 500" not in msg for msg in logged_messages)


def test_fetch_and_validate_thumbnail_unexpected_status_logged(app, requests_mock):
    """Test that a status code NOT in expected_status_codes is still logged."""
    url = "https://example.com/cover.jpg"
    requests_mock.get(url, status_code=503)

    with patch("rero_invenio_thumbnails.contrib.utils.current_app") as mock_app:
        result = fetch_and_validate_thumbnail(url, "BNF", "9780000000000", expected_status_codes={500})

    assert result is False
    # 503 is NOT in expected_status_codes → debug log should fire
    logged_messages = [call[0][0] for call in mock_app.logger.debug.call_args_list]
    assert any("HTTP 503" in msg for msg in logged_messages)


def test_fetch_and_validate_thumbnail_request_exception(app, requests_mock):
    """Test that a connection error returns False without raising."""
    import requests as req

    url = "https://example.com/cover.jpg"
    requests_mock.get(url, exc=req.exceptions.ConnectionError("timeout"))

    assert fetch_and_validate_thumbnail(url, "TestProvider", "9780000000000") is False


def test_fetch_and_validate_thumbnail_invalid_image(app, requests_mock):
    """Test that a 200 response with non-image content returns False."""
    url = "https://example.com/cover.jpg"
    requests_mock.get(url, status_code=200, content=b"<html>not an image</html>")

    assert fetch_and_validate_thumbnail(url, "TestProvider", "9780000000000") is False
