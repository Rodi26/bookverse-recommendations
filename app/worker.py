import logging
import os
import time

from .indexer import Indexer


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("recommendations-worker")


def main() -> None:
    """Background refresher that periodically rebuilds indices and popularity."""
    indexer = Indexer()
    interval = int(os.getenv("RECO_WORKER_REFRESH_SECONDS", "60"))
    logger.info("Recommendations worker started. Refresh interval: %ss", interval)
    while True:
        try:
            indexer.rebuild()
            logger.info("Indices rebuilt. Popularity entries: %s, books: %s", len(indexer.indices.popularity), len(indexer.indices.book_by_id))
        except Exception as e:
            logger.exception("Worker rebuild failed: %s", e)
        time.sleep(interval)


if __name__ == "__main__":
    main()


