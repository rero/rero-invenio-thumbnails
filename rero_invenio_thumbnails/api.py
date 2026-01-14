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

"""RERO Invenio module that adds thumbnails."""

import hashlib
from io import BytesIO

from flask import current_app
from invenio_cache import current_cache
from PIL import Image

from .modules.amazon.api import AmazonProvider
from .modules.files.api import FilesProvider
from .modules.google_api.api import GoogleApiProvider
from .modules.google_books.api import GoogleBooksProvider
from .modules.open_library.api import OpenLibraryProvider
from .modules.utils import requests_retry_session

PROVIDERS = {
    "amazon": AmazonProvider,
    "google_api": GoogleApiProvider,
    "google_books": GoogleBooksProvider,
    "files": FilesProvider,
    "open_library": OpenLibraryProvider,
}


def get_thumbnail_url(isbn, cached=True):
    """Get thumbnail URL for a given ISBN from configured providers.

    This function iterates through the configured thumbnail providers and returns
    the first available thumbnail URL for the given ISBN. Results can be cached
    using invenio_cache for improved performance.

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
    """
    if cached:
        # Generate cache key
        cache_key = f"rero_thumbnails_{isbn}"

        # Try to get from cache
        if (cached_url := current_cache.get(cache_key)) is not None:
            return cached_url

    # Get cache timeout
    timeout = current_app.config.get("RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE", 3600)

    # Query providers
    for provider_name in current_app.config.get("RERO_INVENIO_THUMBNAILS_PROVIDERS", []):
        provider = PROVIDERS[provider_name]()
        if url := provider.get_thumbnail_url(isbn):
            # Cache successful result
            if cached:
                current_cache.set(cache_key, url, timeout=timeout)
            return url

    # Cache None result to avoid repeated failed lookups
    if cached:
        current_cache.set(cache_key, None, timeout=timeout)
    return None


def get_thumbnail(isbn, cached=True, width=None, height=None):
    """Get thumbnail image bytes for a given ISBN from configured providers.

    This function retrieves the actual thumbnail image (as bytes) for a given ISBN,
    with optional resizing capabilities. Results can be cached using invenio_cache
    for improved performance.

    :param isbn: The ISBN (International Standard Book Number) of the book.
        Can be ISBN-10 or ISBN-13 format.
    :param cached: Whether to use caching for this request. Defaults to True.
        When True, checks the cache before querying providers and caches the result.
        When False, bypasses cache and queries providers directly.
    :param width: Optional target width in pixels for image resizing.
        If provided alone, maintains aspect ratio.
    :param height: Optional target height in pixels for image resizing.
        If provided alone, maintains aspect ratio.
    :returns: bytes or None - The image data as bytes if found, None otherwise.

    Examples:
        >>> # Get original image
        >>> img_bytes = get_thumbnail("9780134685991")
        >>> with open("cover.jpg", "wb") as f:
        ...     f.write(img_bytes)

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
    """
    # Generate dimension-aware cache key
    cache_key_base = f"{isbn}_{width or 0}x{height or 0}" if width or height else isbn
    key_hash = hashlib.md5(cache_key_base.encode()).hexdigest()
    cache_key = f"rero_thumbnail_img_{key_hash}"

    # Try to get from cache if caching is enabled
    if cached and (cached_data := current_cache.get(cache_key)) is not None:
        return cached_data

    # Get cache timeout
    timeout = current_app.config.get("RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE", 3600)

    # Try to get local file first (FilesProvider specific optimization)
    for provider_name in current_app.config.get("RERO_INVENIO_THUMBNAILS_PROVIDERS", []):
        if provider_name == "files":
            provider = PROVIDERS[provider_name]()
            if hasattr(provider, "get_thumbnail_path") and (thumbnail_path := provider.get_thumbnail_path(isbn)):
                try:
                    with open(thumbnail_path, "rb") as f:
                        if width or height:
                            # Resize local image
                            img = Image.open(f)
                            img_format = img.format or "JPEG"
                            img = _resize_image(img, width, height)
                            img_bytes = BytesIO()
                            img.save(img_bytes, format=img_format)
                            img_bytes.seek(0)
                            img_data = img_bytes.getvalue()
                        else:
                            # Return original local image
                            img_data = f.read()

                        # Cache the result
                        if cached:
                            current_cache.set(cache_key, img_data, timeout=timeout)
                        return img_data
                except Exception as e:
                    current_app.logger.warning(f"Failed to read local thumbnail {thumbnail_path}: {e}")
                    break

    # Get URL from any provider using existing function
    if url := get_thumbnail_url(isbn, cached=cached):
        try:
            resp = requests_retry_session().get(url, timeout=10)
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
                    current_cache.set(cache_key, img_data, timeout=timeout)
                return img_data
        except Exception as e:
            current_app.logger.warning(f"Failed to fetch image from {url}: {e}")

    # Cache None result to avoid repeated failed lookups
    if cached:
        current_cache.set(cache_key, None, timeout=timeout)
    return None


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
        new_size = (width, int(orig_height * (width / orig_width)))
    else:  # height only
        new_size = (int(orig_width * (height / orig_height)), height)

    return img.resize(new_size, Image.Resampling.LANCZOS)
