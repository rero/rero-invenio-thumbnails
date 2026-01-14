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

"""Blueprint used for serving local files."""

from io import BytesIO

from flask import Blueprint, current_app, jsonify, request, send_file

from rero_invenio_thumbnails.api import get_thumbnail as get_thumbnail_api
from rero_invenio_thumbnails.api import get_thumbnail_url

api_thumbnails = Blueprint("api_thumbnails", __name__, url_prefix="/")


@api_thumbnails.route("/thumbnails/<isbn>", methods=["GET"])
def get_thumbnail(isbn):
    """Retrieve and serve a thumbnail for a given ISBN from any provider.

    :param isbn: ISBN identifier from URL path

    Query parameters:
        - width: desired width in pixels (optional)
        - height: desired height in pixels (optional)
        - cached: if 'false', disables cache lookup and storage (default: true)

    If either width or height is provided, the image will be scaled proportionally.
    """
    width = request.args.get("width", type=int)
    height = request.args.get("height", type=int)
    cached = request.args.get("cached", default="true").lower() != "false"

    try:
        # Use the API function to get the thumbnail image bytes
        img_data = get_thumbnail_api(isbn, cached=cached, width=width, height=height)

        if not img_data:
            current_app.logger.warning(f"Thumbnail not found for ISBN: {isbn}")
            return jsonify(
                {"error": "Thumbnail not found", "isbn": isbn, "message": f"No thumbnail available for ISBN {isbn}"}
            ), 404

        # Serve the image
        current_app.logger.debug(f"Serving thumbnail for ISBN {isbn}")
        img_bytes = BytesIO(img_data)
        return send_file(img_bytes, mimetype="image/jpeg", as_attachment=False)

    except Exception as e:
        current_app.logger.error(f"Error retrieving thumbnail for ISBN {isbn}: {e!s}")
        return jsonify(
            {"error": "Server error", "isbn": isbn, "message": "An error occurred while retrieving the thumbnail"}
        ), 500


@api_thumbnails.route("/thumbnails-url/<isbn>", methods=["GET"])
def get_thumbnail_url_endpoint(isbn):
    """Retrieve thumbnail URL for a given ISBN as JSON.

    :param isbn: ISBN identifier from URL path

    Query parameters:
        - cached: if 'false', disables cache lookup (default: true)
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
        return jsonify({"url": url, "isbn": isbn}), 200

    except Exception as e:
        current_app.logger.error(f"Error retrieving thumbnail URL for ISBN {isbn}: {e!s}")
        return jsonify(
            {"error": "Server error", "isbn": isbn, "message": "An error occurred while retrieving the thumbnail URL"}
        ), 500
