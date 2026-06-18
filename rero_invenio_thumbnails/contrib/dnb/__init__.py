# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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
