# BookVerse Platform

## Enterprise Microservices Platform with Secure Software Supply Chain Management

BookVerse is a comprehensive microservices platform that delivers modern software development practices, secure CI/CD pipelines, and enterprise-grade deployment automation. Built with industry-leading technologies, BookVerse provides organizations with a complete reference architecture for scalable, secure, and compliant software delivery.

---

## 🎯 Where Do You Want to Start?

Choose your path based on your needs:

- **🚀 Quick Start**: Follow the [Getting Started Guide](docs/GETTING_STARTED.md) for rapid deployment
- **🏗️ Deep Dive**: Explore the [Architecture Overview](docs/ARCHITECTURE.md) for detailed system understanding
- **🎮 Demo**: Run through the [Demo Runbook](docs/DEMO_RUNBOOK.md) for hands-on experience

---
## 🚀 Quick Start

### Prerequisites

Ensure you have the following tools and access:

- **JFrog Platform** with admin privileges (Artifactory + AppTrust)
- **GitHub Organization** with repository creation permissions  
- **GitHub CLI** (`gh`) installed and authenticated
- **Basic Tools**: `curl`, `jq`, `bash`
- **Optional**: Kubernetes cluster for runtime deployment

### Setup

BookVerse is distributed across multiple repositories. For a complete setup:

```bash
# 1. Clone the orchestration repository (contains setup automation)
git clone https://github.com/your-org/bookverse-demo-init.git
cd bookverse-demo-init

# 2. Configure your environment
export JFROG_URL="https://your-instance.jfrog.io"
export JFROG_ADMIN_TOKEN="your-admin-token"
export GITHUB_ORG="your-github-org"

# 3. Run automated platform setup (creates all repositories and CI/CD)
./scripts/setup-platform.sh

# 4. Verify deployment
./scripts/validate-platform.sh
```

**Note**: The setup script will automatically create and configure all service repositories:
- `bookverse-inventory` - Product catalog service
- `bookverse-recommendations` - ML recommendation engine  
- `bookverse-checkout` - Order processing service
- `bookverse-web` - Frontend application
- `bookverse-platform` - Integration testing service
- `bookverse-helm` - Kubernetes deployment charts

### Access Your Application

After successful deployment, the BookVerse web application will be available at:

- **🌐 BookVerse Web App**: `http://bookverse.demo` (or your configured domain)
  - Complete bookstore interface with catalog, recommendations, and checkout
  - Service health monitoring via the release info modal
  - Individual service APIs accessible through the web app

---

## 📋 Platform Components

| Component | Purpose | Technology Stack | Deployment |
|-----------|---------|------------------|------------|
| **Inventory** | Product catalog & inventory management | Python, FastAPI, SQLite | Container + K8s |
| **Recommendations** | AI-powered recommendation engine | Python, scikit-learn, FastAPI | Container + K8s |
| **Checkout** | Order processing & payments | Python, FastAPI, PostgreSQL | Container + K8s |
| **Web App** | Frontend user interface | Vanilla JS, Vite, HTML5 | Static + CDN |
| **Platform** | Service orchestration | Python, FastAPI | Container + K8s |
| **Helm Charts** | K8s deployment automation | Helm 3, YAML | GitOps |
| **Orchestration** | Platform automation | Python, Shell, GitHub Actions | Automation |

---

## 🎯 Use Cases

### 🏢 **Enterprise Development Teams**

- Reference architecture for microservices transformation
- Secure CI/CD pipeline implementation
- Container orchestration and deployment automation
- DevSecOps practices and compliance automation

### 🔧 **DevOps Engineers**

- Complete GitOps workflow implementation
- Multi-environment deployment strategies
- Infrastructure as Code patterns
- Monitoring and observability setup

### 🔐 **Security Teams**

- Software supply chain security implementation
- Zero-trust CI/CD pipeline design
- Vulnerability management workflows
- Compliance and audit trail automation

### 🏗️ **Platform Engineers**

- Microservices architecture patterns
- Service mesh and API gateway configuration
- Cross-service communication strategies
- Platform engineering best practices

---

## 📚 Documentation

