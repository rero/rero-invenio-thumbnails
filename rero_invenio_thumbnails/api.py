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

    :returns: dict - Dictionary mapping provider names to provider classes.
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
        cls = ep.load()
        name = getattr(cls, "name", None)
        if not name or not isinstance(name, str):
            raise ValueError(
                f"Provider class {cls.__module__}.{cls.__name__} has invalid name: {name!r}. "
                "Provider name must be a non-empty string."
            )
        if name in providers:
            existing = providers[name]
            raise ValueError(
                f"Provider name '{name}' is already registered by {existing.__module__}.{existing.__name__}. "
                f"Cannot register duplicate from {cls.__module__}.{cls.__name__}."
            )
        providers[name] = cls

    return providers


# Lazy-load providers from entry points
PROVIDERS = _load_providers()

# Default configuration values
DEFAULT_CACHE_EXPIRE = 3600


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

    Example::

        url, provider = get_thumbnail_url("9780134685991")
        # url == "https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg"
        # provider == "open library"

        # Get without caching
        url, provider = get_thumbnail_url("9780134685991", cached=False)

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
    cache = RedisCache()

    if cached:
        # Generate cache key
        cache_key_prefix = current_app.config.get("RERO_INVENIO_THUMBNAILS_CACHE_KEY_PREFIX", "rero_thumbnails")
        cache_key = f"{cache_key_prefix}_{isbn}"

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
        try:
            provider_class = PROVIDERS[provider_name]
            provider = provider_class()
            url, returned_provider = provider.get_thumbnail_url(isbn)
        except KeyError:
            current_app.logger.warning(f"Provider '{provider_name}' not found in registry")
            continue
        except Exception as exc:
            current_app.logger.error(f"Error with provider '{provider_name}': {exc}", exc_info=True)
            continue
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
