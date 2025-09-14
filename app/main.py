"""
BookVerse Recommendations Service - Main Application

MIGRATION SUCCESS: Now using bookverse-core app factory for standardized FastAPI setup!

Benefits of this migration:
✅ Standardized middleware stack (CORS, auth, logging, error handling, request ID)
✅ Kubernetes-ready health endpoints (/health/live, /health/ready)
✅ Consistent error handling and logging across all services
✅ Built-in authentication middleware integration
✅ Standardized /info endpoint with service metadata
"""

import os
import hashlib
from fastapi import FastAPI

# Import bookverse-core app factory, configuration, logging, middleware, and health
from bookverse_core.api.app_factory import create_app
from bookverse_core.api.middleware import RequestIDMiddleware, RequestLoggingMiddleware
from bookverse_core.api.health import create_health_router
from bookverse_core.config import BaseConfig
from bookverse_core.utils.logging import (
    setup_logging,
    LogConfig,
    get_logger,
    log_service_startup
)

from .api import router as api_router
from .settings import get_config, load_settings

# Setup standardized logging first
log_config = LogConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    include_request_id=True
)
setup_logging(log_config, "recommendations")

# Get logger for this module
logger = get_logger(__name__)

# Create configuration instance using enhanced settings
config = get_config()

# Log service startup
service_version = os.getenv("SERVICE_VERSION", "0.1.0-dev")
log_service_startup(logger, "BookVerse Recommendations Service", service_version)

# Create FastAPI app using bookverse-core factory
app = create_app(
    title="BookVerse Recommendations Service",
    version=os.getenv("SERVICE_VERSION", "0.1.0-dev"),
    description="AI-powered book recommendation engine for BookVerse platform",
    config=config,
    enable_auth=config.auth_enabled,
    enable_cors=True,
    health_checks=["basic", "auth"],  # Enable basic and auth health checks
    middleware_config={
        "cors": {
            "allow_origins": ["*"],  # In production, specify actual origins
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        },
        "logging": {
            "log_request_body": False,  # Don't log request bodies for performance
            "log_response_body": False,  # Don't log response bodies for performance
        },
        "request_id": {
            "header_name": "X-Request-ID",  # Standard request ID header
            "generate_if_missing": True,    # Auto-generate if not provided
        },
        "request_logging": {
            "enabled": True,                # Enable request/response logging
            "log_level": "INFO",           # Log level for requests
            "include_headers": False,       # Don't log headers for security
        }
    }
)

# Add bookverse-core middleware for enhanced request tracing and logging
app.add_middleware(RequestIDMiddleware, header_name="X-Request-ID")
app.add_middleware(RequestLoggingMiddleware, 
                  log_level="INFO", 
                  include_headers=False,
                  log_request_body=False,
                  log_response_body=False)

logger.info("✅ Enhanced middleware added: Request ID tracking and request logging")

# Add custom /info endpoint with recommendations-specific metadata
@app.get("/info")
def get_recommendations_info():
    """
    Enhanced service information endpoint with recommendations-specific details.
    
    This extends the standard bookverse-core /info endpoint with service-specific metadata.
    """
    # Get base service info
    base_info = {
        "service": "recommendations",
        "version": os.getenv("SERVICE_VERSION", "0.1.0-dev"),
        "description": "AI-powered book recommendation engine",
        "environment": config.environment,
        "auth_enabled": config.auth_enabled,
    }
    
    # Add recommendations-specific metadata
    image_tag = os.getenv("IMAGE_TAG", os.getenv("GIT_SHA", "unknown"))
    app_version = os.getenv("APP_VERSION", "unknown")
    settings_path = os.getenv("RECOMMENDATIONS_SETTINGS_PATH", "config/recommendations-settings.yaml")
    settings_loaded = os.path.exists(settings_path)
    settings_checksum = None
    
    try:
        if settings_loaded:
            with open(settings_path, "rb") as f:
                settings_checksum = hashlib.sha256(f.read()).hexdigest()
    except Exception:
        settings_checksum = None
    
    resource_path = "resources/stopwords.txt"
    resource_loaded = os.path.exists(resource_path)
    resource_checksum = None
    
    try:
        if resource_loaded:
            with open(resource_path, "rb") as f:
                resource_checksum = hashlib.sha256(f.read()).hexdigest()
    except Exception:
        resource_checksum = None
    
    s = load_settings()
    
    # Combine base info with service-specific details
    base_info.update({
        "build": {"imageTag": image_tag, "appVersion": app_version},
        "config": {
            "path": config.config_path,
            "loaded": settings_loaded, 
            "sha256": settings_checksum,
            "validation": "pydantic",
            "environment_overrides": "RECO_* supported"
        },
        "resources": {"stopwordsPath": resource_path, "loaded": resource_loaded, "sha256": resource_checksum},
        "algorithm_config": {
            "weights": {
                "genre": config.weights.genre,
                "author": config.weights.author,
                "popularity": config.weights.popularity,
            },
            "limits": {
                "default": config.limits.default,
                "max": config.limits.max,
            },
            "features": {
                "filter_out_of_stock": config.features.filter_out_of_stock,
                "enable_cache": config.features.enable_cache,
                "ttl_seconds": config.features.ttl_seconds,
            }
        },
        "middleware": {
            "cors_enabled": True,
            "auth_enabled": config.auth_enabled,
            "logging_enabled": True,
            "error_handling_enabled": True,
            "request_id_enabled": True,
        }
    })
    
    return base_info


# Include the API router
app.include_router(api_router)

# Add standardized health check router (bookverse-core) alongside existing health endpoint
health_router = create_health_router(
    service_name="BookVerse Recommendations Service",
    service_version=os.getenv("SERVICE_VERSION", "0.1.0-dev"),
    health_checks=["basic", "auth"]  # Match the health checks from create_app
)
app.include_router(health_router, prefix="/health", tags=["health"])

logger.info("✅ Standardized health endpoints added: /health/live, /health/ready, /health/status")

# Note: Health endpoints (/health, /health/live, /health/ready) are automatically 
# added by the bookverse-core app factory, no need to define them manually!

