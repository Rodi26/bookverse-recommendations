from fastapi import FastAPI
from .api import router as api_router

app = FastAPI(title="BookVerse Recommendations Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/info")
def info():
    return {"service": "recommendations", "version": "0.1.0"}


app.include_router(api_router)

