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

"""Google Books API thumbnail provider module.

This module provides thumbnail retrieval functionality using the Google Books API.
It queries Google's extensive book database to retrieve cover images and metadata
using ISBN numbers.

The provider uses the Google Books API volumes endpoint, which provides access to
millions of books without requiring authentication for basic searches. It validates
results to ensure exactly one match is found before returning thumbnail URLs.

Key Features:
    - No API key required for basic searches
    - Access to millions of book covers
    - Automatic ISBN-13 and ISBN-10 support
    - ISBN cleaning (removes hyphens and spaces)
    - Result validation (requires unique match)
    - Image validation with dimension checks
    - Automatic retry with exponential backoff

Example:
    >>> from rero_invenio_thumbnails.modules.google_api.api import GoogleApiProvider
    >>> provider = GoogleApiProvider()
    >>> url = provider.get_thumbnail_url('978-0-13-468599-1')
    >>> print(url)
    http://books.google.com/books/content?id=abc123&printsec=frontcover&img=1

API Documentation:
    - Google Books API: https://developers.google.com/books/docs/v1/using
    - Volumes endpoint: https://www.googleapis.com/books/v1/volumes
    - Query format: ?q=isbn:{isbn}

Response Format:
    The API returns JSON with the following structure:
    {
        "totalItems": 1,
        "items": [{
            "volumeInfo": {
                "imageLinks": {
                    "thumbnail": "http://..."
                }
            }
        }]
    }

Note:
    - Returns None if no books found or multiple matches detected
    - Validates thumbnail URLs before returning
    - Requires internet connectivity
    - Subject to Google API rate limits
"""
