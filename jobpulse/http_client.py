"""
HTTP client utilities for making API requests.

Provides connection pooling, rate limiting, retry logic, and error handling.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import (
    DEFAULT_TIMEOUT,
    MAX_CONNECTIONS,
    MAX_KEEPALIVE_CONNECTIONS,
    MAX_RETRIES,
    MIN_REQUEST_INTERVAL,
    RETRY_MAX_WAIT,
    RETRY_MIN_WAIT,
    USER_AGENT,
)

logger = logging.getLogger(__name__)

# Module-level state
_client: Optional[httpx.Client] = None
_last_request_time: float = 0.0


def get_http_client() -> httpx.Client:
    """
    Get or create the shared HTTP client with connection pooling.

    Returns:
        Configured httpx.Client instance
    """
    global _client

    if _client is None or _client.is_closed:
        _client = httpx.Client(
            timeout=httpx.Timeout(DEFAULT_TIMEOUT),
            limits=httpx.Limits(max_connections=MAX_CONNECTIONS, max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS),
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
        )
        logger.debug("HTTP client created")

    return _client


def close_http_client() -> None:
    """Close the shared HTTP client and cleanup resources."""
    global _client

    if _client and not _client.is_closed:
        _client.close()
        _client = None
        logger.info("HTTP client closed")


@contextmanager
def http_client_context():
    """
    Context manager for HTTP client lifecycle.

    Ensures proper cleanup of HTTP client resources.

    Example:
        with http_client_context():
            # Use get_http_client() here
            pass
    """
    try:
        yield get_http_client()
    finally:
        close_http_client()


def rate_limit() -> None:
    """
    Implement simple rate limiting to avoid overwhelming the API.

    Enforces a minimum interval between requests.
    """
    global _last_request_time

    current_time = time.time()
    time_since_last_request = current_time - _last_request_time

    if time_since_last_request < MIN_REQUEST_INTERVAL:
        sleep_time = MIN_REQUEST_INTERVAL - time_since_last_request
        time.sleep(sleep_time)

    _last_request_time = time.time()


@retry(
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    reraise=True,
)
def api_get(url: str) -> Dict[str, Any]:
    """
    Make a GET request to the API with retry logic.

    Includes automatic retries with exponential backoff for transient failures.

    Args:
        url: The API endpoint URL
        params: Optional query parameters

    Returns:
        Parsed JSON response as dictionary

    Raises:
        httpx.HTTPError: For HTTP-related errors
        ValueError: For invalid JSON responses
        RuntimeError: For API-specific errors
    """
    rate_limit()

    client = get_http_client()

    try:
        logger.debug(f"Making API request to: {url}")
        response = client.get(url)
        response.raise_for_status()

        # Validate JSON response
        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise ValueError(f"API returned invalid JSON: {e}")

        # Check API-level status
        if isinstance(data, dict):
            status_code = data.get("statuscode")
            if status_code and status_code != "1":
                error_msg = data.get("message", "Unknown API error")
                logger.error(f"API error: {error_msg} (status: {status_code})")
                raise RuntimeError(f"API error: {error_msg}")

        logger.debug("API request successful")
        return data

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} error: {e}")
        raise
    except httpx.TimeoutException as e:
        logger.error(f"Request timeout: {e}")
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise
