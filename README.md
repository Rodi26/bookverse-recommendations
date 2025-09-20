# 🎯 BookVerse Recommendations Service

A sophisticated, enterprise-grade recommendation engine for the BookVerse platform. This service demonstrates modern software delivery practices with comprehensive CI/CD automation, multi-artifact publishing, and evidence-based compliance.

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload --port 8000

# Health check
curl http://localhost:8000/health
```

### Docker Deployment
```bash
# Build and run API service
docker build -t bookverse-recommendations:dev .
docker run -p 8000:8000 bookverse-recommendations:dev

# Build and run worker service
docker build -f Dockerfile.worker -t bookverse-recommendations-worker:dev .
docker run bookverse-recommendations-worker:dev
```

## 📋 Service Overview

### 🎯 Purpose
The BookVerse Recommendations Service is an AI-powered recommendation engine that provides personalized book suggestions to users based on their reading history, preferences, and behavioral patterns. The service is designed to showcase enterprise-grade software delivery practices while maintaining simplicity for demonstration purposes.

### 🏗️ Architecture
- **Algorithm**: Sophisticated rule-based scorer using genre/author overlap with popularity weighting
- **Data Source**: Real-time integration with `bookverse-inventory` service for books and transactions
- **Indexing**: High-performance in-memory inverted indices (genre/author) with TTL caching
- **Multi-Artifact Design**: Distributed as multiple coordinated artifacts for maximum flexibility

### 📦 Artifacts Produced
1. **📱 API Service** - Main recommendation service (Docker image)
2. **🔧 Worker Service** - Background processing engine (Docker image)  
3. **⚙️ Configuration Bundle** - Algorithm parameters and settings (Generic artifact)
4. **📚 Resources Bundle** - ML models, stopwords, and training data (Generic artifact)

### 🌟 Key Features
- **Real-time Recommendations** - Sub-200ms response times for personalized suggestions
- **Scalable Architecture** - Independent scaling of API and worker components
- **Configurable Algorithms** - External configuration for easy tuning without code changes
- **Comprehensive Monitoring** - Full observability with health checks and metrics
- **Security First** - OIDC authentication and evidence-based compliance

## 🔗 API Endpoints

### Core Endpoints
| Method | Endpoint | Description | Response Time |
|--------|----------|-------------|---------------|
| `GET` | `/health` | Basic health check | <10ms |
| `GET` | `/info` | Service information and version | <50ms |
| `GET` | `/api/v1/recommendations/health` | Detailed health diagnostics | <100ms |

### Recommendation Endpoints
| Method | Endpoint | Description | Response Time |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/recommendations/similar?book_id=<uuid>&limit=10` | Books similar to specified book | <200ms |
| `POST` | `/api/v1/recommendations/personalized` | Personalized recommendations based on user profile | <300ms |
| `GET` | `/api/v1/recommendations/trending?limit=10` | Currently trending books | <150ms |

### Example Usage
```bash
# Get similar books
curl "http://localhost:8000/api/v1/recommendations/similar?book_id=123e4567-e89b-12d3-a456-426614174000&limit=5"

# Get trending books
curl "http://localhost:8000/api/v1/recommendations/trending?limit=10"

# Get personalized recommendations
curl -X POST "http://localhost:8000/api/v1/recommendations/personalized" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "preferences": {"genres": ["fiction", "mystery"]}}'
```

> **Note**: In the demo environment, the web application consumes these endpoints automatically. Manual API calls are optional for testing purposes.

## 🏗️ Multi-Artifact Build System

This service implements a sophisticated multi-artifact build strategy that demonstrates enterprise-grade software delivery practices. Each artifact serves a specific purpose and is versioned independently for maximum flexibility.

### 📦 Artifact Details

#### 1. 📱 API Service Image
```dockerfile
# File: Dockerfile
# Purpose: Main recommendation service API
# Base: python:3.11-slim
# Size: ~1.2GB
# Ports: 8000
```

**Features**:
- FastAPI-based REST API
- Health check endpoints
- Metrics collection
- OIDC authentication support

#### 2. 🔧 Worker Service Image
```dockerfile
# File: Dockerfile.worker  
# Purpose: Background recommendation processing
# Base: python:3.11-slim
# Size: ~1.3GB
```

**Features**:
- Background task processing
- ML model training and updates
- Index rebuilding operations
- Batch recommendation generation

**Worker Execution**:
```bash
# Local execution
python -m app.worker

# Docker execution
docker run bookverse-recommendations-worker:latest
```

#### 3. ⚙️ Configuration Bundle
```yaml
# Content: Algorithm parameters and feature weights
# Format: TAR.GZ archive of YAML files
# Size: ~10KB
# Path: config/recommendations-settings.yaml
```

