"""API integration module for RPA framework."""

import time
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth

from ..core.logger import LoggerMixin


class APIModule(LoggerMixin):
    """Handle REST API integrations."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self._session = requests.Session()
        self._default_headers: Dict[str, str] = {}

    def configure(
        self,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_header: str = "X-API-Key",
        basic_auth: Optional[tuple] = None,
    ) -> None:
        """Configure API settings.

        Args:
            base_url: Base URL for all requests
            headers: Default headers
            auth_token: Bearer token for authorization
            api_key: API key
            api_key_header: Header name for API key
            basic_auth: Tuple of (username, password)
        """
        if base_url:
            self.base_url = base_url

        if headers:
            self._default_headers.update(headers)

        if auth_token:
            self._default_headers["Authorization"] = f"Bearer {auth_token}"

        if api_key:
            self._default_headers[api_key_header] = api_key

        if basic_auth:
            self._session.auth = HTTPBasicAuth(*basic_auth)

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith("http"):
            return endpoint
        if self.base_url:
            return urljoin(self.base_url, endpoint)
        return endpoint

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """Make an HTTP request with retry logic."""
        url = self._build_url(endpoint)

        request_headers = self._default_headers.copy()
        if headers:
            request_headers.update(headers)

        last_error = None

        for attempt in range(self.retry_count):
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    headers=request_headers,
                    files=files,
                    timeout=self.timeout,
                )

                # Log request
                self.logger.info(f"{method} {url} -> {response.status_code}")

                # Raise for 4xx/5xx errors
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < self.retry_count - 1:
                    self.logger.warning(f"Request failed, retrying ({attempt + 1}/{self.retry_count}): {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    self.logger.error(f"Request failed after {self.retry_count} attempts: {e}")
                    raise

        raise last_error

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers

        Returns:
            JSON response as dict
        """
        response = self._request("GET", endpoint, params=params, headers=headers)
        return response.json()

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a POST request.

        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON body
            headers: Additional headers
            files: Files to upload

        Returns:
            JSON response as dict
        """
        response = self._request("POST", endpoint, data=data, json=json, headers=headers, files=files)
        return response.json()

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        response = self._request("PUT", endpoint, data=data, json=json, headers=headers)
        return response.json()

    def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a PATCH request."""
        response = self._request("PATCH", endpoint, data=data, json=json, headers=headers)
        return response.json()

    def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Make a DELETE request.

        Returns:
            True if successful (2xx status)
        """
        response = self._request("DELETE", endpoint, headers=headers)
        return response.ok

    def get_raw(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """Make a GET request and return raw response."""
        return self._request("GET", endpoint, params=params)

    def paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_param: str = "page",
        limit_param: str = "limit",
        limit: int = 100,
        max_pages: Optional[int] = None,
        data_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch paginated data from an API.

        Args:
            endpoint: API endpoint
            params: Base query parameters
            page_param: Parameter name for page number
            limit_param: Parameter name for page size
            limit: Items per page
            max_pages: Maximum pages to fetch
            data_key: Key in response containing data list

        Returns:
            Combined list of all items
        """
        all_items = []
        page = 1
        params = params or {}

        while True:
            params[page_param] = page
            params[limit_param] = limit

            response = self.get(endpoint, params=params)

            if data_key:
                items = response.get(data_key, [])
            elif isinstance(response, list):
                items = response
            else:
                items = response.get("data", response.get("items", response.get("results", [])))

            if not items:
                break

            all_items.extend(items)
            self.logger.info(f"Fetched page {page}, total items: {len(all_items)}")

            if len(items) < limit:
                break

            if max_pages and page >= max_pages:
                break

            page += 1

        return all_items

    def batch_request(
        self,
        requests_data: List[Dict[str, Any]],
        parallel: bool = False,
    ) -> List[Dict[str, Any]]:
        """Execute multiple API requests.

        Args:
            requests_data: List of request configs, each with:
                - method: HTTP method
                - endpoint: API endpoint
                - params/json/data: Request data
            parallel: Execute in parallel (not implemented yet)

        Returns:
            List of responses
        """
        results = []

        for req in requests_data:
            method = req.get("method", "GET").upper()
            endpoint = req["endpoint"]

            if method == "GET":
                result = self.get(endpoint, params=req.get("params"))
            elif method == "POST":
                result = self.post(endpoint, json=req.get("json"), data=req.get("data"))
            elif method == "PUT":
                result = self.put(endpoint, json=req.get("json"))
            elif method == "DELETE":
                result = {"success": self.delete(endpoint)}
            else:
                raise ValueError(f"Unsupported method: {method}")

            results.append(result)

        return results

    def webhook_handler(
        self,
        callback: Callable[[Dict[str, Any]], Any],
    ) -> Callable:
        """Create a webhook handler function.

        Args:
            callback: Function to call with webhook payload

        Returns:
            Handler function for web frameworks
        """
        def handler(payload: Dict[str, Any]) -> Any:
            self.logger.info(f"Webhook received: {list(payload.keys())}")
            return callback(payload)

        return handler

    def health_check(self, endpoint: str = "/health") -> bool:
        """Check if API is healthy.

        Args:
            endpoint: Health check endpoint

        Returns:
            True if healthy
        """
        try:
            response = self._request("GET", endpoint)
            return response.ok
        except Exception:
            return False

    def set_bearer_token(self, token: str) -> None:
        """Set Bearer token for authentication."""
        self._default_headers["Authorization"] = f"Bearer {token}"

    def set_api_key(self, key: str, header: str = "X-API-Key") -> None:
        """Set API key for authentication."""
        self._default_headers[header] = key

    def clear_auth(self) -> None:
        """Clear authentication headers."""
        self._default_headers.pop("Authorization", None)
        self._session.auth = None
