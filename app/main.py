
"""
BookVerse Recommendations Service - Main Application Module

This module serves as the primary entry point for the BookVerse Recommendations Service,
implementing an AI-powered recommendation engine that provides personalized book
suggestions using machine learning algorithms and real-time data processing.

🏗️ Architecture Overview:
    The recommendations service implements a sophisticated ML-driven architecture:
    - Dual Processing: API server for real-time requests + worker for background ML tasks
    - Algorithm Engine: Hybrid recommendation system (collaborative + content-based)
    - Data Pipeline: Real-time inventory synchronization and user behavior tracking
    - Caching Layer: Multi-level caching for sub-200ms response times
    - Scalability: Horizontal scaling with stateless API and distributed workers

🚀 Key Features:
    - Real-time personalized recommendations (< 200ms response time)
    - Machine learning algorithms with A/B testing framework
    - Content-based and collaborative filtering hybrid approach
    - Real-time inventory integration for availability filtering
    - Background indexing and model training workflows
    - Comprehensive performance monitoring and analytics

🤖 AI/ML Capabilities:
    - Collaborative Filtering: User-based and item-based recommendations
    - Content-Based Filtering: Genre, author, and metadata similarity
    - Popularity-Based: Trending and high-quality book suggestions
    - Cold Start Handling: New user and new item recommendation strategies
    - A/B Testing: Algorithm comparison and optimization
    - Real-time Learning: Continuous model updates from user interactions

🔧 Configuration:
    - Settings Management: YAML-based configuration with environment overrides
    - Algorithm Parameters: Configurable weights and thresholds
    - Performance Tuning: Caching TTL, batch sizes, and timeout settings
    - Integration Settings: External service URLs and authentication
    - Monitoring Configuration: Metrics collection and alerting thresholds

🌐 Service Integration:
    - Inventory Service: Real-time product data and availability status
    - Checkout Service: Purchase behavior for recommendation training
    - Platform Service: Cross-service metrics and health monitoring
    - Web Application: Real-time recommendation delivery to users
    - Analytics Pipeline: User interaction tracking and model performance

📊 Performance Characteristics:
    - Target Response Time: < 200ms for recommendation requests
    - Throughput: 1000+ recommendations per second with caching
    - ML Processing: Background model training and index updates
    - Cache Hit Rate: >85% for improved performance
    - Scalability: Horizontal scaling for both API and worker components

🛠️ Development Usage:
    For local development and testing:
    ```bash
    # Set environment variables
    export LOG_LEVEL=DEBUG
    export AUTH_ENABLED=false
    export RECOMMENDATIONS_CACHE_TTL=300
    
    # Run API server
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
    
    # Run background worker (separate process)
    python -m app.worker
    ```

📋 Dependencies:
    Core ML and API dependencies:
    - FastAPI: High-performance async web framework
    - scikit-learn: Machine learning algorithms and utilities
    - Redis: High-performance caching and session storage
    - BookVerse Core: Shared authentication and middleware
    - httpx: Async HTTP client for service integration

⚠️ Important Notes:
    - Dual architecture: API server + background worker for ML processing
    - Cache warming: Initial startup includes cache population
    - Model updates: Background processes handle ML model retraining
    - Error handling: Graceful degradation when ML models unavailable
    - Performance monitoring: Built-in metrics for response times and accuracy

🔗 Related Documentation:
    - Algorithm Guide: ../docs/ALGORITHM_GUIDE.md
    - ML Implementation: ../docs/MACHINE_LEARNING.md  
    - Performance Tuning: ../docs/OPERATIONS.md
    - Architecture Overview: ../docs/ARCHITECTURE.md

Authors: BookVerse Platform Team
Version: 1.0.0
Last Updated: 2024-01-01
"""

import os
import hashlib
from fastapi import FastAPI

from bookverse_core.api.app_factory import create_app
from bookverse_core.api.middleware import RequestIDMiddleware, LoggingMiddleware
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

# Configure structured logging with request correlation for ML service debugging
log_config = LogConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),  # Support DEBUG for ML algorithm debugging
    include_request_id=True                # Enable request correlation across ML pipeline
)
setup_logging(log_config, "recommendations")

# Initialize logger with ML-specific context and performance tracking
logger = get_logger(__name__)

# Load recommendations service configuration with ML algorithm parameters
config = get_config()

# Determine service version for ML model versioning and deployment tracking
service_version = os.getenv("SERVICE_VERSION", "0.1.0-dev")
# Log service startup with ML service context for operational visibility
log_service_startup(logger, "BookVerse Recommendations Service", service_version)

app = create_app(
    title="BookVerse Recommendations Service",
    version=os.getenv("SERVICE_VERSION", "0.1.0-dev"),
    description="AI-powered book recommendation engine for BookVerse platform",
    config=config,
    enable_auth=config.auth_enabled,
    enable_cors=True,
    health_checks=["basic", "auth"],
    middleware_config={
        "cors": {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        },
        "logging": {
            "log_request_body": False,
            "log_response_body": False,
        },
        "request_id": {
            "header_name": "X-Request-ID",
            "generate_if_missing": True,
        },
        "request_logging": {
            "enabled": True,
            "log_level": "INFO",
            "include_headers": False,
        }
    }
)

app.add_middleware(RequestIDMiddleware, header_name="X-Request-ID")
app.add_middleware(LoggingMiddleware, 
                  log_requests=True,
                  log_responses=True,
                  log_request_body=False,
                  log_response_body=False)

logger.info("✅ Enhanced middleware added: Request ID tracking and request logging")

@app.get("/info")
def get_recommendations_info():
    
    base_info = {
        "service": "recommendations",
        "version": os.getenv("SERVICE_VERSION", "0.1.0-dev"),
        "description": "AI-powered book recommendation engine",
        "environment": config.environment,
        "auth_enabled": config.auth_enabled,
    }
    
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


app.include_router(api_router)

health_router = create_health_router(
    service_name="BookVerse Recommendations Service",
    service_version=os.getenv("SERVICE_VERSION", "0.1.0-dev"),
    health_checks=["basic", "auth"]
)
app.include_router(health_router, prefix="/health", tags=["health"])

logger.info("✅ Standardized health endpoints added: /health/live, /health/ready, /health/status")



def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