**Configuration Structure**:
```yaml
algorithm:
  weights:
    genre_similarity: 0.4
    author_similarity: 0.3
    popularity_boost: 0.2
    recency_factor: 0.1
  thresholds:
    min_similarity: 0.1
    max_recommendations: 50
cache:
  ttl_seconds: 3600
  max_entries: 10000
```

#### 4. 📚 Resources Bundle
```yaml
# Content: ML models, stopwords, training data
# Format: TAR.GZ archive of binary and text files
# Size: ~50MB
# Path: resources/stopwords.txt (and others)
```

**Resource Components**:
- **Stopwords**: NLP text processing exclusions
- **ML Models**: Trained recommendation models
- **Training Data**: Historical user interaction data
- **Feature Vectors**: Precomputed book similarity matrices

## Configuration

- Environment variables
  - `INVENTORY_BASE_URL`: base URL for inventory service (e.g., `http://inventory`).
  - `RECOMMENDATIONS_SETTINGS_PATH`: path to YAML settings, default `config/recommendations-settings.yaml`.
  - `RECO_TTL_SECONDS`: overrides TTL seconds via env (optional).
- Settings YAML
  - See `config/recommendations-settings.yaml` for weights/limits/features.

## 🚀 CI/CD Pipeline

The BookVerse Recommendations Service features a comprehensive, enterprise-grade CI/CD pipeline that demonstrates modern software delivery practices with full automation from code commit to production deployment.

### 🏗️ Pipeline Architecture

```mermaid
graph TB
    A[📝 Code Commit] --> B[🔍 Commit Analysis]
    B --> C[🏗️ Build & Test]
    C --> D[📦 Multi-Artifact Publishing]
    D --> E[🛡️ Evidence Collection]
    E --> F[📋 AppTrust Version Creation]
    F --> G[🚀 Automated Promotion]
    
    subgraph "Stages"
        H[🧪 DEV]
        I[🔍 QA] 
        J[🏗️ STAGING]
        K[🚀 PROD]
    end
    
    G --> H --> I --> J --> K
```

### 🎯 Key Features

- **🔄 Intelligent Commit Analysis** - Smart filtering to determine when to create application versions
- **📦 Multi-Artifact Building** - Coordinated building of Docker images and generic artifacts
- **🛡️ Comprehensive Security** - OIDC authentication, evidence collection, and compliance gates
- **🚀 Automated Promotion** - Full pipeline automation through DEV → QA → STAGING → PROD
- **📊 Complete Traceability** - Full artifact lineage and build provenance tracking

### ⚙️ Configuration Requirements

#### Required Repository Variables
```yaml
PROJECT_KEY: "bookverse"                        # Project identifier
JFROG_URL: "https://releases.jfrog.io"         # JFrog Artifactory URL
DOCKER_REGISTRY: "releases.jfrog.io"          # Docker registry endpoint
EVIDENCE_KEY_ALIAS: "bookverse-evidence-key"  # Evidence signing key alias
```

#### Required Repository Secrets
```yaml
EVIDENCE_PRIVATE_KEY: |                        # PEM-formatted private key for evidence signing
  -----BEGIN PRIVATE KEY-----
  [Your evidence signing private key]
  -----END PRIVATE KEY-----
```

#### Mandatory Configuration Files

##### 1. AppTrust Application Binding
**Path**: `.jfrog/config.yml`
```yaml
# This file binds all artifacts to the correct AppTrust application
# Must be committed to repository (contains no secrets)
application:
  key: "bookverse-recommendations"
```

##### 2. Version Configuration
**Path**: `config/version-map.yaml`
```yaml
# Defines versioning strategy for all artifacts
packages:
  recommendations:
    current_version: "1.2.3"
    version_strategy: "semantic"
  recommendations-worker:
    current_version: "1.2.4" 
    version_strategy: "semantic"
  recommendation-config:
    current_version: "1.2.1"
    version_strategy: "semantic"
  resources:
    current_version: "1.2.2"
    version_strategy: "semantic"
```

### 🔄 Workflow Execution

#### Automatic Triggers
- **Push to `main`** - Full pipeline execution with conditional app version creation
- **Pull Request to `main`** - Build and test only (no app version creation)

#### Manual Triggers
```yaml
# Manual execution with debugging options
inputs:
  reason: "Manual testing or debugging"
  force_app_version: true  # Override commit analysis
```

#### Pipeline Jobs

##### Job 1: Commit Analysis (~1 minute)
- Analyzes changed files to determine pipeline scope
- Decides whether to create AppTrust application version
- Uses shared logic from `bookverse-devops` for consistency

