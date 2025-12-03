# MCP OCI OPSI Server - Production Container
# Multi-stage build for minimal image size

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .
COPY README.md .

# Install dependencies
RUN pip install --no-cache-dir build && \
    pip install --no-cache-dir .

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash mcp && \
    mkdir -p /data/oauth /data/cache && \
    chown -R mcp:mcp /data

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY mcp_oci_opsi/ /app/mcp_oci_opsi/
COPY skills/ /app/skills/

# Set ownership
RUN chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Environment variables (override in deployment)
ENV MCP_TRANSPORT=http \
    MCP_HTTP_HOST=0.0.0.0 \
    MCP_HTTP_PORT=8000 \
    MCP_VERSION=v3 \
    MCP_OAUTH_STORAGE_PATH=/data/oauth \
    PYTHONUNBUFFERED=1

# Expose HTTP port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run server
CMD ["python", "-m", "mcp_oci_opsi"]
