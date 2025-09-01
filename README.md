# BookVerse Recommendations Service

Minimal FastAPI service for BookVerse. This service provides a simple, demo-friendly recommendation engine and is optimized to showcase CI/CD pipeline capabilities and multi-artifact delivery.

## Local run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Docker

```bash
docker build -t bookverse-recommendations:dev .
docker run -p 8000:8000 bookverse-recommendations:dev
```

## Deployment

This demo is deployed to Kubernetes as part of the single platform Helm chart release (multiple services in one chart). Interaction is via the web UI only; direct API calls with curl are not required.

## Overview

- Algorithm: simple rule-based scorer using genre/author overlap with a light popularity tie-breaker.
- Data source: `bookverse-inventory` service for books and transactions.
- Indices: in-memory inverted indices (genre/author) built on-demand; optional TTL cache.
- Multi-artifact: API image, worker image, versioned config, resources.

## Endpoints

- GET `/health` (basic)
- GET `/info`
- GET `/api/v1/recommendations/similar?book_id=<uuid>&limit=10`
- POST `/api/v1/recommendations/personalized` (see body below)
- GET `/api/v1/recommendations/trending?limit=10`
- GET `/api/v1/recommendations/health`

Note: In the demo, the web app consumes these endpoints; manual curl usage is not required.

## Multi-artifact build

This service intentionally produces multiple artifacts for CI/CD demo purposes:

- API image (Dockerfile)
- Worker image (Dockerfile.worker)
- Config bundle (`config/recommendations-settings.yaml`)
- Resources (`resources/stopwords.txt`)

Worker can be run with:

```bash
python -m app.worker
```

## Configuration

- Environment variables
  - `INVENTORY_BASE_URL`: base URL for inventory service (e.g., `http://inventory`).
  - `RECOMMENDATIONS_SETTINGS_PATH`: path to YAML settings, default `config/recommendations-settings.yaml`.
  - `RECO_TTL_SECONDS`: overrides TTL seconds via env (optional).
- Settings YAML
  - See `config/recommendations-settings.yaml` for weights/limits/features.

## CI/CD

GitHub Actions workflow builds both images, runs unit tests, and uploads config/resources as artifacts.
Optional steps (guarded by repo variables/secrets):

- Login and push: set `DOCKER_REGISTRY`, `DOCKER_USERNAME`, `DOCKER_PASSWORD`.
- Scan with Trivy: set `ENABLE_TRIVY=true`.
- Sign with Cosign (OIDC): set `ENABLE_COSIGN=true`.

## Testing

- Run unit tests locally:

```bash
pytest -q
```

Tests cover scoring behavior and basic API health/info.
