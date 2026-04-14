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

"""Utility functions for thumbnail fetching and validation.

This module provides shared utilities used by all thumbnail providers:
    - Image content validation (format, dimensions, quality checks)
"""

from functools import wraps
from io import BytesIO

import requests
from flask import current_app
from invenio_cache import current_cache
from PIL import Image


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


def validate_image_content(content, provider_name="", isbn=""):
    """Validate that image content is a real image with valid dimensions.

    This function checks that the provided content:
    1. Is not empty
    2. Can be opened as a valid image by PIL
    3. Has dimensions at or above ``RERO_INVENIO_THUMBNAILS_MIN_IMAGE_DIMENSION``

    :param content: The image content as bytes.
    :param provider_name: Name of the provider (for logging). Defaults to "".
    :param isbn: ISBN being processed (for logging). Defaults to "".
    :returns: bool - True if the image is valid, False otherwise.

    Example::

        content = requests.get("https://example.com/cover.jpg").content
        if validate_image_content(content, "BNF", "9780134685991"):
            print("Valid image")
    """
    # current_app.config raises RuntimeError when called outside a Flask
    # application context (e.g. from CLI scripts or external providers).
    # Fall back to the same default used in the config key.
    try:
        min_dimension = current_app.config.get("RERO_INVENIO_THUMBNAILS_MIN_IMAGE_DIMENSION", 50)
    except RuntimeError:
        min_dimension = 50
    if not content:
        current_app.logger.debug(f"Empty image data from {provider_name} for ISBN {isbn}")
        return False

    try:
        img = Image.open(BytesIO(content))
        width, height = img.size
        return width >= min_dimension and height >= min_dimension
    except (Image.UnidentifiedImageError, OSError) as e:
        current_app.logger.debug(f"Invalid image data from {provider_name} for ISBN {isbn}: {e}")
        return False
    except MemoryError as e:
        current_app.logger.debug(f"Memory error processing image from {provider_name} for ISBN {isbn}: {e}")
        return False


def fetch_and_validate_thumbnail(url, provider_name, isbn, timeout=None, headers=None):
    """Fetch a thumbnail URL and validate it contains a real image.

    This helper function combines the common pattern of fetching a thumbnail URL,
    checking the HTTP status, and validating the image content. It eliminates
    duplicate code across providers.

    :param url: The thumbnail URL to fetch and validate.
    :param provider_name: Name of the provider (for logging).
    :param isbn: ISBN being processed (for logging).
    :param timeout: Request timeout as ``(connect, read)`` in seconds. Defaults to
        ``RERO_INVENIO_THUMBNAILS_HTTP_TIMEOUT`` from config (``(2, 10)`` if unset).
    :param headers: Optional HTTP headers to include in the request. Defaults to None.
    :returns: bool - True if the URL returns a valid image, False otherwise.

    Example::

        if fetch_and_validate_thumbnail("https://example.com/cover.jpg", "Provider", "9780134685991"):
            return url, "provider"
        # With custom timeout
        if fetch_and_validate_thumbnail("https://example.com/cover.jpg", "BNF", "978...", timeout=(3, 10)):
            return url, "bnf"

    Note:
        Validates both HTTP status code and image content (dimensions, format).
    """
    if timeout is None:
        timeout = current_app.config.get("RERO_INVENIO_THUMBNAILS_HTTP_TIMEOUT", (2, 10))
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as e:
        current_app.logger.debug(f"Request error fetching thumbnail from {provider_name} for ISBN {isbn}: {e}")
        return False

    if response.status_code != requests.codes.ok:
        current_app.logger.debug(
            f"HTTP {response.status_code} fetching thumbnail from {provider_name} for ISBN {isbn}: {url}"
        )
        return False
    return validate_image_content(response.content, provider_name, isbn)


def clean_all_cache():
    """Delete all thumbnail cache entries from the cache backend.

    Scans for keys matching the configured thumbnail cache prefix
    and removes them in batches.

    :returns: int - Number of cache entries deleted.
    """
    prefix = current_app.config.get("RERO_INVENIO_THUMBNAILS_CACHE_KEY_PREFIX", "rero_thumbnails")
    cache = current_cache.cache
    # flask-caching delegates to cachelib; for Redis backends cachelib stores
    # the client in _write_client (and _client for read replicas). Both point
    # to the same object on a standard single-node Redis setup.
    client = getattr(cache, "_write_client", None) or getattr(cache, "_client", None)
    if client is None:
        current_app.logger.warning(
            "clean_all_cache: cannot access Redis client (cache backend has no _write_client/_client). "
            "Pattern-based deletion skipped."
        )
        return 0
    key_prefix = getattr(cache, "key_prefix", "")
    pattern = f"{key_prefix}{prefix}_*"
    deleted = 0
    batch = []
    for key in client.scan_iter(pattern, count=1000):
        batch.append(key)
        if len(batch) >= 1000:
            deleted += client.delete(*batch)
            batch = []
    if batch:
        deleted += client.delete(*batch)
    return deleted
