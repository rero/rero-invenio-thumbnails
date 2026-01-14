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
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""RERO Invenio module that adds thumbnails."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def requests_retry_session(retries=5, backoff_factor=0.5, status_forcelist=(500, 502, 504), session=None, headers=None):
    """Create a requests Session with automatic retry strategy for failed requests.

    This function configures an HTTP session with exponential backoff retry logic
    to handle transient failures gracefully. It adapts both HTTP and HTTPS connections.

    :param retries: The total number of retry attempts to make. Defaults to 5.
    :param backoff_factor: Sleep duration multiplier between failed requests.
        The actual sleep time is calculated as:
        {backoff_factor} * (2 ** ({number_of_total_retries} - 1))
        Defaults to 0.5 seconds.
    :param status_forcelist: HTTP response status codes that trigger a retry.
        Defaults to (500, 502, 504) - server errors.
    :param session: An existing Session object to configure.
        If None, a new Session is created. Defaults to None.
    :param header: Additional HTTP headers to add to the session.
        Defaults to None.
    :returns: requests.Session - A configured Session object with retry adapters mounted
        for both HTTP and HTTPS connections.

    Examples:
        >>> session = requests_retry_session(
        ...     retries=3,
        ...     backoff_factor=1.0,
        ...     header={"User-Agent": "MyApp/1.0"}
        ... )
        >>> response = session.get("https://api.example.com/data")

    Note:
        The retry logic applies to connection errors and specified status codes.
        The session is ready to use immediately after creation.
    """
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    if headers:
        session.headers.update(headers)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
