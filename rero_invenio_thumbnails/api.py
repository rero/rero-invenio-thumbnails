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

"""Core API for retrieving and serving book thumbnail images.

This module provides the main interface for fetching thumbnails from multiple
providers with built-in caching, validation, and image resizing capabilities.

Key features:
    - Multi-provider support with fallback chain
    - Redis and filesystem caching
    - Image validation (minimum 10x10 pixels)
    - Dynamic image resizing
    - Configurable retry logic for HTTP requests
"""

import hashlib
import time
from io import BytesIO
from pathlib import Path

from flask import current_app
from invenio_cache import current_cache
from PIL import Image

from .modules.amazon.api import AmazonProvider
from .modules.bnf.api import BnfProvider
from .modules.files.api import FilesProvider
from .modules.google_api.api import GoogleApiProvider
from .modules.google_books.api import GoogleBooksProvider
from .modules.open_library.api import OpenLibraryProvider
from .modules.utils import fetch_with_retries


def _generate_cache_key(isbn, prefix, width=None, height=None):
    """Generate dimension-aware cache key for thumbnails.

    :param isbn: Book ISBN
    :param prefix: Cache key prefix (e.g., 'img' or 'url')
    :param width: Optional width for dimension-aware caching
    :param height: Optional height for dimension-aware caching
    :returns: str - MD5-hashed cache key
    """
    cache_key_base = f"{isbn}_{width or 0}x{height or 0}" if width or height else isbn
    key_hash = hashlib.md5(cache_key_base.encode()).hexdigest()
    return f"rero_thumbnail_{prefix}_{key_hash}"


PROVIDERS = {
    "files": FilesProvider,
    "open library": OpenLibraryProvider,
    "bnf": BnfProvider,
    "google books": GoogleBooksProvider,
    "google api": GoogleApiProvider,
    "amazon": AmazonProvider,
}

# Default configuration values
DEFAULT_PROVIDERS = ["files", "open library", "bnf", "google books", "google api", "amazon"]
DEFAULT_CACHE_TYPE = "redis"
DEFAULT_CACHE_DIR = "./cache/thumbnails"
DEFAULT_CACHE_EXPIRE = 3600
DEFAULT_HTTP_CACHE_MAX_AGE = 86400


class CacheBackend:
    """Abstract cache backend supporting Redis and filesystem storage."""

    @staticmethod
    def get_backend():
        """Get the configured cache backend."""
        cache_type = current_app.config.get("RERO_INVENIO_THUMBNAILS_CACHE_TYPE", DEFAULT_CACHE_TYPE)
        if cache_type == "filesystem":
            return FilesystemCache()
        return RedisCache()


class RedisCache:
    """Redis-based cache backend using invenio_cache."""

    def get(self, key):
        """Retrieve value from Redis cache."""
        return current_cache.get(key)

    def set(self, key, value, timeout):
        """Store value in Redis cache with expiration."""
        current_cache.set(key, value, timeout=timeout)


class FilesystemCache:
    """Filesystem-based cache backend for persistent storage."""

    def __init__(self):
        """Initialize filesystem cache with configured directory."""
        self.cache_dir = Path(current_app.config.get("RERO_INVENIO_THUMBNAILS_CACHE_DIR", DEFAULT_CACHE_DIR))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key):
        """Get cache file path for a given key."""
        return self.cache_dir / f"{key}.cache"

    def get(self, key):
        """Retrieve value from filesystem cache."""
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            # Read cache file
            with open(cache_path, "rb") as file:
                # First 8 bytes: expiration timestamp
                expiration_bytes = file.read(8)
                if len(expiration_bytes) < 8:
                    return None

                expiration = int.from_bytes(expiration_bytes, "big")

                # Check if expired
                if expiration > 0 and time.time() > expiration:
                    cache_path.unlink(missing_ok=True)
                    return None

                # Read cached data
                return file.read()
        except Exception as err:
            current_app.logger.warning(f"Error reading cache file {cache_path}: {err}")
            return None

    def set(self, key, value, timeout):
        """Store value in filesystem cache with expiration."""
        cache_path = self._get_cache_path(key)
        try:
            # Calculate expiration timestamp
            expiration = int(time.time() + timeout) if timeout > 0 else 0

            # Write cache file
            with open(cache_path, "wb") as file:
                # Write expiration timestamp (8 bytes)
                file.write(expiration.to_bytes(8, "big"))
                # Write data
                if value is not None:
                    file.write(value if isinstance(value, bytes) else str(value).encode())
        except Exception as err:
            current_app.logger.warning(f"Error writing cache file {cache_path}: {err}")


