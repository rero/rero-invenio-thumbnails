# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Flask extension for RERO Invenio Thumbnails.

This module provides the Flask extension class that initializes the thumbnail
service, registers blueprints, and configures default settings.
"""

from . import config
from .api import PROVIDERS, get_thumbnail_url
from .views import api_thumbnails


class REROInvenioThumbnails:
    """rero-invenio-thumbnails extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.init_blueprints(app)
        app.extensions["rero-invenio-thumbnails"] = self

    def init_config(self, app):
        """Initialize configuration."""
        for key in dir(config):
            if key.startswith("RERO_INVENIO_THUMBNAILS_"):
                app.config.setdefault(key, getattr(config, key))

        # Validate that all configured providers exist in the registry
        configured_providers = app.config.get("RERO_INVENIO_THUMBNAILS_PROVIDERS", [])
        for provider_name in configured_providers:
            if provider_name not in PROVIDERS:
                app.logger.error(
                    f"Provider '{provider_name}' is configured in RERO_INVENIO_THUMBNAILS_PROVIDERS "
                    f"but does not exist in the provider registry. Available providers: {list(PROVIDERS.keys())}"
                )

    def init_blueprints(self, app):
        """Initialize and register blueprints."""
        app.register_blueprint(api_thumbnails)

    def get_thumbnail_url(self, isbn):
        """Get thumbnail URL for a given ISBN."""
        return get_thumbnail_url(isbn)
