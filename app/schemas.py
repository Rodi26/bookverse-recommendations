from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator

from bookverse_core.utils.validation import (
    validate_uuid,
    sanitize_string,
    create_validation_error_message
)


class Availability(BaseModel):
    quantity_available: int = Field(..., ge=0)
    in_stock: bool
    low_stock: bool


class BookLite(BaseModel):
    id: str = Field(..., description="Unique book identifier")
    title: str = Field(..., min_length=1, max_length=500, description="Book title")
    authors: List[str] = Field(..., min_length=1, description="List of book authors")
    genres: List[str] = Field(..., min_length=1, description="List of book genres")
    price: float = Field(..., ge=0.0, description="Book price (must be non-negative)")
    cover_image_url: str = Field(..., description="URL to book cover image")
    availability: Availability
    
    @field_validator('id')
    @classmethod
    def validate_book_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Book ID must be a non-empty string")
        
        sanitized_id = sanitize_string(v, max_length=100)
        if len(sanitized_id) < 1:
            raise ValueError("Book ID cannot be empty after sanitization")
        
        return sanitized_id
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Book title must be a non-empty string")
        
        sanitized_title = sanitize_string(v, max_length=500)
        if len(sanitized_title) < 1:
            raise ValueError("Book title cannot be empty after sanitization")
        
        return sanitized_title
    
    @field_validator('authors')
    @classmethod
    def validate_author_names(cls, v):
        if not isinstance(v, list):
            raise ValueError("Authors must be a list")
        
        validated_authors = []
        for author in v:
            if not author or not isinstance(author, str):
                raise ValueError("Author name must be a non-empty string")
            
            sanitized_author = sanitize_string(author, max_length=200)
            if len(sanitized_author) < 1:
                raise ValueError("Author name cannot be empty after sanitization")
            
            validated_authors.append(sanitized_author)
        
        return validated_authors
    
    @field_validator('genres')
    @classmethod
    def validate_genre_names(cls, v):
        if not isinstance(v, list):
            raise ValueError("Genres must be a list")
        
        validated_genres = []
        for genre in v:
            if not genre or not isinstance(genre, str):
                raise ValueError("Genre name must be a non-empty string")
            
            sanitized_genre = sanitize_string(genre, max_length=100)
            if len(sanitized_genre) < 1:
                raise ValueError("Genre name cannot be empty after sanitization")
            
            validated_genres.append(sanitized_genre)
        
        return validated_genres
    
    @field_validator('cover_image_url')
    @classmethod
    def validate_cover_url(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Cover image URL must be a non-empty string")
        
        sanitized_url = sanitize_string(v, max_length=1000)
        if not (sanitized_url.startswith('http://') or sanitized_url.startswith('https://')):
            raise ValueError("Cover image URL must start with http:// or https://")
        
        return sanitized_url


class RecommendationItem(BaseModel):
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
    recommendations: List[RecommendationItem]
    meta: Dict[str, Any]


class PersonalizedRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="User identifier for personalization")
    seed_book_ids: Optional[List[str]] = Field(None, max_length=20, description="Book IDs to base recommendations on")
    recently_viewed: Optional[List[str]] = Field(None, max_length=50, description="Recently viewed book IDs")
    cart_book_ids: Optional[List[str]] = Field(None, max_length=20, description="Book IDs in user's cart")
    seed_genres: Optional[List[str]] = Field(None, max_length=10, description="Preferred genres")
    seed_authors: Optional[List[str]] = Field(None, max_length=10, description="Preferred authors")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Maximum number of recommendations to return")
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("User ID must be a string")
        
        if validate_uuid(v):
            return v
        
        sanitized_id = sanitize_string(v, max_length=100)
        if len(sanitized_id) < 1:
            raise ValueError("User ID cannot be empty after sanitization")
        
        return sanitized_id
    
    @field_validator('seed_book_ids', 'recently_viewed', 'cart_book_ids')
    @classmethod
    def validate_book_ids(cls, v):
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError("Book IDs must be a list")
        
        validated_ids = []
        for book_id in v:
            if not isinstance(book_id, str):
                raise ValueError("Book ID must be a string")
            
            sanitized_id = sanitize_string(book_id, max_length=100)
            if len(sanitized_id) < 1:
                raise ValueError("Book ID cannot be empty after sanitization")
            
            validated_ids.append(sanitized_id)
        
        return validated_ids
    
    @field_validator('seed_genres', 'seed_authors')
    @classmethod
    def validate_seed_strings(cls, v):
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError("Genre/Author names must be a list")
        
        validated_names = []
        for name in v:
            if not isinstance(name, str):
                raise ValueError("Genre/Author name must be a string")
            
            sanitized_name = sanitize_string(name, max_length=200)
            if len(sanitized_name) < 1:
                raise ValueError("Genre/Author name cannot be empty after sanitization")
            
            validated_names.append(sanitized_name)
        
        return validated_names
    
    @model_validator(mode='after')
    def validate_at_least_one_input(self):
        personalization_fields = [
            'seed_book_ids', 'recently_viewed', 'cart_book_ids', 
            'seed_genres', 'seed_authors'
        ]
        
        has_input = any(
            getattr(self, field) and len(getattr(self, field, [])) > 0 
            for field in personalization_fields
        )
        
        if not has_input:
            pass
        
        return self


