# BookVerse Recommendations Service

This repository is part of the JFrog AppTrust BookVerse demo. The demo illustrates a secure software supply chain using the JFrog Platform: AppTrust lifecycle and promotion, signed SBOM/provenance, Xray policies, and GitHub Actions OIDC for passwordless CI/CD.

## What this service does
The Recommendations service provides AI-assisted book recommendations based on user behavior and catalog metadata. In the demo, it serves as a Python microservice packaged as a Python distribution and a Docker image.

## How this repo fits the demo
- CI builds Python and Docker artifacts
- SBOM generation and signing (placeholders in the scaffold)
- Publishes to Artifactory internal repos (DEV/QA/STAGING)
- Promotion workflow demonstrates AppTrust lifecycle up to PROD
- OIDC-based auth from GitHub Actions to JFrog (no long-lived secrets)

## Repository layout
- `.github/workflows/ci.yml`: CI pipeline (test → build → SBOM/sign → publish)
- `.github/workflows/promote.yml`: Manual promotion workflow with evidence placeholders
- Application code and packaging files will be added as the demo evolves

## CI Expectations
Define these GitHub variables at org/repo scope:
- `PROJECT_KEY` = `bookverse`
- `JFROG_URL` = your JFrog instance URL
- `DOCKER_REGISTRY` = Docker registry hostname in Artifactory

Internal targets:
- Docker: `bookverse-recommendations-docker-internal-local`
- Python: `bookverse-recommendations-python-internal-local`

Release targets:
- Docker: `bookverse-recommendations-docker-release-local`
- Python: `bookverse-recommendations-python-release-local`

## Promotion
Run `.github/workflows/promote.yml` and choose QA, STAGING, or PROD. Evidence placeholders can be wired to real test/approval signals in a full setup.

## Related demo resources
- Overview: BookVerse scenario in the AppTrust demo materials
- Sister repos: `bookverse-inventory`, `bookverse-checkout`, `bookverse-platform`, `bookverse-demo-assets`

---
This repository is intentionally minimal to highlight platform capabilities. Extend it with real application code as needed for demonstrations.
