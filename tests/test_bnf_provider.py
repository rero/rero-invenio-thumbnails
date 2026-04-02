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

"""Tests for BNF provider."""

import io

import pytest
import requests
from PIL import Image

from rero_invenio_thumbnails.contrib.bnf.api import BnfProvider

_ISBN = "9782070360284"
_URL = f"https://openapi.bnf.fr/couverture/image/image/recupererImage?ISBN={_ISBN}&couverture=1"


def _make_jpeg(width=100, height=150):
    img = Image.new("RGB", (width, height), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()


def test_bnf_init(app):
    """Test BNF provider initialisation."""
    with app.app_context():
        provider = BnfProvider()
        assert provider.cover_page == 1
        assert "openapi.bnf.fr" in provider.base_url
        assert "rero-invenio-thumbnails" in provider.headers["User-Agent"]


def test_bnf_get_thumbnail_url_success(app, requests_mock):
    """Test successful thumbnail URL retrieval."""
    with app.app_context():
        requests_mock.get(_URL, status_code=200, headers={"Content-Type": "image/jpeg"}, content=_make_jpeg())

        provider = BnfProvider()
        url, name = provider.get_thumbnail_url(_ISBN)

        assert url == _URL
        assert name == "bnf"
        assert requests_mock.call_count == 1


def test_bnf_get_thumbnail_url_hyphenated_isbn(app, requests_mock):
    """Test that hyphens are stripped from the ISBN before the request."""
    with app.app_context():
        requests_mock.get(_URL, status_code=200, headers={"Content-Type": "image/jpeg"}, content=_make_jpeg())

        provider = BnfProvider()
        url, name = provider.get_thumbnail_url("978-2-07-036028-4")

        assert url == _URL
        assert name == "bnf"


def test_bnf_get_thumbnail_url_not_found(app, requests_mock):
    """Test that None is returned when BNF returns 404."""
    with app.app_context():
        requests_mock.get(_URL, status_code=404)

        provider = BnfProvider()
        url, name = provider.get_thumbnail_url(_ISBN)

        assert url is None
        assert name == "bnf"


def test_bnf_get_thumbnail_url_server_error(app, requests_mock):
    """Test that None is returned when BNF returns 500."""
    with app.app_context():
        requests_mock.get(_URL, status_code=500)

        provider = BnfProvider()
        url, name = provider.get_thumbnail_url(_ISBN)

        assert url is None
        assert name == "bnf"


def test_bnf_get_thumbnail_url_invalid_content(app, requests_mock):
    """Test that None is returned when the response is not an image."""
    with app.app_context():
        requests_mock.get(_URL, status_code=200, headers={"Content-Type": "text/html"}, content=b"<html></html>")

        provider = BnfProvider()
        url, name = provider.get_thumbnail_url(_ISBN)

        assert url is None
        assert name == "bnf"


def test_bnf_get_thumbnail_url_small_image(app, requests_mock):
    """Test that placeholder images below min dimension are rejected."""
    with app.app_context():
        requests_mock.get(
            _URL, status_code=200, headers={"Content-Type": "image/jpeg"}, content=_make_jpeg(width=5, height=5)
        )

        provider = BnfProvider()
        url, name = provider.get_thumbnail_url(_ISBN)

        assert url is None
        assert name == "bnf"


def test_bnf_get_thumbnail_url_request_exception(app, requests_mock):
    """Test that a connection error is handled gracefully."""
    with app.app_context():
        requests_mock.get(_URL, exc=requests.exceptions.ConnectionError("timeout"))

        provider = BnfProvider()
        url, name = provider.get_thumbnail_url(_ISBN)

        assert url is None
        assert name == "bnf"


@pytest.mark.external
def test_bnf_real_thumbnail_is_valid_image(app):
    """Test that BNF returns a real valid image for a known ISBN."""
    with app.app_context():
        provider = BnfProvider()
        url, name = provider.get_thumbnail_url("9782070612758")

        assert name == "bnf"
        assert url is not None, "BNF returned no cover URL for ISBN 9782070612758"
        assert "openapi.bnf.fr" in url
