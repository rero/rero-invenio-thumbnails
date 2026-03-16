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

"""Base provider class for thumbnail providers.

This module defines the abstract base class that all thumbnail providers
must inherit from. It establishes a consistent interface for retrieving
thumbnail URLs across different provider implementations.

Example:
    Creating a new provider by inheriting from BaseProvider::

        from rero_invenio_thumbnails.contrib.base import BaseProvider

        class MyCustomProvider(BaseProvider):
            '''Custom provider for fetching thumbnails.'''

            def get_thumbnail_url(self, isbn):
                '''Fetch thumbnail URL for the given ISBN.

                :param isbn: The ISBN to look up
                :returns: str or None - URL of the thumbnail if found
                '''
                # Implementation here
                return f"https://example.com/covers/{isbn}.jpg"
"""

import inspect
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base class for thumbnail providers.

    All thumbnail providers must inherit from this class, define a ``name``
    class attribute, and implement the ``get_thumbnail_url`` method.

    Attributes:
        name: Unique string identifier for the provider (must be defined by subclass).
    """

    name = ""

    def __init_subclass__(cls, **kwargs):
        """Validate that subclasses define a non-empty name."""
        super().__init_subclass__(**kwargs)
        # Skip validation for abstract intermediate classes
        if not inspect.isabstract(cls) and (not cls.name or not isinstance(cls.name, str)):
            raise TypeError(
                f"Provider class {cls.__module__}.{cls.__name__} must define a non-empty 'name' attribute. "
                f"Got: {cls.name!r}"
            )

    @abstractmethod
    def get_thumbnail_url(self, isbn):
        """Retrieve thumbnail URL for the given ISBN.

        :param isbn: The ISBN (ISBN-10 or ISBN-13) to look up.
        :returns: tuple - (url, provider_name) where url is the thumbnail URL or None.
        """
        raise NotImplementedError("Subclasses must implement get_thumbnail_url method.")

    def __repr__(self):
        """Return string representation of the provider."""
        return f"<{self.__class__.__name__}>"
