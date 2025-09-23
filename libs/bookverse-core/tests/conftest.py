

import os
import tempfile
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bookverse_core.config import BaseConfig, ConfigLoader
from bookverse_core.database import create_database_engine, DatabaseConfig


class TestConfig(BaseConfig):
    service_name: str = "Test Service"
    service_version: str = "0.1.0-test"
    environment: str = "test"
    debug: bool = True
    log_level: str = "DEBUG"
    
    database_url: str = "sqlite:///:memory:"
    
    auth_enabled: bool = True
    development_mode: bool = True
    oidc_authority: str = "https://test-auth.example.com"
    oidc_audience: str = "test:api"


@pytest.fixture
def test_config() -> TestConfig:
    return TestConfig()


@pytest.fixture
def mock_oidc_config():
    return {
        "issuer": "https://test-auth.example.com",
        "authorization_endpoint": "https://test-auth.example.com/auth",
        "token_endpoint": "https://test-auth.example.com/token",
        "userinfo_endpoint": "https://test-auth.example.com/userinfo",
        "jwks_uri": "https://test-auth.example.com/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"]
    }


@pytest.fixture
def mock_jwks():
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": "test-key-id",
                "n": "test-modulus",
                "e": "AQAB",
                "alg": "RS256"
            }
        ]
    }


@pytest.fixture
def mock_jwt_token():
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5LWlkIn0.eyJzdWIiOiJ0ZXN0LXVzZXItaWQiLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIiwicm9sZXMiOlsidXNlciJdLCJzY29wZXMiOlsicmVhZCJdLCJpc3MiOiJodHRwczovL3Rlc3QtYXV0aC5leGFtcGxlLmNvbSIsImF1ZCI6InRlc3Q6YXBpIiwiaWF0IjoxNjAwMDAwMDAwLCJleHAiOjk5OTk5OTk5OTl9.test-signature"


@pytest.fixture
def mock_auth_user():
    from bookverse_core.auth import AuthUser
    return AuthUser(
        user_id="test-user-id",
        email="test@test.com",
        name="Test User",
        roles=["user"],
        scopes=["read"]
    )


@pytest.fixture
def temp_config_file():
    import tempfile
    import os
    config_content = """
service_name: "Test Service from YAML"
debug: false
log_level: "INFO"
test_setting: "from_yaml"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def test_db_engine():
    from bookverse_core.database.config import DatabaseConfig
    from bookverse_core.database.engine import create_database_engine
    config = DatabaseConfig(database_url="sqlite:///:memory:")
    engine = create_database_engine(config)
    return engine


@pytest.fixture
def test_db_session(test_db_engine):
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def mock_requests():
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:
        yield {
            'get': mock_get,
            'post': mock_post
        }


@pytest.fixture
def demo_app_client():
    import sys
    import os
    
    app_path = os.path.join(os.path.dirname(__file__), '..', 'app')
    sys.path.insert(0, app_path)
    
    try:
        from main import app
        
        with TestClient(app) as client:
            yield client
    finally:
        if app_path in sys.path:
            sys.path.remove(app_path)


@pytest.fixture(autouse=True)
def reset_caches():
    from bookverse_core.auth.oidc import get_oidc_configuration, get_jwks
    if hasattr(get_oidc_configuration, 'cache_clear'):
        get_oidc_configuration.cache_clear()
    if hasattr(get_jwks, 'cache_clear'):
        get_jwks.cache_clear()
    
    try:
        from bookverse_core.config.loaders import ConfigLoader
        for attr_name in dir(ConfigLoader):
            attr = getattr(ConfigLoader, attr_name)
            if hasattr(attr, 'cache_clear'):
                attr.cache_clear()
    except Exception:
        pass


@pytest.fixture
def sample_books():
    return [
        {
            "id": 1,
            "title": "Test Book 1",
            "author": "Test Author 1",
            "isbn": "978-0-123456-78-9",
            "category": "fiction"
        },
        {
            "id": 2,
            "title": "Test Book 2", 
            "author": "Test Author 2",
            "isbn": "978-0-123456-79-6",
            "category": "non-fiction"
        },
        {
            "id": 3,
            "title": "Test Book 3",
            "author": "Test Author 3", 
            "isbn": "978-0-123456-80-2",
            "category": "science"
        }
    ]


@pytest.fixture(autouse=True)
def setup_test_environment():
    test_env = {
        "TESTING": "true",
        "LOG_LEVEL": "DEBUG",
        "AUTH_ENABLED": "true",
        "DEVELOPMENT_MODE": "true"
    }
    
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value
