# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Configuration options for RERO Invenio Thumbnails.

This module defines all configurable parameters for the thumbnail service,
including provider selection, caching behavior, retry logic, and HTTP headers.
"""

# Base URL of the ILS (Invenio instance) used for constructing thumbnail endpoints
RERO_INVENIO_THUMBNAILS_URL = "http://localhost"

# Minimum image dimensions for validation (width and height in pixels)
# Rationale for choosing 50 pixels:
# - Rejects 1x1 pixel tracking images commonly used by CDNs and analytics
# - Filters out tiny placeholder images (typically 2x2, 4x4, or 8x8 pixels)
# - Too small to be useful as thumbnails (unreadable on any display)
# - Most legitimate book cover thumbnails are at least 50x50 pixels
# - Provides a safety margin while being permissive enough for edge cases
# - Based on empirical observation of actual thumbnail sizes from providers
RERO_INVENIO_THUMBNAILS_MIN_IMAGE_DIMENSION = 50

# Cache key prefix for thumbnail URLs
RERO_INVENIO_THUMBNAILS_CACHE_KEY_PREFIX = "rero_thumbnails"

# List of thumbnail providers to query in order (first match wins).
# Default provider order optimized for typical usage patterns.
# Override in instance config to customize provider precedence.
#
# Note: "dnb" is NOT included by default because its cover images are sourced
# from VLB (operated by MVB GmbH) and require a paid data licence.  To enable
# it, add "dnb" to your instance-specific RERO_INVENIO_THUMBNAILS_PROVIDERS.
RERO_INVENIO_THUMBNAILS_PROVIDERS = [
    "files",
    "google books",
    "google api",
    "bnf",
    "amazon",
    "internet archive",
    "open library"  # Open Library is last because it has frequent timeouts
]

# Local directory for storing thumbnail files (used by FilesProvider)
RERO_INVENIO_THUMBNAILS_FILES_DIR = "./thumbnails"

# Cache expiration time in seconds (default: 1 hour)
RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE = 60 * 60

# HTTP Cache-Control max-age in seconds for browser/CDN caching (default: 24 hours)
# Set to 0 to disable HTTP caching
RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE = 86400

# Default HTTP request timeout as (connect, read) in seconds for cover image fetches.
# Increase if providers are timing out; decrease for faster fallback to next provider.
RERO_INVENIO_THUMBNAILS_HTTP_TIMEOUT = (2, 10)
