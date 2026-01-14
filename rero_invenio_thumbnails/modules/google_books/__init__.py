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

"""Google Books thumbnail provider module.

Provides thumbnail image URLs from Google Books API using ISBN numbers.
Handles JSONP responses and includes fallback mechanisms for missing previews.

Usage:
    >>> from rero_invenio_thumbnails.modules.google_books.api import GoogleBooksProvider
    >>> provider = GoogleBooksProvider()
    >>> url = provider.get_thumbnail_url('9780134685991')

Features:
    - JSONP parsing support
    - Automatic retry with backoff
    - Thumbnail size customization
"""
