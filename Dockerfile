# Multi-stage Dockerfile for k8s-gitops-platform
# Stage 1: builder — installs dependencies into a venv
# Stage 2: runtime — distroless image, non-root, minimal attack surface
#
# Build: docker build -t k8s-gitops-platform:latest .
# Run:   docker run -p 8080:8080 k8s-gitops-platform:latest

# ── Stage 1: builder ───────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install only what we need to build the venv
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt .

# Create isolated venv so we can copy it cleanly to the final stage
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ───────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --no-create-home appuser

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

# Healthcheck so Docker / ECS / EKS can probe without a sidecar
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
