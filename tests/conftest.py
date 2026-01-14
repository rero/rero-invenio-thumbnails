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

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

import contextlib
from io import BytesIO

import pytest
import requests
from flask import Flask
from invenio_app.factory import create_app as _create_app

# Ensure invenio-cache is available in tests
from invenio_cache.ext import InvenioCache
from PIL import Image

# Import extensions to initialize
from rero_invenio_thumbnails.ext import REROInvenioThumbnails


def create_test_image(width=100, height=150, color="blue"):
    """Create a test image and return its bytes.

    This function is available in all test files without needing to import it.
    """
    img = Image.new("RGB", (width, height), color=color)
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes.getvalue()


# Make create_test_image available as a module-level variable for all tests
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest and inject create_test_image into test namespace."""
    import builtins

    builtins.create_test_image = create_test_image


class NetworkAccessError(RuntimeError):
    """Exception raised when test attempts to access external network."""


@pytest.fixture(autouse=True)
def no_external_requests(monkeypatch, request):
    """Prevent tests from making real HTTP requests.

    This fixture is automatically used for all tests to ensure network isolation.
    Tests using requests_mock will automatically mock all requests.
    """
    # Skip monkeypatching if requests_mock fixture is used in the test
    if "requests_mock" in request.fixturenames:
        return  # Let requests_mock handle mocking

    def mock_request(*args, **kwargs):
        """Raise an error if a test tries to make a real HTTP request."""
        url = args[0] if args else kwargs.get("url", "unknown")
        raise NetworkAccessError(
            f"Test attempted to make real HTTP request to {url}. "
            f"All external requests must be mocked. "
            f"Use the requests_mock fixture in your test."
        )

    # Monkeypatch all HTTP methods
    monkeypatch.setattr(requests, "get", mock_request)
    monkeypatch.setattr(requests, "post", mock_request)
    monkeypatch.setattr(requests, "put", mock_request)
    monkeypatch.setattr(requests, "delete", mock_request)
    monkeypatch.setattr(requests, "head", mock_request)
    monkeypatch.setattr(requests, "patch", mock_request)
    monkeypatch.setattr(requests, "request", mock_request)

    # Also patch requests.Session to prevent session-based requests
    monkeypatch.setattr(requests.Session, "get", mock_request)
    monkeypatch.setattr(requests.Session, "post", mock_request)
    monkeypatch.setattr(requests.Session, "put", mock_request)
    monkeypatch.setattr(requests.Session, "delete", mock_request)
    monkeypatch.setattr(requests.Session, "head", mock_request)
    monkeypatch.setattr(requests.Session, "patch", mock_request)
    monkeypatch.setattr(requests.Session, "request", mock_request)


@pytest.fixture(scope="module")
def app_config(app_config):
    """Application config override."""
    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return _create_app


@pytest.fixture
def app():
    """Create a Flask application for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True

    # Set empty providers by default for tests (tests configure explicitly)
    app.config["RERO_INVENIO_THUMBNAILS_PROVIDERS"] = []

    # Configure cache for testing (use simple in-memory cache, not Redis)
    app.config["CACHE_TYPE"] = "SimpleCache"

    # Initialize InvenioCache extension
    InvenioCache(app)

    # Initialize RERO Invenio Thumbnails extension (registers blueprint)
    REROInvenioThumbnails(app)

    # Clear cache after initialization
    with contextlib.suppress(Exception):
        from invenio_cache import current_cache

        with app.app_context():
            current_cache.clear()

    return app
