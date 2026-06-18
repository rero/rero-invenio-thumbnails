# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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

Example::

    from rero_invenio_thumbnails.contrib.files.api import FilesProvider
    provider = FilesProvider()

    # Get local file path
    path = provider.get_thumbnail_path('978-0-13-468599-1')
    # path == "/var/thumbnails/9780134685991.jpg"

    # Get web URL for serving
    url, name = provider.get_thumbnail_url('9780134685991')
    # url == "https://example.com/thumbnails/9780134685991"

Configuration:
    RERO_INVENIO_THUMBNAILS_FILES_DIR: Directory path containing thumbnail files
        - Can be absolute or relative to application root
        - Default: './thumbnails'

    RERO_INVENIO_THUMBNAILS_URL: Base URL for constructing thumbnail endpoints
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
