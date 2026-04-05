"""Unit tests for the k8s-gitops-platform FastAPI service.

Runs with: pytest app/tests/ -v
All tests use the ASGI test client — no real server needed.
"""

import pytest
from fastapi.testclient import TestClient

# Add the app directory to sys.path so the import resolves cleanly
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app  # noqa: E402

client = TestClient(app)


# ── Health endpoint ────────────────────────────────────────────────────────

class TestHealth:
    def test_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_response_has_status_healthy(self):
        response = client.get("/health")
        assert response.json()["status"] == "healthy"

    def test_response_has_version(self):
        response = client.get("/health")
        assert "version" in response.json()

    def test_response_has_timestamp(self):
        response = client.get("/health")
        assert "timestamp" in response.json()

    def test_response_has_environment(self):
        response = client.get("/health")
        assert "environment" in response.json()


# ── Readiness endpoint ─────────────────────────────────────────────────────

class TestReadiness:
    def test_returns_200(self):
        response = client.get("/ready")
        assert response.status_code == 200

    def test_response_has_status_ready(self):
        response = client.get("/ready")
        assert response.json()["status"] == "ready"

    def test_response_has_uptime(self):
        response = client.get("/ready")
        assert "uptime_seconds" in response.json()
        assert isinstance(response.json()["uptime_seconds"], float)


# ── Metrics endpoint ───────────────────────────────────────────────────────

class TestMetrics:
    def test_returns_200(self):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_content_type_is_prometheus(self):
        response = client.get("/metrics")
        assert "text/plain" in response.headers["content-type"]

    def test_contains_uptime_metric(self):
        response = client.get("/metrics")
        assert "app_uptime_seconds" in response.text

    def test_prometheus_format_has_help_line(self):
        response = client.get("/metrics")
        assert "# HELP" in response.text

    def test_prometheus_format_has_type_line(self):
        response = client.get("/metrics")
        assert "# TYPE" in response.text


# ── Root endpoint ──────────────────────────────────────────────────────────

class TestRoot:
    def test_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_contains_service_name(self):
        response = client.get("/")
        assert response.json()["service"] == "k8s-gitops-platform"

    def test_contains_docs_link(self):
        response = client.get("/")
        assert response.json()["docs"] == "/docs"
