# k8s-gitops-platform

> Production-grade GitOps platform on AWS EKS — Terraform · Helm · ArgoCD · tfsec · Checkov · GitHub Actions

[![Terraform CI](https://github.com/kumarrajapuvvalla-bit/k8s-gitops-platform/actions/workflows/terraform-ci.yml/badge.svg)](https://github.com/kumarrajapuvvalla-bit/k8s-gitops-platform/actions/workflows/terraform-ci.yml)
[![Helm Lint](https://github.com/kumarrajapuvvalla-bit/k8s-gitops-platform/actions/workflows/helm-lint.yml/badge.svg)](https://github.com/kumarrajapuvvalla-bit/k8s-gitops-platform/actions/workflows/helm-lint.yml)
[![Image Build](https://github.com/kumarrajapuvvalla-bit/k8s-gitops-platform/actions/workflows/image-build.yml/badge.svg)](https://github.com/kumarrajapuvvalla-bit/k8s-gitops-platform/actions/workflows/image-build.yml)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   GitHub Repository                      │
│                                                          │
│  infrastructure/   helm-charts/   gitops/   .github/    │
│  (Terraform)       (Helm)         (ArgoCD)  (Actions)   │
└──────────┬─────────────┬──────────────┬────────────────-┘
           │             │              │
           ▼             │              ▼
    ┌──────────────┐     │     ┌─────────────────┐
    │ GitHub       │     │     │   ArgoCD        │
    │ Actions CI   │     │     │   (GitOps CD)   │
    │              │     │     │                 │
    │ - tfsec      │     │     │ Watches gitops/ │
    │ - Checkov    │     │     │ Auto-syncs to   │
    │ - Helm lint  │     │     │ EKS cluster     │
    │ - Trivy scan │     │     └────────┬────────┘
    └──────┬───────┘     │              │
           │             │              ▼
           ▼             │     ┌─────────────────┐
    ┌──────────────┐     │     │   AWS EKS       │
    │  Terraform   │─────┘     │   Cluster       │
    │  Apply       │           │                 │
    │              │──────────▶│  - dev ns       │
    │  VPC/EKS/IAM │           │  - prod ns      │
    └──────────────┘           └─────────────────┘
```

## Repository Structure

```
k8s-gitops-platform/
├── infrastructure/                  # Terraform — EKS, VPC, IAM
│   ├── modules/
│   │   ├── eks/                     # EKS cluster module
│   │   ├── vpc/                     # VPC networking module
│   │   └── iam/                     # IAM roles + IRSA module
│   └── environments/
│       ├── dev/                     # Dev environment tfvars
│       └── prod/                    # Prod environment tfvars
├── helm-charts/
│   └── app-chart/                   # Generic app Helm chart
│       ├── Chart.yaml
│       ├── values.yaml              # Default values
│       ├── values-dev.yaml          # Dev overrides
│       ├── values-prod.yaml         # Prod overrides
│       └── templates/
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── ingress.yaml
│           ├── hpa.yaml
│           └── serviceaccount.yaml
├── gitops/                          # ArgoCD manifests
│   ├── argocd-app-of-apps.yaml      # Root App of Apps
│   └── apps/
│       ├── dev/
│       │   └── app.yaml
│       └── prod/
│           └── app.yaml
├── .github/
│   └── workflows/
│       ├── terraform-ci.yml         # tfsec + Checkov + tf plan
│       ├── helm-lint.yml            # Helm lint + template check
│       └── image-build.yml          # Docker build + Trivy scan
└── README.md
```

## CI/CD Pipeline Flow

```
PR Raised
  → tfsec scans Terraform (fails on HIGH severity)
  → Checkov scans Terraform + Helm manifests
  → Helm lint + helm template validation
  → Trivy scans Docker image
  → All green? → terraform plan posted as PR comment
  ↓
Merge to main
  → ArgoCD detects change in gitops/
  → ArgoCD syncs to EKS cluster
  → App deployed to dev or prod namespace
```

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Infrastructure | Terraform | EKS cluster, VPC, IAM/IRSA |
| Packaging | Helm | Application chart with env overrides |
| GitOps CD | ArgoCD | App-of-Apps, auto-sync, drift detection |
| Security Scan | tfsec | Terraform static analysis (HIGH/CRITICAL blocking) |
| Policy Check | Checkov | IaC + K8s manifest scanning |
| Image Security | Trivy | Container vulnerability scanning |
| CI Orchestration | GitHub Actions | Unified pipeline |
| Cluster | AWS EKS | Managed Kubernetes |
| Autoscaling | Cluster Autoscaler | Node-level scaling |
| Observability | Prometheus + Grafana | Metrics + dashboards |

## Getting Started

### Prerequisites

- AWS CLI configured with appropriate permissions
- `terraform` >= 1.5
- `helm` >= 3.12
- `kubectl` configured
- `argocd` CLI

### 1. Provision Infrastructure

```bash
cd infrastructure/environments/dev
terraform init
terraform plan
terraform apply
```

### 2. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### 3. Bootstrap GitOps

```bash
kubectl apply -f gitops/argocd-app-of-apps.yaml
```

ArgoCD will automatically detect and deploy all apps defined under `gitops/apps/`.

### 4. Access ArgoCD UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Username: admin
# Password: kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d
```

## Security Controls

- **tfsec** — blocks PRs with HIGH or CRITICAL Terraform findings
- **Checkov** — scans Terraform and Helm-rendered manifests
- **Trivy** — scans container images for CVEs (CRITICAL/HIGH blocking)
- **IRSA** — IAM Roles for Service Accounts (no node-level credentials)
- **Secret scanning** — enabled on repository
- **Non-root containers** — enforced in Helm chart defaults

## Environments

| Environment | Namespace | Sync Policy | Replicas |
|-------------|-----------|-------------|----------|
| dev | `app-dev` | Automatic | 1 |
| prod | `app-prod` | Manual (approval) | 3 |

## Related Portfolio Projects

- [terraform-aws-eks-platform](https://github.com/kumarrajapuvvalla-bit/terraform-aws-eks-platform) — EKS cluster IaC
- [terraform-aws-three-tier-infra](https://github.com/kumarrajapuvvalla-bit/terraform-aws-three-tier-infra) — Three-tier AWS infrastructure
- [azure-core-banking-platform](https://github.com/kumarrajapuvvalla-bit/azure-core-banking-platform) — Azure AKS banking platform
