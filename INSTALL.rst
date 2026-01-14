Installation
============

This package provides a lightweight Invenio extension to retrieve and serve
book thumbnails from multiple providers (local files, Open Library, Google
Books, Amazon).

Prerequisites
-------------

- Python 3.9+
- Redis (optional, for caching) if you want to enable `invenio_cache`

Quick install
-------------

Install from PyPI::

   $ pip install rero-invenio-thumbnails

Or install in editable mode for development::

   $ pip install -e .

Configuration
-------------

Add the extension and configure the available providers and files directory
in your Flask/Invenio configuration::

   RERO_INVENIO_THUMBNAILS_PROVIDERS = [
      "files",
      "open_library",
      "google_books",
      "google_api",
      "amazon",
   ]

   # Directory used by FilesProvider
   RERO_INVENIO_THUMBNAILS_FILES_DIR = "/path/to/thumbnails"
   RERO_INVENIO_THUMBNAILS_CACHE_EXPIRE = 3600
   # Retry configuration (defaults shown)
   RERO_INVENIO_THUMBNAILS_RETRY_ENABLED = True
   RERO_INVENIO_THUMBNAILS_RETRY_ATTEMPTS = 5
   RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MULTIPLIER = 0.5
   RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MIN = 1
   RERO_INVENIO_THUMBNAILS_RETRY_BACKOFF_MAX = 10

You can also disable retries globally (useful in tests) via environment variable::

   export RERO_THUMBNAILS_DISABLE_RETRIES=true

Application integration
-----------------------

In your application factory or initialization code, register the extension
and its blueprint::

   from rero_invenio_thumbnails import REROInvenioThumbnails

   ext = REROInvenioThumbnails()
   ext.init_app(app)

Testing
-------

Run the test-suite using pytest::

   $ pip install -r requirements.txt
   $ pytest
