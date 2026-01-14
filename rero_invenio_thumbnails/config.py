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

"""RERO Invenio module that adds thumbnails."""

# List of thumbnail providers to query in order (first match wins)
RERO_INVENIO_THUMBNAILS_PROVIDERS = ["files", "open_library", "google_books", "google_api", "amazon"]

# Local directory for storing thumbnail files (used by FilesProvider)
RERO_INVENIO_THUMBNAILS_FILES_DIR = "./thumbnails"

# Cache expiration time in seconds for Redis cache (default: 1 hour = 3600 seconds)
RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE = 60 * 60
