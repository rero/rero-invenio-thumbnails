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
    fetch_url,
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


def test_fetch_and_validate_thumbnail_expected_status_silenced(app, requests_mock, mock_logger):
    """Test that a status code in expected_status_codes stays at debug level."""
    url = "https://example.com/cover.jpg"
    requests_mock.get(url, status_code=500)

    result = fetch_and_validate_thumbnail(url, "bnf", "9780000000000", expected_status_codes={500})

    assert result is False
    # 500 is declared as expected — reported as "no cover", never as an error
    logged_messages = [call[0][0] for call in mock_logger.debug.call_args_list]
    assert any("HTTP 500" in msg and "no cover available" in msg for msg in logged_messages)
    mock_logger.error.assert_not_called()


def test_fetch_and_validate_thumbnail_not_found_silenced(app, requests_mock, mock_logger):
    """Test that a 404 is treated as "no cover" even without expected_status_codes."""
    url = "https://example.com/cover.jpg"
    requests_mock.get(url, status_code=404)

    result = fetch_and_validate_thumbnail(url, "TestProvider", "9780000000000")

    assert result is False
    logged_messages = [call[0][0] for call in mock_logger.debug.call_args_list]
    assert any("HTTP 404" in msg and "no cover available" in msg for msg in logged_messages)
    mock_logger.error.assert_not_called()


def test_fetch_and_validate_thumbnail_unexpected_status_reported_as_error(app, requests_mock, mock_logger):
    """Test that a status code NOT in expected_status_codes is reported at error level."""
    url = "https://example.com/cover.jpg"
    requests_mock.get(url, status_code=503)

    result = fetch_and_validate_thumbnail(url, "bnf", "9780000000000", expected_status_codes={500})

    assert result is False
    # 503 is NOT expected → it signals a problem with the provider itself
    logged_messages = [call[0][0] for call in mock_logger.error.call_args_list]
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


def test_fetch_url_success(app, requests_mock):
    """Test that a 200 response is returned to the caller."""
    url = "https://example.com/api?isbn=9780000000000"
    requests_mock.get(url, status_code=200, json={"ok": True})

    response = fetch_url(url, "TestProvider", "9780000000000")

    assert response is not None
    assert response.json() == {"ok": True}


def test_fetch_url_not_found_returns_none(app, requests_mock, mock_logger):
    """Test that a 404 yields None without being reported as an error."""
    url = "https://example.com/api?isbn=9780000000000"
    requests_mock.get(url, status_code=404)

    assert fetch_url(url, "TestProvider", "9780000000000") is None

    mock_logger.error.assert_not_called()


def test_fetch_url_request_exception_reported_at_warning(app, requests_mock, mock_logger):
    """Test that an unreachable provider is visible at the default log level.

    A provider that cannot be reached at all is an outage: at debug level it leaves
    no trace, while a single unexpected status from the same host is an error.
    """
    import requests as req

    url = "https://example.com/api?isbn=9780000000000"
    requests_mock.get(url, exc=req.exceptions.ConnectTimeout("read timed out"))

    assert fetch_url(url, "TestProvider", "9780000000000") is None

    reported = [call[0][0] for call in mock_logger.warning.call_args_list]
    assert any("Request error" in msg for msg in reported)
    mock_logger.error.assert_not_called()


def test_fetch_url_value_error_from_transport_returns_none(app, requests_mock, mock_logger):
    """Test that a non-RequestException from the transport does not escape.

    Letting it through would have handle_provider_errors report the provider
    failure as an invalid ISBN.
    """
    url = "https://example.com/api?isbn=9780000000000"
    requests_mock.get(url, exc=ValueError("invalid URL"))

    assert fetch_url(url, "TestProvider", "9780000000000") is None

    reported = [call[0][0] for call in mock_logger.warning.call_args_list]
    assert any("Request error" in msg for msg in reported)


def test_fetch_url_unexpected_status_reported_as_error(app, requests_mock, mock_logger):
    """Test that a status meaning neither "cover" nor "no cover" is reported."""
    url = "https://example.com/api?isbn=9780000000000"
    requests_mock.get(url, status_code=403)

    assert fetch_url(url, "bnf", "9780000000000") is None

    reported = [call[0][0] for call in mock_logger.error.call_args_list]
    assert any("HTTP 403" in msg for msg in reported)
    # The report carries the configured provider name, so it can be grepped
    # against RERO_INVENIO_THUMBNAILS_PROVIDERS
    assert any("from bnf " in msg for msg in reported)


def test_fetch_url_uses_configured_timeout(app, requests_mock):
    """Test that the default timeout comes from the application config."""
    url = "https://example.com/api?isbn=9780000000000"
    requests_mock.get(url, status_code=200, json={"ok": True})
    app.config["RERO_INVENIO_THUMBNAILS_HTTP_TIMEOUT"] = (5, 25)

    with patch("rero_invenio_thumbnails.contrib.utils.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        fetch_url(url, "TestProvider", "9780000000000")

    assert mock_get.call_args.kwargs["timeout"] == (5, 25)


def test_handle_provider_errors_reports_json_failure_as_request_error(app, mock_logger):
    """Test that a failed body parse is not reported as a malformed ISBN.

    requests.exceptions.JSONDecodeError inherits from both RequestException and
    ValueError, so the clause order in the decorator decides which one wins.
    """
    import requests as req

    class _Provider:
        @handle_provider_errors("test provider")
        def get_thumbnail_url(self, isbn):
            raise req.exceptions.JSONDecodeError("Expecting value", "<html>", 0)

    assert _Provider().get_thumbnail_url("9780134685991") == (None, "test provider")

    mock_logger.warning.assert_not_called()
    reported = [call[0][0] for call in mock_logger.exception.call_args_list]
    assert any("Request error" in msg for msg in reported)
