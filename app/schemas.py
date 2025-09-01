from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Availability(BaseModel):
    """Availability info mirrored from inventory responses."""
    quantity_available: int = Field(..., ge=0)
    in_stock: bool
    low_stock: bool


class BookLite(BaseModel):
    """Minimal book representation used in recommendations."""
    id: str
    title: str
    authors: List[str]
    genres: List[str]
    price: float
    cover_image_url: str
    availability: Availability


class RecommendationItem(BaseModel):
    """Recommendation item with score and factors for transparency."""
    id: str
    title: str
    authors: List[str]
    genres: List[str]
    price: float
    cover_image_url: str
    availability: Availability
    score: float
    score_factors: Dict[str, float] = {}


class RecommendationResponse(BaseModel):
    """List wrapper with meta for pagination/traceability."""
    recommendations: List[RecommendationItem]
    meta: Dict[str, Any]


class PersonalizedRequest(BaseModel):
    """Optional context and seeds for personalized recommendations."""
    user_id: Optional[str] = None
    seed_book_ids: Optional[List[str]] = None
    recently_viewed: Optional[List[str]] = None
    cart_book_ids: Optional[List[str]] = None
    seed_genres: Optional[List[str]] = None
    seed_authors: Optional[List[str]] = None
    limit: Optional[int] = Field(10, ge=1, le=50)


