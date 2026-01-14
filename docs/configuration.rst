..
    Copyright (C) 2026 RERO.

    rero-invenio-thumbnails is free software; you can redistribute it
    and/or modify it under the terms of the MIT License; see LICENSE file for
    more details.


Configuration
=============

.. automodule:: rero_invenio_thumbnails.config
   :members:

Retry settings
--------------

HTTP retry/backoff for external providers can be tuned via application config:

- ``RERO_INVENIO_THUMBNAILS_RETRY_ENABLED`` (default: ``True``)
- ``RERO_INVENIO_THUMBNAILS_RETRY_ATTEMPTS`` (default: ``5``)
- ``RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MULTIPLIER`` (default: ``0.5``)
- ``RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MIN`` (default: ``1``)
- ``RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MAX`` (default: ``10``)

To disable retries globally (e.g. in tests), set the environment variable::

    export RERO_THUMBNAILS_DISABLE_RETRIES=true
