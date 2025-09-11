import os
import time
from typing import Dict, List, Set

from .clients import InventoryClient
from .schemas import BookLite, Availability
from .settings import get_ttl_seconds


RECO_TTL_SECONDS = int(os.getenv("RECO_TTL_SECONDS", str(get_ttl_seconds())))  # can be overridden via env


class CatalogIndices:
    """In-memory indices for recommendation candidate search."""
    def __init__(self) -> None:
        self.book_by_id: Dict[str, BookLite] = {}
        self.genre_to_book_ids: Dict[str, Set[str]] = {}
        self.author_to_book_ids: Dict[str, Set[str]] = {}
        self.popularity: Dict[str, float] = {}
        self.last_built_at: float = 0.0


class Indexer:
    """Build and serve catalog indices with a simple TTL cache."""

    def __init__(self, client: InventoryClient | None = None) -> None:
        self.client = client or InventoryClient()
        self.indices = CatalogIndices()

    def _is_stale(self) -> bool:
        """Return True if the cached indices are older than TTL or cache disabled."""
        if RECO_TTL_SECONDS <= 0:
            return True
        return (time.time() - self.indices.last_built_at) > RECO_TTL_SECONDS

    def ensure_indices(self) -> CatalogIndices:
        """Return indices, rebuilding if missing or stale."""
        if not self.indices.book_by_id or self._is_stale():
            self.rebuild()
        return self.indices

    def rebuild(self) -> None:
        """Rebuild all in-memory indices and recompute popularity."""
        books_payload = self.client.list_books(per_page=200)
        book_by_id: Dict[str, BookLite] = {}
        genre_to_book_ids: Dict[str, Set[str]] = {}
        author_to_book_ids: Dict[str, Set[str]] = {}

        for item in books_payload:
            availability = Availability(**item["availability"]) if "availability" in item else Availability(quantity_available=0, in_stock=False, low_stock=True)
            book = BookLite(
                id=str(item["id"]),
                title=item["title"],
                authors=item["authors"],
                genres=item["genres"],
                price=float(item["price"]),
                cover_image_url=item["cover_image_url"],
                availability=availability,
            )
            book_by_id[book.id] = book
            for g in book.genres:
                genre_to_book_ids.setdefault(g, set()).add(book.id)
            for a in book.authors:
                author_to_book_ids.setdefault(a, set()).add(book.id)

        # Popularity from recent transactions (stock_out)
        transactions = self.client.list_transactions(per_page=200)
        stock_out_counts: Dict[str, int] = {}
        for tx in transactions:
            if tx.get("transaction_type") == "stock_out":
                bid = str(tx.get("book_id"))
                stock_out_counts[bid] = stock_out_counts.get(bid, 0) + abs(int(tx.get("quantity_change", -1)))

        # Normalize popularity
        if stock_out_counts:
            max_count = max(stock_out_counts.values()) or 1
            popularity = {k: v / max_count for k, v in stock_out_counts.items()}
        else:
            popularity = {}

        self.indices.book_by_id = book_by_id
        self.indices.genre_to_book_ids = genre_to_book_ids
        self.indices.author_to_book_ids = author_to_book_ids
        self.indices.popularity = popularity
        self.indices.last_built_at = time.time()


