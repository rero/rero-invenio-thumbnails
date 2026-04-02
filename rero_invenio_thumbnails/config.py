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
# along with this program. If not, see <https://www.gnu.org/licenses/>.

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
RERO_INVENIO_THUMBNAILS_PROVIDERS = [
    "files",
    "bnf",
    "dnb",
    "google books",
    "google api",
    "open library"  # Open Library is last because it has frequent timeouts
]

# Local directory for storing thumbnail files (used by FilesProvider)
RERO_INVENIO_THUMBNAILS_FILES_DIR = "./thumbnails"

# Cache expiration time in seconds (default: 1 hour)
RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE = 60 * 60

# HTTP Cache-Control max-age in seconds for browser/CDN caching (default: 24 hours)
# Set to 0 to disable HTTP caching
RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE = 86400

# HTTP Retry Configuration
# Enable/disable automatic retries for failed HTTP requests to external providers
RERO_INVENIO_THUMBNAILS_RETRY_ENABLED = True

# Maximum number of retry attempts before giving up
RERO_INVENIO_THUMBNAILS_RETRY_ATTEMPTS = 5

# Exponential backoff multiplier (seconds between retries grow exponentially)
RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MULTIPLIER = 0.5

# Minimum wait time between retries (seconds)
RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MIN = 1

# Maximum wait time between retries (seconds)
RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MAX = 10
