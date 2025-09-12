"""
JWT Authentication Module for BookVerse Inventory Service

Provides secure JWT token validation using OIDC/OAuth2 standards.
Supports both development and production configurations.
"""

import logging
import os
from typing import Optional
from datetime import datetime

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests

logger = logging.getLogger(__name__)

# Configuration
OIDC_AUTHORITY = os.getenv("OIDC_AUTHORITY", "https://dev-auth.bookverse.com")
OIDC_AUDIENCE = os.getenv("OIDC_AUDIENCE", "bookverse:api")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"

# Cache for OIDC configuration and keys
_oidc_config = None
_jwks = None
_jwks_last_updated = None
JWKS_CACHE_DURATION = 3600  # 1 hour in seconds

security = HTTPBearer(auto_error=False)


class AuthUser:
    """Represents an authenticated user with claims from JWT token"""
    
    def __init__(self, token_claims: dict):
        self.claims = token_claims
        self.user_id = token_claims.get("sub")
        self.email = token_claims.get("email")
        self.name = token_claims.get("name", self.email)
        self.roles = token_claims.get("roles", [])
        self.scopes = token_claims.get("scope", "").split()
    
    def has_scope(self, scope: str) -> bool:
        """Check if user has a specific scope"""
        return scope in self.scopes
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles
    
    def __str__(self):
        return f"AuthUser(id={self.user_id}, email={self.email})"


async def get_oidc_configuration() -> dict:
    """Fetch OIDC configuration from the authority"""
    global _oidc_config
    
    if _oidc_config is None:
        try:
            response = requests.get(f"{OIDC_AUTHORITY}/.well-known/openid_configuration", timeout=10)
            response.raise_for_status()
            _oidc_config = response.json()
            logger.info("✅ OIDC configuration loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to fetch OIDC configuration: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
    
    return _oidc_config


async def get_jwks() -> dict:
    """Fetch and cache JWKS (JSON Web Key Set) for token validation"""
    global _jwks, _jwks_last_updated
    
    current_time = datetime.now().timestamp()
    
    # Check if we need to refresh the cache
    if (_jwks is None or 
        _jwks_last_updated is None or 
        current_time - _jwks_last_updated > JWKS_CACHE_DURATION):
        
        try:
            oidc_config = await get_oidc_configuration()
            jwks_uri = oidc_config.get("jwks_uri")
            
            if not jwks_uri:
                raise ValueError("No jwks_uri found in OIDC configuration")
            
            response = requests.get(jwks_uri, timeout=10)
            response.raise_for_status()
            _jwks = response.json()
            _jwks_last_updated = current_time
            logger.info("✅ JWKS refreshed successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch JWKS: {e}")
            if _jwks is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable"
                )
            # Use cached version if available
            logger.warning("⚠️ Using cached JWKS due to fetch failure")
    
    return _jwks


def get_public_key(token_header: dict, jwks: dict) -> str:
    """Extract the public key for token verification"""
    kid = token_header.get("kid")
    if not kid:
        raise ValueError("Token header missing 'kid' field")
    
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    
    raise ValueError(f"No matching key found for kid: {kid}")


async def validate_jwt_token(token: str) -> AuthUser:
    """Validate JWT token and return authenticated user"""
    try:
        # Decode header to get key ID
        header = jwt.get_unverified_header(token)
        
        # Get JWKS for key validation
        jwks = await get_jwks()
        
        # Find the correct public key
        public_key = get_public_key(header, jwks)
        
        # Verify and decode the token
        claims = jwt.decode(
            token,
            public_key,
            algorithms=[JWT_ALGORITHM],
            audience=OIDC_AUDIENCE,
            issuer=OIDC_AUTHORITY
        )
        
        # Validate required claims
        if not claims.get("sub"):
            raise ValueError("Token missing 'sub' claim")
        
        # Check if token has required scope
        scopes = claims.get("scope", "").split()
        if "bookverse:api" not in scopes:
            raise ValueError("Token missing required 'bookverse:api' scope")
        
        logger.debug(f"✅ Token validated for user: {claims.get('email', claims.get('sub'))}")
        return AuthUser(claims)
        
    except JWTError as e:
        logger.warning(f"⚠️ JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"❌ Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthUser]:
    """FastAPI dependency to get the current authenticated user"""
    
    # If authentication is disabled, return a mock user for development
    if not AUTH_ENABLED:
        logger.debug("🔓 Authentication disabled - returning mock user")
        return AuthUser({
            "sub": "dev-user",
            "email": "dev@bookverse.com",
            "name": "Development User",
            "scope": "openid profile email bookverse:api",
            "roles": ["user", "admin"]
        })
    
    # If no credentials provided
    if not credentials:
        if DEVELOPMENT_MODE:
            logger.debug("🔧 Development mode - allowing unauthenticated access")
            return None
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Validate the token
    return await validate_jwt_token(credentials.credentials)


async def require_authentication(
    user: Optional[AuthUser] = Depends(get_current_user)
) -> AuthUser:
    """FastAPI dependency that requires authentication"""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def require_scope(scope: str):
    """Factory function to create a dependency that requires a specific scope"""
    async def scope_checker(user: AuthUser = Depends(require_authentication)) -> AuthUser:
        if not user.has_scope(scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {scope}"
            )
        return user
    return scope_checker


def require_role(role: str):
    """Factory function to create a dependency that requires a specific role"""
    async def role_checker(user: AuthUser = Depends(require_authentication)) -> AuthUser:
        if not user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {role}"
            )
        return user
    return role_checker


# Common dependencies for different access levels
RequireAuth = Depends(require_authentication)
RequireUser = Depends(get_current_user)
RequireApiScope = Depends(require_scope("bookverse:api"))


def get_auth_status() -> dict:
    """Get authentication service status for health checks"""
    return {
        "auth_enabled": AUTH_ENABLED,
        "development_mode": DEVELOPMENT_MODE,
        "oidc_authority": OIDC_AUTHORITY,
        "audience": OIDC_AUDIENCE,
        "algorithm": JWT_ALGORITHM,
        "jwks_cached": _jwks is not None,
        "config_cached": _oidc_config is not None
    }


async def test_auth_connection() -> dict:
    """Test authentication service connectivity"""
    try:
        config = await get_oidc_configuration()
        jwks = await get_jwks()
        return {
            "status": "healthy",
            "oidc_config_loaded": bool(config),
            "jwks_loaded": bool(jwks),
            "keys_count": len(jwks.get("keys", [])) if jwks else 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
