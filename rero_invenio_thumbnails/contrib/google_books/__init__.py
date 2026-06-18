# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Google Books preview API thumbnail provider module.

This module provides thumbnail retrieval functionality using the Google Books preview
API (viewapi endpoint). It fetches book preview URLs and thumbnails using a JSONP
callback format for cross-domain requests.

The provider uses Google's public Books API viewapi endpoint, which provides book
preview information including thumbnail URLs without requiring authentication. It handles
JSONP response parsing and validates thumbnail URLs before returning them.

Key Features:
    - No API key required (public endpoint)
    - JSONP callback format support
    - Cross-domain request compatibility
    - ISBN cleaning (removes hyphens and spaces)
    - JSON parsing with error handling
    - Image validation with dimension checks
    - Automatic retry with exponential backoff

Example::

    from rero_invenio_thumbnails.contrib.google_books.api import GoogleBooksProvider
    provider = GoogleBooksProvider()
    url, name = provider.get_thumbnail_url('978-0-13-468599-1')
    # url == "https://books.google.com/books/about/book_title.html?id=abc123"

API Documentation:
    - Google Books viewapi endpoint
    - URL format: https://books.google.com/books?jscmd=viewapi&callback=book&bibkeys={isbn}
    - JSONP format: book({...data...});

Response Format:
    The API returns JSONP with the following structure:
    book({
        "{isbn}": {
            "thumbnail_url": "https://...",
            "preview_url": "https://...",
            "info_url": "https://..."
        }
    });

Note:
    - Returns None if preview not available
    - Handles malformed JSONP responses gracefully
    - Validates thumbnail URLs to ensure they point to valid images
    - May not have previews for all books
    - Subject to Google's usage policies
"""
