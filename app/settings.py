"""
BookVerse Recommendations Service - Configuration Management

MIGRATION SUCCESS: Enhanced with bookverse-core configuration patterns!

Benefits of this migration:
✅ Standardized configuration loading with validation
✅ Environment variable support with prefixes
✅ Type-safe configuration with Pydantic models
✅ Consistent configuration patterns across services
✅ Built-in validation and error handling
"""

import os
from functools import lru_cache
from typing import Any, Dict, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # optional dependency

# Import bookverse-core configuration
from bookverse_core.config import BaseConfig, ConfigLoader
from pydantic import BaseModel, Field


class WeightsConfig(BaseModel):
    """Configuration for recommendation scoring weights."""
    genre: float = Field(default=1.0, ge=0.0, le=10.0, description="Genre matching weight")
    author: float = Field(default=0.25, ge=0.0, le=10.0, description="Author matching weight")
    popularity: float = Field(default=0.10, ge=0.0, le=10.0, description="Popularity score weight")


class LimitsConfig(BaseModel):
    """Configuration for recommendation limits."""
    default: int = Field(default=10, ge=1, le=100, description="Default number of recommendations")
    max: int = Field(default=50, ge=1, le=100, description="Maximum number of recommendations")


class FeaturesConfig(BaseModel):
    """Configuration for recommendation features."""
    filter_out_of_stock: bool = Field(default=True, description="Filter out-of-stock items")
    enable_cache: bool = Field(default=False, description="Enable recommendation caching")
    ttl_seconds: int = Field(default=60, ge=1, le=3600, description="Cache TTL in seconds")


class RecommendationsConfig(BaseConfig):
    """
    Enhanced configuration for recommendations service using bookverse-core patterns.
    
    This extends BaseConfig to provide service-specific configuration with validation.
    """
    
    # Service-specific configuration
    weights: WeightsConfig = Field(default_factory=WeightsConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    
    # Service metadata
    service_name: str = Field(default="recommendations")
    api_version: str = Field(default="v1")
    
    # Configuration file path
    config_path: Optional[str] = Field(
        default=None,
        description="Path to YAML configuration file"
    )
    
    def __init__(self, **kwargs):
        # Set config path from environment if not provided
        if 'config_path' not in kwargs:
            kwargs['config_path'] = os.getenv(
                "RECOMMENDATIONS_SETTINGS_PATH", 
                "config/recommendations-settings.yaml"
            )
        
        super().__init__(**kwargs)
    
    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> 'RecommendationsConfig':
        """
        Load configuration from YAML file with environment variable overrides.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Loaded and validated configuration
        """
        if config_path is None:
            config_path = os.getenv("RECOMMENDATIONS_SETTINGS_PATH", "config/recommendations-settings.yaml")
        
        # Load YAML configuration if file exists
        yaml_data = {}
        if yaml is not None and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    yaml_data = yaml.safe_load(f) or {}
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to load YAML configuration from {config_path}: {e}")
        
        # Apply environment variable overrides
        env_overrides = {}
        
        # Support RECO_ prefixed environment variables
        for key, value in os.environ.items():
            if key.startswith("RECO_"):
                config_key = key[5:].lower()  # Remove RECO_ prefix
                
                # Handle nested configuration
                if config_key == "ttl_seconds":
                    env_overrides.setdefault("features", {})["ttl_seconds"] = int(value)
                elif config_key == "default_limit":
                    env_overrides.setdefault("limits", {})["default"] = int(value)
                elif config_key == "max_limit":
                    env_overrides.setdefault("limits", {})["max"] = int(value)
                elif config_key == "genre_weight":
                    env_overrides.setdefault("weights", {})["genre"] = float(value)
                elif config_key == "author_weight":
                    env_overrides.setdefault("weights", {})["author"] = float(value)
                elif config_key == "popularity_weight":
                    env_overrides.setdefault("weights", {})["popularity"] = float(value)
        
        # Merge YAML and environment overrides
        config_data = {**yaml_data, **env_overrides}
        config_data["config_path"] = config_path
        
        return cls(**config_data)


# Global configuration instance
_config_instance: Optional[RecommendationsConfig] = None


def get_config() -> RecommendationsConfig:
    """
    Get the global configuration instance.
    
    Returns:
        Loaded and validated configuration
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = RecommendationsConfig.load_from_file()
    return _config_instance


def reload_config() -> RecommendationsConfig:
    """
    Reload the configuration from file.
    
    Returns:
        Reloaded configuration
    """
    global _config_instance
    _config_instance = RecommendationsConfig.load_from_file()
    return _config_instance


@lru_cache(maxsize=1)
def load_settings() -> Dict[str, Any]:
    """Load YAML settings using bookverse-core configuration loader."""
    path = os.getenv("RECOMMENDATIONS_SETTINGS_PATH", "config/recommendations-settings.yaml")
    
    # Use bookverse-core configuration loader
    loader = ConfigLoader(RecommendationsConfig)
    config = loader.load_from(
        yaml_file=path,
        defaults=DEFAULTS,
        env_prefix="RECO_"  # Support RECO_TTL_SECONDS etc.
    )
    
    return config.model_dump()


# Keep legacy function for rollback capability during migration
def load_settings_legacy() -> Dict[str, Any]:
    """Original load_settings implementation - kept for rollback."""
    path = os.getenv("RECOMMENDATIONS_SETTINGS_PATH", "config/recommendations-settings.yaml")
    data: Dict[str, Any] = {}
    if yaml is not None and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to load YAML configuration from {path}: {e}")
            data = {}
    else:
        import logging
        logger = logging.getLogger(__name__)
        if yaml is None:
            logger.warning("YAML library not available, using default configuration")
        else:
            logger.warning(f"Configuration file not found at {path}, using default configuration")
    
    merged = DEFAULTS.copy()
    for k, v in (data or {}).items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            mv = merged[k].copy()
            mv.update(v)
            merged[k] = mv
        else:
            merged[k] = v
    
    ttl_env = os.getenv("RECO_TTL_SECONDS")
    if ttl_env:
        try:
            merged.setdefault("features", {})["ttl_seconds"] = int(ttl_env)
        except ValueError:
            pass
    return merged


def get_weights() -> Dict[str, float]:
    """Return scoring weights as floats (genre, author, popularity)."""
    s = load_settings()
    w = s.get("weights", {})
    return {
        "genre": float(w.get("genre", DEFAULTS["weights"]["genre"])),
        "author": float(w.get("author", DEFAULTS["weights"]["author"])),
        "popularity": float(w.get("popularity", DEFAULTS["weights"]["popularity"])),
    }


def get_ttl_seconds() -> int:
    """Return TTL seconds for cache freshness checks."""
    s = load_settings()
    return int(s.get("features", {}).get("ttl_seconds", DEFAULTS["features"]["ttl_seconds"]))


def get_limits() -> Dict[str, int]:
    """Return default and max limits for recommendation list size."""
    s = load_settings()
    l = s.get("limits", {})
    return {"default": int(l.get("default", 10)), "max": int(l.get("max", 50))}


def filter_out_of_stock_enabled() -> bool:
    """Return True if out-of-stock items should be filtered from results."""
    s = load_settings()
    return bool(s.get("features", {}).get("filter_out_of_stock", True))


