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

"""Wikidata book cover thumbnail provider module.

This module provides thumbnail retrieval from Wikidata / Wikimedia Commons.
It queries the Wikidata SPARQL endpoint to resolve an ISBN to a cover image
stored in Wikimedia Commons (property P18), then uses the Commons imageinfo
API to obtain a rendered JPEG thumbnail URL at a configurable width.

The lookup traverses the Wikidata book data model in three steps:
    1. Edition item (P212 ISBN-13 or P957 ISBN-10) → P18 image on edition
    2. Edition item → P629 (edition of) → work item → P18 image on work
    3. Work item → P747 (has edition) → edition item (P212) + P18 on work

Key Features:
    - No authentication required (public Wikidata and Commons APIs)
    - Handles ISBN-13 stored with hyphens in Wikidata
    - Falls back from edition to parent work for cover images
    - Uses Commons imageinfo API to get rendered JPEG for any source format
    - Configurable thumbnail width (default: 300px)
    - Automatic retry with exponential backoff

Example::

    from rero_invenio_thumbnails.contrib.wikidata.api import WikidataProvider

    provider = WikidataProvider()
    url, name = provider.get_thumbnail_url('978-2-9576887-0-8')
    # url == "https://upload.wikimedia.org/wikipedia/commons/thumb/..."

API Documentation:
    - Wikidata SPARQL: https://query.wikidata.org/
    - Commons imageinfo API: https://commons.wikimedia.org/w/api.php
    - P18 (image): https://www.wikidata.org/wiki/Property:P18
    - P212 (ISBN-13): https://www.wikidata.org/wiki/Property:P212
    - P957 (ISBN-10): https://www.wikidata.org/wiki/Property:P957
    - P629 (edition of): https://www.wikidata.org/wiki/Property:P629
    - P747 (has edition): https://www.wikidata.org/wiki/Property:P747

License:
    Wikidata structured data is CC0 (public domain).
    Wikimedia Commons images are under various free licenses (CC-BY, CC-BY-SA,
    public domain, etc.) — check individual file licensing before reuse.

Rate Limits:
    Wikidata SPARQL: 60 seconds of query time per minute.
    Commons API: no strict rate limit for reasonable usage.
"""
