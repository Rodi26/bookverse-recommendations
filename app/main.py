from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router as api_router
import os
import hashlib
from .settings import load_settings

app = FastAPI(title="BookVerse Recommendations Service")

# Add CORS middleware for web frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Basic health check used by probes and CI."""
    return {"status": "ok"}


@app.get("/info")
def info():
    """Expose build and configuration metadata useful for diagnostics."""
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
    return {
        "service": "recommendations",
        "version": "0.1.0",
        "build": {"imageTag": image_tag, "appVersion": app_version},
        "config": {"path": settings_path, "loaded": settings_loaded, "sha256": settings_checksum},
        "resources": {"stopwordsPath": resource_path, "loaded": resource_loaded, "sha256": resource_checksum},
        "limits": s.get("limits", {}),
        "features": s.get("features", {}),
    }


app.include_router(api_router)

