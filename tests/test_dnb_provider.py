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
import re

import pytest
from PIL import Image

from rero_invenio_thumbnails.contrib.dnb.api import DnbProvider


def test_dnb_provider_success(app, requests_mock):
    """Test DNB provider returns cover URL from MARC21-XML."""
    img = Image.new("RGB", (100, 150), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    marc_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <datafield tag="856" ind1="4" ind2="2">
                            <subfield code="u">https://portal.dnb.de/opac/mvb/cover?isbn=9783161484100</subfield>
                            <subfield code="x">Cover image</subfield>
                        </datafield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    with app.app_context():
        requests_mock.get(re.compile(r".*services\.dnb\.de/sru.*"), status_code=200, text=marc_xml)
        requests_mock.get(
            "https://portal.dnb.de/opac/mvb/cover?isbn=9783161484100",
            status_code=200,
            headers={"Content-Type": "image/jpeg"},
            content=img_bytes.getvalue(),
        )

        provider = DnbProvider()
        url, provider_name = provider.get_thumbnail_url("9783161484100")

        assert url == "https://portal.dnb.de/opac/mvb/cover?isbn=9783161484100"
        assert provider_name == "dnb"


def test_dnb_provider_fallback_isbn_construction(app, requests_mock):
    """Test DNB provider constructs URL from ISBN when no 856 field exists."""
    img = Image.new("RGB", (100, 150), color="green")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    marc_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <datafield tag="020" ind1=" " ind2=" ">
                            <subfield code="a">9783161484100</subfield>
                        </datafield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    with app.app_context():
        requests_mock.get(re.compile(r".*services\.dnb\.de/sru.*"), status_code=200, text=marc_xml)
        requests_mock.get(
            "https://portal.dnb.de/opac/mvb/cover?isbn=9783161484100",
            status_code=200,
            headers={"Content-Type": "image/jpeg"},
            content=img_bytes.getvalue(),
        )

        provider = DnbProvider()
        url, provider_name = provider.get_thumbnail_url("9783161484100")

        assert url == "https://portal.dnb.de/opac/mvb/cover?isbn=9783161484100"
        assert provider_name == "dnb"


def test_dnb_provider_no_results(app, requests_mock):
    """Test DNB provider handles no results."""
    marc_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>0</numberOfRecords>
        <records/>
    </searchRetrieveResponse>"""

    with app.app_context():
        requests_mock.get(re.compile(r".*services\.dnb\.de/sru.*"), status_code=200, text=marc_xml)

        provider = DnbProvider()
        url, provider_name = provider.get_thumbnail_url("9999999999999")

        assert url is None
        assert provider_name == "dnb"


def test_dnb_provider_http_error(app, requests_mock):
    """Test DNB provider handles HTTP errors."""
    with app.app_context():
        requests_mock.get(re.compile(r".*services\.dnb\.de/sru.*"), status_code=500)

        provider = DnbProvider()
        url, provider_name = provider.get_thumbnail_url("9783161484100")

        assert url is None
        assert provider_name == "dnb"


def test_dnb_provider_malformed_xml(app, requests_mock):
    """Test DNB provider handles malformed XML."""
    with app.app_context():
        requests_mock.get(re.compile(r".*services\.dnb\.de/sru.*"), status_code=200, text="<invalid>xml")

        provider = DnbProvider()
        url, provider_name = provider.get_thumbnail_url("9783161484100")

        assert url is None
        assert provider_name == "dnb"


def test_dnb_provider_invalid_isbn(app):
    """Test DNB provider handles invalid ISBN."""
    with app.app_context():
        provider = DnbProvider()
        url, provider_name = provider.get_thumbnail_url("")

        assert url is None
        assert provider_name == "dnb"


def test_dnb_provider_keyword_matching(app, requests_mock):
    """Test DNB provider finds cover URLs with various keywords."""
    img = Image.new("RGB", (100, 150), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    marc_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <datafield tag="856" ind1="4" ind2="2">
                            <subfield code="u">https://example.com/thumbnail/book123.jpg</subfield>
                        </datafield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    with app.app_context():
        requests_mock.get(re.compile(r".*services\.dnb\.de/sru.*"), status_code=200, text=marc_xml)
        requests_mock.get(
            "https://example.com/thumbnail/book123.jpg",
            status_code=200,
            headers={"Content-Type": "image/jpeg"},
            content=img_bytes.getvalue(),
        )

        provider = DnbProvider()
        url, provider_name = provider.get_thumbnail_url("9783161484100")

        assert url == "https://example.com/thumbnail/book123.jpg"
        assert provider_name == "dnb"


def test_dnb_provider_note_matching(app, requests_mock):
    """Test DNB provider finds cover URLs via subfield x notes."""
    img = Image.new("RGB", (100, 150), color="yellow")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    marc_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
        <numberOfRecords>1</numberOfRecords>
        <records>
            <record>
                <recordData>
                    <record xmlns="http://www.loc.gov/MARC21/slim">
                        <datafield tag="856" ind1="4" ind2="2">
                            <subfield code="u">https://example.com/image/book.jpg</subfield>
                            <subfield code="x">Umschlagbild</subfield>
                        </datafield>
                    </record>
                </recordData>
            </record>
        </records>
    </searchRetrieveResponse>"""

    with app.app_context():
        requests_mock.get(re.compile(r".*services\.dnb\.de/sru.*"), status_code=200, text=marc_xml)
        requests_mock.get(
            "https://example.com/image/book.jpg",
            status_code=200,
            headers={"Content-Type": "image/jpeg"},
            content=img_bytes.getvalue(),
        )

        provider = DnbProvider()
        url, provider_name = provider.get_thumbnail_url("9783161484100")

        assert url == "https://example.com/image/book.jpg"
        assert provider_name == "dnb"


@pytest.mark.external
def test_dnb_real_thumbnail_is_valid_image(app):
    """Test that DNB returns a real valid image for a known ISBN."""
    with app.app_context():
        provider = DnbProvider()
        url, provider_name = provider.get_thumbnail_url("9783730615522")

        assert provider_name == "dnb"
        assert url is not None, "DNB returned no cover URL for ISBN 9783730615522"
        assert "portal.dnb.de" in url
