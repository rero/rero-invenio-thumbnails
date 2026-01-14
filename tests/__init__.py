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

"""Test suite for RERO Invenio Thumbnails.

This package contains comprehensive tests for the rero-invenio-thumbnails
extension, including unit tests for individual providers and integration tests.

Test Structure:
    - test_amazon_provider.py: Amazon provider tests
    - test_files_provider.py: Local files provider tests
    - test_google_api_provider.py: Google Custom Search API provider tests
    - test_google_books_provider.py: Google Books provider tests
    - test_open_library_provider.py: Open Library provider tests
    - test_rero_invenio_thumbnails.py: Extension and blueprint tests

Coverage:
    - Provider functionality and error handling
    - Caching behavior
    - HTTP endpoint serving
    - Configuration management
    - Cache integration with fixtures
"""
