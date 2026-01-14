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

        from rero_invenio_thumbnails.modules.base import BaseProvider

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

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base class for thumbnail providers.

    All thumbnail providers must inherit from this class and implement
    the `get_thumbnail_url` method. This ensures a consistent interface
    across all providers.

    The base provider class enforces:
        - Standardized method signatures
        - Clear contract for provider implementations
        - Type hints for better IDE support
        - Consistent error handling patterns

    Attributes:
        None by default - subclasses may define their own attributes.

    Methods:
        get_thumbnail_url: Abstract method that must be implemented by subclasses.
    """

    @abstractmethod
    def get_thumbnail_url(self, isbn):
        """Retrieve thumbnail URL for the given ISBN.

        This method must be implemented by all provider subclasses. It should
        query the provider's API or service and return a tuple containing the
        URL and provider name.

        :param isbn: str - The ISBN (International Standard Book Number) to look up.
            Can be in ISBN-10 or ISBN-13 format. Providers should handle format
            conversion as needed for their specific API requirements.
        :returns: tuple - (url, provider_name) where url is the thumbnail URL or None,
            and provider_name is the string name of the provider.

        Raises:
            NotImplementedError: If the subclass doesn't implement this method.

        Examples:
            >>> provider = MyProvider()
            >>> url, provider_name = provider.get_thumbnail_url("9780134685991")
            >>> print(url, provider_name)
            https://example.com/covers/0134685997.jpg MyProvider

        Note:
            Implementations should:
                - Clean/normalize the ISBN as needed
                - Handle network errors gracefully
                - Validate responses before returning URLs
                - Log warnings for recoverable errors
                - Return (None, provider_name) for missing thumbnails (not raise exceptions)
        """
        raise NotImplementedError("Subclasses must implement get_thumbnail_url method.")

    def __repr__(self):
        """Return string representation of the provider.

        :returns: str - Class name of the provider
        """
        return f"<{self.__class__.__name__}>"
