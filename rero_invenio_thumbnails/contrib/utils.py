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
from typing import Any, Callable, Optional

import requests
from flask import current_app
from PIL import Image
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from rero_invenio_thumbnails.config import MIN_IMAGE_DIMENSION

# Disable retries when running under pytest or when explicitly requested via env.
_RETRY_DISABLE_ENV = os.getenv("RERO_THUMBNAILS_DISABLE_RETRIES", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

_IN_PYTEST = False
with suppress(ImportError):
    import pytest  # noqa: F401

    _IN_PYTEST = True

_DISABLE_RETRIES = _RETRY_DISABLE_ENV or _IN_PYTEST


def clean_isbn(isbn: str) -> str:
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


def handle_provider_errors(provider_name: str) -> Callable:
    """Standardize error handling across providers.

    :param provider_name: Name of the provider for logging
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self: Any, isbn: str) -> tuple[Optional[str], str]:
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


def _get_retry_config() -> dict[str, Any]:
    """Return retry settings from Flask config or defaults."""
    attempts: int = 5
    backoff_multiplier: float = 0.5
    backoff_min: int = 1
    backoff_max: int = 10
    enabled: bool = True

    # Outside app context; stick to defaults
    with suppress(Exception):
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


def fetch_with_retries(url: str, headers: Optional[dict[str, str]] = None, timeout: int = 5) -> requests.Response:
    """Fetch URL with automatic retries on connection errors.

    This function makes HTTP GET requests with automatic retry logic for transient
    failures using exponential backoff (in production only; disabled in tests
    for performance).

    :param url: The URL to fetch.
    :param headers: Optional HTTP headers to include in the request. Defaults to None.
    :param timeout: Request timeout in seconds. Defaults to 5.
    :returns: requests.Response object
    :raises requests.RequestException: If the request fails after all retries.

    Examples:
        >>> response = fetch_with_retries("https://api.example.com/data")
        >>> response = fetch_with_retries("https://example.com/image.jpg", timeout=10)
        >>> response = fetch_with_retries(
        ...     "https://example.com/api",
        ...     headers={"User-Agent": "MyApp/1.0"}
        ... )
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

    return retrying.call(requests.get, url, headers=headers, timeout=timeout)


def validate_image_content(
    content: bytes, provider_name: str = "", isbn: str = "", min_dimension: int = MIN_IMAGE_DIMENSION
) -> bool:
    """Validate that image content is a real image with valid dimensions.

    This function checks that the provided content:
    1. Is not empty
    2. Can be opened as a valid image by PIL
    3. Has dimensions larger than the minimum threshold (to filter out placeholders)

    :param content: The image content as bytes.
    :param provider_name: Name of the provider (for logging). Defaults to "".
    :param isbn: ISBN being processed (for logging). Defaults to "".
    :param min_dimension: Minimum width/height in pixels. Defaults to MIN_IMAGE_DIMENSION.
    :returns: bool - True if the image is valid, False otherwise.

    Examples:
        >>> content = requests.get("https://example.com/cover.jpg").content
        >>> if validate_image_content(content, "BNF", "9780134685991"):
        ...     print("Valid image")
        >>> # Filter out 1x1 pixel placeholders
        >>> if validate_image_content(placeholder_data, min_dimension=10):
        ...     print("Valid image")
    """
    if not content or len(content) == 0:
        with suppress(Exception):
            current_app.logger.debug(f"Empty image data from {provider_name} for ISBN {isbn}")
        return False

    with suppress(Exception):
        img = Image.open(BytesIO(content))
        width, height = img.size
        # Check for zero dimensions or placeholder images (typically 1x1 pixels)
        if width < min_dimension or height < min_dimension:
            with suppress(Exception):
                current_app.logger.debug(
                    f"Invalid or placeholder image dimensions {width}x{height} from {provider_name} for ISBN {isbn}"
                )
            return False
        return True

    with suppress(Exception):
        current_app.logger.debug(f"Invalid image data from {provider_name} for ISBN {isbn}")
    return False


def fetch_and_validate_thumbnail(
    url: str, provider_name: str, isbn: str, timeout: int = 5, min_dimension: int = MIN_IMAGE_DIMENSION
) -> bool:
    """Fetch a thumbnail URL and validate it contains a real image.

    This helper function combines the common pattern of fetching a thumbnail URL,
    checking the HTTP status, and validating the image content. It eliminates
    duplicate code across providers.

    :param url: The thumbnail URL to fetch and validate.
    :param provider_name: Name of the provider (for logging).
    :param isbn: ISBN being processed (for logging).
    :param timeout: Request timeout in seconds. Defaults to 5.
    :param min_dimension: Minimum width/height in pixels for validation. Defaults to MIN_IMAGE_DIMENSION.
    :returns: bool - True if the URL returns a valid image, False otherwise.

    Examples:
        >>> if fetch_and_validate_thumbnail("https://example.com/cover.jpg", "Provider", "9780134685991"):
        ...     return url, "provider"
        >>> # With custom timeout
        >>> if fetch_and_validate_thumbnail("https://example.com/cover.jpg", "BNF", "978...", timeout=10):
        ...     return url, "bnf"

    Note:
        Uses fetch_with_retries() for HTTP requests, so retry logic is applied.
        Validates both HTTP status code and image content (dimensions, format).
    """
    with suppress(Exception):
        response = fetch_with_retries(url, timeout=timeout)
        if response.status_code == requests.codes.ok and validate_image_content(
            response.content, provider_name, isbn, min_dimension=min_dimension
        ):
            return True
    return False
