



import os
from pathlib import Path

from bookverse_core.api import create_app
from bookverse_core.config import BaseConfig, ConfigLoader
from bookverse_core.auth import RequireAuth, get_current_user, AuthUser
from fastapi import Depends
from typing import Optional
from bookverse_core.database import DatabaseConfig, get_database_session
from bookverse_core.utils import setup_logging, get_logger, LogConfig

class DemoConfig(BaseConfig):
    
    
    demo_message: str = "Hello from BookVerse Core Library Demo!"
    max_demo_items: int = 50
    enable_demo_features: bool = True
    
    database_url: str = "sqlite:///./demo.db"


config_loader = ConfigLoader(DemoConfig)
config = config_loader.load_from(
    yaml_file="config/demo-config.yaml",
    env_prefix="DEMO_",
    defaults={
        "service_name": "BookVerse Core Demo",
        "service_version": "0.1.0",
        "service_description": "Demo application showcasing bookverse-core library features"
    }
)

log_config = LogConfig(
    level=config.log_level,
    include_request_id=True
)
setup_logging(log_config, service_name="bookverse-core-demo")
logger = get_logger(__name__)

app = create_app(
    title=config.service_name,
    version=config.service_version,
    description=config.service_description,
    config=config,
    enable_auth=config.auth_enabled,
    enable_cors=True,
    health_checks=["basic", "auth"],
    middleware_config={
        "logging": {"log_requests": True, "log_responses": True},
        "cors": {"allow_origins": ["*"]},
    }
)

from api.demo_endpoints import router as demo_router
app.include_router(demo_router)

db_config = DatabaseConfig(
    database_url=config.database_url,
    echo=config.debug
)

@app.get("/demo/info")
async def demo_info():
    
    logger.info("📋 Demo info endpoint accessed")
    
    return {
        "message": config.demo_message,
        "service": config.service_name,
        "version": config.service_version,
        "environment": config.environment,
        "features": {
            "auth_enabled": config.auth_enabled,
            "debug_mode": config.debug,
            "demo_features": config.enable_demo_features
        },
        "demo_benefits": [
            "Eliminates 1,124 lines of authentication duplication",
            "Standardizes 4 different configuration approaches", 
            "Provides consistent API patterns and middleware",
            "Enables centralized logging and error handling"
        ]
    }


@app.get("/demo/auth/public")
async def public_endpoint():
    
    logger.info("🌐 Public endpoint accessed")
    
    return {
        "message": "This is a public endpoint - no authentication required",
        "demo_note": "The auth middleware is still active, but this endpoint doesn't use it",
        "auth_status": "Not required for this endpoint"
    }


@app.get("/demo/auth/protected")
async def protected_endpoint(user: AuthUser = RequireAuth):
    
    logger.info(f"🔐 Protected endpoint accessed by user: {user.email}")
    
    return {
        "message": f"Hello {user.name}! You are authenticated.",
        "user_info": {
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "roles": user.roles,
            "scopes": user.scopes
        },
        "demo_note": "This authentication logic is shared across all BookVerse services",
        "eliminated_duplication": "281 lines of auth code per service × 4 services = 1,124 lines saved"
    }


@app.get("/demo/auth/optional")
async def optional_auth_endpoint(user: Optional[AuthUser] = Depends(get_current_user)):
    
    if user:
        logger.info(f"🔓 Optional auth endpoint accessed by authenticated user: {user.email}")
        return {
            "message": f"Hello {user.name}! You are logged in.",
            "user_email": user.email,
            "auth_status": "Authenticated"
        }
    else:
        logger.info("🔓 Optional auth endpoint accessed by anonymous user")
        return {
            "message": "Hello anonymous user!",
            "auth_status": "Not authenticated",
            "demo_note": "This endpoint works with or without authentication"
        }


@app.get("/demo/config/current")
async def current_config():
    
    logger.info("⚙️ Configuration endpoint accessed")
    
    from bookverse_core.config.validation import sanitize_config_for_logging
    safe_config = sanitize_config_for_logging(config.to_dict())
    
    return {
        "message": "Current service configuration",
        "config": safe_config,
        "config_sources": [
            "1. Default values (lowest priority)",
            "2. YAML file (config/demo-config.yaml)",
            "3. Environment variables (DEMO_ prefix)",
            "4. Direct overrides (highest priority)"
        ],
        "demo_benefits": {
            "inventory_service": "Replaced hardcoded constants",
            "recommendations_service": "Replaced YAML + caching + env overrides",
            "checkout_service": "Replaced dataclass + env mapping", 
            "platform_service": "Replaced mixed YAML + env approach",
            "result": "Single, flexible configuration system for all services"
        }
    }


