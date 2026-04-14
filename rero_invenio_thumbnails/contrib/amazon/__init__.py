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

"""Amazon thumbnail provider module.

Fetches cover images from Amazon's image CDN using the book's ASIN,
which for books is equivalent to its ISBN-10.

Example::

    from rero_invenio_thumbnails.contrib.amazon.api import AmazonProvider
    provider = AmazonProvider()
    url, name = provider.get_thumbnail_url("978-2-07-061275-8")
    # url == "https://images-na.ssl-images-amazon.com/images/P/2070612759.01.LZZZZZZZ.jpg"

Note:
    ISBN-13 values with a 979 prefix have no ISBN-10 equivalent (no ASIN)
    and cannot be looked up via this provider.
"""
