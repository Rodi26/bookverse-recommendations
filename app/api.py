import os
import logging
from datetime import datetime
from typing import List, Set, Optional

from fastapi import APIRouter, HTTPException, Query, Request, Depends

# Import standardized logging utilities
from bookverse_core.utils.logging import (
    get_logger,
    log_request_start,
    log_request_end,
    log_error_with_context,
    log_demo_info
)

logger = get_logger(__name__)

# Import bookverse-core response models and validation utilities
from bookverse_core.api.responses import (
    SuccessResponse, 
    PaginatedResponse,
    HealthResponse,
    create_success_response,
    create_paginated_response,
    create_health_response
)
from bookverse_core.api.pagination import (
    PaginationParams,
    create_pagination_params,
    create_pagination_meta,
)
from bookverse_core.utils.validation import (
    sanitize_string,
    create_validation_error_message
)
from bookverse_core.api.exceptions import (
    BookVerseHTTPException,
    raise_validation_error,
    raise_not_found_error,
    raise_upstream_error,
    raise_internal_error,
    handle_service_exception,
    create_error_context
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
    start_time = datetime.utcnow()
    
    # Log request start with standardized format
    log_request_start(logger, "GET", f"/api/v1/recommendations/similar?book_id={book_id}&limit={limit}", request_id)
    
    # Validate and sanitize book_id parameter using standardized error handling
    try:
        sanitized_book_id = sanitize_string(book_id, max_length=100)
        if not sanitized_book_id:
            raise_validation_error(
                "Book ID cannot be empty after sanitization",
                field="book_id",
                value=book_id
            )
        book_id = sanitized_book_id
    except ValueError as e:
        raise_validation_error(str(e), field="book_id", value=book_id)
    
    # Get indices with proper error handling
    try:
        idx = get_indexer_with_request_id(request_id).ensure_indices()
    except Exception as e:
        context = create_error_context(request_id=request_id, operation="ensure_indices")
        raise_upstream_error("inventory", e, "Failed to load book catalog")
    
    # Check if book exists
    if book_id not in idx.book_by_id:
        raise_not_found_error(
            "book", 
            book_id, 
            f"Book '{book_id}' not found in catalog of {len(idx.book_by_id)} books"
        )

    # Generate recommendations with error handling
    try:
        seed = idx.book_by_id[book_id]
        candidate_ids: Set[str] = set()
        
        # Collect candidates from genres and authors
        for g in seed.genres:
            candidate_ids |= idx.genre_to_book_ids.get(g, set())
        for a in seed.authors:
            candidate_ids |= idx.author_to_book_ids.get(a, set())
        candidate_ids.discard(book_id)

        # Score and rank candidates
        scored: List[RecommendationItem] = []
        for cid in candidate_ids:
            try:
                b = idx.book_by_id[cid]
                s, factors = score_simple([seed], b, idx.popularity)
                if s <= 0:
                    continue
                scored.append(build_recommendation_item(b, s, factors))
            except Exception as e:
                # Log individual scoring errors but continue processing
                logger.warning(f"Failed to score book {cid}: {e}", extra={"request_id": request_id})
                continue

        ranked = sorted(scored, key=lambda r: r.score, reverse=True)[:limit]
        
        # Log successful completion
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        log_request_end(logger, "GET", f"/api/v1/recommendations/similar", 200, duration_ms, request_id)
        
        # Log demo-specific information
        log_demo_info(logger, f"Generated {len(ranked)} similar recommendations for book '{seed.title}' using rule-based scoring")
        
        # Use standardized success response with metadata
        return create_success_response(
            data=ranked,
            message=f"Found {len(ranked)} similar books for '{seed.title}'",
            request_id=request_id
        )
        
    except Exception as e:
        # Log error with context using standardized logging
        log_error_with_context(
            logger, 
            e, 
            context=f"generate_similar_recommendations for book_id={book_id}",
            request_id=request_id
        )
        
        # Handle unexpected errors in recommendation generation
        context = create_error_context(
            request_id=request_id,
            book_id=book_id,
            operation="generate_similar_recommendations"
        )
        raise_internal_error("Failed to generate similar recommendations", e, context)


@router.post("/api/v1/recommendations/personalized", response_model=SuccessResponse[List[RecommendationItem]])
def get_personalized(payload: PersonalizedRequest, request: Request = None):
    """Return personalized recommendations based on optional seeds/context or trending fallback."""
    request_id = getattr(request.state, 'request_id', None) if request else None
    
    # Get indices with proper error handling
    try:
        idx = get_indexer_with_request_id(request_id).ensure_indices()
    except Exception as e:
        context = create_error_context(request_id=request_id, operation="ensure_indices")
        raise_upstream_error("inventory", e, "Failed to load book catalog")

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


@router.get("/api/v1/recommendations/trending", response_model=PaginatedResponse[RecommendationItem])
def get_trending(
    pagination: PaginationParams = Depends(create_pagination_params),
    request: Request = None
):
    """Return currently trending books based on recent stock_out popularity."""
    request_id = getattr(request.state, 'request_id', None) if request else None
    
    # Get indices with proper error handling
    try:
        idx = get_indexer_with_request_id(request_id).ensure_indices()
    except Exception as e:
        context = create_error_context(request_id=request_id, operation="ensure_indices")
        raise_upstream_error("inventory", e, "Failed to load book catalog")
    # Generate trending recommendations with bookverse-core pagination
    try:
        # Get all trending books sorted by popularity
        ranked_ids = sorted(idx.book_by_id.keys(), key=lambda i: idx.popularity.get(i, 0.0), reverse=True)
        
        # Filter to in-stock books first
        available_items: List[RecommendationItem] = []
        for bid in ranked_ids:
            try:
                b = idx.book_by_id[bid]
                if not b.availability.in_stock:
                    continue
                s = idx.popularity.get(bid, 0.0)
                available_items.append(build_recommendation_item(b, s, {"popularity": s}))
            except Exception as e:
                # Log individual item errors but continue processing
                logger.warning(f"Failed to process trending book {bid}: {e}", extra={"request_id": request_id})
                continue
        
        # Apply pagination to the available items
        total_items = len(available_items)
        start_idx = (pagination.page - 1) * pagination.size
        end_idx = start_idx + pagination.size
        paginated_items = available_items[start_idx:end_idx]
        
        # Create pagination metadata
        pagination_meta = create_pagination_meta(
            page=pagination.page,
            size=pagination.size,
            total=total_items
        )
        
        return create_paginated_response(
            data=paginated_items,
            pagination=pagination_meta,
            message=f"Generated {len(paginated_items)} trending recommendations (page {pagination.page} of {pagination_meta.total_pages})",
            request_id=request_id
        )
        
    except Exception as e:
        # Handle unexpected errors in trending generation
        context = create_error_context(
            request_id=request_id,
            operation="generate_trending_recommendations"
        )
        raise_internal_error("Failed to generate trending recommendations", e, context)


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


