# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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
