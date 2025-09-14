import os
from datetime import datetime
from typing import List, Set

from fastapi import APIRouter, HTTPException, Query, Request

# Import bookverse-core response models for standardization
from bookverse_core.api.responses import (
    SuccessResponse, 
    PaginatedResponse,
    HealthResponse,
    create_success_response,
    create_paginated_response,
    create_health_response
)

from .indexer import Indexer
from .schemas import RecommendationResponse, RecommendationItem, PersonalizedRequest
from .algorithms import score_simple, build_recommendation_item
from .clients import InventoryClient


router = APIRouter()

def get_indexer_with_request_id(request_id: Optional[str] = None) -> Indexer:
    """Create indexer with request ID for HTTP client tracing."""
    client = InventoryClient(request_id=request_id)
    return Indexer(client=client)

# Default indexer for backwards compatibility
indexer = Indexer()


@router.get("/api/v1/recommendations/similar", response_model=SuccessResponse[List[RecommendationItem]])
def get_similar(book_id: str, limit: int = Query(10, ge=1, le=50), request: Request = None):
    """Return similar books to the provided seed `book_id` using simple rule-based scoring."""
    request_id = getattr(request.state, 'request_id', None) if request else None
    idx = get_indexer_with_request_id(request_id).ensure_indices()
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
    
    # Use standardized success response with metadata
    return create_success_response(
        data=ranked,
        message=f"Found {len(ranked)} similar books for '{seed.title}'",
        request_id=getattr(request.state, 'request_id', None) if request else None
    )


@router.post("/api/v1/recommendations/personalized", response_model=SuccessResponse[List[RecommendationItem]])
def get_personalized(payload: PersonalizedRequest, request: Request = None):
    """Return personalized recommendations based on optional seeds/context or trending fallback."""
    request_id = getattr(request.state, 'request_id', None) if request else None
    idx = get_indexer_with_request_id(request_id).ensure_indices()

    seeds: List[str] = []
    if payload.seed_book_ids:
        seeds.extend(payload.seed_book_ids)
    if payload.recently_viewed:
        seeds.extend(payload.recently_viewed)
    if payload.cart_book_ids:
        seeds.extend(payload.cart_book_ids)

    seed_books = [idx.book_by_id[s] for s in seeds if s in idx.book_by_id]
    message_context = "personalized"
    
    if not seed_books:
        # Try feature seeds
        feature_candidates: Set[str] = set()
        for g in payload.seed_genres or []:
            feature_candidates |= idx.genre_to_book_ids.get(g, set())
        for a in payload.seed_authors or []:
            feature_candidates |= idx.author_to_book_ids.get(a, set())
        if not feature_candidates:
            # DEMO PURPOSE: Fallback to trending by popularity when no personalization data available
            ranked_ids = sorted(idx.book_by_id.keys(), key=lambda i: idx.popularity.get(i, 0.0), reverse=True)
            top_ids = ranked_ids[: payload.limit or 10]
            recs = [build_recommendation_item(idx.book_by_id[i], idx.popularity.get(i, 0.0), {"popularity": idx.popularity.get(i, 0.0)}) for i in top_ids if idx.book_by_id[i].availability.in_stock]
            return create_success_response(
                data=recs,
                message=f"Generated {len(recs)} trending recommendations (no personalization data available)",
                request_id=getattr(request.state, 'request_id', None) if request else None
            )
        # Score with pseudo seeds from features
        seed_books = [idx.book_by_id[i] for i in list(feature_candidates)[:3] if i in idx.book_by_id]
        message_context = "feature-based"

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
    
    return create_success_response(
        data=ranked,
        message=f"Generated {len(ranked)} {message_context} recommendations from {len(candidate_ids)} candidates",
        request_id=getattr(request.state, 'request_id', None) if request else None
    )


@router.get("/api/v1/recommendations/trending", response_model=SuccessResponse[List[RecommendationItem]])
def get_trending(limit: int = Query(10, ge=1, le=50), request: Request = None):
    """Return currently trending books based on recent stock_out popularity."""
    request_id = getattr(request.state, 'request_id', None) if request else None
    idx = get_indexer_with_request_id(request_id).ensure_indices()
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
    
    return create_success_response(
        data=items,
        message=f"Generated {len(items)} trending recommendations from {len(ranked_ids)} total books",
        request_id=getattr(request.state, 'request_id', None) if request else None
    )


@router.get("/api/v1/recommendations/health", response_model=HealthResponse)
def recommendations_health():
    """Basic health and cache freshness info for indices and popularity map."""
    idx = indexer.ensure_indices()
    ttl = int(os.getenv("RECO_TTL_SECONDS", "0") or "0")
    last_built = idx.last_built_at
    now = datetime.utcnow().timestamp()
    stale = ttl > 0 and (now - last_built) > ttl
    
    # Determine overall health status
    status = "degraded" if stale else "healthy"
    
    # Detailed health checks
    checks = {
        "indices": {
            "status": "healthy",
            "books": len(idx.book_by_id),
            "genres": len(idx.genre_to_book_ids),
            "authors": len(idx.author_to_book_ids),
            "popularity": len(idx.popularity),
        },
        "cache": {
            "status": "degraded" if stale else "healthy",
            "ttl_seconds": ttl,
            "last_built_at": datetime.utcfromtimestamp(last_built).isoformat() + "Z" if last_built else None,
            "stale": stale,
            "age_seconds": int(now - last_built) if last_built else None,
        },
    }
    
    return create_health_response(
        status=status,
        service="recommendations",
        version=os.getenv("SERVICE_VERSION", "0.1.0-dev"),
        checks=checks,
        uptime=now - last_built if last_built else None
    )


