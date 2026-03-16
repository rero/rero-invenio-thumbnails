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

"""Utility functions for thumbnail fetching and validation.

This module provides shared utilities used by all thumbnail providers:
    - HTTP request handling with configurable retry logic
    - Image content validation (format, dimensions, quality checks)
    - Retry configuration from Flask app or environment variables
"""

import os
from contextlib import suppress
from functools import wraps
from io import BytesIO

import requests
from flask import current_app
from PIL import Image
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

# Disable retries when explicitly requested via env variable.
_DISABLE_RETRIES = os.getenv("RERO_THUMBNAILS_DISABLE_RETRIES", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def clean_isbn(isbn):
    """Clean ISBN by removing hyphens and spaces.

    :param isbn: The ISBN string to clean.
    :returns: str - The cleaned ISBN with hyphens and spaces removed.

    Examples:
        >>> clean_isbn("978-2-07-036028-4")
        '9782070360284'
        >>> clean_isbn("978 2 07 036028 4")
        '9782070360284'
        >>> clean_isbn("9782070360284")
        '9782070360284'
    """
    return isbn.replace("-", "").replace(" ", "")


def handle_provider_errors(provider_name):
    """Standardize error handling across providers.

    :param provider_name: Name of the provider for logging
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, isbn):
            try:
                return func(self, isbn)
            except ValueError as err:
                current_app.logger.warning(f"Invalid ISBN format for {provider_name} provider: {isbn}: {err!s}")
            except requests.RequestException as err:
                current_app.logger.error(
                    f"Request error retrieving thumbnail for ISBN {isbn} from {provider_name}: {err!s}", exc_info=True
                )
            except Exception as err:
                current_app.logger.error(
                    f"Unexpected error retrieving thumbnail for ISBN {isbn} from {provider_name}: {err!s}",
                    exc_info=True,
                )
            # Return tuple format (None, provider_name) to maintain consistency
            return None, provider_name.lower()

        return wrapper

    return decorator


def _get_retry_config():
    """Return retry settings from Flask config or defaults."""
    attempts = 5
    backoff_multiplier = 0.5
    backoff_min = 1
    backoff_max = 10
    enabled = True

    # Outside app context; stick to defaults
    with suppress(RuntimeError, AttributeError):
        if current_app and current_app.config:
            cfg = current_app.config
            attempts = cfg.get("RERO_INVENIO_THUMBNAILS_RETRY_ATTEMPTS", attempts)
            backoff_multiplier = cfg.get("RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MULTIPLIER", backoff_multiplier)
            backoff_min = cfg.get("RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MIN", backoff_min)
            backoff_max = cfg.get("RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MAX", backoff_max)
            enabled = cfg.get("RERO_INVENIO_THUMBNAILS_RETRY_ENABLED", enabled)

    return {
        "attempts": attempts,
        "backoff_multiplier": backoff_multiplier,
        "backoff_min": backoff_min,
        "backoff_max": backoff_max,
        "enabled": enabled,
    }


def fetch_with_retries(url, headers=None, timeout=5):
    """Fetch URL with automatic retries on connection errors.

    This function makes HTTP GET requests with automatic retry logic for transient
    failures using exponential backoff (in production only; disabled in tests
    for performance).

    :param url: The URL to fetch.
    :param headers: Optional HTTP headers to include in the request. Defaults to None.
    :param timeout: Request timeout in seconds. Defaults to 5.
    :returns: requests.Response object
    :raises requests.RequestException: If the request fails after all retries.

    Example::

        response = fetch_with_retries("https://api.example.com/data")
        response = fetch_with_retries("https://example.com/image.jpg", timeout=10)
        response = fetch_with_retries(
            "https://example.com/api",
            headers={"User-Agent": "MyApp/1.0"},
        )
    """
    cfg = _get_retry_config()

    if _DISABLE_RETRIES or not cfg["enabled"]:
        # In tests or when explicitly disabled, skip retries to avoid slow runs
        return requests.get(url, headers=headers, timeout=timeout)

    retrying = Retrying(
        stop=stop_after_attempt(cfg["attempts"]),
        wait=wait_exponential(
            multiplier=cfg["backoff_multiplier"],
            min=cfg["backoff_min"],
            max=cfg["backoff_max"],
        ),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True,
    )

    return retrying(requests.get, url, headers=headers, timeout=timeout)


def validate_image_content(content, provider_name="", isbn="", min_dimension=None):
    """Validate that image content is a real image with valid dimensions.

    This function checks that the provided content:
    1. Is not empty
    2. Can be opened as a valid image by PIL
    3. Has dimensions larger than the minimum threshold (to filter out placeholders)

    :param content: The image content as bytes.
    :param provider_name: Name of the provider (for logging). Defaults to "".
    :param isbn: ISBN being processed (for logging). Defaults to "".
    :param min_dimension: Minimum width/height in pixels. Defaults to
        ``RERO_INVENIO_THUMBNAILS_MIN_IMAGE_DIMENSION`` from app config.
    :returns: bool - True if the image is valid, False otherwise.

    Example::

        content = requests.get("https://example.com/cover.jpg").content
        if validate_image_content(content, "BNF", "9780134685991"):
            print("Valid image")
        # Filter out 1x1 pixel placeholders
        if validate_image_content(placeholder_data, min_dimension=10):
            print("Valid image")
    """
    if min_dimension is None:
        with suppress(AttributeError, RuntimeError):
            min_dimension = current_app.config.get("RERO_INVENIO_THUMBNAILS_MIN_IMAGE_DIMENSION")
        if min_dimension is None:
            min_dimension = 50
    if not content or len(content) == 0:
        with suppress(AttributeError, RuntimeError):
            current_app.logger.debug(f"Empty image data from {provider_name} for ISBN {isbn}")
        return False

    try:
        img = Image.open(BytesIO(content))
        width, height = img.size
        # Check for zero dimensions or placeholder images (typically 1x1 pixels)
        if width < min_dimension or height < min_dimension:
            with suppress(AttributeError, RuntimeError):
                current_app.logger.debug(
                    f"Invalid or placeholder image dimensions {width}x{height} from {provider_name} for ISBN {isbn}"
                )
            return False
        return True
    except (Image.UnidentifiedImageError, OSError) as e:
        with suppress(AttributeError, RuntimeError):
            current_app.logger.debug(f"Invalid image data from {provider_name} for ISBN {isbn}: {e}")
        return False
    except MemoryError as e:
        with suppress(AttributeError, RuntimeError):
            current_app.logger.debug(f"Memory error processing image from {provider_name} for ISBN {isbn}: {e}")
        return False


def fetch_and_validate_thumbnail(url, provider_name, isbn, timeout=5, min_dimension=None):
    """Fetch a thumbnail URL and validate it contains a real image.

    This helper function combines the common pattern of fetching a thumbnail URL,
    checking the HTTP status, and validating the image content. It eliminates
    duplicate code across providers.

    :param url: The thumbnail URL to fetch and validate.
    :param provider_name: Name of the provider (for logging).
    :param isbn: ISBN being processed (for logging).
    :param timeout: Request timeout in seconds. Defaults to 5.
    :param min_dimension: Minimum width/height in pixels for validation. Defaults to
                          RERO_INVENIO_THUMBNAILS_MIN_IMAGE_DIMENSION from app config.
    :returns: bool - True if the URL returns a valid image, False otherwise.

    Example::

        if fetch_and_validate_thumbnail("https://example.com/cover.jpg", "Provider", "9780134685991"):
            return url, "provider"
        # With custom timeout
        if fetch_and_validate_thumbnail("https://example.com/cover.jpg", "BNF", "978...", timeout=10):
            return url, "bnf"

    Note:
        Uses fetch_with_retries() for HTTP requests, so retry logic is applied.
        Validates both HTTP status code and image content (dimensions, format).
    """
    try:
        response = fetch_with_retries(url, timeout=timeout)
    except requests.RequestException:
        # Catch network-related errors only; let other exceptions propagate
        return False

    return response.status_code == requests.codes.ok and validate_image_content(
        response.content, provider_name, isbn, min_dimension=min_dimension
    )
