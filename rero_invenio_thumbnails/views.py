#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Flask blueprint for serving book thumbnail URLs."""

import hashlib
import os
from contextlib import suppress
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, make_response, request, send_file

from rero_invenio_thumbnails.api import get_thumbnail_url
from rero_invenio_thumbnails.config import RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE
from rero_invenio_thumbnails.modules.files.api import FilesProvider

api_thumbnails = Blueprint("api_thumbnails", __name__, url_prefix="/")


def add_cache_headers(response):
    """Add HTTP cache control headers to response.

    :param response: Flask response object
    :returns: Modified response with cache headers
    """
    max_age = current_app.config.get(
        "RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE", RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE
    )
    if max_age > 0:
        response.headers["Cache-Control"] = f"public, max-age={max_age}"
        response.headers["Vary"] = "Accept-Encoding"
    else:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@api_thumbnails.route("/thumbnails-url/<isbn>", methods=["GET"])
def get_thumbnail_url_endpoint(isbn):
    """Retrieve thumbnail URL for a given ISBN as JSON.

    Returns JSON containing the external URL where the thumbnail can be found,
    without fetching or serving the actual image data.

    :param isbn: ISBN identifier (ISBN-10 or ISBN-13)

    Query parameters:
        - cached (str): Set to 'false' to bypass cache (default: 'true')

    :returns: JSON response with URL and ISBN or error details
    :rtype: tuple[flask.Response, int]

    Success response (200)::

        {
            "url": "https://covers.openlibrary.org/b/isbn/9780134685991-L.jpg",
            "isbn": "9780134685991",
            "provider": "open library"
        }

    Error response (404)::

        {
            "error": "Thumbnail not found",
            "isbn": "9780134685991",
            "message": "No thumbnail available for ISBN 9780134685991"
        }

    Example:
        GET /thumbnails-url/9780134685991

        Returns JSON with the external thumbnail URL
    """
    cached = request.args.get("cached", default="true").lower() != "false"
    try:
        # Get thumbnail URL using all configured providers
        url, provider = get_thumbnail_url(isbn, cached=cached)

        if not url:
            current_app.logger.debug(f"Thumbnail URL not found for ISBN: {isbn}")
            return jsonify(
                {"error": "Thumbnail not found", "isbn": isbn, "message": f"No thumbnail available for ISBN {isbn}"}
            ), 404

        # Return thumbnail URL in JSON format
        current_app.logger.debug(f"Found thumbnail URL for ISBN {isbn}: {url} from provider: {provider}")
        response = jsonify({"url": url, "isbn": isbn, "provider": provider})
        return add_cache_headers(response), 200

    except Exception as err:
        current_app.logger.error(f"Error retrieving thumbnail URL for ISBN {isbn}: {err!s}")
        return jsonify(
            {"error": "Server error", "isbn": isbn, "message": "An error occurred while retrieving the thumbnail URL"}
        ), 500


@api_thumbnails.route("/thumbnails/<isbn>", methods=["GET"])
def serve_thumbnail(isbn):
    """Serve the actual thumbnail image file for a given ISBN.

    This endpoint retrieves and serves the thumbnail image directly from
    local file storage. Returns the image file with appropriate MIME type
    and cache headers. Supports client-side caching via ETag and Last-Modified
    headers with conditional request handling (If-None-Match, If-Modified-Since).

    :param isbn: ISBN identifier (ISBN-10 or ISBN-13)

    :returns: Image file response or error
    :rtype: flask.Response

    Success response (200):
        Binary image data (JPEG or PNG) with appropriate Content-Type header,
        ETag, and Last-Modified headers for client-side caching

    Not Modified response (304):
        Returned when client's cached version is still valid (via ETag or Last-Modified)

    Error response (404)::

        {
            "error": "Thumbnail not found",
            "isbn": "9780134685991",
            "message": "No thumbnail file available for ISBN 9780134685991"
        }

    Example:
        GET /thumbnails/9780134685991

        Returns the actual image file with ETag and Last-Modified headers
    """
    try:
        # Use FilesProvider to get the thumbnail path
        files_provider = FilesProvider()
        thumbnail_path = files_provider.get_thumbnail_path(isbn)

        if not thumbnail_path:
            current_app.logger.debug(f"Thumbnail file not found for ISBN: {isbn}")
            return jsonify(
                {
                    "error": "Thumbnail not found",
                    "isbn": isbn,
                    "message": f"No thumbnail file available for ISBN {isbn}",
                }
            ), 404

        # Get file stats for client-side caching
        file_stats = os.stat(thumbnail_path)
        file_mtime = file_stats.st_mtime
        file_size = file_stats.st_size

        # Generate ETag based on file path, size, and modification time
        etag_data = f"{thumbnail_path}-{file_size}-{file_mtime}".encode()
        etag = f'"{hashlib.md5(etag_data).hexdigest()}"'

        # Convert modification time to HTTP date format (UTC)
        last_modified = datetime.fromtimestamp(file_mtime, tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

        # Check If-None-Match header (ETag-based conditional request)
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match == etag:
            # Client has current version, return 304 Not Modified
            response = make_response("", 304)
            response.headers["ETag"] = etag
            response.headers["Last-Modified"] = last_modified
            return add_cache_headers(response), 304

        # Check If-Modified-Since header (date-based conditional request)
        if_modified_since = request.headers.get("If-Modified-Since")
        if if_modified_since:
            with suppress(ValueError):
                client_date = datetime.strptime(if_modified_since, "%a, %d %b %Y %H:%M:%S GMT").replace(
                    tzinfo=timezone.utc
                )
                server_date = datetime.fromtimestamp(file_mtime, tz=timezone.utc)
                # Truncate to seconds for comparison (HTTP dates don't include microseconds)
                server_date = server_date.replace(microsecond=0)
                if server_date <= client_date:
                    # File not modified since client's cached version
                    response = make_response("", 304)
                    response.headers["ETag"] = etag
                    response.headers["Last-Modified"] = last_modified
                    return add_cache_headers(response), 304

        # Determine MIME type based on file extension
        mimetype = "image/jpeg"
        if thumbnail_path.lower().endswith(".png"):
            mimetype = "image/png"

        # Serve the file with cache headers
        response = send_file(thumbnail_path, mimetype=mimetype)
        response.headers["ETag"] = etag
        response.headers["Last-Modified"] = last_modified
        return add_cache_headers(response), 200

    except Exception as err:
        current_app.logger.error(f"Error serving thumbnail for ISBN {isbn}: {err!s}")
        return jsonify(
            {"error": "Server error", "isbn": isbn, "message": "An error occurred while serving the thumbnail"}
        ), 500
