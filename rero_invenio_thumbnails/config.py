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

# List of thumbnail providers to query in order (first match wins)
RERO_INVENIO_THUMBNAILS_PROVIDERS = ["files", "open library", "bnf", "google books", "google api", "amazon"]

# Local directory for storing thumbnail files (used by FilesProvider)
RERO_INVENIO_THUMBNAILS_FILES_DIR = "./thumbnails"

# Cache expiration time in seconds (default: 1 hour)
RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE = 60 * 60

# Cache backend: 'redis' (in-memory via invenio_cache) or 'filesystem' (disk-based)
RERO_INVENIO_THUMBNAILS_CACHE_TYPE = "redis"

# Directory for filesystem cache (only used when CACHE_TYPE='filesystem')
RERO_INVENIO_THUMBNAILS_CACHE_DIR = "./thumbnails/cache"

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
