import os
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

import httpx
from bookverse_core.config import BaseConfig


logger = logging.getLogger(__name__)

INVENTORY_BASE_URL = os.getenv("INVENTORY_BASE_URL", "http://inventory")


class StandardizedHTTPClient:
    """
    Standardized HTTP client with best practices for BookVerse services.
    
    Features:
    - Automatic retries with exponential backoff
    - Request/response logging with request IDs
    - Standardized error handling
    - Authentication header injection
    - Timeout configuration
    - Circuit breaker pattern (basic)
    """
    
    def __init__(
        self,
        base_url: str,
        service_name: str,
        timeout_seconds: float = 10.0,
        max_retries: int = 3,
        auth_token: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.service_name = service_name
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.auth_token = auth_token
        self.request_id = request_id
        
        # Default headers
        self.default_headers = {
            "User-Agent": f"bookverse-recommendations/1.0 (StandardizedHTTPClient)",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        if self.request_id:
            self.default_headers["X-Request-ID"] = self.request_id
            
        if self.auth_token:
            self.default_headers["Authorization"] = f"Bearer {self.auth_token}"
    
    def _create_client(self) -> httpx.Client:
        """Create configured httpx client with retries and timeouts."""
        return httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            headers=self.default_headers,
            follow_redirects=True
        )
    
    def _log_request(self, method: str, url: str, **kwargs):
        """Log outgoing request."""
        logger.info(
            f"🌐 HTTP {method.upper()} {self.service_name}: {url}",
            extra={
                "service": self.service_name,
                "method": method.upper(),
                "url": url,
                "request_id": self.request_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _log_response(self, method: str, url: str, status_code: int, duration_ms: float):
        """Log response with timing."""
        level = logging.INFO if status_code < 400 else logging.WARNING
        logger.log(
            level,
            f"📡 HTTP {method.upper()} {self.service_name}: {url} → {status_code} ({duration_ms:.1f}ms)",
            extra={
                "service": self.service_name,
                "method": method.upper(),
                "url": url,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "request_id": self.request_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retries and logging."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self._log_request(method, url, params=params, json=json_data)
        
        start_time = datetime.utcnow()
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                with self._create_client() as client:
                    response = client.request(
                        method=method,
                        url=endpoint,
                        params=params,
                        json=json_data,
                        **kwargs
                    )
                    
                    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                    self._log_response(method, url, response.status_code, duration_ms)
                    
                    # Raise for HTTP errors (4xx, 5xx)
                    response.raise_for_status()
                    return response
                    
            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code < 500 or attempt == self.max_retries:
                    # Don't retry client errors (4xx) or on final attempt
                    logger.error(
                        f"❌ HTTP {method.upper()} {self.service_name}: {url} failed with {e.response.status_code}",
                        extra={"request_id": self.request_id, "attempt": attempt + 1}
                    )
                    raise
                    
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt == self.max_retries:
                    logger.error(
                        f"❌ HTTP {method.upper()} {self.service_name}: {url} failed after {attempt + 1} attempts: {e}",
                        extra={"request_id": self.request_id}
                    )
                    raise
                    
            # Exponential backoff for retries
            if attempt < self.max_retries:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    f"⚠️ HTTP {method.upper()} {self.service_name}: {url} failed, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})",
                    extra={"request_id": self.request_id, "wait_time": wait_time}
                )
                import time
                time.sleep(wait_time)
        
        # This should never be reached, but just in case
        raise last_exception or Exception("Unexpected error in HTTP client")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """Make GET request."""
        return self._make_request("GET", endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """Make POST request."""
        return self._make_request("POST", endpoint, json_data=json_data, **kwargs)
    
    def put(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """Make PUT request."""
        return self._make_request("PUT", endpoint, json_data=json_data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make DELETE request."""
        return self._make_request("DELETE", endpoint, **kwargs)


class InventoryClient:
    """Enhanced HTTP client for the inventory service with standardized patterns."""

    def __init__(
        self, 
        base_url: Optional[str] = None, 
        timeout_seconds: float = 10.0,
        auth_token: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        self.base_url = base_url or INVENTORY_BASE_URL
        self.client = StandardizedHTTPClient(
            base_url=self.base_url,
            service_name="inventory",
            timeout_seconds=timeout_seconds,
            auth_token=auth_token,
            request_id=request_id
        )

    def list_books(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch a page of books with availability from the inventory service."""
        params = {"page": 1, "per_page": per_page}
        try:
            response = self.client.get("/api/v1/books", params=params)
            data = response.json()
            books = data.get("books", [])
            logger.info(f"✅ Retrieved {len(books)} books from inventory service")
            return books
        except Exception as e:
            logger.error(f"❌ Failed to fetch books from inventory service: {e}")
            raise

    def list_transactions(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch a page of stock transactions (used to derive popularity)."""
        params = {"page": 1, "per_page": per_page}
        try:
            response = self.client.get("/api/v1/transactions", params=params)
            data = response.json()
            transactions = data.get("transactions", [])
            logger.info(f"✅ Retrieved {len(transactions)} transactions from inventory service")
            return transactions
        except Exception as e:
            logger.error(f"❌ Failed to fetch transactions from inventory service: {e}")
            raise
    
    def get_book_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific book by ID from the inventory service."""
        try:
            response = self.client.get(f"/api/v1/books/{book_id}")
            book = response.json()
            logger.info(f"✅ Retrieved book {book_id} from inventory service")
            return book
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"📚 Book {book_id} not found in inventory service")
                return None
            logger.error(f"❌ Failed to fetch book {book_id} from inventory service: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to fetch book {book_id} from inventory service: {e}")
            raise
    
    def check_availability(self, book_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Check availability for multiple books."""
        try:
            # Batch availability check
            response = self.client.post("/api/v1/books/availability", json_data={"book_ids": book_ids})
            availability_data = response.json()
            logger.info(f"✅ Checked availability for {len(book_ids)} books")
            return availability_data.get("availability", {})
        except Exception as e:
            logger.error(f"❌ Failed to check availability for books: {e}")
            # Fallback to individual checks if batch fails
            availability = {}
            for book_id in book_ids:
                try:
                    book = self.get_book_by_id(book_id)
                    if book:
                        availability[book_id] = book.get("availability", {})
                except Exception:
                    continue
            return availability


