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

"""Syndetics book cover thumbnail provider module.

This module provides thumbnail retrieval from the Syndetics cover service.
Syndetics offers direct ISBN-based cover image access without authentication
for a free tier. It returns a JPEG image when a cover exists, or an HTML
response when no cover is available (which fails image validation).

Key Features:
    - No authentication required (free public tier)
    - Direct ISBN-based URL — single HTTP request, no lookup step
    - ISBN cleaning (removes hyphens and spaces)
    - Image validation rejects the HTML fallback response
    - Automatic retry with exponential backoff
    - Good coverage of English, French, and German titles (~18% on RERO catalog)

Example::

    from rero_invenio_thumbnails.contrib.syndetics.api import SyndeticsProvider

    provider = SyndeticsProvider()
    url, name = provider.get_thumbnail_url('978-2-07-061275-8')
    # url == "https://www.syndetics.com/index.aspx?isbn=9782070612758/LC.GIF"

API Documentation:
    - Base URL: https://www.syndetics.com/index.aspx
    - Parameters: isbn={isbn}/{size}
    - Sizes: SC.GIF (small), MC.GIF (medium), LC.GIF (large, default)
    - Returns JPEG image if cover exists, HTML page otherwise

Note:
    Syndetics is a commercial service operated by ProQuest/Clarivate.
    The free unauthenticated tier provides cover images without a client key.
    Authenticated access (client= parameter) offers higher coverage and
    additional content types (summaries, TOC, etc.).
"""