##### Job 2: Build & Test (~8 minutes)
- Multi-artifact building (API + Worker images, Config + Resources bundles)
- Comprehensive testing with coverage reporting
- Evidence collection and attachment
- JFrog Artifactory publishing with build-info

##### Job 3: Create & Promote (~6 minutes)
- AppTrust application version creation
- Evidence attachment at application level
- Automated promotion through all stages (DEV → QA → STAGING → PROD)
- Stage-specific evidence collection

### 📊 Monitoring & Observability

#### Build Metrics
- **Success Rate**: >95% target
- **Duration**: ~15 minutes total
- **Artifact Count**: 4 artifacts per build
- **Evidence Collection**: 100% coverage

#### Integration Points
- **GitHub Actions** - CI/CD orchestration and logging
- **JFrog Artifactory** - Artifact storage and build-info
- **AppTrust Platform** - Application lifecycle and compliance
- **Evidence System** - Security and compliance evidence collection

## Testing

- Run unit tests locally:

```bash
python -m pytest -v
```

## How it works

- `Indexer` fetches a snapshot of books and transactions from `bookverse-inventory`, builds inverted indices for authors/genres, and derives a simple popularity prior from recent `stock_out` transactions.
- `score_simple` combines genre/author overlap with the popularity prior (weights from `config/recommendations-settings.yaml`).
- APIs in `app/api.py` expose similar, personalized, and trending endpoints, with a TTL cache configurable via `RECO_TTL_SECONDS`.

## 📚 Documentation

### 📖 Core Documentation
- **[📖 Complete Service Guide](./docs/SERVICE_GUIDE.md)** - Comprehensive service documentation (API, Algorithm, Deployment, Monitoring)
- **[🏗️ CI/CD Architecture](./docs/CI_CD_ARCHITECTURE.md)** - Complete CI/CD system architecture and design
- **[📋 Workflow Reference](./docs/WORKFLOW_REFERENCE.md)** - Detailed workflow steps and configuration reference
- **[🔧 Troubleshooting Guide](./docs/TROUBLESHOOTING.md)** - Common issues, solutions, and debug procedures
- **[🚀 CI/CD Overview](./docs/CI_CD.md)** - Quick CI/CD pipeline overview and getting started

### 🔧 Workflow Files
- **[`ci.yml`](.github/workflows/ci.yml)** - Main CI/CD pipeline with multi-artifact building and evidence collection
- **[`promote.yml`](.github/workflows/promote.yml)** - Manual promotion workflow for advancing through stages
- **[`promotion-rollback.yml`](.github/workflows/promotion-rollback.yml)** - Emergency rollback utility for production issues

### 🚀 Quick Links
- [📖 Service Guide - Local Development](./docs/SERVICE_GUIDE.md#local-development) - Complete development setup
- [📖 Service Guide - API Reference](./docs/SERVICE_GUIDE.md#api-reference) - Complete API documentation
- [📖 Service Guide - Algorithm](./docs/SERVICE_GUIDE.md#algorithm) - Recommendation algorithm details
- [📖 Service Guide - Deployment](./docs/SERVICE_GUIDE.md#deployment) - Production deployment procedures
- [🔧 Troubleshooting](./docs/TROUBLESHOOTING.md) - Common issues and solutions

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards
- **Python**: Follow PEP 8 style guidelines
- **Testing**: Maintain >80% test coverage
- **Documentation**: Update relevant documentation for all changes
- **Security**: All code must pass security scans

### CI/CD Integration
- All PRs trigger the full CI pipeline
- Code coverage reports are automatically generated
- Security scanning is performed on all commits
- Evidence collection validates compliance requirements

## 📞 Support

### Getting Help
- **Documentation**: Check the [comprehensive documentation](./docs/) first
- **Issues**: Create a [GitHub issue](https://github.com/bookverse/bookverse-recommendations/issues) for bugs or feature requests
- **Discussions**: Use [GitHub Discussions](https://github.com/bookverse/bookverse-recommendations/discussions) for questions

### Team Contacts
| Component | Team | Email |
|-----------|------|-------|
| **Service Development** | Backend Team | backend@bookverse.com |
| **CI/CD Pipeline** | DevOps Team | devops@bookverse.com |
| **Security & Compliance** | Security Team | security@bookverse.com |
| **Architecture** | Platform Team | platform@bookverse.com |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **JFrog Platform** - Artifact management and security scanning
- **AppTrust** - Application lifecycle and evidence management
- **GitHub Actions** - CI/CD orchestration and automation
- **FastAPI** - High-performance Python web framework
- **BookVerse Team** - Continuous improvement and innovation

---

*Last Updated: 2024-01-15*
*Service Version: 1.2.3*
*Documentation Version: 1.0.0*
# TEST 3: Recommendations Service tag management test - Sat Sep 20 22:05:00 IDT 2025
