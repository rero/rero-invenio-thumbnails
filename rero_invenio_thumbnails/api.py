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
    - Plugin-based architecture via entry points
    - Redis caching via invenio_cache
    - Image validation (minimum 10x10 pixels)
    - Dynamic image resizing
    - Configurable retry logic for HTTP requests

Provider Discovery:
    Providers are automatically discovered via the
    'rero_invenio_thumbnails.providers' entry point group. Custom providers
    can be registered by adding entry points in setup.py or pyproject.toml.

    Example entry point registration in pyproject.toml::

        [project.entry-points."rero_invenio_thumbnails.providers"]
        custom = "my_module.providers:CustomProvider"
"""

import json
from contextlib import suppress
from importlib.metadata import entry_points

from flask import current_app
from invenio_cache import current_cache


def _load_providers():
    """Load thumbnail providers from entry points.

    :returns: dict - Dictionary mapping provider names to provider classes
    """
    providers = {}
    eps = entry_points()

    # Handle both old (dict) and new (SelectableGroups) API
    provider_eps = (
        eps.get("rero_invenio_thumbnails.providers", [])
        if hasattr(eps, "get")
        else eps.select(group="rero_invenio_thumbnails.providers")
    )

    for ep in provider_eps:
        providers[ep.name] = ep.load()

    return providers


# Lazy-load providers from entry points
PROVIDERS = _load_providers()

# Default configuration values
DEFAULT_CACHE_EXPIRE = 3600


class CacheBackend:
    """Cache backend using Redis via invenio_cache."""

    @staticmethod
    def get_backend():
        """Get the Redis cache backend."""
        return RedisCache()


class RedisCache:
    """Redis-based cache backend using invenio_cache."""

    def get(self, key):
        """Retrieve value from Redis cache."""
        return current_cache.get(key)

    def set(self, key, value, timeout):
        """Store value in Redis cache with expiration."""
        current_cache.set(key, value, timeout=timeout)


def get_thumbnail_url(isbn, cached=True):
    """Get thumbnail URL for a given ISBN from configured providers.

    This function iterates through the configured thumbnail providers and returns
    a tuple containing the thumbnail URL and provider name. Results are cached
    using Redis via invenio_cache.

    :param isbn: The ISBN (International Standard Book Number) of the book.
        Can be ISBN-10 or ISBN-13 format.
    :param cached: Whether to use caching for this request. Defaults to True.
        When True, checks the cache before querying providers and caches the result.
        When False, bypasses cache and queries providers directly.
    :returns: tuple - (url, provider_name) where url is the thumbnail URL or None,
        and provider_name is the string name of the provider that provided the result.

    Examples:
        >>> url, provider = get_thumbnail_url("9780134685991")
        >>> print(url, provider)
        https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg open library

        >>> # Get without caching
        >>> url, provider = get_thumbnail_url("9780134685991", cached=False)

    Note:
        The function relies on the "RERO_INVENIO_THUMBNAILS_PROVIDERS" config
        to determine which providers to query in order. If not configured,
        all providers discovered via entry points will be used.
        Results are cached based on the "RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE"
        configuration using Redis via invenio_cache.

        Providers are loaded from the 'rero_invenio_thumbnails.providers'
        entry point group. Custom providers can be registered by adding
        entry points in your package configuration.
    """
    cache = CacheBackend.get_backend()

    if cached:
        # Generate cache key
        cache_key = f"rero_thumbnails_{isbn}"

        # Try to get from cache
        if (cached_result := cache.get(cache_key)) is not None:
            # Cached result is JSON: {"url": "...", "provider": "..."}
            with suppress(json.JSONDecodeError, AttributeError, TypeError):
                data = json.loads(cached_result)
                url = data.get("url")
                provider = data.get("provider")
                return url, provider

    # Get cache timeout
    timeout = current_app.config.get("RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE", DEFAULT_CACHE_EXPIRE)

    # Query providers
    providers = current_app.config.get("RERO_INVENIO_THUMBNAILS_PROVIDERS", list(PROVIDERS.keys()))
    for provider_name in providers:
        provider = PROVIDERS[provider_name]()
        url, returned_provider = provider.get_thumbnail_url(isbn)
        if url:
            # Cache successful result
            if cached:
                cache_data = json.dumps({"url": url, "provider": returned_provider})
                cache.set(cache_key, cache_data, timeout=timeout)
            return url, returned_provider

    # Cache None result to avoid repeated failed lookups
    # Use last provider name or None
    last_provider = providers[-1] if providers else None
    if cached:
        cache_data = json.dumps({"url": None, "provider": last_provider})
        cache.set(cache_key, cache_data, timeout=timeout)
    return None, last_provider


def get_base_urls():
    """Get base URLs for all configured thumbnail providers.

    Returns a dictionary mapping base URLs to their provider names.
    For providers that don't have a static base_url (e.g., FilesProvider),
    the function will instantiate them to retrieve the configured URL.

    :returns: dict - Dictionary mapping base URLs to provider names

    Examples:
        >>> base_urls = get_base_urls()
        >>> print(base_urls)
        {
            'http://catalogue.bnf.fr/couverture': 'bnf',
            'https://services.dnb.de/sru/dnb': 'dnb',
            'http://localhost': 'files',
            'https://www.googleapis.com/books/v1/volumes': 'google api',
            'https://books.google.com/books': 'google books',
            'https://covers.openlibrary.org': 'open library'
        }
    """
    base_urls = {}
    # Get configured providers (same as in get_thumbnail_url)
    providers = current_app.config.get("RERO_INVENIO_THUMBNAILS_PROVIDERS", list(PROVIDERS.keys()))
    for provider_name in providers:
        with suppress(Exception):
            provider = PROVIDERS[provider_name]()
            base_urls[provider.base_url] = provider_name
    return base_urls
