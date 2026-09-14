# ==============================================================================
# Multi-Stage Production Dockerfile for looksmaxxing.guide
# Conforms to /hub-cloud & Senior DevOps invariants:
# - Multi-stage separation of build tools and runtime
# - Non-root container execution (UID 10001)
# - Container healthcheck integration
# ==============================================================================

# STAGE 1: Build Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --upgrade pip \
    && pip install wheel setuptools \
    && pip install . \
    && pip install langgraph langchain-core opentelemetry-api opentelemetry-sdk langfuse httpx fastapi uvicorn

# ==============================================================================
# STAGE 2: Minimal Production Runtime
# ==============================================================================
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    ENVIRONMENT=production

# Install curl for healthcheck verification
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user and group (UID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -d /app -s /sbin/nologin appuser

# Copy installed site-packages and binaries from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY --chown=appuser:appgroup src/ ./src
COPY --chown=appuser:appgroup pyproject.toml README.md ./

# Create data directories with non-root ownership
RUN mkdir -p /app/dist/content /app/data && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER 10001:10001

EXPOSE 8000

# Container Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
