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

"""Flask extension for RERO Invenio Thumbnails.

This module provides the Flask extension class that initializes the thumbnail
service, registers blueprints, and configures default settings.
"""

from . import config
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
        from .api import PROVIDERS

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
        from .api import get_thumbnail_url

        return get_thumbnail_url(isbn)
