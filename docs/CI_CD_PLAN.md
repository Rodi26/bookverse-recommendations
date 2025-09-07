# BookVerse Recommendations – CI/CD and AppTrust Implementation Plan

## Purpose

Define the complete software delivery lifecycle for the Recommendations service: publish multi-artifacts, capture and publish build info, create an AppTrust application version, attach evidence, and promote through DEV → QA → STAGING → PROD with gates.

## TL;DR

- Build and publish two Docker images (API, Worker) with a single build name/number via JFrog CLI.
- Attach evidence (coverage, SAST) to packages; optionally sign images (not as evidence).
- Create an AppTrust application version, bind the build, and attach SDLC evidence.
- Replace the placeholder promotion workflow with gated promotions across QA/STAGING/PROD.

## Current state (Recommendations)

- CI builds API and Worker images, runs tests, and optionally pushes to a registry.
- Optional Trivy scan and Cosign signing; config/resources are uploaded as GitHub artifacts only.
- No JFrog CLI publishing, no build info, no AppTrust application version, no evidence attachments, no real promotion.

## Reference expectations (from Inventory and templates)

- Use JFrog CLI for resolve/install, building, publishing, and evidence (`bookverse-demo-init/templates/python_docker/ci.yml`).
- Publish artifacts with a single build name/number per commit.
- Create AppTrust application version, bind builds as sources, and attach SDLC evidence.
- Implement promotion workflow with evidence gates across environments.

## Gap analysis

- Missing: JFrog CLI publishing to Artifactory and build-info association.
- Missing: AppTrust application version creation and binding.
- Missing: Evidence attachments to packages and application version parity with Inventory (coverage, SAST on packages; SDLC on app version).
- Missing: Promotion workflow with policy/evidence gates and artifact moves across repos.
- Missing: Publishing config/resources as versioned artifacts.

## Prerequisites

- Repository variables and secrets:
  - `vars.JFROG_URL`, `vars.PROJECT_KEY`
  - `secrets.JFROG_ACCESS_TOKEN` (or OIDC with server-side trust)
  - `secrets.EVIDENCE_PRIVATE_KEY` (optional if no server-side key alias)
- Artifactory repositories (project-scoped):
  - `${PROJECT_KEY}-recommendations-internal-docker-nonprod-local`
  - `${PROJECT_KEY}-recommendations-internal-docker-release-local`
  - Optional: `${PROJECT_KEY}-recommendations-internal-generic-nonprod-local` for config/resources

## Target model

- Build name: `recommendations`, build number: short SHA.
- Images published per build:
  - `recommendations-api`
  - `recommendations-worker`
- Non-image supporting artifacts (recommended; must be used by the service):
  - Config bundle (`config/`) for algorithm weights and TTLs
  - Resources bundle (`resources/`), e.g., `resources/stopwords.txt` used by the scorer
  - Note: Also included in the images for simplicity; publishing them ensures they appear in the AppTrust application version and are traceable
- Application key: `bookverse-recommendations`, version: SemVer with auto-increment patch.
- Evidence attached:
  - Test Coverage (pytest)
  - SAST Scan (CodeQL-style JSON + markdown summary)
  - SBOM (automatic via AppTrust; do not attach as evidence here)
  - SDLC Release (application version level)

## Phase 1 — CI pipeline upgrade (build, test, publish, evidence on packages)

1) Bootstrap JFrog CLI and dependency resolution
- Setup JFrog CLI (`jf c add` with OIDC/PAT)
- Configure pip resolver: `jf pipc --repo-resolve=${PROJECT_KEY}-pypi-virtual`
- Install deps via `jf pip install` (captures dependency metadata)

2) Test and collect reports
- Run `pytest` with coverage → generate `coverage.xml` and `htmlcov/`
- On failure, generate fallback coverage to keep demo flow consistent

3) Static analysis
- Generate SAST results JSON (CodeQL-like) and `sast-summary.md` (or run CodeQL if enabled)

4) Build and publish two images with one build name/number
- Compute `IMAGE_TAG` = short SHA
- `REGISTRY_URL` = `${JFROG_URL}` stripped of scheme
- Build:
  - `${REGISTRY_URL}/${PROJECT_KEY}-recommendations-internal-docker-nonprod-local/recommendations-api:${IMAGE_TAG}`
  - `${REGISTRY_URL}/${PROJECT_KEY}-recommendations-internal-docker-nonprod-local/recommendations-worker:${IMAGE_TAG}`
- Push via `jf rt dp` for both and associate with build name/number
- Optional: Cosign OIDC sign both images