def get_thumbnail_url(isbn, cached=True):
    """Get thumbnail URL for a given ISBN from configured providers.

    This function iterates through the configured thumbnail providers and returns
    the first available thumbnail URL for the given ISBN. Results can be cached
    using either Redis (fast, in-memory) or filesystem (persistent, cost-effective).

    :param isbn: The ISBN (International Standard Book Number) of the book.
        Can be ISBN-10 or ISBN-13 format.
    :param cached: Whether to use caching for this request. Defaults to True.
        When True, checks the cache before querying providers and caches the result.
        When False, bypasses cache and queries providers directly.
    :returns: str or None - The URL of the thumbnail image if found, None otherwise.

    Examples:
        >>> url = get_thumbnail_url("9780134685991")
        >>> print(url)
        https://images-na.ssl-images-amazon.com/images/P/0134685997...

        >>> # Get without caching
        >>> url = get_thumbnail_url("9780134685991", cached=False)

    Note:
        The function relies on the "RERO_INVENIO_THUMBNAILS_PROVIDERS" config
        to determine which providers to query in order. Results are cached
        based on the "RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE" configuration.
        Cache backend (Redis or filesystem) is determined by
        "RERO_INVENIO_THUMBNAILS_CACHE_TYPE" configuration.
    """
    cache = CacheBackend.get_backend()

    if cached:
        # Generate cache key
        cache_key = f"rero_thumbnails_{isbn}"

        # Try to get from cache
        if (cached_url := cache.get(cache_key)) is not None:
            # Decode if bytes (filesystem cache returns bytes)
            if isinstance(cached_url, bytes):
                cached_url = cached_url.decode("utf-8")
            return cached_url if cached_url != "None" else None

    # Get cache timeout
    timeout = current_app.config.get("RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE", DEFAULT_CACHE_EXPIRE)

    # Query providers
    providers = current_app.config.get("RERO_INVENIO_THUMBNAILS_PROVIDERS", DEFAULT_PROVIDERS)
    for provider_name in providers:
        provider = PROVIDERS[provider_name]()
        if url := provider.get_thumbnail_url(isbn):
            # Cache successful result
            if cached:
                cache.set(cache_key, url.encode("utf-8") if isinstance(url, str) else url, timeout=timeout)
            return url

    # Cache None result to avoid repeated failed lookups
    if cached:
        cache.set(cache_key, b"None", timeout=timeout)
    return None


