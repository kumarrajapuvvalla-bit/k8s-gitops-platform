"""k8s-gitops-platform - Application Service

Simple FastAPI service demonstrating the application deployed
via ArgoCD GitOps pipeline. Exposes health, readiness and
metrics endpoints expected by the Helm chart probes.
"""

import os
import time
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import uvicorn

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# ── App bootstrap ──────────────────────────────────────────────────────────
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
START_TIME = time.time()

app = FastAPI(
    title="k8s-gitops-platform",
    description="Demo service deployed via ArgoCD GitOps pipeline",
    version=APP_VERSION,
)


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["observability"])
async def health() -> JSONResponse:
    """Liveness probe — returns 200 if the process is alive."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "version": APP_VERSION,
            "environment": ENVIRONMENT,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.get("/ready", tags=["observability"])
async def readiness() -> JSONResponse:
    """Readiness probe — returns 200 when ready to serve traffic."""
    # In a real service you'd check DB connections, downstream deps, etc.
    return JSONResponse(
        status_code=200,
        content={"status": "ready", "uptime_seconds": round(time.time() - START_TIME, 2)},
    )


@app.get("/metrics", tags=["observability"])
async def metrics(response: Response) -> Response:
    """Prometheus-compatible metrics endpoint (plain text format)."""
    uptime = round(time.time() - START_TIME, 2)
    body = (
        "# HELP app_uptime_seconds Total uptime of the application\n"
        "# TYPE app_uptime_seconds gauge\n"
        f'app_uptime_seconds{{environment="{ENVIRONMENT}",version="{APP_VERSION}"}} {uptime}\n'
    )
    return Response(content=body, media_type="text/plain; version=0.0.4")


@app.get("/", tags=["root"])
async def root() -> JSONResponse:
    """Root endpoint — useful for smoke testing."""
    return JSONResponse(
        content={
            "service": "k8s-gitops-platform",
            "version": APP_VERSION,
            "environment": ENVIRONMENT,
            "docs": "/docs",
        }
    )


# ── Entrypoint ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    logger.info("Starting server on port %s (env=%s)", port, ENVIRONMENT)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
