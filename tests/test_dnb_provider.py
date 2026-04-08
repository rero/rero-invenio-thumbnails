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

"""Tests for DNB provider."""

import io

import pytest
import requests
from PIL import Image

from rero_invenio_thumbnails.contrib.dnb.api import DnbProvider

_ISBN = "9783161484100"
_URL = f"https://portal.dnb.de/opac/mvb/cover?isbn={_ISBN}"


def _make_jpeg(width=100, height=150):
    img = Image.new("RGB", (width, height), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()


def test_dnb_init(app):
    """Test DNB provider initialisation."""
    with app.app_context():
        provider = DnbProvider()
        assert provider.name == "dnb"
        assert "portal.dnb.de" in provider.base_url


def test_dnb_get_thumbnail_url_success(app, requests_mock):
    """Test successful cover retrieval — single HTTP call, no SRU lookup."""
    with app.app_context():
        requests_mock.get(_URL, status_code=200, headers={"Content-Type": "image/jpeg"}, content=_make_jpeg())

        provider = DnbProvider()
        url, name = provider.get_thumbnail_url(_ISBN)

        assert url == _URL
        assert name == "dnb"
        assert requests_mock.call_count == 1


def test_dnb_get_thumbnail_url_hyphenated_isbn(app, requests_mock):
    """Test that hyphens are stripped before constructing the URL."""
    with app.app_context():
        requests_mock.get(_URL, status_code=200, headers={"Content-Type": "image/jpeg"}, content=_make_jpeg())

        provider = DnbProvider()
        url, name = provider.get_thumbnail_url("978-3-16-148410-0")

        assert url == _URL
        assert name == "dnb"


def test_dnb_get_thumbnail_url_not_found(app, requests_mock):
    """Test that None is returned when DNB returns 404."""
    with app.app_context():
        requests_mock.get(_URL, status_code=404)

        provider = DnbProvider()
        url, name = provider.get_thumbnail_url(_ISBN)

        assert url is None
        assert name == "dnb"


def test_dnb_get_thumbnail_url_server_error(app, requests_mock):
    """Test that None is returned when DNB returns 500."""
    with app.app_context():
        requests_mock.get(_URL, status_code=500)

        provider = DnbProvider()
        url, name = provider.get_thumbnail_url(_ISBN)

        assert url is None
        assert name == "dnb"


def test_dnb_get_thumbnail_url_invalid_content(app, requests_mock):
    """Test that None is returned when the response is not an image."""
    with app.app_context():
        requests_mock.get(_URL, status_code=200, headers={"Content-Type": "text/html"}, content=b"<html></html>")

        provider = DnbProvider()
        url, name = provider.get_thumbnail_url(_ISBN)

        assert url is None
        assert name == "dnb"


def test_dnb_get_thumbnail_url_small_image(app, requests_mock):
    """Test that placeholder images below min dimension are rejected."""
    with app.app_context():
        requests_mock.get(
            _URL, status_code=200, headers={"Content-Type": "image/jpeg"}, content=_make_jpeg(width=5, height=5)
        )

        provider = DnbProvider()
        url, name = provider.get_thumbnail_url(_ISBN)

        assert url is None
        assert name == "dnb"


def test_dnb_get_thumbnail_url_request_exception(app, requests_mock):
    """Test that a connection error is handled gracefully."""
    with app.app_context():
        requests_mock.get(_URL, exc=requests.exceptions.ConnectionError("timeout"))

        provider = DnbProvider()
        url, name = provider.get_thumbnail_url(_ISBN)

        assert url is None
        assert name == "dnb"


def test_dnb_get_thumbnail_url_empty_isbn(app, requests_mock):
    """Test that an empty ISBN returns None without making any network calls."""
    with app.app_context():
        provider = DnbProvider()
        url, name = provider.get_thumbnail_url("")

        assert url is None
        assert name == "dnb"
        assert requests_mock.call_count == 0, (
            "DnbProvider.get_thumbnail_url should not make any HTTP request for an empty ISBN"
        )


@pytest.mark.external
def test_dnb_real_thumbnail_is_valid_image(app):
    """Test that DNB returns a real valid image for a known ISBN."""
    with app.app_context():
        provider = DnbProvider()
        url, name = provider.get_thumbnail_url("9783730615522")

        assert name == "dnb"
        assert url is not None, "DNB returned no cover URL for ISBN 9783730615522"
        assert "portal.dnb.de" in url
