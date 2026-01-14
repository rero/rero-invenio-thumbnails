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

"""DNB (Deutsche Nationalbibliothek) thumbnail provider.

This module provides thumbnail URL discovery for book covers from the German
National Library (Deutsche Nationalbibliothek). The provider queries the DNB's
SRU (Search/Retrieve via URL) interface to retrieve bibliographic metadata in
MARC21-XML format, then extracts cover image URLs from the records.

Key Features:
    - ISBN-based search via DNB SRU interface
    - MARC21-XML metadata parsing
    - Cover URL extraction from field 856 (Electronic Location and Access)
    - Keyword-based URL identification (cover, thumbnail, bild, umschlag)
    - Fallback URL construction from ISBN
    - Automatic retry logic with exponential backoff

The DNB maintains bibliographic records for publications received through German
legal deposit and provides access to cover images when available from publishers.

Examples:
    Basic usage::

        from rero_invenio_thumbnails.modules.dnb.api import DnbProvider

        provider = DnbProvider()
        url = provider.get_thumbnail_url("9783161484100")

    The provider returns URLs in formats like::

        https://portal.dnb.de/opac/mvb/cover?isbn=9783161484100

API Documentation:
    See :class:`~rero_invenio_thumbnails.modules.dnb.api.DnbProvider` for
    detailed API documentation.

Note:
    Cover image availability depends on whether publishers have provided
    cover metadata to the DNB. Not all publications have cover images.
"""