### 🚀 **Platform Setup & Architecture**

- [📖 **Getting Started**](docs/GETTING_STARTED.md) - Complete setup and deployment instructions
- [🏗️ **Architecture Overview**](docs/ARCHITECTURE.md) - System design and component relationships
- [🎮 **Demo Runbook**](docs/DEMO_RUNBOOK.md) - Step-by-step demo execution guide
- [⚙️ **Repository Architecture**](docs/REPO_ARCHITECTURE.md) - Code organization and structure

### ⚙️ **Operations & Integration**

- [🔄 **CI/CD Deployment**](docs/CICD_DEPLOYMENT_GUIDE.md) - Pipeline configuration and automation
- [🔐 **OIDC Authentication**](docs/OIDC_AUTHENTICATION.md) - Zero-trust authentication setup
- [🏗️ **Setup Automation**](docs/SETUP_AUTOMATION.md) - Platform provisioning and configuration
- [📈 **Evidence Collection**](docs/EVIDENCE_COLLECTION.md) - Compliance and audit trail automation
- [🚀 **GitOps Deployment**](docs/GITOPS_DEPLOYMENT.md) - Continuous deployment workflows
- [🔗 **JFrog Integration**](docs/JFROG_INTEGRATION.md) - Artifact management and security

### 🔧 **Advanced Topics**

- [🔄 **Promotion Workflows**](docs/PROMOTION_WORKFLOWS.md) - Multi-stage deployment strategies
- [📋 **AppTrust Lifecycle**](docs/APPTRUST_LIFECYCLE.md) - Software supply chain security
- [🏗️ **Orchestration Overview**](docs/ORCHESTRATION_OVERVIEW.md) - Platform coordination patterns
- [🔑 **Evidence Key Deployment**](docs/EVIDENCE_KEY_DEPLOYMENT.md) - Cryptographic key management
- [🔧 **JFrog Platform Switch**](docs/SWITCH_JFROG_PLATFORM.md) - Platform migration procedures

---

## 🌟 Key Features

### ✅ **Production Ready**

- Enterprise-grade security and compliance
- Scalable microservices architecture
- Comprehensive monitoring and observability
- Multi-environment deployment support

### ✅ **Developer Friendly**

- Clear documentation and examples
- Local development environment
- Automated testing and quality gates
- Modern development practices

### ✅ **Operations Focused**

- GitOps deployment workflows
- Infrastructure as Code
- Automated scaling and healing
- Comprehensive audit trails

### ✅ **Secure by Design**

- Zero-trust authentication
- Encrypted communication
- Vulnerability scanning
- Compliance automation

---

## 📚 Documentation

### 🚀 **Platform Setup & Architecture**

- [📖 **Getting Started**](docs/GETTING_STARTED.md) - Complete setup and deployment instructions
- [🏗️ **Architecture Overview**](docs/ARCHITECTURE.md) - System design and component relationships
- [🎮 **Demo Runbook**](docs/DEMO_RUNBOOK.md) - Step-by-step demo execution guide
- [⚙️ **Repository Architecture**](docs/REPO_ARCHITECTURE.md) - Code organization and structure

### ⚙️ **Operations & Integration**

- [🔄 **CI/CD Deployment**](docs/CICD_DEPLOYMENT_GUIDE.md) - Pipeline configuration and automation
- [🔐 **OIDC Authentication**](docs/OIDC_AUTHENTICATION.md) - Zero-trust authentication setup
- [🏗️ **Setup Automation**](docs/SETUP_AUTOMATION.md) - Platform provisioning and configuration
- [📈 **Evidence Collection**](docs/EVIDENCE_COLLECTION.md) - Compliance and audit trail automation
- [🚀 **GitOps Deployment**](docs/GITOPS_DEPLOYMENT.md) - Continuous deployment workflows
- [🔗 **JFrog Integration**](docs/JFROG_INTEGRATION.md) - Artifact management and security

### 🔧 **Advanced Topics**

