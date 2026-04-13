# Multi-stage Dockerfile for k8s-gitops-platform
#
# Stage 1: builder (python:3.12-slim) — compile deps into an isolated venv
# Stage 2: runtime (python:3.12-alpine) — minimal OS attack surface,
#          no apt packages, non-root user
#
# Build: docker build -t k8s-gitops-platform:latest .
# Run:   docker run -p 8080:8080 k8s-gitops-platform:latest

# ── Stage 1: builder ──────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# gcc needed to compile some Python C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt .

# Isolated venv so we can copy it cleanly to the runtime stage
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip --no-cache-dir \
    && pip install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────────────
# Alpine has a dramatically smaller CVE surface than debian-slim:
# musl libc + apk packages have far fewer unfixed CRITICAL/HIGH CVEs.
# glibc-dependent binaries from builder venv are copied in directly.
FROM python:3.12-alpine AS runtime

# Security: run as non-root user
RUN addgroup -g 1001 appgroup \
    && adduser -u 1001 -G appgroup -H -D appuser

WORKDIR /app

# Copy the venv from builder (no pip, no gcc in final image)
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY app/main.py .

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    ENVIRONMENT=prod

# Drop to non-root
USER appuser

EXPOSE 8080

# Liveness probe compatible with both Docker and Kubernetes
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
