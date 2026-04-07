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

"""Tests for SyndeticsProvider."""

import re

import pytest

from rero_invenio_thumbnails.contrib.syndetics.api import SyndeticsProvider

SYNDETICS_RE = re.compile(r".*syndetics\.com.*")


def test_syndetics_provider_success(app, requests_mock):
    """Test Syndetics provider returns cover URL for a valid ISBN."""
    with app.app_context():
        isbn = "9782070612758"
        url = f"https://www.syndetics.com/index.aspx?isbn={isbn}/LC.GIF"
        requests_mock.get(url, content=create_test_image(), status_code=200)

        result_url, provider_name = SyndeticsProvider().get_thumbnail_url(isbn)

        assert provider_name == "syndetics"
        assert result_url == url


def test_syndetics_provider_isbn_with_hyphens(app, requests_mock):
    """Test that ISBN hyphens are stripped before constructing the URL."""
    with app.app_context():
        url = "https://www.syndetics.com/index.aspx?isbn=9782070612758/LC.GIF"
        requests_mock.get(url, content=create_test_image(), status_code=200)

        result_url, provider_name = SyndeticsProvider().get_thumbnail_url("978-2-07-061275-8")

        assert provider_name == "syndetics"
        assert result_url == url


def test_syndetics_provider_no_cover(app, requests_mock):
    """Test Syndetics returns None when response is HTML (no cover exists)."""
    with app.app_context():
        requests_mock.get(
            SYNDETICS_RE,
            status_code=200,
            headers={"Content-Type": "text/html"},
            content=b"<html>No cover found</html>",
        )

        url, provider_name = SyndeticsProvider().get_thumbnail_url("9999999999999")

        assert url is None
        assert provider_name == "syndetics"


def test_syndetics_provider_http_error(app, requests_mock):
    """Test Syndetics returns None on HTTP error."""
    with app.app_context():
        requests_mock.get(SYNDETICS_RE, status_code=404)

        url, provider_name = SyndeticsProvider().get_thumbnail_url("9782070612758")

        assert url is None
        assert provider_name == "syndetics"


def test_syndetics_provider_small_image(app, requests_mock):
    """Test Syndetics returns None when image is too small (placeholder)."""
    with app.app_context():
        requests_mock.get(
            SYNDETICS_RE,
            content=create_test_image(5, 5),
            status_code=200,
        )

        url, provider_name = SyndeticsProvider().get_thumbnail_url("9782070612758")

        assert url is None
        assert provider_name == "syndetics"


def test_syndetics_provider_init_defaults(app):
    """Test SyndeticsProvider initializes with expected defaults."""
    with app.app_context():
        provider = SyndeticsProvider()

        assert provider.name == "syndetics"
        assert "syndetics.com" in provider.base_url
        assert provider.size == "LC.GIF"


def test_syndetics_provider_with_client_key(app, requests_mock):
    """Test that client key is appended when configured."""
    with app.app_context():
        app.config["RERO_INVENIO_THUMBNAILS_SYNDETICS_CLIENT"] = "mykey"
        isbn = "9782070612758"
        url = f"https://www.syndetics.com/index.aspx?isbn={isbn}/LC.GIF&client=mykey"
        requests_mock.get(url, content=create_test_image(), status_code=200)

        result_url, provider_name = SyndeticsProvider().get_thumbnail_url(isbn)

        assert provider_name == "syndetics"
        assert result_url == url
        assert "client=mykey" in result_url


def test_syndetics_provider_without_client_key(app, requests_mock):
    """Test that no client parameter is added when key is not configured."""
    with app.app_context():
        app.config["RERO_INVENIO_THUMBNAILS_SYNDETICS_CLIENT"] = ""
        isbn = "9782070612758"
        url = f"https://www.syndetics.com/index.aspx?isbn={isbn}/LC.GIF"
        requests_mock.get(url, content=create_test_image(), status_code=200)

        result_url, _ = SyndeticsProvider().get_thumbnail_url(isbn)

        assert result_url == url
        assert "client=" not in result_url


@pytest.mark.external
def test_syndetics_real_thumbnail_is_valid_image(app):
    """Test that Syndetics returns a real valid image for a known ISBN."""
    with app.app_context():
        provider = SyndeticsProvider()
        # 9782070612758 confirmed 274x400 JPEG in coverage benchmark
        url, provider_name = provider.get_thumbnail_url("9782070612758")

        assert provider_name == "syndetics"
        assert url is not None, "Syndetics returned no cover URL for ISBN 9782070612758"
        assert "syndetics.com" in url
