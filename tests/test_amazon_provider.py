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

"""Tests for Amazon provider."""

import io

import pytest
import requests
from isbnlib import to_isbn10
from PIL import Image

from rero_invenio_thumbnails.contrib.amazon.api import AmazonProvider

_ISBN13 = "9782070612758"
_ISBN10 = "2070612759"
_COVER_URL = f"https://images-na.ssl-images-amazon.com/images/P/{_ISBN10}.01.LZZZZZZZ.jpg"


def _make_jpeg(width=100, height=150):
    img = Image.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()


def _make_gif_1x1():
    """Return a minimal 43-byte GIF — Amazon's placeholder for unknown ASINs."""
    img = Image.new("RGB", (1, 1), color="white")
    buf = io.BytesIO()
    img.save(buf, format="GIF")
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# isbnlib.to_isbn10 (smoke tests)
# ---------------------------------------------------------------------------


def test_to_isbn10_valid_978():
    """Convert a 978-prefix ISBN-13 to ISBN-10."""
    assert to_isbn10("9782070612758") == "2070612759"
    assert to_isbn10("9782745919595") == "2745919598"


def test_to_isbn10_check_digit_x():
    """ISBN-10 with check digit X (value 10)."""
    assert to_isbn10("9780804429573") == "080442957X"


def test_to_isbn10_979_prefix():
    """979-prefix ISBNs have no ISBN-10 equivalent."""
    assert to_isbn10("9790001138673") == ""


def test_to_isbn10_invalid():
    """Invalid strings return empty string."""
    assert to_isbn10("invalid") == ""
    assert to_isbn10("978207061275") == ""  # 12 digits


# ---------------------------------------------------------------------------
# AmazonProvider
# ---------------------------------------------------------------------------


def test_amazon_get_thumbnail_url_success_isbn13(app, requests_mock):
    """Test successful cover retrieval using an ISBN-13."""
    requests_mock.get(_COVER_URL, status_code=200, content=_make_jpeg())

    provider = AmazonProvider()
    url, name = provider.get_thumbnail_url(_ISBN13)

    assert url == _COVER_URL
    assert name == "amazon"
    assert requests_mock.call_count == 1


def test_amazon_get_thumbnail_url_success_isbn10(app, requests_mock):
    """Test successful cover retrieval using an ISBN-10 directly."""
    requests_mock.get(_COVER_URL, status_code=200, content=_make_jpeg())

    provider = AmazonProvider()
    url, name = provider.get_thumbnail_url(_ISBN10)

    assert url == _COVER_URL
    assert name == "amazon"


def test_amazon_get_thumbnail_url_hyphenated_isbn(app, requests_mock):
    """Test that hyphens are stripped before the request."""
    requests_mock.get(_COVER_URL, status_code=200, content=_make_jpeg())

    provider = AmazonProvider()
    url, name = provider.get_thumbnail_url("978-2-07-061275-8")

    assert url == _COVER_URL
    assert name == "amazon"


def test_amazon_get_thumbnail_url_placeholder_gif(app, requests_mock):
    """Test that Amazon's 1x1 GIF placeholder is rejected."""
    requests_mock.get(_COVER_URL, status_code=200, content=_make_gif_1x1())

    provider = AmazonProvider()
    url, name = provider.get_thumbnail_url(_ISBN13)

    assert url is None
    assert name == "amazon"


def test_amazon_get_thumbnail_url_979_prefix(app, requests_mock):
    """Test that 979-prefix ISBN-13 (no ASIN) returns None without a request."""
    provider = AmazonProvider()
    url, name = provider.get_thumbnail_url("9790001138673")

    assert url is None
    assert name == "amazon"
    assert requests_mock.call_count == 0


def test_amazon_get_thumbnail_url_not_found(app, requests_mock):
    """Test that a 404 response returns None."""
    requests_mock.get(_COVER_URL, status_code=404)

    provider = AmazonProvider()
    url, name = provider.get_thumbnail_url(_ISBN13)

    assert url is None
    assert name == "amazon"


def test_amazon_get_thumbnail_url_request_exception(app, requests_mock):
    """Test that connection errors are handled gracefully."""
    requests_mock.get(_COVER_URL, exc=requests.exceptions.ConnectionError("timeout"))

    provider = AmazonProvider()
    url, name = provider.get_thumbnail_url(_ISBN13)

    assert url is None
    assert name == "amazon"


def test_amazon_get_thumbnail_url_small_image(app, requests_mock):
    """Test that images below the minimum dimension are rejected."""
    requests_mock.get(_COVER_URL, status_code=200, content=_make_jpeg(width=5, height=5))

    provider = AmazonProvider()
    url, name = provider.get_thumbnail_url(_ISBN13)

    assert url is None
    assert name == "amazon"


def test_amazon_get_thumbnail_url_empty_isbn(app, requests_mock):
    """Test that an empty/invalid ISBN returns None without a network call."""
    provider = AmazonProvider()
    url, name = provider.get_thumbnail_url("")

    assert url is None
    assert name == "amazon"
    assert requests_mock.call_count == 0


@pytest.mark.external
def test_amazon_real_thumbnail_is_valid_image(app):
    """Test that Amazon returns a real image for a known ISBN."""
    provider = AmazonProvider()
    url, name = provider.get_thumbnail_url("9782070612758")

    assert name == "amazon"
    assert url is not None, "Amazon returned no cover URL for ISBN 9782070612758"
    assert "images-na.ssl-images-amazon.com" in url


@pytest.mark.external
def test_amazon_real_thumbnail_pre2010_french(app):
    """Test that Amazon has a cover for a pre-2010 French book unavailable on BNF."""
    provider = AmazonProvider()
    url, name = provider.get_thumbnail_url("9782745919595")

    assert name == "amazon"
    assert url is not None, "Amazon returned no cover for ISBN 9782745919595 (Éditions Milan, 2005)"