def get_thumbnail(isbn, cached=True, width=None, height=None):
    """Get thumbnail image bytes for a given ISBN from configured providers.

    This function retrieves the actual thumbnail image (as bytes) for a given ISBN,
    with optional resizing capabilities. Results can be cached using either Redis
    (fast, in-memory) or filesystem (persistent, cost-effective).

    :param isbn: The ISBN (International Standard Book Number) of the book.
        Can be ISBN-10 or ISBN-13 format.
    :param cached: Whether to use caching for this request. Defaults to True.
        When True, checks the cache before querying providers and caches the result.
        When False, bypasses cache and queries providers directly.
    :param width: Optional target width in pixels for image resizing.
        If provided alone, maintains aspect ratio.
    :param height: Optional target height in pixels for image resizing.
        If provided alone, maintains aspect ratio.
    :returns: tuple or None - A tuple of (bytes, str) containing the image data
        and provider name if found, None otherwise.

    Examples:
        >>> # Get original image
        >>> img_bytes = get_thumbnail("9780134685991")
        >>> with open("cover.jpg", "wb") as file:
        ...     file.write(img_bytes)

        >>> # Get resized image (200px width, maintaining aspect ratio)
        >>> img_bytes = get_thumbnail("9780134685991", width=200)

        >>> # Get image with specific dimensions
        >>> img_bytes = get_thumbnail("9780134685991", width=200, height=300)

        >>> # Get without caching
        >>> img_bytes = get_thumbnail("9780134685991", cached=False)

    .. note::
        When both width and height are provided, image is resized to exact dimensions.
        When only one dimension is provided, aspect ratio is maintained.
        Dimension-aware caching ensures different sizes are cached separately.
        Cache backend (Redis or filesystem) is determined by
        "RERO_INVENIO_THUMBNAILS_CACHE_TYPE" configuration.
    """
    cache = CacheBackend.get_backend()

    # Generate dimension-aware cache key
    cache_key = _generate_cache_key(isbn, "img", width, height)

    # Try to get from cache if caching is enabled
    if cached and (cached_data := cache.get(cache_key)) is not None:
        # Handle None marker (cached negative result)
        if cached_data == b"None":
            return None, None
        # Cache doesn't store provider info, so return "cache" as provider
        return cached_data, "cache"

    # Get cache timeout
    timeout = current_app.config.get("RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE", DEFAULT_CACHE_EXPIRE)

    # Try to get local file first (FilesProvider specific optimization)
    providers = current_app.config.get("RERO_INVENIO_THUMBNAILS_PROVIDERS", DEFAULT_PROVIDERS)
    for provider_name in providers:
        if provider_name == "files":
            provider = PROVIDERS[provider_name]()
            if hasattr(provider, "get_thumbnail_path") and (thumbnail_path := provider.get_thumbnail_path(isbn)):
                try:
                    with open(thumbnail_path, "rb") as file:
                        if width or height:
                            # Resize local image
                            img = Image.open(file)
                            img_format = img.format or "JPEG"
                            img = _resize_image(img, width, height)
                            img_bytes = BytesIO()
                            img.save(img_bytes, format=img_format)
                            img_bytes.seek(0)
                            img_data = img_bytes.getvalue()
                        else:
                            # Return original local image
                            img_data = file.read()

                        # Cache the result
                        if cached:
                            cache.set(cache_key, img_data, timeout=timeout)
                        return img_data, "files"
                except Exception as err:
                    current_app.logger.warning(f"Failed to read local thumbnail {thumbnail_path}: {err}")
                    break

    # Get URL from any provider using existing function
    if url := get_thumbnail_url(isbn, cached=cached):
        # Detect provider from URL
        provider_name = "unknown"
        if "openlibrary.org" in url:
            provider_name = "open_library"
        elif "amazon" in url:
            provider_name = "amazon"
        elif "bnf.fr" in url:
            provider_name = "bnf"
        elif "google" in url:
            provider_name = "google_books" if "books.google.com" in url else "google_api"

        try:
            resp = fetch_with_retries(url, timeout=10)
            if resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("image/"):
                if width or height:
                    # Resize fetched image
                    img = Image.open(BytesIO(resp.content))
                    img_format = img.format or "JPEG"
                    img = _resize_image(img, width, height)
                    resized_bytes = BytesIO()
                    img.save(resized_bytes, format=img_format)
                    resized_bytes.seek(0)
                    img_data = resized_bytes.getvalue()
                else:
                    # Return original fetched image
                    img_data = resp.content

                # Cache the result
                if cached:
                    cache.set(cache_key, img_data, timeout=timeout)
                return img_data, provider_name
        except Exception as err:
            current_app.logger.warning(f"Failed to fetch image from {url}: {err}")

    # Cache None result to avoid repeated failed lookups
    if cached:
        cache.set(cache_key, b"None", timeout=timeout)
    return None, None


def _resize_image(img, width, height):
    """Resize an image proportionally based on provided dimensions.

    :param img: PIL Image object to resize
    :param width: Target width in pixels (optional)
    :param height: Target height in pixels (optional)
    :returns: PIL Image object resized to target dimensions

    .. note::
        If both dimensions provided, image is resized to exact size.
        If only one dimension provided, maintains aspect ratio.
    """
    # If neither is set, return original
    if not width and not height:
        return img

    orig_width, orig_height = img.size

    # Validate original dimensions to prevent division by zero
    if orig_width == 0 or orig_height == 0:
        current_app.logger.warning(f"Invalid image dimensions: {orig_width}x{orig_height}")
        return img

    if width and height:
        new_size = (width, height)
    elif width:
        new_size = (width, int(width * orig_height / orig_width))
    else:  # height only
        new_size = (int(height * orig_width / orig_height), height)

    return img.resize(new_size, Image.Resampling.LANCZOS)
