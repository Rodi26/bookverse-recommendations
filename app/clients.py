import os
from typing import Dict, Any, List
import httpx


INVENTORY_BASE_URL = os.getenv("INVENTORY_BASE_URL", "http://inventory")


class InventoryClient:
    """Minimal HTTP client for the inventory service used by recommendations."""

    def __init__(self, base_url: str | None = None, timeout_seconds: float = 5.0):
        self.base_url = base_url or INVENTORY_BASE_URL
        self.timeout = timeout_seconds

    def _client(self) -> httpx.Client:
        """Create a short-lived httpx client instance."""
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def list_books(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch a page of books with availability from the inventory service."""
        url = "/api/v1/books"
        params = {"page": 1, "per_page": per_page}
        with self._client() as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("books", [])

    def list_transactions(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch a page of stock transactions (used to derive popularity)."""
        url = "/api/v1/transactions"
        params = {"page": 1, "per_page": per_page}
        with self._client() as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("transactions", [])


