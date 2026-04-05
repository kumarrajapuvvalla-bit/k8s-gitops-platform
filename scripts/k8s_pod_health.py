#!/usr/bin/env python3
"""k8s_pod_health.py — Kubernetes Pod Health Checker

Connects to an EKS cluster and reports on pod health across
namespaces. Flags CrashLoopBackOff, OOMKilled, and pending pods.
Useful as a scheduled diagnostic script or post-deployment check.

Usage:
    # Using current kubeconfig context
    python scripts/k8s_pod_health.py --namespace app-dev

    # All namespaces
    python scripts/k8s_pod_health.py --all-namespaces

Requires:
    pip install kubernetes
    kubectl configured with cluster access (IRSA or kubeconfig)
"""

import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Optional

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PROBLEM_REASONS = {"CrashLoopBackOff", "OOMKilled", "Error", "ImagePullBackOff", "ErrImagePull"}


@dataclass
class PodStatus:
    namespace: str
    name: str
    phase: str
    ready: bool
    restart_count: int
    problem_reason: Optional[str]

    @property
    def healthy(self) -> bool:
        return self.phase == "Running" and self.ready and self.problem_reason is None

    def summary_line(self) -> str:
        icon = "✅" if self.healthy else "❌"
        reason = f" [{self.problem_reason}]" if self.problem_reason else ""
        return (
            f"{icon} {self.namespace}/{self.name} "
            f"phase={self.phase} ready={self.ready} "
            f"restarts={self.restart_count}{reason}"
        )


def load_kube_config() -> None:
    """Load kubeconfig — in-cluster config if running inside a pod, else local."""
    try:
        config.load_incluster_config()
        log.info("Using in-cluster Kubernetes config")
    except config.ConfigException:
        config.load_kube_config()
        log.info("Using local kubeconfig")


def get_pod_statuses(namespace: Optional[str] = None) -> list[PodStatus]:
    """Return PodStatus objects for all pods in a namespace (or all namespaces)."""
    v1 = client.CoreV1Api()
    try:
        if namespace:
            pod_list = v1.list_namespaced_pod(namespace=namespace)
        else:
            pod_list = v1.list_pod_for_all_namespaces()
    except ApiException as exc:
        log.error("Kubernetes API error: %s", exc)
        sys.exit(1)

    statuses = []
    for pod in pod_list.items:
        ns = pod.metadata.namespace
        name = pod.metadata.name
        phase = pod.status.phase or "Unknown"

        restart_count = 0
        problem_reason = None
        ready = False

        if pod.status.container_statuses:
            for cs in pod.status.container_statuses:
                restart_count += cs.restart_count
                if cs.ready:
                    ready = True
                # Check waiting/terminated reasons
                if cs.state.waiting and cs.state.waiting.reason in PROBLEM_REASONS:
                    problem_reason = cs.state.waiting.reason
                if cs.state.terminated and cs.state.terminated.reason in PROBLEM_REASONS:
                    problem_reason = cs.state.terminated.reason

        statuses.append(PodStatus(ns, name, phase, ready, restart_count, problem_reason))

    return statuses


def main() -> None:
    parser = argparse.ArgumentParser(description="Kubernetes pod health checker")
    parser.add_argument("--namespace", "-n", default="", help="Namespace to inspect")
    parser.add_argument("--all-namespaces", "-A", action="store_true", help="Check all namespaces")
    parser.add_argument("--fail-on-unhealthy", action="store_true", help="Exit 1 if any pod is unhealthy")
    args = parser.parse_args()

    load_kube_config()

    ns = None if args.all_namespaces else (args.namespace or "default")
    log.info("Checking pods in %s", f"namespace={ns}" if ns else "all namespaces")

    statuses = get_pod_statuses(ns)

    if not statuses:
        log.warning("No pods found")
        sys.exit(0)

    unhealthy = [s for s in statuses if not s.healthy]
    healthy = [s for s in statuses if s.healthy]

    print(f"\n=== Pod Health Report ({len(statuses)} pods) ===")
    print(f"Healthy: {len(healthy)}  |  Unhealthy: {len(unhealthy)}")
    print("-" * 60)

    for s in sorted(statuses, key=lambda x: (x.healthy, x.namespace, x.name)):
        print(s.summary_line())

    if unhealthy:
        print(f"\n⚠️  {len(unhealthy)} pod(s) require attention")
        if args.fail_on_unhealthy:
            sys.exit(1)
    else:
        print("\n✅ All pods are healthy")


if __name__ == "__main__":
    main()
