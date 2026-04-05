# DevOps Automation Scripts

Python scripts for operational tasks. All use Boto3 (AWS SDK) or the
Kubernetes Python client — tools commonly expected in UK DevOps roles.

## Scripts

### `validate_tfstate.py` — Terraform Drift Validator

Compares live AWS resource counts against Terraform state stored in S3.
Useful as a post-apply validation step or scheduled drift detection job.

```bash
pip install boto3
python scripts/validate_tfstate.py \
  --bucket my-tfstate-bucket \
  --key gitops-platform/dev/terraform.tfstate \
  --region eu-west-2
```

### `aws_cost_report.py` — Cost Explorer Reporter

Fetches last N days of AWS spend broken down by service for
resources tagged with `Project=k8s-gitops-platform`.
Optionally posts the report to a Slack webhook.

```bash
pip install boto3
python scripts/aws_cost_report.py \
  --project k8s-gitops-platform \
  --days 30 \
  --slack-webhook https://hooks.slack.com/YOUR_WEBHOOK
```

### `k8s_pod_health.py` — Pod Health Checker

Connects to the EKS cluster and flags CrashLoopBackOff, OOMKilled,
and pending pods. Can be run as a post-deployment smoke test.

```bash
pip install kubernetes
python scripts/k8s_pod_health.py --namespace app-dev
python scripts/k8s_pod_health.py --all-namespaces --fail-on-unhealthy
```

## IAM Permissions Required

| Script | IAM Actions |
|--------|-------------|
| `validate_tfstate.py` | `s3:GetObject`, `eks:ListClusters`, `ec2:DescribeVpcs` |
| `aws_cost_report.py` | `ce:GetCostAndUsage` |
| `k8s_pod_health.py` | Kubernetes RBAC: `get`, `list` on `pods` |