5) SBOM handling (by AppTrust)
- SBOMs are generated and managed by AppTrust automatically; do not attach SBOM as evidence here

6) Coverage and SAST evidence on packages
- Create JSON predicates and markdown summaries
- Attach with `jf evd create-evidence` using:
  - `--package-name recommendations-api|recommendations-worker`
  - `--package-repo-name ${PROJECT_KEY}-recommendations-internal-docker-nonprod-local`
  - `--package-version ${IMAGE_TAG}`
  - `--predicate-type "Test Coverage"|"SAST Scan"`
  - Use the exact predicate type names and JSON/Markdown formats used in Inventory (`coverage-evidence.json`/`coverage-evidence.md`, `sast-evidence.json`/`sast-summary.md`).

7) Optional: publish config/resources as versioned generic artifacts
- Tar/GZip and upload to `${PROJECT_KEY}-recommendations-internal-generic-nonprod-local/recommendations-config/${IMAGE_TAG}/...`
- Attach a short evidence document referencing checksums and contents

8) CI summary
- Emit a concise summary to `$GITHUB_STEP_SUMMARY` listing images, evidence, and build coordinates

Deliverable: Both images published with build-info and evidence attached to packages.

## Phase 2 — AppTrust application version and SDLC evidence

1) Determine application version
- Query AppTrust latest version; increment patch or start at `1.0.X`

2) Create application version and bind build
- POST `version` and `sources.builds` with `{ name: recommendations, number: ${IMAGE_TAG} }`

3) SDLC evidence on application version
- Predicate JSON: developer, reviewer, tickets, gates, commit, build URL
- Markdown summary for readability
- `jf evd create-evidence --predicate sdlc.json --markdown sdlc.md --predicate-type "SDLC Release" --release-bundle bookverse-recommendations --release-bundle-version ${APP_VERSION}`

Deliverable: AppTrust version created with SDLC evidence.

## Phase 3 — Promotion workflow with gates (QA/STAGING/PROD)

1) Inputs
- `target_stage`: QA | STAGING | PROD
- Optional `app_version` (fallback to latest)

2) Pre-promotion gates
- Verify evidence present and thresholds met:
  - Coverage ≥ 85%
  - SAST: no Critical/High
  - Optional: Cosign signature present
  - Optional: Xray policy gate on build passes (policy can rely on AppTrust-provided SBOM)

3) Promote build/artifacts
- Promote/move images across repos:
  - `internal-local → qa-local → staging-local → prod-local`
- Keep `${IMAGE_TAG}` constant; only repository path changes

4) Promotion evidence
- Attach promotion evidence (approver, checks, change ref, time)

5) Release handoff (internal consumption)
- Do not trigger ArgoCD. This service is released internally for consumption by other services.
- A future platform aggregator will compose service releases into a single platform release for Argo CD.

Deliverable: Gate-enforced promotion with recorded evidence.

## Phase 4 — Security and provenance hardening (optional)

- Cosign OIDC signatures with attestations per image
- Policy gates (Xray) can rely on AppTrust-provided SBOM (no separate evidence attachment)
- SLSA-style provenance where feasible

## Phase 5 — Reuse and standardization

- Convert CI and Promote into reusable workflows in `bookverse-demo-init/templates/`
- Parameterize by service name and `${PROJECT_KEY}` to minimize drift

## File updates required

- `.github/workflows/ci.yml`: swap to JFrog-driven pipeline (two images, build-info, evidence, app version)
- `.github/workflows/promote.yml`: replace placeholder with gated promotion and promotion evidence
- `README.md`: add CI/CD notes; link to this plan
- Optional: `scripts/` helpers for predicates and API calls

## Checklist

- [ ] Configure `vars` and `secrets` for JFrog and evidence keys
- [ ] Publish `recommendations-api` and `recommendations-worker` to internal-local with one build name/number
- [ ] Evidence parity with Inventory: Coverage + SAST on packages; SDLC on app version
- [ ] Implement gated promotion across QA/STAGING/PROD repos
- [ ] Attach promotion evidence per stage
- [ ] (Optional) Publish config/resources bundles and attach reference evidence
- [ ] Emit rich `$GITHUB_STEP_SUMMARY` entries for demo visibility

## Suggestions

- Prefer OIDC to avoid long-lived tokens; use server-side key aliases if available
- Keep demo-friendly fallbacks (e.g., coverage fallback) but document where to enforce strict gates
- Centralize evidence generation scripts to reduce duplication
- Keep tags immutable; use repository path changes for environment separation
