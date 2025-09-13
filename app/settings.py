import os
from functools import lru_cache
from typing import Any, Dict

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # optional dependency


DEFAULTS = {
    "weights": {"genre": 1.0, "author": 0.25, "popularity": 0.10},
    "limits": {"default": 10, "max": 50},
    "features": {
        "filter_out_of_stock": True,
        "enable_cache": False,
        "ttl_seconds": 60,
    },
}


@lru_cache(maxsize=1)
def load_settings() -> Dict[str, Any]:
    """Load YAML settings and merge with defaults and environment overrides."""
    path = os.getenv("RECOMMENDATIONS_SETTINGS_PATH", "config/recommendations-settings.yaml")
    data: Dict[str, Any] = {}
    if yaml is not None and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            # Log the error instead of silently falling back
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to load YAML configuration from {path}: {e}")
            # Still fall back to empty dict but with proper error reporting
            data = {}
    else:
        # Log when configuration file is missing
        import logging
        logger = logging.getLogger(__name__)
        if yaml is None:
            logger.warning("YAML library not available, using default configuration")
        else:
            logger.warning(f"Configuration file not found at {path}, using default configuration")
    # Merge with defaults (shallow)
    merged = DEFAULTS.copy()
    for k, v in (data or {}).items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            mv = merged[k].copy()
            mv.update(v)
            merged[k] = mv
        else:
            merged[k] = v
    # Env overrides
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


