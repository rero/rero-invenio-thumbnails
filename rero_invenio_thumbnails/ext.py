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
        for k in dir(config):
            if k.startswith("RERO_INVENIO_THUMBNAILS_"):
                app.config.setdefault(k, getattr(config, k))

    def init_blueprints(self, app):
        """Initialize and register blueprints."""
        app.register_blueprint(api_thumbnails)