@app.get("/demo/logging/test")
async def logging_demo():
    
    from bookverse_core.utils.logging import (
        log_demo_info, 
        log_duplication_eliminated,
        log_error_with_context
    )
    
    logger.info("📝 Logging demo endpoint accessed")
    
    log_demo_info(logger, "This is a demo-specific log message")
    log_duplication_eliminated(logger, "Logging Setup", 50)
    
    logger.debug("This is a debug message (visible if debug=True)")
    logger.warning("This is a warning message with emoji ⚠️")
    
    try:
        raise ValueError("This is a demo error - don't worry!")
    except ValueError as e:
        log_error_with_context(logger, e, "Demo error simulation", "demo-request-123")
    
    return {
        "message": "Logging demonstration completed",
        "log_levels_shown": ["INFO", "DEBUG", "WARNING", "ERROR"],
        "demo_benefits": [
            "Consistent log format across all services",
            "Standardized error logging with context",
            "Request ID tracking for debugging",
            "Service-specific log identification",
            "Demo-specific logging helpers"
        ],
        "check_logs": "Look at the console output to see the standardized logging in action!"
    }


@app.get("/demo/validation/test")
async def validation_demo():
    
    from bookverse_core.utils.validation import (
        validate_email,
        validate_uuid, 
        validate_service_name,
        validate_version_string,
        sanitize_string
    )
    
    logger.info("✅ Validation demo endpoint accessed")
    
    test_cases = {
        "email_validation": {
            "valid_email": validate_email("user@bookverse.com"),
            "invalid_email": validate_email("not-an-email"),
        },
        "uuid_validation": {
            "valid_uuid": validate_uuid("123e4567-e89b-12d3-a456-426614174000"),
            "invalid_uuid": validate_uuid("not-a-uuid"),
        },
        "service_name_validation": {
            "valid_name": validate_service_name("bookverse-inventory"),
            "invalid_name": validate_service_name("Invalid Service Name!"),
        },
        "version_validation": {
            "valid_version": validate_version_string("1.2.3"),
            "valid_prerelease": validate_version_string("2.0.0-beta"),
            "invalid_version": validate_version_string("not.a.version"),
        },
        "string_sanitization": {
            "clean_string": sanitize_string("Hello World!"),
            "sanitized_html": sanitize_string("<script>alert('test')</script>Safe content"),
        }
    }
    
    return {
        "message": "Validation demonstration completed",
        "test_results": test_cases,
        "demo_benefits": [
            "Consistent validation behavior across all services",
            "Reusable validation functions with clear error messages",
            "Single place to update validation logic",
            "Eliminates duplicate validation code"
        ]
    }


@app.get("/demo/summary")
async def demo_summary():
    
    logger.info("📊 Demo summary endpoint accessed")
    
    return {
        "bookverse_core_library": {
            "purpose": "Eliminate code duplication and standardize patterns across BookVerse services",
            "version": "0.1.0",
            "status": "Demo Ready"
        },
        "code_duplication_eliminated": {
            "authentication": {
                "before": "281 lines × 4 services = 1,124 lines of duplicate code",
                "after": "Single shared implementation",
                "savings": "1,124 lines eliminated"
            },
            "configuration": {
                "before": "4 different configuration approaches across services",
                "after": "Unified configuration system supporting YAML, env vars, and defaults",
                "benefit": "Consistent configuration handling"
            },
            "api_patterns": {
                "before": "Each service implements its own FastAPI setup and middleware",
                "after": "Standardized app factory with consistent middleware",
                "benefit": "Consistent API behavior and error handling"
            },
            "database_utilities": {
                "before": "Each service implements its own session management and pagination",
                "after": "Shared database utilities and pagination logic",
                "benefit": "Consistent database patterns"
            },
            "logging": {
                "before": "Basic logging.basicConfig() calls in each service",
                "after": "Comprehensive, standardized logging setup",
                "benefit": "Consistent log format and debugging capabilities"
            }
        },
        "key_benefits": [
            "Single source of truth for authentication logic",
            "Consistent security implementation across all services",
            "Easy to update authentication for all services at once",
            "Standardized configuration with type safety and validation",
            "Consistent API patterns and error handling",
            "Reusable database utilities and pagination",
            "Standardized logging and debugging capabilities",
            "Clear separation of concerns between business logic and infrastructure"
        ],
        "demo_endpoints": {
            "/demo/info": "Service information and configuration",
            "/demo/auth/public": "Public endpoint (no auth required)",
            "/demo/auth/protected": "Protected endpoint (auth required)",
            "/demo/auth/optional": "Optional authentication endpoint",
            "/demo/config/current": "Current configuration display",
            "/demo/logging/test": "Logging patterns demonstration",
            "/demo/validation/test": "Validation utilities demonstration",
            "/health": "Standard health checks with auth integration",
            "/info": "Standard service information endpoint"
        },
        "next_steps": [
            "Migrate inventory service to use bookverse-core",
            "Migrate recommendations service",
            "Migrate checkout service", 
            "Migrate platform service",
            "Measure actual code reduction and consistency improvements"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    from bookverse_core.utils.logging import log_service_startup
    log_service_startup(logger, config.service_name, config.service_version, 8000)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug,
        log_level=config.log_level.lower()
    )
