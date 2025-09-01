import os
from datetime import datetime
from typing import List, Set

from fastapi import APIRouter, HTTPException, Query

from .indexer import Indexer
from .schemas import RecommendationResponse, RecommendationItem, PersonalizedRequest
from .algorithms import score_simple, build_recommendation_item


router = APIRouter()
indexer = Indexer()


@router.get("/api/v1/recommendations/similar", response_model=RecommendationResponse)
def get_similar(book_id: str, limit: int = Query(10, ge=1, le=50)):
    """Return similar books to the provided seed `book_id` using simple rule-based scoring."""
    idx = indexer.ensure_indices()
    if book_id not in idx.book_by_id:
        raise HTTPException(status_code=404, detail="Seed book not found")

    seed = idx.book_by_id[book_id]
    candidate_ids: Set[str] = set()
    for g in seed.genres:
        candidate_ids |= idx.genre_to_book_ids.get(g, set())
    for a in seed.authors:
        candidate_ids |= idx.author_to_book_ids.get(a, set())
    candidate_ids.discard(book_id)

    scored: List[RecommendationItem] = []
    for cid in candidate_ids:
        b = idx.book_by_id[cid]
        s, factors = score_simple([seed], b, idx.popularity)
        if s <= 0:
            continue
        scored.append(build_recommendation_item(b, s, factors))

    ranked = sorted(scored, key=lambda r: r.score, reverse=True)[:limit]
    return RecommendationResponse(
        recommendations=ranked,
        meta={
            "limit": limit,
            "total_candidates": len(candidate_ids),
            "generated_at": datetime.utcnow().isoformat() + "Z",
        },
    )


@router.post("/api/v1/recommendations/personalized", response_model=RecommendationResponse)
def get_personalized(payload: PersonalizedRequest):
    """Return personalized recommendations based on optional seeds/context or trending fallback."""
    idx = indexer.ensure_indices()

    seeds: List[str] = []
    if payload.seed_book_ids:
        seeds.extend(payload.seed_book_ids)
    if payload.recently_viewed:
        seeds.extend(payload.recently_viewed)
    if payload.cart_book_ids:
        seeds.extend(payload.cart_book_ids)

    seed_books = [idx.book_by_id[s] for s in seeds if s in idx.book_by_id]
    if not seed_books:
        # Try feature seeds
        feature_candidates: Set[str] = set()
        for g in payload.seed_genres or []:
            feature_candidates |= idx.genre_to_book_ids.get(g, set())
        for a in payload.seed_authors or []:
            feature_candidates |= idx.author_to_book_ids.get(a, set())
        if not feature_candidates:
            # Fallback to trending by popularity
            ranked_ids = sorted(idx.book_by_id.keys(), key=lambda i: idx.popularity.get(i, 0.0), reverse=True)
            top_ids = ranked_ids[: payload.limit or 10]
            recs = [build_recommendation_item(idx.book_by_id[i], idx.popularity.get(i, 0.0), {"popularity": idx.popularity.get(i, 0.0)}) for i in top_ids if idx.book_by_id[i].availability.in_stock]
            return RecommendationResponse(
                recommendations=recs,
                meta={"limit": payload.limit or 10, "total_candidates": len(top_ids), "generated_at": datetime.utcnow().isoformat() + "Z"},
            )
        # Score with pseudo seeds from features
        seed_books = [idx.book_by_id[i] for i in list(feature_candidates)[:3] if i in idx.book_by_id]

    # Collect candidates from seeds
    candidate_ids: Set[str] = set()
    for sb in seed_books:
        for g in sb.genres:
            candidate_ids |= idx.genre_to_book_ids.get(g, set())
        for a in sb.authors:
            candidate_ids |= idx.author_to_book_ids.get(a, set())
    candidate_ids.difference_update({b.id for b in seed_books})

    scored: List[RecommendationItem] = []
    for cid in candidate_ids:
        b = idx.book_by_id[cid]
        s, factors = score_simple(seed_books, b, idx.popularity)
        if s <= 0:
            continue
        scored.append(build_recommendation_item(b, s, factors))

    limit = payload.limit or 10
    ranked = sorted(scored, key=lambda r: r.score, reverse=True)[:limit]
    return RecommendationResponse(
        recommendations=ranked,
        meta={
            "limit": limit,
            "total_candidates": len(candidate_ids),
            "generated_at": datetime.utcnow().isoformat() + "Z",
        },
    )


@router.get("/api/v1/recommendations/trending", response_model=RecommendationResponse)
def get_trending(limit: int = Query(10, ge=1, le=50)):
    """Return currently trending books based on recent stock_out popularity."""
    idx = indexer.ensure_indices()
    ranked_ids = sorted(idx.book_by_id.keys(), key=lambda i: idx.popularity.get(i, 0.0), reverse=True)
    items: List[RecommendationItem] = []
    for bid in ranked_ids:
        b = idx.book_by_id[bid]
        if not b.availability.in_stock:
            continue
        s = idx.popularity.get(bid, 0.0)
        items.append(build_recommendation_item(b, s, {"popularity": s}))
        if len(items) >= limit:
            break
    return RecommendationResponse(
        recommendations=items,
        meta={"limit": limit, "total_candidates": len(ranked_ids), "generated_at": datetime.utcnow().isoformat() + "Z"},
    )


@router.get("/api/v1/recommendations/health")
def recommendations_health():
    """Basic health and cache freshness info for indices and popularity map."""
    idx = indexer.ensure_indices()
    ttl = int(os.getenv("RECO_TTL_SECONDS", "0") or "0")
    last_built = idx.last_built_at
    now = datetime.utcnow().timestamp()
    stale = ttl > 0 and (now - last_built) > ttl
    return {
        "status": "healthy",
        "indices": {
            "books": len(idx.book_by_id),
            "genres": len(idx.genre_to_book_ids),
            "authors": len(idx.author_to_book_ids),
            "popularity": len(idx.popularity),
        },
        "cache": {
            "ttl_seconds": ttl,
            "last_built_at": datetime.utcfromtimestamp(last_built).isoformat() + "Z" if last_built else None,
            "stale": stale,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


