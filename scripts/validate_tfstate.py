#!/usr/bin/env python3
"""validate_tfstate.py — Terraform State Drift Validator

Compares live AWS resource counts against what Terraform state
expects. Useful as a scheduled job or post-apply validation step
in a CI/CD pipeline.

Usage:
    python scripts/validate_tfstate.py \
        --bucket my-tfstate-bucket \
        --key gitops-platform/dev/terraform.tfstate \
        --region eu-west-2

Requires:
    pip install boto3
    AWS credentials via env vars, instance profile, or IRSA
"""

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


@dataclass
class DriftResult:
    resource_type: str
    expected: int
    actual: int

    @property
    def drifted(self) -> bool:
        return self.expected != self.actual

    def __str__(self) -> str:
        status = "DRIFT" if self.drifted else "OK"
        return f"[{status}] {self.resource_type}: expected={self.expected} actual={self.actual}"


def fetch_tfstate(bucket: str, key: str, region: str) -> dict[str, Any]:
    """Download and parse Terraform state from S3."""
    s3 = boto3.client("s3", region_name=region)
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        raw = response["Body"].read()
        return json.loads(raw)
    except ClientError as exc:
        log.error("Failed to fetch state from s3://%s/%s: %s", bucket, key, exc)
        sys.exit(1)


def count_resources_in_state(state: dict[str, Any], resource_type: str) -> int:
    """Count instances of a resource type in the Terraform state file."""
    count = 0
    for resource in state.get("resources", []):
        if resource.get("type") == resource_type:
            count += len(resource.get("instances", []))
    return count


def count_live_eks_clusters(region: str, cluster_name_prefix: str) -> int:
    """Count live EKS clusters matching a name prefix."""
    eks = boto3.client("eks", region_name=region)
    try:
        paginator = eks.get_paginator("list_clusters")
        clusters = []
        for page in paginator.paginate():
            clusters.extend(page["clusters"])
        return sum(1 for c in clusters if c.startswith(cluster_name_prefix))
    except ClientError as exc:
        log.warning("Could not list EKS clusters: %s", exc)
        return -1


def count_live_vpcs(region: str, tag_project: str) -> int:
    """Count live VPCs tagged with a specific project name."""
    ec2 = boto3.client("ec2", region_name=region)
    try:
        response = ec2.describe_vpcs(
            Filters=[{"Name": "tag:Project", "Values": [tag_project]}]
        )
        return len(response["Vpcs"])
    except ClientError as exc:
        log.warning("Could not describe VPCs: %s", exc)
        return -1


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Terraform state drift")
    parser.add_argument("--bucket", required=True, help="S3 bucket containing tfstate")
    parser.add_argument("--key", required=True, help="S3 key path to terraform.tfstate")
    parser.add_argument("--region", default="eu-west-2", help="AWS region")
    parser.add_argument("--cluster-prefix", default="gitops", help="EKS cluster name prefix")
    parser.add_argument("--project-tag", default="k8s-gitops-platform", help="Project tag value")
    args = parser.parse_args()

    log.info("Fetching Terraform state from s3://%s/%s", args.bucket, args.key)
    state = fetch_tfstate(args.bucket, args.key, args.region)
    log.info("Terraform state serial: %s", state.get("serial", "unknown"))

    results: list[DriftResult] = []

    # EKS clusters
    expected_eks = count_resources_in_state(state, "aws_eks_cluster")
    actual_eks = count_live_eks_clusters(args.region, args.cluster_prefix)
    results.append(DriftResult("aws_eks_cluster", expected_eks, actual_eks))

    # VPCs
    expected_vpc = count_resources_in_state(state, "aws_vpc")
    actual_vpc = count_live_vpcs(args.region, args.project_tag)
    results.append(DriftResult("aws_vpc", expected_vpc, actual_vpc))

    # Report
    print("\n=== Drift Validation Report ===")
    drift_found = False
    for result in results:
        print(result)
        if result.drifted:
            drift_found = True

    if drift_found:
        log.error("Drift detected — investigate before next apply")
        sys.exit(1)
    else:
        log.info("No drift detected — state matches live resources")


if __name__ == "__main__":
    main()
