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

"""BNF (Bibliothèque nationale de France) thumbnail provider module.

This module provides thumbnail retrieval functionality for the French National Library.
It interfaces with the BNF catalogue API to fetch book cover images using ARK identifiers.

The provider implements a two-step process:
1. Convert ISBN to ARK identifier via the BNF SRU (Search/Retrieve via URL) API
2. Retrieve the cover image using the ARK identifier

Key Features:
    - Automatic ISBN to ARK conversion
    - Support for ISBN-10 and ISBN-13 formats
    - Configurable cover page (front/back)
    - Custom application name support
    - ISBN cleaning (removes hyphens and spaces)
    - Image validation (dimensions and content type)

Example:
    >>> from rero_invenio_thumbnails.modules.bnf.api import BnfProvider
    >>> provider = BnfProvider()
    >>> url = provider.get_thumbnail_url("978-2-07-036028-4")
    >>> print(url)
    http://catalogue.bnf.fr/couverture?appName=NE&idArk=ark:/12148/cb450989938&couverture=1

API Documentation:
    - SRU API: https://catalogue.bnf.fr/api/SRU
    - Cover API: http://catalogue.bnf.fr/couverture
    - BNF Hackathon Documentation: https://github.com/hackathonBnF/hackathon2016/wiki/API-Couverture-Service

Note:
    This provider is specifically designed for documents published or distributed in France
    and received by the BnF under legal deposit (since 2010).
"""
