"""test_main.py — pytest test suite for k8s-gitops-platform FastAPI app.

Covers all public endpoints: /, /health, /ready, /metrics
and validates response shapes, status codes, and key fields.
"""

from fastapi.testclient import TestClient
from main import app, APP_VERSION, ENVIRONMENT

client = TestClient(app)


# ── Root ───────────────────────────────────────────────────────────────────────

class TestRoot:
    def test_root_status(self):
        r = client.get("/")
        assert r.status_code == 200

    def test_root_has_service_key(self):
        body = client.get("/").json()
        assert body["service"] == "k8s-gitops-platform"

    def test_root_has_version(self):
        body = client.get("/").json()
        assert body["version"] == APP_VERSION

    def test_root_has_docs_link(self):
        body = client.get("/").json()
        assert body["docs"] == "/docs"

    def test_root_has_environment(self):
        body = client.get("/").json()
        assert body["environment"] == ENVIRONMENT


# ── Health ───────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_status_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_body_status_healthy(self):
        body = client.get("/health").json()
        assert body["status"] == "healthy"

    def test_health_has_version(self):
        body = client.get("/health").json()
        assert body["version"] == APP_VERSION

    def test_health_has_environment(self):
        body = client.get("/health").json()
        assert body["environment"] == ENVIRONMENT

    def test_health_has_timestamp(self):
        body = client.get("/health").json()
        assert "timestamp" in body
        # Should be ISO-8601 with timezone
        assert "T" in body["timestamp"]


# ── Readiness ─────────────────────────────────────────────────────────────────

class TestReadiness:
    def test_ready_status_200(self):
        r = client.get("/ready")
        assert r.status_code == 200

    def test_ready_body_status_ready(self):
        body = client.get("/ready").json()
        assert body["status"] == "ready"

    def test_ready_has_uptime(self):
        body = client.get("/ready").json()
        assert "uptime_seconds" in body
        assert isinstance(body["uptime_seconds"], (int, float))
        assert body["uptime_seconds"] >= 0


# ── Metrics ───────────────────────────────────────────────────────────────────

class TestMetrics:
    def test_metrics_status_200(self):
        r = client.get("/metrics")
        assert r.status_code == 200

    def test_metrics_content_type_prometheus(self):
        r = client.get("/metrics")
        assert "text/plain" in r.headers["content-type"]

    def test_metrics_contains_uptime_gauge(self):
        r = client.get("/metrics")
        assert "app_uptime_seconds" in r.text

    def test_metrics_contains_help_line(self):
        r = client.get("/metrics")
        assert "# HELP" in r.text

    def test_metrics_contains_type_line(self):
        r = client.get("/metrics")
        assert "# TYPE" in r.text

    def test_metrics_contains_environment_label(self):
        r = client.get("/metrics")
        assert f'environment="{ENVIRONMENT}"' in r.text


# ── OpenAPI / docs ─────────────────────────────────────────────────────────────

class TestOpenAPI:
    def test_openapi_json_accessible(self):
        r = client.get("/openapi.json")
        assert r.status_code == 200

    def test_openapi_has_correct_title(self):
        body = client.get("/openapi.json").json()
        assert body["info"]["title"] == "k8s-gitops-platform"

    def test_openapi_has_version(self):
        body = client.get("/openapi.json").json()
        assert body["info"]["version"] == APP_VERSION
