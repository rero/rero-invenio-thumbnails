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

"""Configuration options for RERO Invenio Thumbnails.

This module defines all configurable parameters for the thumbnail service,
including provider selection, caching behavior, retry logic, and HTTP headers.
"""

from importlib.metadata import entry_points


def _load_provider_constants():
    """Generate provider name constants from entry points.

    This automatically creates constants for all registered providers,
    ensuring a single source of truth from pyproject.toml entry points.

    :returns: dict - Dictionary of provider constants
    """
    constants = {}
    eps = entry_points()

    # Handle both old (dict) and new (SelectableGroups) API
    provider_eps = (
        eps.get("rero_invenio_thumbnails.providers", [])
        if hasattr(eps, "get")
        else eps.select(group="rero_invenio_thumbnails.providers")
    )

    for ep in provider_eps:
        # Convert provider name to constant format: "open library" -> PROVIDER_OPEN_LIBRARY
        const_name = f"PROVIDER_{ep.name.upper().replace(' ', '_')}"
        constants[const_name] = ep.name

    return constants


# Dynamically generate provider constants from entry points
_PROVIDER_CONSTANTS = _load_provider_constants()

# Export provider constants to module namespace
globals().update(_PROVIDER_CONSTANTS)

# Explicitly declare constants for static type checkers (VSCode/Pylance)
# These are generated dynamically above but need explicit declarations for IDE support
PROVIDER_BNF: str = _PROVIDER_CONSTANTS.get("PROVIDER_BNF", "bnf")
PROVIDER_DNB: str = _PROVIDER_CONSTANTS.get("PROVIDER_DNB", "dnb")
PROVIDER_FILES: str = _PROVIDER_CONSTANTS.get("PROVIDER_FILES", "files")
PROVIDER_GOOGLE_API: str = _PROVIDER_CONSTANTS.get("PROVIDER_GOOGLE_API", "google api")
PROVIDER_GOOGLE_BOOKS: str = _PROVIDER_CONSTANTS.get("PROVIDER_GOOGLE_BOOKS", "google books")
PROVIDER_OPEN_LIBRARY: str = _PROVIDER_CONSTANTS.get("PROVIDER_OPEN_LIBRARY", "open library")

# Minimum image dimensions for validation (width and height in pixels)
# Rationale for choosing 50 pixels:
# - Rejects 1x1 pixel tracking images commonly used by CDNs and analytics
# - Filters out tiny placeholder images (typically 2x2, 4x4, or 8x8 pixels)
# - Too small to be useful as thumbnails (unreadable on any display)
# - Most legitimate book cover thumbnails are at least 50x50 pixels
# - Provides a safety margin while being permissive enough for edge cases
# - Based on empirical observation of actual thumbnail sizes from providers
MIN_IMAGE_DIMENSION = 50

# Cache key prefix for thumbnail URLs
CACHE_KEY_PREFIX = "rero_thumbnails"

# List of thumbnail providers to query in order (first match wins)
# Uses dynamically loaded provider names from entry points
RERO_INVENIO_THUMBNAILS_PROVIDERS = list(_PROVIDER_CONSTANTS.values())

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
