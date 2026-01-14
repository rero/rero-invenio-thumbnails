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

from rero_invenio_thumbnails.modules.files.api import FilesProvider


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def files_provider():
    """Create a FilesProvider instance for testing."""
    return FilesProvider()


class TestFilesProviderGetThumbnailPath:
    """Test FilesProvider.get_thumbnail_path method."""

    def test_get_thumbnail_path_success(self, app, temp_dir, files_provider):
        """Test successful thumbnail path retrieval."""
        with app.app_context():
            # Create a test file
            test_isbn = "9780134685991"
            test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
            open(test_file, "w").close()

            # Configure app to use temp directory
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Test
            path = files_provider.get_thumbnail_path(test_isbn)

            # Assertions
            assert path is not None
            assert path == test_file
            assert os.path.isfile(path)

    def test_get_thumbnail_path_multiple_extensions(self, app, temp_dir, files_provider):
        """Test thumbnail path retrieval with multiple file extensions."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Test each supported extension
            extensions = [".jpg", ".jpeg", ".png"]
            for ext in extensions:
                test_isbn = f"isbn_{ext[1:]}"
                test_file = os.path.join(temp_dir, f"{test_isbn}{ext}")
                open(test_file, "w").close()

                path = files_provider.get_thumbnail_path(test_isbn)
                assert path == test_file
                os.remove(test_file)

    def test_get_thumbnail_path_not_found(self, app, temp_dir, files_provider):
        """Test thumbnail path retrieval when file not found."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Test
            path = files_provider.get_thumbnail_path("nonexistent-isbn")

            # Assertions
            assert path is None

    def test_get_thumbnail_path_directory_not_exist(self, app, files_provider):
        """Test thumbnail path retrieval when directory doesn't exist."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/nonexistent/directory"

            # Test
            path = files_provider.get_thumbnail_path("9780134685991")

            # Assertions
            assert path is None

    def test_get_thumbnail_path_relative_path(self, app, temp_dir, files_provider):
        """Test thumbnail path retrieval with relative path configuration."""
        with app.app_context():
            # Create a test file
            test_isbn = "9780134685991"
            test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
            open(test_file, "w").close()

            # Use relative path
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Test
            path = files_provider.get_thumbnail_path(test_isbn)

            # Assertions
            assert path is not None
            assert os.path.isfile(path)

    def test_get_thumbnail_path_exception_handling(self, app, files_provider):
        """Test exception handling in get_thumbnail_path."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/some/path"

            # Test with non-existent path
            path = files_provider.get_thumbnail_path("9780134685991")

            # Assertions
            assert path is None


class TestFilesProviderGetThumbnailUrl:
    """Test FilesProvider.get_thumbnail_url method."""

    def test_get_thumbnail_url_success(self, app, temp_dir, files_provider):
        """Test successful thumbnail URL retrieval."""
        with app.app_context():
            # Create a test file
            test_isbn = "9780134685991"
            test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
            open(test_file, "w").close()

            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Test
            url = files_provider.get_thumbnail_url(test_isbn)

            # Assertions
            assert url is not None
            assert test_isbn in url
            assert "/thumbnails/" in url
            assert url.startswith("http")

    def test_get_thumbnail_url_not_found(self, app, temp_dir, files_provider):
        """Test thumbnail URL retrieval when file not found."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Test
            url = files_provider.get_thumbnail_url("nonexistent-isbn")

            # Assertions
            assert url is None

    def test_get_thumbnail_url_format(self, app, temp_dir, files_provider):
        """Test thumbnail URL format."""
        with app.app_context():
            # Create a test file
            test_isbn = "9780134685991"
            test_file = os.path.join(temp_dir, f"{test_isbn}.jpg")
            open(test_file, "w").close()

            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Test
            url = files_provider.get_thumbnail_url(test_isbn)

            # Assertions
            assert "http" in url
            assert test_isbn in url
            assert url.endswith(test_isbn)

    def test_get_thumbnail_url_exception_handling(self, app, files_provider):
        """Test exception handling in get_thumbnail_url."""
        app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = "/some/path"

        # Test
        url = files_provider.get_thumbnail_url("9780134685991")

        # Assertions
        assert url is None


class TestFilesProviderDefaults:
    """Test FilesProvider default behavior."""

    def test_default_directory_config(self, app, files_provider):
        """Test default directory configuration."""
        with app.app_context():
            # Don't configure a directory, should use default
            path = files_provider.get_thumbnail_path("any-isbn")

            # Should return None for non-existent default directory
            assert path is None

    def test_multiple_calls(self, app, temp_dir, files_provider):
        """Test multiple consecutive calls."""
        with app.app_context():
            app.config["RERO_INVENIO_THUMBNAILS_FILES_DIR"] = temp_dir

            # Create multiple test files
            isbns = ["isbn1", "isbn2", "isbn3"]
            for isbn in isbns:
                test_file = os.path.join(temp_dir, f"{isbn}.jpg")
                open(test_file, "w").close()

            # Test
            for isbn in isbns:
                path = files_provider.get_thumbnail_path(isbn)
                assert path is not None
                assert isbn in path
