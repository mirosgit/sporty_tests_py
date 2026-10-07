"""Generic HTTP layer: one shared session with the base URL, headers and timeout."""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, base_url: str, user_id: str, timeout: float) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json", "x-user-id": user_id})

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, json: Any = None, **kwargs: Any) -> requests.Response:
        return self._request("POST", path, json=json, **kwargs)

    def close(self) -> None:
        self._session.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self._base_url}{path}"
        try:
            response = self._session.request(method, url, timeout=self._timeout, **kwargs)
        except requests.RequestException as error:
            logger.error("%s %s failed: %s", method, url, error)
            raise
        logger.info("%s %s -> %s", method, url, response.status_code)
        return response
