# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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
