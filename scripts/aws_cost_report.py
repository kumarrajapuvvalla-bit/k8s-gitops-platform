#!/usr/bin/env python3
"""aws_cost_report.py — EKS & Infrastructure Cost Reporter

Uses AWS Cost Explorer to fetch last 30 days of spend broken
down by service and tagged resources. Outputs a summary to
stdout and optionally posts it to a Slack webhook.

Usage:
    python scripts/aws_cost_report.py \
        --region eu-west-2 \
        --project k8s-gitops-platform \
        [--slack-webhook https://hooks.slack.com/...]

Requires:
    pip install boto3
    AWS Cost Explorer must be enabled in the account.
    IAM permission: ce:GetCostAndUsage
"""

import argparse
import json
import logging
import sys
import urllib.request
from datetime import date, timedelta
from typing import Any

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def get_cost_by_service(
    region: str, start: str, end: str, tag_key: str, tag_value: str
) -> list[dict[str, Any]]:
    """Fetch cost grouped by AWS service for tagged resources."""
    ce = boto3.client("ce", region_name="us-east-1")  # CE is global, endpoint is us-east-1
    try:
        response = ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Filter={
                "Tags": {
                    "Key": tag_key,
                    "Values": [tag_value],
                    "MatchOptions": ["EQUALS"],
                }
            },
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            Metrics=["UnblendedCost"],
        )
        return response.get("ResultsByTime", [])
    except ClientError as exc:
        log.error("Cost Explorer query failed: %s", exc)
        sys.exit(1)


def format_report(results: list[dict[str, Any]], project: str, period_start: str, period_end: str) -> str:
    """Format cost results into a human-readable report string."""
    lines = [
        f"AWS Cost Report — Project: {project}",
        f"Period: {period_start} to {period_end}",
        "-" * 50,
    ]

    total = 0.0
    for period in results:
        for group in period.get("Groups", []):
            service = group["Keys"][0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            currency = group["Metrics"]["UnblendedCost"]["Unit"]
            if amount > 0.01:  # Skip negligible amounts
                lines.append(f"  {service:<40} {amount:>10.2f} {currency}")
                total += amount

    lines.append("-" * 50)
    lines.append(f"  {'TOTAL':<40} {total:>10.2f} USD")
    return "\n".join(lines)


def post_to_slack(webhook_url: str, message: str) -> None:
    """Post a plain-text message to a Slack incoming webhook."""
    payload = json.dumps({"text": f"```{message}```"}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            log.warning("Slack webhook returned %s", resp.status)
        else:
            log.info("Cost report posted to Slack")


def main() -> None:
    parser = argparse.ArgumentParser(description="AWS cost report for tagged project resources")
    parser.add_argument("--region", default="eu-west-2")
    parser.add_argument("--project", default="k8s-gitops-platform", help="Value of the Project tag")
    parser.add_argument("--days", type=int, default=30, help="Number of days to look back")
    parser.add_argument("--slack-webhook", default="", help="Optional Slack webhook URL")
    args = parser.parse_args()

    end_date = date.today()
    start_date = end_date - timedelta(days=args.days)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    log.info("Fetching costs for project=%s from %s to %s", args.project, start_str, end_str)
    results = get_cost_by_service(args.region, start_str, end_str, "Project", args.project)

    report = format_report(results, args.project, start_str, end_str)
    print(report)

    if args.slack_webhook:
        post_to_slack(args.slack_webhook, report)


if __name__ == "__main__":
    main()
