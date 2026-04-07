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

"""Tests for WikidataProvider."""

import json
import re

import pytest

from rero_invenio_thumbnails.contrib.wikidata.api import WikidataProvider

# SPARQL and Commons API URL patterns
SPARQL_RE = re.compile(r".*query\.wikidata\.org.*")
COMMONS_RE = re.compile(r".*commons\.wikimedia\.org.*")

# Minimal SPARQL response with one image binding
SPARQL_RESPONSE_FOUND = json.dumps(
    {"results": {"bindings": [{"image": {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/Cover.jpg"}}]}}
)

# SPARQL response with no results
SPARQL_RESPONSE_NOT_FOUND = json.dumps({"results": {"bindings": []}})

# Commons imageinfo API response with a thumb URL
COMMONS_RESPONSE_FOUND = json.dumps(
    {
        "query": {
            "pages": {
                "12345": {
                    "imageinfo": [
                        {
                            "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/x/xx/Cover.jpg/300px-Cover.jpg"
                        }
                    ]
                }
            }
        }
    }
)

# Commons imageinfo API response with no imageinfo (file not found)
COMMONS_RESPONSE_NOT_FOUND = json.dumps({"query": {"pages": {"-1": {}}}})


def test_wikidata_provider_success(app, requests_mock):
    """Test Wikidata provider returns cover URL when both APIs succeed."""
    with app.app_context():
        thumb_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/x/xx/Cover.jpg/300px-Cover.jpg"
        requests_mock.get(SPARQL_RE, text=SPARQL_RESPONSE_FOUND, status_code=200)
        requests_mock.get(COMMONS_RE, text=COMMONS_RESPONSE_FOUND, status_code=200)
        requests_mock.get(thumb_url, content=create_test_image(), status_code=200)

        url, provider_name = WikidataProvider().get_thumbnail_url("9782957688708")

        assert provider_name == "wikidata"
        assert url == thumb_url


def test_wikidata_provider_isbn_to_commons_filename_success(app, requests_mock):
    """Test isbn_to_commons_filename extracts filename from SPARQL response."""
    with app.app_context():
        requests_mock.get(SPARQL_RE, text=SPARQL_RESPONSE_FOUND, status_code=200)

        provider = WikidataProvider()
        filename = provider.isbn_to_commons_filename("9782957688708")

        assert filename == "Cover.jpg"


def test_wikidata_provider_isbn_to_commons_filename_not_found(app, requests_mock):
    """Test isbn_to_commons_filename returns None when no Wikidata entry exists."""
    with app.app_context():
        requests_mock.get(SPARQL_RE, text=SPARQL_RESPONSE_NOT_FOUND, status_code=200)

        provider = WikidataProvider()
        filename = provider.isbn_to_commons_filename("9999999999999")

        assert filename is None


def test_wikidata_provider_isbn_to_commons_filename_http_error(app, requests_mock):
    """Test isbn_to_commons_filename returns None on SPARQL HTTP error."""
    with app.app_context():
        requests_mock.get(SPARQL_RE, status_code=500)

        provider = WikidataProvider()
        filename = provider.isbn_to_commons_filename("9782957688708")

        assert filename is None


def test_wikidata_provider_commons_filename_to_thumb_url_success(app, requests_mock):
    """Test commons_filename_to_thumb_url returns thumburl from imageinfo response."""
    with app.app_context():
        requests_mock.get(COMMONS_RE, text=COMMONS_RESPONSE_FOUND, status_code=200)

        provider = WikidataProvider()
        url = provider.commons_filename_to_thumb_url("Cover.jpg")

        assert url == "https://upload.wikimedia.org/wikipedia/commons/thumb/x/xx/Cover.jpg/300px-Cover.jpg"


def test_wikidata_provider_commons_filename_to_thumb_url_not_found(app, requests_mock):
    """Test commons_filename_to_thumb_url returns None when file not in Commons."""
    with app.app_context():
        requests_mock.get(COMMONS_RE, text=COMMONS_RESPONSE_NOT_FOUND, status_code=200)

        provider = WikidataProvider()
        url = provider.commons_filename_to_thumb_url("NonExistent.jpg")

        assert url is None


def test_wikidata_provider_commons_filename_to_thumb_url_http_error(app, requests_mock):
    """Test commons_filename_to_thumb_url returns None on HTTP error."""
    with app.app_context():
        requests_mock.get(COMMONS_RE, status_code=503)

        provider = WikidataProvider()
        url = provider.commons_filename_to_thumb_url("Cover.jpg")

        assert url is None


def test_wikidata_provider_no_sparql_result(app, requests_mock):
    """Test get_thumbnail_url returns None when ISBN not in Wikidata."""
    with app.app_context():
        requests_mock.get(SPARQL_RE, text=SPARQL_RESPONSE_NOT_FOUND, status_code=200)

        url, provider_name = WikidataProvider().get_thumbnail_url("9999999999999")

        assert url is None
        assert provider_name == "wikidata"


def test_wikidata_provider_no_commons_image(app, requests_mock):
    """Test get_thumbnail_url returns None when Commons has no imageinfo."""
    with app.app_context():
        requests_mock.get(SPARQL_RE, text=SPARQL_RESPONSE_FOUND, status_code=200)
        requests_mock.get(COMMONS_RE, text=COMMONS_RESPONSE_NOT_FOUND, status_code=200)

        url, provider_name = WikidataProvider().get_thumbnail_url("9782957688708")

        assert url is None
        assert provider_name == "wikidata"


def test_wikidata_provider_image_too_small(app, requests_mock):
    """Test get_thumbnail_url returns None when image is too small."""
    with app.app_context():
        thumb_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/x/xx/Cover.jpg/300px-Cover.jpg"
        requests_mock.get(SPARQL_RE, text=SPARQL_RESPONSE_FOUND, status_code=200)
        requests_mock.get(COMMONS_RE, text=COMMONS_RESPONSE_FOUND, status_code=200)
        requests_mock.get(thumb_url, content=create_test_image(5, 5), status_code=200)

        url, provider_name = WikidataProvider().get_thumbnail_url("9782957688708")

        assert url is None
        assert provider_name == "wikidata"


def test_wikidata_provider_isbn_with_hyphens(app, requests_mock):
    """Test that ISBN hyphens are stripped before querying."""
    with app.app_context():
        thumb_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/x/xx/Cover.jpg/300px-Cover.jpg"
        requests_mock.get(SPARQL_RE, text=SPARQL_RESPONSE_FOUND, status_code=200)
        requests_mock.get(COMMONS_RE, text=COMMONS_RESPONSE_FOUND, status_code=200)
        requests_mock.get(thumb_url, content=create_test_image(), status_code=200)

        url, provider_name = WikidataProvider().get_thumbnail_url("978-2-9576887-0-8")

        assert provider_name == "wikidata"
        assert url == thumb_url
        # Verify the SPARQL request was made with cleaned ISBN
        assert "9782957688708" in requests_mock.request_history[0].url


def test_wikidata_provider_init_defaults(app):
    """Test WikidataProvider initializes with expected defaults."""
    with app.app_context():
        provider = WikidataProvider()

        assert provider.name == "wikidata"
        assert "query.wikidata.org" in provider.sparql_url
        assert "commons.wikimedia.org" in provider.commons_api_url
        assert provider.thumb_width == 300
        assert "rero-invenio-thumbnails" in provider.headers["User-Agent"]
        assert "github.com/rero/rero-invenio-thumbnails" in provider.headers["User-Agent"]


@pytest.mark.network
def test_wikidata_real_thumbnail_is_valid_image(app):
    """Test that Wikidata returns a real valid image for a known ISBN."""
    with app.app_context():
        provider = WikidataProvider()
        # ISBN 978-2-9576887-0-8 (Q100601027) has P18 directly on the edition
        url, provider_name = provider.get_thumbnail_url("9782957688708")

        assert provider_name == "wikidata"
        assert url is not None, "Wikidata returned no cover URL for ISBN 9782957688708"
        assert "wikimedia.org" in url
