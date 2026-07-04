"""
EasySwitch - Advanced Async HTTP Client for API requests
"""
import json
import asyncio
import logging
from typing import (
    Any, Dict, Optional, Union, AsyncIterator, List
)
from dataclasses import dataclass
from time import monotonic
import aiohttp
from aiohttp import ClientTimeout, ClientResponse, ClientSession

from easyswitch.exceptions import (
    NetworkError, RateLimitError, APIError
)



logger = logging.getLogger("easyswitch.http")

@dataclass
class HTTPResponse:
    """Structured HTTP response container"""
    status: int
    headers: Dict[str, str]
    data: Union[Dict[str, Any], str]
    elapsed: float
    url: str

class HTTPClient:
    """Advanced asynchronous HTTP client with retry logic and connection pooling"""
    
    def __init__(
        self,
        base_url: str,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        debug: bool = False,
        proxy: Optional[str] = None,
        pool_size: int = 100
    ):
        """
        Initialize the HTTP client with advanced configuration.
        
        Args:
            base_url: Base API endpoint
            default_headers: Default headers for all requests
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            retry_delay: Initial delay between retries in seconds
            debug: Enable debug logging
            proxy: Proxy server URL
            pool_size: Connection pool size
        """
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.timeout = ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.debug = debug
        self.proxy = proxy
        self.pool_size = pool_size
        self._session: Optional[ClientSession] = None
        self.connector: Optional[aiohttp.TCPConnector] = None

    async def __aenter__(self) -> 'HTTPClient':
        await self.start_session()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close_session()
        
    @property
    def is_closed(self) -> bool:
        """Check if the session is closed"""
        return self._session is None or self._session.closed

    async def start_session(self) -> None:
        """Initialize the client session"""
        if self._session is None or self._session.closed:
            if self.connector is None:
                self.connector = aiohttp.TCPConnector(
                    limit = self.pool_size,
                    force_close = False,
                    enable_cleanup_closed = True
                )
            self._session = ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                headers=self.default_headers
            )

    async def close_session(self) -> None:
        """Close the client session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Union[Dict[str, Any], List[Any]]] = None,
        **kwargs
    ) -> HTTPResponse:
        """
        Execute HTTP request with retry logic and advanced error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            headers: Additional headers
            params: Query parameters
            data: Raw request data
            json_data: JSON-serializable data
            kwargs: Additional aiohttp request parameters
            
        Returns:
            HTTPResponse: Structured response object
            
        Raises:
            NetworkError: For connection issues
            APIError: For API-level errors
            RateLimitError: For 429 responses
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        merged_headers = {**self.default_headers, **(headers or {})}
        
        if self.debug:
            logger.debug(
                f"Request: {method} {url}\n"
                f"Headers: {merged_headers}\n"
                f"Params: {params}\n"
                f"Data: {data or json_data}"
            )

        start_time = monotonic()
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if not self._session or self._session.closed:
                    await self.start_session()

                async with self._session.request(
                    method=method,
                    url=url,
                    headers=merged_headers,
                    params=params,
                    data=data,
                    json=json_data,
                    proxy=self.proxy,
                    **kwargs
                ) as response:
                    elapsed = monotonic() - start_time
                    
                    # Process response content
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        response_data = await response.json()
                    else:
                        response_text = await response.text()
                        try:
                            response_data = json.loads(response_text)
                        except json.JSONDecodeError:
                            response_data = {"raw_response": response_text}

                    if self.debug:
                        logger.debug(
                            f"Response ({response.status}) in {elapsed:.2f}s\n"
                            f"Data: {response_data}"
                        )

                    # Handle error responses
                    if response.status == 429:
                        raise RateLimitError(
                            message = "Rate limit exceeded",
                            status_code=response.status,
                            raw_response=response_data,
                        )

                    # Non-2xx checks are intentionally handled at the adapter level,
                    # since each provider API returns errors in a different format.
                    # Uncomment below to enforce a blanket non-2xx rejection instead.

                    return HTTPResponse(
                        status = response.status,
                        headers = dict(response.headers),
                        data = response_data,
                        elapsed = elapsed,
                        url = response.url
                    )

            except (aiohttp.ClientError, aiohttp.ClientPayloadError) as e:
                last_exception = e
                if attempt == self.max_retries:
                    logger.error(f"Request failed after {self.max_retries} attempts")
                    raise NetworkError(
                        message=f"Network error: {str(e)}",
                        original_exception=e
                    ) from e
                
                retry_wait = self.retry_delay * (2 ** attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed. Retrying in {retry_wait:.1f}s. Error: {str(e)}"
                )
                await asyncio.sleep(retry_wait)

            except json.JSONDecodeError as e:
                raise APIError(
                    message="Invalid JSON response",
                    status_code=500,
                    raw_response=str(e)
                ) from e

    async def stream_response(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> AsyncIterator[bytes]:
        """Stream response content in chunks"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        merged_headers = {**self.default_headers, **(headers or {})}

        async with self._session.request(
            method=method,
            url=url,
            headers=merged_headers,
            proxy=self.proxy,
            **kwargs
        ) as response:
            async for chunk in response.content.iter_chunked(1024):
                yield chunk

    async def get(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> HTTPResponse:
        """Perform GET request"""
        return await self._request("GET", endpoint, headers, params, **kwargs)

    async def post(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Union[Dict[str, Any], List[Any]]] = None,
        **kwargs
    ) -> HTTPResponse:
        """Perform POST request"""
        return await self._request(
            "POST", endpoint, headers, params, data, json_data, **kwargs
        )

    async def put(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Union[Dict[str, Any], List[Any]]] = None,
        **kwargs
    ) -> HTTPResponse:
        """Perform PUT request"""
        return await self._request(
            "PUT", endpoint, headers, params, data, json_data, **kwargs
        )

    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> HTTPResponse:
        """Perform DELETE request"""
        return await self._request("DELETE", endpoint, headers, params, **kwargs)

    async def patch(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Union[Dict[str, Any], List[Any]]] = None,
        **kwargs
    ) -> HTTPResponse:
        """Perform PATCH request"""
        return await self._request(
            "PATCH", endpoint, headers, params, data, json_data, **kwargs
        )