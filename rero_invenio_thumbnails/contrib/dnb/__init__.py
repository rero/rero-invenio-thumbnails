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

"""DNB (Deutsche Nationalbibliothek) thumbnail provider.

Fetches cover images directly from the DNB/MVB cover service using the ISBN.

.. warning::

    Cover images are sourced from **VLB** (Verzeichnis Lieferbarer Bücher,
    operated by MVB GmbH) and are subject to copyright.  They are **not**
    freely reusable.  Use requires a valid data licence agreement with MVB.
    Contact: kundenservice@mvb-online.de

Example::

    from rero_invenio_thumbnails.contrib.dnb.api import DnbProvider
    provider = DnbProvider()
    url, name = provider.get_thumbnail_url("9783161484100")
    # url == "https://portal.dnb.de/opac/mvb/cover?isbn=9783161484100"
"""
