# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test suite for RERO Invenio Thumbnails.

This package contains comprehensive tests for the rero-invenio-thumbnails
extension, including unit tests for individual providers and integration tests.

Test Structure:
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
