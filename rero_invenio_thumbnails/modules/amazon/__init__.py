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

"""Amazon product images thumbnail provider module.

This module provides thumbnail retrieval functionality from Amazon's product image service.
It fetches book cover images using ISBN numbers by constructing URLs to Amazon's image servers.

The provider automatically converts ISBN-13 to ISBN-10 format as required by Amazon's API,
and supports multiple Amazon regional domains with configurable image sizes.

Key Features:
    - Automatic ISBN-13 to ISBN-10 conversion
    - Support for multiple Amazon domains (US, UK, DE, FR, JP, etc.)
    - Configurable image sizes (thumbnail to large)
    - ISBN cleaning (removes hyphens and spaces)
    - Image validation with dimension checks
    - Automatic retry with exponential backoff

Example:
    >>> from rero_invenio_thumbnails.modules.amazon.api import AmazonProvider
    >>> # Default US provider with standard size
    >>> provider = AmazonProvider()
    >>> url = provider.get_thumbnail_url('978-0-13-468599-1')
    >>> print(url)
    https://images-na.ssl-images-amazon.com/images/P/0134685997.08._SCLZZZZZZZ_.jpg
    >>>
    >>> # UK provider with medium size
    >>> provider_uk = AmazonProvider(country='01', size='MZZZZZZZZZ')
    >>> url = provider_uk.get_thumbnail_url('9780134685991')

Configuration:
    country: Amazon country code (default: '08' for US)
    size: Image size code (default: 'SCLZZZZZZZ' for standard)

API Documentation:
    - Amazon Product Advertising API
    - Image URL format: https://images-na.ssl-images-amazon.com/images/P/{ISBN10}.{COUNTRY}._{SIZE}_.jpg

Note:
    This provider requires valid ISBN numbers and may be subject to Amazon's
    rate limiting and usage policies.
"""