- [🔄 **Promotion Workflows**](docs/PROMOTION_WORKFLOWS.md) - Multi-stage deployment strategies
- [📋 **AppTrust Lifecycle**](docs/APPTRUST_LIFECYCLE.md) - Software supply chain security
- [🏗️ **Orchestration Overview**](docs/ORCHESTRATION_OVERVIEW.md) - Platform coordination patterns
- [🔑 **Evidence Key Deployment**](docs/EVIDENCE_KEY_DEPLOYMENT.md) - Cryptographic key management
- [🔧 **JFrog Platform Switch**](docs/SWITCH_JFROG_PLATFORM.md) - Platform migration procedures

---

## 🌟 Key Features

### ✅ **Production Ready**

- Enterprise-grade security and compliance
- Scalable microservices architecture
- Comprehensive monitoring and observability
- Multi-environment deployment support

### ✅ **Developer Friendly**

- Clear documentation and examples
- Local development environment
- Automated testing and quality gates
- Modern development practices

### ✅ **Operations Focused**

- GitOps deployment workflows
- Infrastructure as Code
- Automated scaling and healing
- Comprehensive audit trails

### ✅ **Secure by Design**

- Zero-trust authentication
- Encrypted communication
- Vulnerability scanning
- Compliance automation

---

## 🎯 What's Next?

Ready to get started with BookVerse? Choose your path:

- **🚀 Quick Start**: Follow the [Getting Started Guide](docs/GETTING_STARTED.md) for rapid deployment
- **🏗️ Deep Dive**: Explore the [Architecture Overview](docs/ARCHITECTURE.md) for detailed system understanding  
- **🎮 Demo**: Run through the [Demo Runbook](docs/DEMO_RUNBOOK.md) for hands-on experience

**BookVerse provides everything you need to implement enterprise-grade microservices with secure, automated software delivery.**

---

