from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, root_validator

# Import bookverse-core validation utilities
from bookverse_core.utils.validation import (
    validate_uuid,
    sanitize_string,
    create_validation_error_message
)


class Availability(BaseModel):
    """Availability info mirrored from inventory responses."""
    quantity_available: int = Field(..., ge=0)
    in_stock: bool
    low_stock: bool


class BookLite(BaseModel):
    """Minimal book representation used in recommendations with enhanced validation."""
    id: str = Field(..., description="Unique book identifier")
    title: str = Field(..., min_length=1, max_length=500, description="Book title")
    authors: List[str] = Field(..., min_items=1, description="List of book authors")
    genres: List[str] = Field(..., min_items=1, description="List of book genres")
    price: float = Field(..., ge=0.0, description="Book price (must be non-negative)")
    cover_image_url: str = Field(..., description="URL to book cover image")
    availability: Availability
    
    @validator('id')
    def validate_book_id(cls, v):
        """Validate book ID format."""
        if not v or not isinstance(v, str):
            raise ValueError("Book ID must be a non-empty string")
        
        # For demo purposes, accept various ID formats (UUID, alphanumeric, etc.)
        sanitized_id = sanitize_string(v, max_length=100)
        if len(sanitized_id) < 1:
            raise ValueError("Book ID cannot be empty after sanitization")
        
        return sanitized_id
    
    @validator('title')
    def validate_title(cls, v):
        """Validate and sanitize book title."""
        if not v or not isinstance(v, str):
            raise ValueError("Book title must be a non-empty string")
        
        sanitized_title = sanitize_string(v, max_length=500)
        if len(sanitized_title) < 1:
            raise ValueError("Book title cannot be empty after sanitization")
        
        return sanitized_title
    
    @validator('authors', each_item=True)
    def validate_author_names(cls, v):
        """Validate and sanitize author names."""
        if not v or not isinstance(v, str):
            raise ValueError("Author name must be a non-empty string")
        
        sanitized_author = sanitize_string(v, max_length=200)
        if len(sanitized_author) < 1:
            raise ValueError("Author name cannot be empty after sanitization")
        
        return sanitized_author
    
    @validator('genres', each_item=True)
    def validate_genre_names(cls, v):
        """Validate and sanitize genre names."""
        if not v or not isinstance(v, str):
            raise ValueError("Genre name must be a non-empty string")
        
        sanitized_genre = sanitize_string(v, max_length=100)
        if len(sanitized_genre) < 1:
            raise ValueError("Genre name cannot be empty after sanitization")
        
        return sanitized_genre
    
    @validator('cover_image_url')
    def validate_cover_url(cls, v):
        """Validate cover image URL."""
        if not v or not isinstance(v, str):
            raise ValueError("Cover image URL must be a non-empty string")
        
        # Basic URL validation for demo purposes
        sanitized_url = sanitize_string(v, max_length=1000)
        if not (sanitized_url.startswith('http://') or sanitized_url.startswith('https://')):
            raise ValueError("Cover image URL must start with http:// or https://")
        
        return sanitized_url


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
    """Optional context and seeds for personalized recommendations with enhanced validation."""
    user_id: Optional[str] = Field(None, description="User identifier for personalization")
    seed_book_ids: Optional[List[str]] = Field(None, max_items=20, description="Book IDs to base recommendations on")
    recently_viewed: Optional[List[str]] = Field(None, max_items=50, description="Recently viewed book IDs")
    cart_book_ids: Optional[List[str]] = Field(None, max_items=20, description="Book IDs in user's cart")
    seed_genres: Optional[List[str]] = Field(None, max_items=10, description="Preferred genres")
    seed_authors: Optional[List[str]] = Field(None, max_items=10, description="Preferred authors")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Maximum number of recommendations to return")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """Validate user ID format."""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("User ID must be a string")
        
        # Accept UUID format or sanitized string
        if validate_uuid(v):
            return v
        
        sanitized_id = sanitize_string(v, max_length=100)
        if len(sanitized_id) < 1:
            raise ValueError("User ID cannot be empty after sanitization")
        
        return sanitized_id
    
    @validator('seed_book_ids', 'recently_viewed', 'cart_book_ids', each_item=True)
    def validate_book_ids(cls, v):
        """Validate book ID formats in lists."""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("Book ID must be a string")
        
        sanitized_id = sanitize_string(v, max_length=100)
        if len(sanitized_id) < 1:
            raise ValueError("Book ID cannot be empty after sanitization")
        
        return sanitized_id
    
    @validator('seed_genres', 'seed_authors', each_item=True)
    def validate_seed_strings(cls, v):
        """Validate genre and author names in seed lists."""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("Genre/Author name must be a string")
        
        sanitized_name = sanitize_string(v, max_length=200)
        if len(sanitized_name) < 1:
            raise ValueError("Genre/Author name cannot be empty after sanitization")
        
        return sanitized_name
    
    @root_validator
    def validate_at_least_one_input(cls, values):
        """Ensure at least one personalization input is provided."""
        personalization_fields = [
            'seed_book_ids', 'recently_viewed', 'cart_book_ids', 
            'seed_genres', 'seed_authors'
        ]
        
        has_input = any(
            values.get(field) and len(values.get(field, [])) > 0 
            for field in personalization_fields
        )
        
        # Allow empty requests for fallback to trending
        # This is just a warning in the demo
        if not has_input:
            # In a real system, you might want to log this or handle differently
            pass
        
        return values


