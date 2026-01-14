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

"""Thumbnails Files."""

import os
from contextlib import suppress

from flask import current_app

from rero_invenio_thumbnails.modules.api import BaseProvider
from rero_invenio_thumbnails.modules.utils import clean_isbn


class FilesProvider(BaseProvider):
    """Thumbnail provider for local file storage.

    This provider retrieves book cover thumbnails from local file storage,
    supporting integration with the Invenio Files system.
    """

    def __init__(self):
        """Initialize the Files provider.

        Examples:
            >>> # Default provider
            >>> provider = FilesProvider()
        """
        self.base_url = current_app.config.get("RERO_ILS_URL", "http://localhost")

    def get_thumbnail_path(self, isbn):
        """Retrieve the file path for a thumbnail from local file storage.

        This method searches the configured files directory for a thumbnail
        matching the ISBN and returns the absolute file path.

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13 format).
        :returns: str or None - The absolute file path of the thumbnail if found,
            None otherwise.

        Note:
            - Searches for files named: {isbn}.jpg, {isbn}.png, {isbn}.jpeg
            - Requires RERO_INVENIO_THUMBNAILS_FILES_DIR configuration
            - Returns None if directory doesn't exist or file not found
        """
        # Clean ISBN (remove hyphens and spaces)
        clean_isbn_value = clean_isbn(isbn)
        with suppress(Exception):
            # Get the configured files directory
            files_dir = current_app.config.get("RERO_INVENIO_THUMBNAILS_FILES_DIR", "./thumbnails")

            # Convert to absolute path if relative
            if not os.path.isabs(files_dir):
                files_dir = os.path.join(current_app.root_path, files_dir)

            # Ensure the directory exists
            if not os.path.isdir(files_dir):
                current_app.logger.debug(f"Files directory does not exist: {files_dir}")
                return None

            # Search for thumbnail file with common image extensions
            supported_extensions = [".jpg", ".jpeg", ".png"]

            for ext in supported_extensions:
                thumbnail_path = os.path.join(files_dir, f"{clean_isbn_value}{ext}")

                if os.path.isfile(thumbnail_path):
                    return thumbnail_path

            return None
        return None

    def get_thumbnail_url(self, isbn):
        """Retrieve the HTTPS URL for a thumbnail from local file storage.

        This method searches for a thumbnail file and returns the complete
        HTTPS URL that can be used to access it via the web endpoint.

        :param isbn: The ISBN of the book (ISBN-10 or ISBN-13 format).
        :returns: tuple - (url, provider_name) where url is the HTTPS URL of the
            thumbnail if found (None otherwise), and provider_name is "files".

        Examples:
            >>> provider = FilesProvider()
            >>> url, provider = provider.get_thumbnail_url("9780134685991")
            >>> print(url, provider)
            https://example.com/thumbnails/9780134685991 files

        Note:
            - Returns (None, "files") if thumbnail file is not found
            - URL is constructed from the Flask application URL root
            - Requires the application context to be active
        """
        # Clean ISBN (remove hyphens and spaces)
        clean_isbn_value = clean_isbn(isbn)
        with suppress(Exception):
            # First check if the file exists
            thumbnail_path = self.get_thumbnail_path(clean_isbn_value)

            if not thumbnail_path:
                return None, "files"

            return f"{self.base_url}/thumbnails/{clean_isbn_value}", "files"
        return None, "files"
