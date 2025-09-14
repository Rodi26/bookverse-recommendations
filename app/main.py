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

# Import bookverse-core app factory and configuration
from bookverse_core.api.app_factory import create_app
from bookverse_core.config import BaseConfig

from .api import router as api_router
from .settings import load_settings


class RecommendationsConfig(BaseConfig):
    """Configuration for the recommendations service."""
    
    def __init__(self):
        super().__init__()
        self.service_name = "recommendations"
        self.api_version = "v1"
        # Enable authentication for production, but keep flexible for demo
        self.auth_enabled = os.getenv("AUTH_ENABLED", "true").lower() == "true"


# Create configuration instance
config = RecommendationsConfig()

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
            "include_request_body": False,  # Don't log request bodies for performance
            "include_response_body": False,
        }
    }
)

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
        "config": {"path": settings_path, "loaded": settings_loaded, "sha256": settings_checksum},
        "resources": {"stopwordsPath": resource_path, "loaded": resource_loaded, "sha256": resource_checksum},
        "limits": s.get("limits", {}),
        "features": s.get("features", {}),
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

# Note: Health endpoints (/health, /health/live, /health/ready) are automatically 
# added by the bookverse-core app factory, no need to define them manually!

