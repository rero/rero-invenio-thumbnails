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

"""Local file storage thumbnail provider module.

This module provides thumbnail retrieval functionality from local file storage,
enabling integration with Invenio Files system and custom thumbnail repositories.

The provider searches for thumbnail files in a configured directory using ISBN
as the filename, supporting common image formats (JPG, PNG, JPEG). It provides
both file path retrieval and URL construction for serving thumbnails.

Key Features:
    - Local file system storage support
    - Multiple image format support (.jpg, .jpeg, .png)
    - Automatic file discovery by ISBN
    - Absolute and relative path handling
    - ISBN cleaning (removes hyphens and spaces)
    - URL construction for web serving
    - Integration with Flask configuration

Example:
    >>> from rero_invenio_thumbnails.modules.files.api import FilesProvider
    >>> provider = FilesProvider()
    >>>
    >>> # Get local file path
    >>> path = provider.get_thumbnail_path('978-0-13-468599-1')
    >>> print(path)
    /var/thumbnails/9780134685991.jpg
    >>>
    >>> # Get web URL for serving
    >>> url = provider.get_thumbnail_url('9780134685991')
    >>> print(url)
    https://example.com/thumbnails/9780134685991

Configuration:
    RERO_INVENIO_THUMBNAILS_FILES_DIR: Directory path containing thumbnail files
        - Can be absolute or relative to application root
        - Default: './thumbnails'

    RERO_ILS_URL: Base URL for constructing thumbnail endpoints
        - Used to generate full URLs for web serving
        - Default: 'http://localhost'

File Organization:
    Thumbnail files should be named using ISBN without hyphens:
    - 9780134685991.jpg
    - 9780134685991.png
    - 9780134685991.jpeg

Note:
    This provider is ideal for pre-loaded thumbnail collections or integration
    with existing digital asset management systems.
"""
