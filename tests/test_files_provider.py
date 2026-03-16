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

"""Tests for FilesProvider."""

import os
import tempfile

import pytest

from rero_invenio_thumbnails.contrib.files.api import FilesProvider


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_files_get_thumbnail_path_success(app, temp_dir):
    """Test successful thumbnail path retrieval."""
    with app.app_context():
        provider = FilesProvider()
        test_isbn = "9780134685991"
        test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
        open(test_file, "w").close()
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

        path = provider.get_thumbnail_path(test_isbn)

        assert path == test_file
        assert os.path.isfile(path)


def test_files_get_thumbnail_path_multiple_extensions(app, temp_dir):
    """Test thumbnail path retrieval with multiple file extensions."""
    with app.app_context():
        provider = FilesProvider()
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

        for ext in [".jpg", ".jpeg", ".png"]:
            test_isbn = f"isbn_{ext[1:]}"
            test_file = os.path.join(temp_dir, f"{test_isbn}{ext}")
            open(test_file, "w").close()

            path = provider.get_thumbnail_path(test_isbn)
            assert path == test_file
            os.remove(test_file)


def test_files_get_thumbnail_path_not_found(app, temp_dir):
    """Test thumbnail path retrieval when file not found."""
    with app.app_context():
        provider = FilesProvider()
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

        assert provider.get_thumbnail_path("nonexistent-isbn") is None


def test_files_get_thumbnail_path_directory_not_exist(app):
    """Test thumbnail path retrieval when directory doesn't exist."""
    with app.app_context():
        provider = FilesProvider()
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/nonexistent/directory"

        assert provider.get_thumbnail_path("9780134685991") is None


def test_files_get_thumbnail_path_relative_path(app, temp_dir):
    """Test thumbnail path retrieval with relative path configuration."""
    with app.app_context():
        # Create a subdirectory under app.root_path to test relative path handling
        relative_dir = "test_thumbnails"
        full_dir = os.path.join(app.root_path, relative_dir)
        os.makedirs(full_dir, exist_ok=True)

        test_isbn = "9780134685991"
        test_file = os.path.join(full_dir, f"{test_isbn}.jpg")
        open(test_file, "w").close()

        # Use relative path to trigger the relative-path branch
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = relative_dir
        provider = FilesProvider()

        path = provider.get_thumbnail_path(test_isbn)

        assert path is not None
        assert os.path.isfile(path)

        # Cleanup
        os.remove(test_file)
        os.rmdir(full_dir)


def test_files_get_thumbnail_path_exception_handling(app, monkeypatch, temp_dir):
    """Test exception handling in get_thumbnail_path."""
    with app.app_context():
        # First test: directory doesn't exist (current test)
        provider = FilesProvider()
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/some/path"
        assert provider.get_thumbnail_path("9780134685991") is None

        # Second test: trigger OSError from filesystem operation
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

        def mock_isfile_raises(*args, **kwargs):
            raise OSError("Mocked OS error")

        monkeypatch.setattr(os.path, "isfile", mock_isfile_raises)
        assert provider.get_thumbnail_path("9780134685991") is None


def test_files_get_thumbnail_url_success(app, temp_dir):
    """Test successful thumbnail URL retrieval."""
    with app.app_context():
        provider = FilesProvider()
        test_isbn = "9780134685991"
        test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
        open(test_file, "w").close()
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

        url, provider_name = provider.get_thumbnail_url(test_isbn)

        assert url is not None
        assert provider_name == "files"
        assert test_isbn in url
        assert "/thumbnails/" in url
        assert url.startswith("http")


def test_files_get_thumbnail_url_not_found(app, temp_dir):
    """Test thumbnail URL retrieval when file not found."""
    with app.app_context():
        provider = FilesProvider()
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

        url, provider_name = provider.get_thumbnail_url("nonexistent-isbn")

        assert url is None
        assert provider_name == "files"


def test_files_get_thumbnail_url_format(app, temp_dir):
    """Test thumbnail URL format."""
    with app.app_context():
        provider = FilesProvider()
        test_isbn = "9780134685991"
        test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
        open(test_file, "w").close()
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

        url, provider_name = provider.get_thumbnail_url(test_isbn)

        assert "http" in url
        assert test_isbn in url
        assert url.endswith(test_isbn)
        assert provider_name == "files"


def test_files_get_thumbnail_url_exception_handling(app, monkeypatch):
    """Test exception handling in get_thumbnail_url."""
    with app.app_context():
        # Monkeypatch get_thumbnail_path to raise an exception
        def mock_get_thumbnail_path(isbn):
            raise Exception("Simulated error in get_thumbnail_path")

        monkeypatch.setattr(FilesProvider, "get_thumbnail_path", mock_get_thumbnail_path)

        url, provider_name = FilesProvider().get_thumbnail_url("9780134685991")

        assert url is None
        assert provider_name == "files"


def test_files_default_directory_config(app):
    """Test default directory configuration returns None for non-existent path."""
    with app.app_context():
        provider = FilesProvider()

        assert provider.get_thumbnail_path("any-isbn") is None


def test_files_multiple_calls(app, temp_dir):
    """Test multiple consecutive calls."""
    with app.app_context():
        provider = FilesProvider()
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

        isbns = ["isbn1", "isbn2", "isbn3"]
        for isbn in isbns:
            open(os.path.join(temp_dir, f"{isbn}.jpg"), "w").close()

        for isbn in isbns:
            path = provider.get_thumbnail_path(isbn)
            assert path is not None
            assert isbn in path
