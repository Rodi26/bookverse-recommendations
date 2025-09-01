# CI/CD

Workflow highlights:

- Install deps and run unit tests (pytest)
- Build two images: API and Worker
- Upload config/resources as artifacts
- Optional: login and push if DOCKER_REGISTRY/credentials are set
- Optional: Trivy scan if ENABLE_TRIVY=true
- Optional: Cosign sign (OIDC) if ENABLE_COSIGN=true
