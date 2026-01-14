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

"""Flask blueprint for serving book thumbnail images and URLs."""

from flask import Blueprint, current_app, jsonify, make_response, request

from rero_invenio_thumbnails.api import get_thumbnail as get_thumbnail_api
from rero_invenio_thumbnails.api import get_thumbnail_url

api_thumbnails = Blueprint("api_thumbnails", __name__, url_prefix="/")


def add_cache_headers(response):
    """Add HTTP cache control headers to response.

    :param response: Flask response object
    :returns: Modified response with cache headers
    """
    max_age = current_app.config.get("RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE", 86400)
    if max_age > 0:
        response.headers["Cache-Control"] = f"public, max-age={max_age}"
        response.headers["Vary"] = "Accept-Encoding"
    else:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


def _make_text_response(message, status_code):
    """Create a text/plain response.

    :param message: Response message
    :param status_code: HTTP status code
    :returns: Flask Response object
    """
    response = make_response(message, status_code)
    response.headers["Content-Type"] = "text/plain"
    return response


@api_thumbnails.route("/thumbnails/<isbn>", methods=["GET"])
def get_thumbnail(isbn):
    """Retrieve and serve a thumbnail image for a given ISBN.

    Returns raw JPEG image data from the first available provider.
    The image is validated to ensure minimum 10x10 dimensions and valid format.

    :param isbn: ISBN identifier (ISBN-10 or ISBN-13)

    Query parameters:
        - width (int): Desired width in pixels (maintains aspect ratio)
        - height (int): Desired height in pixels (maintains aspect ratio)
        - cached (str): Set to 'false' to bypass cache (default: 'true')

    :returns: Response with raw JPEG image data (200) or error message (404/500)
    :rtype: tuple[flask.Response, int]

    Response headers:
        - Content-Type: image/jpeg (on success) or text/plain (on error)
        - Cache-Control: Configurable via RERO_INVENIO_THUMBNAILS_HTTP_CACHE_MAX_AGE

    Example:
        GET /thumbnails/9780134685991?width=200

        Returns raw JPEG image data scaled to 200px width
    """
    width = request.args.get("width", type=int)
    height = request.args.get("height", type=int)
    cached = request.args.get("cached", default="true").lower() != "false"

    current_app.logger.debug(">>>>>")

    try:
        # Use the API function to get the thumbnail image bytes
        img_data, _provider = get_thumbnail_api(isbn, cached=cached, width=width, height=height)

        if not img_data:
            current_app.logger.warning(f"Thumbnail not found for ISBN: {isbn}")
            return _make_text_response(f"Thumbnail not found for ISBN {isbn}", 404)

        # Return image data directly
        # current_app.logger.debug(
        #     f"Serving thumbnail for ISBN {isbn} from provider '{provider}' "
        #     f"(width={width}, height={height}, cached={cached}, "
        #     f"client={request.remote_addr}, user_agent={request.headers.get('User-Agent', 'unknown')[:50]})"
        # )
        response = make_response(img_data)
        response.headers["Content-Type"] = "image/jpeg"
        return add_cache_headers(response), 200

    except Exception as err:
        current_app.logger.error(f"Error retrieving thumbnail for ISBN {isbn}: {err!s}")
        return _make_text_response(f"Error retrieving thumbnail for ISBN {isbn}", 500)


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
            "isbn": "9780134685991"
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
        url = get_thumbnail_url(isbn, cached=cached)

        if not url:
            current_app.logger.debug(f"Thumbnail URL not found for ISBN: {isbn}")
            return jsonify(
                {"error": "Thumbnail not found", "isbn": isbn, "message": f"No thumbnail available for ISBN {isbn}"}
            ), 404

        # Return thumbnail URL in JSON format
        current_app.logger.debug(f"Found thumbnail URL for ISBN {isbn}: {url}")
        response = jsonify({"url": url, "isbn": isbn})
        return add_cache_headers(response), 200

    except Exception as err:
        current_app.logger.error(f"Error retrieving thumbnail URL for ISBN {isbn}: {err!s}")
        return jsonify(
            {"error": "Server error", "isbn": isbn, "message": "An error occurred while retrieving the thumbnail URL"}
        ), 500
