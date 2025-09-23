from typing import Dict, List, Tuple, Iterable
from .schemas import BookLite, RecommendationItem, Availability
from .settings import get_weights, filter_out_of_stock_enabled


def score_simple(seed_books: Iterable[BookLite], candidate: BookLite, popularity: Dict[str, float]) -> Tuple[float, Dict[str, float]]:

    seed_genres = set(g for b in seed_books for g in b.genres)
    seed_authors = set(a for b in seed_books for a in b.authors)
    if filter_out_of_stock_enabled() and not candidate.availability.in_stock:
        return 0.0, {"genre": 0.0, "author": 0.0, "popularity": 0.0}

    genre_overlap = len(seed_genres.intersection(set(candidate.genres)))
    author_overlap = len(seed_authors.intersection(set(candidate.authors)))
    pop = popularity.get(candidate.id, 0.0)

    w = get_weights()
    score = w["genre"] * genre_overlap + w["author"] * author_overlap + w["popularity"] * pop
    return score, {"genre": float(genre_overlap), "author": float(author_overlap), "popularity": float(pop)}


def build_recommendation_item(b: BookLite, score: float, factors: Dict[str, float]) -> RecommendationItem:
    return RecommendationItem(
        id=b.id,
        title=b.title,
        authors=b.authors,
        genres=b.genres,
        price=b.price,
        cover_image_url=b.cover_image_url,
        availability=Availability(**b.availability.model_dump()),
        score=score,
        score_factors=factors,
    )


