# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for Flask views (blueprint endpoints)."""

import os
import tempfile
import time
from unittest.mock import patch

import pytest


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


# ---------------------------------------------------------------------------
# /thumbnails-url/<isbn>
# ---------------------------------------------------------------------------


def test_get_thumbnail_url_endpoint_success(app, client):
    """Test successful JSON response from /thumbnails-url endpoint."""
    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock:
        mock.return_value = ("https://example.com/cover.jpg", "open library")

        response = client.get("/thumbnails-url/9780134685991")

        assert response.status_code == 200
        data = response.get_json()
        assert data["url"] == "https://example.com/cover.jpg"
        assert data["isbn"] == "9780134685991"
        assert data["provider"] == "open library"


def test_get_thumbnail_url_endpoint_not_found(app, client):
    """Test 404 response when no thumbnail URL found."""
    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock:
        mock.return_value = (None, "open library")

        response = client.get("/thumbnails-url/9999999999999")

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Thumbnail not found"
        assert data["isbn"] == "9999999999999"
        assert "message" in data


def test_get_thumbnail_url_endpoint_cached_false(app, client):
    """Test that cached=false query param is forwarded correctly."""
    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock:
        mock.return_value = ("https://example.com/cover.jpg", "files")

        client.get("/thumbnails-url/9780134685991?cached=false")

        mock.assert_called_once_with("9780134685991", cached=False)


def test_get_thumbnail_url_endpoint_cached_true_by_default(app, client):
    """Test that cached defaults to True when not specified."""
    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock:
        mock.return_value = ("https://example.com/cover.jpg", "files")

        client.get("/thumbnails-url/9780134685991")

        mock.assert_called_once_with("9780134685991", cached=True)


def test_get_thumbnail_url_endpoint_server_error(app, client):
    """Test 500 response when an exception is raised in the view."""
    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock:
        mock.side_effect = Exception("unexpected")

        response = client.get("/thumbnails-url/9780134685991")

        assert response.status_code == 500
        data = response.get_json()
        assert data["error"] == "Server error"
        assert data["isbn"] == "9780134685991"


def test_get_thumbnail_url_endpoint_cache_headers_positive_max_age(app, client):
    """Test Cache-Control header is set when max_age > 0."""
    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock:
        app.config["RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE"] = 3600
        mock.return_value = ("https://example.com/cover.jpg", "open library")

        response = client.get("/thumbnails-url/9780134685991")

        assert response.status_code == 200
        assert "max-age=3600" in response.headers["Cache-Control"]
        assert "public" in response.headers["Cache-Control"]


def test_get_thumbnail_url_endpoint_no_cache_when_max_age_zero(app, client):
    """Test no-cache headers when max_age is 0 (covers add_cache_headers else branch)."""
    with patch("rero_invenio_thumbnails.views.get_thumbnail_url") as mock:
        app.config["RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE"] = 0
        mock.return_value = ("https://example.com/cover.jpg", "open library")

        response = client.get("/thumbnails-url/9780134685991")

        assert response.status_code == 200
        assert "no-cache" in response.headers["Cache-Control"]
        assert response.headers.get("Pragma") == "no-cache"
        assert response.headers.get("Expires") == "0"


# ---------------------------------------------------------------------------
# /thumbnails/<isbn>
# ---------------------------------------------------------------------------


def test_serve_thumbnail_jpeg_success(app, client):
    """Test serving a JPEG thumbnail file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        isbn = "9780134685991"
        path = os.path.join(temp_dir, f"{isbn}.jpg")
        with open(path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        response = client.get(f"/thumbnails/{isbn}")

        assert response.status_code == 200
        assert response.mimetype == "image/jpeg"
        assert "ETag" in response.headers
        assert "Last-Modified" in response.headers
        assert "Cache-Control" in response.headers


def test_serve_thumbnail_png_success(app, client):
    """Test serving a PNG thumbnail file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        isbn = "9780134685992"
        path = os.path.join(temp_dir, f"{isbn}.png")
        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")

        response = client.get(f"/thumbnails/{isbn}")

        assert response.status_code == 200
        assert response.mimetype == "image/png"


