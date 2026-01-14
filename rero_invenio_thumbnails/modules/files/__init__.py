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

"""Local files thumbnail provider module.

Provides thumbnail image URLs from local file storage, supporting integration
with Invenio Files system. Searches for thumbnail files using ISBN as filename.

Usage:
    >>> from rero_invenio_thumbnails.modules.files.api import FilesProvider
    >>> provider = FilesProvider()
    >>> path = provider.get_thumbnail_path('9780134685991')
    >>> url = provider.get_thumbnail_url('9780134685991')

Configuration:
    RERO_INVENIO_THUMBNAILS_FILES_DIR: Directory containing thumbnail files
"""
