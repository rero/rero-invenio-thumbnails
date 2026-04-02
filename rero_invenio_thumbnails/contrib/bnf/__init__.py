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

"""BNF (Bibliothèque nationale de France) thumbnail provider module.

Fetches cover images via the BNF openapi cover service.

Example::

    from rero_invenio_thumbnails.contrib.bnf.api import BnfProvider
    provider = BnfProvider()
    url, name = provider.get_thumbnail_url("978-2-07-036028-4")
    # url == "https://openapi.bnf.fr/couverture/image/image/recupererImage?ISBN=9782070360284&couverture=1"

API Documentation:
    https://api.bnf.fr/fr/api-service-couvertures-du-catalogue-general

Note:
    Covers documents published or distributed in France and received by
    the BnF under legal deposit since 2010.
"""
