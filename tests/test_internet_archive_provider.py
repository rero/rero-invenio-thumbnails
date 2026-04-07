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

"""Tests for InternetArchiveProvider."""

import json
import re

import pytest

from rero_invenio_thumbnails.contrib.internet_archive.api import InternetArchiveProvider

IA_SEARCH_RE = re.compile(r".*archive\.org/advancedsearch.*")
IA_IMG_RE = re.compile(r".*archive\.org/services/img/.*")

OCAID = "lepetitnicelasvil0000unse"
ISBN = "9782070360284"

SEARCH_RESPONSE = json.dumps({"response": {"numFound": 1, "docs": [{"identifier": OCAID}]}}).encode()
EMPTY_SEARCH_RESPONSE = json.dumps({"response": {"numFound": 0, "docs": []}}).encode()


def test_internet_archive_provider_success(app, requests_mock):
    """Test IA provider returns cover URL when OCAID and image are found."""
    with app.app_context():
        requests_mock.get(IA_SEARCH_RE, content=SEARCH_RESPONSE, status_code=200)
        requests_mock.get(IA_IMG_RE, content=create_test_image(), status_code=200)

        url, provider_name = InternetArchiveProvider().get_thumbnail_url(ISBN)

        assert provider_name == "internet archive"
        assert url == f"https://archive.org/services/img/{OCAID}"


def test_internet_archive_provider_isbn_with_hyphens(app, requests_mock):
    """Test that ISBN hyphens are stripped before the search query."""
    with app.app_context():
        requests_mock.get(IA_SEARCH_RE, content=SEARCH_RESPONSE, status_code=200)
        requests_mock.get(IA_IMG_RE, content=create_test_image(), status_code=200)

        url, provider_name = InternetArchiveProvider().get_thumbnail_url("978-2-07-036028-4")

        assert provider_name == "internet archive"
        assert url == f"https://archive.org/services/img/{OCAID}"
        # Confirm hyphens were stripped: digits are never percent-encoded so the clean ISBN is in the URL
        assert "9782070360284" in requests_mock.request_history[0].url


def test_internet_archive_provider_no_search_result(app, requests_mock):
    """Test IA returns None when no item is found for the ISBN."""
    with app.app_context():
        requests_mock.get(IA_SEARCH_RE, content=EMPTY_SEARCH_RESPONSE, status_code=200)

        url, provider_name = InternetArchiveProvider().get_thumbnail_url("9999999999999")

        assert url is None
        assert provider_name == "internet archive"


def test_internet_archive_provider_search_http_error(app, requests_mock):
    """Test IA returns None when the search API returns an error."""
    with app.app_context():
        requests_mock.get(IA_SEARCH_RE, status_code=503)

        url, provider_name = InternetArchiveProvider().get_thumbnail_url(ISBN)

        assert url is None
        assert provider_name == "internet archive"


def test_internet_archive_provider_image_not_found(app, requests_mock):
    """Test IA returns None when the cover image request fails."""
    with app.app_context():
        requests_mock.get(IA_SEARCH_RE, content=SEARCH_RESPONSE, status_code=200)
        requests_mock.get(IA_IMG_RE, status_code=404)

        url, provider_name = InternetArchiveProvider().get_thumbnail_url(ISBN)

        assert url is None
        assert provider_name == "internet archive"


def test_internet_archive_provider_small_image(app, requests_mock):
    """Test IA returns None when the cover image is too small (placeholder)."""
    with app.app_context():
        requests_mock.get(IA_SEARCH_RE, content=SEARCH_RESPONSE, status_code=200)
        requests_mock.get(IA_IMG_RE, content=create_test_image(5, 5), status_code=200)

        url, provider_name = InternetArchiveProvider().get_thumbnail_url(ISBN)

        assert url is None
        assert provider_name == "internet archive"


def test_internet_archive_provider_init_defaults(app):
    """Test InternetArchiveProvider initializes with expected defaults."""
    with app.app_context():
        provider = InternetArchiveProvider()

        assert provider.name == "internet archive"
        assert "archive.org" in provider.search_url
        assert "rero-invenio-thumbnails" in provider.headers["User-Agent"]
        assert "github.com/rero/rero-invenio-thumbnails" in provider.headers["User-Agent"]


def test_internet_archive_isbn_to_ocaid_success(app, requests_mock):
    """Test isbn_to_ocaid returns identifier from search response."""
    with app.app_context():
        requests_mock.get(IA_SEARCH_RE, content=SEARCH_RESPONSE, status_code=200)

        ocaid = InternetArchiveProvider().isbn_to_ocaid(ISBN)

        assert ocaid == OCAID


def test_internet_archive_isbn_to_ocaid_not_found(app, requests_mock):
    """Test isbn_to_ocaid returns None when no results."""
    with app.app_context():
        requests_mock.get(IA_SEARCH_RE, content=EMPTY_SEARCH_RESPONSE, status_code=200)

        ocaid = InternetArchiveProvider().isbn_to_ocaid("9999999999999")

        assert ocaid is None


def test_internet_archive_isbn_to_ocaid_invalid_json(app, requests_mock):
    """Test isbn_to_ocaid returns None on malformed JSON response."""
    with app.app_context():
        requests_mock.get(IA_SEARCH_RE, content=b"not-json", status_code=200)

        ocaid = InternetArchiveProvider().isbn_to_ocaid(ISBN)

        assert ocaid is None


@pytest.mark.external
def test_internet_archive_real_thumbnail_is_valid_image(app):
    """Test that Internet Archive returns a real valid image for a known ISBN."""
    with app.app_context():
        provider = InternetArchiveProvider()
        # Le Petit Nice - confirmed present in Internet Archive
        url, provider_name = provider.get_thumbnail_url("9782070360284")

        assert provider_name == "internet archive"
        assert url is not None, "Internet Archive returned no cover URL for ISBN 9782070360284"
        assert "archive.org" in url