> **Note**: Individual service documentation is available in each service repository:
> **Note**: Individual service documentation is available in each service repository:
> - [Inventory Service](https://github.com/yonatanp-jfrog/bookverse-inventory)
> - [Recommendations Service](https://github.com/yonatanp-jfrog/bookverse-recommendations)  
> - [Checkout Service](https://github.com/yonatanp-jfrog/bookverse-checkout)
> - [Platform Service](https://github.com/yonatanp-jfrog/bookverse-platform)
> - [Web Application](https://github.com/yonatanp-jfrog/bookverse-web)
> - [Helm Charts](https://github.com/yonatanp-jfrog/bookverse-helm)

### Summary

| Component | Purpose | Technology Stack | Deployment | Build Pattern |
|-----------|---------|------------------|------------|---------------|
| **Inventory** | Product catalog & inventory management | Python, FastAPI, SQLite | Container + K8s | Single-container |
| **Recommendations** | AI-powered recommendation engine | Python, scikit-learn, FastAPI | Container + K8s | Multi-container |
| **Checkout** | Order processing & payments | Python, FastAPI, PostgreSQL | Container + K8s | Service dependencies |
| **Web App** | Frontend user interface | Vanilla JS, Vite, HTML5 | Static + CDN | Static assets |
| **Platform** | Integration testing & validation | Python, FastAPI | Container + K8s | Aggregation service |
| **Infrastructure** | Shared libraries & DevOps tooling | Python, Shell | Multi-artifact | Library publishing |
| **Helm Charts** | K8s deployment automation | Helm 3, YAML | GitOps | Infrastructure as Code |
| **Demo Orchestration** | Platform setup automation | Python, Shell, GitHub Actions | Automation | Setup automation |

---

## 🚀 Quick Start

### Prerequisites

Ensure you have the following tools and access:

- **JFrog Platform** with admin privileges (Artifactory + AppTrust)
- **GitHub Organization** with repository creation permissions  
- **GitHub CLI** (`gh`) installed and authenticated
- **Basic Tools**: `curl`, `jq`, `bash`
- **Optional**: Kubernetes cluster for runtime deployment

### Setup

BookVerse is distributed across multiple repositories. For a complete setup:

```bash
# 1. Clone the orchestration repository (contains setup automation)
git clone https://github.com/your-org/bookverse-demo-init.git
cd bookverse-demo-init

# 2. Configure your environment
export JFROG_URL="https://your-instance.jfrog.io"
export JFROG_ADMIN_TOKEN="your-admin-token"
export GITHUB_ORG="your-github-org"

# 3. Run automated platform setup (creates all repositories and CI/CD)
./scripts/setup-platform.sh

# 4. Verify deployment
./scripts/validate-platform.sh
```

**Note**: The setup script will automatically create and configure all service repositories:
- `bookverse-inventory` - Product catalog service
- `bookverse-recommendations` - ML recommendation engine  
- `bookverse-checkout` - Order processing service
- `bookverse-web` - Frontend application
- `bookverse-platform` - Integration testing service
- `bookverse-helm` - Kubernetes deployment charts

### Access Your Application

After successful deployment, the BookVerse web application will be available at:

- **🌐 BookVerse Web App**: `http://bookverse.demo` (or your configured domain)
  - Complete bookstore interface with catalog, recommendations, and checkout
  - Service health monitoring via the release info modal
  - Individual service APIs accessible through the web app

---

## 🎯 Use Cases

### 🏢 **Enterprise Development Teams**

- Reference architecture for microservices transformation
- Secure CI/CD pipeline implementation
- Container orchestration and deployment automation
- DevSecOps practices and compliance automation

### 🔧 **DevOps Engineers**

- Complete GitOps workflow implementation
- Multi-environment deployment strategies
- Infrastructure as Code patterns
- Monitoring and observability setup

### 🔐 **Security Teams**

- Software supply chain security implementation
- Zero-trust CI/CD pipeline design
- Vulnerability management workflows
- Compliance and audit trail automation

### 🏗️ **Platform Engineers**

- Microservices architecture patterns
- Service mesh and API gateway configuration
- Cross-service communication strategies
- Platform engineering best practices

---

## 📚 Documentation

### 🚀 **Platform Setup & Architecture**

- [📖 **Getting Started**](docs/GETTING_STARTED.md) - Complete setup and deployment instructions
- [🏗️ **Architecture Overview**](docs/ARCHITECTURE.md) - System design and component relationships
- [🎮 **Demo Runbook**](docs/DEMO_RUNBOOK.md) - Step-by-step demo execution guide
- [⚙️ **Repository Architecture**](docs/REPO_ARCHITECTURE.md) - Code organization and structure

### ⚙️ **Operations & Integration**

- [🔄 **CI/CD Deployment**](docs/CICD_DEPLOYMENT_GUIDE.md) - Pipeline configuration and automation
- [🔐 **OIDC Authentication**](docs/OIDC_AUTHENTICATION.md) - Zero-trust authentication setup
- [🏗️ **Setup Automation**](docs/SETUP_AUTOMATION.md) - Platform provisioning and configuration
- [📈 **Evidence Collection**](docs/EVIDENCE_COLLECTION.md) - Compliance and audit trail automation
- [🚀 **GitOps Deployment**](docs/GITOPS_DEPLOYMENT.md) - Continuous deployment workflows
- [🔗 **JFrog Integration**](docs/JFROG_INTEGRATION.md) - Artifact management and security

### 🔧 **Advanced Topics**

- [🔄 **Promotion Workflows**](docs/PROMOTION_WORKFLOWS.md) - Multi-stage deployment strategies
- [📋 **AppTrust Lifecycle**](docs/APPTRUST_LIFECYCLE.md) - Software supply chain security
- [🏗️ **Orchestration Overview**](docs/ORCHESTRATION_OVERVIEW.md) - Platform coordination patterns
- [🔑 **Evidence Key Deployment**](docs/EVIDENCE_KEY_DEPLOYMENT.md) - Cryptographic key management
- [🔧 **JFrog Platform Switch**](docs/SWITCH_JFROG_PLATFORM.md) - Platform migration procedures

---

## 🌟 Key Features

### ✅ **Production Ready**

- Enterprise-grade security and compliance
- Scalable microservices architecture
- Comprehensive monitoring and observability
- Multi-environment deployment support

### ✅ **Developer Friendly**

- Clear documentation and examples
- Local development environment
- Automated testing and quality gates
- Modern development practices

### ✅ **Operations Focused**

- GitOps deployment workflows
- Infrastructure as Code
- Automated scaling and healing
- Comprehensive audit trails

### ✅ **Secure by Design**

- Zero-trust authentication
- Encrypted communication
- Vulnerability scanning
- Compliance automation

---

## 📚 Documentation

### 🚀 **Platform Setup & Architecture**

- [📖 **Getting Started**](docs/GETTING_STARTED.md) - Complete setup and deployment instructions
- [🏗️ **Architecture Overview**](docs/ARCHITECTURE.md) - System design and component relationships
- [🎮 **Demo Runbook**](docs/DEMO_RUNBOOK.md) - Step-by-step demo execution guide
- [⚙️ **Repository Architecture**](docs/REPO_ARCHITECTURE.md) - Code organization and structure

### ⚙️ **Operations & Integration**

- [🔄 **CI/CD Deployment**](docs/CICD_DEPLOYMENT_GUIDE.md) - Pipeline configuration and automation
- [🔐 **OIDC Authentication**](docs/OIDC_AUTHENTICATION.md) - Zero-trust authentication setup
- [🏗️ **Setup Automation**](docs/SETUP_AUTOMATION.md) - Platform provisioning and configuration
- [📈 **Evidence Collection**](docs/EVIDENCE_COLLECTION.md) - Compliance and audit trail automation
- [🚀 **GitOps Deployment**](docs/GITOPS_DEPLOYMENT.md) - Continuous deployment workflows
- [🔗 **JFrog Integration**](docs/JFROG_INTEGRATION.md) - Artifact management and security

### 🔧 **Advanced Topics**

- [🔄 **Promotion Workflows**](docs/PROMOTION_WORKFLOWS.md) - Multi-stage deployment strategies
- [📋 **AppTrust Lifecycle**](docs/APPTRUST_LIFECYCLE.md) - Software supply chain security
- [🏗️ **Orchestration Overview**](docs/ORCHESTRATION_OVERVIEW.md) - Platform coordination patterns
- [🔑 **Evidence Key Deployment**](docs/EVIDENCE_KEY_DEPLOYMENT.md) - Cryptographic key management
- [🔧 **JFrog Platform Switch**](docs/SWITCH_JFROG_PLATFORM.md) - Platform migration procedures

---

## 🌟 Key Features

### ✅ **Production Ready**

- Enterprise-grade security and compliance
- Scalable microservices architecture
- Comprehensive monitoring and observability
- Multi-environment deployment support

### ✅ **Developer Friendly**

- Clear documentation and examples
- Local development environment
- Automated testing and quality gates
- Modern development practices

### ✅ **Operations Focused**

- GitOps deployment workflows
- Infrastructure as Code
- Automated scaling and healing
- Comprehensive audit trails

### ✅ **Secure by Design**

- Zero-trust authentication
- Encrypted communication
- Vulnerability scanning
- Compliance automation

---

## 🎯 What's Next?

Ready to get started with BookVerse? Choose your path:

- **🚀 Quick Start**: Follow the [Getting Started Guide](docs/GETTING_STARTED.md) for rapid deployment
- **🏗️ Deep Dive**: Explore the [Architecture Overview](docs/ARCHITECTURE.md) for detailed system understanding  
- **🎮 Demo**: Run through the [Demo Runbook](docs/DEMO_RUNBOOK.md) for hands-on experience

**BookVerse provides everything you need to implement enterprise-grade microservices with secure, automated software delivery.**

---

> **Note**: Individual service documentation is available in each service repository:
> **Note**: Individual service documentation is available in each service repository:
> - [Inventory Service](https://github.com/yonatanp-jfrog/bookverse-inventory)
> - [Recommendations Service](https://github.com/yonatanp-jfrog/bookverse-recommendations)  
> - [Checkout Service](https://github.com/yonatanp-jfrog/bookverse-checkout)
> - [Platform Service](https://github.com/yonatanp-jfrog/bookverse-platform)
> - [Web Application](https://github.com/yonatanp-jfrog/bookverse-web)
> - [Helm Charts](https://github.com/yonatanp-jfrog/bookverse-helm)
