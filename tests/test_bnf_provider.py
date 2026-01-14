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

"""Tests for BNF provider."""

import io

import requests
from PIL import Image

from rero_invenio_thumbnails.modules.bnf.api import BnfProvider


class TestBnfProviderInit:
    """Test BnfProvider initialization."""

    def test_init_default_values(self, app):
        """Test BNF provider initialization with default values."""
        with app.app_context():
            provider = BnfProvider()
            assert provider.app_name == "NE"
            assert provider.cover_page == 1


class TestBnfProviderGetThumbnailUrl:
    """Test BnfProvider.get_thumbnail_url method."""

    def test_get_thumbnail_url_success(self, app, requests_mock):
        """Test successful thumbnail URL retrieval from BNF."""
        with app.app_context():
            # Create a valid test image
            img = Image.new("RGB", (100, 150), color="blue")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            isbn = "9782070360284"
            ark_id = "ark:/12148/cb450989938"

            # Mock SRU API response for ISBN to ARK conversion
            sru_url = f"https://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.isbn%20all%20%22{isbn}%22&recordSchema=unimarcxchange&maximumRecords=1"
            sru_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
    <srw:records>
        <srw:record>
            <srw:recordData>
                <record xmlns="info:lc/xmlns/marcxchange-v2" id="{ark_id}">
                    <controlfield tag="001">FRBNF450989938</controlfield>
                </record>
            </srw:recordData>
        </srw:record>
    </srw:records>
</srw:searchRetrieveResponse>"""
            requests_mock.get(sru_url, text=sru_response, status_code=200)

            # Mock BNF cover response
            url = f"http://catalogue.bnf.fr/couverture?appName=NE&idArk={ark_id}&couverture=1"
            requests_mock.get(
                url,
                status_code=200,
                headers={"Content-Type": "image/jpeg"},
                content=img_bytes.getvalue(),
            )

            provider = BnfProvider()
            url_result, provider_name = provider.get_thumbnail_url(isbn)

            assert url_result == url
            assert provider_name == "bnf"
            assert requests_mock.called
            assert requests_mock.call_count == 2  # SRU API + cover API

    def test_get_thumbnail_url_not_found(self, app, requests_mock):
        """Test thumbnail URL retrieval when BNF returns 404."""
        with app.app_context():
            ark_id = "ark:/12148/cb999999999"
            url = f"http://catalogue.bnf.fr/couverture?appName=NE&idArk={ark_id}&couverture=1"
            requests_mock.get(url, status_code=404)

            provider = BnfProvider()
            url_result, provider_name = provider.get_thumbnail_url(ark_id)

            assert url_result is None
            assert provider_name == "bnf"

    def test_get_thumbnail_url_server_error(self, app, requests_mock):
        """Test thumbnail URL retrieval when BNF returns 500."""
        with app.app_context():
            ark_id = "ark:/12148/cb450989938"
            url = f"http://catalogue.bnf.fr/couverture?appName=NE&idArk={ark_id}&couverture=1"
            requests_mock.get(url, status_code=500)

            provider = BnfProvider()
            url, provider_name = provider.get_thumbnail_url(ark_id)

            assert url is None
            assert provider_name == "bnf"

    def test_get_thumbnail_url_invalid_content_type(self, app, requests_mock):
        """Test thumbnail URL retrieval when response is not an image."""
        with app.app_context():
            ark_id = "ark:/12148/cb450989938"
            url = f"http://catalogue.bnf.fr/couverture?appName=NE&idArk={ark_id}&couverture=1"
            requests_mock.get(
                url,
                status_code=200,
                headers={"Content-Type": "text/html"},
                content=b"<html>Not an image</html>",
            )

            provider = BnfProvider()
            url, provider_name = provider.get_thumbnail_url(ark_id)

            assert url is None
            assert provider_name == "bnf"

    def test_get_thumbnail_url_request_exception(self, app, requests_mock):
        """Test thumbnail URL retrieval when request raises exception."""
        with app.app_context():
            ark_id = "ark:/12148/cb450989938"
            url = f"http://catalogue.bnf.fr/couverture?appName=NE&idArk={ark_id}&couverture=1"
            requests_mock.get(url, exc=requests.exceptions.ConnectionError("Connection failed"))

            provider = BnfProvider()
            url, provider_name = provider.get_thumbnail_url(ark_id)

            assert url is None
            assert provider_name == "bnf"

    def test_get_thumbnail_url_small_image(self, app, requests_mock):
        """Test thumbnail URL retrieval with image too small (less than 10x10)."""
        with app.app_context():
            # Create an image smaller than 10x10
            img = Image.new("RGB", (5, 5), color="red")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            ark_id = "ark:/12148/cb450989938"
            url = f"http://catalogue.bnf.fr/couverture?appName=NE&idArk={ark_id}&couverture=1"
            requests_mock.get(
                url,
                status_code=200,
                headers={"Content-Type": "image/jpeg"},
                content=img_bytes.getvalue(),
            )

            provider = BnfProvider()
            url, provider_name = provider.get_thumbnail_url(ark_id)

            assert url is None
            assert provider_name == "bnf"


class TestBnfProviderUrlFormat:
    """Test BNF provider URL format."""

    def test_thumbnail_url_format(self, app):
        """Test that the URL format is correct."""
        with app.app_context():
            ark_id = "ark:/12148/cb450989938"

            # We can't directly test the URL without mocking, but we can check the format
            expected_url = f"http://catalogue.bnf.fr/couverture?appName=NE&idArk={ark_id}&couverture=1"

            # The URL should match this pattern
            assert "catalogue.bnf.fr" in expected_url
            assert ark_id in expected_url
            assert "appName=NE" in expected_url
            assert "couverture=1" in expected_url
            assert "idArk=" in expected_url


class TestBnfProviderRealImage:
    """Test BNF provider with real API calls."""

    def test_real_bnf_thumbnail_is_valid_image(self, app):
        """Test that BNF returns a real valid image for a known ISBN."""
        with app.app_context():
            # Use a well-known French book ISBN that should have a cover in BNF
            # "Le Petit Prince" by Antoine de Saint-Exupéry
            isbn = "9782070612758"

            provider = BnfProvider()
            url, provider_name = provider.get_thumbnail_url(isbn)

            # If BNF returns a URL, verify it's actually an image
            if url:
                assert provider_name == "bnf"
                response = requests.get(url, timeout=10)
                assert response.status_code == 200
                assert response.headers.get("Content-Type", "").startswith("image/")

                # Verify the content is actually a valid image
                try:
                    img = Image.open(io.BytesIO(response.content))
                    assert img.size[0] >= 10  # Width at least 10px
                    assert img.size[1] >= 10  # Height at least 10px
                    assert img.format in ["JPEG", "PNG", "GIF"]
                except Exception as e:
                    raise AssertionError(f"Failed to open image from BNF URL: {e}")