def test_serve_thumbnail_not_found(app, client):
    """Test 404 when no thumbnail file exists for the ISBN."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

        response = client.get("/thumbnails/9999999999999")

        assert response.status_code == 404
        data = response.get_json()
        assert data["error"] == "Thumbnail not found"
        assert data["isbn"] == "9999999999999"


def test_serve_thumbnail_directory_missing(app, client):
    """Test 404 when the configured directory does not exist."""
    app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/nonexistent/path"

    response = client.get("/thumbnails/9780134685991")

    assert response.status_code == 404


def test_serve_thumbnail_etag_304_on_match(app, client):
    """Test 304 Not Modified when ETag matches If-None-Match header."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        isbn = "9780134685991"
        path = os.path.join(temp_dir, f"{isbn}.jpg")
        with open(path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        first = client.get(f"/thumbnails/{isbn}")
        etag = first.headers["ETag"]

        response = client.get(f"/thumbnails/{isbn}", headers={"If-None-Match": etag})

        assert response.status_code == 304
        assert response.headers["ETag"] == etag


def test_serve_thumbnail_etag_200_on_mismatch(app, client):
    """Test 200 when ETag does not match If-None-Match header."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        isbn = "9780134685991"
        path = os.path.join(temp_dir, f"{isbn}.jpg")
        with open(path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        response = client.get(f"/thumbnails/{isbn}", headers={"If-None-Match": '"stale-etag"'})

        assert response.status_code == 200


def test_serve_thumbnail_if_modified_since_304(app, client):
    """Test 304 Not Modified when file not modified since client date."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        isbn = "9780134685991"
        path = os.path.join(temp_dir, f"{isbn}.jpg")
        with open(path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        first = client.get(f"/thumbnails/{isbn}")
        last_modified = first.headers["Last-Modified"]

        response = client.get(f"/thumbnails/{isbn}", headers={"If-Modified-Since": last_modified})

        assert response.status_code == 304


def test_serve_thumbnail_if_modified_since_invalid_date(app, client):
    """Test 200 when If-Modified-Since header has an unparseable date."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        isbn = "9780134685991"
        path = os.path.join(temp_dir, f"{isbn}.jpg")
        with open(path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        response = client.get(f"/thumbnails/{isbn}", headers={"If-Modified-Since": "not-a-date"})

        assert response.status_code == 200
        assert "ETag" in response.headers


def test_serve_thumbnail_etag_changes_after_file_update(app, client):
    """Test ETag changes when the file is updated."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        isbn = "9780134685991"
        path = os.path.join(temp_dir, f"{isbn}.jpg")

        with open(path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")
        etag1 = client.get(f"/thumbnails/{isbn}").headers["ETag"]

        time.sleep(1.1)  # Ensure mtime changes on filesystems with 1-second resolution
        with open(path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00")
        etag2 = client.get(f"/thumbnails/{isbn}").headers["ETag"]

        assert etag1 != etag2


def test_serve_thumbnail_cache_headers_positive_max_age(app, client):
    """Test Cache-Control header with max_age > 0 on image response."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE"] = 86400
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        isbn = "9780134685991"
        path = os.path.join(temp_dir, f"{isbn}.jpg")
        with open(path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        response = client.get(f"/thumbnails/{isbn}")

        assert response.status_code == 200
        assert "max-age=86400" in response.headers["Cache-Control"]


def test_serve_thumbnail_no_cache_when_max_age_zero(app, client):
    """Test no-cache headers on image response when max_age is 0."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config["RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE"] = 0
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir
        isbn = "9780134685991"
        path = os.path.join(temp_dir, f"{isbn}.jpg")
        with open(path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01")

        response = client.get(f"/thumbnails/{isbn}")

        assert response.status_code == 200
        assert "no-cache" in response.headers["Cache-Control"]


def test_serve_thumbnail_exception_returns_500(app, client):
    """Test 500 response when FilesProvider raises an unexpected exception."""
    with patch("rero_invenio_thumbnails.views.FilesProvider") as mock_cls:
        mock_cls.return_value.get_thumbnail_path.side_effect = RuntimeError("disk failure")

        response = client.get("/thumbnails/9780134685991")

        assert response.status_code == 500
        data = response.get_json()
        assert data["error"] == "Server error"
        assert data["isbn"] == "9780134685991"
