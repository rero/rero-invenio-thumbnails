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

"""Thumbnail provider modules.

This package contains implementations of various thumbnail providers that
return URLs for book cover images from different sources.

Modules:
    amazon: Amazon product images provider
    files: Local file storage provider
    google_api: Google Custom Search API provider
    google_books: Google Books provider
    open_library: Open Library provider
    utils: Utility functions for HTTP requests with retry/backoff

Provider Interface:
    All provider classes implement get_thumbnail_url(isbn) method which
    returns the URL of a thumbnail image or None if not found.
"""
